#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AnomAI/JugiAI Local Model Support Installer

This script installs llama-cpp-python for local GGUF/LLM model support.
It handles the installation process safely across different Windows environments
(cmd.exe, PowerShell, Windows Terminal, etc.).

Usage:
    python install_tool_for_windows.py           # Install CPU version (default)
    python install_tool_for_windows.py --gpu     # Install GPU version (CUDA)
    python install_tool_for_windows.py --help    # Show help

Requirements:
    - Python 3.10+ (64-bit)
    - Internet connection
    - Visual C++ Build Tools (may be needed for compilation)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from typing import List, Optional


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def disable():
        """Disable colors (for non-ANSI terminals)."""
        Colors.HEADER = ''
        Colors.OKBLUE = ''
        Colors.OKCYAN = ''
        Colors.OKGREEN = ''
        Colors.WARNING = ''
        Colors.FAIL = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''


# Disable colors on Windows unless in modern terminal
if sys.platform.startswith('win'):
    # Check if we're in Windows Terminal or modern console
    if not os.environ.get('WT_SESSION') and not os.environ.get('ANSICON'):
        Colors.disable()


def print_header(text: str) -> None:
    """Print a header message."""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'=' * 70}{Colors.ENDC}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def check_python_version() -> bool:
    """
    Check if Python version meets requirements (3.10+ 64-bit).
    
    Returns:
        True if version is OK, False otherwise.
    """
    try:
        version = sys.version_info
        bits = 8 * 8 if sys.maxsize > 2**32 else 32
        
        print_info(f"Python versio: {version.major}.{version.minor}.{version.micro}")
        print_info(f"Arkkitehtuuri: {bits}-bit")
        
        if version.major < 3 or (version.major == 3 and version.minor < 10):
            print_error(f"Python 3.10+ vaaditaan, mutta löydettiin versio {version.major}.{version.minor}")
            print_error("Lataa uudempi Python-versio: https://www.python.org/downloads/")
            return False
        
        if bits != 64:
            print_error(f"64-bittinen Python vaaditaan, mutta löydettiin {bits}-bittinen versio")
            print_error("Lataa 64-bittinen Python: https://www.python.org/downloads/")
            return False
        
        print_success("Python-versio täyttää vaatimukset")
        return True
    except Exception as e:
        print_error(f"Python-version tarkistus epäonnistui: {e}")
        return False


def check_pip_available() -> bool:
    """
    Check if pip is available.
    
    Returns:
        True if pip is available, False otherwise.
    """
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        print_success("pip on saatavilla")
        return True
    except subprocess.TimeoutExpired:
        print_error("pip-tarkistus aikakatkaistiin")
        return False
    except subprocess.CalledProcessError:
        print_error("pip ei ole saatavilla")
        print_error("Asenna pip komennolla: python -m ensurepip --upgrade")
        return False
    except FileNotFoundError:
        print_error("Python tai pip ei löytynyt")
        return False
    except Exception as e:
        print_error(f"pip-tarkistus epäonnistui: {e}")
        return False


def run_pip_command(args: List[str], description: str, timeout: int = 600) -> bool:
    """
    Run a pip command safely with comprehensive error handling.
    
    Args:
        args: List of pip command arguments (without 'python -m pip')
        description: Description of what the command does
        timeout: Command timeout in seconds (default 600 = 10 minutes)
    
    Returns:
        True if command succeeded, False otherwise.
    """
    print_info(f"{description}...")
    
    cmd = [sys.executable, "-m", "pip"] + args
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Show output if verbose or if there were warnings
        if result.stdout and "--verbose" in args:
            print(result.stdout)
        
        print_success(f"{description} onnistui")
        return True
        
    except subprocess.TimeoutExpired:
        print_error(f"{description} aikakatkaistiin ({timeout} sekuntia)")
        print_info("Yritä uudelleen paremmalla internet-yhteydellä tai suurenna timeout-arvoa")
        return False
        
    except subprocess.CalledProcessError as e:
        print_error(f"{description} epäonnistui")
        print_error(f"Virhekoodi: {e.returncode}")
        
        if e.stdout:
            print("\nTuloste:")
            print(e.stdout)
        
        if e.stderr:
            print("\nVirheviesti:")
            print(e.stderr)
        
        return False
    
    except FileNotFoundError:
        print_error(f"{description} epäonnistui: Python tai pip ei löytynyt")
        print_info("Tarkista että Python on asennettu ja PATH-muuttuja on asetettu oikein")
        return False
    
    except Exception as e:
        print_error(f"{description} epäonnistui odottamattoman virheen vuoksi: {e}")
        return False


def install_cpu_version() -> bool:
    """
    Install CPU version of llama-cpp-python with error recovery.
    
    Returns:
        True if installation succeeded, False otherwise.
    """
    print_header("Asennetaan llama-cpp-python (CPU-versio)")
    
    print_info("Tämä saattaa kestää useita minuutteja...")
    print_info("Asennus käyttää esikäännettyjä binäärejä (--prefer-binary)")
    print()
    
    try:
        return run_pip_command(
            ["install", "--upgrade", "--prefer-binary", "llama-cpp-python"],
            "llama-cpp-python (CPU) asennus",
            timeout=600
        )
    except Exception as e:
        print_error(f"Asennus epäonnistui odottamattoman virheen vuoksi: {e}")
        return False


def install_gpu_version() -> bool:
    """
    Install GPU version of llama-cpp-python with CUDA support and error recovery.
    
    Returns:
        True if installation succeeded, False otherwise.
    """
    print_header("Asennetaan llama-cpp-python (GPU-versio, CUDA)")
    
    print_warning("GPU-asennus vaatii CUDA-yhteensopivan NVIDIA-näytönohjaimen")
    print_info("Tämä saattaa kestää useita minuutteja...")
    print()
    
    try:
        # First, try to install/upgrade the GPU version
        cuda_url = "https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu121"
        
        success = run_pip_command(
            [
                "install",
                "llama-cpp-python",
                "--force-reinstall",
                "--no-cache-dir",
                "--extra-index-url",
                cuda_url
            ],
            "llama-cpp-python (CUDA) asennus",
            timeout=900  # GPU version may take longer
        )
        
        if success:
            print()
            print_success("GPU-versio asennettu")
            print_info("Huom: GPU-kiihdytys toimii vain CUDA-yhteensopivilla NVIDIA-näytönohjaimilla")
        
        return success
    except Exception as e:
        print_error(f"GPU-asennus epäonnistui odottamattoman virheen vuoksi: {e}")
        return False


def verify_installation() -> bool:
    """
    Verify that llama-cpp-python is installed and can be imported.
    
    Returns:
        True if verification succeeded, False otherwise.
    """
    print_header("Tarkistetaan asennus")
    
    try:
        # Try to import llama_cpp
        result = subprocess.run(
            [sys.executable, "-c", "import llama_cpp; print(llama_cpp.__version__)"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        version = result.stdout.strip()
        print_success(f"llama-cpp-python asennettu onnistuneesti (versio {version})")
        return True
        
    except subprocess.TimeoutExpired:
        print_error("Asennuksen tarkistus aikakatkaistiin")
        return False
        
    except subprocess.CalledProcessError:
        print_error("llama-cpp-python ei ole käytettävissä")
        print_error("Asennus saattoi epäonnistua tai moduulia ei voitu tuoda")
        return False
    
    except FileNotFoundError:
        print_error("Python ei löytynyt asennuksen tarkistuksessa")
        return False
    
    except Exception as e:
        print_error(f"Asennuksen tarkistus epäonnistui: {e}")
        return False


def show_usage_instructions(gpu_mode: bool) -> None:
    """
    Show instructions for using local models.
    
    Args:
        gpu_mode: Whether GPU mode was installed
    """
    print_header("Käyttöohjeet")
    
    print("1. Avaa JugiAI")
    print("2. Mene Asetukset (⚙️) > Profiili-asetukset")
    print("3. Valitse 'Backend': 'local'")
    print("4. Aseta 'Paikallisen mallin polku' GGUF-tiedoston poluksi")
    
    if gpu_mode:
        print("5. Valitse 'GPU-tila': 'gpu' (GPU-kiihdytys)")
    else:
        print("5. Valitse 'GPU-tila': 'cpu' (suositeltu ensimmäisellä kerralla)")
    
    print("6. Tallenna asetukset")
    print()
    print_info("GGUF-malleja voi ladata esim. Hugging Facesta:")
    print_info("  https://huggingface.co/models?library=gguf")
    print()


def main() -> int:
    """
    Main function with comprehensive error handling.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        parser = argparse.ArgumentParser(
            description="Asenna llama-cpp-python JugiAI:lle (paikallinen mallikäyttö)",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Esimerkkejä:
  python install_tool_for_windows.py           # Asenna CPU-versio
  python install_tool_for_windows.py --gpu     # Asenna GPU-versio (CUDA)

Lisätietoja:
  https://github.com/AnomFIN/AnomAI
            """
        )
        
        parser.add_argument(
            "--gpu",
            action="store_true",
            help="Asenna GPU-versio CUDA-tuella (vaatii NVIDIA-näytönohjaimen)"
        )
        
        parser.add_argument(
            "--skip-verify",
            action="store_true",
            help="Ohita asennuksen tarkistus"
        )
        
        args = parser.parse_args()
        
        # Print banner
        print_header("JugiAI - Paikallisen mallin tuen asennus")
        
        # Check prerequisites
        if not check_python_version():
            return 1
        
        if not check_pip_available():
            return 1
        
        print()
        
        # Install appropriate version
        if args.gpu:
            success = install_gpu_version()
        else:
            success = install_cpu_version()
        
        if not success:
            print()
            print_error("Asennus epäonnistui!")
            print()
            print_info("Yleisiä ratkaisuja:")
            print_info("  1. Tarkista internet-yhteys")
            print_info("  2. Asenna Visual C++ Build Tools:")
            print_info("     https://visualstudio.microsoft.com/visual-cpp-build-tools/")
            print_info("  3. Yritä uudelleen järjestelmänvalvojana")
            print_info("  4. Tarkista palomuuri/virustorjunta-asetukset")
            print_info("  5. Käytä --skip-verify jos asennus näyttää onnistuneen")
            return 1
        
        print()
        
        # Verify installation
        if not args.skip_verify:
            try:
                if not verify_installation():
                    print_warning("Tarkistus epäonnistui, mutta asennus saattoi silti onnistua")
                    print_info("Kokeile käynnistää JugiAI ja tarkista toimiiko paikallinen malli")
                    return 1
            except Exception as e:
                print_error(f"Tarkistus epäonnistui odottamattoman virheen vuoksi: {e}")
                print_warning("Asennus saattoi silti onnistua")
                print_info("Kokeile käynnistää JugiAI ja tarkista toimiiko paikallinen malli")
                return 1
        
        print()
        
        # Show usage instructions
        try:
            show_usage_instructions(args.gpu)
        except Exception as e:
            print_warning(f"Käyttöohjeiden näyttö epäonnistui: {e}")
        
        print_success("Asennus valmis! 🎉")
        print()
        
        return 0
    
    except Exception as e:
        print()
        print_error(f"Kriittinen virhe asennuksessa: {e}")
        print_info("Jos ongelma jatkuu, raportoi virhe GitHubissa:")
        print_info("https://github.com/AnomFIN/AnomAI/issues")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        print_warning("Asennus keskeytetty käyttäjän toimesta")
        sys.exit(130)
    except Exception as e:
        print()
        print_error(f"Odottamaton virhe: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
