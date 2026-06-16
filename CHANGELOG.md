# Changelog

All notable changes to the Smart Meter Configurator will be documented in this file.

## [V1.08]
### Changed
- Tab layout restructured to match the official "EMIS Integrator" workflow.
- Complete implementation of read/write functionality for all required meter parameters.
- Stabilized meter connection and ModBus parameter reconfiguration logic.
- Rewrote and translated Help documentation into English and Simplified Chinese.

### Added
- Multilingual interface architecture (extensible), currently supporting:
  - 🇷🇺 Russian
  - 🇬 English
  - 🇳 Simplified Chinese
- Language persistence across application sessions.
- UI/UX enhancements, including dedicated icons for program settings.
- Visual meter type images for selection and switching screens.
- Dynamic window resizing upon language switch to prevent text overflow.

## [V1.07b]
### Added
- New "Energy Consumption" tab.
- Energy readings from register map tables 5.2 & 5.3 for all meter types.
- Password-protected (`0451`) energy reset button.

## [V1.07a]
### Changed
- Moved meter type switch button from Settings to the "Connection" tab.
- Rewrote Help dialog text with critical operational notes.

### Added
- Current meter type display in the "Connection" tab.
- Important note in Help: device operates correctly only with ModBus Parity set to `EVEN`.

## [V1.06b]
### Fixed
- Restored and stabilized power/RS-485 disconnection error handling (regression from V1.05).
- Fixed parameter display freeze when switching meter types.
- Fixed crash when canceling meter type selection at startup.

### Changed
- Extended ModBus parameter scan timeout to detect slow-responding devices.
- App now launches centered on screen; fullscreen maximization disabled (to be re-enabled if future UI changes require it).
- Codebase cleaned and documented following PEP-8 and Google Python Style Guide standards.

### Added
- "Searching..." dialog during device discovery to improve UX.

## [V1.06a]
### Added
- Meter type selection (single/dual-channel) at application startup.
- Meter type switching option in program settings.
- Dynamic parameter tab layout based on selected meter type.

### Known Issues
- Hot-swapping meter type without restart is not yet implemented.
- Error handling for disconnections temporarily regressed (fixed in V1.06b).

## [V1.05]
### Added
- Error handling and user notifications for meter power loss.
- Error handling and user notifications for ModBus/RS-485 disconnection.

## [V1.04]
### Added
- Functional calendar integration for device date/time configuration.
- "Sync with PC Time" button for quick synchronization.

## [V1.03]
### Added
- New "Device Parameters" tab displaying live Voltage, Current, and Power readings.

## [V1.02]
### Changed
- Refactored monolithic script into three modules: `constants.py`, `device.py`, `gui.py`.
- Code structured and formatted according to PEP-8 standards.
- UI modernized from Windows 98 style to Windows 11 aesthetic.
- Fixed ModBus parameter configuration bugs.

### Added
- Loading cursor (hourglass) for long-running operations to improve UX.

## [V1.01]
### Initial Release
- Single-file unstructured implementation.
- Basic ModBus connection parameter read/write functionality.
- Legacy Windows 98-style UI.
