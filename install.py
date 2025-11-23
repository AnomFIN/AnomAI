#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AnomAI/JugiAI Unified Cross-Platform Installer
==============================================

This is the authoritative installer for AnomAI/JugiAI that works on:
- Windows (10/11 x64)
- Linux (Ubuntu, Debian, Fedora, etc.)
- macOS (Intel and Apple Silicon)

Usage:
    python install.py [options]

Options:
    --help              Show this help message
    --no-venv          Skip virtual environment creation
    --no-llama         Skip llama-cpp-python installation
    --no-exe           Skip executable build (Windows only)
    --no-shortcut      Skip desktop shortcut creation
    --no-interactive   Run in non-interactive mode with defaults
    --verbose          Enable verbose output
    --force            Force reinstallation even if already installed

Requirements:
    - Python 3.10+ (64-bit recommended)
    - Internet connection (for package installation)
    - ~1GB free disk space

This installer replaces all legacy installation scripts and provides
a consistent experience across all platforms.
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union


class Colors:
    """ANSI color codes for cross-platform terminal output."""
    if platform.system() == "Windows":
        # Enable ANSI colors on Windows 10+
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except Exception:
            pass
    
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"


class InstallError(Exception):
    """Custom exception for installation errors."""
    pass


class AnomAIInstaller:
    """Cross-platform installer for AnomAI/JugiAI."""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.root_dir = Path(__file__).parent.absolute()
        self.venv_dir = self.root_dir / ".venv"
        self.is_windows = platform.system() == "Windows"
        self.is_macos = platform.system() == "Darwin"
        self.is_linux = platform.system() == "Linux"
        self.python_exe = self._find_python()
        
        # Installation state
        self.venv_created = False
        self.requirements_installed = False
        self.llama_installed = False
        self.exe_built = False
        self.shortcut_created = False
    
    def _find_python(self) -> str:
        """Find the best Python executable for this platform."""
        candidates = []
        
        if self.is_windows:
            candidates = ["python", "py -3", "python3"]
        else:
            candidates = ["python3", "python"]
        
        for cmd in candidates:
            try:
                result = subprocess.run(
                    f"{cmd} --version".split(),
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Check version is 3.10+
                    version_str = result.stdout.strip()
                    if "Python 3." in version_str:
                        version_parts = version_str.split()[1].split('.')
                        major, minor = int(version_parts[0]), int(version_parts[1])
                        if major == 3 and minor >= 10:
                            return cmd
                        elif major > 3:
                            return cmd
            except Exception:
                continue
        
        raise InstallError(
            f"Python 3.10+ not found. Please install Python 3.10 or newer.\n"
            f"Download from: https://www.python.org/downloads/"
        )
    
    def _run_cmd(self, cmd: Union[str, List[str]], **kwargs) -> subprocess.CompletedProcess:
        """Run a command with proper error handling."""
        if isinstance(cmd, str):
            cmd = cmd.split()
        
        if self.args.verbose:
            self.print_status(f"Running: {' '.join(cmd)}", Colors.BLUE)
        
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=not self.args.verbose,
                text=True,
                **kwargs
            )
            return result
        except subprocess.CalledProcessError as e:
            error_msg = f"Command failed: {' '.join(cmd)}"
            if e.stderr:
                error_msg += f"\nError: {e.stderr}"
            raise InstallError(error_msg) from e
    
    def print_status(self, message: str, color: str = Colors.GREEN) -> None:
        """Print a colored status message."""
        print(f"{color}[AnomAI] {message}{Colors.RESET}")
    
    def print_header(self, title: str) -> None:
        """Print a section header."""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}{Colors.RESET}\n")
    
    def check_system_requirements(self) -> None:
        """Verify system meets minimum requirements."""
        self.print_header("System Requirements Check")
        
        # Check Python version and architecture
        result = self._run_cmd([self.python_exe, "-c", 
            "import sys, struct; "
            "print(f'{sys.version_info.major}.{sys.version_info.minor}'); "
            "print(f'{struct.calcsize(\"P\")*8}bit')"
        ])
        
        lines = result.stdout.strip().split('\n')
        py_version = lines[0]
        py_arch = lines[1]
        
        self.print_status(f"Python {py_version} ({py_arch}) detected")
        
        # Check architecture for PyInstaller compatibility
        if "32bit" in py_arch and not self.args.no_exe:
            self.print_status(
                "WARNING: 32-bit Python detected. Executable builds may fail. "
                "Consider using 64-bit Python for best results.",
                Colors.YELLOW
            )
        
        # Check available disk space
        try:
            free_space = shutil.disk_usage(self.root_dir).free // (1024**3)  # GB
            if free_space < 1:
                self.print_status(
                    f"WARNING: Only {free_space}GB free space. Installation may fail.",
                    Colors.YELLOW
                )
        except Exception:
            pass
        
        # Check if tkinter is available
        try:
            self._run_cmd([self.python_exe, "-c", "import tkinter"])
            self.print_status("tkinter GUI library available")
        except InstallError:
            error_msg = "tkinter not available. "
            if self.is_linux:
                error_msg += "Install with: sudo apt-get install python3-tk"
            elif self.is_macos:
                error_msg += "Install with: brew install python-tk"
            else:
                error_msg += "Please reinstall Python with tkinter support."
            raise InstallError(error_msg)
    
    def create_virtual_environment(self) -> None:
        """Create and activate virtual environment."""
        if self.args.no_venv:
            self.print_status("Skipping virtual environment creation")
            return
        
        self.print_header("Virtual Environment Setup")
        
        if self.venv_dir.exists():
            if self.args.force:
                self.print_status("Removing existing virtual environment")
                shutil.rmtree(self.venv_dir)
            else:
                self.print_status("Using existing virtual environment")
                self.venv_created = True
                return
        
        self.print_status("Creating virtual environment...")
        venv.create(self.venv_dir, with_pip=True)
        self.venv_created = True
        self.print_status("Virtual environment created successfully")
    
    def get_venv_python(self) -> str:
        """Get the Python executable path for the virtual environment."""
        if self.args.no_venv:
            return self.python_exe
        
        if self.is_windows:
            return str(self.venv_dir / "Scripts" / "python.exe")
        else:
            return str(self.venv_dir / "bin" / "python")
    
    def install_requirements(self) -> None:
        """Install Python package requirements."""
        self.print_header("Installing Requirements")
        
        venv_python = self.get_venv_python()
        
        # Upgrade pip first
        self.print_status("Upgrading pip...")
        self._run_cmd([venv_python, "-m", "pip", "install", "--upgrade", 
                      "pip", "setuptools", "wheel"])
        
        # Install requirements.txt if it exists
        requirements_file = self.root_dir / "requirements.txt"
        if requirements_file.exists():
            self.print_status("Installing requirements from requirements.txt...")
            self._run_cmd([venv_python, "-m", "pip", "install", "-r", 
                          str(requirements_file)])
            self.requirements_installed = True
        else:
            self.print_status("No requirements.txt found, installing minimal dependencies")
            # Install Pillow as it's recommended
            self._run_cmd([venv_python, "-m", "pip", "install", "pillow>=8.0.0"])
            self.requirements_installed = True
    
    def install_llama_cpp(self) -> None:
        """Install llama-cpp-python for local model support."""
        if self.args.no_llama:
            self.print_status("Skipping llama-cpp-python installation")
            return
        
        self.print_header("Local Model Support (llama-cpp-python)")
        
        if not self.args.no_interactive:
            response = input(
                f"{Colors.CYAN}Install llama-cpp-python for local GGUF models? "
                f"This enables offline AI without API keys. [Y/n]: {Colors.RESET}"
            ).strip().lower()
            
            if response and response[0] == 'n':
                self.print_status("Skipping llama-cpp-python at user request")
                return
        
        venv_python = self.get_venv_python()
        
        self.print_status("Installing llama-cpp-python (CPU version)...")
        self.print_status("This may take several minutes...", Colors.YELLOW)
        
        try:
            self._run_cmd([
                venv_python, "-m", "pip", "install", 
                "--upgrade", "--prefer-binary", "llama-cpp-python"
            ])
            self.llama_installed = True
            self.print_status("Local model support installed successfully")
            
            if not self.args.no_interactive:
                self.print_status(
                    "For GPU acceleration (CUDA), you can upgrade later with:\n"
                    f"  {self.get_venv_python()} -m pip install llama-cpp-python "
                    "--force-reinstall --no-cache-dir --extra-index-url "
                    "https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu121",
                    Colors.BLUE
                )
        
        except InstallError as e:
            self.print_status(
                f"llama-cpp-python installation failed: {e}\n"
                "You can install it manually later if needed.",
                Colors.YELLOW
            )
    
    def setup_configuration(self) -> None:
        """Set up initial configuration."""
        self.print_header("Configuration Setup")
        
        config_file = self.root_dir / "config.json"
        
        if config_file.exists() and not self.args.force:
            if self.args.no_interactive:
                self.print_status("Using existing configuration")
                return
            
            response = input(
                f"{Colors.CYAN}Configuration already exists. Reconfigure? [y/N]: {Colors.RESET}"
            ).strip().lower()
            
            if not response or response[0] != 'y':
                self.print_status("Keeping existing configuration")
                return
        
        if self.args.no_interactive:
            # Create default configuration
            config = {
                "api_key": "",
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 4000,
                "backend": "local" if self.llama_installed else "openai",
                "offline_mode": False
            }
        else:
            # Interactive configuration
            print(f"{Colors.CYAN}Setting up AnomAI configuration...{Colors.RESET}")
            print("Press ENTER to use default values shown in [brackets]")
            
            api_key = input("\nOpenAI API Key (leave empty for local models only): ").strip()
            
            model = input("OpenAI Model [gpt-4o-mini]: ").strip() or "gpt-4o-mini"
            
            temp_str = input("Temperature (0.0-2.0) [0.7]: ").strip() or "0.7"
            try:
                temperature = float(temp_str)
            except ValueError:
                temperature = 0.7
            
            tokens_str = input("Max Tokens [4000]: ").strip() or "4000"
            try:
                max_tokens = int(tokens_str)
            except ValueError:
                max_tokens = 4000
            
            config = {
                "api_key": api_key,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "backend": "openai" if api_key else "local",
                "offline_mode": False
            }
        
        # Save configuration
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        self.print_status("Configuration saved to config.json")
        
        # Create empty history file
        history_file = self.root_dir / "history.json"
        if not history_file.exists():
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            self.print_status("Created history.json")
    
    def build_executable(self) -> None:
        """Build standalone executable (Windows/Linux/macOS)."""
        if self.args.no_exe:
            self.print_status("Skipping executable build")
            return
        
        self.print_header("Building Executable")
        
        if not self.args.no_interactive:
            response = input(
                f"{Colors.CYAN}Build standalone executable? "
                f"This allows running AnomAI without activating the virtual environment. [Y/n]: {Colors.RESET}"
            ).strip().lower()
            
            if response and response[0] == 'n':
                self.print_status("Skipping executable build at user request")
                return
        
        venv_python = self.get_venv_python()
        
        # Install PyInstaller
        self.print_status("Installing PyInstaller...")
        try:
            self._run_cmd([venv_python, "-m", "pip", "install", "pyinstaller"])
        except InstallError:
            self.print_status("Failed to install PyInstaller, skipping executable build", Colors.YELLOW)
            return
        
        # Build executable
        self.print_status("Building executable (this may take several minutes)...")
        
        build_args = [
            venv_python, "-m", "PyInstaller",
            "--onefile", "--windowed" if self.is_windows else "--onedir",
            "--name", "AnomAI"
        ]
        
        # Add icon if available
        icon_files = ["logo.ico", "icon.ico", "anoma.ico"]
        for icon in icon_files:
            if (self.root_dir / icon).exists():
                build_args.extend(["--icon", str(self.root_dir / icon)])
                break
        
        build_args.append("jugiai.py")
        
        try:
            self._run_cmd(build_args, cwd=self.root_dir)
            
            # Find the built executable
            if self.is_windows:
                exe_path = self.root_dir / "dist" / "AnomAI.exe"
                if exe_path.exists():
                    # Copy to root for easier access
                    shutil.copy2(exe_path, self.root_dir / "AnomAI.exe")
                    self.exe_built = True
                    self.print_status("Executable built successfully: AnomAI.exe")
                else:
                    self.print_status("Executable build completed but file not found", Colors.YELLOW)
            else:
                exe_dir = self.root_dir / "dist" / "AnomAI"
                if exe_dir.exists():
                    self.exe_built = True
                    self.print_status(f"Executable built successfully: {exe_dir}/")
                else:
                    self.print_status("Executable build completed but directory not found", Colors.YELLOW)
        
        except InstallError as e:
            self.print_status(f"Executable build failed: {e}", Colors.YELLOW)
            self.print_status("You can still run AnomAI using the start script", Colors.BLUE)
    
    def create_desktop_shortcut(self) -> None:
        """Create desktop shortcut (Windows/Linux)."""
        if self.args.no_shortcut or self.is_macos:
            return
        
        self.print_header("Desktop Shortcut")
        
        if not self.args.no_interactive:
            response = input(
                f"{Colors.CYAN}Create desktop shortcut? [Y/n]: {Colors.RESET}"
            ).strip().lower()
            
            if response and response[0] == 'n':
                self.print_status("Skipping desktop shortcut creation")
                return
        
        if self.is_windows:
            self._create_windows_shortcut()
        elif self.is_linux:
            self._create_linux_shortcut()
    
    def _create_windows_shortcut(self) -> None:
        """Create Windows desktop shortcut."""
        try:
            # Determine target executable
            if (self.root_dir / "AnomAI.exe").exists():
                target = str(self.root_dir / "AnomAI.exe")
            else:
                target = str(self.root_dir / "start_jugiai.bat")
            
            # Create shortcut using PowerShell
            ps_script = f'''
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\\AnomAI.lnk')
            $Shortcut.TargetPath = '{target}'
            $Shortcut.WorkingDirectory = '{self.root_dir}'
            $Shortcut.Save()
            '''
            
            subprocess.run(["powershell", "-Command", ps_script], 
                         check=True, capture_output=True)
            
            self.shortcut_created = True
            self.print_status("Desktop shortcut created")
            
        except Exception as e:
            self.print_status(f"Failed to create desktop shortcut: {e}", Colors.YELLOW)
    
    def _create_linux_shortcut(self) -> None:
        """Create Linux desktop shortcut (.desktop file)."""
        try:
            desktop_dir = Path.home() / "Desktop"
            if not desktop_dir.exists():
                desktop_dir = Path.home() / ".local" / "share" / "applications"
                desktop_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine executable
            if (self.root_dir / "dist" / "AnomAI").exists():
                exec_path = str(self.root_dir / "dist" / "AnomAI" / "AnomAI")
            else:
                exec_path = f"{self.get_venv_python()} {self.root_dir / 'jugiai.py'}"
            
            # Create .desktop file
            desktop_content = f"""[Desktop Entry]
Name=AnomAI
Comment=AI Chat Application
Exec={exec_path}
Path={self.root_dir}
Terminal=false
Type=Application
Categories=Office;
StartupNotify=true
"""
            
            desktop_file = desktop_dir / "AnomAI.desktop"
            with open(desktop_file, 'w') as f:
                f.write(desktop_content)
            
            # Make executable
            desktop_file.chmod(0o755)
            
            self.shortcut_created = True
            self.print_status("Desktop shortcut created")
            
        except Exception as e:
            self.print_status(f"Failed to create desktop shortcut: {e}", Colors.YELLOW)
    
    def create_launcher_scripts(self) -> None:
        """Create platform-specific launcher scripts."""
        self.print_header("Creating Launcher Scripts")
        
        venv_python = self.get_venv_python()
        
        if self.is_windows:
            # Create start_jugiai.bat
            batch_content = f'''@echo off
cd /d "%~dp0"
"{venv_python}" jugiai.py %*
pause
'''
            with open(self.root_dir / "start_jugiai.bat", 'w') as f:
                f.write(batch_content)
            self.print_status("Created start_jugiai.bat")
            
        else:
            # Create start_jugiai.sh
            script_content = f'''#!/bin/bash
cd "$(dirname "$0")"
"{venv_python}" jugiai.py "$@"
'''
            script_file = self.root_dir / "start_jugiai.sh"
            with open(script_file, 'w') as f:
                f.write(script_content)
            script_file.chmod(0o755)
            self.print_status("Created start_jugiai.sh")
    
    def cleanup_build_artifacts(self) -> None:
        """Clean up temporary build files."""
        if self.args.verbose:
            return  # Keep artifacts for debugging
        
        cleanup_dirs = ["build", "dist", "__pycache__"]
        cleanup_files = ["AnomAI.spec"]
        
        for dirname in cleanup_dirs:
            dir_path = self.root_dir / dirname
            if dir_path.exists():
                shutil.rmtree(dir_path, ignore_errors=True)
        
        for filename in cleanup_files:
            file_path = self.root_dir / filename
            if file_path.exists():
                file_path.unlink()
    
    def print_summary(self) -> None:
        """Print installation summary."""
        self.print_header("Installation Complete!")
        
        print(f"{Colors.GREEN}✓ AnomAI/JugiAI has been installed successfully!{Colors.RESET}\n")
        
        # Installation summary
        print(f"{Colors.BOLD}Installation Summary:{Colors.RESET}")
        print(f"  Virtual Environment: {'✓' if self.venv_created else '✗'}")
        print(f"  Requirements: {'✓' if self.requirements_installed else '✗'}")
        print(f"  Local Models: {'✓' if self.llama_installed else '✗'}")
        print(f"  Executable: {'✓' if self.exe_built else '✗'}")
        print(f"  Desktop Shortcut: {'✓' if self.shortcut_created else '✗'}")
        
        # How to run
        print(f"\n{Colors.BOLD}How to Start AnomAI:{Colors.RESET}")
        
        if self.exe_built and self.is_windows:
            print(f"  • Double-click: {Colors.CYAN}AnomAI.exe{Colors.RESET}")
        elif self.exe_built and not self.is_windows:
            print(f"  • Run: {Colors.CYAN}./dist/AnomAI/AnomAI{Colors.RESET}")
        
        if self.is_windows:
            print(f"  • Double-click: {Colors.CYAN}start_jugiai.bat{Colors.RESET}")
        else:
            print(f"  • Run: {Colors.CYAN}./start_jugiai.sh{Colors.RESET}")
        
        print(f"  • Command line: {Colors.CYAN}{self.get_venv_python()} jugiai.py{Colors.RESET}")
        
        # Configuration files
        print(f"\n{Colors.BOLD}Configuration:{Colors.RESET}")
        print(f"  • Settings: {Colors.CYAN}config.json{Colors.RESET}")
        print(f"  • Chat History: {Colors.CYAN}history.json{Colors.RESET}")
        
        # Next steps
        if self.llama_installed:
            print(f"\n{Colors.BOLD}Local Models:{Colors.RESET}")
            print(f"  • Download GGUF models to use offline")
            print(f"  • Configure model path in AnomAI settings")
            print(f"  • For GPU acceleration, upgrade llama-cpp-python")
        
        print(f"\n{Colors.BOLD}Support:{Colors.RESET}")
        print(f"  • Documentation: {Colors.CYAN}README.md{Colors.RESET}")
        print(f"  • Issues: {Colors.CYAN}https://github.com/AnomFIN/AnomAI{Colors.RESET}")
        
        print(f"\n{Colors.GREEN}🎉 Enjoy using AnomAI!{Colors.RESET}\n")
    
    def run(self) -> None:
        """Run the complete installation process."""
        try:
            self.print_header("AnomAI/JugiAI Cross-Platform Installer")
            
            if not self.args.no_interactive:
                print(f"{Colors.CYAN}This installer will set up AnomAI on your system.")
                print(f"Platform: {platform.system()} {platform.machine()}")
                print(f"Installation directory: {self.root_dir}{Colors.RESET}\n")
                
                if not self.args.force:
                    response = input("Continue with installation? [Y/n]: ").strip().lower()
                    if response and response[0] == 'n':
                        print("Installation cancelled.")
                        sys.exit(0)
            
            # Run installation steps
            self.check_system_requirements()
            self.create_virtual_environment()
            self.install_requirements()
            self.install_llama_cpp()
            self.setup_configuration()
            self.create_launcher_scripts()
            self.build_executable()
            self.create_desktop_shortcut()
            self.cleanup_build_artifacts()
            
            self.print_summary()
            
        except KeyboardInterrupt:
            self.print_status("\nInstallation cancelled by user.", Colors.YELLOW)
            sys.exit(1)
        except InstallError as e:
            self.print_status(f"\nInstallation failed: {e}", Colors.RED)
            sys.exit(1)
        except Exception as e:
            self.print_status(f"\nUnexpected error: {e}", Colors.RED)
            if self.args.verbose:
                import traceback
                traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="AnomAI/JugiAI Cross-Platform Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--no-venv", action="store_true",
                       help="Skip virtual environment creation")
    parser.add_argument("--no-llama", action="store_true",
                       help="Skip llama-cpp-python installation")
    parser.add_argument("--no-exe", action="store_true",
                       help="Skip executable build")
    parser.add_argument("--no-shortcut", action="store_true",
                       help="Skip desktop shortcut creation")
    parser.add_argument("--no-interactive", action="store_true",
                       help="Run in non-interactive mode with defaults")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--force", action="store_true",
                       help="Force reinstallation")
    
    args = parser.parse_args()
    
    installer = AnomAIInstaller(args)
    installer.run()


if __name__ == "__main__":
    main()