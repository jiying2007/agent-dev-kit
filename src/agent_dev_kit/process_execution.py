"""One bounded process lifecycle for target smoke and native campaigns.

Output is captured only within an aggregate byte budget. Callers own evidence
projection and business error codes; this module does not grant certification.
POSIX cleanup covers the launched session's process group, including pipe
holders left behind by an exited launcher. Other platforms kill the direct
child only and must not claim POSIX descendant cleanup.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import signal
import time
from contextlib import suppress
from pathlib import Path
from typing import Mapping, Sequence, TypedDict


class OutputBudgetExceeded(ValueError):
    """The combined stdout/stderr budget was exceeded; no raw output escapes."""


class ProcessResult(TypedDict):
    exit_code: int
    duration_ms: float
    stdout_bytes: int
    stdout_sha256: str
    stdout: bytes
    stderr_bytes: int
    stderr_sha256: str
    stderr: bytes


def _kill_process(transport: asyncio.SubprocessTransport) -> None:
    # Kill the group even when its launcher has exited: descendants can still
    # own inherited pipes or continue work after the direct process is gone.
    if os.name == "posix":
        with suppress(ProcessLookupError):
            os.killpg(transport.get_pid(), signal.SIGKILL)
    elif transport.get_returncode() is None:
        transport.kill()


class _OutputProtocol(asyncio.SubprocessProtocol):
    """Capture a bounded pair of streams and signal full transport closure."""

    def __init__(self, loop: asyncio.AbstractEventLoop, output_limit: int) -> None:
        self.completed: asyncio.Future[None] = loop.create_future()
        self.closed: asyncio.Future[None] = loop.create_future()
        self.output_limit = output_limit
        self.total = 0
        self.streams = {1: bytearray(), 2: bytearray()}
        self.digests = {1: hashlib.sha256(), 2: hashlib.sha256()}

    def pipe_data_received(self, fd: int, data: bytes) -> None:
        if self.completed.done() or fd not in self.streams:
            return
        # Callbacks share one event loop. Splitting stdout/stderr never grants
        # another budget; reject the overflowing chunk before retaining it.
        self.total += len(data)
        if self.total > self.output_limit:
            self.completed.set_exception(OutputBudgetExceeded("process_output_budget_exceeded"))
            return
        self.streams[fd].extend(data)
        self.digests[fd].update(data)

    def pipe_connection_lost(self, fd: int, exc: Exception | None) -> None:
        if exc is not None and not self.completed.done():
            self.completed.set_exception(exc)

    def connection_lost(self, exc: Exception | None) -> None:
        # Process exit alone is insufficient: this callback follows closure
        # of the complete subprocess transport, including its pipe handles.
        if not self.completed.done():
            if exc is not None:
                self.completed.set_exception(exc)
            else:
                self.completed.set_result(None)
        if not self.closed.done():
            self.closed.set_result(None)


async def execute_bounded_async(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: int,
    output_limit: int,
) -> ProcessResult:
    if (type(timeout_seconds) is not int or timeout_seconds < 1
            or type(output_limit) is not int or output_limit < 1):
        raise ValueError("invalid_process_budget")
    loop = asyncio.get_running_loop()
    protocol = _OutputProtocol(loop, output_limit)
    started = time.monotonic()
    transport, _ = await loop.subprocess_exec(
        lambda: protocol,
        *command,
        cwd=str(cwd),
        env=dict(env),
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=os.name == "posix",
    )
    try:
        # A successful direct exit is insufficient while descendants retain
        # stdout/stderr. The same deadline bounds exit AND both pipe drains.
        await asyncio.wait_for(
            asyncio.shield(protocol.completed),
            timeout=max(0, timeout_seconds - (time.monotonic() - started)),
        )
    except BaseException:
        _kill_process(transport)
        # Use public transport ownership rather than Process._transport. Closing
        # pipes after killing the group also handles an already-exited launcher;
        # cancelled StreamReader tasks alone would leak their underlying handles.
        transport.close()
        # Transport handles are closed; preserve the original failure if the
        # bounded cleanup wait itself reaches its deadline.
        with suppress(asyncio.TimeoutError):
            await asyncio.wait_for(asyncio.shield(protocol.closed), timeout=5)
        raise
    finally:
        transport.close()
        if not protocol.completed.done():
            protocol.completed.cancel()
        elif not protocol.completed.cancelled():
            protocol.completed.exception()
    returncode = transport.get_returncode()
    if returncode is None:
        raise RuntimeError("process_closed_without_exit")
    return {
        "exit_code": returncode,
        "duration_ms": round((time.monotonic() - started) * 1000),
        "stdout_bytes": len(protocol.streams[1]),
        "stdout_sha256": protocol.digests[1].hexdigest(),
        "stdout": bytes(protocol.streams[1]),
        "stderr_bytes": len(protocol.streams[2]),
        "stderr_sha256": protocol.digests[2].hexdigest(),
        "stderr": bytes(protocol.streams[2]),
    }


def execute_bounded(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    timeout_seconds: int,
    output_limit: int,
) -> ProcessResult:
    return asyncio.run(
        execute_bounded_async(
            command, cwd=cwd, env=env,
            timeout_seconds=timeout_seconds, output_limit=output_limit,
        )
    )
