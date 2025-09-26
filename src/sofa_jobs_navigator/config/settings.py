"""Persistent configuration management."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List

from platformdirs import user_config_path

from .flags import FlagSet, FLAGS
from . import reference_data as ref

CONFIG_APP_NAME = "sofa_jobs_navigator"
CONFIG_FILE_NAME = "config.json"


@dataclass
class Favorite:
    label: str
    path: str
    hotkey: str | None = None


@dataclass
class Settings:
    favorites: List[Favorite] = field(default_factory=list)
    working_folder: str | None = None
    # Suffix appended to SKU when creating local folders (persisted)
    default_suffix: str = " - FTR "
    save_recent_skus: bool = True
    sounds_enabled: bool = True
    connect_on_startup: bool = False
    # If True, show a connect prompt when no valid credentials exist at startup (unless offline)
    prompt_for_connect_on_startup: bool = True
    # If True, after a successful startup connect (auto or prompted) perform a clipboard SKU auto-search
    auto_search_clipboard_after_connect: bool = False
    # If True, when multiple SKUs are detected they are auto-loaded into Recents (up to 7) without prompting
    auto_load_multi_skus_without_prompt: bool = False
    # When enabled, automatically open the SKU root in the browser when a SKU is found
    open_root_on_sku_found: bool = False
    recent_skus: List[str] = field(default_factory=list)
    show_help_on_startup: bool = True
    # When True, suppress the startup prompt to open Help after a failed auto-connect
    suppress_connect_setup_prompt: bool = False


# =================== SETTINGS MANAGER ===================

class SettingsManager:
    def __init__(self, *, flags: FlagSet = FLAGS, config_dir: Path | None = None) -> None:
        self._flags = flags
        self._config_dir = config_dir or user_config_path(CONFIG_APP_NAME)
        self._config_path = Path(self._config_dir) / CONFIG_FILE_NAME

    def load(self) -> Settings:
        if not self._config_path.exists():
            return self._defaults()
        with self._config_path.open('r', encoding='utf-8') as fh:
            raw = json.load(fh)
        favorites = [Favorite(**fav) for fav in raw.get('favorites', [])]
        # Ensure a minimum of 8 favorites (pad with empty entries for older configs)
        while len(favorites) < 8:
            favorites.append(Favorite(label='', path='', hotkey=None))
        return Settings(
            favorites=favorites,
            working_folder=raw.get('working_folder'),
            default_suffix=raw.get('default_suffix', ' - FTR '),
            save_recent_skus=raw.get('save_recent_skus', True),
            sounds_enabled=raw.get('sounds_enabled', True),
            connect_on_startup=raw.get('connect_on_startup', False),
            prompt_for_connect_on_startup=raw.get('prompt_for_connect_on_startup', True),
            auto_search_clipboard_after_connect=raw.get('auto_search_clipboard_after_connect', False),
            auto_load_multi_skus_without_prompt=raw.get('auto_load_multi_skus_without_prompt', False),
            open_root_on_sku_found=raw.get('open_root_on_sku_found', False),
            recent_skus=raw.get('recent_skus', []),
            show_help_on_startup=raw.get('show_help_on_startup', True),
            suppress_connect_setup_prompt=raw.get('suppress_connect_setup_prompt', False),
        )

    def save(self, settings: Settings) -> None:
        if self._flags.config_dry_run:
            return
        self._config_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            'favorites': [asdict(fav) for fav in settings.favorites],
            'working_folder': settings.working_folder,
            'default_suffix': getattr(settings, 'default_suffix', ' - FTR '),
            'save_recent_skus': settings.save_recent_skus,
            'sounds_enabled': settings.sounds_enabled,
            'connect_on_startup': settings.connect_on_startup,
            'prompt_for_connect_on_startup': getattr(settings, 'prompt_for_connect_on_startup', True),
            'auto_search_clipboard_after_connect': getattr(settings, 'auto_search_clipboard_after_connect', False),
            'auto_load_multi_skus_without_prompt': getattr(settings, 'auto_load_multi_skus_without_prompt', False),
            'open_root_on_sku_found': getattr(settings, 'open_root_on_sku_found', False),
            'recent_skus': settings.recent_skus,
            'show_help_on_startup': settings.show_help_on_startup,
            'suppress_connect_setup_prompt': getattr(settings, 'suppress_connect_setup_prompt', False),
        }
        with self._config_path.open('w', encoding='utf-8') as fh:
            json.dump(payload, fh, indent=2)

    def _defaults(self) -> Settings:
        favorites = [Favorite(label=data['label'], path=data.get('path', ''), hotkey=None) for data in ref.DEFAULT_SHORTCUTS]
        # Guarantee at least 8 entries even if defaults change
        while len(favorites) < 8:
            favorites.append(Favorite(label='', path='', hotkey=None))
        return Settings(favorites=favorites, recent_skus=[])


# =================== END SETTINGS MANAGER ===================
