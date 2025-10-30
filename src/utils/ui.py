import os
import sys
from pathlib import Path
from typing import Optional

def resolve_ui_path(module_file: str, ui_filename: Optional[str] = None) -> str:
    """Resolve the file system path to a .ui file for a given module file.

    Works both in development and in PyInstaller-frozen builds.

    Strategy:
    - Prefer a .ui next to the module (same folder, same stem) in dev.
    - In frozen mode, try under sys._MEIPASS with both 'components/...' and 'src/components/...'
      keeping the relative path after the 'components' folder if present.
    - Fall back to common locations under MEIPASS.
    """
    p = Path(module_file)
    if ui_filename is None:
        ui_filename = p.with_suffix('.ui').name

    # 1) Next to the module
    candidates = [p.with_suffix('.ui'), p.parent / ui_filename]

    # 2) If frozen, try MEIPASS variants
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', None)
        if base:
            parts = p.parts
            after_components = None
            if 'components' in parts:
                try:
                    idx = parts.index('components')
                    after_components = Path(*parts[idx:]).with_suffix('.ui')
                except Exception:
                    after_components = None
            base_path = Path(base)
            # components/... and src/components/...
            if after_components:
                candidates.append(base_path / after_components)
                candidates.append(base_path / 'src' / after_components)
            # Generic fallbacks
            candidates.append(base_path / 'components' / ui_filename)
            candidates.append(base_path / 'src' / 'components' / ui_filename)

    for c in candidates:
        try:
            if c and os.path.exists(str(c)):
                return str(c)
        except Exception:
            continue

    # Last resort: return default path (may raise later if missing)
    return str(p.with_suffix('.ui'))
