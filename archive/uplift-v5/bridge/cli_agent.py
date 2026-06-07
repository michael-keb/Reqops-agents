"""Cursor `agent` CLI — one chat session, headless print per turn (readable output)."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from shutil import which

from bridge.logging_util import ROOT, fmt_cmd, log

AGENT_TIMEOUT = int(os.environ.get("UPLIFT_AGENT_TIMEOUT", "600"))


class CliAgentSession:
    """Same agent *conversation* via --resume <chat-id>; headless -p for clean terminal text."""

    def __init__(self, session_dir: Path) -> None:
        self.session_dir = session_dir
        self._chat_id: str | None = None
        self._pid_last: int | None = None

    @property
    def is_alive(self) -> bool:
        # Conversation persists via chat id on disk
        return bool(self._chat_id or self._chat_id_path.is_file())

    @property
    def _chat_id_path(self) -> Path:
        return self.session_dir / ".chat-id"

    def _agent_bin(self) -> str:
        path = which("agent")
        if not path:
            raise RuntimeError("Cursor agent CLI not on PATH — run: curl https://cursor.com/install -fsS | bash")
        return path

    def _env(self) -> dict[str, str]:
        return {**os.environ, "UPLIFT_SESSION": str(self.session_dir)}

    def _load_chat_id(self) -> str | None:
        if self._chat_id:
            return self._chat_id
        if self._chat_id_path.is_file():
            cid = self._chat_id_path.read_text(encoding="utf-8").strip()
            if cid:
                self._chat_id = cid
                return cid
        return None

    def _save_chat_id(self, chat_id: str) -> None:
        self._chat_id = chat_id.strip()
        self._chat_id_path.write_text(self._chat_id, encoding="utf-8")

    def ensure_chat(self) -> str:
        existing = self._load_chat_id()
        if existing:
            return existing
        log("agent create-chat")
        proc = subprocess.run(
            [self._agent_bin(), "create-chat"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            env=self._env(),
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(f"agent create-chat failed: {err}")
        chat_id = (proc.stdout or "").strip().splitlines()[-1].strip()
        if not chat_id:
            raise RuntimeError("agent create-chat returned empty id")
        self._save_chat_id(chat_id)
        log(f"chat id: {chat_id[:12]}… (reused for every turn in this session)")
        return chat_id

    def _cmd(self, chat_id: str, prompt: str) -> list[str]:
        cmd = [
            self._agent_bin(),
            "--resume",
            chat_id,
            "-p",
            prompt,
            "--output-format",
            "text",
            "--trust",
            "--force",
        ]
        if os.environ.get("UPLIFT_APPROVE_MCPS", "1").strip() not in ("0", "false", "no"):
            cmd.append("--approve-mcps")
        return cmd

    def send(self, message: str) -> int:
        chat_id = self.ensure_chat()
        cmd = self._cmd(chat_id, message.strip())
        log(f"$ {fmt_cmd(cmd)}")
        log("")

        proc = subprocess.Popen(
            cmd,
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=self._env(),
        )
        self._pid_last = proc.pid
        if proc.stdout is None:
            raise RuntimeError("agent stdout unavailable")

        try:
            for line in proc.stdout:
                text = line.rstrip("\n")
                if text.strip():
                    log(text, kind="agent")
        except Exception:
            proc.kill()
            raise

        try:
            proc.wait(timeout=AGENT_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            raise RuntimeError(f"agent timed out after {AGENT_TIMEOUT}s") from None

        if proc.returncode != 0:
            log(f"agent exited {proc.returncode}", kind="err")
            return proc.returncode or 1
        return 0

    def close(self) -> None:
        # Chat id stays on disk; nothing to kill between turns
        pass

    @property
    def pid_hint(self) -> str | None:
        return str(self._pid_last) if self._pid_last else None
