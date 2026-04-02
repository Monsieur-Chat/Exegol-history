# -*- mode: python ; coding: utf-8 -*-
# Build (from repo root, with Poetry env active):
#   poetry install
#   poetry run pip install pyinstaller
#   poetry run pyinstaller packaging/exegol-history.spec
# Binary: dist/exegol-history
#
# PyInstaller bundles the interpreter; expect ~40–80 MB for onefile.

from pathlib import Path

try:
    from PyInstaller.utils.hooks import collect_all, copy_metadata
except ImportError as e:
    raise SystemExit(
        "PyInstaller is required. Install with: poetry run pip install pyinstaller"
    ) from e


def _repo_paths() -> tuple[Path, Path, Path]:
    """PyInstaller does not define __file__ when executing the spec — use cwd."""
    cwd = Path.cwd().resolve()
    if (cwd / "pyproject.toml").is_file() and (cwd / "packaging" / "pyinstaller_entry.py").is_file():
        root = cwd
    elif cwd.name == "packaging" and (cwd / "pyinstaller_entry.py").is_file():
        root = cwd.parent
    else:
        raise SystemExit(
            "Run PyInstaller from the repository root, e.g.\n"
            "  cd /path/to/Exegol-history && poetry run pyinstaller packaging/exegol-history.spec"
        )
    packaging = root / "packaging"
    entry = packaging / "pyinstaller_entry.py"
    if not entry.is_file():
        raise SystemExit(f"Missing entry script: {entry}")
    return root, packaging, entry


ROOT, PACKAGING, ENTRY = _repo_paths()

datas = []
binaries = []
hiddenimports = []

for pkg in ("textual", "rich", "exegol_history", "sqlalchemy"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

for pkg in (
    "pykeepass",
    "pyperclip",
    "psycopg",
    "psycopg_binary",
    "psycopg_pool",
    "yaml",
    "argcomplete",
    "tomlkit",
):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        pass

try:
    datas += copy_metadata("exegol-history")
except Exception:
    pass

block_cipher = None

a = Analysis(
    [str(ENTRY)],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports
    + [
        "sqlalchemy.dialects.sqlite",
        "sqlite3",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="exegol-history",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
