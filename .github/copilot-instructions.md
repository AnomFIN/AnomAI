# GitHub Copilot Instructions for AnomAI/JugiAI

## Project Overview

AnomAI/JugiAI is a Windows-focused AI chat application built with Python and Tkinter. It supports both OpenAI API and local LLM models (GGUF format via llama-cpp-python). The project emphasizes zero-friction Windows deployment with PyInstaller executables.

## Language and Documentation

- **Primary Language**: Finnish (documentation, UI, comments)
- **Code**: Python with English variable/function names where standard
- All README and documentation should be in Finnish
- UI strings and messages should be in Finnish

## Build and Test Process

### Running Tests

```bash
# Run all tests (uses Python's unittest framework)
python -m unittest discover -s tests -v

# Run specific test file
python -m unittest tests.test_playback_utils

# Run tests with coverage (if coverage is installed)
python -m coverage run -m unittest discover -s tests
python -m coverage report
```

**Expected**: 39+ tests should pass. One test (`test_error_messages`) may fail in headless environments due to missing tkinter - this is acceptable in CI.

### Linting

The project uses GitHub Actions for linting:
- Windows batch script encoding validation (UTF-8 without BOM, CRLF line endings)
- See `.github/workflows/lint.yml` for details

### Building the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Build executable (Windows only)
build_exe.bat

# The executable will be created at: dist/AnomAI/AnomAI.exe
```

## Coding Standards

### Python Code

1. **Python Version**: Requires Python 3.10+ (64-bit)
2. **Standard Library First**: Minimize external dependencies
3. **Type Hints**: Use type hints from `typing` module
4. **Encoding**: All Python files use UTF-8 with `# -*- coding: utf-8 -*-`
5. **Error Handling**: Comprehensive try-except blocks with user-friendly Finnish messages
6. **Threading**: UI updates must be thread-safe (use `after()` for GUI updates from threads)

### Windows Batch Scripts

1. **Encoding**: UTF-8 **without BOM**
2. **Line Endings**: CRLF (Windows style) - enforced by lint workflow
3. **Robustness**: Continue on errors where possible, provide clear error messages
4. **JSON Logging**: Use JSON format for structured logging where applicable

### File Naming Conventions

- Python modules: lowercase with underscores (e.g., `playback_utils.py`)
- Batch scripts: lowercase with underscores (e.g., `install.bat`, `build_exe.bat`)
- Tests: `test_*.py` in the `tests/` directory

## Testing Requirements

### When to Add Tests

- **Always** add tests for new utility functions in separate modules (like `playback_utils.py`)
- **Always** add tests for validation logic (offline mode, input validation)
- **Optional** for GUI-specific code (Tkinter widgets) - visual testing preferred
- **Required** for data processing, business logic, and configuration handling

### Test Structure

- Use Python's `unittest` framework
- Test files should be named `test_<feature>.py`
- Each test class should test one logical component
- Include docstrings explaining what each test validates

### Example Test Pattern

```python
import unittest

class MyFeatureTests(unittest.TestCase):
    """Test suite for my feature."""
    
    def test_basic_functionality(self):
        """Test that basic feature works as expected."""
        result = my_function(input_value)
        self.assertEqual(result, expected_value)
    
    def test_edge_case(self):
        """Test edge case handling."""
        result = my_function(None)
        self.assertIsNone(result)
```

## Project-Specific Guidance

### Configuration Management

- **Config File**: `config.json` - stores user settings, API keys, profiles
- **History File**: `history.json` - stores chat conversation history
- **Encoding**: Always use UTF-8 for JSON files (Python handles this by default)
- **Defaults**: Provide sensible defaults for all configuration values

### Offline Mode Support

The application supports full offline operation with local models:
- Check `offline_mode` flag in config
- Validate local model paths before use
- Provide clear error messages when llama-cpp-python is missing
- See `tests/test_offline_mode.py` for offline mode requirements

### Windows-Specific Considerations

1. **Windows Store Python**: Detect and redirect Windows Store Python stub (see `_guard_windows_store_stub()`)
2. **Path Handling**: Use `os.path.join()` for cross-compatibility
3. **Executable Detection**: Support multiple Python launchers (`py -3`, `python`, `python3`)
4. **PyInstaller**: Code must be compatible with frozen executables

### UI/UX Guidelines

- **Theme**: Cyber-neon dark theme with turquoise accents (#00f0ff, #0080ff)
- **Fonts**: Configurable with zoom controls (MIN: 8, MAX: 24)
- **Accessibility**: Support font size adjustments via zoom buttons
- **Error Messages**: Always in Finnish, user-friendly, actionable
- **Loading States**: Show progress for long-running operations

### External Dependencies

**Core (Required)**:
- `pillow>=8.0.0` - Image handling (watermarks, backgrounds, icons)

**Optional**:
- `llama-cpp-python` - Local LLM support (installed separately by `install.bat`)

**Important**: Do NOT add `llama-cpp-python` to `requirements.txt` as it requires special installation flags and C++ build tools on Windows.

## Security and Privacy

1. **API Keys**: Never commit API keys or secrets to the repository
2. **Local-First**: Support offline mode for full privacy
3. **Data Storage**: Chat history is stored locally in `history.json`
4. **No Telemetry**: No data collection or external tracking

## Common Tasks

### Adding a New Feature

1. Implement the feature in appropriate module
2. Add unit tests if the feature involves logic/validation
3. Update Finnish documentation in README.MD
4. Test in both Python script and PyInstaller executable modes
5. Ensure offline mode compatibility if applicable

### Fixing a Bug

1. Add a test that reproduces the bug (if possible)
2. Fix the bug with minimal changes
3. Verify all existing tests still pass
4. Update documentation if behavior changes

### Updating Dependencies

1. Check if the dependency is truly necessary
2. For Pillow: Ensure version supports Python 3.9+ (>=8.0.0)
3. Do NOT add llama-cpp-python to requirements.txt
4. Test in both development and PyInstaller build

## Files to Never Modify

- `logo.png` - AnomFIN branding asset
- `demo_final.png`, `screenshot_*.png` - Documentation assets
- `.git/` - Git internals

## Files That Require Special Care

- `install.bat`, `install_utf8.bat` - Must maintain UTF-8 without BOM, CRLF line endings
- `build_exe.bat` - PyInstaller build script, test thoroughly on Windows
- `jugiai.py` - Main application file, large and complex, minimize changes
- `config.json` - User configuration, preserve backward compatibility

## Getting Help

- Review existing tests in `tests/` directory for examples
- Check README.MD for detailed Finnish documentation
- Examine `playback_utils.py` for example of well-tested utility module
- Look at `test_offline_mode.py` for validation pattern examples
