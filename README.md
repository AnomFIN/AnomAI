# AnomAI/JugiAI

> **Windows-native AI chat application with local and cloud AI support**  
> Zero friction, full acceleration.

[![CI Pipeline](https://github.com/AnomFIN/AnomAI/workflows/CI%20Pipeline/badge.svg)](https://github.com/AnomFIN/AnomAI/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform: Windows](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/AnomFIN/AnomAI)

AnomAI (also known as JugiAI) is a modern, user-friendly AI chat application built with Python and Tkinter. It provides seamless access to both OpenAI's GPT models and local GGUF models for private, offline AI conversations.

## 🌟 Key Features

- **🎨 Modern UI**: Cyber-neon theme with dark background and turquoise accents
- **🌐 Dual Backend Support**: OpenAI API and local GGUF models via llama-cpp-python  
- **🔒 Privacy First**: Complete offline mode with local model support
- **📱 Cross-Platform**: Native support for Windows, Linux, and macOS
- **📂 Conversation Management**: History storage with playback functionality
- **⚙️ Configurable**: Extensive settings for models, temperature, context windows
- **📷 Camera Integration**: WiFi/IP camera connection support
- **🔧 Easy Installation**: One-click installer with automatic dependency management
- **📦 Portable**: Builds to standalone executables

## 🏗️ Architecture

AnomAI is designed as a desktop-first application with minimal external dependencies:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Tkinter GUI   │ ←→ │   Core Engine    │ ←→ │   AI Backends   │
│                 │    │                  │    │                 │
│ • Chat Interface│    │ • Config Manager │    │ • OpenAI API    │
│ • Settings      │    │ • History Store  │    │ • Local GGUF    │
│ • Camera Setup  │    │ • Model Manager  │    │ • llama-cpp-py  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Core Components:**
- **jugiai.py**: Main Tkinter application with GUI and business logic
- **playback_utils.py**: Conversation playback and font management utilities
- **install.py**: Cross-platform installer with dependency management
- **make_ico.py**: Icon generation utility for executable builds

## 🚀 Installation

### Quick Start (All Platforms)

```bash
# Clone or download the repository
git clone https://github.com/AnomFIN/AnomAI.git
cd AnomAI

# Run the unified installer
python install.py
```

### Platform-Specific Installation

#### Windows
```cmd
# Use the Windows wrapper (recommended)
install.bat

# Or run directly
python install.py
```

#### Linux/macOS
```bash
# Run the installer
python3 install.py

# Or use the shell wrapper
./start_jugiai.sh
```

### Installation Options

The installer supports various options for different use cases:

```bash
# Non-interactive installation with defaults
python install.py --no-interactive

# Skip virtual environment (use system Python)
python install.py --no-venv

# Skip local model support
python install.py --no-llama

# Skip executable build
python install.py --no-exe

# Force reinstallation
python install.py --force

# Verbose output for debugging
python install.py --verbose
```

## 💻 Usage

### Starting the Application

After installation, you can start AnomAI in several ways:

**Windows:**
- Double-click the desktop shortcut
- Run `AnomAI.exe` (if built)
- Execute `start_jugiai.bat`

**Linux/macOS:**
- Run `./start_jugiai.sh`
- Execute `./dist/AnomAI/AnomAI` (if built)
- Command line: `python3 jugiai.py`

### First-Time Setup

1. **Launch AnomAI** using any of the methods above
2. **Configure AI Backend**: Click the ⚙️ settings icon
3. **Choose Backend**:
   - **OpenAI**: Enter your API key and select a model (e.g., `gpt-4o-mini`)
   - **Local**: Select a GGUF model file for offline operation
4. **Adjust Settings**: Configure temperature, max tokens, and UI preferences
5. **Start Chatting**: Type your message and press Enter

### Configuration Examples

**OpenAI Configuration:**
```json
{
  "backend": "openai",
  "api_key": "sk-...",
  "model": "gpt-4o-mini",
  "temperature": 0.7,
  "max_tokens": 4000
}
```

**Local Model Configuration:**
```json
{
  "backend": "local",
  "local_model_path": "/path/to/model.gguf",
  "local_n_ctx": 4096,
  "local_gpu_layers": -1,
  "offline_mode": true
}
```

## 🤖 Local Model Support

AnomAI supports local GGUF models for complete privacy and offline operation.

### Requirements
- Python 3.10+ (64-bit)
- 4GB+ RAM (8GB+ recommended)
- Optional: NVIDIA GPU with CUDA for acceleration

### Installing Local Model Support

```bash
# CPU-only version (included in main installer)
python -m pip install llama-cpp-python --prefer-binary

# GPU acceleration (after main installation)
python -m pip install llama-cpp-python --force-reinstall --no-cache-dir \
  --extra-index-url https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu121
```

### Obtaining GGUF Models

**Recommended Sources:**
- [Hugging Face](https://huggingface.co/models?search=gguf) - Search for GGUF models
- Popular series: Llama 3, Mistral, Phi-3, Gemma

**Quantization Guide:**
- **Q4_K_M**: Recommended balance of quality/size (~4GB for 7B model)
- **Q5_K_M**: Higher quality (~5GB for 7B model) 
- **Q8_0**: Best quality (~7GB for 7B model)

### Configuration

1. Open Settings (⚙️) → "Paikallinen" (Local) tab
2. Click "Valitse..." to select your `.gguf` model file
3. Configure:
   - **GPU Layers**: -1 (auto), 0 (CPU only), or specific number
   - **Context Window**: 4096 (default) or higher for longer conversations
   - **Threads**: 0 (auto) or manual thread count
4. Set "Backend" to "local" 
5. Save settings

## 📷 Camera Integration

AnomAI includes WiFi/IP camera connection support for future multimedia features.

### Manual Camera Setup
1. Open Settings (⚙️) → "Kamera" tab
2. Enter camera IP address (e.g., `192.168.1.100`)
3. Enter username (default: `admin`) and password
4. Set port (default: `8080`)
5. Save settings

### Automatic Camera Discovery
1. Open Settings (⚙️) → "Kamera" tab
2. Click "Etsi kamerat" (Find cameras)
3. Wait for network scan to complete
4. Select discovered camera from list
5. Click "Käytä valittua kameraa" (Use selected camera)
6. Enter credentials and save

## 🛠️ Development Setup

### Requirements
- Python 3.10+ (64-bit recommended)
- Virtual environment (recommended)
- Git for version control

### Development Installation

```bash
# Clone the repository
git clone https://github.com/AnomFIN/AnomAI.git
cd AnomAI

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate.bat
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install flake8 pytest pyinstaller

# Run the application
python jugiai.py
```

### Running Tests

```bash
# Run all tests
python -m unittest discover -s tests -v

# Run specific test categories
python -m unittest tests.smoke_test -v
python -m unittest tests.test_camera_discovery -v
python -m unittest tests.test_offline_mode -v

# Run linting
python -m flake8 . --exclude=legacy-orig
```

### Building Executables

```bash
# Build standalone executable
python -m PyInstaller --onefile --windowed --name AnomAI jugiai.py

# The executable will be created in dist/AnomAI.exe (Windows)
# or dist/AnomAI (Linux/macOS)
```

## 📁 Repository Structure

```
AnomAI/
├── jugiai.py                 # Main application entry point
├── playback_utils.py         # Conversation playback utilities  
├── install.py                # Unified cross-platform installer
├── install.bat               # Windows installer wrapper
├── make_ico.py               # Icon generation utility
├── requirements.txt          # Python dependencies
├── config.json               # User configuration (auto-generated)
├── history.json             # Chat history (auto-generated)
├── tests/                   # Test suite
│   ├── smoke_test.py        # CI smoke tests
│   ├── test_camera_discovery.py
│   ├── test_offline_mode.py
│   └── ... (other tests)
├── legacy-orig/             # Archived legacy installers
│   ├── install.bat          # Original Windows installer
│   ├── install_utf8.bat     # UTF-8 wrapper
│   └── README.md            # Archive documentation
├── .github/
│   └── workflows/
│       └── ci.yml           # CI/CD pipeline
└── docs/                    # Additional documentation (future)
```

## 🔄 CI & Quality Gates

AnomAI uses GitHub Actions for continuous integration across multiple platforms:

### CI Pipeline
- **Platforms**: Ubuntu, Windows, macOS
- **Python Versions**: 3.10, 3.11, 3.12
- **Test Coverage**: Unit tests, smoke tests, integration tests
- **Code Quality**: flake8 linting, security scanning (bandit)
- **Build Tests**: PyInstaller executable validation

### Running CI Locally

```bash
# Install CI dependencies
pip install flake8 bandit safety

# Run linting (same as CI)
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
python -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=legacy-orig

# Run security checks
python -m bandit -r . -ll
python -m safety check
```

## 🐛 Troubleshooting

### Common Issues

#### Installation Problems

**Python not found**
```
Solution: Install Python 3.10+ (64-bit) from python.org
Ensure "Add Python to PATH" is checked during installation
```

**llama-cpp-python installation fails**
```
Windows: Install Microsoft C++ Build Tools
Linux: sudo apt-get install build-essential
macOS: xcode-select --install
Or use: pip install llama-cpp-python --prefer-binary
```

**GUI doesn't appear (Linux)**
```
sudo apt-get install python3-tk
```

#### Runtime Issues

**Application closes immediately**
```
Check jugiai_error.log for detailed error messages
Ensure all dependencies are installed in the virtual environment
```

**Local model fails to load**
```
Verify the .gguf file path is correct
Check available RAM/VRAM (need 4GB+ for 7B models)
Try reducing local_gpu_layers or local_n_ctx
```

**OpenAI API errors**
```
Verify API key is correct and has sufficient credits
Check internet connection
Try a different model (e.g., gpt-4o-mini)
```

### Advanced Troubleshooting

**Enable verbose logging:**
```python
# Edit jugiai.py temporarily
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check configuration:**
```bash
# View current config
cat config.json

# Reset configuration
rm config.json
# Restart app to regenerate with defaults
```

**Test network connectivity:**
```python
# Test OpenAI connection
python -c "import urllib.request; print(urllib.request.urlopen('https://api.openai.com').status)"

# Test local camera discovery
python demo_camera_feature.py
```

## 🔒 Security & Privacy

### Privacy Features
- **Local Mode**: Complete offline operation with GGUF models
- **No Data Collection**: No telemetry or usage tracking
- **Local Storage**: All conversations stored locally in `history.json`
- **Configurable**: Choose between cloud and local AI backends

### Security Measures
- **Code Scanning**: Regular CodeQL security analysis (0 alerts)
- **Dependency Scanning**: Automatic vulnerability detection
- **Input Validation**: Sanitized file paths and user inputs
- **Safe Defaults**: Secure configuration defaults

## 🚧 Known Limitations & Next Steps

### Current Limitations
- **GUI Framework**: Tkinter-based (native look may vary by platform)
- **Model Size**: Local models limited by available RAM/VRAM
- **Threading**: Some UI operations may block briefly during heavy processing
- **Camera Feature**: Currently configuration-only (streaming planned)

### Planned Improvements
- **Enhanced UI**: Modern web-based interface option
- **Model Management**: Built-in model download and management
- **Conversation Export**: PDF/Markdown export functionality  
- **Plugin System**: Support for custom AI backends
- **Voice Integration**: Speech-to-text and text-to-speech
- **Camera Streaming**: Live camera feed integration
- **Multi-language**: UI localization beyond Finnish

### Contributing
We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`python -m unittest discover -s tests`)
5. Commit with descriptive messages (`git commit -m 'Add amazing feature'`)
6. Push to your branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for providing excellent language models and APIs
- **llama.cpp** team for making local LLM inference accessible
- **Python/Tkinter** community for the GUI framework
- **PyInstaller** for cross-platform executable building
- **GitHub Actions** for CI/CD infrastructure

## 📞 Support

- **Documentation**: See files in this repository
- **Issues**: [GitHub Issues](https://github.com/AnomFIN/AnomAI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AnomFIN/AnomAI/discussions)
- **Security**: See [SECURITY.md](SECURITY.md) for security policy

---

**AnomFIN · Älykkyyden käyttöönotto**  
*Intelligent Experiences*

© 2024-2025 AnomFIN. Built with ❤️ for the AI community.