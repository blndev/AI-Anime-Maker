# Release Notes

## Version 1.2 - 2025-02-20

### New Features
- New Analytics Dashboard (analytics_dashboard.py):
  - Real-time usage statistics and trends
  - Geographic distribution visualization with interactive world map
  - Image upload analysis with timeline and patterns
  - Generation details with style usage statistics
  - Advanced filtering system across all analytics components
  - Full-size image preview capability
  - Search functionality by Input ID or SHA1 hash
- Improved startup script (run.sh):
  - Added interactive menu for component selection
  - Option to start AI Anime Maker only
  - Option to start Analytics Dashboard only
  - Option to run both components simultaneously
  
### Improvements
- More robust version management:
  - Only considers version tags starting with 'V' (e.g., V1.0, V2.1)
  - Provides clear feedback about update availability and status
  - Continues application startup regardless of update choice
- Enhanced auto-update system in run.sh:
  - Detects and shows latest version tag (V* format) and creation date
  - Asks for user confirmation before updating
  - Continues with current version if user declines
  - Gracefully handles non-git repositories and missing version tags

## Version 1.1.1 - 2024-02-19

### New Features
- Added command-line debug mode with `--debug` flag
- Added colorized logging output for better readability

### Improvements
- Enhanced error logging with detailed stack traces in debug mode
- Standardized logging format across all modules
- Replaced print statements with proper logging levels
- Added wrapper functions for UI actions to improve code maintainability and reliability
- Improved session management using AppState instead of request sessions
- Added comprehensive unit tests for UI components:
  - Response wrapper functions
  - Image input handling with various scenarios
  - Token generation and analytics integration
  - Image hash caching and token lock mechanisms
  - Image generation with AI and fallback scenarios
  - Error handling and token management during generation
  - Edge cases (missing images, requests, descriptions)
  - Token management scenarios (enabled/disabled, validation)

### Bugfixes
- Start crashes if analytics is enabled as the model downloads is placed after initialization of the component 

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
