#!/usr/bin/env python3
"""
Build script for creating executable files.

This script uses PyInstaller to create standalone executables
for Windows, macOS, and Linux.

Usage:
    python build_exe.py          # Build for current platform
    python build_exe.py --onefile # Single file executable
    python build_exe.py --clean   # Clean build artifacts first
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


def clean_build():
    """Remove previous build artifacts."""
    dirs_to_remove = ["build", "dist", "__pycache__"]
    files_to_remove = ["*.spec"]

    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"Removing {dir_name}/...")
            shutil.rmtree(dir_name)

    for pattern in files_to_remove:
        for file_path in Path(".").glob(pattern):
            print(f"Removing {file_path}...")
            file_path.unlink()

    # Clean __pycache__ in subdirectories
    for cache_dir in Path(".").rglob("__pycache__"):
        print(f"Removing {cache_dir}/...")
        shutil.rmtree(cache_dir)


def build_executable(onefile=False, debug=False):
    """Build the executable using PyInstaller."""

    # Base PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=AnimeCharacterCrawler",
        "--windowed",  # No console window
        "--noconfirm",  # Overwrite without asking
    ]

    # Single file or directory
    if onefile:
        cmd.append("--onefile")
    else:
        cmd.append("--onedir")

    # Add icon if exists
    icon_path = Path("assets/icon.ico")
    if icon_path.exists():
        cmd.extend(["--icon", str(icon_path)])

    # Hidden imports for PyQt6
    hidden_imports = [
        "PyQt6.QtWidgets",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "requests",
        "PIL",
    ]

    for imp in hidden_imports:
        cmd.extend(["--hidden-import", imp])

    # Include data files
    cmd.extend([
        "--add-data", f"gui{os.pathsep}gui",
    ])

    # Debug mode
    if debug:
        cmd.append("--debug=all")

    # Entry point
    cmd.append("app.py")

    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")
    print()

    # Run PyInstaller
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print()
        print("=" * 50)
        print("Build successful!")
        print("=" * 50)

        if onefile:
            exe_path = Path("dist/AnimeCharacterCrawler")
            if sys.platform == "win32":
                exe_path = exe_path.with_suffix(".exe")
            print(f"Executable: {exe_path}")
        else:
            print(f"Executable folder: dist/AnimeCharacterCrawler/")

        print()
        print("To run the application:")
        if sys.platform == "win32":
            print("  dist\\AnimeCharacterCrawler\\AnimeCharacterCrawler.exe")
        else:
            print("  ./dist/AnimeCharacterCrawler/AnimeCharacterCrawler")
    else:
        print()
        print("Build failed!")
        sys.exit(1)


def create_spec_file():
    """Create a PyInstaller spec file for more control."""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('gui', 'gui'),
    ],
    hiddenimports=[
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'requests',
        'PIL',
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
    [],
    exclude_binaries=True,
    name='AnimeCharacterCrawler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AnimeCharacterCrawler',
)

# For macOS app bundle (optional)
# app = BUNDLE(
#     coll,
#     name='AnimeCharacterCrawler.app',
#     icon=None,
#     bundle_identifier='com.animecrawler.app',
# )
'''

    with open("AnimeCharacterCrawler.spec", "w") as f:
        f.write(spec_content)

    print("Created AnimeCharacterCrawler.spec")
    print("To build using the spec file:")
    print("  pyinstaller AnimeCharacterCrawler.spec")


def main():
    parser = argparse.ArgumentParser(
        description="Build Anime Character Crawler executable"
    )
    parser.add_argument(
        "--onefile", "-o",
        action="store_true",
        help="Create a single executable file"
    )
    parser.add_argument(
        "--clean", "-c",
        action="store_true",
        help="Clean build artifacts before building"
    )
    parser.add_argument(
        "--spec-only", "-s",
        action="store_true",
        help="Only create the spec file, don't build"
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Build with debug information"
    )

    args = parser.parse_args()

    # Change to project directory
    os.chdir(Path(__file__).parent)

    if args.clean:
        clean_build()

    if args.spec_only:
        create_spec_file()
    else:
        build_executable(onefile=args.onefile, debug=args.debug)


if __name__ == "__main__":
    main()
