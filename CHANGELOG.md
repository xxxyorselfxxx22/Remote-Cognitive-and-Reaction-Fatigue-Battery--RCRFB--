# Changelog

All notable changes to the Cognitive Fatigue Reaction Time Testing Suite.

## [0.0.495] - 2026-03-31

### Added
- Increased dialog font size from 48pt to 56pt for better readability (elderly participants)
- All dialogs now use larger fonts (consent, checklist, subject info, errors)

### Changed
- Based on v0.0.492 stable base with hybrid GPU optimization

## [0.0.492] - 2026-03-31

### Added
- Visual RT test optimization: Deferred performance logging (~1.2ms less overhead per frame)
- Audio RT test optimization: Deferred performance logging (~1.2ms less overhead per frame)
- GPU pre-warm: 10-second initialization for consistent performance on hybrid GPU systems

### Changed
- All RT tests now have ~0.3ms overhead (was ~1.5ms)
- Purer reaction time measurements

## [0.0.491] - 2026-03-30

### Added
- GPU pre-warming (10s after window creation) for consistent framerate performance
- Helps hybrid GPU systems (dGPU + iGPU) achieve better stability

### Fixed
- Memory bottom text spacing (moved down to 1.2x)

## [0.0.490] - 2026-03-30

### Added
- Deferred dropped frame calculation in framerate test
- Removed unused `current_time` variable

### Changed
- Framerate test overhead reduced to ~0.3ms per frame (was ~1ms)

## [0.0.487] - 2026-03-29

### Fixed
- Copyright position calculation optimized (removed int() multiplication overhead)
- Simplified to direct pixel offsets for better performance
- Break wording changed to "Read instructions carefully" (prevents data skew)

## [0.0.486] - 2026-03-28

### Fixed
- Infinite loop bug in Important Reminders framerate redo
- Removed broken while loops, implemented direct test approach

## [0.0.485] - 2026-03-28

### Added
- Keyboard restart screen: Help text with 5 troubleshooting steps
- ESC exit option on keyboard restart (clickable)
- Forced redo logic for POOR framerate from Important Reminders

### Fixed
- Framerate POOR screen: Hide SPACE, show only forced redo options
- Memory grid: Changed to 7 columns (wider, shorter layout)

## [0.0.484] - 2026-03-27

### Fixed
- Sound selection button spacing (increased to 400*scale_x)
- Memory image spacing (increased to 220*scale_avg)
- Memory image sizes (all uniform with scale_avg)
- Copyright overscan safe positioning
- Volume button click detection (proper scaling)

## [0.0.475] - 2026-03-26

### Fixed
- Memory crash: Added missing 'changed' and 'click_count' keys to initialization
- Prevents KeyError during Memory Test 1 Iteration 1

## [0.0.474] - 2026-03-25

### Fixed
- Memory Test data export: Save snapshots of both iterations
- Excel now correctly exports all 3 memory tests
- Completion screen: Replaced core.quit() with sys.exit(0) for clean exit

## [0.0.473] - 2026-03-24

### Added
- DPI awareness for Windows: Detects true physical resolution
- Fixes scaling issues on high-DPI displays (200%+ scaling)

### Fixed
- Window size detection now accurate on all Windows DPI settings
- All positioning issues resolved

## [0.0.460] - 2026-03-20

### Changed
- Converted ALL gui.DlgFromDict() to gui.Dlg() with addField()
- Dialogs now work in PyInstaller executables
- Consent dialog split text into chunks

### Fixed
- "list indices" errors in built executables

## [0.0.458] - 2026-03-18

### Added
- Initial stable release
- Complete test suite (Visual RT, Audio RT, Memory, Framerate, Keyboard)
- Excel export (HTML-based, no extra libraries)
- CSV export
- Dynamic UI scaling
- Progress bar system
- Performance optimization checklist

### Features
- 9,638 lines of optimized code
- Comprehensive data export (TXT + CSV + XLS)
- Touch screen compatible
- Elderly-friendly design

---

## Version Numbering

Format: `MAJOR.MINOR.PATCH`
- **MAJOR**: Breaking changes (e.g., data format changes)
- **MINOR**: New features, significant improvements
- **PATCH**: Bug fixes, minor improvements

Current: `0.0.495` indicates pre-release (not yet v1.0)

## Future Roadmap

### Planned for v1.0
- [ ] Modular code structure
- [ ] Configuration file (config.py)
- [ ] Separated test modules
- [ ] JSON export format
- [ ] macOS .app build
- [ ] Linux AppImage build

### Under Consideration
- [ ] Real-time performance graphs
- [ ] Multi-language support
- [ ] Adaptive difficulty
- [ ] Web-based version (with timing caveats)
- [ ] Database integration

---

**See [README.md](README.md) for full documentation and installation instructions.**
