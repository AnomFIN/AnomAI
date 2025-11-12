# GitHub Copilot Instructions for AnomAI/JugiAI

## Project Overview

AnomAI/JugiAI is a Windows-native AI chat application built with Python and Tkinter. It provides a GUI interface for interacting with OpenAI APIs and local LLM models (via llama-cpp-python).

**Key Features:**
- Tkinter-based GUI with modern cyber-neon theme
- Support for OpenAI API and local GGUF models
- Conversation history with playback features
- Profile management and customizable settings
- PyInstaller-based Windows executable generation
- UTF-8 safe installation scripts for Windows

## Project Structure

```
AnomAI/
├── jugiai.py                    # Main application (Tkinter GUI)
├── playback_utils.py            # Playback and font utilities
├── install.bat                  # Main installation script
├── install_utf8.bat             # UTF-8 wrapper for install.bat
├── build_exe.bat                # PyInstaller build script
├── start_jugiai.bat             # Application launcher
├── make_ico.py                  # Icon generation utility
├── requirements.txt             # Python dependencies
├── config.json                  # User configuration (auto-generated)
├── history.json                 # Chat history (auto-generated)
├── tests/                       # Unit tests
│   ├── test_offline_mode.py
│   ├── test_playback_utils.py
│   ├── test_model_formatting.py
│   └── ...
├── scripts/                     # Helper scripts
└── .github/
    └── workflows/               # CI/CD workflows
        ├── build-windows.yml
        ├── lint.yml
        └── windows-pyinstaller.yml
```

## Technology Stack

- **Language:** Python 3.10+ (64-bit required for PyInstaller)
- **GUI Framework:** Tkinter (standard library)
- **HTTP Client:** urllib (standard library)
- **Optional Dependencies:**
  - Pillow (>=8.0.0) - Image processing
  - llama-cpp-python - Local LLM support (installed separately)
- **Build Tool:** PyInstaller (for .exe generation)
- **Testing:** unittest (standard library)

## Development Guidelines

### Code Style

1. **Encoding:** All Python files use UTF-8 with BOM-free encoding
2. **Batch Scripts:** Windows batch files (.bat, .cmd) must be:
   - UTF-8 encoded without BOM
   - Use CRLF line endings (required for Windows)
   - Validated by lint.yml workflow
3. **Documentation:** Finnish language for user-facing docs, English for code comments
4. **Type Hints:** Use modern Python type hints (from `__future__ import annotations`)

### Coding Patterns

1. **Configuration Management:**
   - Use JSON for config files (config.json, history.json)
   - Always write with UTF-8 encoding: `json.dump(..., ensure_ascii=False)`
   - Provide sensible defaults for missing settings

2. **Error Handling:**
   - Graceful degradation for missing optional dependencies (PIL, llama-cpp-python)
   - User-friendly error messages in Finnish
   - Log errors to jugiai_error.log with full tracebacks

3. **Threading:**
   - Use threading for API calls to prevent GUI freezing
   - Validate thread counts against CPU limits
   - See `test_thread_validation.py` for patterns

4. **Offline Mode:**
   - Detect offline mode via: explicit flag, local backend, or missing API key
   - Prevent API calls when offline
   - See `test_offline_mode.py` for implementation

### Testing

**Run Tests:**
```bash
python -m unittest discover -s tests -v
```

**Test Organization:**
- Unit tests in `tests/` directory
- One test file per feature/module
- Use descriptive test names and docstrings
- Mock external dependencies (API calls, file I/O)

**CI/CD:**
- All tests run on push/PR via GitHub Actions
- Windows-specific testing environment
- Lint checks for encoding and line endings

### Building

**Development Build:**
```bash
python jugiai.py
```

**Production Build:**
```bash
build_exe.bat
```
This creates:
- `dist\AnomAI\AnomAI.exe` - Standalone executable
- `AnomAI_Windows.zip` - Distribution package
- `build_exe.log` - Build log

**Installation:**
```bash
install.bat
```
Performs full setup:
1. Creates virtual environment (.venv)
2. Installs dependencies
3. Configures application
4. Builds executable
5. Creates desktop shortcut

### Important Constraints

1. **Windows Focus:** This is a Windows-native application
   - Use Windows path conventions (backslash)
   - Test on Windows environment
   - Batch scripts must use CRLF line endings

2. **Minimal Dependencies:** Prefer standard library
   - Core features work without external packages
   - Optional features gracefully degrade

3. **UTF-8 Safety:** Windows console encoding is fragile
   - Use UTF-8 without BOM for all text files
   - Batch scripts handle codepage switching
   - JSON files use `ensure_ascii=False`

4. **PyInstaller Compatibility:**
   - Avoid dynamic imports when possible
   - Bundle data files explicitly in .spec
   - Test .exe builds before release

## Common Tasks

### Adding a New Feature

1. Implement in `jugiai.py` or separate module
2. Add unit tests in `tests/test_<feature>.py`
3. Update README.MD if user-facing
4. Test with both Python and .exe versions
5. Ensure offline mode compatibility if applicable

### Fixing a Bug

1. Add failing test that reproduces the bug
2. Fix the bug with minimal changes
3. Verify test passes
4. Check for regressions in related features

### Updating Dependencies

1. Update `requirements.txt`
2. Test installation with `install.bat`
3. Verify .exe build with `build_exe.bat`
4. Update README.MD if needed

### Modifying Batch Scripts

1. Use UTF-8 encoding without BOM
2. Ensure CRLF line endings
3. Test on Windows command prompt
4. Verify lint checks pass
5. Add error handling for user-friendly output

## Security Considerations

1. **API Keys:** Never commit API keys to version control
   - Store in config.json (gitignored)
   - Prompt user during installation
   - Validate before use

2. **User Input:** Sanitize file paths and user inputs
   - Use os.path operations for path handling
   - Validate model file paths before loading

3. **Dependencies:** Keep dependencies minimal and updated
   - Check for vulnerabilities before adding
   - Use `--prefer-binary` for llama-cpp-python

## Performance Tips

1. **GUI Responsiveness:**
   - Use threads for long-running operations
   - Update GUI from main thread only
   - Show loading indicators for API calls

2. **Memory Management:**
   - Clear history when it grows large
   - Unload images when not needed
   - Limit conversation context size

3. **Build Optimization:**
   - Use PyInstaller's `--onefile` for distribution
   - Exclude unnecessary modules with `--exclude-module`

## Troubleshooting

### Common Issues

1. **"No module named 'tkinter'"**
   - tkinter is not available in headless environments
   - Tests that import jugiai.py will fail in CI without display
   - Solution: Mock tkinter in tests or skip GUI tests

2. **UTF-8 Encoding Errors**
   - Ensure batch files are UTF-8 without BOM
   - Use `chcp 65001` before running scripts
   - install_utf8.bat handles this automatically

3. **PyInstaller Build Failures**
   - Check Python is 64-bit and version 3.10+
   - Install Visual C++ Build Tools for llama-cpp-python
   - Review build_exe.log for details

4. **Offline Mode Not Working**
   - Verify `offline_mode: true` in config.json
   - Check local_model_path points to .gguf file
   - Ensure llama-cpp-python is installed

## Best Practices for Copilot

1. **When suggesting code changes:**
   - Preserve existing code style and patterns
   - Maintain UTF-8 encoding without BOM
   - Keep changes minimal and focused
   - Add tests for new functionality

2. **When working with batch files:**
   - Always use CRLF line endings
   - Follow existing error handling patterns
   - Include informative error messages in Finnish

3. **When adding features:**
   - Check if similar functionality exists
   - Ensure Windows compatibility
   - Test both Python and .exe versions
   - Update documentation

4. **When fixing bugs:**
   - Reproduce with a test first
   - Verify fix doesn't break offline mode
   - Check impact on PyInstaller build
   - Test with different configurations

## Resources

- **Repository:** https://github.com/AnomFIN/AnomAI
- **Documentation:** README.MD (Finnish)
- **Issue Tracker:** GitHub Issues
- **CI/CD:** GitHub Actions workflows in .github/workflows/

## Notes

- This project uses Finnish for user-facing content
- Focus on Windows compatibility
- Prioritize offline mode functionality
- Maintain backward compatibility with existing configs
