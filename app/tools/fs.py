import os
import logging
from pathlib import Path
from langchain.tools import tool

logger = logging.getLogger("tools.fs")

# ---------------------------------------------------------------------------
# Sandbox — all file operations are jailed to this directory
# ---------------------------------------------------------------------------
WORKSPACE = Path(os.getenv("AGENT_WORKSPACE", "./workspace")).resolve()
WORKSPACE.mkdir(parents=True, exist_ok=True)


def _safe_path(path: str) -> Path:
    """Resolve path and verify it stays within WORKSPACE. Raises on traversal."""
    resolved = (WORKSPACE / path).resolve()
    if not str(resolved).startswith(str(WORKSPACE)):
        logger.warning(f"Path traversal blocked: '{path}' resolved to '{resolved}'")
        raise ValueError(f"Access denied — path outside workspace: {path}")
    return resolved


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
@tool
def read_file(path: str) -> str:
    """Read a file from the agent workspace. Path is relative to workspace root."""
    target = _safe_path(path)
    if not target.exists():
        raise FileNotFoundError(f"File not found in workspace: {path}")
    if not target.is_file():
        raise ValueError(f"Path is not a file: {path}")
    logger.info(f"READ: {target}")
    return target.read_text(encoding="utf-8")


@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file in the agent workspace. Creates parent dirs as needed."""
    target = _safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    logger.info(f"WRITE: {target} ({len(content)} chars)")
    return f"Written: {path} ({len(content)} chars)"


@tool
def delete_file(path: str) -> str:
    """Delete a file from the agent workspace."""
    target = _safe_path(path)
    if not target.exists():
        raise FileNotFoundError(f"File not found in workspace: {path}")
    if not target.is_file():
        raise ValueError(f"Path is not a file: {path}")
    target.unlink()
    logger.info(f"DELETE: {target}")
    return f"Deleted: {path}"


@tool
def list_files(subdir: str = "") -> str:
    """List files in the workspace or a subdirectory of it."""
    target = _safe_path(subdir) if subdir else WORKSPACE
    if not target.is_dir():
        raise ValueError(f"Not a directory: {subdir}")
    files = [str(f.relative_to(WORKSPACE)) for f in target.rglob("*") if f.is_file()]
    logger.info(f"LIST: {target} — {len(files)} files")
    return "\n".join(files) if files else "(empty)"
