import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional

from pyrogram.errors import FloodWait, MessageNotModified

MIN_PROGRESS_UPDATE_SECONDS = 3.0
SPEED_SMOOTHING_ALPHA = 0.3
PROGRESS_BAR_LENGTH = 12


def _fmt_size(num_bytes: float) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    value = float(max(num_bytes, 0.0))
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{num_bytes:.2f} B"


def _fmt_duration(seconds: float) -> str:
    seconds = max(int(seconds), 0)
    mins, secs = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{hours}h {mins}m {secs}s"
    if mins:
        return f"{mins}m {secs}s"
    return f"{secs}s"


@dataclass(slots=True)
class TransferState:
    status: str
    current: int = 0
    total: Optional[int] = None
    started_at: float = field(default_factory=time.monotonic)
    done: bool = False
    failed: bool = False
    error: Optional[str] = None
    _last_sample_at: float = field(default_factory=time.monotonic)
    _last_sample_bytes: int = 0
    _speed_bps: float = 0.0

    def add_progress(self, chunk_size: int) -> None:
        self.current += max(chunk_size, 0)

    def set_progress(self, current: int, total: Optional[int] = None) -> None:
        self.current = max(current, 0)
        if total is not None:
            self.total = max(total, 0)

    def mark_done(self) -> None:
        self.done = True

    def mark_failed(self, error: str) -> None:
        self.failed = True
        self.error = error
        self.done = True

    def elapsed(self) -> float:
        return max(time.monotonic() - self.started_at, 0.001)

    def speed_bps(self) -> float:
        now = time.monotonic()
        delta_t = max(now - self._last_sample_at, 1e-6)
        delta_b = max(self.current - self._last_sample_bytes, 0)
        instant_bps = delta_b / delta_t

        if self._speed_bps == 0.0:
            self._speed_bps = instant_bps
        else:
            self._speed_bps = (
                SPEED_SMOOTHING_ALPHA * instant_bps
                + (1.0 - SPEED_SMOOTHING_ALPHA) * self._speed_bps
            )

        self._last_sample_at = now
        self._last_sample_bytes = self.current
        return max(self._speed_bps, 0.0)

    def render_text(self) -> str:
        elapsed = self.elapsed()
        speed = self.speed_bps()
        speed_text = _fmt_size(speed) + "/s"
        current_text = _fmt_size(self.current)

        if self.total:
            total_text = _fmt_size(self.total)
            percent = min((self.current / self.total) * 100.0, 100.0)
            filled = int(PROGRESS_BAR_LENGTH * percent / 100.0)
            bar = "#" * filled + "-" * (PROGRESS_BAR_LENGTH - filled)
            if speed > 0:
                eta = (self.total - self.current) / speed
                eta_text = _fmt_duration(eta)
            else:
                eta_text = "Unknown"
            return (
                f"{self.status}\n"
                f"[{bar}] {percent:.2f}%\n"
                f"Size: {current_text} / {total_text}\n"
                f"Speed: {speed_text}\n"
                f"ETA: {eta_text}\n"
                f"Elapsed: {_fmt_duration(elapsed)}"
            )

        return (
            f"{self.status}\n"
            f"Size: {current_text}\n"
            f"Speed: {speed_text}\n"
            f"Elapsed: {_fmt_duration(elapsed)}"
        )


class TelegramProgressReporter:
    def __init__(self, message, state: TransferState, update_interval: float = 3.0):
        self.message = message
        self.state = state
        self.update_interval = max(float(update_interval), MIN_PROGRESS_UPDATE_SECONDS)
        self._stop_event = asyncio.Event()

    def stop(self) -> None:
        self._stop_event.set()

    async def run(self) -> None:
        while not self.state.done and not self._stop_event.is_set():
            await self._edit_once()
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.update_interval,
                )
            except asyncio.TimeoutError:
                pass

    async def _edit_once(self) -> None:
        try:
            await self.message.edit_text(self.state.render_text())
        except MessageNotModified:
            return
        except FloodWait as fw:
            await asyncio.sleep(max(fw.value, MIN_PROGRESS_UPDATE_SECONDS))
        except Exception:
            # Progress updates should never break transfer flow.
            return
