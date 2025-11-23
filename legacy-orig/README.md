# Legacy Installation Scripts Archive

This directory contains the original installation scripts that have been replaced by the unified cross-platform installer (`install.py`).

## Archived Files

### install.bat (Original)
- **Purpose**: Windows-specific installation script with interactive setup
- **Features**: Virtual environment creation, dependency installation, executable building
- **Issues**: Windows-only, complex logic, hard to maintain
- **Replacement**: `install.py` with `install.bat` wrapper

### install_utf8.bat (Original)  
- **Purpose**: UTF-8 wrapper for install.bat to handle console encoding
- **Features**: Console codepage switching, error logging
- **Issues**: Windows-only UTF-8 handling, complex batch scripting
- **Replacement**: Built-in UTF-8 support in `install.py`

## Migration Notes

The new unified installer (`install.py`) provides:

1. **Cross-platform support**: Windows, Linux, macOS
2. **Better error handling**: Python exceptions with clear messages
3. **Consistent behavior**: Same experience across platforms  
4. **Maintainable code**: Python instead of batch scripting
5. **Modern features**: Argument parsing, colored output, progress indication

## Usage Migration

### Old Way
```bash
# Windows only
install.bat
# or
install_utf8.bat
```

### New Way  
```bash
# Cross-platform
python install.py

# Windows wrapper (maintains compatibility)
install.bat

# With options
python install.py --no-interactive --verbose --force
```

## Backward Compatibility

The new `install.bat` is a minimal wrapper that:
- Maintains the same filename for existing users
- Provides UTF-8 support automatically  
- Delegates to the unified installer
- Shows the same success/error behavior

## Why These Were Archived

1. **Complexity**: Original scripts had 300+ lines of batch code
2. **Platform Limitation**: Windows-only, no Linux/macOS support
3. **Maintenance**: Difficult to debug and extend batch scripts  
4. **Encoding Issues**: UTF-8 handling was complex and error-prone
5. **Feature Gaps**: Missing modern installer features (progress, colors, etc.)
6. **Testing**: Hard to unit test batch scripts reliably

The unified installer solves all these issues while maintaining full compatibility.

## Restoration

If you need to restore the original installers for any reason:

```bash
# Restore original install.bat
cp legacy-orig/install.bat ./install_legacy.bat

# Restore UTF-8 wrapper  
cp legacy-orig/install_utf8.bat ./install_utf8_legacy.bat
```

These files are preserved for historical reference and emergency fallback scenarios.

---
*Archived on: 2025-11-23*  
*Replaced by: install.py (unified cross-platform installer)*