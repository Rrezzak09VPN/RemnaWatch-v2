import asyncio
import json
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from typing import AsyncIterator, Tuple

logger = logging.getLogger(__name__)


class PortAllocator:
    def __init__(self, start: int = 20001, end: int = 30000):
        self._current = start
        self._start = start
        self._end = end

    def next_port(self) -> int:
        port = self._current
        self._current += 1
        if self._current > self._end:
            self._current = self._start
        return port


class SingBoxRunner:
    def __init__(self, singbox_bin: str):
        self.singbox_bin = singbox_bin
        self._port_alloc = PortAllocator()

    def _next_port(self) -> int:
        return self._port_alloc.next_port()

    @staticmethod
    def _read_tail(path: str, limit: int = 8000) -> str:
        try:
            with open(path, "rb") as f:
                data = f.read()[-limit:]
            return data.decode("utf-8", errors="replace").strip()
        except OSError:
            return ""

    @asynccontextmanager
    async def run(self, config: dict, label: str = "", timeout: float = 10.0) -> AsyncIterator[Tuple[int, asyncio.subprocess.Process]]:
        port = self._next_port()
        config["inbounds"][0]["listen_port"] = port

        cfg_tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        log_tmp = tempfile.NamedTemporaryFile(mode="wb", suffix=".log", delete=False)
        cfg_path = cfg_tmp.name
        log_path = log_tmp.name
        try:
            json.dump(config, cfg_tmp, ensure_ascii=False)
            cfg_tmp.close()
            log_tmp.close()

            log_fd = open(log_path, "ab")
            proc = await asyncio.create_subprocess_exec(
                self.singbox_bin,
                "run",
                "-c",
                cfg_path,
                stdout=log_fd,
                stderr=log_fd,
            )
            await asyncio.sleep(2)
            if proc.returncode is not None:
                log_fd.close()
                tail = self._read_tail(log_path)
                raise RuntimeError(f"sing-box exited during startup rc={proc.returncode}: {tail}")

            logger.info("sing-box started for %s on 127.0.0.1:%s pid=%s", label or "check", port, proc.pid)
            try:
                yield port, proc
            finally:
                try:
                    if proc.returncode is None:
                        proc.terminate()
                        try:
                            await asyncio.wait_for(proc.wait(), timeout=2.0)
                        except asyncio.TimeoutError:
                            proc.kill()
                            await proc.wait()
                except ProcessLookupError:
                    pass
                finally:
                    log_fd.close()
                    tail = self._read_tail(log_path)
                    if tail:
                        logger.debug("sing-box log for %s: %s", label or "check", tail)
        finally:
            for path in (cfg_path, log_path):
                try:
                    os.unlink(path)
                except OSError:
                    pass
