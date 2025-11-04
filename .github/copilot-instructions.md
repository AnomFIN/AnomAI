# GitHub Copilot Instructions for AnomAI/JugiAI

## Project Overview

AnomAI/JugiAI is a **production-grade Windows AI desktop application** built with Python and packaged with PyInstaller. The application provides a Tkinter-based chat interface for OpenAI and local LLM models, designed to deliver an outstanding end-user experience as a standalone Windows executable.

## Core Architecture Principles

### 1. PyInstaller Compatibility - CRITICAL

**Always prioritize PyInstaller compatibility in every code change:**

- **Avoid dynamic imports**: Never use `__import__()`, `importlib.import_module()` with runtime-determined module names, or dynamic `exec()`/`eval()` for imports
- **Use explicit imports**: All imports must be at the top of files or in clearly defined functions with static import statements
- **Hidden imports**: When adding new dependencies, check if they require PyInstaller hidden imports and document them
- **Module discovery**: Structure code so PyInstaller can statically analyze all dependencies
- **Test packaging**: After significant changes, verify the code still packages correctly with PyInstaller

**Example - GOOD:**
```python
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
```

**Example - BAD:**
```python
# DO NOT DO THIS - dynamic import breaks PyInstaller
module_name = "PIL.Image"
PIL = __import__(module_name)
```

### 2. Dependency Management

**Python Version:**
- Minimum: Python 3.10 (64-bit)
- Test compatibility with Python 3.10, 3.11, and 3.12
- Use `from __future__ import annotations` for forward compatibility

**Required Dependencies:**
- Keep dependencies minimal - prefer Python standard library
- `tkinter`: GUI framework (included with Python on Windows)
- `pillow>=8.0.0`: Optional but recommended for image handling

**Optional Dependencies:**
- `llama-cpp-python`: For local GGUF models (requires special installation with `--prefer-binary`)
- Handle optional dependencies gracefully with try/except and feature flags

**When adding new dependencies:**
1. Check if they're compatible with PyInstaller
2. Verify they support Python 3.10+
3. Test on Windows 64-bit
4. Update `requirements.txt` with version constraints
5. Document any special installation requirements

### 3. Code Quality Standards

**Error Handling:**
- Never use bare `except:` clauses - always catch specific exceptions
- Provide clear, actionable error messages in JSON format where appropriate
- Log errors to `jugiai_error.log` with full tracebacks
- Handle network failures gracefully (API timeouts, connection errors)
- Validate user inputs before processing

**Example - GOOD:**
```python
try:
    response = urllib.request.urlopen(request, timeout=30)
except urllib.error.HTTPError as e:
    logger.error(f"HTTP error: {e.code} - {e.reason}")
    show_user_error(f"API request failed: {e.reason}")
except urllib.error.URLError as e:
    logger.error(f"Connection error: {e.reason}")
    show_user_error("Cannot connect to API. Check your internet connection.")
```

**Example - BAD:**
```python
try:
    response = urllib.request.urlopen(request)
except:  # BAD - catches everything, no user feedback
    pass
```

**Logging:**
- Use descriptive log messages with context
- Include timestamps for debugging
- Support JSON-formatted logs for structured logging
- Log to both console and file where appropriate

**Input Validation:**
- Validate all user inputs (API keys, file paths, configuration values)
- Check file paths exist before using them
- Validate JSON configuration before loading
- Sanitize inputs to prevent injection issues

### 4. Code Structure

**Modularity:**
- Keep functions focused and single-purpose
- Extract reusable logic into utility modules (see `playback_utils.py`)
- Use type hints for function signatures
- Document complex logic with clear comments

**File Organization:**
- Main application: `jugiai.py`
- Utility modules: Separate files for reusable logic
- Tests: Mirror source structure in `tests/` directory
- Configuration: JSON files with UTF-8 encoding

**Naming Conventions:**
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: Prefix with `_`

### 5. Windows-Specific Considerations

**File Paths:**
- Use `os.path.join()` or `pathlib.Path` for cross-platform compatibility
- Handle Windows paths with spaces and special characters
- Use absolute paths resolved from `__file__` for resources

**Character Encoding:**
- Always use UTF-8 encoding for file I/O: `open(file, 'r', encoding='utf-8')`
- Set console encoding to UTF-8: `chcp 65001`
- Handle BOM correctly in batch scripts (avoid it)
- Test with non-ASCII characters (ääkköset)

**Line Endings:**
- Batch files (`.bat`, `.cmd`): Use CRLF (`\r\n`)
- Python files: Use LF (`\n`)
- Configure `.gitattributes` to enforce correct line endings

**Example:**
```python
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

def load_config() -> dict:
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_config(config: dict) -> None:
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
```

### 6. UI/UX Requirements

**User Experience:**
- Fast startup time (minimize imports and initialization)
- Responsive UI (use threading for long-running operations)
- Clear visual feedback for actions (loading indicators, status messages)
- Graceful degradation when optional features unavailable
- Consistent theming following the cyber-neon dark theme

**GUI Best Practices:**
- Keep UI responsive - never block the main thread
- Use `threading` for API calls and long operations
- Update UI from main thread only (use `after()` for thread-safe updates)
- Provide progress indicators for long operations
- Handle window close events cleanly

**Example:**
```python
def send_message_async(self):
    """Send message in background thread to keep UI responsive."""
    def _send():
        try:
            response = self.call_api(self.message_text)
            # Update UI from main thread
            self.root.after(0, lambda: self.display_response(response))
        except Exception as e:
            self.root.after(0, lambda: self.show_error(str(e)))
    
    thread = threading.Thread(target=_send, daemon=True)
    thread.start()
```

**Accessibility:**
- Support font size adjustment (zoom in/out)
- Use clear, high-contrast colors
- Provide keyboard shortcuts for common actions
- Ensure all UI elements have proper labels

### 7. Testing Requirements

**Test Coverage:**
- Write unit tests for all utility functions
- Test error handling paths
- Test edge cases (empty inputs, None values, invalid data)
- Test Windows-specific code paths where possible

**Test Structure:**
- Place tests in `tests/` directory
- Name test files: `test_<module_name>.py`
- Use `unittest` framework (already in use)
- Mock external dependencies (API calls, file I/O when appropriate)

**Running Tests:**
```bash
python -m unittest discover -s tests -v
```

**Example Test:**
```python
import unittest
from playback_utils import clamp_font_size, MIN_FONT_SIZE, MAX_FONT_SIZE

class TestFontSizing(unittest.TestCase):
    def test_clamp_within_bounds(self):
        self.assertEqual(clamp_font_size(12, 1), 13)
    
    def test_clamp_at_upper_bound(self):
        self.assertEqual(clamp_font_size(MAX_FONT_SIZE, 1), MAX_FONT_SIZE)
    
    def test_clamp_at_lower_bound(self):
        self.assertEqual(clamp_font_size(MIN_FONT_SIZE, -1), MIN_FONT_SIZE)
```

### 8. Build and Packaging

**PyInstaller Configuration:**
- One-file mode for easy distribution: `--onefile`
- Include icon: `--icon=logo.ico`
- Add hidden imports when needed: `--hidden-import=<module>`
- Handle data files: Use `--add-data` for resources
- Test the built executable thoroughly

**Build Process:**
1. Validate Python version (3.10+, 64-bit)
2. Create clean virtual environment
3. Install dependencies from `requirements.txt`
4. Generate icon from PNG: `make_ico.py`
5. Run PyInstaller with proper flags
6. Test the resulting `.exe`
7. Create distribution package

**Build Scripts:**
- `build_exe.bat`: Automated build with logging
- `install.bat`: Complete setup for end users
- Both scripts include error handling and user feedback

**Build Validation:**
```bash
# After building, always test:
.\dist\AnomAI\AnomAI.exe  # Quick launch test
# Check for missing dependencies in error logs
# Verify all features work in the packaged version
```

### 9. Configuration Management

**Configuration Files:**
- `config.json`: Application settings (UTF-8 encoded)
- `history.json`: Chat history (UTF-8 encoded)
- Always include `ensure_ascii=False` when writing JSON
- Validate configuration before using values
- Provide sensible defaults for missing keys

**Configuration Structure:**
```python
DEFAULT_CONFIG = {
    "openai_api_key": "",
    "openai_model": "gpt-4o-mini",
    "system_prompt": "You are a helpful assistant.",
    "temperature": 0.7,
    "max_tokens": 2048,
    # ... more settings
}

def get_config_value(key: str, default: Any = None) -> Any:
    """Safely get configuration value with fallback."""
    config = load_config()
    return config.get(key, default)
```

### 10. Security Best Practices

**API Keys:**
- Never hardcode API keys in source code
- Store in configuration files (excluded from git)
- Prompt user for keys on first run
- Validate key format before using
- Clear from memory when possible

**Input Validation:**
- Validate all file paths to prevent directory traversal
- Sanitize user inputs before using in system calls
- Validate JSON structure before loading
- Check file sizes before reading

**Dependency Security:**
- Keep dependencies updated
- Review dependency changes for security issues
- Use version pinning in `requirements.txt`
- Avoid dependencies with known vulnerabilities

## Common Patterns and Anti-Patterns

### ✅ DO:

```python
# Use explicit imports
import json
import os
from typing import Optional

# Handle optional dependencies gracefully
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Use type hints
def process_message(text: str, config: dict) -> Optional[str]:
    """Process user message with proper typing."""
    if not text.strip():
        return None
    # ... processing
    return result

# Provide clear error messages
except FileNotFoundError as e:
    messagebox.showerror(
        "File Not Found",
        f"Could not find configuration file: {config_path}\n\n"
        f"Please run install.bat to set up the application."
    )

# Use context managers for file operations
with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)
```

### ❌ DON'T:

```python
# DON'T use dynamic imports
module = __import__(f"modules.{module_name}")  # BAD

# DON'T use bare except
try:
    risky_operation()
except:  # BAD - catches everything including KeyboardInterrupt
    pass

# DON'T block the UI thread
def button_click():
    result = slow_api_call()  # BAD - freezes UI
    display_result(result)

# DON'T ignore encoding
with open(file, 'r') as f:  # BAD - uses system encoding
    data = f.read()

# DON'T use relative imports for resources
file = open("../config.json")  # BAD - breaks when packaged
```

## Git Workflow

**Commit Messages:**
- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Use conventional commit format when appropriate

**Branch Strategy:**
- Feature branches: `feature/description`
- Bug fixes: `fix/description`
- Copilot branches: `copilot/description`

**Pre-Commit Checks:**
- Run tests: `python -m unittest discover -s tests`
- Check code format
- Verify batch file encodings (UTF-8 without BOM, CRLF line endings)

## Continuous Integration

The project uses GitHub Actions for CI:

- **Linting** (`lint.yml`): Validates batch file encodings and line endings
- **PyInstaller Build** (`windows-pyinstaller.yml`): Builds Windows executable
- **Windows Build** (`build-windows.yml`): Full build and test workflow

**When adding new workflows:**
- Test on `windows-latest` runner
- Cache pip dependencies for faster builds
- Upload artifacts for testing
- Include proper error handling

## Documentation Standards

**Code Comments:**
- Document complex algorithms and business logic
- Explain "why" not "what" for non-obvious code
- Use docstrings for all public functions and classes
- Keep comments up-to-date with code changes

**Docstring Format:**
```python
def calculate_tokens(text: str, model: str) -> int:
    """
    Calculate approximate token count for text.
    
    Args:
        text: Input text to tokenize
        model: Model name to determine tokenization rules
        
    Returns:
        Approximate number of tokens
        
    Raises:
        ValueError: If model is not supported
    """
    # Implementation
```

**README Updates:**
- Keep installation instructions current
- Document new features and configuration options
- Include troubleshooting for common issues
- Maintain examples in Finnish (project language)

## Performance Optimization

**Startup Time:**
- Lazy-load heavy dependencies (PIL, llama-cpp-python)
- Defer UI initialization until needed
- Cache configuration in memory
- Minimize file I/O during startup

**Runtime Performance:**
- Use appropriate data structures
- Cache computed values when beneficial
- Profile before optimizing
- Test memory usage with PyInstaller executable

**Example:**
```python
# Lazy load PIL only when needed
_pil_image_cache = None

def get_pil_image():
    global _pil_image_cache
    if _pil_image_cache is None and PIL_AVAILABLE:
        from PIL import Image
        _pil_image_cache = Image
    return _pil_image_cache
```

## Localization

**Language:**
- Primary language: Finnish (Finnish documentation and UI)
- Code comments: Can be in English or Finnish
- Error messages: User-facing messages in Finnish
- Variable names: English for consistency

**Encoding:**
- All text files: UTF-8 encoding
- Support non-ASCII characters throughout
- Test with Finnish characters (ä, ö, å, etc.)

## Summary Checklist

Before submitting code, verify:

- [ ] Code is PyInstaller-compatible (no dynamic imports)
- [ ] All imports are explicit and at the top of files
- [ ] Error handling is specific with clear user messages
- [ ] File operations use UTF-8 encoding
- [ ] File paths use `os.path.join()` or `pathlib`
- [ ] Long operations run in background threads
- [ ] UI updates happen on main thread only
- [ ] Type hints are used for function signatures
- [ ] Unit tests cover new functionality
- [ ] Tests pass: `python -m unittest discover -s tests`
- [ ] Configuration changes are backward-compatible
- [ ] New dependencies are documented and justified
- [ ] Code follows existing patterns and style
- [ ] Documentation is updated as needed
- [ ] Windows batch files use UTF-8 without BOM, CRLF line endings

---

**Remember:** This is a production application distributed to end users. Every change should prioritize stability, user experience, and maintainability. When in doubt, choose the approach that makes the PyInstaller build more reliable and the user experience more robust.

**Project Signature:** AnomFIN · Intelligent Experiences
