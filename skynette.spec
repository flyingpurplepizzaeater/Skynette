# -*- mode: python ; coding: utf-8 -*-
"""
Skynette PyInstaller Spec File.

Bundles the application with all dependencies for Windows distribution.
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Get the project root
project_root = os.path.dirname(os.path.abspath(SPEC))

# Collect all source files
src_path = os.path.join(project_root, 'src')

# Data files to include
datas = [
    # Include entire src directory as data
    (src_path, 'src'),
]

# Check for assets/icons if they exist
assets_path = os.path.join(project_root, 'assets')
if os.path.exists(assets_path):
    datas.append((assets_path, 'assets'))

# Hidden imports that PyInstaller might miss
hiddenimports = [
    # Flet and Flutter
    'flet',
    'flet_core',
    'flet_runtime',

    # Core dependencies
    'pydantic',
    'pydantic_core',
    'httpx',
    'httpcore',
    'anyio',
    'sniffio',
    'certifi',
    'h11',
    'h2',
    'hpack',
    'hyperframe',

    # Async
    'asyncio',
    'aiofiles',

    # Data handling
    'json',
    'yaml',
    'pyyaml',
    'hashlib',
    'base64',

    # AI providers
    'openai',
    'anthropic',

    # Cloud services
    'boto3',
    'botocore',
    's3transfer',

    # Google APIs
    'google.auth',
    'google.oauth2',
    'google_auth_oauthlib',
    'googleapiclient',

    # Email
    'email',
    'smtplib',
    'imaplib',

    # Standard library modules
    'sqlite3',
    'datetime',
    'uuid',
    're',
    'pathlib',
    'logging',
    'typing',
    'dataclasses',
    'enum',

    # All src modules
    'src',
    'src.core',
    'src.core.engine',
    'src.core.workflow',
    'src.core.workflow.models',
    'src.core.workflow.executor',
    'src.core.nodes',
    'src.core.nodes.base',
    'src.core.nodes.registry',
    'src.core.nodes.ai',
    'src.core.nodes.apps',
    'src.core.nodes.utility',
    'src.core.nodes.triggers',
    'src.core.nodes.http',
    'src.core.nodes.flow',
    'src.core.nodes.data',
    'src.core.nodes.coding',
    'src.core.expressions',
    'src.core.expressions.parser',
    'src.ai',
    'src.ai.gateway',
    'src.ai.models',
    'src.ai.models.hub',
    'src.ai.providers',
    'src.ai.providers.base',
    'src.ai.providers.local',
    'src.ai.providers.openai',
    'src.ai.providers.anthropic',
    'src.ai.providers.demo',
    'src.ai.assistant',
    'src.ai.assistant.skynet',
    'src.ui',
    'src.ui.app',
    'src.ui.theme',
    'src.ui.components',
    'src.ui.views',
    'src.ui.views.workflows',
    'src.ui.views.workflow_editor',
    'src.ui.views.simple_mode',
    'src.ui.views.ai_hub',
    'src.ui.views.plugins',
    'src.ui.views.runs',
    'src.ui.views.settings',
    'src.storage',
]

a = Analysis(
    ['main.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
    ],
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
    name='Skynette',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(project_root, 'assets', 'icon.ico') if os.path.exists(os.path.join(project_root, 'assets', 'icon.ico')) else None,
)
