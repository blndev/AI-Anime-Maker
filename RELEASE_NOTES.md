# Release Notes

## Version 1.1.1 - 2024-02-23

### New Features
- Added command-line debug mode with `--debug` flag
- Added colorized logging output for better readability

### Improvements
- Enhanced error logging with detailed stack traces in debug mode
- Standardized logging format across all modules
- Replaced print statements with proper logging levels
- Added wrapper functions for UI actions to improve code maintainability and reliability
- Improved session management using AppState instead of request sessions

## Version 1.1 - 2024-02-17

### New Features
- Analytics allows you to determine which style is mostly used and more
- Disclaimer can be shown
- UI theme can be selected via configuration file
- Rendering could be limited by enabling render token

### Improvements
- Error Handling and robustnes

### Bug Fixes
- Strength of Styles is not used, System always use default strength

## Version 1.0.0 - 2023-10-20

### New Features
- Initial release of AI-Anime-Maker! 🎉
- Transform photos into anime using Stable Diffusion.
- Support for Hugging Face models and safetensor files.
- Customizable styles for different artistic outputs.
- User-friendly configuration via `app.config` file.

### Improvements
- Enhanced user interface for better usability.

### Bug Fixes
- Initial release, no bugs to fix yet!
