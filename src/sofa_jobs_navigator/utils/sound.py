"""Sound playback helpers."""

from __future__ import annotations

import os
import platform
import subprocess
from typing import Optional

from ..config.flags import FlagSet, FLAGS


class SoundPlayer:
    def __init__(self, *, flags: FlagSet = FLAGS) -> None:
        self._flags = flags
        self._system = platform.system()

    def play_success(self) -> None:
        self._play('success')

    def play_warning(self) -> None:
        self._play('warning')

    def _play(self, sound_type: str) -> None:
        if self._flags.mute_sounds:
            return
        try:
            if self._system == 'Darwin':
                name = 'Glass' if sound_type == 'success' else 'Funk'
                subprocess.run(['afplay', f'/System/Library/Sounds/{name}.aiff'], check=False)
            elif self._system == 'Windows':
                import winsound  # type: ignore
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION if sound_type == 'warning' else winsound.MB_ICONASTERISK)
            else:
                sound = 'success.wav' if sound_type == 'success' else 'warning.wav'
                subprocess.run(['paplay', os.path.expanduser(f'~/sounds/{sound}')], check=False)
        except Exception:
            pass


PLAYER = SoundPlayer()

# =================== END SOUND PLAYER ===================
