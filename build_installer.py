"""
Cross-Platform Installer Build Script for Skynette.

Creates proper installers for:
- Windows: MSI installer (via WiX or NSIS fallback)
- Linux: AppImage and .deb package
- macOS: DMG with .app bundle

Usage:
    python build_installer.py [platform] [--msi] [--portable]

    platform: windows, linux, macos, all (default: current platform)
    --msi: Build MSI installer on Windows (requires WiX)
    --portable: Also create portable ZIP
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Version info
VERSION = "1.0.0"
APP_NAME = "Skynette"
APP_ID = "com.skynette.app"
DESCRIPTION = "AI-Native Workflow Automation Platform"


class InstallerBuilder:
    """Cross-platform installer builder."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dist_dir = project_root / "dist"
        self.build_dir = project_root / "build"
        self.installer_dir = project_root / "installer"
        self.current_platform = platform.system().lower()

    def clean(self):
        """Clean previous builds."""
        print("Cleaning previous builds...")
        for folder in [self.dist_dir, self.build_dir]:
            if folder.exists():
                shutil.rmtree(folder)
        self.dist_dir.mkdir(exist_ok=True)
        self.build_dir.mkdir(exist_ok=True)

    def check_dependencies(self):
        """Check and install Python dependencies."""
        print("Checking Python dependencies...")
        deps = [
            "pyinstaller>=6.0.0",
            "flet>=0.21.0",
            "pydantic>=2.0.0",
            "httpx>=0.25.0",
            "aiofiles>=23.0.0",
            "pyyaml>=6.0",
            "python-dotenv>=1.0.0",
            "openai>=1.0.0",
            "anthropic>=0.18.0",
            "boto3>=1.28.0",
            "google-auth>=2.0.0",
            "google-auth-oauthlib>=1.0.0",
            "google-api-python-client>=2.0.0",
        ]

        for dep in deps:
            pkg_name = dep.split(">=")[0].split("[")[0].replace("-", "_")
            try:
                __import__(pkg_name)
            except ImportError:
                print(f"  Installing {dep}...")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep, "-q"],
                    check=True
                )

    def build_executable(self) -> bool:
        """Build the main executable with PyInstaller."""
        print("\nBuilding executable...")

        spec_content = self._generate_spec()
        spec_path = self.project_root / "skynette.spec"
        spec_path.write_text(spec_content)

        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", str(spec_path), "--clean", "--noconfirm"],
            cwd=self.project_root
        )

        return result.returncode == 0

    def _generate_spec(self) -> str:
        """Generate PyInstaller spec file."""
        icon_ext = ".ico" if self.current_platform == "windows" else ".icns"
        icon_path = self.project_root / "assets" / f"icon{icon_ext}"
        icon_line = f"icon=r'{icon_path}'," if icon_path.exists() else ""

        console = "False" if self.current_platform != "linux" else "False"

        return f'''# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None
project_root = r'{self.project_root}'

datas = [
    (os.path.join(project_root, 'src'), 'src'),
]

assets_path = os.path.join(project_root, 'assets')
if os.path.exists(assets_path):
    datas.append((assets_path, 'assets'))

hiddenimports = [
    'flet', 'pydantic', 'pydantic_core', 'httpx', 'httpcore',
    'anyio', 'sniffio', 'certifi', 'h11', 'aiofiles',
    'yaml', 'openai', 'anthropic', 'boto3', 'botocore',
    'google.auth', 'google.oauth2', 'google_auth_oauthlib', 'googleapiclient',
    'email', 'smtplib', 'imaplib', 'sqlite3',
    'src', 'src.core', 'src.core.workflow', 'src.core.nodes',
    'src.core.nodes.base', 'src.core.nodes.ai', 'src.core.nodes.apps',
    'src.core.nodes.utility', 'src.ai', 'src.ai.gateway',
    'src.ai.models', 'src.ai.providers', 'src.ui', 'src.ui.app',
]

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas', 'scipy'],
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
    name='{APP_NAME}',
    debug=False,
    strip=False,
    upx=True,
    runtime_tmpdir=None,
    console={console},
    {icon_line}
)
'''

    # =========================================================================
    # Windows MSI Builder
    # =========================================================================

    def build_windows_msi(self) -> bool:
        """Build Windows MSI installer using WiX or NSIS."""
        print("\nBuilding Windows MSI installer...")

        exe_path = self.dist_dir / f"{APP_NAME}.exe"
        if not exe_path.exists():
            print("  Error: Executable not found. Build it first.")
            return False

        # Try WiX first
        if self._check_wix():
            return self._build_with_wix()

        # Try NSIS as fallback
        if self._check_nsis():
            return self._build_with_nsis()

        # Use Inno Setup style script with iscc or create simple installer
        print("  WiX/NSIS not found. Creating Inno Setup script...")
        return self._create_inno_script()

    def _check_wix(self) -> bool:
        """Check if WiX Toolset is installed."""
        try:
            result = subprocess.run(["candle", "-?"], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _check_nsis(self) -> bool:
        """Check if NSIS is installed."""
        try:
            result = subprocess.run(["makensis", "/VERSION"], capture_output=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _build_with_wix(self) -> bool:
        """Build MSI using WiX Toolset."""
        print("  Using WiX Toolset...")

        wxs_path = self.installer_dir / "windows" / "skynette.wxs"
        if not wxs_path.exists():
            print(f"  Error: WiX source file not found at {wxs_path}")
            return False

        # Compile
        obj_path = self.build_dir / "skynette.wixobj"
        result = subprocess.run([
            "candle", str(wxs_path),
            "-out", str(obj_path),
            f"-dProjectDir={self.project_root}"
        ])
        if result.returncode != 0:
            return False

        # Link
        msi_path = self.dist_dir / f"{APP_NAME}-{VERSION}-setup.msi"
        result = subprocess.run([
            "light", str(obj_path),
            "-out", str(msi_path),
            "-ext", "WixUIExtension"
        ])

        if result.returncode == 0:
            print(f"  Created: {msi_path}")
            return True
        return False

    def _build_with_nsis(self) -> bool:
        """Build installer using NSIS."""
        print("  Using NSIS...")

        nsi_content = self._generate_nsis_script()
        nsi_path = self.build_dir / "skynette.nsi"
        nsi_path.write_text(nsi_content)

        result = subprocess.run(["makensis", str(nsi_path)])

        if result.returncode == 0:
            print(f"  Created: {self.dist_dir / f'{APP_NAME}-{VERSION}-setup.exe'}")
            return True
        return False

    def _generate_nsis_script(self) -> str:
        """Generate NSIS installer script."""
        return f'''
!include "MUI2.nsh"

Name "{APP_NAME}"
OutFile "{self.dist_dir}\\{APP_NAME}-{VERSION}-setup.exe"
InstallDir "$PROGRAMFILES64\\{APP_NAME}"
RequestExecutionLevel admin

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "{self.installer_dir}\\windows\\license.rtf"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Section "Install"
    SetOutPath "$INSTDIR"
    File "{self.dist_dir}\\{APP_NAME}.exe"
    File "{self.dist_dir}\\README.txt"

    CreateDirectory "$SMPROGRAMS\\{APP_NAME}"
    CreateShortcut "$SMPROGRAMS\\{APP_NAME}\\{APP_NAME}.lnk" "$INSTDIR\\{APP_NAME}.exe"
    CreateShortcut "$DESKTOP\\{APP_NAME}.lnk" "$INSTDIR\\{APP_NAME}.exe"

    WriteUninstaller "$INSTDIR\\uninstall.exe"

    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "DisplayName" "{APP_NAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" "DisplayVersion" "{VERSION}"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\\{APP_NAME}.exe"
    Delete "$INSTDIR\\README.txt"
    Delete "$INSTDIR\\uninstall.exe"
    RMDir "$INSTDIR"

    Delete "$SMPROGRAMS\\{APP_NAME}\\{APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\\{APP_NAME}"
    Delete "$DESKTOP\\{APP_NAME}.lnk"

    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}"
SectionEnd
'''

    def _create_inno_script(self) -> bool:
        """Create Inno Setup script for manual building."""
        print("  Creating Inno Setup script (build manually with Inno Setup)...")

        iss_content = f'''[Setup]
AppName={APP_NAME}
AppVersion={VERSION}
AppPublisher=Skynette
AppPublisherURL=https://github.com/skynette/skynette
DefaultDirName={{autopf}}\\{APP_NAME}
DefaultGroupName={APP_NAME}
OutputDir={self.dist_dir}
OutputBaseFilename={APP_NAME}-{VERSION}-setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
PrivilegesRequired=admin

[Files]
Source: "{self.dist_dir}\\{APP_NAME}.exe"; DestDir: "{{app}}"; Flags: ignoreversion
Source: "{self.dist_dir}\\README.txt"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"
Name: "{{commondesktop}}\\{APP_NAME}"; Filename: "{{app}}\\{APP_NAME}.exe"

[Run]
Filename: "{{app}}\\{APP_NAME}.exe"; Description: "Launch {APP_NAME}"; Flags: nowait postinstall skipifsilent
'''

        iss_path = self.dist_dir / f"{APP_NAME}-setup.iss"
        iss_path.write_text(iss_content)
        print(f"  Created: {iss_path}")
        print("  To build MSI: Install Inno Setup and compile the .iss file")

        # Also try iscc if available
        try:
            result = subprocess.run(
                ["iscc", str(iss_path)],
                capture_output=True
            )
            if result.returncode == 0:
                print(f"  Created: {self.dist_dir / f'{APP_NAME}-{VERSION}-setup.exe'}")
                return True
        except FileNotFoundError:
            pass

        return True  # Script created successfully

    # =========================================================================
    # Linux Builder
    # =========================================================================

    def build_linux_appimage(self) -> bool:
        """Build Linux AppImage."""
        print("\nBuilding Linux AppImage...")

        exe_path = self.dist_dir / APP_NAME
        if not exe_path.exists():
            print("  Error: Executable not found. Build it first.")
            return False

        # Create AppDir structure
        appdir = self.build_dir / f"{APP_NAME}.AppDir"
        appdir.mkdir(parents=True, exist_ok=True)

        # Copy executable
        usr_bin = appdir / "usr" / "bin"
        usr_bin.mkdir(parents=True, exist_ok=True)
        shutil.copy(exe_path, usr_bin / APP_NAME)
        (usr_bin / APP_NAME).chmod(0o755)

        # Create desktop file
        desktop_content = f"""[Desktop Entry]
Name={APP_NAME}
Exec={APP_NAME}
Icon={APP_NAME.lower()}
Type=Application
Categories=Development;Utility;
Comment={DESCRIPTION}
"""
        (appdir / f"{APP_NAME.lower()}.desktop").write_text(desktop_content)

        # Create AppRun
        apprun_content = f"""#!/bin/bash
SELF=$(readlink -f "$0")
HERE=${{SELF%/*}}
export PATH="${{HERE}}/usr/bin:${{PATH}}"
exec "${{HERE}}/usr/bin/{APP_NAME}" "$@"
"""
        apprun_path = appdir / "AppRun"
        apprun_path.write_text(apprun_content)
        apprun_path.chmod(0o755)

        # Create simple icon (placeholder)
        icon_dir = appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
        icon_dir.mkdir(parents=True, exist_ok=True)

        # Try to download appimagetool
        print("  Downloading appimagetool...")
        appimagetool = self.build_dir / "appimagetool"
        try:
            subprocess.run([
                "curl", "-L", "-o", str(appimagetool),
                "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
            ], check=True)
            appimagetool.chmod(0o755)

            # Build AppImage
            appimage_path = self.dist_dir / f"{APP_NAME}-{VERSION}-x86_64.AppImage"
            subprocess.run([
                str(appimagetool), str(appdir), str(appimage_path)
            ], check=True, env={**os.environ, "ARCH": "x86_64"})

            print(f"  Created: {appimage_path}")
            return True

        except Exception as e:
            print(f"  AppImage creation failed: {e}")
            print("  AppDir created at:", appdir)
            return False

    def build_linux_deb(self) -> bool:
        """Build Debian .deb package."""
        print("\nBuilding Linux .deb package...")

        exe_path = self.dist_dir / APP_NAME
        if not exe_path.exists():
            print("  Error: Executable not found. Build it first.")
            return False

        # Create debian package structure
        pkg_name = APP_NAME.lower()
        deb_dir = self.build_dir / f"{pkg_name}_{VERSION}_amd64"
        deb_dir.mkdir(parents=True, exist_ok=True)

        # DEBIAN control
        debian_dir = deb_dir / "DEBIAN"
        debian_dir.mkdir(exist_ok=True)

        control_content = f"""Package: {pkg_name}
Version: {VERSION}
Section: devel
Priority: optional
Architecture: amd64
Maintainer: Skynette <hello@skynette.io>
Description: {DESCRIPTION}
 AI-native workflow automation platform with multi-AI model support.
 Open-source alternative to n8n with visual workflow builder.
"""
        (debian_dir / "control").write_text(control_content)

        # Copy binary
        usr_bin = deb_dir / "usr" / "bin"
        usr_bin.mkdir(parents=True, exist_ok=True)
        shutil.copy(exe_path, usr_bin / pkg_name)
        (usr_bin / pkg_name).chmod(0o755)

        # Desktop file
        apps_dir = deb_dir / "usr" / "share" / "applications"
        apps_dir.mkdir(parents=True, exist_ok=True)
        desktop_content = f"""[Desktop Entry]
Name={APP_NAME}
Exec={pkg_name}
Icon={pkg_name}
Type=Application
Categories=Development;Utility;
Comment={DESCRIPTION}
"""
        (apps_dir / f"{pkg_name}.desktop").write_text(desktop_content)

        # Build .deb
        deb_path = self.dist_dir / f"{pkg_name}_{VERSION}_amd64.deb"
        try:
            subprocess.run(["dpkg-deb", "--build", str(deb_dir), str(deb_path)], check=True)
            print(f"  Created: {deb_path}")
            return True
        except FileNotFoundError:
            print("  dpkg-deb not found. Install dpkg to build .deb packages.")
            return False

    # =========================================================================
    # macOS Builder
    # =========================================================================

    def build_macos_dmg(self) -> bool:
        """Build macOS DMG installer."""
        print("\nBuilding macOS DMG...")

        app_path = self.dist_dir / f"{APP_NAME}.app"
        if not app_path.exists():
            print("  Error: .app bundle not found. Build it first.")
            return False

        dmg_path = self.dist_dir / f"{APP_NAME}-{VERSION}.dmg"

        # Create DMG
        try:
            # Create temporary DMG folder
            dmg_temp = self.build_dir / "dmg_temp"
            dmg_temp.mkdir(exist_ok=True)

            # Copy app to temp folder
            shutil.copytree(app_path, dmg_temp / f"{APP_NAME}.app")

            # Create symlink to Applications
            apps_link = dmg_temp / "Applications"
            if not apps_link.exists():
                os.symlink("/Applications", apps_link)

            # Create DMG
            subprocess.run([
                "hdiutil", "create",
                "-volname", APP_NAME,
                "-srcfolder", str(dmg_temp),
                "-ov",
                "-format", "UDZO",
                str(dmg_path)
            ], check=True)

            print(f"  Created: {dmg_path}")
            return True

        except Exception as e:
            print(f"  DMG creation failed: {e}")
            return False

    def build_macos_app(self) -> bool:
        """Build macOS .app bundle using PyInstaller."""
        print("\nBuilding macOS .app bundle...")

        # Modify spec for macOS bundle
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None
project_root = r'{self.project_root}'

datas = [
    (os.path.join(project_root, 'src'), 'src'),
]

assets_path = os.path.join(project_root, 'assets')
if os.path.exists(assets_path):
    datas.append((assets_path, 'assets'))

hiddenimports = [
    'flet', 'pydantic', 'pydantic_core', 'httpx', 'httpcore',
    'anyio', 'sniffio', 'certifi', 'h11', 'aiofiles',
    'yaml', 'openai', 'anthropic', 'boto3', 'botocore',
    'google.auth', 'google.oauth2', 'google_auth_oauthlib', 'googleapiclient',
    'src', 'src.core', 'src.core.workflow', 'src.core.nodes',
    'src.ui', 'src.ui.app', 'src.ai', 'src.ai.gateway',
]

a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=['tkinter', 'matplotlib', 'numpy', 'pandas'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='{APP_NAME}',
    debug=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='{APP_NAME}',
)

app = BUNDLE(
    coll,
    name='{APP_NAME}.app',
    icon=os.path.join(project_root, 'assets', 'icon.icns') if os.path.exists(os.path.join(project_root, 'assets', 'icon.icns')) else None,
    bundle_identifier='{APP_ID}',
    info_plist={{
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '{VERSION}',
    }},
)
'''

        spec_path = self.project_root / "skynette_macos.spec"
        spec_path.write_text(spec_content)

        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", str(spec_path), "--clean", "--noconfirm"],
            cwd=self.project_root
        )

        return result.returncode == 0

    # =========================================================================
    # Portable ZIP
    # =========================================================================

    def create_portable_zip(self) -> bool:
        """Create portable ZIP distribution."""
        print("\nCreating portable ZIP...")

        exe_name = f"{APP_NAME}.exe" if self.current_platform == "windows" else APP_NAME
        exe_path = self.dist_dir / exe_name

        if not exe_path.exists():
            print("  Error: Executable not found.")
            return False

        zip_name = f"{APP_NAME}-{VERSION}-{self.current_platform}-portable"
        zip_path = self.dist_dir / zip_name

        shutil.make_archive(str(zip_path), "zip", self.dist_dir, exe_name)

        print(f"  Created: {zip_path}.zip")
        return True

    # =========================================================================
    # Main Build Methods
    # =========================================================================

    def build_windows(self, msi: bool = True, portable: bool = True) -> bool:
        """Build Windows installers."""
        print("\n" + "="*60)
        print("Building for Windows")
        print("="*60)

        success = True

        # Build executable
        if not self.build_executable():
            print("Failed to build executable!")
            return False

        # Create README
        self._create_readme()

        # Build MSI
        if msi:
            if not self.build_windows_msi():
                print("MSI build had issues, but continuing...")

        # Create portable ZIP
        if portable:
            self.create_portable_zip()

        return success

    def build_linux(self, appimage: bool = True, deb: bool = True) -> bool:
        """Build Linux packages."""
        print("\n" + "="*60)
        print("Building for Linux")
        print("="*60)

        # Build executable
        if not self.build_executable():
            print("Failed to build executable!")
            return False

        self._create_readme()

        if appimage:
            self.build_linux_appimage()

        if deb:
            self.build_linux_deb()

        return True

    def build_macos(self, dmg: bool = True) -> bool:
        """Build macOS packages."""
        print("\n" + "="*60)
        print("Building for macOS")
        print("="*60)

        # Build .app bundle
        if not self.build_macos_app():
            print("Failed to build .app bundle!")
            return False

        self._create_readme()

        if dmg:
            self.build_macos_dmg()

        return True

    def _create_readme(self):
        """Create README file."""
        readme = f"""# {APP_NAME} v{VERSION}

{DESCRIPTION}

## Installation

### Windows
- Run the installer (.msi or setup.exe)
- Or extract the portable ZIP and run {APP_NAME}.exe

### Linux
- AppImage: Make executable and run
  chmod +x {APP_NAME}-*.AppImage && ./{APP_NAME}-*.AppImage
- Debian/Ubuntu: sudo dpkg -i {APP_NAME.lower()}_*.deb

### macOS
- Open the DMG and drag {APP_NAME} to Applications

## Getting Started

1. Launch {APP_NAME}
2. Create a new workflow
3. Add nodes from the sidebar
4. Connect nodes to build your automation
5. Click Run to execute

## Features

- Visual workflow builder
- 50+ integration nodes
- Multi-AI support (OpenAI, Anthropic, Local)
- Git, Docker, and CI/CD integrations
- Cross-platform

## Documentation

https://docs.skynette.io

## License

MIT License
"""
        (self.dist_dir / "README.txt").write_text(readme)


def main():
    parser = argparse.ArgumentParser(description="Build Skynette installers")
    parser.add_argument("platform", nargs="?", default="auto",
                       choices=["windows", "linux", "macos", "all", "auto"],
                       help="Target platform (default: current)")
    parser.add_argument("--msi", action="store_true", help="Build MSI (Windows)")
    parser.add_argument("--portable", action="store_true", help="Create portable ZIP")
    parser.add_argument("--no-clean", action="store_true", help="Don't clean build dirs")

    args = parser.parse_args()

    project_root = Path(__file__).parent
    os.chdir(project_root)

    builder = InstallerBuilder(project_root)

    # Determine platform
    if args.platform == "auto":
        args.platform = builder.current_platform

    print("="*60)
    print(f"{APP_NAME} Installer Builder v{VERSION}")
    print("="*60)
    print(f"Project: {project_root}")
    print(f"Platform: {args.platform}")

    # Clean
    if not args.no_clean:
        builder.clean()

    # Check dependencies
    builder.check_dependencies()

    # Build
    if args.platform in ["windows", "all"]:
        builder.build_windows(msi=True, portable=True)

    if args.platform in ["linux", "all"]:
        builder.build_linux(appimage=True, deb=True)

    if args.platform in ["macos", "all"]:
        builder.build_macos(dmg=True)

    print("\n" + "="*60)
    print("Build complete!")
    print(f"Output: {builder.dist_dir}")
    print("="*60)


if __name__ == "__main__":
    main()
