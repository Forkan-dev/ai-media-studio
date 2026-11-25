"""Starts the worker process when work is queued and it is not running, so nobody has to start it by hand.
The worker writes a heartbeat file; a lock file makes sure only one worker ever runs."""
import fcntl
import subprocess
import sys
import time
from typing import IO

from app.core.config import ROOT, settings

HEARTBEAT = settings.storage_dir / "worker.heartbeat"
LOCK = settings.storage_dir / "worker.lock"
LOG = settings.storage_dir / "logs" / "worker.log"
ALIVE_SECONDS = 10  # the worker beats every ~2 s


def is_alive() -> bool:
    return HEARTBEAT.exists() and time.time() - HEARTBEAT.stat().st_mtime < ALIVE_SECONDS


def beat() -> None:
    """Called by the worker on every loop."""
    HEARTBEAT.touch()


def ensure_running() -> None:
    """Start the worker in the background if it is not alive (a second one would exit on the lock)."""
    if is_alive():
        return
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as log:
        subprocess.Popen([sys.executable, "-m", "app.worker"], cwd=ROOT / "backend", stdout=log, stderr=log,
                         stdin=subprocess.DEVNULL, start_new_session=True)  # keeps running if the API restarts
    HEARTBEAT.touch()  # counts as alive while it starts, so the next requests do not start more


def hold_lock() -> IO | None:
    """Worker: an exclusive lock for its whole life. None if another worker already runs."""
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    handle = LOCK.open("w")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        return None
    return handle
