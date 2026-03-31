# Cognitive Fatigue Reaction Time Testing Suite

**A comprehensive PsychoPy-based assessment tool for measuring reaction time and memory performance under cognitive fatigue conditions.**

© 2026 Ericson P. Kimbel, II

---

## 📋 Overview

This software suite is designed for remote cognitive testing research, specifically measuring:
- Visual and audio reaction times
- Working memory performance across multiple iterations
- Hardware validation (framerate stability, keyboard consistency)
- Performance tracking under mental fatigue conditions

**Key Feature:** Designed for elderly participants with large fonts, validation retry dialogs, and comprehensive error handling.

---

## ✨ Features

### Core Tests
- **Visual Reaction Time Test** - Respond to white square stimulus
- **Audio Reaction Time Test** - Respond to audio beep (customizable frequency)
- **Memory Recognition Tests** - Two independent memory sets with multiple iterations
- **Framerate Stability Test** - Validates display performance for accurate timing
- **Keyboard Hardware Test** - Measures input latency and polling rate

### Quality Assurance
- **Forced Quality Checks** - Cannot proceed with poor framerate or keyboard performance
- **Performance Optimization Checklist** - Optional but recommended system optimizations
- **Validation Retries** - User-friendly error handling (no crashes on typos)
- **Dynamic UI Scaling** - Adapts to any screen resolution (tested 1080p - 4K)
- **DPI Awareness** - Accurate on Windows scaling settings

### Data Export
- **Text (.txt)** - Human-readable comprehensive results
- **CSV** - Visual RT and Audio RT data for analysis
- **Excel (.xls)** - Multi-sheet workbook with all test results
- **Single Folder Output** - All files in one folder for easy sharing

### Accessibility
- **Large Dialog Fonts** - 56pt for elderly participants
- **Multiple Audio Frequencies** - 250Hz, 1000Hz, 2000Hz options
- **Touchscreen Compatible** - Works with touch input (no special code needed)
- **Mouse + Keyboard** - All controls accessible both ways

---

## 🔧 Requirements

### Software
- **Python 3.8+** (recommended: Anaconda distribution)
- **PsychoPy 2023.2+**
- **wxPython** (usually included with PsychoPy)

### Hardware (Recommended)
- Windows 10/11 (primary), macOS/Linux (basic support)
- Monitor: 60Hz+ refresh rate
- Wired keyboard and mouse (for best results)
- Sound output (speakers or wired headphones)

---

## 📦 Installation

### Method 1: Anaconda (Recommended)

```bash
# 1. Install Anaconda (if not already installed)
# Download from: https://www.anaconda.com/download

# 2. Create environment and install PsychoPy
conda create -n psychopy python=3.11
conda activate psychopy
conda install -c conda-forge psychopy

# 3. Install PyInstaller (for .exe creation)
pip install pyinstaller --break-system-packages

# 4. Download the script
# Place reaction_time_test_v0.0.495_BIGGER_DIALOGS.py in your Downloads folder
```

### Method 2: pip (Alternative)

```bash
pip install psychopy wxpython pyinstaller
```

---

## 🚀 Usage

### Running the Python Script Directly

```bash
# Activate environment (Anaconda)
conda activate psychopy

# Navigate to file location
cd C:\Users\[YourName]\Downloads

# Run the script
python reaction_time_test_v0.0.495_BIGGER_DIALOGS.py
```

### Running Tests
1. Complete consent form (3 pages)
2. Complete performance checklist (optional but recommended)
3. Enter subject information
4. Tests run in this order:
   - Memory Set 1 Study
   - Visual RT Test
   - Memory Set 1 Recognition #1
   - Memory Set 2 Study
   - Audio RT Test
   - Memory Set 2 Recognition #1
   - Memory Set 1 Recognition #2

### Results Location
All results save to a single folder in your Downloads:
```
Downloads/
  └── ReactionTest_Sub[X]_Session[X]_[timestamp]/
      ├── reaction_data_sub[X]_session[X]_[timestamp].txt
      ├── reaction_data_sub[X]_session[X]_[timestamp].xls
      ├── reaction_data_sub[X]_session[X]_[timestamp]_visual_rt.csv
      └── reaction_data_sub[X]_session[X]_[timestamp]_audio_rt.csv
```

**To share results:** Just zip this entire folder and send to researcher.

---

## 🏗️ Building Standalone Executable (.exe)

### For Windows Distribution

**Full Build Command (Anaconda Prompt):**

```bash
cd C:\Users\[YourName]\Downloads

# Clean previous builds
rmdir /s /q build
rmdir /s /q dist
del *.spec

# Build .exe (this takes 5-10 minutes)
pyinstaller --exclude-module=PyQt5 --exclude-module=PyQt6 --exclude-module=psychopy.iohub --hidden-import=psychopy.visual.backends.pygletbackend --hidden-import=pyglet --hidden-import=pyglet.window --hidden-import=pyglet.gl --hidden-import=pyglet.image --hidden-import=pyglet.font --hidden-import=psychopy.visual --hidden-import=psychopy.visual.line --hidden-import=psychopy.visual.rect --hidden-import=psychopy.visual.shape --hidden-import=psychopy.visual.circle --hidden-import=psychopy.visual.polygon --hidden-import=psychopy.visual.textbox2 --hidden-import=psychopy.visual.textbox2.textbox2 --hidden-import=psychopy.sound --hidden-import=psychopy.sound.backend_ptb --name "TrialPackage" reaction_time_test_v0.0.495_BIGGER_DIALOGS.py
```

**Result:** Creates `dist\TrialPackage\` folder with:
- `TrialPackage.exe` - The executable
- `_internal\` folder - Required dependencies (MUST include!)
- Various .dll and .pyd files - Required support files

### Testing the .exe

```bash
dist\TrialPackage\TrialPackage.exe
```

### Distributing to Participants

**Create Distribution Package:**

1. **Add README** to `dist\TrialPackage\` folder (participant instructions)
2. **Zip entire folder:** Right-click `TrialPackage` → "Send to" → "Compressed folder"
3. **Upload** `TrialPackage.zip` to Google Drive/OneDrive/your server
4. **Email participants** the download link with instructions

**Important:** Must send the **entire TrialPackage folder**, not just the .exe! The .exe won't work without the `_internal\` folder.

---

## ⚙️ Configuration

### Test Configuration (Lines 49-92)

Edit these variables to customize testing:

```python
# Reaction test trials
NUM_ITERATIONS = 2  # Number of RT trials (increase for more data)
INTERVAL_MIN = 1.5  # Minimum seconds between stimuli
INTERVAL_MAX = 3.0  # Maximum seconds between stimuli

# Memory test settings
MEMORY_POOL_SIZE = 30  # Total unique images
MEMORY_SET_1_SIZE = 10  # Images to memorize in set 1
MEMORY_SET_2_SIZE = 10  # Images to memorize in set 2
MEMORY_SET_1_STUDY_TIME = 5.0  # Study time in seconds (300 = 5 min)
MEMORY_SET_2_STUDY_TIME = 5.0  # Study time in seconds

# Enable/disable test sections
RUN_CONSENT_SCREEN = True
RUN_PERFORMANCE_CHECKLIST = True
RUN_DATA_GATHERING = True
RUN_FRAMERATE_TEST = True
RUN_KEYBOARD_TEST = True
RUN_AUDIO_VERIFICATION = True
RUN_VISUAL_TEST = True
RUN_AUDIO_TEST = True
RUN_MEMORY_TEST_1 = True
RUN_MEMORY_TEST_2 = True
```

### Developer Mode
Enter `"e"` as Name to bypass validation (for testing).

---

## 📊 Data Export Format

### Text File (.txt)
Comprehensive human-readable results including:
- Subject information
- System details (resolution, refresh rate, GPU info)
- All test results with detailed metrics
- Frame-by-frame timing data
- Event log (stimulus/response timestamps)

### CSV Files
- `*_visual_rt.csv` - Visual RT data with error ranges
- `*_audio_rt.csv` - Audio RT data with error ranges

### Excel File (.xls)
Multi-sheet workbook with:
- Subject Information
- Keyboard Hardware Test
- Framerate Test Results
- Visual RT (color-coded)
- Audio RT (color-coded)
- Memory Test 1 - Iteration 1 (detailed, color-coded)
- Memory Test 1 - Iteration 2 (detailed, color-coded)
- Memory Test 2 (detailed, color-coded)
- Test Configuration
- Frame Time Data (complete log for debugging)

---

## 🎯 Performance Optimizations

### Code Optimizations
- **Deferred dropped frame calculation** - Calculated after test, not during
- **Deferred performance logging** - RT tests log after trial completion
- **Minimal measurement loops** - ~0.3ms overhead per frame (all tests)
- **GPU pre-warm** - 10s initialization for consistent performance
- **Static text rendering** - Text set once, not updated during measurement

### Recommended System Setup
- Close all background applications
- Disable Windows updates during test
- Disable antivirus real-time scanning (or add exception)
- Plug in device (not on battery)
- Use wired keyboard and mouse
- Use maximum performance power plan
- Enable both dGPU + iGPU on hybrid systems (best results!)

---

## 🐛 Troubleshooting

### "POOR" Framerate Rating
1. Close all background apps
2. Enable both dGPU + iGPU (if hybrid GPU system)
3. Set power plan to "High Performance"
4. Check GPU isn't thermal throttling
5. Restart and try again

### Keyboard Test Keeps Failing
1. Use wired USB keyboard (not wireless)
2. Start tapping IMMEDIATELY when "START TAPPING NOW!" appears
3. Tap continuously without pausing
4. Use one finger from one hand only

### SmartScreen Warning (When Running .exe)
**This is normal for unsigned executables.**
1. Click "More info"
2. Click "Run anyway"
3. Program is safe - SmartScreen warns about any unsigned .exe

---

## 🔬 Technical Details

### Timing Precision
- **Framerate measurement:** V-sync enabled, dropped frame detection
- **RT measurement:** Timestamps captured immediately on key press
- **Error calculation:** Individual per trial (frame time + input latency)
- **Typical accuracy:** ±1-2ms system latency

### Dynamic UI Scaling
- **Reference resolution:** 2560x1600 (16:10)
- **Scales to:** Any resolution (1080p, 1440p, 4K tested)
- **Aspect ratio handling:** Adjusts for 16:9, 16:10, 4:3 screens
- **DPI aware:** Works with Windows 100%-300% scaling

### Memory Test Design
- 30 unique images (shapes, colors, patterns)
- Randomized presentation order each iteration
- Click tracking (confidence measurement)
- Green border selection feedback

---

## 📝 Citation

If you use this software in your research, please cite:

```
Kimbel, E. P. II (2026). Cognitive Fatigue Reaction Time Testing Suite (Version 0.0.495) 
[Computer software]. https://github.com/[YourUsername]/[YourRepo]
```

**BibTeX:**
```bibtex
@software{kimbel2026_reaction_test,
  author = {Kimbel, Ericson P., II},
  title = {Cognitive Fatigue Reaction Time Testing Suite},
  year = {2026},
  version = {0.0.495},
  url = {https://github.com/[YourUsername]/[YourRepo]}
}
```

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Summary:** You are free to use, modify, and distribute this software. You must include the original copyright notice and license in any copies or substantial portions.

---

## 🙏 Acknowledgments

**Built with:**
- [PsychoPy](https://www.psychopy.org/) - Psychology software in Python
- [wxPython](https://wxpython.org/) - GUI toolkit
- [PyInstaller](https://pyinstaller.org/) - Python to executable bundler

**Developed by:**
- Ericson P. Kimbel, II - Primary developer and researcher

**Special thanks to:**
- Claude (Anthropic) - Development assistance and optimization
- PsychoPy community - Foundation libraries

---

## 📧 Contact

For questions, bug reports, or collaboration:
- Email: epk36@pitt.edu
- Phone: 412-607-2969

---

## 🔄 Version History

### v0.0.495 (Current - March 2026)
- Increased dialog fonts to 56pt for elderly participants
- All RT tests optimized (~0.3ms overhead)
- GPU pre-warm for consistent framerate performance
- All validation retry dialogs implemented
- Comprehensive testing on premium hardware

### v0.0.490
- Deferred dropped frame calculation in framerate test
- Optimized copyright position

### v0.0.475
- Initial stable release
- Memory crash fix
- DPI awareness implementation

---

## 🎓 Research Use

This software is designed for:
- Cognitive psychology research
- Aging and cognition studies
- Fatigue effect measurement
- Remote participant testing
- Multi-session longitudinal studies

**IRB Approved:** Designed to meet multi-IRB requirements with comprehensive informed consent.

**Data Privacy:** All data stored locally on participant's machine. No cloud upload. Participant sends results manually to researcher.

---

## 💡 Future Development Ideas

- Export to JSON format
- Real-time data visualization
- Adaptive difficulty based on performance
- Additional memory test patterns
- Multi-language support
- macOS and Linux .app/.AppImage builds

**Contributions welcome!** See CONTRIBUTING.md for guidelines.

---

**Built for Research. Optimized for Performance. Designed for Accessibility.**
