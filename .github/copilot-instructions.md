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

## Core Principles (MUST FOLLOW)

### 1. Visual Design Excellence
- **Consistency is King**: Design the UI to be as clear, stylish, and cohesive as possible
- **Unified Color Scheme**: Use a consistent color palette throughout the application
- **Typography**: Maintain consistent font families, sizes, and weights - avoid visual noise
- **Accessibility**: Always consider accessibility (e.g., contrast ratios, text sizes)
- **Current Theme**: The application uses a cyber-neon theme with dark backgrounds and bright accent colors

### 2. Error Resilience (CRITICAL)
- **Never Crash**: The application MUST NOT crash in exceptional situations!
- **Comprehensive Error Handling**: Wrap all potentially failing code in try/except blocks
- **User-Friendly Messages**: Provide friendly error messages in Finnish with suggested corrective actions
- **Debug Logging**: Log exceptions for debugging purposes, but NEVER show raw tracebacks to users
- **Graceful Degradation**: When features fail, the application should continue functioning with reduced capability

### 3. Repository Hygiene
- **No Temporary Files**: Never commit unnecessary/temporary files (*.pyc, *.tmp, .DS_Store, etc.)
- **Use .gitignore**: Add rules to prevent accidental commits of build artifacts, dependencies, and temporary files
- **Clean Commits**: Only commit intentional changes that are part of the feature or fix

## Project Structure

The repository follows a logical, clear structure:

```
AnomAI/
├── jugiai.py                    # Main application (Tkinter GUI)
├── playback_utils.py            # Playback and font utilities
├── demo_camera_feature.py       # Camera feature demonstration
├── make_ico.py                  # Icon generation utility
├── install.bat                  # Main installation script
├── install_utf8.bat             # UTF-8 wrapper for install.bat
├── build_exe.bat                # PyInstaller build script
├── start_jugiai.bat             # Application launcher
├── requirements.txt             # Python dependencies
├── config.json                  # User configuration (auto-generated, gitignored)
├── history.json                 # Chat history (auto-generated)
├── tests/                       # Unit tests (comprehensive coverage)
│   ├── test_offline_mode.py
│   ├── test_playback_utils.py
│   ├── test_model_formatting.py
│   ├── test_error_messages.py
│   ├── test_thread_validation.py
│   └── ...
├── scripts/                     # Helper scripts
│   └── verify-win-env.bat
├── .github/
│   ├── copilot-instructions.md  # This file
│   └── workflows/               # CI/CD workflows
│       ├── build-windows.yml
│       ├── lint.yml
│       └── windows-pyinstaller.yml
└── docs/                        # Documentation (markdown files)
    ├── CAMERA_FEATURE.md
    ├── LOCAL_MODEL_GUIDE.md
    └── ...
```

**Folder Organization Principles:**
- **Root**: Main application files and entry points
- **tests/**: All unit tests, one file per feature/module
- **scripts/**: Helper scripts for development and deployment
- **docs/**: Markdown documentation (feature guides, implementation notes)
- **.github/**: GitHub-specific files (workflows, Copilot instructions)
- **Build artifacts**: Excluded via .gitignore (dist/, build/, .venv/, *.pyc, etc.)

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
5. **Code Formatting:** Follow PEP 8 style guidelines, use linters (flake8, black if added)
6. **Comments:** Only add comments when necessary to explain complex logic, not obvious code

### Coding Patterns

1. **Configuration Management:**
   - Use JSON for config files (config.json, history.json)
   - Always write with UTF-8 encoding: `json.dump(..., ensure_ascii=False)`
   - Provide sensible defaults for missing settings

2. **Error Handling (CRITICAL):**
   - **NEVER allow the application to crash** - wrap all risky operations in try/except
   - Provide user-friendly error messages in Finnish with suggested corrective actions
   - Log full tracebacks to `jugiai_error.log` for debugging
   - Example pattern:
   ```python
   try:
       risky_operation()
   except SpecificError as e:
       log_error(f"Error details: {e}")
       show_user_message("Ystävällinen virheviesti käyttäjälle")
       # Continue gracefully or provide alternative
   ```
   - Gracefully degrade for missing optional dependencies (PIL, llama-cpp-python)

3. **Threading:**
   - Use threading for API calls to prevent GUI freezing
   - Validate thread counts against CPU limits
   - See `test_thread_validation.py` for patterns

4. **Offline Mode:**
   - Detect offline mode via: explicit flag, local backend, or missing API key
   - Prevent API calls when offline
   - See `test_offline_mode.py` for implementation

### Testing

**CRITICAL RULE: Never push broken code!**
- All changes MUST be tested before committing
- Tests MUST pass before pushing
- Write new tests for new functionality

**Run Tests:**
```bash
python -m unittest discover -s tests -v
```

**Test Organization:**
- Unit tests in `tests/` directory
- One test file per feature/module
- Use descriptive test names and docstrings
- Mock external dependencies (API calls, file I/O)
- Ensure tests are independent and can run in any order

**CI/CD:**
- All tests run on push/PR via GitHub Actions
- Windows-specific testing environment
- Lint checks for encoding and line endings
- Build verification for PyInstaller

**Test Coverage:**
- Aim for comprehensive coverage of new features
- Test error paths and edge cases
- Verify error handling with appropriate exceptions

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
   - Check compatibility before adding dependencies

3. **UTF-8 Safety:** Windows console encoding is fragile
   - Use UTF-8 without BOM for all text files
   - Batch scripts handle codepage switching
   - JSON files use `ensure_ascii=False`

4. **PyInstaller Compatibility:**
   - Avoid dynamic imports when possible
   - Bundle data files explicitly in .spec
   - Test .exe builds before release

5. **Library Compatibility (CRITICAL):**
   - Ensure all library versions work together (use `pip check`)
   - Update `requirements.txt` when adding or updating dependencies
   - Document WHY a dependency update was necessary
   - Test the entire application after dependency changes

## Common Tasks

### Adding a New Feature

1. **Create a feature branch** - ALWAYS work on a separate branch
2. Implement in `jugiai.py` or separate module
3. Add comprehensive unit tests in `tests/test_<feature>.py`
4. Ensure error handling with try/except blocks
5. Test both success and failure scenarios
6. Update README.MD if user-facing
7. Test with both Python and .exe versions
8. Ensure offline mode compatibility if applicable
9. Run linters and ensure code quality
10. Verify all tests pass before committing

### Fixing a Bug

1. **Create a bugfix branch** - ALWAYS work on a separate branch
2. Add failing test that reproduces the bug
3. Fix the bug with minimal changes
4. Ensure proper error handling
5. Verify test passes
6. Check for regressions in related features
7. Write clear, descriptive commit message in English

### Updating Dependencies

1. Check compatibility with existing dependencies (`pip check`)
2. Update `requirements.txt`
3. Document the reason for the update in commit message
4. Test installation with `install.bat`
5. Verify .exe build with `build_exe.bat`
6. Run full test suite
7. Update README.MD if needed

### Modifying Batch Scripts

1. Use UTF-8 encoding without BOM
2. Ensure CRLF line endings
3. Test on Windows command prompt
4. Verify lint checks pass
5. Add error handling for user-friendly output
6. Include informative error messages in Finnish
7. Use `:maybe_pause` function to keep window open on errors

### Working with UI/Visual Design

1. **Consistency First**: Follow existing color scheme and typography
2. **Color Palette**: Use the cyber-neon theme (dark backgrounds, bright accents)
3. **Typography**: Maintain consistent font sizes and families
4. **Accessibility**: Ensure good contrast ratios (WCAG AA minimum)
5. **User Experience**: Keep UI clean and uncluttered
6. **Test Visually**: Always verify visual changes match the application's style

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

## Error Handling Patterns (CRITICAL)

### Required Pattern for All Risky Operations

**NEVER let the application crash!** All potentially failing operations must be wrapped in try/except blocks:

```python
import logging

# Setup logging
logging.basicConfig(filename='jugiai_error.log', level=logging.ERROR)

def risky_operation():
    try:
        # Code that might fail
        result = potentially_failing_function()
        return result
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}", exc_info=True)
        show_error_dialog("Tiedostoa ei löytynyt", 
                         "Tarkista tiedostopolku ja yritä uudelleen.")
        return None
    except PermissionError as e:
        logging.error(f"Permission denied: {e}", exc_info=True)
        show_error_dialog("Käyttöoikeus evätty",
                         "Varmista että sinulla on oikeudet tiedostoon.")
        return None
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        show_error_dialog("Odottamaton virhe",
                         "Katso jugiai_error.log lisätiedoista.")
        return None
```

### Error Message Guidelines

1. **In Finnish**: All user-facing error messages must be in Finnish
2. **Friendly Tone**: Use polite, helpful language
3. **Actionable**: Always suggest what the user can do to fix the issue
4. **No Technical Jargon**: Avoid raw exceptions or technical details for users
5. **Log Everything**: Log full technical details to jugiai_error.log

### Examples of Good Error Messages

**Bad** (don't do this):
```python
raise Exception("API call failed")
```

**Good** (do this):
```python
try:
    response = api_call()
except requests.RequestException as e:
    logging.error(f"API call failed: {e}", exc_info=True)
    show_error_dialog(
        "Yhteysvirhe",
        "API-kutsu epäonnistui. Tarkista internet-yhteytesi ja yritä uudelleen."
    )
```

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
   - **ALWAYS wrap risky operations in try/except blocks**
   - Never commit broken code

2. **When working with batch files:**
   - Always use CRLF line endings
   - Follow existing error handling patterns
   - Include informative error messages in Finnish
   - Test on Windows environment

3. **When adding features:**
   - **Create a feature branch first**
   - Check if similar functionality exists
   - Ensure Windows compatibility
   - Test both Python and .exe versions
   - Update documentation
   - Add comprehensive error handling
   - Write clear, descriptive commit messages in English

4. **When fixing bugs:**
   - **Create a bugfix branch first**
   - Reproduce with a test first
   - Verify fix doesn't break offline mode
   - Check impact on PyInstaller build
   - Test with different configurations
   - Ensure proper error handling

5. **General Workflow:**
   - **Always use branches** - never commit directly to main
   - Write clear, descriptive commit messages in English
   - Test thoroughly before committing
   - Run linters and fix issues
   - Verify all tests pass
   - Document architectural decisions
   - Check library compatibility with `pip check`

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

## Summary: Golden Rules for AnomAI/JugiAI Development

### 🚨 CRITICAL (Never Violate)
1. **Never push broken code** - all tests must pass
2. **Never let the app crash** - always use try/except with friendly error messages in Finnish
3. **Always use branches** - never commit directly to main
4. **Always test before committing** - verify functionality and run test suite

### 🎨 Design Principles
1. Keep UI clean, stylish, and consistent with cyber-neon theme
2. Maintain unified color scheme and typography
3. Consider accessibility (contrast, text size)
4. Avoid visual noise and clutter

### 📁 Repository Hygiene
1. Never commit temporary files (*.pyc, *.tmp, .DS_Store, etc.)
2. Use .gitignore to prevent accidental commits
3. Keep folder structure logical and documented
4. Only commit intentional, reviewed changes

### 💻 Code Quality
1. Write comprehensive tests for all new features
2. Use linters and follow PEP 8
3. Add comments only when necessary
4. Log errors to jugiai_error.log, show friendly messages to users
5. Ensure library compatibility with `pip check`

### 🔄 Workflow
1. Create feature/bugfix branch
2. Make minimal, focused changes
3. Write/update tests
4. Run tests and linters
5. Write clear commit message in English
6. Document architectural decisions
7. Verify .exe build if applicable

### 📝 Commit Messages
- Write in English
- Be descriptive and clear
- Follow format: "Add feature X" or "Fix bug in Y"
- Reference issue numbers when applicable

### 🤝 When in Doubt
- Check existing code patterns
- Look at similar features for reference
- Ask via GitHub Issues if unclear
- Prefer conservative, minimal changes

Remember: **Quality over speed. A working, tested feature is better than a rushed, broken one.**
