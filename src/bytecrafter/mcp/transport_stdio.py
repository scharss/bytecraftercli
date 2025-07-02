import json
import subprocess
import threading
import time
import uuid
import sys
import shlex
from typing import Any, Dict, Optional


class StdioClient:
    """Simple JSON-RPC 2.0 client over STDIO for MCP servers.

    The client spawns the server process locally and communicates using
    newline-delimited JSON messages on stdin/stdout.
    """

    def __init__(self, command: str | list[str]):
        # Accept either a shell string or a list. If it's a python file, run with current interpreter.
        if isinstance(command, str):
            if command.endswith(".py"):
                cmd_list = [sys.executable, command]
            else:
                cmd_list = shlex.split(command)
        else:
            cmd_list = command

        self._proc = subprocess.Popen(
            cmd_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self._lock = threading.Lock()
        self._responses: dict[str, Any] = {}
        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

    # -------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------
    def send_request(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 15.0) -> Any:
        """Sends a JSON-RPC request and waits for the response."""
        req_id = str(uuid.uuid4())
        message = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params or {},
        }
        line = json.dumps(message, ensure_ascii=False)
        with self._lock:
            if self._proc.stdin is None:
                raise RuntimeError("Process stdin closed")
            self._proc.stdin.write(line + "\n")
            self._proc.stdin.flush()

        # Wait for response
        start = time.time()
        while time.time() - start < timeout:
            if req_id in self._responses:
                return self._responses.pop(req_id)
            time.sleep(0.05)
        return {"error": "timeout"}

    def close(self):
        """Terminate the server process gracefully."""
        try:
            if self._proc.stdin:
                self._proc.stdin.close()
            if self._proc.poll() is None:
                self._proc.terminate()
        except Exception:
            pass

    # -------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------
    def _reader_loop(self):
        if self._proc.stdout is None:
            return
        for raw_line in self._proc.stdout:
            line = raw_line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            resp_id = data.get("id")
            if resp_id:
                self._responses[resp_id] = data.get("result", data) 