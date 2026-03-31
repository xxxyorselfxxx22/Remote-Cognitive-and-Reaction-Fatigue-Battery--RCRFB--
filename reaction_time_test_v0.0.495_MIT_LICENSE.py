#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cognitive Fatigue Reaction Time Testing Suite
Version 0.0.495

A comprehensive PsychoPy-based assessment tool for measuring reaction time 
and memory performance under cognitive fatigue conditions.

Copyright (c) 2026 Ericson P. Kimbel, II

Licensed under the MIT License.
See LICENSE file in repository root for full license text.

Repository: https://github.com/[YourUsername]/cognitive-fatigue-reaction-test
Documentation: See README.md for installation and usage instructions

===============================================================================
ACKNOWLEDGMENTS
===============================================================================

Built with:
- PsychoPy (GPL v3): https://www.psychopy.org/
  Peirce, J. W., et al. (2019). PsychoPy2: Experiments in behavior made easy.
  Behavior Research Methods, 51(1), 195-203.

- wxPython: https://wxpython.org/
- PyInstaller: https://pyinstaller.org/

===============================================================================
"""

# WINDOWS DPI AWARENESS - Get true physical resolution (not scaled logical resolution)
import sys
import os
if sys.platform == 'win32':
    try:
        import ctypes
        # Set process to be DPI aware - reports true physical resolution
        # PROCESS_PER_MONITOR_DPI_AWARE = 2
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception as e:
        print(f"Note: Could not set DPI awareness: {e}")
        # Not critical - will fall back to logical resolution

from psychopy import visual, core, event, gui, sound
import wx
import random
from datetime import datetime
import statistics
import csv

# VERSION: 0.0.495
# © 2026 Ericson P. Kimbel, II
# Multi-format export: .txt + .csv + .xls (HTML-based, no extra libraries needed!)


# Function to increase dialog font sizes
def increase_dialog_font_size():
    """Increase the default font size for PsychoPy dialogs."""
    try:
        # Set multiple font types to ensure size applies everywhere
        font_size = 56  # EXTRA LARGE font - increased from 48pt for elderly participants
        
        # Default GUI font
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        font.SetPointSize(font_size)
        wx.SystemSettings.SetFont(wx.SYS_DEFAULT_GUI_FONT, font)
        
        # System font
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
        font.SetPointSize(font_size)
        wx.SystemSettings.SetFont(wx.SYS_SYSTEM_FONT, font)
        
    except:
        pass  # If wx isn't available, just continue

# ============ CONFIGURATION ============
# Reaction test configuration
NUM_ITERATIONS = 2  # Number of times the square/sound appears
INTERVAL_MIN = 1.5   # Minimum seconds between squares/sounds (15 seconds = 15.0)
INTERVAL_MAX = 3.0   # Maximum seconds between squares/sounds (30 seconds = 30.0)
PRE_EXPERIMENT_DELAY = 5.0  # Seconds of black screen before first square/sound appears

# Framerate test configuration
FRAMERATE_WARMUP_DURATION = 2.0  # DYNAMIC - calculated based on FPS (minimum 5s, more for higher FPS)
FRAMERATE_WARMUP_BASE = 5.0  # Minimum warmup time in seconds
FRAMERATE_WARMUP_FPS_BASELINE = 165  # Your testing setup (165 Hz baseline)
FRAMERATE_WARMUP_FPS_FACTOR = 2.0  # Additional seconds at baseline FPS
FRAMERATE_TEST_DURATION = 5.0  # Seconds to run framerate stability test
FRAMERATE_DISCARD_TIME_PERCENTAGE = 1.2  # Percentage of TEST DURATION to discard as settling period
# Example: 5s test → discard 1.2% = 0.06s settling → at 165 FPS = 10 frames
# Example: 10s test → discard 1.2% = 0.12s settling → at 165 FPS = 20 frames
# Scales with BOTH FPS and test duration

# Keyboard hardware test configuration
# Uses rapid tapping to measure keyboard polling rate and consistency
KEYBOARD_TAPPING_DURATION = 5.0  # Seconds to tap space as fast as possible
KEYBOARD_MIN_TAPS = int(KEYBOARD_TAPPING_DURATION * 3)  # Minimum taps = duration * 3 taps/sec (conservative)

# Memory test configuration
MEMORY_POOL_SIZE = 30  # Total number of images in recognition pool (shared by both sets)

# Memory Set 1 configuration
MEMORY_SET_1_STUDY_TIME = 5.0  # Seconds to memorize Memory Set 1 (300 = 5 minutes)
MEMORY_SET_1_SIZE = 10  # Number of images to memorize in Memory Set 1

# Memory Set 2 configuration
MEMORY_SET_2_STUDY_TIME = 5.0  # Seconds to memorize Memory Set 2 (300 = 5 minutes)
MEMORY_SET_2_SIZE = 10  # Number of images to memorize in Memory Set 2

# NOTE: MEMORY_SET_1_SIZE + MEMORY_SET_2_SIZE must be <= MEMORY_POOL_SIZE

# Test type configuration
RUN_CONSENT_SCREEN = True      # Set to True to show informed consent screen before testing
RUN_PERFORMANCE_CHECKLIST = True  # Set to True to show optimization checklist
RUN_DATA_GATHERING = True      # Set to True to show subject info dialog
RUN_FRAMERATE_TEST = True      # Set to True to run framerate stability test
RUN_KEYBOARD_TEST = True       # Set to True to run keyboard hardware test
RUN_AUDIO_VERIFICATION = True  # Set to True to run audio system verification test
RUN_VISUAL_TEST = True        # Set to True to run visual reaction test
RUN_AUDIO_TEST = True         # Set to True to run audio reaction test
RUN_MEMORY_TEST_1 = True       # Set to True to run Memory Test 1 (study + 2 iterations)
RUN_MEMORY_TEST_2 = True       # Set to True to run Memory Test 2 (study + 1 iteration)

# Consent screen configuration
CONSENT_TITLE = "Informed Consent"
CONSENT_TEXT = """
This program measures reaction time and memory performance.

TESTS: Visual/audio reaction time, memory recognition, hardware validation
TIME: Total estimated time: varies based on enabled tests

DATA: Demographics, performance metrics, system info (stored locally)

REQUIREMENTS: May need to optimize device settings for accuracy

TEST GOAL: This test is designed to induce mental fatigue to observe
cognitive performance changes. You may become tired during testing.

PARTICIPATION: Voluntary. Exit anytime (press ESC). However, to obtain
valid data, please complete the entire test without breaks if possible.

By typing "I consent" below, you agree to participate and to complete
the test without breaks to the best of your ability.
"""
# =======================================

def format_time_estimate(seconds):
    """
    Format time estimate with appropriate units.
    Returns string like "30 seconds", "5 minutes", "1 hour 15 minutes", etc.
    """
    if seconds < 60:
        # Less than 1 minute - show seconds
        return f"{int(seconds)} second{'s' if int(seconds) != 1 else ''}"
    elif seconds < 3600:
        # Less than 1 hour - show minutes (and seconds if needed)
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        if secs > 0:
            return f"{mins} minute{'s' if mins != 1 else ''} {secs} second{'s' if secs != 1 else ''}"
        else:
            return f"{mins} minute{'s' if mins != 1 else ''}"
    else:
        # 1 hour or more - show hours and minutes
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        if mins > 0:
            return f"{hours} hour{'s' if hours != 1 else ''} {mins} minute{'s' if mins != 1 else ''}"
        else:
            return f"{hours} hour{'s' if hours != 1 else ''}"

def log_performance_event(performance_log, event_type, description, reference_time):
    """Log a performance event with timestamp"""
    timestamp = core.getTime() - reference_time
    performance_log['event_log'].append({
        'timestamp': timestamp,
        'event_type': event_type,
        'description': description
    })

def log_section_boundary(performance_log, section_name, action, reference_time):
    """Log section start/end"""
    timestamp = core.getTime() - reference_time
    if action == 'START':
        performance_log['section_log'].append({
            'section': section_name,
            'start_time': timestamp,
            'end_time': None
        })
    elif action == 'END' and performance_log['section_log']:
        # Find the last entry for this section and update end_time
        for entry in reversed(performance_log['section_log']):
            if entry['section'] == section_name and entry['end_time'] is None:
                entry['end_time'] = timestamp
                break

def is_text_clicked(text_stim, mouse_obj):
    """
    Check if a text stimulus was clicked by the mouse.
    Returns True if clicked, False otherwise.
    
    Uses approximate bounding box based on text content and height.
    """
    if not mouse_obj.getPressed()[0]:  # Left click
        return False
    
    mouse_pos = mouse_obj.getPos()
    text_pos = text_stim.pos
    
    # Estimate text bounds based on text content and height
    # Approximate character width as 60% of height (typical for most fonts)
    char_width = text_stim.height * 0.6
    text_width = len(text_stim.text) * char_width
    
    # Add 20% padding for easier clicking
    text_width *= 1.2
    text_height = text_stim.height * 1.8  # Vertical padding
    
    # Check if mouse is within text bounds
    if (abs(mouse_pos[0] - text_pos[0]) < text_width / 2 and 
        abs(mouse_pos[1] - text_pos[1]) < text_height / 2):
        return True
    return False

def create_control_buttons(win, continue_text, continue_key='SPACE', quit_key='ESC', 
                           redo_text=None, redo_key=None, y_pos=-650, scale_x=1.0, scale_y=1.0, scale_avg=1.0):
    """
    Create standardized control buttons (continue, redo optional, quit).
    Returns: (continue_btn, redo_btn or None, quit_btn)
    """
    continue_btn = visual.TextStim(
        win=win,
        text=f'Press {continue_key} {continue_text}',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-450 * scale_x), int(y_pos * scale_y)) if redo_text else (int(-350 * scale_x), int(y_pos * scale_y)),
        bold=True
    )
    
    redo_btn = None
    if redo_text:
        redo_btn = visual.TextStim(
            win=win,
            text=f'Press {redo_key} {redo_text}',
            color='yellow',
            height=int(32 * scale_avg),
            pos=(int(0 * scale_x), int(y_pos * scale_y)),
            bold=True
        )
    
    quit_btn = visual.TextStim(
        win=win,
        text=f'Press {quit_key} to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(450 * scale_x), int(y_pos * scale_y)) if redo_text else (int(350 * scale_x), int(y_pos * scale_y)),
        bold=True
    )
    
    return (continue_btn, redo_btn, quit_btn)

def wait_for_key_with_mouse(win, keys_to_check, button_objects, mouse_obj, 
                            test_sections=None, current_section=None, copyright_text=None):
    """
    Universal waiting function with mouse click support.
    keys_to_check: list like ['space', 'escape'] or ['k', 'g', 'escape']
    button_objects: dict like {'space': continue_btn, 'escape': quit_btn}
    Returns: key that was pressed (from keyboard or simulated by mouse click)
    """
    global_mouse.setVisible(True)
    waiting = True
    last_click_time = 0
    
    while waiting:
        keys = event.getKeys(keys_to_check)
        current_time = core.getTime()
        
        # Check keyboard input
        for key in keys:
            if key in keys_to_check:
                return key
        
        # Check mouse clicks on buttons
        if current_time - last_click_time > 0.3:
            for key, btn_obj in button_objects.items():
                if btn_obj and is_text_clicked(btn_obj, mouse_obj):
                    print(f"User clicked {key.upper()} button")
                    last_click_time = current_time
                    core.wait(0.2)
                    return key
        
        core.wait(0.01)

def show_skip_screen(win, test_name, config_var_name, test_sections, current_section, 
                    copyright_text_small, scale_x, scale_y, scale_avg):
    """
    Display a standardized skip screen for any test.
    Returns: None (waits for user to continue or quit)
    """
    skip_screen = visual.TextStim(
        win=win,
        text=f"=== {test_name} ===\n\nThis test has been skipped.\n\n{config_var_name} is set to False.",
        color='yellow',
        height=int(48 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    continue_btn, _, quit_btn = create_control_buttons(
        win, 'to continue', 'SPACE', 'ESC', 
        y_pos=-650, scale_x=scale_x, scale_y=scale_y, scale_avg=scale_avg
    )
    
    skip_screen.draw()
    continue_btn.draw()
    quit_btn.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    print(f"{test_name} skipped - waiting for user input...")
    result = wait_for_key_with_mouse(win, ['space', 'escape'], 
                                     {'space': continue_btn, 'escape': quit_btn},
                                     global_mouse, test_sections, current_section, copyright_text_small)
    
    if result == 'escape':
        win.close()
        core.quit()

def show_simple_message(win, title, message, color='white', scale_x=1.0, scale_y=1.0, scale_avg=1.0, 
                       wait_time=2.0, show_copyright=True, copyright_text_small=None):
    """
    Display a simple message screen (for transitions, confirmations, etc.).
    Returns: None (automatically dismisses after wait_time)
    """
    msg_text = visual.TextStim(
        win=win,
        text=f"{title}\n\n{message}",
        color=color,
        height=int(48 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(0 * scale_y))
    )
    msg_text.draw()
    if show_copyright and copyright_text_small:
        copyright_text_small.draw()
    win.flip()
    core.wait(wait_time)

def calculate_framerate_metrics(frame_times, expected_fps=165, filter_delays=False, delay_threshold_multiplier=10):
    """
    Calculate comprehensive framerate metrics from frame timestamps.
    filter_delays: If True, excludes delays > (expected_frame_time * delay_threshold_multiplier)
    """
    if len(frame_times) < 2:
        return None
    
    # Calculate frame intervals (time between frames)
    intervals = [frame_times[i] - frame_times[i-1] for i in range(1, len(frame_times))]
    intervals_ms = [x * 1000 for x in intervals]  # Convert to milliseconds
    
    # Filter delays if requested (for experiment metrics)
    if filter_delays:
        expected_frame_time_ms = 1000.0 / expected_fps
        delay_threshold = expected_frame_time_ms * delay_threshold_multiplier
        intervals_ms_filtered = [x for x in intervals_ms if x < delay_threshold]
        
        # If we filtered out too many, something is wrong - use all
        if len(intervals_ms_filtered) < len(intervals_ms) * 0.1:
            intervals_ms_filtered = intervals_ms
        
        intervals_ms = intervals_ms_filtered
    
    # Frame time statistics
    avg_frame_time = statistics.mean(intervals_ms)
    min_frame_time = min(intervals_ms)
    max_frame_time = max(intervals_ms)
    frame_time_std = statistics.stdev(intervals_ms) if len(intervals_ms) > 1 else 0
    
    # Calculate FPS for each frame interval, filtering outliers based on monitor refresh rate
    fps_values = []
    max_reasonable_fps = expected_fps * 1.5  # Filter anything above 1.5x monitor refresh rate
    
    for interval_ms in intervals_ms:
        if interval_ms > 0:
            fps = 1000 / interval_ms
            # Filter out impossibly high FPS (likely measurement errors)
            if fps <= max_reasonable_fps:
                fps_values.append(fps)
    
    # If we filtered too many, use all values
    if len(fps_values) < len(intervals_ms) * 0.5:
        fps_values = [1000 / interval_ms for interval_ms in intervals_ms if interval_ms > 0]
    
    # Sort FPS values from lowest to highest
    sorted_fps = sorted(fps_values)
    
    # Average FPS
    avg_fps = 1000 / avg_frame_time if avg_frame_time > 0 else 0
    
    # Percentile FPS calculations
    def get_percentile(data, percentile):
        if len(data) == 0:
            return 0
        k = (len(data) - 1) * (percentile / 100)
        f = int(k)
        c = k - f
        if f + 1 < len(data):
            return data[f] * (1 - c) + data[f + 1] * c
        return data[f]
    
    # FPS percentiles
    # Gaming convention: "99% FPS" or "1% lows" means 99% of frames were at this FPS or HIGHER
    fps_100 = max(sorted_fps) if sorted_fps else 0  # Best single frame (maximum)
    fps_99 = get_percentile(sorted_fps, 1)   # 99% FPS: 1st percentile (99% of frames at or above)
    
    # Calculate average of worst 1% and 0.1% of frames (more meaningful than just percentile)
    one_percent_count = max(1, int(len(sorted_fps) * 0.01))
    worst_1_percent = sorted_fps[:one_percent_count]
    fps_1 = statistics.mean(worst_1_percent) if worst_1_percent else fps_99
    
    point_one_percent_count = max(1, int(len(sorted_fps) * 0.001))
    worst_01_percent = sorted_fps[:point_one_percent_count]
    fps_01 = statistics.mean(worst_01_percent) if worst_01_percent else fps_1
    
    # Frame pacing consistency (coefficient of variation)
    frame_pacing_cv = (frame_time_std / avg_frame_time) * 100 if avg_frame_time > 0 else 0
    
    # Input latency estimate (avg frame time + half a frame)
    estimated_input_latency = avg_frame_time + (avg_frame_time / 2)
    
    return {
        'avg_frame_time': avg_frame_time,
        'min_frame_time': min_frame_time,
        'max_frame_time': max_frame_time,
        'frame_time_std': frame_time_std,
        'frame_pacing_cv': frame_pacing_cv,
        'avg_fps': avg_fps,
        'fps_100': fps_100,
        'fps_99': fps_99,
        'fps_1': fps_1,
        'fps_01': fps_01,
        'estimated_input_latency': estimated_input_latency
    }

def create_memory_images(win, num_images=30):
    """Create unique visual patterns for memory test with proper contrast."""
    images = []
    colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'cyan', 'magenta', 
              'pink', 'brown', 'lime', 'navy', 'teal', 'coral', 'gold']
    shapes = ['circle', 'square', 'triangle']
    
    # Function to calculate relative luminance
    def get_luminance(color_name):
        color_map = {
            'red': (1.0, 0.0, 0.0), 'blue': (0.0, 0.0, 1.0), 'green': (0.0, 0.5, 0.0),
            'yellow': (1.0, 1.0, 0.0), 'purple': (0.5, 0.0, 0.5), 'orange': (1.0, 0.647, 0.0),
            'cyan': (0.0, 1.0, 1.0), 'magenta': (1.0, 0.0, 1.0), 'pink': (1.0, 0.753, 0.796),
            'brown': (0.647, 0.165, 0.165), 'lime': (0.0, 1.0, 0.0), 'navy': (0.0, 0.0, 0.5),
            'teal': (0.0, 0.5, 0.5), 'coral': (1.0, 0.498, 0.314), 'gold': (1.0, 0.843, 0.0),
            'white': (1.0, 1.0, 1.0), 'black': (0.0, 0.0, 0.0)
        }
        rgb = color_map.get(color_name, (0.5, 0.5, 0.5))
        
        # Calculate relative luminance
        def linearize(c):
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        
        r, g, b = [linearize(c) for c in rgb]
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    # Function to calculate contrast ratio
    def contrast_ratio(color1, color2):
        l1 = get_luminance(color1)
        l2 = get_luminance(color2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)
    
    for i in range(num_images):
        # Create unique pattern for each image
        color_idx = i % len(colors)
        main_color = colors[color_idx]
        shape_type = shapes[i % 3]
        pattern_type = (i // 3) % 3  # Different pattern arrangements
        
        # Create container for this image's elements
        image_elements = []
        
        if shape_type == 'circle':
            shape = visual.Circle(win, radius=int(60 * scale_avg), fillColor=main_color,  # SCALED radius
                                lineColor='white', lineWidth=3)
        elif shape_type == 'square':
            shape = visual.Rect(win, width=int(120 * scale_x), height=int(120 * scale_avg), fillColor=main_color,
                              lineColor='white', lineWidth=3)
        else:  # triangle
            # SCALED vertices for consistent size with other shapes
            tri_size = int(60 * scale_avg)
            shape = visual.ShapeStim(win, vertices=[(-tri_size, -tri_size), (tri_size, -tri_size), (0, tri_size)],
                                   fillColor=main_color, lineColor='white', lineWidth=3)
        
        # Choose secondary color with proper contrast
        secondary_color = 'white'  # Default
        if contrast_ratio(main_color, 'white') < 4.5:
            # White doesn't have enough contrast, use black
            secondary_color = 'black'
        
        # Add secondary element based on pattern type
        if pattern_type == 0:
            # Add small circle in corner - SCALED
            secondary = visual.Circle(win, radius=int(20 * scale_avg), pos=(int(40 * scale_x), int(40 * scale_y)),
                                    fillColor=secondary_color, lineColor=main_color)
            image_elements = [shape, secondary]
        elif pattern_type == 1:
            # Add horizontal line - SCALED
            secondary = visual.Rect(win, width=int(100 * scale_x), height=int(10 * scale_avg), pos=(int(0 * scale_x), int(0 * scale_y)),
                                  fillColor=secondary_color, lineColor=secondary_color)
            image_elements = [shape, secondary]
        else:
            # Just the shape
            image_elements = [shape]
        
        images.append({
            'id': i, 
            'elements': image_elements, 
            'selected': False,
            'changed': False,  # Track if selection was changed
            'click_count': 0   # Track number of clicks
        })
    
    return images

# ===== STEP 1: GET SUBJECT INFORMATION =====
print("=" * 80)
print("STEP 1: SUBJECT INFORMATION")
print("=" * 80)

# Validate configuration
if (RUN_MEMORY_TEST_1 or RUN_MEMORY_TEST_2) and (MEMORY_SET_1_SIZE + MEMORY_SET_2_SIZE > MEMORY_POOL_SIZE):
    print(f"ERROR: Memory set sizes ({MEMORY_SET_1_SIZE} + {MEMORY_SET_2_SIZE} = {MEMORY_SET_1_SIZE + MEMORY_SET_2_SIZE}) exceed pool size ({MEMORY_POOL_SIZE})")
    print("Please reduce MEMORY_SET_1_SIZE and/or MEMORY_SET_2_SIZE, or increase MEMORY_POOL_SIZE")
    core.quit()

# ===== PRE-DIALOG NOTICE MOVED TO AFTER WINDOW CREATION =====
# (This section now appears after line ~800 to fix 'win' not defined error)

# Initialize wx.App for dialog font modifications to work properly
print("Initializing wx.App for dialog support...")
try:
    app = wx.App(False)  # Create app without showing it
    print("✓ wx.App initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize wx.App: {e}")
    app = None

# Increase dialog font sizes for better readability
increase_dialog_font_size()

# ===== INFORMED CONSENT SCREEN =====
if RUN_CONSENT_SCREEN:
    print("=" * 80)
    print("INFORMED CONSENT SCREEN")
    print("=" * 80)
    
    # Calculate estimated total time based on enabled tests
    estimated_total_time = 0
    if RUN_FRAMERATE_TEST:
        estimated_total_time += FRAMERATE_WARMUP_DURATION + FRAMERATE_TEST_DURATION + 5  # +5 for display/approval
    if RUN_KEYBOARD_TEST:
        estimated_total_time += KEYBOARD_TAPPING_DURATION + 5  # +5 for instructions/results
    if RUN_MEMORY_TEST_1:
        estimated_total_time += MEMORY_SET_1_STUDY_TIME + (MEMORY_SET_1_SIZE * 20) * 2  # Study + 2 recognition tests
    if RUN_VISUAL_TEST:
        estimated_total_time += PRE_EXPERIMENT_DELAY + (NUM_ITERATIONS * ((INTERVAL_MIN + INTERVAL_MAX) / 2))
    if RUN_MEMORY_TEST_2:
        estimated_total_time += MEMORY_SET_2_STUDY_TIME + (MEMORY_SET_2_SIZE * 20)  # Study + 1 recognition test
    if RUN_AUDIO_TEST:
        estimated_total_time += PRE_EXPERIMENT_DELAY + (NUM_ITERATIONS * ((INTERVAL_MIN + INTERVAL_MAX) / 2))
    
    # Format estimated time
    est_hours = int(estimated_total_time // 3600)
    est_mins = int((estimated_total_time % 3600) // 60)
    est_secs = int(estimated_total_time % 60)
    
    if est_hours > 0:
        if est_mins > 0:
            time_estimate_str = f"roughly {est_hours} hour{'s' if est_hours != 1 else ''} {est_mins} minutes"
        else:
            time_estimate_str = f"roughly {est_hours} hour{'s' if est_hours != 1 else ''}"
    elif est_mins > 0:
        time_estimate_str = f"roughly {est_mins} minutes"
    else:
        time_estimate_str = f"roughly {est_secs} seconds"
    
    # Update consent text with calculated time
    consent_text_with_time = CONSENT_TEXT.replace("Total estimated time: varies based on enabled tests", 
                                                   f"Total estimated time: {time_estimate_str}")
    
    print("\n" + "=" * 80)
    print("INFORMED CONSENT SCREEN (3 pages)")
    print("=" * 80)
    
    # MULTI-PAGE CONSENT for better display in executables
    
    # PAGE 1/3: Overview
    consent_page1 = gui.Dlg(title=f'Informed Consent (Page 1/3) | © 2026 Ericson P. Kimbel, II | v0.0.495')
    consent_page1.addText("INFORMED CONSENT - Page 1 of 3")
    consent_page1.addText("")
    consent_page1.addText("This program measures reaction time and memory performance.")
    consent_page1.addText("")
    consent_page1.addText("TESTS INCLUDED:")
    consent_page1.addText("  - Visual/audio reaction time")
    consent_page1.addText("  - Memory recognition")  
    consent_page1.addText("  - Hardware validation")
    consent_page1.addText("")
    consent_page1.addText(f"ESTIMATED TIME: {time_estimate_str}")
    consent_page1.addText("")
    consent_page1.addText("DATA COLLECTED: Demographics, performance metrics,")
    consent_page1.addText("                system info (stored locally)")
    consent_page1.addText("")
    consent_page1.addText("Click OK to continue to Page 2 of 3")
    
    page1_result = consent_page1.show()
    if not consent_page1.OK:
        core.quit()
    
    # PAGE 2/3: Requirements and Goals
    consent_page2 = gui.Dlg(title=f'Informed Consent (Page 2/3) | © 2026 Ericson P. Kimbel, II | v0.0.495')
    consent_page2.addText("INFORMED CONSENT - Page 2 of 3")
    consent_page2.addText("")
    consent_page2.addText("REQUIREMENTS:")
    consent_page2.addText("  - May need to optimize device settings for accuracy")
    consent_page2.addText("")
    consent_page2.addText("TEST GOAL:")
    consent_page2.addText("  - This test is designed to induce mental fatigue")
    consent_page2.addText("  - Observes cognitive performance changes")
    consent_page2.addText("  - You may become tired during testing")
    consent_page2.addText("")
    consent_page2.addText("PARTICIPATION:")
    consent_page2.addText("  - Voluntary - exit anytime (press ESC)")
    consent_page2.addText("  - For valid data, complete test without breaks")
    consent_page2.addText("")
    consent_page2.addText("Click OK to continue to Page 3 of 3")
    
    page2_result = consent_page2.show()
    if not consent_page2.OK:
        core.quit()
    
    # PAGE 3/3: Agreement and Input - RETRY LOOP until valid
    consent_valid = False
    while not consent_valid:
        consent_page3 = gui.Dlg(title=f'Informed Consent (Page 3/3) | © 2026 Ericson P. Kimbel, II | v0.0.495')
        consent_page3.addText("INFORMED CONSENT - Page 3 of 3")
        consent_page3.addText("")
        consent_page3.addText("By typing 'I consent' below, you agree to:")
        consent_page3.addText("")
        consent_page3.addText("  - Participate in this research study")
        consent_page3.addText("  - Complete test without breaks (to best of ability)")
        consent_page3.addText("  - Allow de-identified data for research")
        consent_page3.addText("")
        consent_page3.addText("Type 'I consent' below to proceed:")
        consent_page3.addField('Your response:', initial='                                                  ')
        
        consent_result = consent_page3.show()
        
        # If user cancels, quit
        if not consent_page3.OK:
            print("\n✗ Participant declined consent (cancelled dialog)")
            print("Exiting program...")
            core.quit()
        
        # Get what user typed
        consent_input_text = consent_result[0].strip() if consent_result and len(consent_result) > 0 else ""
        
        # Check if valid
        if consent_input_text.upper() == "I CONSENT":
            # Valid!
            consent_valid = True
            consent_status = "CONSENTED"
            print(f"\n✓ Participant has provided informed consent")
            print(f"  User typed: '{consent_input_text}'")
            print(f"  Estimated test time: {time_estimate_str}")
            print("Proceeding with testing...")
        else:
            # Invalid - show error dialog and retry
            if consent_input_text == "":
                error_msg = "You must type 'I consent' to proceed."
            else:
                error_msg = f"You typed: '{consent_input_text}'\n\nYou must type: I consent"
            
            error_dlg = gui.Dlg(title='Consent Error | © 2026 Ericson P. Kimbel, II | v0.0.495')
            error_dlg.addText("Incorrect Input")
            error_dlg.addText("")
            error_dlg.addText(error_msg)
            error_dlg.addText("")
            error_dlg.addText("(Not case-sensitive)")
            error_dlg.addText("")
            error_dlg.addText("Click OK to try again or Cancel to exit.")
            
            error_result = error_dlg.show()
            
            if not error_dlg.OK:
                print("\n✗ Participant declined consent")
                core.quit()
            
            # Loop continues, will show consent page 3 again
            print("Retrying consent input...")
    
    # Consent validated - continue
else:
    # Consent screen skipped
    consent_status = "SKIPPED"
    consent_input_text = "[Consent screen skipped]"
    print("=" * 80)
    print("INFORMED CONSENT SCREEN SKIPPED")
    print("RUN_CONSENT_SCREEN is set to False")
    print("=" * 80)

# ===== STEP 0: PERFORMANCE OPTIMIZATION CHECKLIST =====
if RUN_PERFORMANCE_CHECKLIST and RUN_DATA_GATHERING:
    print("=" * 80)
    print("STEP 0: PERFORMANCE OPTIMIZATION CHECKLIST")
    print("=" * 80)
    
    # Create checklist dialog
    checklist_info = {
        'Using ONLY 1 monitor (laptop screen if laptop, 1 monitor if desktop)': False,
        'Using WIRED over-ear headphones (NOT wireless, NOT earbuds)': False,
        'Closed all background tasks, apps, and activities': False,
        'Disabled Windows/OS automatic updates during test': False,
        'Disabled antivirus real-time scanning (or added exception)': False,
        'Plugged device in for maximum power (not on battery)': False,
        'Using wired keyboard (not wireless/Bluetooth)': False,
        'Using wired mouse (not wireless/Bluetooth)': False,
        'Testing in a quiet, low-distraction area': False,
        'Sound is on and working (verified audio output)': False,
        'Disabled all notifications (OS, apps, messages)': False,
        'Drivers are up to date and stable (GPU, chipset, USB)': False,
        'Using discrete GPU only (disabled integrated GPU if applicable)': False,
        'Monitor set to native resolution and MAXIMUM native refresh rate': False,
        'Device set to maximum performance mode (OS + OEM software)': False,
        'Disabled RGB/lighting effects and monitoring software': False,
        'Screen brightness set to stable level (not auto-brightness)': False
    }
    
    # EXECUTABLE-COMPATIBLE: Use simple gui.Dlg with checkboxes
    checklist_dlg = gui.Dlg(title='Performance Optimization Checklist | © 2026 Ericson P. Kimbel, II | v0.0.495')
    checklist_dlg.addText("OPTIONAL PERFORMANCE OPTIMIZATIONS")
    checklist_dlg.addText("")
    checklist_dlg.addText("These optimizations improve data quality by reducing hardware")
    checklist_dlg.addText("variation and latency spikes. However, they are NOT REQUIRED.")
    checklist_dlg.addText("")
    checklist_dlg.addText("Check off any you have completed. You can continue regardless")
    checklist_dlg.addText("of how many are checked. If your system performance is stable,")
    checklist_dlg.addText("unchecked items will not affect data validity.")
    checklist_dlg.addText("")
    checklist_dlg.addText("Check all that apply:")
    checklist_dlg.addText("")
    
    # Add each item as a checkbox field
    checklist_dlg.addField('1 monitor only', initial=False)
    checklist_dlg.addField('Wired over-ear headphones', initial=False)
    checklist_dlg.addField('Closed background tasks', initial=False)
    checklist_dlg.addField('Disabled auto updates', initial=False)
    checklist_dlg.addField('Disabled antivirus scanning', initial=False)
    checklist_dlg.addField('Plugged in (not battery)', initial=False)
    checklist_dlg.addField('Wired keyboard', initial=False)
    checklist_dlg.addField('Wired mouse', initial=False)
    checklist_dlg.addField('Quiet testing area', initial=False)
    checklist_dlg.addField('Sound working', initial=False)
    checklist_dlg.addField('Disabled notifications', initial=False)
    checklist_dlg.addField('Drivers up to date', initial=False)
    checklist_dlg.addField('Discrete GPU only', initial=False)
    checklist_dlg.addField('Native res + max refresh', initial=False)
    checklist_dlg.addField('Performance mode', initial=False)
    checklist_dlg.addField('Disabled RGB software', initial=False)
    checklist_dlg.addField('Stable brightness', initial=False)
    
    checklist_result = checklist_dlg.show()
    
    # If user cancels, quit
    if not checklist_dlg.OK:
        core.quit()
    
    # Map results back to full checklist items
    checklist_items_full = [
        'Using ONLY 1 monitor (laptop screen if laptop, 1 monitor if desktop)',
        'Using WIRED over-ear headphones (NOT wireless, NOT earbuds)',
        'Closed all background tasks, apps, and activities',
        'Disabled Windows/OS automatic updates during test',
        'Disabled antivirus real-time scanning (or added exception)',
        'Plugged device in for maximum power (not on battery)',
        'Using wired keyboard (not wireless/Bluetooth)',
        'Using wired mouse (not wireless/Bluetooth)',
        'Testing in a quiet, low-distraction area',
        'Sound is on and working (verified audio output)',
        'Disabled all notifications (OS, apps, messages)',
        'Drivers are up to date and stable (GPU, chipset, USB)',
        'Using discrete GPU only (disabled integrated GPU if applicable)',
        'Monitor set to native resolution and MAXIMUM native refresh rate',
        'Device set to maximum performance mode (OS + OEM software)',
        'Disabled RGB/lighting effects and monitoring software',
        'Screen brightness set to stable level (not auto-brightness)'
    ]
    
    checklist_info = {}
    for i, item in enumerate(checklist_items_full):
        checklist_info[item] = checklist_result[i] if i < len(checklist_result) else False
    
    # Count and display checklist results
    items_completed = sum(1 for checked in checklist_info.values() if checked)
    total_items = len(checklist_info)
    
    # Store critical values for later use
    using_over_ear_headphones = checklist_info['Using WIRED over-ear headphones (NOT wireless, NOT earbuds)']
    using_single_monitor = checklist_info['Using ONLY 1 monitor (laptop screen if laptop, 1 monitor if desktop)']
    
    print("\nPerformance Optimization Checklist:")
    print(f"  Completed: {items_completed}/{total_items} optimizations")
    print("")
    for item, checked in checklist_info.items():
        status = "✓" if checked else "✗"
        print(f"  {status} {item}")
else:
    # Performance checklist skipped - set default values
    using_over_ear_headphones = False
    using_single_monitor = False
    print("=" * 80)
    print("STEP 0: PERFORMANCE OPTIMIZATION CHECKLIST SKIPPED")
    if not RUN_DATA_GATHERING:
        print("RUN_DATA_GATHERING is set to False")
    else:
        print("RUN_PERFORMANCE_CHECKLIST is set to False")
    print("=" * 80)
    
    checklist_info = {
        'Closed all background tasks, apps, and activities': False,
        'Disabled Windows/OS automatic updates during test': False,
        'Disabled antivirus real-time scanning (or added exception)': False,
        'Plugged device in for maximum power (not on battery)': False,
        'Using wired keyboard (not wireless/Bluetooth)': False,
        'Using wired mouse (not wireless/Bluetooth)': False,
        'Testing in a quiet, low-distraction area': False,
        'Sound is on and working (verified audio output)': False,
        'Disabled all notifications (OS, apps, messages)': False,
        'Drivers are up to date and stable (GPU, chipset, USB)': False,
        'Using discrete GPU only (disabled integrated GPU if applicable)': False,
        'Monitor set to native resolution and MAXIMUM native refresh rate': False,
        'Device set to maximum performance mode (OS + OEM software)': False,
        'Disabled RGB/lighting effects and monitoring software': False,
        'Screen brightness set to stable level (not auto-brightness)': False
    }

# ===== STEP 1: SUBJECT INFORMATION =====
if RUN_DATA_GATHERING:
    # RETRY LOOP for subject information validation
    subject_info_valid = False
    
    while not subject_info_valid:
        # EXECUTABLE-COMPATIBLE: Use simple gui.Dlg (not DlgFromDict)
        dlg = gui.Dlg(title='Subject Information | © 2026 Ericson P. Kimbel, II | v0.0.495')
        dlg.addField('Name:', initial='                                                  ')
        dlg.addField('Age (18-150):', initial='                                                  ')
        dlg.addField('Sex (M/F/Male/Female):', initial='                                                  ')
        dlg.addField('Subject Number:', initial='                                                  ')
        dlg.addField('Session Number (1/2):', initial='1                                                 ')
        dlg.addField('Sleep Apnea (Y/N/Yes/No):', initial='                                                  ')
        dlg.addField('Health conditions (ADHD, ADD, meds, or "None"):', initial='                                                  ')
        
        subject_result = dlg.show()

        # If user cancels, quit
        if not dlg.OK:
            core.quit()
        
        # Store results
        subject_info = {
            'Name': subject_result[0].strip() if len(subject_result) > 0 else '',
            'Age': subject_result[1].strip() if len(subject_result) > 1 else '',
            'Sex': subject_result[2].strip() if len(subject_result) > 2 else '',
            'Subject Number': subject_result[3].strip() if len(subject_result) > 3 else '',
            'Session Number': subject_result[4].strip() if len(subject_result) > 4 else '1',
            'Sleep Apnea': subject_result[5].strip() if len(subject_result) > 5 else '',
            'Health conditions affecting cognition (ADHD, ADD, meds, etc. or "None")': subject_result[6].strip() if len(subject_result) > 6 else ''
        }

        # Check if this is developer mode (hidden feature)
        is_developer = subject_info['Name'].strip().upper() == 'E'
        
        if is_developer:
            # Developer mode - bypass validation
            print("Developer mode activated")
            subject_info['Sleep Apnea Treatment'] = 'N/A'
            subject_info_valid = True
        else:
            # Normal validation
            validation_errors = []
            
            # Validate Name
            if not subject_info['Name'].strip():
                validation_errors.append("- Name cannot be empty")
        
            # Validate Age
            age_str = subject_info['Age'].strip()
            if not age_str:
                validation_errors.append("- Age cannot be empty")
            else:
                try:
                    age_val = int(age_str)
                    if age_val < 18 or age_val > 150:
                        validation_errors.append(f"- Age must be between 18 and 150. You entered: {age_val}")
                    else:
                        subject_info['Age'] = str(age_val)  # Standardize
                except ValueError:
                    validation_errors.append(f"- Age must be a valid number. You entered: '{age_str}'")
        
            # Validate Sex
            sex_input = subject_info['Sex'].strip().upper()
            if not sex_input:
                validation_errors.append("- Sex cannot be empty")
            elif sex_input in ['M', 'MALE']:
                subject_info['Sex'] = 'M'  # Standardize to M
            elif sex_input in ['F', 'FEMALE']:
                subject_info['Sex'] = 'F'  # Standardize to F
            else:
                validation_errors.append(f"- Sex must be 'M', 'F', 'Male', or 'Female'. You entered: '{sex_input}'")
        
            # Validate Subject Number
            subject_num_str = subject_info['Subject Number'].strip()
            if not subject_num_str:
                validation_errors.append("- Subject Number cannot be empty")
            else:
                try:
                    subject_num_val = int(subject_num_str)
                    if subject_num_val <= 0:
                        validation_errors.append(f"- Subject Number must be greater than 0. You entered: {subject_num_val}")
                    else:
                        subject_info['Subject Number'] = str(subject_num_val)
                except ValueError:
                    validation_errors.append(f"- Subject Number must be a valid integer. You entered: '{subject_num_str}'")
        
            # Validate Session Number
            session_input = subject_info['Session Number'].strip()
            if not session_input:
                validation_errors.append("- Session Number cannot be empty")
            elif session_input not in ['1', '2']:
                validation_errors.append(f"- Session Number must be '1' or '2'. You entered: '{session_input}'")
            # Session Number already stored correctly
            
            # Validate Sleep Apnea
            sleep_apnea_input = subject_info['Sleep Apnea'].strip().upper()
            if not sleep_apnea_input:
                validation_errors.append("- Sleep Apnea field cannot be empty (enter Y or N)")
            elif sleep_apnea_input in ['Y', 'YES']:
                subject_info['Sleep Apnea'] = 'Yes'
            elif sleep_apnea_input in ['N', 'NO']:
                subject_info['Sleep Apnea'] = 'No'
            else:
                validation_errors.append(f"- Sleep Apnea must be 'Y' or 'N'. You entered: '{sleep_apnea_input}'")
    
            # If there are validation errors, show dialog and retry
            if validation_errors:
                print("\n" + "=" * 80)
                print("VALIDATION ERRORS:")
                print("=" * 80)
                for error in validation_errors:
                    print(error)
                print("=" * 80)
                print("\nShowing error dialog - user can retry...")
                
                # Show error dialog
                error_dlg = gui.Dlg(title='Input Errors - Please Correct | © 2026 Ericson P. Kimbel, II | v0.0.495')
                error_dlg.addText("The following errors were found:")
                error_dlg.addText("")
                for error in validation_errors:
                    error_dlg.addText(error)
                error_dlg.addText("")
                error_dlg.addText("Click OK to re-enter your information.")
                error_dlg.addText("Click Cancel to exit.")
                
                error_result = error_dlg.show()
                
                if not error_dlg.OK:
                    # User chose to exit
                    print("User cancelled after validation errors")
                    core.quit()
                
                # Loop back - will show subject info dialog again
                continue
            
            # No errors - check sleep apnea follow-up
            sleep_apnea_input = subject_info['Sleep Apnea'].strip().upper()
            has_sleep_apnea = sleep_apnea_input in ['Y', 'YES']
            sleep_apnea_treatment = 'N/A'
            
            if has_sleep_apnea:
                treatment_dlg = gui.Dlg(title='Sleep Apnea Follow-up | © 2026 Ericson P. Kimbel, II | v0.0.495')
                treatment_dlg.addText("You indicated you have sleep apnea.")
                treatment_dlg.addField('Treatment Method:', initial='                                                  ')
                
                treatment_result = treatment_dlg.show()
                
                if treatment_dlg.OK and len(treatment_result) > 0:
                    sleep_apnea_treatment = treatment_result[0].strip()
                    if not sleep_apnea_treatment:
                        sleep_apnea_treatment = 'Not specified'
                else:
                    sleep_apnea_treatment = 'Not provided'
            
            subject_info['Sleep Apnea Treatment'] = sleep_apnea_treatment
            subject_info_valid = True
    
    # Validation complete - exit while loop

else:
    # Data gathering skipped - use default values
    print("=" * 80)
    print("STEP 1: SUBJECT INFORMATION - SKIPPED")
    print("RUN_DATA_GATHERING is set to False")
    print("Using default subject information")
    print("=" * 80)
    
    subject_info = {
        'Name': 'TestUser',
        'Age': '25',
        'Sex': 'M',
        'Subject Number': '999',
        'Session Number': '1',
        'Sleep Apnea': 'No',
        'Sleep Apnea Treatment': 'N/A'
    }


# Create unique filename with subject number, session, and timestamp
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
subject_number = subject_info['Subject Number'].replace(' ', '_')
session_number = subject_info['Session Number']

# Get Downloads folder path
downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')

# Create OUTPUT FOLDER for all result files (easier for participants to send)
output_folder_name = f"ReactionTest_Sub{subject_number}_Session{session_number}_{timestamp}"
output_folder_path = os.path.join(downloads_folder, output_folder_name)

# Create the output folder if it doesn't exist
try:
    os.makedirs(output_folder_path, exist_ok=True)
    print(f"\n✓ Created output folder: {output_folder_path}")
except Exception as e:
    print(f"Warning: Could not create output folder: {e}")
    print("Files will be saved to Downloads folder directly")
    output_folder_path = downloads_folder

# Create full file path (inside output folder)
filename = f"reaction_data_sub{subject_number}_session{session_number}_{timestamp}.txt"
OUTPUT_FILE = os.path.join(output_folder_path, filename)

print(f"\nAll data files will be saved to folder:")
print(f"  {output_folder_name}/")
print(f"  Location: Downloads folder")
print(f"\nParticipants: Just send this ONE FOLDER back to researcher!")

# ===== STEP 2: CREATE WINDOW AND SCAN FRAMERATE =====
print("\n" + "=" * 80)
print("STEP 2: SCANNING SCREEN FRAMERATE")
print("=" * 80)

# Create window with v-sync enabled
win = visual.Window(
    color='black',
    units='pix',
    fullscr=True,  # Fullscreen mode - auto-detects and uses native resolution
    waitBlanking=True,  # Enable v-sync (wait for vertical blank)
    monitor='testMonitor',
    useFBO=True,  # Use framebuffer objects for better performance
    allowGUI=False  # Disable GUI elements for better performance
)

# Immediately clear to black to prevent startup flash
win.flip()
core.wait(0.1)

# ===== GPU/SYSTEM PRE-WARMING =====
# Pre-warm GPU and display pipeline for consistent performance
# This ensures the INITIAL framerate test has the same warm system as redo tests
print("\n" + "=" * 80)
print("PRE-WARMING GPU AND DISPLAY SYSTEM")
print("=" * 80)
print("Running blank renders for 10 seconds to fully warm GPU...")
print("This ensures consistent performance for all tests.")

prewarm_start = core.getTime()
prewarm_duration = 10.0  # 10 seconds of blank rendering

while core.getTime() - prewarm_start < prewarm_duration:
    # Just flip blank screen - warms up GPU/display pipeline
    win.flip()

print(f"✓ GPU pre-warm complete ({prewarm_duration:.0f} seconds)")
print("System ready for testing")
print("=" * 80)

# ===== DYNAMIC UI SCALING FOR REMOTE TESTING =====
# Reference setup: 13.4" screen, 2560x1600 resolution (16:10 aspect ratio)
print("\n" + "=" * 80)
print("DYNAMIC UI SCALING INITIALIZATION")
print("=" * 80)

REFERENCE_WIDTH = 2560
REFERENCE_HEIGHT = 1600
REFERENCE_ASPECT = REFERENCE_WIDTH / REFERENCE_HEIGHT  # 1.6 (16:10)

# Get current screen resolution
current_width, current_height = win.size
current_aspect = current_width / current_height

print(f"Reference resolution: {REFERENCE_WIDTH}x{REFERENCE_HEIGHT} (aspect: {REFERENCE_ASPECT:.3f})")
print(f"Current resolution: {current_width}x{current_height} (aspect: {current_aspect:.3f})")

# Calculate base scaling factors
scale_x_base = current_width / REFERENCE_WIDTH
scale_y_base = current_height / REFERENCE_HEIGHT

# Adjust for aspect ratio differences
# If aspect ratios match, no adjustment needed
# If current is wider (16:9 vs 16:10), reduce x scaling to prevent stretching
# If current is narrower (4:3 vs 16:10), reduce y scaling
if abs(current_aspect - REFERENCE_ASPECT) > 0.01:  # Different aspect ratio
    if current_aspect > REFERENCE_ASPECT:
        # Wider screen (e.g., 16:9 when reference is 16:10)
        # Use height-based scaling to prevent horizontal stretching
        scale_x = scale_y_base
        scale_y = scale_y_base
        print(f"Aspect adjustment: Current is wider - using height-based scaling")
    else:
        # Narrower screen (e.g., 4:3 when reference is 16:10)
        # Use width-based scaling to prevent vertical stretching
        scale_x = scale_x_base
        scale_y = scale_x_base
        print(f"Aspect adjustment: Current is narrower - using width-based scaling")
else:
    # Same aspect ratio - use direct scaling
    scale_x = scale_x_base
    scale_y = scale_y_base
    print(f"Aspect match - using direct scaling")

# Average scaling for fonts and general sizes
scale_avg = (scale_x + scale_y) / 2

print(f"Scaling factors: x={scale_x:.3f}, y={scale_y:.3f}, avg={scale_avg:.3f}")
print(f"Example: 48pt font → {48 * scale_avg:.1f}pt, (0,300) → ({0 * scale_x:.0f},{300 * scale_y:.0f})")
print("=" * 80)
print()

# ===== COLLECT SYSTEM INFORMATION FOR DATA FILE =====
print("Collecting system information...")
system_info = {
    'screen_resolution_width': current_width,
    'screen_resolution_height': current_height,
    'screen_aspect_ratio': current_aspect,
    'reference_resolution': f"{REFERENCE_WIDTH}x{REFERENCE_HEIGHT}",
    'reference_aspect_ratio': REFERENCE_ASPECT,
    'ui_scaling_factor_x': scale_x,
    'ui_scaling_factor_y': scale_y,
    'ui_scaling_factor_avg': scale_avg,
    'aspect_ratio_match': abs(current_aspect - REFERENCE_ASPECT) < 0.01
}
print(f"✓ Screen: {current_width}x{current_height}, Aspect: {current_aspect:.3f}, Scale: {scale_avg:.3f}")

# Create white square stimulus
square = visual.Rect(
    win=win,
    width=int(200 * scale_x),
    height=int(200 * scale_avg),
    fillColor='white',
    lineColor='white'
)

# Create audio stimulus (1000 Hz tone, 1 second duration)
beep = sound.Sound(value=1000, secs=1.0, hamming=True)

# Create looping version for instructions - longer duration for smoother looping
beep_continuous = sound.Sound(value=1000, secs=2.0, hamming=True, loops=-1)

# Measure actual monitor refresh rate by running test frames
print("Measuring actual monitor refresh rate...")

# Warm up - run a few frames first to stabilize
for _ in range(10):
    win.flip()

# Now measure for 2 seconds for better accuracy
measure_start = core.getTime()
measure_frames = []

while core.getTime() - measure_start < 2.0:
    win.flip()
    measure_frames.append(core.getTime())

# Calculate actual FPS from measurements
if len(measure_frames) > 100:  # Need good sample size
    # Calculate frame intervals
    measure_intervals = [measure_frames[i] - measure_frames[i-1] 
                        for i in range(1, len(measure_frames))]
    
    # Remove outliers (first few frames can be unstable)
    measure_intervals = measure_intervals[10:]  # Skip first 10 intervals
    
    # Calculate median interval (more robust than mean)
    median_frame_period = statistics.median(measure_intervals)
    measured_fps = 1.0 / median_frame_period if median_frame_period > 0 else 60.0
    
    # Round to nearest common refresh rate
    common_rates = [30, 60, 75, 90, 100, 120, 144, 165, 180, 200, 240, 360]
    expected_fps = min(common_rates, key=lambda x: abs(x - measured_fps))
    
    refresh_rate = 1.0 / expected_fps
else:
    # Fallback if measurement fails
    refresh_rate = win.monitorFramePeriod
    expected_fps = round(1.0 / refresh_rate) if refresh_rate > 0 else 60

print(f"Measured refresh rate: {expected_fps} Hz")
print(f"Frame period: {refresh_rate*1000:.2f} ms")

# Add refresh rate to system_info
system_info['measured_refresh_rate_hz'] = expected_fps
system_info['frame_period_ms'] = refresh_rate * 1000
system_info['measured_fps'] = measured_fps if 'measured_fps' in locals() else expected_fps

# Create copyright text (small, bottom right - used throughout)
copyright_text_small = visual.TextStim(
    win=win,
    text="© 2026 Ericson P. Kimbel, II | v0.0.495 | MIT License",
    color=[0.5, 0.5, 0.5],  # Gray instead of white for subtlety
    height=int(16 * scale_avg),  # SCALED for different resolutions
    pos=(win.size[0]/2 - 50, -win.size[1]/2 + 30),  # Simpler calculation, still overscan safe
    anchorHoriz='right',
    anchorVert='bottom'
)

# Create global mouse object
global_mouse = event.Mouse(visible=False, win=win)  # Start hidden

# Mouse auto-hide system
last_mouse_pos = global_mouse.getPos()
last_mouse_move_time = core.getTime()
MOUSE_HIDE_DELAY = 1.0  # Seconds of inactivity before hiding mouse

def update_mouse_visibility(mouse_obj, auto_hide=True):
    """Update mouse visibility based on movement. Returns True if mouse moved."""
    global last_mouse_pos, last_mouse_move_time
    
    if not auto_hide:
        # Keep mouse always visible (for memory tests)
        mouse_obj.setVisible(True)
        return False
    
    # Get current mouse position
    current_pos = mouse_obj.getPos()
    current_time = core.getTime()
    
    # Check if mouse has moved
    moved = (current_pos[0] != last_mouse_pos[0] or current_pos[1] != last_mouse_pos[1])
    
    if moved:
        # Mouse moved - show it and update tracking
        mouse_obj.setVisible(True)
        last_mouse_pos = current_pos
        last_mouse_move_time = current_time
        return True
    else:
        # Mouse hasn't moved - check if we should hide it
        if current_time - last_mouse_move_time > MOUSE_HIDE_DELAY:
            mouse_obj.setVisible(False)
        return False

# ===== PROGRESS BAR SYSTEM =====
# Define test sections with labels and estimated times
test_sections = [
    {'label': 'Mem1 Study', 'time': MEMORY_SET_1_STUDY_TIME, 'completed': False, 'run': RUN_MEMORY_TEST_1},
    {'label': 'Visual RT', 'time': PRE_EXPERIMENT_DELAY + (NUM_ITERATIONS * ((INTERVAL_MIN + INTERVAL_MAX) / 2)), 'completed': False, 'run': RUN_VISUAL_TEST},
    {'label': 'Mem1 Rec1', 'time': MEMORY_SET_1_SIZE * 20, 'completed': False, 'run': RUN_MEMORY_TEST_1},
    {'label': 'Mem2 Study', 'time': MEMORY_SET_2_STUDY_TIME, 'completed': False, 'run': RUN_MEMORY_TEST_2},
    {'label': 'Audio RT', 'time': PRE_EXPERIMENT_DELAY + (NUM_ITERATIONS * ((INTERVAL_MIN + INTERVAL_MAX) / 2)), 'completed': False, 'run': RUN_AUDIO_TEST},
    {'label': 'Mem2 Rec1', 'time': MEMORY_SET_2_SIZE * 20, 'completed': False, 'run': RUN_MEMORY_TEST_2},
    {'label': 'Mem1 Rec2', 'time': MEMORY_SET_1_SIZE * 20, 'completed': False, 'run': RUN_MEMORY_TEST_1}
]

current_section = -1  # -1 means before tests start
total_estimated_time = sum(section['time'] for section in test_sections if section['run'])

# Pre-create progress bar visual elements (for performance)
bar_width = int(1200 * scale_x)  # SCALED - original width
bar_height = int(68 * scale_avg)  # SCALED
section_width = bar_width / len(test_sections)
bar_y = win.size[1]/2 - int(120 * scale_y)  # SCALED
bar_start_x = -bar_width / 2  # CENTERED (original design)

# Create time text object (reused each frame) - original position
progress_time_text = visual.TextStim(
    win=win,
    text='',
    color='white',
    height=int(40 * scale_avg),  # SCALED
    pos=(win.size[0]/2 - int(180 * scale_x), bar_y),  # SCALED - original position
    anchorHoriz='right'
)

# Create section boxes and labels (reused each frame)
progress_boxes = []
progress_labels = []

for i, section in enumerate(test_sections):
    x_pos = bar_start_x + (i * section_width) + (section_width / 2)
    
    # Create box
    box = visual.Rect(
        win=win,
        width=section_width - 4,
        height=bar_height,
        pos=(x_pos, bar_y),
        fillColor='gray',
        lineColor='white',
        lineWidth=2
    )
    progress_boxes.append(box)
    
    # Create label
    label = visual.TextStim(
        win=win,
        text=section['label'],
        color='white',
        height=int(27 * scale_avg),  # SCALED
        pos=(x_pos, bar_y),
        bold=False
    )
    progress_labels.append(label)

def draw_progress_bar(win, sections, current_idx, copyright_text):
    """Draw a progress bar at the top of the screen with section labels and time remaining."""
    # Calculate time remaining (only include sections that will actually run)
    # Only count time from COMPLETED sections (not the current one unless it's marked completed)
    time_completed = sum(sections[i]['time'] for i in range(len(sections)) 
                        if i >= 0 and sections[i]['run'] and sections[i]['completed'])
    time_total = sum(section['time'] for section in sections if section['run'])
    time_remaining = max(0, time_total - time_completed)
    
    # Format time remaining with appropriate units
    hours = int(time_remaining // 3600)
    mins = int((time_remaining % 3600) // 60)
    secs = int(time_remaining % 60)
    
    if hours > 0:
        # Show hours and minutes
        if mins > 0:
            time_str = f"{hours} hour{'s' if hours != 1 else ''} {mins} min"
        else:
            time_str = f"{hours} hour{'s' if hours != 1 else ''}"
    elif mins > 0:
        # Show minutes and seconds
        if secs > 0:
            time_str = f"{mins} min {secs} sec"
        else:
            time_str = f"{mins} min"
    else:
        # Show seconds only
        time_str = f"{secs} sec"
    
    # Update and draw time text
    progress_time_text.text = f"Time Left: ~{time_str}"
    progress_time_text.draw()
    
    # Update and draw each section
    for i, section in enumerate(sections):
        # Determine colors
        if not section['run']:
            fill_color = 'darkgray'
            line_color = 'gray'
            text_color = 'white'
            is_bold = False
        elif i < current_idx or (i == current_idx and section['completed']):
            fill_color = 'green'
            line_color = 'white'
            text_color = 'black'
            is_bold = False
        elif i == current_idx:
            fill_color = 'yellow'
            line_color = 'white'
            text_color = 'black'
            is_bold = True
        else:
            fill_color = 'gray'
            line_color = 'white'
            text_color = 'white'
            is_bold = False
        
        # Update box colors
        progress_boxes[i].fillColor = fill_color
        progress_boxes[i].lineColor = line_color
        progress_boxes[i].draw()
        
        progress_labels[i].color = text_color
        progress_labels[i].bold = is_bold
        progress_labels[i].draw()

def write_csv_exports(base_filename, visual_results, audio_results, subject_info, system_info, 
                      expected_fps, keyboard_input_latency):
    """Export key data to CSV files with copyright headers."""
    base_path = base_filename.replace('.txt', '')
    print("\nExporting CSV files...")
    
    try:
        # Visual RT CSV with copyright
        if visual_results:
            with open(f"{base_path}_visual_rt.csv", 'w', newline='') as f:
                writer = csv.writer(f)
                # Copyright header
                writer.writerow(['# VISUAL REACTION TIME DATA'])
                writer.writerow(['# © 2026 Ericson P. Kimbel, II | v0.0.495'])
                writer.writerow(['# Reaction Time Test Results'])
                writer.writerow([])  # Blank line
                # Data header
                writer.writerow(['Trial', 'RT_ms', 'RT_Low', 'RT_High', 'Error', 'Frame_Time', 'Input_Latency', 'Misclicks'])
                for r in visual_results:
                    rt = r['reaction_time']
                    ft = r.get('response_frame_time', 1000/expected_fps)
                    il = keyboard_input_latency if keyboard_input_latency else 10
                    err = ft + il
                    writer.writerow([r['trial'], round(rt,1), round(max(0,rt-err),1), round(rt+err,1), round(err,1), round(ft,1), round(il,1), r['misclicks']])
            print(f"  ✓ {base_path}_visual_rt.csv")
        
        # Audio RT CSV with copyright
        if audio_results:
            with open(f"{base_path}_audio_rt.csv", 'w', newline='') as f:
                writer = csv.writer(f)
                # Copyright header
                writer.writerow(['# AUDIO REACTION TIME DATA'])
                writer.writerow(['# © 2026 Ericson P. Kimbel, II | v0.0.495'])
                writer.writerow(['# Reaction Time Test Results'])
                writer.writerow([])  # Blank line
                # Data header
                writer.writerow(['Trial', 'RT_ms', 'RT_Low', 'RT_High', 'Error', 'Frame_Time', 'Input_Latency', 'Misclicks'])
                for r in audio_results:
                    rt = r['reaction_time']
                    ft = r.get('response_frame_time', 1000/expected_fps)
                    il = keyboard_input_latency if keyboard_input_latency else 10
                    err = ft + il
                    writer.writerow([r['trial'], round(rt,1), round(max(0,rt-err),1), round(rt+err,1), round(err,1), round(ft,1), round(il,1), r['misclicks']])
            print(f"  ✓ {base_path}_audio_rt.csv")
        
        print("✓ CSV export complete")
    except Exception as e:
        print(f"WARNING: CSV export failed: {e}")

def write_excel_export(base_filename, visual_results, audio_results, subject_info, system_info,
                       expected_fps, keyboard_input_latency, memory_set_1_test_1_results=None,
                       memory_set_1_test_2_results=None, memory_set_2_test_1_results=None,
                       checklist_info=None, stability_metrics=None, all_framerate_attempts=None,
                       all_keyboard_sessions=None, performance_log=None, NUM_ITERATIONS=0,
                       INTERVAL_MIN=0, INTERVAL_MAX=0, FRAMERATE_TEST_DURATION=0,
                       MEMORY_SET_1_SIZE=0, MEMORY_SET_1_STUDY_TIME=0,
                       MEMORY_SET_2_SIZE=0, MEMORY_SET_2_STUDY_TIME=0,
                       using_over_ear_headphones="N/A", using_single_monitor="N/A"):
    """Excel-compatible HTML export with comprehensive data tables."""
    excel_file = base_filename.replace('.txt', '.xls')
    print(f"\nGenerating Excel file: {excel_file}")
    try:
        with open(excel_file, 'w', encoding='utf-8') as f:
            f.write('<!DOCTYPE html>\n<html>\n<head><meta charset="utf-8">\n<style>\n')
            f.write('body{font-family:Arial;margin:20px}table{border-collapse:collapse;margin:20px 0;width:100%;max-width:1000px}')
            f.write('th{background:#4472C4;color:white;padding:10px;border:1px solid #000;font-weight:bold}')
            f.write('td{padding:8px;border:1px solid #ccc}h2{color:#2E5C8A;margin-top:40px;border-bottom:2px solid #4472C4;padding-bottom:5px}')
            f.write('.summary{background:#F8F8F8;padding:15px;margin:15px 0;border-left:4px solid #4472C4}')
            f.write('.correct{background:#D4EDDA}.incorrect{background:#F8D7DA}')
            f.write('</style></head><body>\n<h1 style="color:#2E5C8A">REACTION TIME TEST RESULTS</h1>\n')
            
            # Summary
            f.write('<div class="summary"><h2>SUMMARY</h2>\n<h3>Subject Information</h3><table style="width:700px">\n')
            f.write('<tr><th>Field</th><th>Value</th></tr>\n')
            f.write(f'<tr><td>Name</td><td>{subject_info.get("Name","N/A")}</td></tr>\n')
            f.write(f'<tr><td>Age</td><td>{subject_info.get("Age","N/A")}</td></tr>\n')
            f.write(f'<tr><td>Sex</td><td>{subject_info.get("Sex","N/A")}</td></tr>\n')
            f.write(f'<tr><td>Subject Number</td><td>{subject_info.get("Subject Number","N/A")}</td></tr>\n')
            f.write(f'<tr><td>Session Number</td><td>{subject_info.get("Session Number","N/A")}</td></tr>\n')
            f.write(f'<tr><td>Sleep Apnea</td><td>{subject_info.get("Sleep Apnea","N/A")}</td></tr>\n')
            f.write(f'<tr><td>Sleep Apnea Treatment</td><td>{subject_info.get("Sleep Apnea Treatment","N/A")}</td></tr>\n')
            health_key = 'Health conditions affecting cognition (ADHD, ADD, meds, etc. or "None")'
            f.write(f'<tr><td>Health Conditions</td><td>{subject_info.get(health_key,"N/A")}</td></tr>\n')
            f.write('</table>\n')
            
            # Test Configuration & Metadata
            f.write('<h3>Test Configuration & Metadata</h3><table style="width:700px">\n<tr><th>Parameter</th><th>Value</th></tr>\n')
            f.write(f'<tr><td>Test Date/Time</td><td>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</td></tr>\n')
            f.write(f'<tr><td>Program Version</td><td>v0.0.495</td></tr>\n')
            f.write(f'<tr><td>RT Trials per Test</td><td>{NUM_ITERATIONS if "NUM_ITERATIONS" in dir() else "N/A"}</td></tr>\n')
            f.write(f'<tr><td>RT Interval Range</td><td>{INTERVAL_MIN if "INTERVAL_MIN" in dir() else "N/A"}-{INTERVAL_MAX if "INTERVAL_MAX" in dir() else "N/A"}s</td></tr>\n')
            f.write(f'<tr><td>Framerate Test Duration</td><td>{FRAMERATE_TEST_DURATION if "FRAMERATE_TEST_DURATION" in dir() else "N/A"}s</td></tr>\n')
            f.write(f'<tr><td>Memory Set 1 Size</td><td>{MEMORY_SET_1_SIZE if "MEMORY_SET_1_SIZE" in dir() else "N/A"} images</td></tr>\n')
            f.write(f'<tr><td>Memory Set 1 Study Time</td><td>{MEMORY_SET_1_STUDY_TIME if "MEMORY_SET_1_STUDY_TIME" in dir() else "N/A"}s</td></tr>\n')
            f.write(f'<tr><td>Memory Set 2 Size</td><td>{MEMORY_SET_2_SIZE if "MEMORY_SET_2_SIZE" in dir() else "N/A"} images</td></tr>\n')
            f.write(f'<tr><td>Memory Set 2 Study Time</td><td>{MEMORY_SET_2_STUDY_TIME if "MEMORY_SET_2_STUDY_TIME" in dir() else "N/A"}s</td></tr>\n')
            f.write(f'<tr><td>Using Over-Ear Headphones</td><td>{"N/A" if "using_over_ear_headphones" not in dir() else using_over_ear_headphones}</td></tr>\n')
            f.write(f'<tr><td>Using Single Monitor</td><td>{"N/A" if "using_single_monitor" not in dir() else using_single_monitor}</td></tr>\n')
            f.write('</table>\n')
            
            f.write('<h3>System Information</h3><table style="width:700px">\n<tr><th>Metric</th><th>Value</th></tr>\n')
            f.write(f'<tr><td>Resolution</td><td>{system_info.get("screen_resolution_width")}x{system_info.get("screen_resolution_height")}</td></tr>\n')
            f.write(f'<tr><td>Aspect Ratio</td><td>{system_info.get("screen_aspect_ratio", 0):.3f}</td></tr>\n')
            f.write(f'<tr><td>Refresh Rate</td><td>{system_info.get("measured_refresh_rate_hz")} Hz</td></tr>\n')
            f.write(f'<tr><td>UI Scaling Factor</td><td>{system_info.get("ui_scaling_factor_avg", 1.0):.3f}</td></tr>\n')
            f.write('</table></div>\n')
            
            # Visual RT
            if visual_results:
                f.write('<h2>VISUAL RT</h2><table>\n<tr><th>Trial</th><th>RT</th><th>RT_Low</th><th>RT_High</th><th>Error</th><th>Misclicks</th></tr>\n')
                for r in visual_results:
                    rt=r['reaction_time'];ft=r.get('response_frame_time',1000/expected_fps);il=keyboard_input_latency if keyboard_input_latency else 10;err=ft+il
                    f.write(f'<tr><td>{r["trial"]}</td><td>{rt:.1f}</td><td>{max(0,rt-err):.1f}</td><td>{rt+err:.1f}</td><td>{err:.1f}</td><td>{r["misclicks"]}</td></tr>\n')
                f.write('</table>\n')
            
            # Audio RT
            if audio_results:
                f.write('<h2>AUDIO RT</h2><table>\n<tr><th>Trial</th><th>RT</th><th>RT_Low</th><th>RT_High</th><th>Error</th><th>Misclicks</th></tr>\n')
                for r in audio_results:
                    rt=r['reaction_time'];ft=r.get('response_frame_time',1000/expected_fps);il=keyboard_input_latency if keyboard_input_latency else 10;err=ft+il
                    f.write(f'<tr><td>{r["trial"]}</td><td>{rt:.1f}</td><td>{max(0,rt-err):.1f}</td><td>{rt+err:.1f}</td><td>{err:.1f}</td><td>{r["misclicks"]}</td></tr>\n')
                f.write('</table>\n')
            
            # Memory tests - ALL DETAILED RESULTS (No summaries, all data for analysis)
            if memory_set_1_test_1_results:
                f.write('<h2>MEMORY SET 1 - RECOGNITION TEST ITERATION 1 (Detailed Results)</h2>\n')
                f.write(f'<p><strong>Study Time: {MEMORY_SET_1_SIZE if "MEMORY_SET_1_SIZE" in dir() else "N/A"} images studied</strong></p>\n')
                f.write('<table>\n<tr><th>Image_ID</th><th>Was_In_Study_Set</th><th>User_Selected</th><th>Changed_Mind</th><th>Total_Clicks</th><th>Confidence</th><th>Correct_Selection</th><th>Result</th></tr>\n')
                for img_id in sorted(memory_set_1_test_1_results.keys()):
                    data = memory_set_1_test_1_results[img_id]
                    cls = 'correct' if data.get('selection_correct') else 'incorrect'
                    confidence = "High (1 click)" if data.get('clicks', 0) == 1 else f"Low ({data.get('clicks', 0)} clicks)"
                    f.write(f'<tr class="{cls}">')
                    f.write(f'<td>{img_id}</td>')
                    f.write(f'<td>{"YES" if data.get("correct") else "NO"}</td>')
                    f.write(f'<td>{"YES" if data.get("selected") else "NO"}</td>')
                    f.write(f'<td>{"YES" if data.get("changed") else "NO"}</td>')
                    f.write(f'<td>{data.get("clicks", 0)}</td>')
                    f.write(f'<td>{confidence}</td>')
                    f.write(f'<td>{"Correct" if data.get("selection_correct") else "Incorrect"}</td>')
                    f.write(f'<td><strong>{"✓ CORRECT" if data.get("selection_correct") else "✗ INCORRECT"}</strong></td>')
                    f.write('</tr>\n')
                f.write('</table>\n')
                # Add summary at bottom for quick reference
                correct_count = sum(1 for data in memory_set_1_test_1_results.values() if data.get('selection_correct'))
                total_count = len(memory_set_1_test_1_results)
                accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
                f.write(f'<p><strong>Accuracy: {accuracy:.1f}% ({correct_count}/{total_count} correct)</strong></p>\n')
            
            if memory_set_1_test_2_results:
                f.write('<h2>MEMORY SET 1 - RECOGNITION TEST ITERATION 2 (Detailed Results)</h2>\n')
                f.write(f'<p><strong>Second iteration of same {MEMORY_SET_1_SIZE if "MEMORY_SET_1_SIZE" in dir() else "N/A"} images</strong></p>\n')
                f.write('<table>\n<tr><th>Image_ID</th><th>Was_In_Study_Set</th><th>User_Selected</th><th>Changed_Mind</th><th>Total_Clicks</th><th>Confidence</th><th>Correct_Selection</th><th>Result</th></tr>\n')
                for img_id in sorted(memory_set_1_test_2_results.keys()):
                    data = memory_set_1_test_2_results[img_id]
                    cls = 'correct' if data.get('selection_correct') else 'incorrect'
                    confidence = "High (1 click)" if data.get('clicks', 0) == 1 else f"Low ({data.get('clicks', 0)} clicks)"
                    f.write(f'<tr class="{cls}">')
                    f.write(f'<td>{img_id}</td>')
                    f.write(f'<td>{"YES" if data.get("correct") else "NO"}</td>')
                    f.write(f'<td>{"YES" if data.get("selected") else "NO"}</td>')
                    f.write(f'<td>{"YES" if data.get("changed") else "NO"}</td>')
                    f.write(f'<td>{data.get("clicks", 0)}</td>')
                    f.write(f'<td>{confidence}</td>')
                    f.write(f'<td>{"Correct" if data.get("selection_correct") else "Incorrect"}</td>')
                    f.write(f'<td><strong>{"✓ CORRECT" if data.get("selection_correct") else "✗ INCORRECT"}</strong></td>')
                    f.write('</tr>\n')
                f.write('</table>\n')
                correct_count = sum(1 for data in memory_set_1_test_2_results.values() if data.get('selection_correct'))
                total_count = len(memory_set_1_test_2_results)
                accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
                f.write(f'<p><strong>Accuracy: {accuracy:.1f}% ({correct_count}/{total_count} correct)</strong></p>\n')
            
            if memory_set_2_test_1_results:
                f.write('<h2>MEMORY SET 2 - RECOGNITION TEST (Detailed Results)</h2>\n')
                f.write(f'<p><strong>Study Time: {MEMORY_SET_2_SIZE if "MEMORY_SET_2_SIZE" in dir() else "N/A"} images studied</strong></p>\n')
                f.write('<table>\n<tr><th>Image_ID</th><th>Was_In_Study_Set</th><th>User_Selected</th><th>Changed_Mind</th><th>Total_Clicks</th><th>Confidence</th><th>Correct_Selection</th><th>Result</th></tr>\n')
                for img_id in sorted(memory_set_2_test_1_results.keys()):
                    data = memory_set_2_test_1_results[img_id]
                    cls = 'correct' if data.get('selection_correct') else 'incorrect'
                    confidence = "High (1 click)" if data.get('clicks', 0) == 1 else f"Low ({data.get('clicks', 0)} clicks)"
                    f.write(f'<tr class="{cls}">')
                    f.write(f'<td>{img_id}</td>')
                    f.write(f'<td>{"YES" if data.get("correct") else "NO"}</td>')
                    f.write(f'<td>{"YES" if data.get("selected") else "NO"}</td>')
                    f.write(f'<td>{"YES" if data.get("changed") else "NO"}</td>')
                    f.write(f'<td>{data.get("clicks", 0)}</td>')
                    f.write(f'<td>{confidence}</td>')
                    f.write(f'<td>{"Correct" if data.get("selection_correct") else "Incorrect"}</td>')
                    f.write(f'<td><strong>{"✓ CORRECT" if data.get("selection_correct") else "✗ INCORRECT"}</strong></td>')
                    f.write('</tr>\n')
                f.write('</table>\n')
                correct_count = sum(1 for data in memory_set_2_test_1_results.values() if data.get('selection_correct'))
                total_count = len(memory_set_2_test_1_results)
                accuracy = (correct_count / total_count * 100) if total_count > 0 else 0
                f.write(f'<p><strong>Accuracy: {accuracy:.1f}% ({correct_count}/{total_count} correct)</strong></p>\n')
            
            # Performance checklist
            if checklist_info:
                f.write('<h2>PERFORMANCE CHECKLIST</h2><table>\n<tr><th>Item</th><th>Completed</th></tr>\n')
                for item,checked in checklist_info.items():
                    cls='correct' if checked else 'incorrect'
                    f.write(f'<tr class="{cls}"><td>{item}</td><td><strong>{"YES" if checked else "NO"}</strong></td></tr>\n')
                f.write('</table>\n')
            
            # Framerate test results - COMPREHENSIVE DATA LIKE KEYBOARD TEST
            if stability_metrics:
                f.write('<h2>FRAMERATE STABILITY TEST RESULTS</h2><table>\n<tr><th>Metric</th><th>Value</th></tr>\n')
                # Core FPS metrics
                f.write(f'<tr><td>Average FPS</td><td>{stability_metrics.get("avg_fps", 0):.2f}</td></tr>\n')
                f.write(f'<tr><td>99% FPS</td><td>{stability_metrics.get("fps_99", 0):.2f}</td></tr>\n')
                f.write(f'<tr><td>1% FPS (1% lows)</td><td>{stability_metrics.get("fps_1", 0):.2f}</td></tr>\n')
                f.write(f'<tr><td>0.1% FPS (0.1% lows)</td><td>{stability_metrics.get("fps_01", 0):.2f}</td></tr>\n')
                f.write(f'<tr><td>100% FPS (Max FPS)</td><td>{stability_metrics.get("fps_100", 0):.2f}</td></tr>\n')
                # Frame time statistics
                f.write(f'<tr><td>Average Frame Time</td><td>{stability_metrics.get("avg_frame_time", 0):.3f} ms</td></tr>\n')
                f.write(f'<tr><td>Max Frame Time</td><td>{stability_metrics.get("max_frame_time", 0):.3f} ms</td></tr>\n')
                f.write(f'<tr><td>Min Frame Time</td><td>{stability_metrics.get("min_frame_time", 0):.3f} ms</td></tr>\n')
                f.write(f'<tr><td>Frame Time Std Dev</td><td>{stability_metrics.get("frame_time_std", 0):.3f} ms</td></tr>\n')
                # Stability and consistency
                f.write(f'<tr><td>Frame Pacing CV</td><td>{stability_metrics.get("frame_pacing_cv", 0):.2f}%</td></tr>\n')
                f.write(f'<tr><td>Estimated Input Latency</td><td>{stability_metrics.get("estimated_input_latency", 0):.2f} ms</td></tr>\n')
                # Test details (if available from all_framerate_attempts)
                if all_framerate_attempts and len(all_framerate_attempts) > 0:
                    final_attempt = all_framerate_attempts[-1]
                    f.write(f'<tr><td>Total Frames Collected</td><td>{final_attempt.get("frames", "N/A")}</td></tr>\n')
                    f.write(f'<tr><td>Dropped Frames</td><td>{final_attempt.get("dropped", "N/A")}</td></tr>\n')
                    f.write(f'<tr><td>Stability Percentage</td><td>{final_attempt.get("stability", 0):.2f}%</td></tr>\n')
                    f.write(f'<tr><td>Number of Attempts</td><td>{len(all_framerate_attempts)} (includes redos)</td></tr>\n')
                f.write('</table>\n')
            
            # Keyboard hardware test - COMPREHENSIVE DATA
            if all_keyboard_sessions and len(all_keyboard_sessions) > 0:
                # Use the final session (most recent/accepted results)
                final_session = all_keyboard_sessions[-1]
                f.write('<h2>KEYBOARD HARDWARE TEST RESULTS</h2><table>\n<tr><th>Metric</th><th>Value</th></tr>\n')
                f.write(f'<tr><td>Average Input Latency</td><td>{keyboard_input_latency:.2f} ms</td></tr>\n')
                f.write(f'<tr><td>Total Taps</td><td>{final_session.get("total_taps", "N/A")}</td></tr>\n')
                f.write(f'<tr><td>Average Tap Rate</td><td>{final_session.get("avg_tap_rate", 0):.2f} taps/sec</td></tr>\n')
                f.write(f'<tr><td>Max Tap Rate</td><td>{final_session.get("max_tap_rate", 0):.2f} taps/sec</td></tr>\n')
                f.write(f'<tr><td>Average Tap Interval</td><td>{final_session.get("avg_tap_interval", 0):.2f} ms</td></tr>\n')
                f.write(f'<tr><td>Min Tap Interval</td><td>{final_session.get("min_tap_interval", 0):.2f} ms</td></tr>\n')
                f.write(f'<tr><td>Tap Interval CV</td><td>{final_session.get("tap_cv", 0):.2f}%</td></tr>\n')
                f.write(f'<tr><td>Estimated USB Polling</td><td>{final_session.get("estimated_polling", "N/A")}</td></tr>\n')
                f.write(f'<tr><td>Hardware Rating</td><td><strong>{final_session.get("keyboard_rating", "N/A")}</strong></td></tr>\n')
                f.write('</table>\n')
            elif keyboard_input_latency:
                # Fallback if session data not available
                f.write('<h2>KEYBOARD HARDWARE TEST</h2><table>\n<tr><th>Metric</th><th>Value</th></tr>\n')
                f.write(f'<tr><td>Average Input Latency</td><td>{keyboard_input_latency:.2f} ms</td></tr>\n')
                f.write('</table>\n')
            
            # Frame time data - ALL FRAMES for debugging
            if performance_log and 'frame_log' in performance_log:
                expected_frame_ms = 1000.0 / expected_fps
                delay_threshold = expected_frame_ms * 10
                # Include ALL frames for complete debugging (not just first 100)
                all_frames = performance_log['frame_log']
                
                if all_frames:
                    f.write('<h2>COMPLETE FRAME TIME DATA (All Frames - For Debugging)</h2>\n')
                    f.write(f'<p><strong>Total frames: {len(all_frames)}</strong></p>\n')
                    f.write('<p><em>Copy this table to Excel to analyze frame times, find issues, and identify performance problems.</em></p>\n')
                    f.write(f'<p><em>Delay threshold: {delay_threshold:.1f}ms - Frames below this are actual frames, above are intentional delays between trials.</em></p>\n')
                    f.write('<table>\n<tr><th>Frame#</th><th>Frame_Time_ms</th><th>Is_Delay</th><th>Section</th><th>Detailed_Info</th></tr>\n')
                    
                    for idx, entry in enumerate(all_frames, 1):
                        ft = entry['frame_time']
                        is_delay = "YES" if ft >= delay_threshold else "NO"
                        section = entry['section']
                        
                        # Add detailed info for RT test frames
                        if 'Visual Test - Trial' in section or 'Audio Test - Trial' in section:
                            if '(Stimulus)' in section:
                                detail = "STIMULUS PRESENTED"
                            elif '(Response)' in section:
                                detail = "WAITING FOR RESPONSE"
                            elif '(Pre-Delay)' in section:
                                detail = "Black screen delay before trial"
                            else:
                                detail = ""
                        elif 'Memory' in section:
                            detail = "Memory test (frame time not critical)"
                        elif 'Keyboard' in section:
                            detail = "Keyboard test (frame time not critical)"
                        elif 'Framerate' in section:
                            detail = "Framerate stability test"
                        else:
                            detail = ""
                        
                        # Color code delays
                        row_class = 'style="background-color:#FFF3CD"' if is_delay == "YES" else ''
                        f.write(f'<tr {row_class}><td>{idx}</td><td>{ft:.3f}</td><td>{is_delay}</td><td>{section}</td><td>{detail}</td></tr>\n')
                    
                    f.write('</table>\n')
                    f.write('<p><em>Note: Rows highlighted in yellow are intentional delays between trials (not performance issues).</em></p>\n')
            
            f.write('<p style="margin-top:50px;color:#999">© 2026 Ericson P. Kimbel, II | v0.0.495</p></body></html>')
        print(f"✓ Excel file created: {excel_file} (HTML format - no libraries needed!)")
    except Exception as e:
        print(f"WARNING: Excel export failed: {e}")

# Show copyright notice (small, bottom right)
copyright_notice = visual.TextStim(
    win=win,
    text="© 2026 Ericson P. Kimbel, II | v0.0.495",
    color=[0.5, 0.5, 0.5],
    height=int(16 * scale_avg),
    pos=(win.size[0]/2 - 10, -win.size[1]/2 + 10),
    anchorHoriz='right',
    anchorVert='bottom'
)
copyright_notice.draw()
draw_progress_bar(win, test_sections, current_section, copyright_text_small)
copyright_text_small.draw()
win.flip()
core.wait(2.0)  # Display for 2 seconds

# ===== STEP 3: FRAMERATE STABILITY TEST =====
framerate_test_complete = False
framerate_attempt_number = 0
all_framerate_attempts = []  # Store all attempts for file output

while not framerate_test_complete:
    if RUN_FRAMERATE_TEST:
        framerate_attempt_number += 1
        print("\n" + "=" * 80)
        print(f"STEP 3: FRAMERATE STABILITY TEST - ATTEMPT #{framerate_attempt_number}")
        print("=" * 80)
        
        if framerate_attempt_number > 1:
            # Show redoing message
            redo_msg = visual.TextStim(
                win=win,
                text=f"REDOING FRAMERATE TEST\n\nAttempt #{framerate_attempt_number}",
                color='yellow',
                height=int(48 * scale_avg),  # SCALED
                pos=(int(0 * scale_x), int(0 * scale_y))
            )
            redo_msg.draw()
            copyright_text_small.draw()
            draw_progress_bar(win, test_sections, current_section, copyright_text_small)
            win.flip()
            core.wait(1.5)
        
        print(f"Starting {int(FRAMERATE_TEST_DURATION)}-second framerate stability test...")

        test_text = visual.TextStim(
            win=win,
            text='',
            color='white',
            height=int(25 * scale_avg),  # SCALED
            pos=(int(0 * scale_x), int(0 * scale_y)),
            wrapWidth=int(7000 * scale_x) if scale_x > 0 else 7000  # SCALED
        )

        # Run test for configured duration
        test_duration = FRAMERATE_TEST_DURATION

        # ADAPTIVE WARMUP - Calculate based on measured FPS
        # Higher FPS systems need more warmup (more cores, more components to initialize)
        # Formula: base_time + (current_fps / baseline_fps) * factor
        # At 165 FPS (baseline): 5 + (165/165) * 2 = 7 seconds
        # At 60 FPS: 5 + (60/165) * 2 = 5.7 seconds
        # At 240 FPS: 5 + (240/165) * 2 = 7.9 seconds
        # At 1000 FPS: 5 + (1000/165) * 2 = 17.1 seconds
        warmup_duration = FRAMERATE_WARMUP_BASE + (expected_fps / FRAMERATE_WARMUP_FPS_BASELINE) * FRAMERATE_WARMUP_FPS_FACTOR
        
        print(f"Adaptive warmup duration: {warmup_duration:.1f} seconds (based on {expected_fps} FPS)")
        print(f"  Base: {FRAMERATE_WARMUP_BASE}s + FPS factor: {warmup_duration - FRAMERATE_WARMUP_BASE:.1f}s")

        # WARMUP PHASE - Let system stabilize before recording
        print(f"Warming up ({warmup_duration:.1f} seconds)...")
        warmup_start = core.getTime()
        warmup_text = visual.TextStim(
        win=win,
        text=f"Warming up display system...\n\n{warmup_duration:.0f} seconds\n\nPlease wait...",
        color='white',
        height=int(25 * scale_avg)  # SCALED
        )

        while core.getTime() - warmup_start < warmup_duration:
            warmup_text.draw()
            copyright_text_small.draw()
            win.flip()

        # Clear screen and pause briefly
        copyright_text_small.draw()
        win.flip()
        core.wait(0.5)

        print(f"Starting {test_duration} second framerate stability test...")

        # Create STATIC text (no updates during measurement for best performance)
        test_text.text = (
            f"=== FRAMERATE STABILITY TEST ===\n\n"
            f"Measuring for {int(test_duration)} seconds...\n\n"
            f"Expected FPS: {expected_fps}\n\n"
            f"Please wait..."
        )

        # NOW start the actual test
        test_start = core.getTime()
        frame_times = []

        # ULTRA-MINIMAL MEASUREMENT LOOP (no text updates, no escape, no dropped frame checking)
        # Dropped frames calculated AFTER test for maximum performance
        while core.getTime() - test_start < test_duration:
            # Draw STATIC text (no updates - text set before loop)
            test_text.draw()
            copyright_text_small.draw()
            
            # Flip and record time AFTER flip
            win.flip()
            frame_times.append(core.getTime())
        
        # Test complete - NOW calculate dropped frames from recorded timestamps
        dropped_frames = 0
        for i in range(1, len(frame_times)):
            frame_duration = frame_times[i] - frame_times[i-1]
            if frame_duration > (refresh_rate * 1.5):
                dropped_frames += 1
        
        print(f"Dropped frames calculated: {dropped_frames} of {len(frame_times)}")
        
        # Test complete - now safe to check for escape if needed

        # Clear screen after test completes
        copyright_text_small.draw()
        win.flip()
        core.wait(0.3)

        # Store stability test results immediately
        stability_test_frames = len(frame_times)
        stability_test_dropped = dropped_frames

        # VALIDATE FRAME COLLECTION (FPS and Duration Based)
        # Expected frames = FPS × test_duration
        # Minimum acceptable = 50% of expected (flags major issues)
        expected_frames = int(expected_fps * test_duration)
        minimum_acceptable_frames = int(expected_frames * 0.5)
        
        print(f"\nFrame Collection Validation:")
        print(f"  Expected frames: {expected_frames} ({expected_fps} FPS × {test_duration}s)")
        print(f"  Collected frames: {stability_test_frames}")
        print(f"  Minimum acceptable: {minimum_acceptable_frames} (50% of expected)")
        
        if stability_test_frames < minimum_acceptable_frames:
            print(f"  ⚠️ WARNING: Only collected {stability_test_frames}/{expected_frames} frames ({stability_test_frames/expected_frames*100:.1f}%)")
            print(f"  ⚠️ This is below 50% threshold - possible hardware issue or test interruption!")
            print(f"  ⚠️ Results may not be reliable - consider redoing test")
        elif stability_test_frames < expected_frames * 0.9:
            print(f"  ⚠️ NOTICE: Collected {stability_test_frames/expected_frames*100:.1f}% of expected frames")
            print(f"  ⚠️ Slightly low - check for background processes or hardware issues")
        else:
            print(f"  ✓ Frame collection OK: {stability_test_frames/expected_frames*100:.1f}% of expected")

        # DISCARD INITIAL FRAMES (settling period) - Based on FPS AND test duration
        # Settling time = percentage of test duration
        # Frames to discard = FPS × settling_time
        # This scales with BOTH FPS and test duration
        settling_time_seconds = test_duration * (FRAMERATE_DISCARD_TIME_PERCENTAGE / 100)
        discard_count = int(expected_fps * settling_time_seconds)
        discard_count = max(5, discard_count)  # Minimum 5 frames
        
        print(f"Discarding settling period: {settling_time_seconds:.3f}s = {discard_count} frames")
        print(f"  Calculation: {expected_fps} FPS × {settling_time_seconds:.3f}s settling time")
        print(f"  ({FRAMERATE_DISCARD_TIME_PERCENTAGE}% of {test_duration}s test duration)")
        
        # Use frames after settling period for metrics
        settled_frame_times = frame_times[discard_count:]
        
        print(f"Calculating metrics from {len(settled_frame_times)} settled frames (discarded {discard_count} initial frames)")

        # Calculate final statistics from settled frames
        avg_fps = len(settled_frame_times) / (settled_frame_times[-1] - settled_frame_times[0]) if len(settled_frame_times) > 1 else 0
        frame_intervals = [settled_frame_times[i] - settled_frame_times[i-1] for i in range(1, len(settled_frame_times))]
        avg_interval = sum(frame_intervals) / len(frame_intervals) * 1000 if frame_intervals else 0  # in ms
        
        # Recalculate dropped frames for settled period only
        settled_dropped = 0
        for i in range(1, len(settled_frame_times)):
            frame_duration = settled_frame_times[i] - settled_frame_times[i-1]
            if frame_duration > (refresh_rate * 1.5):
                settled_dropped += 1
        
        stability = (1 - (settled_dropped / len(settled_frame_times))) * 100 if len(settled_frame_times) > 0 else 0

        # Calculate comprehensive metrics from settled frames
        stability_metrics = calculate_framerate_metrics(settled_frame_times, expected_fps)

        print(f"\nFramerate test complete:")
        print(f"Average FPS: {avg_fps:.2f}")
        print(f"Average frame interval: {avg_interval:.2f} ms")
        print(f"Dropped frames: {dropped_frames}")
        print(f"Stability: {stability:.2f}%")
        
        # Store this attempt's data
        framerate_attempt_data = {
            'attempt_number': framerate_attempt_number,
            'frames': stability_test_frames,
            'dropped': stability_test_dropped,
            'stability': stability,
            'avg_fps': avg_fps,
            'metrics': stability_metrics
        }
        all_framerate_attempts.append(framerate_attempt_data)
        print(f"Framerate attempt #{framerate_attempt_number} data saved")

        # ===== STEP 4: FRAMERATE TEST RESULTS =====
        print("\n" + "=" * 80)
        print("STEP 4: FRAMERATE TEST RESULTS")
        print("=" * 80)

        # Determine performance status and recommendations
        performance_rating = "EXCELLENT"
        performance_color = "green"
        recommendations = []

        # Primary metric: Stability percentage
        # Realistic thresholds for optimized code
        if stability < 96.5:
            performance_rating = "POOR"
            performance_color = "red"
            recommendations.append("- High frame drop rate detected")
            recommendations.append("- Consider closing background applications")
            recommendations.append("- Remote testing NOT recommended")
        elif stability < 98.0:
            performance_rating = "FAIR"
            performance_color = "yellow"
            recommendations.append("- Moderate frame drops detected")
            recommendations.append("- Results may be affected by timing inconsistencies")
        elif stability < 99.0:
            performance_rating = "GOOD"
            performance_color = "lightgreen"
        else:
            # stability >= 99.0% = EXCELLENT by default
            # This is realistic for well-optimized systems
            pass

        # Secondary metric: Frame pacing CV
        # Excellent CV (< 15%) can promote GOOD to EXCELLENT
        # Poor CV (> 20%) can demote EXCELLENT to GOOD
        if stability_metrics['frame_pacing_cv'] < 15 and stability >= 98.5:
            # Bonus: Excellent frame pacing promotes GOOD to EXCELLENT
            if performance_rating == "GOOD":
                performance_rating = "EXCELLENT"
                performance_color = "green"
        elif stability_metrics['frame_pacing_cv'] > 25:
            # Penalty: Poor frame pacing demotes EXCELLENT to GOOD
            if performance_rating == "EXCELLENT":
                performance_rating = "GOOD"
                performance_color = "lightgreen"
            recommendations.append("- Moderate frame pacing variation detected")
        elif stability_metrics['frame_pacing_cv'] > 20 and stability < 99.5:
            # Moderate penalty for combined moderate CV and moderate stability
            if performance_rating == "EXCELLENT":
                performance_rating = "GOOD"
                performance_color = "lightgreen"

        # 1% lows check - only flag if critically low (< 50% of expected)
        if stability_metrics['fps_1'] < expected_fps * 0.50:
            if performance_rating in ["EXCELLENT", "GOOD"]:
                performance_rating = "FAIR"
                performance_color = "yellow"
            recommendations.append("- 1% lows critically low")
            recommendations.append("- System may have serious background interference")

        # Determine if framerate is acceptable or requires forced redo
        framerate_needs_redo = (performance_rating == "POOR")
        
        # Build recommendation text
        rec_text = "\n".join(recommendations) if recommendations else "System performance is stable for testing."
        
        # Add persistent redo help if needed
        if framerate_needs_redo:
            rec_text += (
                "\n\nIF YOU REPEATEDLY GET THIS SCREEN:\n"
                "1. Press ESC to exit the program\n"
                "2. Restart and complete the Performance Checklist\n"
                "3. Close all background applications\n"
                "4. Try the test again\n"
                "5. If still failing, contact your researcher for assistance"
            )

        # PREVENT AUTO-COMPLETION: Clear events and add delay before showing results
        event.clearEvents()
        core.wait(1.0)
        event.clearEvents()

        # Show comprehensive results
        result_text = visual.TextStim(
        win=win,
        text=(
            f"=== FRAMERATE STABILITY TEST ===\n\n"
            f"PERFORMANCE RATING: {performance_rating}\n\n"
            f"KEY METRICS:\n"
            f"Average FPS: {avg_fps:.2f} (Expected: {expected_fps:.2f})\n"
            f"99% FPS: {stability_metrics['fps_99']:.2f}\n"
            f"1% FPS (1% lows): {stability_metrics['fps_1']:.2f}\n"
            f"0.1% FPS (0.1% lows): {stability_metrics['fps_01']:.2f}\n\n"
            f"STABILITY ANALYSIS:\n"
            f"Dropped frames: {dropped_frames} of {stability_test_frames}\n"
            f"Overall stability: {stability:.2f}%\n"
            f"Frame pacing CV: {stability_metrics['frame_pacing_cv']:.2f}%\n"
            f"Avg frame time: {stability_metrics['avg_frame_time']:.2f} ms\n"
            f"Est. input latency: {stability_metrics['estimated_input_latency']:.2f} ms\n\n"
            f"{rec_text}"
        ),
        color=performance_color,
        height=int(32 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
        )
        
        # Create colored control instructions
        continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to continue',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-450 * scale_x), int(-650 * scale_y)),
        bold=True
        )
        
        redo_instr = visual.TextStim(
        win=win,
        text='Press G to redo test',
        color='yellow',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-650 * scale_y)),
        bold=True
        )
        
        quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to cancel',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(450 * scale_x), int(-650 * scale_y)),
        bold=True
        )
        
        # Update continue instruction based on whether redo is forced (framerate_needs_redo already defined above)
        if framerate_needs_redo:
            # POOR performance - only show G (redo) and ESC (exit) in RED
            redo_instr.text = 'MUST REDO - Press G'
            redo_instr.color = 'red'
            redo_instr.pos = (int(-250 * scale_x), int(-650 * scale_y))  # Move left
            
            quit_instr.text = 'Press ESC to exit'
            quit_instr.color = 'red'
            quit_instr.pos = (int(250 * scale_x), int(-650 * scale_y))  # Move right
            
            print("WARNING: Framerate performance too poor - FORCED REDO required")
            print(f"Performance: {performance_rating}, Stability: {stability:.2f}%")
        else:
            # Acceptable performance - show all three options in normal colors
            continue_instr.text = 'Press SPACE to continue'
            continue_instr.color = 'green'
            
            redo_instr.text = 'Press G to redo test'
            redo_instr.color = 'yellow'
            
            quit_instr.text = 'Press ESC to cancel'
            quit_instr.color = 'red'
        
        # Draw screen elements
        result_text.draw()
        if not framerate_needs_redo:
            continue_instr.draw()  # Only draw if continuing is allowed
        redo_instr.draw()
        quit_instr.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        # Wait for user decision
        print("WAITING FOR DECISION:")
        print(f"Performance Rating: {performance_rating}")
        print(f"Stability: {stability:.2f}%")
        if framerate_needs_redo:
            print("FORCED REDO: Performance too poor - must press G to redo (SPACE disabled)")
        else:
            print("Press SPACE to continue, G to redo test, or ESC to cancel")

        # Clear any lingering key presses
        event.clearEvents()
        core.wait(0.3)

        global_mouse.setVisible(True)  # Show mouse for clicking instructions
        waiting = True
        last_click_time = 0
        while waiting:
            keys = event.getKeys(['space', 'escape', 'g'])
            current_time = core.getTime()
            
            if 'space' in keys:
                if framerate_needs_redo:
                    # FORCED REDO - don't allow continue
                    print("\n✗ SPACE disabled - Performance too poor, must redo test (press G)")
                    core.wait(0.5)
                    continue  # Stay in waiting loop
                else:
                    # Performance acceptable - allow continue
                    print("\nContinuing to next section...")
                    waiting = False
                    redo_framerate = False
            elif 'g' in keys:
                print("\nExperimenter chose to redo framerate test")
                waiting = False
                redo_framerate = True
            elif 'escape' in keys:
                print("\nExperiment cancelled by experimenter")
                win.close()
                core.quit()
            
            # Check for mouse clicks on instruction text
            if current_time - last_click_time > 0.3:
                if is_text_clicked(continue_instr, global_mouse):
                    if framerate_needs_redo:
                        # FORCED REDO - don't allow continue
                        print("\n✗ CONTINUE disabled - Performance too poor, must redo test (click REDO)")
                        last_click_time = current_time
                        core.wait(0.5)
                    else:
                        # Performance acceptable - allow continue
                        print("\nClicked CONTINUE")
                        waiting = False
                        redo_framerate = False
                        last_click_time = current_time
                        core.wait(0.2)
                elif is_text_clicked(redo_instr, global_mouse):
                    print("\nExperimenter clicked REDO")
                    waiting = False
                    redo_framerate = True
                    last_click_time = current_time
                    core.wait(0.2)
                elif is_text_clicked(quit_instr, global_mouse):
                    print("\nExperimenter clicked CANCEL")
                    win.close()
                    core.quit()
            
            core.wait(0.01)
        
        # If redo requested, continue loop; otherwise break
        if not redo_framerate:
            framerate_test_complete = True

    else:
        # Framerate test skipped - set default values
        framerate_test_complete = True  # Exit loop immediately if test is skipped
        all_framerate_attempts = []  # No attempts
        framerate_attempt_number = 0
        
        print("\n" + "=" * 80)
        print("STEP 3-4: FRAMERATE STABILITY TEST SKIPPED")
        print("RUN_FRAMERATE_TEST is set to False")
        print("=" * 80)
        
        # Set default values
        frame_times = []  # Initialize empty frame times list
        stability_test_frames = 0
        stability_test_dropped = 0
        avg_fps = expected_fps
        stability = 100.0
        stability_metrics = {
            'avg_frame_time': 1000.0 / expected_fps,
            'min_frame_time': 1000.0 / expected_fps,
            'max_frame_time': 1000.0 / expected_fps,
            'frame_time_std': 0,
            'frame_pacing_cv': 0,
            'avg_fps': expected_fps,
            'fps_100': expected_fps,
            'fps_99': expected_fps,
            'fps_1': expected_fps,
            'fps_01': expected_fps,
            'estimated_input_latency': (1000.0 / expected_fps) * 1.5
        }
        performance_rating = "SKIPPED"
        performance_color = "gray"
        rec_text = "Framerate test was skipped."
        
        # Show skip screen
        skip_screen = visual.TextStim(
            win=win,
            text=(
                "=== FRAMERATE STABILITY TEST ===\n\n"
                "This test has been skipped.\n\n"
                "RUN_FRAMERATE_TEST is set to False."
            ),
            color='yellow',
            height=int(48 * scale_avg),
            wrapWidth=int(5070 * scale_x),
            pos=(int(0 * scale_x), int(50 * scale_y))
        )
        
        continue_instr = visual.TextStim(
            win=win,
            text='Press SPACE to continue',
            color='green',
            height=int(32 * scale_avg),
            pos=(int(-350 * scale_x), int(-650 * scale_y)),
            bold=True
        )
        
        quit_instr = visual.TextStim(
            win=win,
            text='Press ESC to exit',
            color='red',
            height=int(32 * scale_avg),
            pos=(int(350 * scale_x), int(-650 * scale_y)),
            bold=True
        )
        
        skip_screen.draw()
        continue_instr.draw()
        quit_instr.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        print("Framerate test skipped - waiting for user input...")
        global_mouse.setVisible(True)  # Show mouse for clicking instructions
        waiting = True
        last_click_time = 0
        while waiting:
            keys = event.getKeys(['space', 'escape'])
            current_time = core.getTime()
            
            if 'space' in keys:
                waiting = False
            elif 'escape' in keys:
                win.close()
                core.quit()
            # Check for mouse clicks on instruction text
            if current_time - last_click_time > 0.3:
                if is_text_clicked(continue_instr, global_mouse):
                    print("User clicked CONTINUE")
                    waiting = False
                    last_click_time = current_time
                    core.wait(0.2)
                elif is_text_clicked(quit_instr, global_mouse):
                    print("User clicked QUIT")
                    win.close()
                    core.quit()
            
            core.wait(0.01)

# ===== STEP 5: KEYBOARD HARDWARE TEST =====
keyboard_test_complete = False
keyboard_session_number = 0  # Tracks manual redo sessions
all_keyboard_sessions = []  # Store all manual redo sessions

while not keyboard_test_complete:
    if RUN_KEYBOARD_TEST:
        keyboard_session_number += 1
        print("\n" + "=" * 80)
        print(f"STEP 5: KEYBOARD HARDWARE TEST - SESSION #{keyboard_session_number}")
        print("=" * 80)
        
        if keyboard_session_number > 1:
            # Show redoing message
            redo_msg = visual.TextStim(
                win=win,
                text=f"REDOING KEYBOARD TEST\n\nSession #{keyboard_session_number}",
                color='yellow',
                height=int(48 * scale_avg),
                pos=(int(0 * scale_x), int(0 * scale_y))
            )
            redo_msg.draw()
            copyright_text_small.draw()
            draw_progress_bar(win, test_sections, current_section, copyright_text_small)
            win.flip()
            core.wait(1.5)

        # Clear screen and wait - PREVENT KEY CARRYOVER
        copyright_text_small.draw()
        win.flip()
        event.clearEvents()  # Clear any lingering key presses
        core.wait(1.0)  # Longer delay to prevent accidental advancement
        event.clearEvents()  # Clear again after wait

        # Instructions for keyboard hardware test
        keyboard_instruction = visual.TextStim(
            win=win,
            text=(
                "=== KEYBOARD HARDWARE TEST ===\n\n"
                "This test measures your keyboard's hardware quality.\n\n"
                "You will TAP the SPACE BAR as FAST as you can.\n\n"
                "This is NOT a reaction test - it measures:\n"
                "- Keyboard polling rate (how often it checks for input)\n"
                "- Input consistency (USB/wireless reliability)\n\n"
                f"Test duration: {format_time_estimate(KEYBOARD_TAPPING_DURATION)}\n"
                f"Minimum taps required: {KEYBOARD_MIN_TAPS} taps\n"
                f"(That's {KEYBOARD_MIN_TAPS / KEYBOARD_TAPPING_DURATION:.1f} taps per second)\n\n"
                "IMPORTANT Instructions:\n"
                "1. Use ONLY ONE FINGER from ONE HAND\n"
                "2. Press SPACE to begin\n"
                "3. Tap SPACE as rapidly as possible\n"
                "4. Continue tapping until test completes\n\n"
                "Using multiple fingers or alternating hands will\n"
                "cause variation and skew the hardware measurement.\n\n"
                "This will NOT affect your actual reaction test results."
            ),
            color='white',
            height=int(32 * scale_avg),  # Reduced from 48 to 32 to use less vertical space
            wrapWidth=int(6500 * scale_x),  # Wider to use less vertical space
            pos=(int(0 * scale_x), int(-80 * scale_y))  # Moved down to avoid progress bar
        )
    
        # Create colored control instructions
        continue_instr = visual.TextStim(
            win=win,
            text='Press SPACE to begin',
            color='green',
            height=int(32 * scale_avg),
            pos=(int(-350 * scale_x), int(-700 * scale_y)),
            bold=True
        )
    
        quit_instr = visual.TextStim(
            win=win,
            text='Press ESC to quit',
            color='red',
            height=int(32 * scale_avg),
            pos=(int(350 * scale_x), int(-700 * scale_y)),
            bold=True
        )
    
        keyboard_instruction.draw()
        continue_instr.draw()
        quit_instr.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()

        print("Waiting for SPACE to start keyboard hardware test...")
        global_mouse.setVisible(True)  # Show mouse for clicking instructions
        waiting = True
        while waiting:
            keys = event.getKeys(['space', 'escape'])
            current_time = core.getTime()
            
            if 'space' in keys:
                waiting = False
            elif 'escape' in keys:
                win.close()
                core.quit()
            # Check for mouse clicks on instruction text
            if current_time - last_click_time > 0.3:
                if is_text_clicked(continue_instr, global_mouse):
                    print("User clicked CONTINUE")
                    waiting = False
                    last_click_time = current_time
                    core.wait(0.2)
                elif is_text_clicked(quit_instr, global_mouse):
                    print("User clicked QUIT")
                    win.close()
                    core.quit()
            
            core.wait(0.01)

        # Clear events and short pause
        event.clearEvents()
        core.wait(0.5)

        # RETRY LOOP - repeat test if user starts too late or has large gaps
        test_successful = False
        gap_threshold = KEYBOARD_TAPPING_DURATION * 0.20  # 20% of total duration
        attempt_number = 0
        all_attempts = []  # Store all attempts for debugging
    
        while not test_successful:
            attempt_number += 1
            print(f"\n--- KEYBOARD TEST ATTEMPT #{attempt_number} ---")
            # COUNTDOWN before test starts - gives user time to prepare
            print("Showing countdown before keyboard test starts...")
        
            countdown_instruction = visual.TextStim(
                win=win,
                text='GET READY TO TAP SPACE AS FAST AS YOU CAN!',
                color='yellow',
                height=int(48 * scale_avg),
                pos=(int(0 * scale_x), int(150 * scale_y)),
                bold=True
            )
        
            countdown_text = visual.TextStim(
                win=win,
                text='',
                color='yellow',
                height=int(100 * scale_avg),
                pos=(int(0 * scale_x), int(-50 * scale_y)),
                bold=True
            )
        
            for count in [3, 2, 1]:
                countdown_instruction.draw()
                countdown_text.text = f"{count}"
                countdown_text.draw()
                copyright_text_small.draw()
                draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                win.flip()
                core.wait(1.0)
        
            # Show GO screen with space bar prompt
            go_text = visual.TextStim(
                win=win,
                text='START TAPPING NOW!',
                color='green',
                height=int(120 * scale_avg),
                pos=(int(0 * scale_x), int(50 * scale_y)),
                bold=True
            )
        
            go_disclaimer = visual.TextStim(
                win=win,
                text='(press space to start)',
                color='yellow',
                height=int(40 * scale_avg),
                pos=(int(0 * scale_x), int(-200 * scale_y)),  # Moved down from -100 to avoid overlap with START TAPPING text
                bold=True
            )
        
            # Display and wait for first space press
            go_text.draw()
            go_disclaimer.draw()
            copyright_text_small.draw()
            draw_progress_bar(win, test_sections, current_section, copyright_text_small)
            win.flip()
        
            # Wait for user to press space to start - this becomes the first tap
            print("Waiting for user to press SPACE to begin tapping test...")
            event.clearEvents()
            waiting_for_start = True
            while waiting_for_start:
                keys = event.getKeys(['space', 'escape'])
                current_time = core.getTime()
                
                if 'space' in keys:
                    waiting_for_start = False
                    print("First space press detected - starting test NOW!")
                elif 'escape' in keys:
                    win.close()
                    core.quit()
                core.wait(0.01)
        
            # Record the first tap time (the one that started the test)
            test_start = core.getTime()
            first_tap_time = 0.0  # First tap is at time 0
            tap_events = [test_start]  # First tap is the start
        
            print(f"Running rapid tapping test ({int(KEYBOARD_TAPPING_DURATION)} seconds)...")
            print("Timer started from first space press - counting additional taps...")

            # Progress display
            keyboard_progress_text = visual.TextStim(
                win=win,
                text='',
                color='white',
                height=int(32 * scale_avg),
                pos=(int(0 * scale_x), int(0 * scale_y))
            )

            # Test loop - continue tapping for the duration
            while core.getTime() - test_start < KEYBOARD_TAPPING_DURATION:
                current_time = core.getTime()
                time_remaining = KEYBOARD_TAPPING_DURATION - (current_time - test_start)
        
                # Record all key presses
                keys = event.getKeys(timeStamped=True)
                for key, timestamp in keys:
                    if key == 'space':
                        tap_events.append(timestamp)
                    elif key == 'escape':
                        win.close()
                        core.quit()
        
                # Update display
                keyboard_progress_text.text = (
                    f"KEYBOARD HARDWARE TEST\n\n"
                    f"TAP SPACE AS FAST AS YOU CAN!\n\n"
                    f"Time remaining: {time_remaining:.1f}s\n"
                    f"Taps detected: {len(tap_events)}"
                )
                keyboard_progress_text.draw()
                copyright_text_small.draw()
                draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                win.flip()

            print(f"\nRapid tapping test complete: {len(tap_events)} taps recorded")
        
            # Calculate intervals between all consecutive taps
            tap_intervals_raw = []
            max_interval = 0
            max_interval_position = 0
        
            if len(tap_events) >= 2:
                for i in range(1, len(tap_events)):
                    interval = (tap_events[i] - tap_events[i-1])
                    tap_intervals_raw.append(interval)
                    if interval > max_interval:
                        max_interval = interval
                        max_interval_position = i
        
            print(f"Maximum interval between taps: {max_interval:.2f} seconds at taps {max_interval_position-1} to {max_interval_position}")
            print(f"Gap threshold: {gap_threshold:.2f} seconds (20% of test duration)")
        
            # Store this attempt's data for debugging
            attempt_data = {
                'attempt_number': attempt_number,
                'total_taps': len(tap_events),
                'max_interval': max_interval,
                'max_interval_position': max_interval_position,
                'passed': False,
                'failure_reason': ''
            }
        
            # Check if any interval exceeds the 20% threshold
            if len(tap_events) < 2:
                # Not enough taps - automatic fail
                attempt_data['failure_reason'] = f'Insufficient taps ({len(tap_events)} taps)'
                all_attempts.append(attempt_data)
            
                print(f"✗ Insufficient taps for validation ({len(tap_events)} taps)")
                print("Showing retry warning screen...")
            
                retry_warning = visual.TextStim(
                    win=win,
                    text=(
                        "KEYBOARD TEST - RESTART REQUIRED\n\n"
                        f"Insufficient clicks ({len(tap_events)} out of {KEYBOARD_MIN_TAPS} needed)\n"
                        f"Too long between clicks (max allowed: {gap_threshold:.2f}s)\n\n"
                        "You need to tap CONTINUOUSLY and RAPIDLY.\n\n"
                        "IMPORTANT:\n"
                        "Start tapping IMMEDIATELY when you see\n"
                        "'START TAPPING NOW!' on the screen.\n"
                        "Continue tapping rapidly without stopping.\n\n"
                        ""
                    ),
                    color='red',
                    height=int(40 * scale_avg),
                    wrapWidth=int(6000 * scale_x),
                    pos=(int(0 * scale_x), int(0 * scale_y))
                )
        
            elif max_interval > gap_threshold:
                # Large gap detected
                attempt_data['failure_reason'] = f'Gap too large: {max_interval:.2f}s at position {max_interval_position}'
                all_attempts.append(attempt_data)
            
                print(f"✗ Gap too large between taps {max_interval_position-1} and {max_interval_position}: {max_interval:.2f}s > {gap_threshold:.2f}s threshold")
                print("Showing retry warning screen...")
            
                retry_warning = visual.TextStim(
                    win=win,
                    text=(
                        "KEYBOARD TEST - RESTART REQUIRED\n\n"
                        f"Insufficient clicks ({len(tap_events)} out of {KEYBOARD_MIN_TAPS} needed)\n"
                        f"Too long between clicks ({max_interval:.2f}s, max allowed: {gap_threshold:.2f}s)\n\n"
                        "You paused too long during tapping.\n\n"
                        "IMPORTANT:\n"
                        "Tap CONTINUOUSLY without stopping.\n"
                        "Keep tapping rapidly throughout the entire test.\n\n"
                        ""
                    ),
                    color='red',
                    height=int(40 * scale_avg),
                    wrapWidth=int(6000 * scale_x),
                    pos=(int(0 * scale_x), int(0 * scale_y))
                )
        
            else:
                # Test successful - all intervals acceptable
                attempt_data['passed'] = True
                attempt_data['failure_reason'] = 'PASSED'
                all_attempts.append(attempt_data)
            
                test_successful = True
                print("✓ All tap intervals within acceptable range")
        
            # If test failed, show retry screen
            if not test_successful:
            
                retry_warning = visual.TextStim(
                    win=win,
                    text=(
                        "KEYBOARD TEST - RESTART REQUIRED\n\n"
                        "Insufficient taps detected.\n\n"
                        f"You need to tap continuously and rapidly.\n\n"
                        "IMPORTANT:\n"
                        "Start tapping IMMEDIATELY when you see\n"
                        "'START TAPPING NOW!' on the screen.\n"
                        "Continue tapping rapidly until test ends.\n\n"
                        "IF YOU REPEATEDLY GET THIS SCREEN:\n"
                        "1. Press ESC to exit the program\n"
                        "2. Restart and complete the Performance Checklist\n"
                        "3. Close all background applications\n"
                        "4. Try the test again\n"
                        "5. If still failing, contact your researcher"
                    ),
                    color='red',
                    height=int(32 * scale_avg),  # Smaller to fit more text
                    wrapWidth=int(6000 * scale_x),
                    pos=(int(0 * scale_x), int(50 * scale_y))  # Move up slightly
                )
            
                retry_instr = visual.TextStim(
                    win=win,
                    text='Press K to retry',
                    color='red',
                    height=int(48 * scale_avg),
                    pos=(int(-250 * scale_x), int(-650 * scale_y)),  # Left side
                    bold=True
                )
                
                quit_instr_keyboard = visual.TextStim(
                    win=win,
                    text='Press ESC to exit',
                    color='red',
                    height=int(48 * scale_avg),
                    pos=(int(250 * scale_x), int(-650 * scale_y)),  # Right side
                    bold=True
                )
            
                retry_warning.draw()
                retry_instr.draw()
                quit_instr_keyboard.draw()
                copyright_text_small.draw()
                draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                win.flip()
            
                # Wait for K to retry or ESC to exit
                event.clearEvents()
                global_mouse.setVisible(True)  # Ensure mouse is visible for clicking
                waiting_retry = True
                last_click_time = 0
                while waiting_retry:
                    keys = event.getKeys(['k', 'escape'])
                    current_time = core.getTime()
                    
                    if 'k' in keys:
                        waiting_retry = False
                        print("User pressed K - restarting keyboard test...")
                    elif 'escape' in keys:
                        print("User pressed ESC - exiting program...")
                        win.close()
                        sys.exit(0)
                    
                    # Check for mouse clicks on instruction text
                    if current_time - last_click_time > 0.3:
                        if is_text_clicked(retry_instr, global_mouse):
                            print("User clicked RETRY")
                            waiting_retry = False
                            last_click_time = current_time
                            core.wait(0.2)
                        elif is_text_clicked(quit_instr_keyboard, global_mouse):
                            print("User clicked EXIT")
                            win.close()
                            sys.exit(0)
                    
                    core.wait(0.01)
            
                # Clear screen and prepare for retry
                copyright_text_small.draw()
                win.flip()
                event.clearEvents()
                core.wait(0.5)
    
        # Test completed successfully
        print(f"\n✓ Keyboard test completed successfully after {attempt_number} attempt(s)")
        print(f"Total attempts: {len(all_attempts)}")
        for att in all_attempts:
            print(f"  Attempt {att['attempt_number']}: {att['failure_reason']} ({att['total_taps']} taps, max gap: {att['max_interval']:.2f}s)")

        # Calculate tapping metrics from the successful attempt
        if len(tap_events) >= 2:  # Need at least 2 taps to calculate intervals
            # Calculate intervals between taps
            tap_intervals = [(tap_events[i] - tap_events[i-1]) * 1000 
                             for i in range(1, len(tap_events))]
    
            avg_tap_interval = statistics.mean(tap_intervals)
            tap_interval_std = statistics.stdev(tap_intervals) if len(tap_intervals) > 1 else 0
            min_tap_interval = min(tap_intervals)
            max_tap_interval = max(tap_intervals)
    
            # Calculate tap rate (Hz)
            avg_tap_rate = 1000.0 / avg_tap_interval if avg_tap_interval > 0 else 0
            max_tap_rate = 1000.0 / min_tap_interval if min_tap_interval > 0 else 0
    
            # Calculate coefficient of variation (CV)
            tap_cv = (tap_interval_std / avg_tap_interval) * 100 if avg_tap_interval > 0 else 0
    
            # Estimate keyboard polling rate from fastest taps
            # Human max tapping speed ~10-12 taps/sec, so intervals <100ms reveal polling
            if min_tap_interval <= 10.0:
                estimated_polling = "1000Hz (1ms) - High-end gaming keyboard"
            elif min_tap_interval <= 20.0:
                estimated_polling = "500Hz (2ms) - Gaming keyboard"
            elif min_tap_interval <= 40.0:
                estimated_polling = "250Hz (4ms) - Standard keyboard"
            elif min_tap_interval <= 80.0:
                estimated_polling = "125Hz (8ms) - Basic keyboard"
            else:
                estimated_polling = "Low polling rate - May be wireless or basic USB"
    
            # Check if threshold was met
            if len(tap_events) >= KEYBOARD_MIN_TAPS:
                print(f"THRESHOLD MET - Total taps: {len(tap_events)}")
            else:
                print(f"THRESHOLD NOT MET - Need at least {KEYBOARD_MIN_TAPS}, got {len(tap_events)}")
        
            print(f"Average tap rate: {avg_tap_rate:.1f} taps/sec")
            print(f"Max tap rate: {max_tap_rate:.1f} taps/sec")
            print(f"Average interval: {avg_tap_interval:.2f} ms")
            print(f"Min interval: {min_tap_interval:.2f} ms")
            print(f"Consistency (std dev): {tap_interval_std:.2f} ms")
            print(f"Consistency (CV): {tap_cv:.2f}%")
            print(f"Estimated polling: {estimated_polling}")
        else:
            # Less than 2 taps - cannot calculate any metrics
            print(f"INSUFFICIENT TAPS - Need at least 2 taps to calculate metrics, got {len(tap_events)}")
            tap_intervals = []
            avg_tap_interval = 0
            tap_interval_std = 0
            min_tap_interval = 0
            max_tap_interval = 0
            avg_tap_rate = 0
            max_tap_rate = 0
            tap_cv = 0
            estimated_polling = "UNKNOWN - Insufficient data"

        # Set compatibility variables
        repeat_events = tap_events
        repeat_intervals = tap_intervals
        avg_repeat_interval = avg_tap_interval
        repeat_interval_std = tap_interval_std
        min_repeat_interval = min_tap_interval
        max_repeat_interval = max_tap_interval
        avg_repeat_rate = avg_tap_rate
        repeat_cv = tap_cv

        latency_offsets = []
        avg_latency = 0
        latency_std = 0
        min_latency = 0
        max_latency = 0
        latency_range = 0
        acceptable_percent = 100
        latency_jitter = 0
        latency_cv = 0

        # Clear any lingering key presses and show "Please wait" message
        event.clearEvents()

        please_wait_text = visual.TextStim(
            win=win,
            text="Processing results...\n\nPlease wait...",
            color='white',
            height=30
        )
        please_wait_text.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        core.wait(2.0)  # 2 second delay to prevent accidental space presses

        # Show test results
        print("\n" + "=" * 80)
        print("KEYBOARD HARDWARE TEST RESULTS")
        print("=" * 80)

        # Determine performance rating
        keyboard_rating = "EXCELLENT"
        keyboard_color = "green"
        keyboard_recommendations = []

        if len(tap_events) < KEYBOARD_MIN_TAPS:
            keyboard_rating = "FAILED"
            keyboard_color = "red"
            keyboard_recommendations.append(f"- Test failed - need {KEYBOARD_MIN_TAPS} taps, got {len(tap_events)}")
            keyboard_recommendations.append("- User did not tap enough times")
            keyboard_recommendations.append("- Remote testing NOT possible")
        elif tap_cv > 40:
            keyboard_rating = "POOR"
            keyboard_color = "red"
            keyboard_recommendations.append("- Very high tapping inconsistency")
            keyboard_recommendations.append("- Likely wireless keyboard with poor signal")
            keyboard_recommendations.append("- Remote testing NOT recommended")
        elif tap_cv > 25:
            keyboard_rating = "FAIR"
            keyboard_color = "yellow"
            keyboard_recommendations.append("- Moderate keyboard input variation")
            keyboard_recommendations.append("- May indicate wireless interference or USB issues")
            keyboard_recommendations.append("- Remote testing may have reduced reliability")
        elif tap_cv > 15:
            keyboard_rating = "GOOD"
            keyboard_color = "lightgreen"

        # Check if max tap rate reveals polling issues
        if min_tap_interval > 50 and len(tap_events) >= KEYBOARD_MIN_TAPS:
            keyboard_recommendations.append("- Slow max tap rate detected")
            keyboard_recommendations.append("- May indicate low USB polling or wireless lag")

        keyboard_rec_text = "\n".join(keyboard_recommendations) if keyboard_recommendations else "Keyboard hardware is consistent and reliable for testing."
        
        # Add persistent help if poor/failed performance
        if keyboard_rating in ["FAILED", "POOR"]:
            keyboard_rec_text += (
                "\n\n"
                "CONSIDER: Switch to a hardwired (USB) keyboard if possible.\n"
                "Wireless keyboards often have inconsistent latency.\n\n"
                "IF YOU REPEATEDLY GET THIS SCREEN:\n"
                "1. Press ESC to exit the program\n"
                "2. Restart and complete the Performance Checklist\n"
                "3. Close all background applications\n"
                "4. Try the test again\n"
                "5. If still failing, contact your researcher for assistance"
            )
    
        # Store this session's data (includes all automatic retry attempts)
        keyboard_session_data = {
            'session_number': keyboard_session_number,
            'all_attempts': all_attempts.copy(),  # All automatic retry attempts in this session
            'final_attempt': attempt_number,
            'total_taps': len(tap_events),
            'avg_tap_rate': avg_tap_rate,
            'max_tap_rate': max_tap_rate,
            'avg_tap_interval': avg_tap_interval,
            'min_tap_interval': min_tap_interval,
            'tap_cv': tap_cv,
            'estimated_polling': estimated_polling,
            'keyboard_rating': keyboard_rating
        }
        all_keyboard_sessions.append(keyboard_session_data)
        print(f"Keyboard session #{keyboard_session_number} data saved (containing {len(all_attempts)} automatic attempts)")
    
        # Calculate estimated latencies (only if framerate test was run)
        if RUN_FRAMERATE_TEST:
            # Physical constants
            DISTANCE_TO_USER = 0.3  # meters
            SPEED_OF_LIGHT = 300000000  # m/s
            SPEED_OF_SOUND = 300  # m/s
        
            light_travel_time = (DISTANCE_TO_USER / SPEED_OF_LIGHT) * 1000  # ms
            sound_travel_time = (DISTANCE_TO_USER / SPEED_OF_SOUND) * 1000  # ms
        
            display_latency = stability_metrics['estimated_input_latency']
            # Keyboard latency = (polling interval / 2) + OS overhead
            # min_tap_interval reveals USB polling rate
            keyboard_input_latency = (min_tap_interval / 2) + 2 if min_tap_interval > 0 else 10.0
        
            visual_est_latency = display_latency + keyboard_input_latency + light_travel_time
            audio_est_latency = display_latency + keyboard_input_latency + sound_travel_time
        
            latency_section = (
                f"\nESTIMATED REACTION TEST LATENCIES:\n"
                f"Visual reaction: {visual_est_latency:.2f} ms\n"
                f"Audio reaction: {audio_est_latency:.2f} ms\n"
                f"(Display: {display_latency:.2f} ms + Keyboard: {keyboard_input_latency:.2f} ms + Travel)\n"
                f"[Keyboard = (min_interval/2) + 2ms OS overhead]\n\n"
            )
        else:
            latency_section = ""

        # PREVENT AUTO-COMPLETION: Clear events and add delay before showing results
        event.clearEvents()
        core.wait(1.0)
        event.clearEvents()

        # Show results
        keyboard_result_text = visual.TextStim(
            win=win,
            text=(
                f"=== KEYBOARD HARDWARE TEST - SESSION #{keyboard_session_number} ===\n"
                f"(Passed after {attempt_number} automatic attempts in this session)\n\n"
                f"PERFORMANCE RATING: {keyboard_rating}\n\n"
                f"RAPID TAPPING METRICS:\n"
                f"Total taps: {len(tap_events)}\n"
                f"Average tap rate: {avg_tap_rate:.1f} taps/sec\n"
                f"Maximum tap rate: {max_tap_rate:.1f} taps/sec\n"
                f"Average interval: {avg_tap_interval:.2f} ms\n"
                f"Minimum interval: {min_tap_interval:.2f} ms\n"
                f"Interval std dev: {tap_interval_std:.2f} ms\n"
                f"Consistency (CV): {tap_cv:.2f}%\n"
                f"Estimated polling rate: {estimated_polling}\n\n"
                f"{latency_section}"
                f"ANALYSIS:\n"
                f"{keyboard_rec_text}\n\n"
                f"NOTE: Rapid tapping is different from single reactions.\n"
                f"This test will not bias your actual test performance."
            ),
            color=keyboard_color,
            height=int(32 * scale_avg),
            wrapWidth=int(5070 * scale_x),
            pos=(int(0 * scale_x), int(50 * scale_y))
        )
    
        # Create colored control instructions
        continue_instr = visual.TextStim(
            win=win,
            text='Press K to continue',
            color='green',
            height=int(32 * scale_avg),
            pos=(int(-450 * scale_x), int(-650 * scale_y)),
            bold=True
        )
    
        redo_instr = visual.TextStim(
            win=win,
            text='Press G to redo test',
            color='yellow',
            height=int(32 * scale_avg),
            pos=(int(0 * scale_x), int(-650 * scale_y)),
            bold=True
        )
    
        quit_instr = visual.TextStim(
            win=win,
            text='Press ESC to cancel',
            color='red',
            height=int(32 * scale_avg),
            pos=(int(450 * scale_x), int(-650 * scale_y)),
            bold=True
        )
    
        keyboard_result_text.draw()
        continue_instr.draw()
        redo_instr.draw()
        quit_instr.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()

        # Wait for user decision
        print("WAITING FOR EXPERIMENTER DECISION:")
        print(f"Keyboard Hardware Rating: {keyboard_rating}")
        print(f"Tapping consistency (CV): {tap_cv:.2f}%")
        print("Press K to continue, G to redo test, or ESC to cancel")

        # Clear any lingering key presses
        event.clearEvents()
        core.wait(0.3)

        global_mouse.setVisible(True)  # Show mouse for clicking instructions
        waiting = True
        last_click_time = 0
        while waiting:
            keys = event.getKeys(['k', 'escape', 'g'])
            current_time = core.getTime()
            
            if 'k' in keys:
                print("\nExperimenter approved - Continuing to next section...")
                waiting = False
                redo_keyboard = False
            elif 'g' in keys:
                print("\nExperimenter chose to redo keyboard test")
                waiting = False
                redo_keyboard = True
            elif 'escape' in keys:
                print("\nExperiment cancelled by experimenter")
                win.close()
                core.quit()
            
            # Check for mouse clicks on instruction text
            if current_time - last_click_time > 0.3:
                if is_text_clicked(continue_instr, global_mouse):
                    print("\nExperimenter clicked CONTINUE")
                    waiting = False
                    redo_keyboard = False
                    last_click_time = current_time
                    core.wait(0.2)
                elif is_text_clicked(redo_instr, global_mouse):
                    print("\nExperimenter clicked REDO")
                    waiting = False
                    redo_keyboard = True
                    last_click_time = current_time
                    core.wait(0.2)
                elif is_text_clicked(quit_instr, global_mouse):
                    print("\nExperimenter clicked CANCEL")
                    win.close()
                    core.quit()
            
            core.wait(0.01)
    
        # If redo requested, continue loop; otherwise break
        if not redo_keyboard:
            keyboard_test_complete = True

    else:
        # Keyboard test skipped - set default values
        keyboard_test_complete = True
        
        print("\n" + "=" * 80)
        print("STEP 5: KEYBOARD HARDWARE TEST SKIPPED")
        print("RUN_KEYBOARD_TEST is set to False")
        print("=" * 80)
        
        # Set default values
        tap_events = []
        tap_intervals = []
        avg_tap_interval = 0
        tap_interval_std = 0
        min_tap_interval = 0
        max_tap_interval = 0
        avg_tap_rate = 0
        max_tap_rate = 0
        tap_cv = 0
        estimated_polling = "SKIPPED"
        all_attempts = []
        attempt_number = 0
        gap_threshold = 0
        all_keyboard_sessions = []
        keyboard_session_number = 0
        
        repeat_events = []
        repeat_intervals = []
        avg_repeat_interval = 0
        repeat_interval_std = 0
        min_repeat_interval = 0
        max_repeat_interval = 0
        avg_repeat_rate = 0
        repeat_cv = 0
        
        keyboard_rating = "SKIPPED"
        keyboard_color = "gray"
        
        # Show skip screen
        skip_screen = visual.TextStim(
            win=win,
            text=(
                "=== KEYBOARD HARDWARE TEST ===\n\n"
                "This test has been skipped.\n\n"
                "RUN_KEYBOARD_TEST is set to False."
            ),
            color='yellow',
            height=int(48 * scale_avg),
            wrapWidth=int(5070 * scale_x),
            pos=(int(0 * scale_x), int(50 * scale_y))
        )
        
        continue_instr = visual.TextStim(
            win=win,
            text='Press SPACE to continue',
            color='green',
            height=int(32 * scale_avg),
            pos=(int(-350 * scale_x), int(-650 * scale_y)),
            bold=True
        )
        
        quit_instr = visual.TextStim(
            win=win,
            text='Press ESC to exit',
            color='red',
            height=int(32 * scale_avg),
            pos=(int(350 * scale_x), int(-650 * scale_y)),
            bold=True
        )
        
        skip_screen.draw()
        continue_instr.draw()
        quit_instr.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        print("Keyboard test skipped - waiting for user input...")
        global_mouse.setVisible(True)  # Show mouse for clicking instructions
        waiting = True
        while waiting:
            keys = event.getKeys(['space', 'escape'])
            current_time = core.getTime()
            
            if 'space' in keys:
                waiting = False
            elif 'escape' in keys:
                win.close()
                core.quit()
            # Check for mouse clicks on instruction text
            if current_time - last_click_time > 0.3:
                if is_text_clicked(continue_instr, global_mouse):
                    print("User clicked CONTINUE")
                    waiting = False
                    last_click_time = current_time
                    core.wait(0.2)
                elif is_text_clicked(quit_instr, global_mouse):
                    print("User clicked QUIT")
                    win.close()
                    core.quit()
            
            core.wait(0.01)


# ===== CALCULATE ESTIMATED REACTION TEST LATENCIES =====
# Based on framerate test (display latency) and keyboard test (input latency)
# Physical constants
DISTANCE_TO_USER = 0.3  # meters (30 cm typical monitor/user distance)
SPEED_OF_LIGHT = 300000000  # m/s
SPEED_OF_SOUND = 300  # m/s (approximate at sea level, room temperature)

# Calculate travel times
light_travel_time = (DISTANCE_TO_USER / SPEED_OF_LIGHT) * 1000  # Convert to ms

# Sound travel time depends on headphone type
if using_over_ear_headphones:
    sound_travel_time = 0.0  # Over-ear headphones eliminate travel distance
    print("Using over-ear headphones - sound travel time set to 0 ms")
else:
    sound_travel_time = (DISTANCE_TO_USER / SPEED_OF_SOUND) * 1000  # Convert to ms
    print(f"Using speakers/earbuds - sound travel time: {sound_travel_time:.2f} ms")

# Calculate system latencies
if RUN_FRAMERATE_TEST and RUN_KEYBOARD_TEST:
    # Display latency from framerate test
    display_latency = stability_metrics['estimated_input_latency']
    
    # Keyboard input latency from tapping test
    # Formula: (polling interval / 2) + OS overhead
    # min_tap_interval reveals USB polling rate
    keyboard_input_latency = (min_tap_interval / 2) + 2 if min_tap_interval > 0 else 10.0  # Default 10ms if no data
    
    # Total estimated latencies for reaction tests
    visual_reaction_estimated_latency = display_latency + keyboard_input_latency + light_travel_time
    audio_reaction_estimated_latency = display_latency + keyboard_input_latency + sound_travel_time
    
    print(f"\nEstimated System Latencies:")
    print(f"  Display latency: {display_latency:.2f} ms")
    print(f"  Keyboard input latency: {keyboard_input_latency:.2f} ms (from min_tap_interval/2 + 2ms)")
    print(f"  Light travel time (0.3m): {light_travel_time:.6f} ms (negligible)")
    print(f"  Sound travel time (0.3m): {sound_travel_time:.2f} ms")
    print(f"  Visual reaction test estimated latency: {visual_reaction_estimated_latency:.2f} ms")
    print(f"  Audio reaction test estimated latency: {audio_reaction_estimated_latency:.2f} ms")
elif RUN_FRAMERATE_TEST:
    display_latency = stability_metrics['estimated_input_latency']
    keyboard_input_latency = 10.0  # Default estimate
    visual_reaction_estimated_latency = display_latency + keyboard_input_latency + light_travel_time
    audio_reaction_estimated_latency = display_latency + keyboard_input_latency + sound_travel_time
    print(f"\nEstimated latencies (keyboard test skipped, using default 10ms keyboard latency):")
    print(f"  Visual reaction test estimated latency: {visual_reaction_estimated_latency:.2f} ms")
    print(f"  Audio reaction test estimated latency: {audio_reaction_estimated_latency:.2f} ms")
elif RUN_KEYBOARD_TEST:
    display_latency = (1000.0 / expected_fps) * 1.5  # Default estimate
    # Formula: (polling interval / 2) + OS overhead
    keyboard_input_latency = (min_tap_interval / 2) + 2 if min_tap_interval > 0 else 10.0
    visual_reaction_estimated_latency = display_latency + keyboard_input_latency + light_travel_time
    audio_reaction_estimated_latency = display_latency + keyboard_input_latency + sound_travel_time
    print(f"\nEstimated latencies (framerate test skipped, using default display latency):")
    print(f"  Visual reaction test estimated latency: {visual_reaction_estimated_latency:.2f} ms")
    print(f"  Audio reaction test estimated latency: {audio_reaction_estimated_latency:.2f} ms")
else:
    # Both tests skipped
    display_latency = (1000.0 / expected_fps) * 1.5
    keyboard_input_latency = 10.0
    visual_reaction_estimated_latency = display_latency + keyboard_input_latency + light_travel_time
    audio_reaction_estimated_latency = display_latency + keyboard_input_latency + sound_travel_time
    print(f"\nEstimated latencies (both tests skipped, using defaults):")
    print(f"  Visual reaction test estimated latency: {visual_reaction_estimated_latency:.2f} ms")
    print(f"  Audio reaction test estimated latency: {audio_reaction_estimated_latency:.2f} ms")


# ===== STEP 5.5: AUDIO VERIFICATION TEST =====
if RUN_AUDIO_VERIFICATION:
    print("\n" + "=" * 80)
    print("STEP 5.5: AUDIO VERIFICATION TEST")
    print("=" * 80)
    
    # Clear screen and wait - PREVENT KEY CARRYOVER
    copyright_text_small.draw()
    win.flip()
    event.clearEvents()  # Clear any lingering key presses
    core.wait(1.0)  # Longer delay to prevent accidental advancement
    event.clearEvents()  # Clear again after wait
    
    # Create three test tones at different frequencies for accessibility
    tone_low = sound.Sound(value=250, secs=0.5, volume=0.7)    # 250Hz - Low frequency
    tone_mid = sound.Sound(value=1000, secs=0.5, volume=0.7)   # 1000Hz - Mid frequency (original)
    tone_high = sound.Sound(value=2000, secs=0.5, volume=0.7)  # 2000Hz - High frequency
    
    # Show instruction screen
    audio_verify_instruction = visual.TextStim(
        win=win,
        text=(
            "=== AUDIO VERIFICATION & SOUND SELECTION ===\n\n"
            "Select which sound you will use for the audio reaction test.\n\n"
            "Three different frequencies are available for accessibility:"
        ),
        color='white',
        height=int(36 * scale_avg),
        wrapWidth=int(6500 * scale_x),
        pos=(int(0 * scale_x), int(280 * scale_y))  # Top of screen
    )
    
    # Instruction for keys
    key_instruction = visual.TextStim(
        win=win,
        text=(
            "Press A = Low frequency (250 Hz)\n"
            "Press G = Mid frequency (1000 Hz)\n"
            "Press K = High frequency (2000 Hz)"
        ),
        color='yellow',
        height=int(32 * scale_avg),
        wrapWidth=int(6500 * scale_x),
        pos=(int(0 * scale_x), int(100 * scale_y)),  # Moved down from 150
        bold=True
    )
    
    # Volume control instruction
    volume_instruction = visual.TextStim(
        win=win,
        text=(
            "Press UP ARROW to increase volume | Press DOWN ARROW to decrease volume"
        ),
        color='cyan',
        height=int(28 * scale_avg),
        wrapWidth=int(6500 * scale_x),
        pos=(int(0 * scale_x), int(20 * scale_y)),  # Above selection instruction
        bold=True
    )
    
    # Volume control buttons (clickable)
    volume_up_btn = visual.Rect(
        win=win,
        width=int(180 * scale_x),
        height=int(80 * scale_avg),
        lineColor='cyan',
        lineWidth=3,
        fillColor='darkblue',
        pos=(int(-350 * scale_x), int(-530 * scale_y))
    )
    
    volume_up_text = visual.TextStim(
        win=win,
        text='VOLUME\nUP\n▲',
        color='cyan',
        height=int(28 * scale_avg),
        pos=(int(-350 * scale_x), int(-530 * scale_y)),
        bold=True
    )
    
    volume_down_btn = visual.Rect(
        win=win,
        width=int(180 * scale_x),
        height=int(80 * scale_avg),
        lineColor='cyan',
        lineWidth=3,
        fillColor='darkblue',
        pos=(int(350 * scale_x), int(-530 * scale_y))
    )
    
    volume_down_text = visual.TextStim(
        win=win,
        text='VOLUME\nDOWN\n▼',
        color='cyan',
        height=int(28 * scale_avg),
        pos=(int(350 * scale_x), int(-530 * scale_y)),
        bold=True
    )
    
    # Instruction for selection
    selection_instruction = visual.TextStim(
        win=win,
        text=(
            "You can press these keys multiple times to test each sound.\n"
            "Then CLICK the sound box you prefer with your MOUSE.\n"
            "Selected sound will show a GREEN BORDER."
        ),
        color='white',
        height=int(32 * scale_avg),
        wrapWidth=int(6500 * scale_x),
        pos=(int(0 * scale_x), int(-70 * scale_y))  # Moved down to make more room
    )
    
    # Create three sound option boxes - moved down even further
    box_spacing = int(400 * scale_x)  # SCALED, increased from 300 for better visual separation
    box_y = int(-270 * scale_y)  # SCALED - moved down from -180 to -270 for more text space above
    
    sound_box_low = visual.Rect(
        win=win,
        width=int(250 * scale_x),
        height=int(150 * scale_avg),
        lineColor='white',
        lineWidth=3,
        fillColor='darkgray',
        pos=(-box_spacing, box_y)
    )
    
    sound_box_mid = visual.Rect(
        win=win,
        width=int(250 * scale_x),
        height=int(150 * scale_avg),
        lineColor='white',
        lineWidth=3,
        fillColor='darkgray',
        pos=(0, box_y)
    )
    
    sound_box_high = visual.Rect(
        win=win,
        width=int(250 * scale_x),
        height=int(150 * scale_avg),
        lineColor='white',
        lineWidth=3,
        fillColor='darkgray',
        pos=(box_spacing, box_y)
    )
    
    # Create selection borders (green, initially invisible)
    selection_border_low = visual.Rect(
        win=win,
        width=int(260 * scale_x),
        height=int(160 * scale_avg),
        lineColor='green',
        lineWidth=8,
        fillColor=None,
        pos=(-box_spacing, box_y)
    )
    
    selection_border_mid = visual.Rect(
        win=win,
        width=int(260 * scale_x),
        height=int(160 * scale_avg),
        lineColor='green',
        lineWidth=8,
        fillColor=None,
        pos=(0, box_y)
    )
    
    selection_border_high = visual.Rect(
        win=win,
        width=int(260 * scale_x),
        height=int(160 * scale_avg),
        lineColor='green',
        lineWidth=8,
        fillColor=None,
        pos=(box_spacing, box_y)
    )
    
    # Create labels for each sound
    label_low = visual.TextStim(
        win=win,
        text='LOW\n250 Hz\n\nPress A',
        color='white',
        height=int(28 * scale_avg),
        pos=(-box_spacing, box_y),
        bold=True
    )
    
    label_mid = visual.TextStim(
        win=win,
        text='MID\n1000 Hz\n\nPress G',
        color='white',
        height=int(28 * scale_avg),
        pos=(0, box_y),
        bold=True
    )
    
    label_high = visual.TextStim(
        win=win,
        text='HIGH\n2000 Hz\n\nPress K',
        color='white',
        height=int(28 * scale_avg),
        pos=(box_spacing, box_y),
        bold=True
    )
    
    # Create colored control instructions - moved down
    instruction_bottom = visual.TextStim(
        win=win,
        text='CLICK a sound box to select',
        color='yellow',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-460 * scale_y)),  # Moved down from -380
        bold=True
    )
    
    # Volume display
    volume_display = visual.TextStim(
        win=win,
        text='',
        color='cyan',
        height=int(28 * scale_avg),
        pos=(int(0 * scale_x), int(-530 * scale_y)),
        bold=True
    )
    
    # Dynamic continue instruction (only shows after selection)
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to continue',
        color='green',
        height=int(36 * scale_avg),
        pos=(int(-350 * scale_x), int(-700 * scale_y)),  # Moved down and to the left
        bold=True,
        wrapWidth=int(600 * scale_x)  # Added wrap width to prevent wrapping
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-700 * scale_y)),  # Moved to the right
        bold=True
    )
    
    # Create mouse for selection
    audio_mouse = event.Mouse(visible=True, win=win)
    
    # Track selection state and volume
    selected_sound = None  # 'low', 'mid', or 'high'
    selected_frequency = None
    current_volume = 0.7  # Start at 70% volume
    
    print("Waiting for audio verification and sound selection...")
    audio_verified = False
    
    # Update tone volumes
    tone_low.setVolume(current_volume)
    tone_mid.setVolume(current_volume)
    tone_high.setVolume(current_volume)
    
    while not audio_verified:
        # Check keyboard for sound playback and volume control
        keys = event.getKeys(['a', 'g', 'k', 'space', 'escape', 'up', 'down'])
        if 'a' in keys:
            tone_low.play()
            print(f"Playing LOW frequency (250 Hz) at {int(current_volume * 100)}% volume")
            core.wait(0.1)
        elif 'g' in keys:
            tone_mid.play()
            print(f"Playing MID frequency (1000 Hz) at {int(current_volume * 100)}% volume")
            core.wait(0.1)
        elif 'k' in keys:
            tone_high.play()
            print(f"Playing HIGH frequency (2000 Hz) at {int(current_volume * 100)}% volume")
            core.wait(0.1)
        elif 'up' in keys:
            # Increase volume
            current_volume = min(1.0, current_volume + 0.1)
            tone_low.setVolume(current_volume)
            tone_mid.setVolume(current_volume)
            tone_high.setVolume(current_volume)
            print(f"Volume increased to {int(current_volume * 100)}%")
            core.wait(0.1)
        elif 'down' in keys:
            # Decrease volume
            current_volume = max(0.1, current_volume - 0.1)
            tone_low.setVolume(current_volume)
            tone_mid.setVolume(current_volume)
            tone_high.setVolume(current_volume)
            print(f"Volume decreased to {int(current_volume * 100)}%")
            core.wait(0.1)
        elif 'space' in keys:
            if selected_sound is not None:
                audio_verified = True
                print(f"Audio verified - user selected {selected_sound.upper()} frequency ({selected_frequency} Hz) at {int(current_volume * 100)}% volume")
            else:
                print("Cannot continue - no sound selected. Please click a sound box first.")
        elif 'escape' in keys:
            win.close()
            core.quit()
        
        # Check mouse clicks for sound box selection
        if audio_mouse.getPressed()[0]:  # Left click
            mouse_pos = audio_mouse.getPos()
            
            # Check if clicked on SPACE or ESC instruction text
            if selected_sound is not None:  # Only check SPACE if sound is selected
                if is_text_clicked(continue_instr, audio_mouse):
                    audio_verified = True
                    print(f"User clicked CONTINUE - Audio verified with {selected_sound.upper()} frequency")
                    core.wait(0.3)
                    continue  # Skip rest of mouse checking
            
            if is_text_clicked(quit_instr, audio_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
            
            # Check if clicked on volume control buttons - PROPERLY SCALED
            volume_up_x = int(-350 * scale_x)
            volume_up_y = int(-530 * scale_y)
            volume_btn_half_width = int(90 * scale_x)  # Half of 180
            volume_btn_half_height = int(40 * scale_avg)  # Half of 80
            
            if (abs(mouse_pos[0] - volume_up_x) < volume_btn_half_width and 
                abs(mouse_pos[1] - volume_up_y) < volume_btn_half_height):
                # Volume UP button clicked
                current_volume = min(1.0, current_volume + 0.1)
                tone_low.setVolume(current_volume)
                tone_mid.setVolume(current_volume)
                tone_high.setVolume(current_volume)
                print(f"User clicked VOLUME UP - Volume increased to {int(current_volume * 100)}%")
                core.wait(0.3)  # Debounce
                continue
            
            volume_down_x = int(350 * scale_x)
            volume_down_y = int(-530 * scale_y)
            
            if (abs(mouse_pos[0] - volume_down_x) < volume_btn_half_width and 
                abs(mouse_pos[1] - volume_down_y) < volume_btn_half_height):
                # Volume DOWN button clicked
                current_volume = max(0.1, current_volume - 0.1)
                tone_low.setVolume(current_volume)
                tone_mid.setVolume(current_volume)
                tone_high.setVolume(current_volume)
                print(f"User clicked VOLUME DOWN - Volume decreased to {int(current_volume * 100)}%")
                core.wait(0.3)  # Debounce
                continue
            
            # Check if clicked on low sound box
            if (abs(mouse_pos[0] - (-box_spacing)) < (125 * scale_x) and 
                abs(mouse_pos[1] - box_y) < 75):
                selected_sound = 'low'
                selected_frequency = 250
                print(f"Selected: LOW frequency (250 Hz)")
                core.wait(0.3)  # Debounce
                
            # Check if clicked on mid sound box
            elif (abs(mouse_pos[0] - 0) < (125 * scale_x) and 
                  abs(mouse_pos[1] - box_y) < 75):
                selected_sound = 'mid'
                selected_frequency = 1000
                print(f"Selected: MID frequency (1000 Hz)")
                core.wait(0.3)  # Debounce
                
            # Check if clicked on high sound box
            elif (abs(mouse_pos[0] - box_spacing) < (125 * scale_x) and 
                  abs(mouse_pos[1] - box_y) < 75):
                selected_sound = 'high'
                selected_frequency = 2000
                print(f"Selected: HIGH frequency (2000 Hz)")
                core.wait(0.3)  # Debounce
        
        # Update volume display text
        volume_display.text = f"Current Volume: {int(current_volume * 100)}%"
        
        # Draw everything
        audio_verify_instruction.draw()
        key_instruction.draw()
        volume_instruction.draw()
        
        # Draw volume control buttons
        volume_up_btn.draw()
        volume_up_text.draw()
        volume_down_btn.draw()
        volume_down_text.draw()
        
        selection_instruction.draw()
        
        # Draw sound boxes
        sound_box_low.draw()
        sound_box_mid.draw()
        sound_box_high.draw()
        
        # Draw selection borders only for selected sound
        if selected_sound == 'low':
            selection_border_low.draw()
        elif selected_sound == 'mid':
            selection_border_mid.draw()
        elif selected_sound == 'high':
            selection_border_high.draw()
        
        # Draw labels
        label_low.draw()
        label_mid.draw()
        label_high.draw()
        
        volume_display.draw()
        instruction_bottom.draw()
        
        # Only show continue prompt if a sound has been selected
        if selected_sound is not None:
            continue_instr.draw()
        
        quit_instr.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        core.wait(0.01)
    
    # Update the beep sound for audio reaction test with selected frequency
    print(f"\nUpdating audio reaction test to use {selected_frequency} Hz...")
    beep = sound.Sound(value=selected_frequency, secs=1.0, hamming=True)
    # Create continuous looping sound with longer duration for smoother transitions
    beep_continuous = sound.Sound(value=selected_frequency, secs=2.0, hamming=True, loops=-1)
    
    # Show confirmation
    confirm_text = visual.TextStim(
        win=win,
        text=(
            "AUDIO SOUND SELECTED\n\n"
            f"Selected frequency: {selected_frequency} Hz ({selected_sound.upper()})\n\n"
            "This sound will be used for the audio reaction test.\n\n"
            "Proceeding to test overview..."
        ),
        color='green',
        height=int(36 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(0 * scale_y))
    )
    confirm_text.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    core.wait(2.0)  # Show confirmation for 2 seconds
    
else:
    # Audio verification skipped - use default mid frequency
    selected_frequency = 1000  # Default to mid frequency
    selected_sound = 'mid'
    print("\n" + "=" * 80)
    print("STEP 5.5: AUDIO VERIFICATION TEST SKIPPED")
    print("RUN_AUDIO_VERIFICATION is set to False")
    print(f"Using default frequency: {selected_frequency} Hz (MID)")
    print("=" * 80)
    
    # Initialize beep sounds with default frequency
    beep = sound.Sound(value=selected_frequency, secs=1.0, hamming=True)
    # Longer duration for smoother continuous looping
    beep_continuous = sound.Sound(value=selected_frequency, secs=2.0, hamming=True, loops=-1)
    
    # Show skip screen
    skip_screen = visual.TextStim(
        win=win,
        text=(
            "=== AUDIO VERIFICATION TEST ===\n\n"
            "This test has been skipped.\n\n"
            "RUN_AUDIO_VERIFICATION is set to False.\n\n"
            f"Using default frequency: {selected_frequency} Hz (MID)"
        ),
        color='yellow',
        height=int(48 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to continue',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to exit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    skip_screen.draw()
    continue_instr.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    print("Audio verification skipped - waiting for user input...")
    global_mouse.setVisible(True)
    waiting = True
    last_click_time = 0
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        
        # Check for mouse clicks on instruction text
        if current_time - last_click_time > 0.3:
            if is_text_clicked(continue_instr, global_mouse):
                print("User clicked CONTINUE")
                waiting = False
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(quit_instr, global_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
        
        core.wait(0.01)


# ===== STEP 6: OVERALL TEST INSTRUCTIONS =====
print("\n" + "=" * 80)
print("STEP 6: OVERALL TEST INSTRUCTIONS")
print("=" * 80)

# Clear screen and wait - PREVENT KEY CARRYOVER
copyright_text_small.draw()
win.flip()
event.clearEvents()
core.wait(1.0)  # Longer delay to prevent accidental advancement
event.clearEvents()

# Clear any lingering events
event.clearEvents()
core.wait(0.5)

# ===== IMPORTANT REMINDERS BEFORE STARTING =====
reminders_complete = False
while not reminders_complete:
    print("\n" + "=" * 80)
    print("SHOWING IMPORTANT REMINDERS")
    print("=" * 80)

    # Show single monitor and fatigue disclaimers with redo options
    reminder_screen = visual.TextStim(
        win=win,
        text=(
            "=== IMPORTANT REMINDERS BEFORE STARTING ===\n\n"
            "SINGLE MONITOR REQUIREMENT:\n"
            "You should be using ONLY ONE MONITOR:\n"
            "- Laptop users: Use ONLY your laptop screen\n"
            "- Desktop users: Use ONLY one monitor\n"
            "Multiple monitors can cause performance issues.\n\n"
            "HEADPHONES REQUIREMENT:\n"
            "If using headphones, they MUST be WIRED (not wireless).\n"
            "Wireless headphones add latency and jitter.\n"
            "If you have wireless headphones, use computer speakers instead.\n\n"
            "MENTAL FATIGUE & TEST CONTINUITY:\n"
            "This test is designed to induce mental fatigue.\n"
            "The GOAL is to observe performance when tired.\n\n"
            "PLEASE DO NOT TAKE BREAKS during the test.\n"
            "Continue even if you feel tired - this is expected.\n"
            "Your tired performance is valuable data.\n\n"
            "SWITCHED EQUIPMENT?\n"
            "You can re-test Audio, Framerate, or Keyboard below.\n\n"
            "Ready to begin?"
        ),
        color='yellow',
        height=int(28 * scale_avg),
        wrapWidth=int(6500 * scale_x),
        pos=(int(0 * scale_x), int(150 * scale_y))
    )

    continue_reminder = visual.TextStim(
        win=win,
        text='Press K to continue to test overview',
        color='green',
        height=int(30 * scale_avg),
        pos=(int(0 * scale_x), int(-450 * scale_y)),
        bold=True,
        wrapWidth=int(1500 * scale_x)
    )
    
    # Redo test buttons - arranged horizontally
    redo_audio_btn = visual.TextStim(
        win=win,
        text='A = Redo Audio',
        color='cyan',
        height=int(26 * scale_avg),
        pos=(int(-400 * scale_x), int(-550 * scale_y)),
        bold=True,
        wrapWidth=int(350 * scale_x)
    )
    
    redo_framerate_btn = visual.TextStim(
        win=win,
        text='F = Redo Framerate',
        color='cyan',
        height=int(26 * scale_avg),
        pos=(int(0 * scale_x), int(-550 * scale_y)),
        bold=True,
        wrapWidth=int(400 * scale_x)
    )
    
    redo_keyboard_btn = visual.TextStim(
        win=win,
        text='R = Redo Keyboard',
        color='cyan',
        height=int(26 * scale_avg),
        pos=(int(400 * scale_x), int(-550 * scale_y)),
        bold=True,
        wrapWidth=int(400 * scale_x)
    )

    quit_reminder = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(26 * scale_avg),
        pos=(int(0 * scale_x), int(-650 * scale_y)),
        bold=True
    )

    reminder_screen.draw()
    continue_reminder.draw()
    redo_audio_btn.draw()
    redo_framerate_btn.draw()
    redo_keyboard_btn.draw()
    quit_reminder.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()

    print("Waiting for user input...")
    print("Options: K=continue, A=redo audio, F=redo framerate, R=redo keyboard, ESC=quit")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting_reminder = True
    last_click_time = 0
    
    while waiting_reminder:
        # Check for mouse clicks FIRST, before keyboard input
        current_time = core.getTime()
        
        # Initialize keys as empty list
        keys = []
        
        # Check mouse clicks first with higher priority
        if current_time - last_click_time > 0.3:
            if is_text_clicked(continue_reminder, global_mouse):
                print("User clicked CONTINUE")
                keys = ['k']
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(redo_audio_btn, global_mouse):
                print("User clicked REDO AUDIO")
                keys = ['a']
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(redo_framerate_btn, global_mouse):
                print("User clicked REDO FRAMERATE")
                keys = ['f']
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(redo_keyboard_btn, global_mouse):
                print("User clicked REDO KEYBOARD")
                keys = ['r']
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(quit_reminder, global_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
        
        # If no mouse clicks detected, get keyboard input
        if not keys:
            keys = event.getKeys(['k', 'escape', 'a', 'f', 'r'])
        
        # Now process keys (from mouse OR keyboard)
        if 'k' in keys:
            waiting_reminder = False
            reminders_complete = True
            print("User ready to begin - proceeding to test overview...")
        elif 'a' in keys:
            waiting_reminder = False
            reminders_complete = False  # Return to reminders after test
            
            # Check if audio verification is enabled
            if not RUN_AUDIO_VERIFICATION:
                print("Cannot redo audio verification - RUN_AUDIO_VERIFICATION is disabled")
                error_msg = visual.TextStim(
                    win=win,
                    text=(
                        "AUDIO REDO NOT AVAILABLE\n\n"
                        "RUN_AUDIO_VERIFICATION is set to False.\n\n"
                        "Cannot redo a test that was skipped.\n\n"
                        "Returning to reminders..."
                    ),
                    color='red',
                    height=int(40 * scale_avg),
                    pos=(int(0 * scale_x), int(0 * scale_y))
                )
                error_msg.draw()
                copyright_text_small.draw()
                win.flip()
                core.wait(2.0)
                continue  # Return to reminders loop
            
            print("User chose to redo audio verification...")
            
            # Show redoing message
            show_simple_message(win, "REDOING AUDIO VERIFICATION", "Starting now...", 'cyan', scale_x, scale_y, scale_avg, wait_time=1.5, show_copyright=True, copyright_text_small=copyright_text_small)
            # ===== FULL AUDIO VERIFICATION TEST =====
            # Clear screen and wait - PREVENT KEY CARRYOVER
            copyright_text_small.draw()
            win.flip()
            event.clearEvents()  # Clear any lingering key presses
            core.wait(1.0)  # Longer delay to prevent accidental advancement
            event.clearEvents()  # Clear again after wait
            
            # Create three test tones at different frequencies for accessibility
            tone_low = sound.Sound(value=250, secs=0.5, volume=0.7)    # 250Hz - Low frequency
            tone_mid = sound.Sound(value=1000, secs=0.5, volume=0.7)   # 1000Hz - Mid frequency (original)
            tone_high = sound.Sound(value=2000, secs=0.5, volume=0.7)  # 2000Hz - High frequency
            
            # Show instruction screen
            audio_verify_instruction = visual.TextStim(
                win=win,
                text=(
                    "=== AUDIO VERIFICATION & SOUND SELECTION ===\n\n"
                    "Select which sound you will use for the audio reaction test.\n\n"
                    "Three different frequencies are available for accessibility:"
                ),
                color='white',
                height=int(36 * scale_avg),
                wrapWidth=int(6500 * scale_x),
                pos=(int(0 * scale_x), int(280 * scale_y))  # Top of screen
            )
            
            # Instruction for keys
            key_instruction = visual.TextStim(
                win=win,
                text=(
                    "Press A = Low frequency (250 Hz)\n"
                    "Press G = Mid frequency (1000 Hz)\n"
                    "Press K = High frequency (2000 Hz)"
                ),
                color='yellow',
                height=int(32 * scale_avg),
                wrapWidth=int(6500 * scale_x),
                pos=(int(0 * scale_x), int(100 * scale_y)),  # Moved down from 150
                bold=True
            )
            
            # Volume control instruction
            volume_instruction = visual.TextStim(
                win=win,
                text=(
                    "Press UP ARROW to increase volume | Press DOWN ARROW to decrease volume"
                ),
                color='cyan',
                height=int(28 * scale_avg),
                wrapWidth=int(6500 * scale_x),
                pos=(int(0 * scale_x), int(20 * scale_y)),  # Above selection instruction
                bold=True
            )
            
            # Volume control buttons (clickable)
            volume_up_btn = visual.Rect(
                win=win,
                width=int(180 * scale_x),
                height=int(80 * scale_avg),
                lineColor='cyan',
                lineWidth=3,
                fillColor='darkblue',
                pos=(int(-350 * scale_x), int(-530 * scale_y))
            )
            
            volume_up_text = visual.TextStim(
                win=win,
                text='VOLUME\nUP\n▲',
                color='cyan',
                height=int(28 * scale_avg),
                pos=(int(-350 * scale_x), int(-530 * scale_y)),
                bold=True
            )
            
            volume_down_btn = visual.Rect(
                win=win,
                width=int(180 * scale_x),
                height=int(80 * scale_avg),
                lineColor='cyan',
                lineWidth=3,
                fillColor='darkblue',
                pos=(int(350 * scale_x), int(-530 * scale_y))
            )
            
            volume_down_text = visual.TextStim(
                win=win,
                text='VOLUME\nDOWN\n▼',
                color='cyan',
                height=int(28 * scale_avg),
                pos=(int(350 * scale_x), int(-530 * scale_y)),
                bold=True
            )
            
            # Instruction for selection
            selection_instruction = visual.TextStim(
                win=win,
                text=(
                    "You can press these keys multiple times to test each sound.\n"
                    "Then CLICK the sound box you prefer with your MOUSE.\n"
                    "Selected sound will show a GREEN BORDER."
                ),
                color='white',
                height=int(32 * scale_avg),
                wrapWidth=int(6500 * scale_x),
                pos=(int(0 * scale_x), int(-70 * scale_y))  # Moved down to make more room
            )
            
            # Create three sound option boxes - moved down even further
            box_spacing = 300
            box_y = -270  # Moved down from -180 to -270 for more text space above
            
            sound_box_low = visual.Rect(
                win=win,
                width=int(250 * scale_x),
                height=int(150 * scale_avg),
                lineColor='white',
                lineWidth=3,
                fillColor='darkgray',
                pos=(-box_spacing, box_y)
            )
            
            sound_box_mid = visual.Rect(
                win=win,
                width=int(250 * scale_x),
                height=int(150 * scale_avg),
                lineColor='white',
                lineWidth=3,
                fillColor='darkgray',
                pos=(0, box_y)
            )
            
            sound_box_high = visual.Rect(
                win=win,
                width=int(250 * scale_x),
                height=int(150 * scale_avg),
                lineColor='white',
                lineWidth=3,
                fillColor='darkgray',
                pos=(box_spacing, box_y)
            )
            
            # Create selection borders (green, initially invisible)
            selection_border_low = visual.Rect(
                win=win,
                width=int(260 * scale_x),
                height=int(160 * scale_avg),
                lineColor='green',
                lineWidth=8,
                fillColor=None,
                pos=(-box_spacing, box_y)
            )
            
            selection_border_mid = visual.Rect(
                win=win,
                width=int(260 * scale_x),
                height=int(160 * scale_avg),
                lineColor='green',
                lineWidth=8,
                fillColor=None,
                pos=(0, box_y)
            )
            
            selection_border_high = visual.Rect(
                win=win,
                width=int(260 * scale_x),
                height=int(160 * scale_avg),
                lineColor='green',
                lineWidth=8,
                fillColor=None,
                pos=(box_spacing, box_y)
            )
            
            # Create labels for each sound
            label_low = visual.TextStim(
                win=win,
                text='LOW\n250 Hz\n\nPress A',
                color='white',
                height=int(28 * scale_avg),
                pos=(-box_spacing, box_y),
                bold=True
            )
            
            label_mid = visual.TextStim(
                win=win,
                text='MID\n1000 Hz\n\nPress G',
                color='white',
                height=int(28 * scale_avg),
                pos=(0, box_y),
                bold=True
            )
            
            label_high = visual.TextStim(
                win=win,
                text='HIGH\n2000 Hz\n\nPress K',
                color='white',
                height=int(28 * scale_avg),
                pos=(box_spacing, box_y),
                bold=True
            )
            
            # Create colored control instructions - moved down
            instruction_bottom = visual.TextStim(
                win=win,
                text='CLICK a sound box to select',
                color='yellow',
                height=int(32 * scale_avg),
                pos=(int(0 * scale_x), int(-460 * scale_y)),  # Moved down from -380
                bold=True
            )
            
            # Volume display
            volume_display = visual.TextStim(
                win=win,
                text='',
                color='cyan',
                height=int(28 * scale_avg),
                pos=(int(0 * scale_x), int(-530 * scale_y)),
                bold=True
            )
            
            # Dynamic continue instruction (only shows after selection)
            continue_instr_audio = visual.TextStim(
                win=win,
                text='Press SPACE to continue',
                color='green',
                height=int(36 * scale_avg),
                pos=(int(-350 * scale_x), int(-700 * scale_y)),  # Moved down and to the left
                bold=True,
                wrapWidth=int(600 * scale_x)  # Added wrap width to prevent wrapping
            )
            
            quit_instr_audio = visual.TextStim(
                win=win,
                text='Press ESC to quit',
                color='red',
                height=int(32 * scale_avg),
                pos=(int(350 * scale_x), int(-700 * scale_y)),  # Moved to the right
                bold=True
            )
            
            # Create mouse for selection
            audio_mouse = event.Mouse(visible=True, win=win)
            
            # Track selection state and volume
            selected_sound_redo = None  # 'low', 'mid', or 'high'
            selected_frequency_redo = None
            current_volume = 0.7  # Start at 70% volume
            
            print("Waiting for audio verification and sound selection...")
            audio_verified = False
            
            # Update tone volumes
            tone_low.setVolume(current_volume)
            tone_mid.setVolume(current_volume)
            tone_high.setVolume(current_volume)
            
            while not audio_verified:
                # Check keyboard for sound playback and volume control
                keys_audio = event.getKeys(['a', 'g', 'k', 'space', 'escape', 'up', 'down'])
                if 'a' in keys_audio:
                    tone_low.play()
                    print(f"Playing LOW frequency (250 Hz) at {int(current_volume * 100)}% volume")
                    core.wait(0.1)
                elif 'g' in keys_audio:
                    tone_mid.play()
                    print(f"Playing MID frequency (1000 Hz) at {int(current_volume * 100)}% volume")
                    core.wait(0.1)
                elif 'k' in keys_audio:
                    tone_high.play()
                    print(f"Playing HIGH frequency (2000 Hz) at {int(current_volume * 100)}% volume")
                    core.wait(0.1)
                elif 'up' in keys_audio:
                    # Increase volume
                    current_volume = min(1.0, current_volume + 0.1)
                    tone_low.setVolume(current_volume)
                    tone_mid.setVolume(current_volume)
                    tone_high.setVolume(current_volume)
                    print(f"Volume increased to {int(current_volume * 100)}%")
                    core.wait(0.1)
                elif 'down' in keys_audio:
                    # Decrease volume
                    current_volume = max(0.1, current_volume - 0.1)
                    tone_low.setVolume(current_volume)
                    tone_mid.setVolume(current_volume)
                    tone_high.setVolume(current_volume)
                    print(f"Volume decreased to {int(current_volume * 100)}%")
                    core.wait(0.1)
                elif 'space' in keys_audio:
                    if selected_sound_redo is not None:
                        audio_verified = True
                        print(f"Audio verified - user selected {selected_sound_redo.upper()} frequency ({selected_frequency_redo} Hz) at {int(current_volume * 100)}% volume")
                    else:
                        print("Cannot continue - no sound selected. Please click a sound box first.")
                elif 'escape' in keys_audio:
                    win.close()
                    core.quit()
                
                # Check mouse clicks for sound box selection and instructions
                if audio_mouse.getPressed()[0]:  # Left click
                    mouse_pos = audio_mouse.getPos()
                    
                    # Check if clicked on SPACE or ESC instruction text
                    if selected_sound_redo is not None:  # Only check SPACE if sound is selected
                        if is_text_clicked(continue_instr_audio, audio_mouse):
                            audio_verified = True
                            print(f"User clicked CONTINUE - Audio verified with {selected_sound_redo.upper()} frequency")
                            core.wait(0.3)
                            continue  # Skip rest of mouse checking
                    
                    if is_text_clicked(quit_instr_audio, audio_mouse):
                        print("User clicked QUIT")
                        win.close()
                        core.quit()
                    
                    # Check if clicked on volume control buttons - PROPERLY SCALED
                    volume_up_x = int(-350 * scale_x)
                    volume_up_y = int(-530 * scale_y)
                    volume_btn_half_width = int(90 * scale_x)  # Half of 180
                    volume_btn_half_height = int(40 * scale_avg)  # Half of 80
                    
                    if (abs(mouse_pos[0] - volume_up_x) < volume_btn_half_width and 
                        abs(mouse_pos[1] - volume_up_y) < volume_btn_half_height):
                        # Volume UP button clicked
                        current_volume = min(1.0, current_volume + 0.1)
                        tone_low.setVolume(current_volume)
                        tone_mid.setVolume(current_volume)
                        tone_high.setVolume(current_volume)
                        print(f"User clicked VOLUME UP - Volume increased to {int(current_volume * 100)}%")
                        core.wait(0.3)  # Debounce
                        continue
                    
                    volume_down_x = int(350 * scale_x)
                    volume_down_y = int(-530 * scale_y)
                    
                    if (abs(mouse_pos[0] - volume_down_x) < volume_btn_half_width and 
                        abs(mouse_pos[1] - volume_down_y) < volume_btn_half_height):
                        # Volume DOWN button clicked
                        current_volume = max(0.1, current_volume - 0.1)
                        tone_low.setVolume(current_volume)
                        tone_mid.setVolume(current_volume)
                        tone_high.setVolume(current_volume)
                        print(f"User clicked VOLUME DOWN - Volume decreased to {int(current_volume * 100)}%")
                        core.wait(0.3)  # Debounce
                        continue
                    
                    # Check if clicked on low sound box
                    if (abs(mouse_pos[0] - (-box_spacing)) < (125 * scale_x) and 
                        abs(mouse_pos[1] - box_y) < 75):
                        selected_sound_redo = 'low'
                        selected_frequency_redo = 250
                        print(f"Selected: LOW frequency (250 Hz)")
                        core.wait(0.3)  # Debounce
                        
                    # Check if clicked on mid sound box
                    elif (abs(mouse_pos[0] - 0) < (125 * scale_x) and 
                          abs(mouse_pos[1] - box_y) < 75):
                        selected_sound_redo = 'mid'
                        selected_frequency_redo = 1000
                        print(f"Selected: MID frequency (1000 Hz)")
                        core.wait(0.3)  # Debounce
                        
                    # Check if clicked on high sound box
                    elif (abs(mouse_pos[0] - box_spacing) < (125 * scale_x) and 
                          abs(mouse_pos[1] - box_y) < 75):
                        selected_sound_redo = 'high'
                        selected_frequency_redo = 2000
                        print(f"Selected: HIGH frequency (2000 Hz)")
                        core.wait(0.3)  # Debounce
                
                # Update volume display text
                volume_display.text = f"Current Volume: {int(current_volume * 100)}%"
                
                # Draw everything
                audio_verify_instruction.draw()
                key_instruction.draw()
                volume_instruction.draw()
                
                # Draw volume control buttons
                volume_up_btn.draw()
                volume_up_text.draw()
                volume_down_btn.draw()
                volume_down_text.draw()
                
                selection_instruction.draw()
                
                # Draw sound boxes
                sound_box_low.draw()
                sound_box_mid.draw()
                sound_box_high.draw()
                
                # Draw selection borders only for selected sound
                if selected_sound_redo == 'low':
                    selection_border_low.draw()
                elif selected_sound_redo == 'mid':
                    selection_border_mid.draw()
                elif selected_sound_redo == 'high':
                    selection_border_high.draw()
                
                # Draw labels
                label_low.draw()
                label_mid.draw()
                label_high.draw()
                
                volume_display.draw()
                instruction_bottom.draw()
                
                # Only show continue prompt if a sound has been selected
                if selected_sound_redo is not None:
                    continue_instr_audio.draw()
                
                quit_instr_audio.draw()
                copyright_text_small.draw()
                draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                win.flip()
                
                core.wait(0.01)
            
            # Update the beep sound for audio reaction test with selected frequency
            print(f"\nUpdating audio reaction test to use {selected_frequency_redo} Hz...")
            beep = sound.Sound(value=selected_frequency_redo, secs=1.0, hamming=True)
            beep_continuous = sound.Sound(value=selected_frequency_redo, secs=2.0, hamming=True, loops=-1)
            selected_frequency = selected_frequency_redo
            selected_sound = selected_sound_redo
            
            # Show confirmation
            confirm_text = visual.TextStim(
                win=win,
                text=(
                    "AUDIO SOUND SELECTED\n\n"
                    f"Selected frequency: {selected_frequency_redo} Hz ({selected_sound_redo.upper()})\n\n"
                    "This sound will be used for the audio reaction test.\n\n"
                    "Returning to reminders..."
                ),
                color='green',
                height=int(36 * scale_avg),
                wrapWidth=int(5070 * scale_x),
                pos=(int(0 * scale_x), int(0 * scale_y))
            )
            confirm_text.draw()
            copyright_text_small.draw()
            win.flip()
            core.wait(2.0)
            
        elif 'f' in keys:
            waiting_reminder = False
            reminders_complete = False
            
            # Check if framerate test is enabled
            if not RUN_FRAMERATE_TEST:
                print("Cannot redo framerate test - RUN_FRAMERATE_TEST is disabled")
                error_msg = visual.TextStim(
                    win=win,
                    text=(
                        "FRAMERATE REDO NOT AVAILABLE\n\n"
                        "RUN_FRAMERATE_TEST is set to False.\n\n"
                        "Cannot redo a test that was skipped.\n\n"
                        "Returning to reminders..."
                    ),
                    color='red',
                    height=int(40 * scale_avg),
                    pos=(int(0 * scale_x), int(0 * scale_y))
                )
                error_msg.draw()
                copyright_text_small.draw()
                win.flip()
                core.wait(2.0)
                continue  # Return to reminders loop
            
            print("User chose to redo framerate test...")
            
            # Show redoing message
            show_simple_message(win, "REDOING FRAMERATE TEST", "Starting now...", 'cyan', scale_x, scale_y, scale_avg, wait_time=1.5, show_copyright=True, copyright_text_small=copyright_text_small)
            # ===== FULL FRAMERATE TEST =====
            print(f"Starting {int(FRAMERATE_TEST_DURATION)}-second framerate stability test...")

            test_text = visual.TextStim(
                win=win,
                text='',
                color='white',
                height=int(24 * scale_avg),  # Slightly smaller to fit on one line
                pos=(int(0 * scale_x), int(0 * scale_y)),
                wrapWidth=int(7000 * scale_x)  # Much wider to prevent title wrapping
            )

            # Run test for configured duration
            test_duration = FRAMERATE_TEST_DURATION

            # ADAPTIVE WARMUP - Calculate based on measured FPS
            warmup_duration = FRAMERATE_WARMUP_BASE + (expected_fps / FRAMERATE_WARMUP_FPS_BASELINE) * FRAMERATE_WARMUP_FPS_FACTOR
            
            print(f"Adaptive warmup duration: {warmup_duration:.1f} seconds")

            # WARMUP PHASE - Let system stabilize before recording
            print(f"Warming up ({warmup_duration:.1f} seconds)...")
            warmup_start = core.getTime()
            warmup_text = visual.TextStim(
            win=win,
            text=f"Warming up display system...\n\n{warmup_duration:.0f} seconds\n\nPlease wait...",
            color='white',
            height=int(25 * scale_avg)
            )

            while core.getTime() - warmup_start < warmup_duration:
                warmup_text.draw()
                copyright_text_small.draw()
                win.flip()

            # Clear screen and pause briefly
            copyright_text_small.draw()
            win.flip()
            core.wait(0.5)

            print(f"Starting {test_duration} second framerate stability test...")

            # Create STATIC text (no updates during measurement)
            test_text.text = (
                f"=== FRAMERATE STABILITY TEST (REDO) ===\n\n"
                f"Measuring for {int(test_duration)} seconds...\n\n"
                f"Expected FPS: {expected_fps}\n\n"
                f"Please wait..."
            )

            # NOW start the actual test
            test_start = core.getTime()
            frame_times_redo = []

            # ULTRA-MINIMAL MEASUREMENT LOOP (no dropped frame checking during test)
            while core.getTime() - test_start < test_duration:
                # Draw STATIC text
                test_text.draw()
                copyright_text_small.draw()
                
                # Flip and record time AFTER flip
                win.flip()
                frame_times_redo.append(core.getTime())

            # Calculate dropped frames AFTER test completes
            dropped_frames_redo = 0
            for i in range(1, len(frame_times_redo)):
                frame_duration = frame_times_redo[i] - frame_times_redo[i-1]
                if frame_duration > (refresh_rate * 1.5):
                    dropped_frames_redo += 1
            
            print(f"Dropped frames calculated (redo): {dropped_frames_redo} of {len(frame_times_redo)}")

            # Clear screen after test completes
            copyright_text_small.draw()
            win.flip()
            core.wait(0.3)

            # VALIDATE FRAME COLLECTION (FPS and Duration Based)
            expected_frames_redo = int(expected_fps * test_duration)
            minimum_acceptable_frames_redo = int(expected_frames_redo * 0.5)
            
            print(f"\nFrame Collection Validation (Redo):")
            print(f"  Expected frames: {expected_frames_redo}")
            print(f"  Collected frames: {len(frame_times_redo)}")
            print(f"  Minimum acceptable: {minimum_acceptable_frames_redo}")
            
            if len(frame_times_redo) < minimum_acceptable_frames_redo:
                print(f"  ⚠️ WARNING: Only collected {len(frame_times_redo)/expected_frames_redo*100:.1f}% of expected frames!")
            elif len(frame_times_redo) < expected_frames_redo * 0.9:
                print(f"  ⚠️ NOTICE: Collected {len(frame_times_redo)/expected_frames_redo*100:.1f}% of expected frames")
            else:
                print(f"  ✓ Frame collection OK: {len(frame_times_redo)/expected_frames_redo*100:.1f}% of expected")

            # DISCARD INITIAL FRAMES (based on FPS and duration)
            settling_time_seconds_redo = test_duration * (FRAMERATE_DISCARD_TIME_PERCENTAGE / 100)
            discard_count_redo = int(expected_fps * settling_time_seconds_redo)
            discard_count_redo = max(5, discard_count_redo)
            
            print(f"Discarding settling period: {settling_time_seconds_redo:.3f}s = {discard_count_redo} frames")
            settled_frame_times_redo = frame_times_redo[discard_count_redo:]

            # Calculate final statistics from settled frames
            avg_fps_redo = len(settled_frame_times_redo) / (settled_frame_times_redo[-1] - settled_frame_times_redo[0]) if len(settled_frame_times_redo) > 1 else 0
            frame_intervals_redo = [settled_frame_times_redo[i] - settled_frame_times_redo[i-1] for i in range(1, len(settled_frame_times_redo))]
            avg_interval_redo = sum(frame_intervals_redo) / len(frame_intervals_redo) * 1000 if frame_intervals_redo else 0
            
            # Recalculate dropped frames for settled period
            settled_dropped_redo = 0
            for i in range(1, len(settled_frame_times_redo)):
                frame_duration = settled_frame_times_redo[i] - settled_frame_times_redo[i-1]
                if frame_duration > (refresh_rate * 1.5):
                    settled_dropped_redo += 1
            
            stability_redo = (1 - (settled_dropped_redo / len(settled_frame_times_redo))) * 100 if len(settled_frame_times_redo) > 0 else 0

            # Calculate comprehensive metrics from settled frames
            stability_metrics_redo = calculate_framerate_metrics(settled_frame_times_redo, expected_fps)

            print(f"\nFramerate test (redo) complete:")
            print(f"Average FPS: {avg_fps_redo:.2f}")
            print(f"Average frame interval: {avg_interval_redo:.2f} ms")
            print(f"Dropped frames: {dropped_frames_redo}")
            print(f"Stability: {stability_redo:.2f}%")
            
            # Update main framerate variables with redo results
            frame_times = frame_times_redo
            stability_test_frames = len(frame_times_redo)
            stability_test_dropped = dropped_frames_redo
            avg_fps = avg_fps_redo
            stability = stability_redo
            stability_metrics = stability_metrics_redo
            
            # Add to attempts list - mark as REDO
            framerate_attempt_number += 1
            framerate_attempt_data = {
                'attempt_number': f"{framerate_attempt_number} (REDO)",
                'frames': stability_test_frames,
                'dropped': stability_test_dropped,
                'stability': stability,
                'avg_fps': avg_fps,
                'metrics': stability_metrics
            }
            all_framerate_attempts.append(framerate_attempt_data)
            
            # Show results
            performance_rating = "EXCELLENT"
            performance_color = "green"
            recommendations = []

            if stability < 96.5:
                performance_rating = "POOR"
                performance_color = "red"
                recommendations.append("- High frame drop rate detected")
            elif stability < 98.0:
                performance_rating = "FAIR"
                performance_color = "yellow"
                recommendations.append("- Moderate frame drops detected")
            elif stability < 99.0:
                performance_rating = "GOOD"
                performance_color = "lightgreen"

            rec_text = "\n".join(recommendations) if recommendations else "System performance is stable for testing."
            
            # Check if forced redo needed (same logic as main section)
            framerate_needs_redo_reminders = (performance_rating == "POOR")
            
            if framerate_needs_redo_reminders:
                # POOR - must redo, cannot return to reminders yet
                rec_text += (
                    "\n\nIF YOU REPEATEDLY GET THIS SCREEN:\n"
                    "1. Press ESC to exit the program\n"
                    "2. Restart and complete the Performance Checklist\n"
                    "3. Close all background applications\n"
                    "4. Try the test again\n"
                    "5. If still failing, contact your researcher for assistance"
                )
                
                result_text = visual.TextStim(
                    win=win,
                    text=(
                        f"=== FRAMERATE STABILITY TEST (REDO) ===\n\n"
                        f"PERFORMANCE RATING: {performance_rating}\n\n"
                        f"Average FPS: {avg_fps:.2f}\n"
                        f"Stability: {stability:.2f}%\n"
                        f"Dropped frames: {dropped_frames_redo}\n\n"
                        f"{rec_text}"
                    ),
                    color='red',
                    height=int(28 * scale_avg),
                    wrapWidth=int(5070 * scale_x),
                    pos=(int(0 * scale_x), int(100 * scale_y))
                )
                
                redo_instr_fr = visual.TextStim(
                    win=win,
                    text='MUST REDO - Press F',
                    color='red',
                    height=int(40 * scale_avg),
                    pos=(int(-250 * scale_x), int(-600 * scale_y)),
                    bold=True
                )
                
                quit_instr_fr = visual.TextStim(
                    win=win,
                    text='Press ESC to exit',
                    color='red',
                    height=int(40 * scale_avg),
                    pos=(int(250 * scale_x), int(-600 * scale_y)),
                    bold=True
                )
                
                result_text.draw()
                redo_instr_fr.draw()
                quit_instr_fr.draw()
                copyright_text_small.draw()
                draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                win.flip()
                
                print("FORCED REDO: Framerate POOR - returning to reminders to retry")
                
                # Wait for F or ESC
                event.clearEvents()
                global_mouse.setVisible(True)
                waiting_fr = True
                last_click_fr = 0
                while waiting_fr:
                    current_time_fr = core.getTime()
                    keys_fr = event.getKeys(['f', 'escape'])
                    
                    if 'f' in keys_fr:
                        print("User pressed F - will return to reminders and press F again")
                        waiting_fr = False
                    elif 'escape' in keys_fr:
                        print("User pressed ESC - exiting program")
                        win.close()
                        sys.exit(0)
                    
                    # Check mouse clicks
                    if current_time_fr - last_click_fr > 0.3:
                        if is_text_clicked(redo_instr_fr, global_mouse):
                            print("Clicked REDO - returning to reminders")
                            waiting_fr = False
                            last_click_fr = current_time_fr
                        elif is_text_clicked(quit_instr_fr, global_mouse):
                            print("Clicked EXIT")
                            win.close()
                            sys.exit(0)
                    
                    core.wait(0.01)
                
                # Return to reminders loop (user will see reminders and can press F again to retry)
                continue
                
            else:
                # FAIR or better - show results and return to reminders
                result_text = visual.TextStim(
                    win=win,
                    text=(
                        f"=== FRAMERATE STABILITY TEST (REDO) ===\n\n"
                        f"PERFORMANCE RATING: {performance_rating}\n\n"
                        f"Average FPS: {avg_fps:.2f}\n"
                        f"Stability: {stability:.2f}%\n"
                        f"Dropped frames: {dropped_frames_redo}\n\n"
                        f"{rec_text}\n\n"
                        f"Press K to return to reminders"
                    ),
                    color=performance_color,
                    height=int(32 * scale_avg),
                    wrapWidth=int(5070 * scale_x),
                    pos=(int(0 * scale_x), int(50 * scale_y))
                )
                
                continue_k = visual.TextStim(
                    win=win,
                    text='Press K to return',
                    color='green',
                    height=int(36 * scale_avg),
                    pos=(int(0 * scale_x), int(-500 * scale_y)),
                    bold=True
                )
                
                result_text.draw()
                continue_k.draw()
                copyright_text_small.draw()
                draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                win.flip()
                
                # Wait for K to return
                event.clearEvents()
                core.wait(0.5)
                event.getKeys()
                
                waiting_return = True
                while waiting_return:
                    keys_return = event.getKeys(['k', 'escape'])
                    if 'k' in keys_return or is_text_clicked(continue_k, global_mouse):
                        print("Returning to reminders...")
                        waiting_return = False
                    elif 'escape' in keys_return:
                        win.close()
                        sys.exit(0)
                    core.wait(0.01)
            
            # Continue to next iteration of reminders loop
            
        elif 'r' in keys:
            waiting_reminder = False
            reminders_complete = False
            
            # Check if keyboard test is enabled
            if not RUN_KEYBOARD_TEST:
                print("Cannot redo keyboard test - RUN_KEYBOARD_TEST is disabled")
                error_msg = visual.TextStim(
                    win=win,
                    text=(
                        "KEYBOARD REDO NOT AVAILABLE\n\n"
                        "RUN_KEYBOARD_TEST is set to False.\n\n"
                        "Cannot redo a test that was skipped.\n\n"
                        "Returning to reminders..."
                    ),
                    color='red',
                    height=int(40 * scale_avg),
                    pos=(int(0 * scale_x), int(0 * scale_y))
                )
                error_msg.draw()
                copyright_text_small.draw()
                win.flip()
                core.wait(2.0)
                continue  # Return to reminders loop
            
            print("User chose to redo keyboard test...")
            
            # Show redoing message
            show_simple_message(win, "REDOING KEYBOARD TEST", "Starting now...", 'cyan', scale_x, scale_y, scale_avg, wait_time=1.5, show_copyright=True, copyright_text_small=copyright_text_small)
            # ===== FULL KEYBOARD TEST =====
            # Clear screen and wait
            copyright_text_small.draw()
            win.flip()
            event.clearEvents()
            core.wait(1.0)
            event.clearEvents()

            # Instructions for keyboard hardware test
            keyboard_instruction = visual.TextStim(
                win=win,
                text=(
                    "=== KEYBOARD HARDWARE TEST (REDO) ===\n\n"
                    "This test measures your keyboard's hardware quality.\n\n"
                    "You will TAP the SPACE BAR as FAST as you can.\n\n"
                    "This is NOT a reaction test - it measures:\n"
                    "- Keyboard polling rate (how often it checks for input)\n"
                    "- Input consistency (USB/wireless reliability)\n\n"
                    f"Test duration: {format_time_estimate(KEYBOARD_TAPPING_DURATION)}\n"
                    f"Minimum taps required: {KEYBOARD_MIN_TAPS} taps\n"
                    f"(That's {KEYBOARD_MIN_TAPS / KEYBOARD_TAPPING_DURATION:.1f} taps per second)\n\n"
                    "IMPORTANT Instructions:\n"
                    "1. Use ONLY ONE FINGER from ONE HAND\n"
                    "2. Press SPACE to begin\n"
                    "3. Tap SPACE as rapidly as possible\n"
                    "4. Continue tapping until test completes\n\n"
                    "Using multiple fingers or alternating hands will\n"
                    "cause variation and skew the hardware measurement.\n\n"
                    "This will NOT affect your actual reaction test results."
                ),
                color='white',
                height=int(32 * scale_avg),
                wrapWidth=int(6500 * scale_x),
                pos=(int(0 * scale_x), int(-80 * scale_y))
            )
        
            continue_instr_kb = visual.TextStim(
                win=win,
                text='Press SPACE to begin',
                color='green',
                height=int(32 * scale_avg),
                pos=(int(-350 * scale_x), int(-700 * scale_y)),
                bold=True
            )
        
            quit_instr_kb = visual.TextStim(
                win=win,
                text='Press ESC to quit',
                color='red',
                height=int(32 * scale_avg),
                pos=(int(350 * scale_x), int(-700 * scale_y)),
                bold=True
            )
        
            keyboard_instruction.draw()
            continue_instr_kb.draw()
            quit_instr_kb.draw()
            copyright_text_small.draw()
            draw_progress_bar(win, test_sections, current_section, copyright_text_small)
            win.flip()

            print("Waiting for SPACE to start keyboard hardware test (redo)...")
            global_mouse.setVisible(True)  # Show mouse for clicking
            waiting_kb = True
            last_click_time = 0
            while waiting_kb:
                keys_kb = event.getKeys(['space', 'escape'])
                current_time = core.getTime()
                
                if 'space' in keys_kb:
                    waiting_kb = False
                elif 'escape' in keys_kb:
                    win.close()
                    core.quit()
                
                # Check for mouse clicks on instruction text
                if current_time - last_click_time > 0.3:
                    if is_text_clicked(continue_instr_kb, global_mouse):
                        print("User clicked BEGIN")
                        waiting_kb = False
                        last_click_time = current_time
                        core.wait(0.2)
                    elif is_text_clicked(quit_instr_kb, global_mouse):
                        print("User clicked QUIT")
                        win.close()
                        core.quit()
                
                core.wait(0.01)

            event.clearEvents()
            core.wait(0.5)

            # Keyboard test execution (simplified - one attempt only for redo)
            gap_threshold_redo = KEYBOARD_TAPPING_DURATION * 0.20
            test_successful_redo = False
            attempt_number_redo = 0
            all_attempts_redo = []
        
            while not test_successful_redo:
                attempt_number_redo += 1
                print(f"\n--- KEYBOARD TEST (REDO) ATTEMPT #{attempt_number_redo} ---")
                
                countdown_instruction = visual.TextStim(
                    win=win,
                    text='GET READY TO TAP SPACE AS FAST AS YOU CAN!',
                    color='yellow',
                    height=int(48 * scale_avg),
                    pos=(int(0 * scale_x), int(150 * scale_y)),
                    bold=True
                )
            
                countdown_text_kb = visual.TextStim(
                    win=win,
                    text='',
                    color='yellow',
                    height=int(100 * scale_avg),
                    pos=(int(0 * scale_x), int(-50 * scale_y)),
                    bold=True
                )
            
                for count in [3, 2, 1]:
                    countdown_instruction.draw()
                    countdown_text_kb.text = f"{count}"
                    countdown_text_kb.draw()
                    copyright_text_small.draw()
                    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                    win.flip()
                    core.wait(1.0)
            
                go_text = visual.TextStim(
                    win=win,
                    text='START TAPPING NOW!',
                    color='green',
                    height=int(120 * scale_avg),
                    pos=(int(0 * scale_x), int(50 * scale_y)),
                    bold=True
                )
            
                go_disclaimer = visual.TextStim(
                    win=win,
                    text='(press space to start)',
                    color='yellow',
                    height=int(40 * scale_avg),
                    pos=(int(0 * scale_x), int(-200 * scale_y)),
                    bold=True
                )
            
                go_text.draw()
                go_disclaimer.draw()
                copyright_text_small.draw()
                draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                win.flip()
            
                print("Waiting for user to press SPACE to begin tapping test...")
                event.clearEvents()
                waiting_for_start = True
                while waiting_for_start:
                    keys_start = event.getKeys(['space', 'escape'])
                    current_time = core.getTime()
                    
                    if 'space' in keys_start:
                        waiting_for_start = False
                        print("First space press detected - starting test NOW!")
                    elif 'escape' in keys_start:
                        win.close()
                        core.quit()
                    core.wait(0.01)
            
                test_start = core.getTime()
                tap_events_redo = [test_start]
            
                print(f"Running rapid tapping test ({int(KEYBOARD_TAPPING_DURATION)} seconds)...")

                keyboard_progress_text = visual.TextStim(
                    win=win,
                    text='',
                    color='white',
                    height=int(32 * scale_avg),
                    pos=(int(0 * scale_x), int(0 * scale_y))
                )

                while core.getTime() - test_start < KEYBOARD_TAPPING_DURATION:
                    current_time = core.getTime()
                    time_remaining = KEYBOARD_TAPPING_DURATION - (current_time - test_start)
            
                    keys_tap = event.getKeys(timeStamped=True)
                    for key, timestamp in keys_tap:
                        if key == 'space':
                            tap_events_redo.append(timestamp)
                        elif key == 'escape':
                            win.close()
                            core.quit()
            
                    keyboard_progress_text.text = (
                        f"KEYBOARD HARDWARE TEST (REDO)\n\n"
                        f"TAP SPACE AS FAST AS YOU CAN!\n\n"
                        f"Time remaining: {time_remaining:.1f}s\n"
                        f"Taps detected: {len(tap_events_redo)}"
                    )
                    keyboard_progress_text.draw()
                    copyright_text_small.draw()
                    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                    win.flip()

                print(f"\nRapid tapping test complete: {len(tap_events_redo)} taps recorded")
            
                # Calculate intervals
                tap_intervals_raw_redo = []
                max_interval_redo = 0
                max_interval_position_redo = 0
            
                if len(tap_events_redo) >= 2:
                    for i in range(1, len(tap_events_redo)):
                        interval = (tap_events_redo[i] - tap_events_redo[i-1])
                        tap_intervals_raw_redo.append(interval)
                        if interval > max_interval_redo:
                            max_interval_redo = interval
                            max_interval_position_redo = i
            
                print(f"Maximum interval between taps: {max_interval_redo:.2f} seconds")
                print(f"Gap threshold: {gap_threshold_redo:.2f} seconds")
            
                # Check validation
                if len(tap_events_redo) < 2:
                    print(f"✗ Insufficient taps for validation ({len(tap_events_redo)} taps)")
                    retry_warning = visual.TextStim(
                        win=win,
                        text=(
                            "KEYBOARD TEST - RESTART REQUIRED\n\n"
                            f"Insufficient clicks ({len(tap_events_redo)} out of {KEYBOARD_MIN_TAPS} needed)\n\n"
                            ""
                        ),
                        color='red',
                        height=int(40 * scale_avg),
                        wrapWidth=int(6000 * scale_x),
                        pos=(int(0 * scale_x), int(0 * scale_y))
                    )
                    retry_instr = visual.TextStim(
                        win=win,
                        text='Press K to retry',
                        color='red',
                        height=int(56 * scale_avg),
                        pos=(int(0 * scale_x), int(-300 * scale_y)),
                        bold=True,
                        wrapWidth=int(800 * scale_x)
                    )
                    retry_warning.draw()
                    retry_instr.draw()
                    copyright_text_small.draw()
                    win.flip()
                    event.clearEvents()
                    global_mouse.setVisible(True)  # Ensure mouse visible for clicking retry
                    waiting_retry = True
                    last_click_time = 0
                    while waiting_retry:
                        keys_retry = event.getKeys(['k', 'escape'])
                        current_time = core.getTime()
                        
                        if 'k' in keys_retry:
                            waiting_retry = False
                        elif 'escape' in keys_retry:
                            win.close()
                            core.quit()
                        
                        # Check for mouse clicks on retry instruction
                        if current_time - last_click_time > 0.3:
                            if is_text_clicked(retry_instr, global_mouse):
                                print("User clicked RETRY button")
                                waiting_retry = False
                                last_click_time = current_time
                                core.wait(0.2)
                        
                        core.wait(0.01)
                    copyright_text_small.draw()
                    win.flip()
                    event.clearEvents()
                    core.wait(0.5)
                elif max_interval_redo > gap_threshold_redo:
                    print(f"✗ Gap too large: {max_interval_redo:.2f}s > {gap_threshold_redo:.2f}s")
                    retry_warning = visual.TextStim(
                        win=win,
                        text=(
                            "KEYBOARD TEST - RESTART REQUIRED\n\n"
                            f"Too long between clicks ({max_interval_redo:.2f}s, max: {gap_threshold_redo:.2f}s)\n\n"
                            ""
                        ),
                        color='red',
                        height=int(40 * scale_avg),
                        wrapWidth=int(6000 * scale_x),
                        pos=(int(0 * scale_x), int(0 * scale_y))
                    )
                    retry_instr = visual.TextStim(
                        win=win,
                        text='Press K to retry',
                        color='red',
                        height=int(56 * scale_avg),
                        pos=(int(0 * scale_x), int(-300 * scale_y)),
                        bold=True,
                        wrapWidth=int(800 * scale_x)
                    )
                    retry_warning.draw()
                    retry_instr.draw()
                    copyright_text_small.draw()
                    win.flip()
                    event.clearEvents()
                    global_mouse.setVisible(True)  # Ensure mouse visible for clicking retry
                    waiting_retry = True
                    last_click_time = 0
                    while waiting_retry:
                        keys_retry = event.getKeys(['k', 'escape'])
                        current_time = core.getTime()
                        
                        if 'k' in keys_retry:
                            waiting_retry = False
                        elif 'escape' in keys_retry:
                            win.close()
                            core.quit()
                        
                        # Check for mouse clicks on retry instruction
                        if current_time - last_click_time > 0.3:
                            if is_text_clicked(retry_instr, global_mouse):
                                print("User clicked RETRY button")
                                waiting_retry = False
                                last_click_time = current_time
                                core.wait(0.2)
                        
                        core.wait(0.01)
                    copyright_text_small.draw()
                    win.flip()
                    event.clearEvents()
                    core.wait(0.5)
                else:
                    test_successful_redo = True
                    print("✓ All tap intervals within acceptable range")
        
            # Test completed successfully - calculate metrics
            print(f"\n✓ Keyboard test (redo) completed successfully")

            if len(tap_events_redo) >= 2:
                tap_intervals_redo = [(tap_events_redo[i] - tap_events_redo[i-1]) * 1000 
                                     for i in range(1, len(tap_events_redo))]
        
                avg_tap_interval_redo = statistics.mean(tap_intervals_redo)
                tap_interval_std_redo = statistics.stdev(tap_intervals_redo) if len(tap_intervals_redo) > 1 else 0
                min_tap_interval_redo = min(tap_intervals_redo)
                max_tap_interval_redo = max(tap_intervals_redo)
        
                avg_tap_rate_redo = 1000.0 / avg_tap_interval_redo if avg_tap_interval_redo > 0 else 0
                max_tap_rate_redo = 1000.0 / min_tap_interval_redo if min_tap_interval_redo > 0 else 0
                tap_cv_redo = (tap_interval_std_redo / avg_tap_interval_redo) * 100 if avg_tap_interval_redo > 0 else 0
        
                if min_tap_interval_redo <= 10.0:
                    estimated_polling_redo = "1000Hz (1ms) - High-end gaming keyboard"
                elif min_tap_interval_redo <= 20.0:
                    estimated_polling_redo = "500Hz (2ms) - Gaming keyboard"
                elif min_tap_interval_redo <= 40.0:
                    estimated_polling_redo = "250Hz (4ms) - Standard keyboard"
                elif min_tap_interval_redo <= 80.0:
                    estimated_polling_redo = "125Hz (8ms) - Basic keyboard"
                else:
                    estimated_polling_redo = "Low polling rate - May be wireless or basic USB"
        
                print(f"Average tap rate: {avg_tap_rate_redo:.1f} taps/sec")
                print(f"Consistency (CV): {tap_cv_redo:.2f}%")
                
                # Calculate keyboard rating (same logic as original test)
                keyboard_rating_redo = "EXCELLENT"
                keyboard_color_redo = "green"

                if len(tap_events_redo) < KEYBOARD_MIN_TAPS:
                    keyboard_rating_redo = "FAILED"
                    keyboard_color_redo = "red"
                elif tap_cv_redo > 40:
                    keyboard_rating_redo = "POOR"
                    keyboard_color_redo = "red"
                elif tap_cv_redo > 25:
                    keyboard_rating_redo = "FAIR"
                    keyboard_color_redo = "yellow"
                elif tap_cv_redo > 15:
                    keyboard_rating_redo = "GOOD"
                    keyboard_color_redo = "lightgreen"
                
                print(f"Keyboard rating: {keyboard_rating_redo}")
                
                # Update main keyboard variables
                tap_events = tap_events_redo
                tap_intervals = tap_intervals_redo
                avg_tap_interval = avg_tap_interval_redo
                tap_interval_std = tap_interval_std_redo
                min_tap_interval = min_tap_interval_redo
                max_tap_interval = max_tap_interval_redo
                avg_tap_rate = avg_tap_rate_redo
                max_tap_rate = max_tap_rate_redo
                tap_cv = tap_cv_redo
                estimated_polling = estimated_polling_redo
                keyboard_rating = keyboard_rating_redo
                
                # Update keyboard session tracking - mark as REDO in session number
                keyboard_session_number += 1
                keyboard_session_data = {
                    'session_number': f"{keyboard_session_number} (REDO)",
                    'all_attempts': [],
                    'final_attempt': attempt_number_redo,
                    'total_taps': len(tap_events_redo),
                    'avg_tap_rate': avg_tap_rate_redo,
                    'max_tap_rate': max_tap_rate_redo,
                    'avg_tap_interval': avg_tap_interval_redo,
                    'min_tap_interval': min_tap_interval_redo,
                    'tap_cv': tap_cv_redo,
                    'estimated_polling': estimated_polling_redo,
                    'keyboard_rating': keyboard_rating_redo
                }
                all_keyboard_sessions.append(keyboard_session_data)
                
                # Recalculate keyboard input latency
                keyboard_input_latency = (min_tap_interval_redo / 2) + 2 if min_tap_interval_redo > 0 else 10.0
                visual_reaction_estimated_latency = display_latency + keyboard_input_latency + light_travel_time
                audio_reaction_estimated_latency = display_latency + keyboard_input_latency + sound_travel_time
                
                print(f"Keyboard input latency updated: {keyboard_input_latency:.2f} ms")
            else:
                print(f"Insufficient taps - using previous keyboard data")
            
            # Check if forced redo needed (same logic as main section)
            keyboard_needs_redo_reminders = (keyboard_rating_redo in ["FAILED", "POOR"])
            
            keyboard_rec_text_redo = "Keyboard hardware is consistent and reliable for testing."
            if keyboard_rating_redo in ["FAILED", "POOR"]:
                keyboard_rec_text_redo = (
                    "High keyboard input variation detected.\n"
                    "CONSIDER: Switch to hardwired (USB) keyboard if possible.\n"
                    "Wireless keyboards often have inconsistent latency.\n\n"
                    "IF YOU REPEATEDLY GET THIS SCREEN:\n"
                    "1. Press ESC to exit the program\n"
                    "2. Restart and complete the Performance Checklist\n"
                    "3. Close all background applications\n"
                    "4. Try the test again\n"
                    "5. If still failing, contact your researcher for assistance"
                )
            
            if keyboard_needs_redo_reminders:
                # FAILED/POOR - show forced redo (same as main section)
                result_kb = visual.TextStim(
                    win=win,
                    text=(
                        f"KEYBOARD TEST - REDO REQUIRED\n\n"
                        f"PERFORMANCE RATING: {keyboard_rating_redo}\n\n"
                        f"Total taps: {len(tap_events_redo)}\n"
                        f"Minimum interval: {min_tap_interval_redo:.2f} ms\n"
                        f"Consistency (CV): {tap_cv_redo:.2f}%\n\n"
                        f"{keyboard_rec_text_redo}"
                    ),
                    color='red',
                    height=int(28 * scale_avg),
                    wrapWidth=int(5070 * scale_x),
                    pos=(int(0 * scale_x), int(100 * scale_y))
                )
                
                retry_instr_kb = visual.TextStim(
                    win=win,
                    text='MUST REDO - Press R',
                    color='red',
                    height=int(40 * scale_avg),
                    pos=(int(-250 * scale_x), int(-600 * scale_y)),
                    bold=True
                )
                
                quit_instr_kb = visual.TextStim(
                    win=win,
                    text='Press ESC to exit',
                    color='red',
                    height=int(40 * scale_avg),
                    pos=(int(250 * scale_x), int(-600 * scale_y)),
                    bold=True
                )
                
                result_kb.draw()
                retry_instr_kb.draw()
                quit_instr_kb.draw()
                copyright_text_small.draw()
                draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                win.flip()
                
                print("FORCED REDO: Keyboard FAILED/POOR - must redo or exit")
                
                # Wait for R (redo) or ESC (exit)
                event.clearEvents()
                waiting_kb = True
                while waiting_kb:
                    keys_kb = event.getKeys(['r', 'escape'])
                    if 'r' in keys_kb:
                        print("Redoing keyboard test...")
                        waiting_kb = False
                        # Will loop back to run keyboard test again
                    elif 'escape' in keys_kb:
                        print("User exiting program...")
                        win.close()
                        sys.exit(0)
                    
                    # Check clicks
                    if is_text_clicked(retry_instr_kb, global_mouse):
                        print("Clicked REDO keyboard")
                        waiting_kb = False
                    elif is_text_clicked(quit_instr_kb, global_mouse):
                        print("Clicked EXIT")
                        win.close()
                        sys.exit(0)
                    
                    core.wait(0.01)
                
                # Loop back to reminders to run keyboard test again
                print("Looping back to reminders - user will press R again to retry")
                continue  # Return to reminders loop
                
            else:
                # FAIR or better - can return to reminders
                complete_msg = visual.TextStim(
                    win=win,
                    text=(
                        "KEYBOARD TEST (REDO) COMPLETE\n\n"
                        f"RATING: {keyboard_rating_redo}\n"
                        f"Total taps: {len(tap_events_redo)}\n"
                        f"Average rate: {avg_tap_rate_redo:.1f} taps/sec\n\n"
                        "Results updated.\n\n"
                        "Press K to return to reminders"
                    ),
                    color='green',
                    height=int(32 * scale_avg),
                    wrapWidth=int(5070 * scale_x),
                    pos=(int(0 * scale_x), int(0 * scale_y))
                )
                complete_msg.draw()
                copyright_text_small.draw()
                draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                win.flip()
                
                # Wait for K
                event.clearEvents()
                core.wait(0.5)
                event.getKeys()
                
                waiting_kb = True
                while waiting_kb:
                    keys_kb = event.getKeys(['k', 'escape'])
                    if 'k' in keys_kb:
                        print("Returning to reminders...")
                        waiting_kb = False
                    elif 'escape' in keys_kb:
                        win.close()
                        sys.exit(0)
                    core.wait(0.01)
            
            # Exit keyboard redo section - return to reminders
            
        elif 'escape' in keys:
            win.close()
            core.quit()
        
        core.wait(0.01)

# Clear screen
copyright_text_small.draw()
win.flip()
event.clearEvents()
core.wait(0.5)

# Calculate estimated times for each section
def format_time(seconds):
    """Convert seconds to a readable time format."""
    if seconds < 60:
        return f"{int(seconds)} sec"
    else:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        if secs == 0:
            return f"{mins} min"
        else:
            return f"{mins} min {secs} sec"

# Calculate times
memory_1_study_time = MEMORY_SET_1_STUDY_TIME
memory_2_study_time = MEMORY_SET_2_STUDY_TIME

# Reaction tests: delay + (num_trials * average_interval)
avg_interval = (INTERVAL_MIN + INTERVAL_MAX) / 2
visual_test_time = PRE_EXPERIMENT_DELAY + (NUM_ITERATIONS * avg_interval)
audio_test_time = PRE_EXPERIMENT_DELAY + (NUM_ITERATIONS * avg_interval)

# Recognition tests are user-paced
# Formula: Each shape takes ~15 seconds to remember + 5 seconds to select = 20 seconds total
# Time = number of shapes to select * 20 seconds
memory_1_recog_1_time = MEMORY_SET_1_SIZE * 20  # Memory Set 1 recognition
memory_2_recog_1_time = MEMORY_SET_2_SIZE * 20  # Memory Set 2 recognition
memory_1_recog_2_time = MEMORY_SET_1_SIZE * 20  # Memory Set 1 recognition iteration 2

# Calculate total time (only for tests that will actually run)
total_time = 0
if RUN_MEMORY_TEST_1:
    total_time += memory_1_study_time + memory_1_recog_1_time + memory_1_recog_2_time
if RUN_VISUAL_TEST:
    total_time += visual_test_time
if RUN_MEMORY_TEST_2:
    total_time += memory_2_study_time + memory_2_recog_1_time
if RUN_AUDIO_TEST:
    total_time += audio_test_time

# Create skip indicators
skip_mem1 = " [SKIPPED]" if not RUN_MEMORY_TEST_1 else ""
skip_visual = " [SKIPPED]" if not RUN_VISUAL_TEST else ""
skip_mem2 = " [SKIPPED]" if not RUN_MEMORY_TEST_2 else ""
skip_audio = " [SKIPPED]" if not RUN_AUDIO_TEST else ""

# Show overall test instruction screen
overall_instruction = visual.TextStim(
    win=win,
    text=(
        "=== COMPLETE TEST OVERVIEW ===\n\n"
        "You will complete the following tests in this order:\n\n"
        f"1. [📚] MEMORY SET 1 - Study Phase (~{format_time(memory_1_study_time)}){skip_mem1}\n"
        f"     Memorize {MEMORY_SET_1_SIZE} unique images\n\n"
        f"2. [□] VISUAL REACTION TEST (~{format_time(visual_test_time)}){skip_visual}\n"
        f"     Press SPACE when you see a white square ({NUM_ITERATIONS} trials)\n\n"
        f"3. [✓] MEMORY SET 1 - Recognition Test #1 (~{format_time(memory_1_recog_1_time)}){skip_mem1}\n"
        f"     Identify the {MEMORY_SET_1_SIZE} images from Memory Set 1\n\n"
        f"4. [📚] MEMORY SET 2 - Study Phase (~{format_time(memory_2_study_time)}){skip_mem2}\n"
        f"     Memorize {MEMORY_SET_2_SIZE} NEW different images\n\n"
        f"5. [♪] AUDIO REACTION TEST (~{format_time(audio_test_time)}){skip_audio}\n"
        f"     Press SPACE when you hear a beep sound ({NUM_ITERATIONS} trials)\n\n"
        f"6. [✓] MEMORY SET 2 - Recognition Test #1 (~{format_time(memory_2_recog_1_time)}){skip_mem2}\n"
        f"     Identify the {MEMORY_SET_2_SIZE} images from Memory Set 2\n\n"
        f"7. [✓] MEMORY SET 1 - Recognition Test #2 (~{format_time(memory_1_recog_2_time)}){skip_mem1}\n"
        f"     Identify the Memory Set 1 images again\n\n"
        f"Total estimated time (active tests only): ~{format_time(total_time)}"
    ),
    color='white',
    height=int(38 * scale_avg),  # Reduced from 42 to 38 (10% smaller)
    wrapWidth=int(6500 * scale_x),  # Much wider to use less vertical space
    alignText='center',
    pos=(int(0 * scale_x), int(-50 * scale_y))  # Moved down from y=80 to y=-50, below progress bar
)

continue_instr = visual.TextStim(
    win=win,
    text='Press SPACE to begin',  # Shortened to fit on one line
    color='green',
    height=int(32 * scale_avg),
    pos=(int(-350 * scale_x), int(-700 * scale_y)),
    bold=True
)

quit_instr = visual.TextStim(
    win=win,
    text='Press ESC to quit',
    color='red',
    height=int(32 * scale_avg),
    pos=(int(350 * scale_x), int(-700 * scale_y)),
    bold=True
)

overall_instruction.draw()
continue_instr.draw()
quit_instr.draw()
copyright_text_small.draw()
draw_progress_bar(win, test_sections, current_section, copyright_text_small)
win.flip()

print("Waiting for SPACE to start overall test sequence...")
print(f"Estimated total time: {format_time(total_time)}")
global_mouse.setVisible(True)  # Show mouse for clicking instructions
waiting = True
last_click_time = 0
while waiting:
    keys = event.getKeys(['space', 'escape'])
    current_time = core.getTime()
    
    if 'space' in keys:
        waiting = False
    elif 'escape' in keys:
        win.close()
        core.quit()
    
    # Check for mouse clicks on instruction text
    if current_time - last_click_time > 0.3:
        if is_text_clicked(continue_instr, global_mouse):
            print("User clicked BEGIN")
            waiting = False
            last_click_time = current_time
            core.wait(0.2)
        elif is_text_clicked(quit_instr, global_mouse):
            print("User clicked QUIT")
            win.close()
            core.quit()
    
    core.wait(0.01)

# ===== STEP 7: MEMORY TEST 1 - STUDY PHASE INSTRUCTIONS =====
if RUN_MEMORY_TEST_1:
    print("\n" + "=" * 80)
    print("STEP 7: MEMORY TEST 1 - STUDY PHASE INSTRUCTIONS")
    print("=" * 80)
else:
    print("\n" + "=" * 80)
    print("STEP 7: MEMORY TEST 1 - SKIPPED (RUN_MEMORY_TEST_1 = False)")
    print("=" * 80)
    
    # Show skip screen
    skip_screen = visual.TextStim(
        win=win,
        text=(
            "=== MEMORY SET 1 - STUDY PHASE ===\n\n"
            "This test has been skipped.\n\n"
            "RUN_MEMORY_TEST_1 is set to False."
        ),
        color='yellow',
        height=int(48 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to continue',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to exit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    skip_screen.draw()
    continue_instr.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    print("Memory Test 1 Study skipped - waiting for user input...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        # Check for mouse clicks on instruction text
        if current_time - last_click_time > 0.3:
            if is_text_clicked(continue_instr, global_mouse):
                print("User clicked CONTINUE")
                waiting = False
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(quit_instr, global_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
        
        core.wait(0.01)

# Clear screen and wait
copyright_text_small.draw()
win.flip()
core.wait(0.5)

# Create all memory images (always create for potential use)
all_memory_images = create_memory_images(win, MEMORY_POOL_SIZE)

# Initialize memory test variables
memory_set_1_indices = []
memory_set_1_images = []
memory_set_2_indices = []
memory_set_2_images = []

if RUN_MEMORY_TEST_1 or RUN_MEMORY_TEST_2:
    # Randomly select images for Memory Set 1
    if RUN_MEMORY_TEST_1:
        memory_set_1_indices = random.sample(range(MEMORY_POOL_SIZE), MEMORY_SET_1_SIZE)
        memory_set_1_images = [all_memory_images[i] for i in memory_set_1_indices]
        print(f"Memory Set 1 images selected: {sorted(memory_set_1_indices)}")
    
    # Select DIFFERENT images for Memory Set 2 (from remaining images)
    if RUN_MEMORY_TEST_2:
        remaining_indices = [i for i in range(MEMORY_POOL_SIZE) if i not in memory_set_1_indices]
        memory_set_2_indices = random.sample(remaining_indices, MEMORY_SET_2_SIZE)
        memory_set_2_images = [all_memory_images[i] for i in memory_set_2_indices]
        print(f"Memory Set 2 images selected: {sorted(memory_set_2_indices)}")
    
    if RUN_MEMORY_TEST_1 and RUN_MEMORY_TEST_2:
        print(f"Total unique images used: {len(set(memory_set_1_indices + memory_set_2_indices))} / {MEMORY_POOL_SIZE}")

# Create shared UI elements globally (used by all memory recognition tests)
timer_text = visual.TextStim(
    win=win,
    text='',
    color='white',
    height=int(48 * scale_avg),
    pos=(int(0 * scale_x), int(320 * scale_y))  # Lowered from 450 to avoid progress bar overlap
)

mouse = event.Mouse(visible=True, win=win)

selection_border = visual.Rect(
    win, 
    width=int(150 * scale_x), 
    height=int(150 * scale_avg), 
    lineColor='green', 
    lineWidth=6,
    fillColor=None  # Explicitly no fill - just outline
)

# Calculate optimal grid layout for recognition tests (based on pool size)
if MEMORY_POOL_SIZE == 0:
    grid_cols = 1
    grid_rows = 0
else:
    grid_cols = min(5, MEMORY_POOL_SIZE)  # Back to 5 columns (original)
    grid_rows = (MEMORY_POOL_SIZE + grid_cols - 1) // grid_cols

image_spacing = int(180 * scale_avg)  # SCALED, reduced to 180 for tighter vertical spacing
start_x = -(grid_cols - 1) * image_spacing / 2
start_y = (grid_rows - 1) * image_spacing / 2 - int(50 * scale_y)  # Shift down 50px to avoid progress bar

# Calculate instruction positions
instruction_top_pos = start_y + image_spacing * 0.8
instruction_bottom_pos = -(start_y + image_spacing * 1.2)  # Increased from 0.8 to 1.2 for more space below grid

# Create instruction and counter text (will be updated for each test)
instruction_display = visual.TextStim(
    win=win,
    text='',
    color='white',
    height=int(32 * scale_avg),
    pos=(0, instruction_top_pos)
)

counter_text = visual.TextStim(
    win=win,
    text='',
    color='white',
    height=int(25 * scale_avg),
    pos=(0, instruction_bottom_pos)
)

if RUN_MEMORY_TEST_1:
    # Set current section to Memory Set 1 Study
    current_section = 0
    
    # Clear any lingering events
    event.clearEvents()
    core.wait(0.5)

    # Show instruction screen
    memory_instruction = visual.TextStim(
        win=win,
        text=(
            "=== MEMORY SET 1 - STUDY PHASE ===\n\n"
            f"You will now see {MEMORY_SET_1_SIZE} unique images.\n\n"
            f"You will have {format_time_estimate(MEMORY_SET_1_STUDY_TIME)} to memorize these images.\n\n"
            "Try to remember as many details as possible:\n"
            "- Shape\n"
            "- Color\n"
            "- Pattern\n\n"
            "Later, you will be asked to identify these images\n"
            "from a larger set."
        ),
        color='white',
        height=int(42 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to begin studying',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    memory_instruction.draw()
    continue_instr.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()

    # Wait for spacebar
    print("Waiting for SPACE to start memory study phase...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        # Check for mouse clicks on instruction text
        if current_time - last_click_time > 0.3:
            if is_text_clicked(continue_instr, global_mouse):
                print("User clicked CONTINUE")
                waiting = False
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(quit_instr, global_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
        
        core.wait(0.01)

    # Clear events
    event.clearEvents()
    core.wait(0.3)

    # ===== STEP 8: MEMORY TEST 1 - REMEMBERING PERIOD =====
    print("\n" + "=" * 80)
    print(f"STEP 8: MEMORY TEST 1 - REMEMBERING PERIOD ({MEMORY_SET_1_SIZE} images, {int(MEMORY_SET_1_STUDY_TIME/60)} minutes)")
    print("=" * 80)

    # Display all Memory Set 1 images at once for study period
    study_start = core.getTime()

    # Calculate optimal grid layout for Memory Set 1
    if MEMORY_SET_1_SIZE == 0:
        study_1_grid_cols = 1
        study_1_grid_rows = 0
    else:
        # Use 5 columns as standard, calculate rows needed
        study_1_grid_cols = min(5, MEMORY_SET_1_SIZE)  # Use fewer columns if less than 5 images
        study_1_grid_rows = (MEMORY_SET_1_SIZE + study_1_grid_cols - 1) // study_1_grid_cols

    study_1_image_spacing = 220
    # Center the grid horizontally
    study_1_start_x = -(study_1_grid_cols - 1) * study_1_image_spacing / 2
    # Center the grid vertically
    study_1_start_y = (study_1_grid_rows - 1) * study_1_image_spacing / 2

    print(f"Displaying all {MEMORY_SET_1_SIZE} images simultaneously ({study_1_grid_rows} rows x {study_1_grid_cols} cols) for {MEMORY_SET_1_STUDY_TIME} seconds...")

    while core.getTime() - study_start < MEMORY_SET_1_STUDY_TIME:
        elapsed = core.getTime() - study_start
        time_remaining = MEMORY_SET_1_STUDY_TIME - elapsed
        
        # Update mouse visibility (auto-hide during study)
        update_mouse_visibility(global_mouse, auto_hide=True)
        
        # Update timer
        timer_text.text = f"MEMORY SET 1 - STUDY PHASE\nTime Remaining: {int(time_remaining//60)}:{int(time_remaining%60):02d}"
        
        # Draw all Memory Set 1 images in grid
        for idx, img_data in enumerate(memory_set_1_images):
            row = idx // study_1_grid_cols
            col = idx % study_1_grid_cols
            x_pos = study_1_start_x + col * study_1_image_spacing
            y_pos = study_1_start_y - row * study_1_image_spacing
            
            # Draw image elements at grid position
            for element in img_data['elements']:
                element.pos = (x_pos, y_pos)
                element.draw()
        
        timer_text.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        # Check for escape
        keys = event.getKeys(['escape'])
        if 'escape' in keys:
            win.close()
            core.quit()
        
        core.wait(0.01)

    print("Memory Set 1 study phase complete")

    # Mark Memory Set 1 Study as completed
    test_sections[0]['completed'] = True
    current_section = 1  # Move to Visual Reaction Test

    # Show transition message
    transition_text = visual.TextStim(
        win=win,
        text="Memory Set 1 study complete!\n\nMoving to Visual Reaction Test...",
        color='green',
        height=int(48 * scale_avg),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-450 * scale_y)),
        bold=True
    )
    
    transition_text.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()

    # Wait 2 seconds but allow ESC
    transition_start = core.getTime()
    while core.getTime() - transition_start < 2.0:
        keys = event.getKeys(['escape'])
        if 'escape' in keys:
            win.close()
            core.quit()
        core.wait(0.01)
else:
    print("\n" + "=" * 80)
    print("STEP 8: MEMORY TEST 1 - REMEMBERING PERIOD SKIPPED")
    print("=" * 80)
    
    # Skip Memory Set 1 sections in progress
    if current_section < 1:
        current_section = 1  # Skip to Visual RT
    
    # Show skip screen
    skip_screen = visual.TextStim(
        win=win,
        text=(
            "=== MEMORY SET 1 ===\n\n"
            "This test has been skipped.\n\n"
            "RUN_MEMORY_TEST_1 is set to False.\n\n"
            "Memory Set 1 study and recognition tests will not run."
        ),
        color='yellow',
        height=int(48 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to continue',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to exit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    skip_screen.draw()
    continue_instr.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    print("Memory Test 1 skipped - waiting for user input...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        # Check for mouse clicks on instruction text
        if current_time - last_click_time > 0.3:
            if is_text_clicked(continue_instr, global_mouse):
                print("User clicked CONTINUE")
                waiting = False
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(quit_instr, global_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
        
        core.wait(0.01)

# ===== STEP 9: VISUAL REACTION TEST - INSTRUCTIONS =====
print("\n" + "=" * 80)
if RUN_VISUAL_TEST:
    print("STEP 9: VISUAL REACTION TEST INSTRUCTIONS")
    
    # Show fatigue reminder before reaction tests
    print("Showing fatigue reminder...")
    global_mouse.setVisible(False)  # Hide mouse for entire visual RT section (instructions + test)
    fatigue_reminder = visual.TextStim(
        win=win,
        text=(
            "=== REACTION TESTS BEGINNING ===\n\n"
            "IMPORTANT REMINDER:\n\n"
            "The reaction tests are designed to induce mental fatigue.\n"
            "This is intentional and expected.\n\n"
            "PLEASE DO NOT TAKE BREAKS during the reaction tests.\n"
            "Continue even when you feel tired.\n\n"
            "Your performance when fatigued is the goal of this study.\n\n"
            "Are you ready to begin the reaction tests?"
        ),
        color='yellow',
        height=int(40 * scale_avg),
        wrapWidth=int(6000 * scale_x),
        pos=(int(0 * scale_x), int(0 * scale_y)),
        bold=True
    )
    
    continue_fatigue = visual.TextStim(
        win=win,
        text='Press SPACE to begin reaction tests',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True,
        wrapWidth=int(600 * scale_x)
    )
    
    quit_fatigue = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    fatigue_reminder.draw()
    continue_fatigue.draw()
    quit_fatigue.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    print("Waiting for user to acknowledge fatigue reminder...")
    waiting_fatigue = True
    while waiting_fatigue:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting_fatigue = False
            print("User ready to begin reaction tests")
        elif 'escape' in keys:
            win.close()
            core.quit()
        core.wait(0.01)
    
    # Clear screen
    copyright_text_small.draw()
    win.flip()
    event.clearEvents()
    core.wait(0.5)
else:
    print("STEP 9: VISUAL REACTION TEST SKIPPED")
print("=" * 80)

# Clear screen and wait
copyright_text_small.draw()
win.flip()
event.clearEvents()
core.wait(1.0)  # Longer delay to prevent accidental advancement
event.clearEvents()

# Initialize data storage
visual_results = []
audio_results = []
experiment_frame_times = []
experiment_dropped_frames = 0

# Initialize comprehensive performance logging
performance_log = {
    'frame_log': [],  # List of {timestamp, frame_time, section, events}
    'event_log': [],  # List of {timestamp, event_type, description}
    'section_log': [],  # List of {section_name, start_time, end_time}
    'extreme_frames': []  # List of {timestamp, frame_time, section, severity}
}
experiment_start_time = core.getTime()  # Reference time for all timestamps

# Clear any lingering events
event.clearEvents()
core.wait(0.5)

if RUN_VISUAL_TEST:
    # Calculate estimated time
    avg_interval = (INTERVAL_MIN + INTERVAL_MAX) / 2
    visual_est_time = PRE_EXPERIMENT_DELAY + (NUM_ITERATIONS * avg_interval)
    visual_est_mins = int(visual_est_time // 60)
    visual_est_secs = int(visual_est_time % 60)
    if visual_est_mins > 0:
        visual_time_str = f"{visual_est_mins} min {visual_est_secs} sec"
    else:
        visual_time_str = f"{visual_est_secs} sec"
    
    # Show comprehensive instruction screen with centered square
    instruction_top = visual.TextStim(
        win=win,
        text=(
            "=== VISUAL REACTION TEST ===\n\n"
            "You will now begin the visual reaction time test.\n\n"
            "REACT TO THE RANDOMLY OCCURRING WHITE SQUARE\n\n"
            "Task: Press the SPACE BAR as quickly as possible\n"
            "when you see this white square:"
        ),
        color='white',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(320 * scale_y)),
        wrapWidth=int(5070 * scale_x)
    )

    instruction_bottom = visual.TextStim(
        win=win,
        text=(
            f"Number of test trials: {NUM_ITERATIONS}\n"
            f"Interval between squares: {INTERVAL_MIN}-{INTERVAL_MAX} seconds\n"
            f"Delay before first square: {PRE_EXPERIMENT_DELAY} seconds (system initialization)\n"
            f"Estimated time: ~{visual_time_str}"
        ),
        color='white',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-180 * scale_y)),
        wrapWidth=int(5070 * scale_x)
    )
    
    instruction_bottom2 = visual.TextStim(
        win=win,
        text=(
            "There will be a black screen delay before the first square appears.\n"
            "This allows the system to initialize and ensures accurate timing."
        ),
        color='white',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-290 * scale_y)),
        wrapWidth=int(5070 * scale_x)
    )
    
    warning_text = visual.TextStim(
        win=win,
        text=(
            "IMPORTANT: If you DO NOT see a white square, DO NOT press SPACE.\n"
            "Only press SPACE when reacting to the actual white square stimulus."
        ),
        color='yellow',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-400 * scale_y)),
        wrapWidth=int(5070 * scale_x),
        bold=True
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text="Press SPACE when ready to begin",
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-700 * scale_y)),
        bold=True,
        wrapWidth=int(600 * scale_x)
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-700 * scale_y)),
        bold=True
    )

    # Position square in center (with larger size, keep centered)
    square.pos = (0, 30)

    # Draw all elements
    instruction_top.draw()
    square.draw()
    instruction_bottom.draw()
    instruction_bottom2.draw()
    warning_text.draw()
    continue_instr.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()

    print("Waiting for participant to press SPACE...")
    
    # Wait for spacebar with ESC handling
    global_mouse.setVisible(False)  # Hide mouse during visual RT to prevent distraction
    waiting = True
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        
        core.wait(0.01)

    # IMMEDIATELY clear screen to black
    event.clearEvents()
    global_mouse.setVisible(False)  # Hide mouse during visual RT test to prevent distraction
    copyright_text_small.draw()
    win.flip()
    core.wait(0.5)  # Longer pause to prevent carryover clicks

    # ===== STEP 10: VISUAL REACTION TEST EXECUTION =====
    print("\n" + "=" * 80)
    print("STEP 10: VISUAL REACTION TEST")
    print("=" * 80)
    
    print(f"Black screen delay: {PRE_EXPERIMENT_DELAY} seconds...")

    # Log delay section start
    log_section_boundary(performance_log, 'Visual Test - Pre-Delay', 'START', experiment_start_time)

    # Black screen delay - MINIMAL LOOP
    delay_start = core.getTime()
    target_delay_end = delay_start + PRE_EXPERIMENT_DELAY
    
    while core.getTime() < target_delay_end:
        copyright_text_small.draw()
        win.flip()
        frame_time = core.getTime()
        
        # Log frame with section info
        performance_log['frame_log'].append({
            'timestamp': frame_time - experiment_start_time,
            'frame_time': (frame_time - experiment_frame_times[-1]) * 1000 if experiment_frame_times else 0,
            'section': 'Visual Test - Pre-Delay',
            'events': []
        })
        
        # Check for dropped frames BEFORE appending
        if len(experiment_frame_times) > 0:
            frame_duration = frame_time - experiment_frame_times[-1]
            if frame_duration > (refresh_rate * 1.5):
                experiment_dropped_frames += 1
        
        experiment_frame_times.append(frame_time)

    # Log delay section end
    log_section_boundary(performance_log, 'Visual Test - Pre-Delay', 'END', experiment_start_time)

    print("Starting visual reaction test trials...")

    # Log section start
    log_section_boundary(performance_log, 'Visual Reaction Test', 'START', experiment_start_time)

    # Visual reaction loop
    for trial in range(1, NUM_ITERATIONS + 1):
        trial_dropped_frames = 0
        trial_misclicks = 0
        
        # Wait random interval before showing square
        interval = random.uniform(INTERVAL_MIN, INTERVAL_MAX)
        
        # Wait interval - OPTIMIZED MINIMAL LOOP (defer logging until after trial)
        interval_start = core.getTime()
        target_interval_end = interval_start + interval
        trial_frame_times = []  # Collect timestamps for post-trial processing
        
        while core.getTime() < target_interval_end:
            copyright_text_small.draw()
            win.flip()
            trial_frame_times.append(core.getTime())
        
        # Clear any previous key presses
        event.clearEvents()
        
        # Show square and start timer
        square.draw()
        copyright_text_small.draw()
        win.flip()
        trial_start = core.getTime()
        
        # Log square appearance
        log_performance_event(performance_log, 'VISUAL_STIMULUS', 
                             f'White square appeared (Trial {trial})', 
                             experiment_start_time)
        # Track this frame
        if len(experiment_frame_times) > 0:
            frame_duration = trial_start - experiment_frame_times[-1]
            if frame_duration > (refresh_rate * 1.5):
                experiment_dropped_frames += 1
                trial_dropped_frames += 1
        experiment_frame_times.append(trial_start)
        
        # Log frame for square appearance
        performance_log['frame_log'].append({
            'timestamp': trial_start - experiment_start_time,
            'frame_time': (trial_start - experiment_frame_times[-2]) * 1000 if len(experiment_frame_times) > 1 else 0,
            'section': f'Visual Test - Trial {trial} (Stimulus)',
            'events': ['SQUARE_SHOWN']
        })
        
        # Wait for response - MINIMAL LOOP with deferred logging
        response_made = False
        correct_reaction_time = 0
        key_press_times = []
        last_event_time = trial_start
        response_frame_time = 0  # Store frame time at moment of response
        
        # Deferred logging: Just collect timestamps during measurement
        frame_timestamp_buffer = []
        
        while not response_made:
            keys = event.getKeys(timeStamped=True)
            
            for key, timestamp in keys:
                if key == 'space':
                    # Correct response
                    interval = (timestamp - last_event_time) * 1000
                    key_press_times.append(interval)
                    correct_reaction_time = (timestamp - trial_start) * 1000
                    
                    # Capture the most recent frame time (frame immediately before response)
                    if len(experiment_frame_times) > 1:
                        response_frame_time = (experiment_frame_times[-1] - experiment_frame_times[-2]) * 1000
                    
                    response_made = True
                    # Log response event
                    log_performance_event(performance_log, 'USER_RESPONSE', 
                                         f'Space pressed (Trial {trial}, RT: {correct_reaction_time:.0f}ms)', 
                                         experiment_start_time)
                    break
                elif key == 'escape':
                    win.close()
                    core.quit()
                else:
                    # Incorrect key press
                    interval = (timestamp - last_event_time) * 1000
                    key_press_times.append(interval)
                    last_event_time = timestamp
                    trial_misclicks += 1
            
            # Keep square visible - MINIMAL OVERHEAD
            square.draw()
            current_frame_time = core.getTime()
            
            # DEFERRED: Just collect timestamp (fast!)
            frame_timestamp_buffer.append((current_frame_time, trial))
            
            # Check for dropped frames
            if len(experiment_frame_times) > 0:
                frame_duration = current_frame_time - experiment_frame_times[-1]
                if frame_duration > (refresh_rate * 1.5):
                    experiment_dropped_frames += 1
                    trial_dropped_frames += 1
            
            experiment_frame_times.append(current_frame_time)
            
            copyright_text_small.draw()
            win.flip()
        
        # PROCESS DEFERRED LOGS (after response collected - doesn't impact measurement)
        for frame_time, trial_num in frame_timestamp_buffer:
            if len(experiment_frame_times) > 0:
                frame_idx = experiment_frame_times.index(frame_time) if frame_time in experiment_frame_times else -1
                if frame_idx > 0:
                    frame_duration_ms = (experiment_frame_times[frame_idx] - experiment_frame_times[frame_idx-1]) * 1000
                else:
                    frame_duration_ms = 0
                
                performance_log['frame_log'].append({
                    'timestamp': frame_time - experiment_start_time,
                    'frame_time': frame_duration_ms,
                    'section': f'Visual Test - Trial {trial_num} (Response)',
                    'events': []
                })
        
        # Clear screen after response
        copyright_text_small.draw()
        win.flip()
        
        # DEFERRED PROCESSING - Process timestamps collected during trial
        # This adds zero overhead to the measurement loop above
        trial_dropped_frames = 0
        for i, frame_time in enumerate(trial_frame_times):
            # Add to experiment frame times
            experiment_frame_times.append(frame_time)
            
            # Create performance log entry
            performance_log['frame_log'].append({
                'timestamp': frame_time - experiment_start_time,
                'frame_time': (frame_time - experiment_frame_times[-2]) * 1000 if len(experiment_frame_times) > 1 else 0,
                'section': 'Visual Test - Waiting',
                'events': []
            })
            
            # Check for dropped frames
            if len(experiment_frame_times) > 1:
                frame_duration = frame_time - experiment_frame_times[-2]
                if frame_duration > (refresh_rate * 1.5):
                    experiment_dropped_frames += 1
                    trial_dropped_frames += 1
        
        # Format interval times as comma-separated list
        interval_list = ",".join([f"{t:.0f}" for t in key_press_times])
        
        # Store trial result
        visual_results.append({
            'trial': trial,
            'reaction_time': correct_reaction_time,
            'response_frame_time': response_frame_time,  # Frame time at moment of response
            'misclicks': trial_misclicks,
            'intervals': interval_list,
            'frame_drops': trial_dropped_frames
        })
        
        print(f"Visual reaction test trial {trial}/{NUM_ITERATIONS} complete: {correct_reaction_time:.0f}ms")

    print("Visual reaction test complete")
    
    # Log section end
    log_section_boundary(performance_log, 'Visual Reaction Test', 'END', experiment_start_time)
    
    # Mark Visual Reaction Test as completed
    test_sections[1]['completed'] = True
    
    # PREVENT ACCIDENTAL SKIP after Visual RT (ensures user reads next test instructions)
    print("\n" + "=" * 80)
    print("INSTRUCTION CONFIRMATION AFTER VISUAL RT")
    print("=" * 80)
    
    confirm_text = visual.TextStim(
        win=win,
        text=(
            "Visual Reaction Time test complete.\n\n"
            "NEXT TEST:\n"
            "You will now see a Memory Recognition test.\n\n"
            "Read the instructions on the next screen carefully.\n\n"
            "Press K when ready to continue."
        ),
        color='yellow',
        height=int(42 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(0 * scale_y))
    )
    
    confirm_continue = visual.TextStim(
        win=win,
        text='Press K to continue',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-400 * scale_y)),
        bold=True
    )
    
    confirm_text.draw()
    confirm_continue.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    # Wait for K - prevents accidental click-through (K less likely to be pressed accidentally than SPACE)
    event.clearEvents()
    core.wait(0.5)  # Extra delay to prevent immediate click-through
    event.clearEvents()
    
    waiting_confirm = True
    while waiting_confirm:
        keys = event.getKeys(['k', 'escape'])
        if 'k' in keys:
            print("User pressed K - continuing to Memory Test 1 Iteration 1")
            waiting_confirm = False
        elif 'escape' in keys:
            win.close()
            sys.exit(0)
        core.wait(0.01)
    
    current_section = 2  # Move to Memory Set 1 Recognition 1
else:
    # Visual test skipped - advance section appropriately
    if current_section < 2:
        current_section = 2  # Skip to Memory 1 Recognition (or further if Memory 1 also skipped)
    
    # Show skip screen  
    print("\n" + "=" * 80)
    print("STEP 10: VISUAL REACTION TEST SKIPPED")
    print("=" * 80)
    
    skip_screen = visual.TextStim(
        win=win,
        text=(
            "=== VISUAL REACTION TEST ===\n\n"
            "This test has been skipped.\n\n"
            "RUN_VISUAL_TEST is set to False."
        ),
        color='yellow',
        height=int(48 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to continue',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to exit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    skip_screen.draw()
    continue_instr.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    print("Visual reaction test skipped - waiting for user input...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        # Check for mouse clicks on instruction text
        if current_time - last_click_time > 0.3:
            if is_text_clicked(continue_instr, global_mouse):
                print("User clicked CONTINUE")
                waiting = False
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(quit_instr, global_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
        
        core.wait(0.01)

# ===== STEP 11: MEMORY SET 1 - RECOGNITION TEST ITERATION 1 =====
if RUN_MEMORY_TEST_1:
    print("\n" + "=" * 80)
    print("STEP 11: MEMORY SET 1 - RECOGNITION TEST ITERATION 1")
    print("=" * 80)
else:
    print("\n" + "=" * 80)
    print("STEP 11: MEMORY SET 1 - RECOGNITION TEST ITERATION 1 SKIPPED")
    print("=" * 80)
    
    # Show skip screen
    skip_screen = visual.TextStim(
        win=win,
        text=(
            "=== MEMORY SET 1 - RECOGNITION TEST ===\n\n"
            "This test has been skipped.\n\n"
            "RUN_MEMORY_TEST_1 is set to False."
        ),
        color='yellow',
        height=int(48 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to continue',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to exit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    skip_screen.draw()
    continue_instr.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    print("Memory Test 1 Recognition Iteration 1 skipped - waiting for user input...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        # Check for mouse clicks on instruction text
        if current_time - last_click_time > 0.3:
            if is_text_clicked(continue_instr, global_mouse):
                print("User clicked CONTINUE")
                waiting = False
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(quit_instr, global_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
        
        core.wait(0.01)

# Initialize default values for when test is skipped
memory_set_1_test_1_selected = []
memory_set_1_test_1_correct = []  # Keep as list for sorted() in file output
memory_set_1_test_1_correct_count = 0  # Count for table
memory_set_1_test_1_incorrect_count = 0  # Count for table
memory_set_1_test_1_accuracy = 0.0
memory_set_1_test_1_correct_not_changed = 0
memory_set_1_test_1_correct_changed = 0
memory_set_1_test_1_incorrect_not_changed = 0
memory_set_1_test_1_incorrect_changed = 0
memory_set_1_test_1_clicks_on_correct = 0
memory_set_1_test_1_clicks_on_incorrect = 0
memory_set_1_test_1_total_clicks = 0

if RUN_MEMORY_TEST_1:
    # Clear screen and wait
    copyright_text_small.draw()
    win.flip()
    core.wait(0.5)

    # Clear any lingering events
    event.clearEvents()
    core.wait(0.5)

    # Calculate estimated time for recognition test (user-paced)
    # Formula: Each shape takes 15 seconds to remember + 5 seconds to select = 20 seconds
    recog_est_time = MEMORY_SET_1_SIZE * 20
    recog_est_mins = int(recog_est_time // 60)
    recog_est_secs = int(recog_est_time % 60)
    if recog_est_mins > 0:
        recog_time_str = f"{recog_est_mins} min {recog_est_secs} sec"
    else:
        recog_time_str = f"{recog_est_secs} sec"

    # Create example/practice image (not in the actual pool)
    # Use a distinctive pattern that's clearly different from pool images
    example_y_pos = -100  # Centered between top text (280) and bottom text (-320)
    example_circle = visual.Circle(win, radius=60, fillColor='white', lineColor='black', lineWidth=3, pos=(0, example_y_pos))
    example_line = visual.Rect(win, width=int(10 * scale_x), height=int(100 * scale_avg), fillColor='black', lineColor='black', pos=(0, example_y_pos))
    example_border = visual.Rect(win, width=int(150 * scale_x), height=int(150 * scale_avg), lineColor='green', lineWidth=6, fillColor=None, pos=(0, example_y_pos))
    example_selected = False
    
    # Create mouse for example
    example_mouse = event.Mouse(visible=True, win=win)
    
    # Show instruction screen with interactive example
    recognition_instruction = visual.TextStim(
        win=win,
        text=(
            "=== MEMORY SET 1 - RECOGNITION TEST ===\n\n"
            f"You will see {MEMORY_POOL_SIZE} images in a grid.\n"
            f"Select the {MEMORY_SET_1_SIZE} images you saw earlier.\n\n"
            "Click to select/deselect. Selected images have a green border.\n\n"
            "TRY THE EXAMPLE BELOW:"
        ),
        color='white',
        height=int(38 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(260 * scale_y))  # Moved up slightly from 280
    )
    
    instruction_bottom = visual.TextStim(
        win=win,
        text=(
            f"Select exactly {MEMORY_SET_1_SIZE} images, then press SPACE.\n"
            f"Estimated time: ~{recog_time_str} (user-paced)"
        ),
        color='white',
        height=int(36 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(-380 * scale_y))  # Moved down from -320 for more space
    )
    
    continue_instr_bottom = visual.TextStim(
        win=win,
        text='Press SPACE to begin test',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr_bottom = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    print("Showing interactive example - waiting for SPACE to start test...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    last_click_time = 0
    
    while waiting:
        # Check for spacebar to continue
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        
        # Check for mouse clicks on example image and instructions
        if example_mouse.getPressed()[0]:
            mouse_pos = example_mouse.getPos()
            current_time_mem = core.getTime()
            
            # Check if clicked on SPACE or ESC instructions first
            if is_text_clicked(continue_instr_bottom, example_mouse):
                print("User clicked BEGIN TEST")
                waiting = False
                core.wait(0.3)
                continue  # Skip rest of mouse checking
            
            if is_text_clicked(quit_instr_bottom, example_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
            
            # Debounce clicks (0.2 second delay)
            if current_time_mem - last_click_time > 0.2:
                # Check if click is on example image (centered at 0,0)
                if abs(mouse_pos[0]) < (75 * scale_x) and abs(mouse_pos[1] - example_y_pos) < 75:
                    example_selected = not example_selected
                    last_click_time = current_time_mem
        
        # Draw everything
        recognition_instruction.draw()
        
        # Draw example image at center
        example_circle.draw()
        example_line.draw()
        
        # Draw selection border if selected
        if example_selected:
            example_border.draw()
        
        instruction_bottom.draw()
        continue_instr_bottom.draw()
        quit_instr_bottom.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        core.wait(0.01)

    # Clear events
    event.clearEvents()
    core.wait(0.3)

    # Recognition test
    print("Starting Memory Set 1 - Recognition Test Iteration 1...")

    # Reset all image element positions to (0,0) before grid placement
    for img in all_memory_images:
        for element in img['elements']:
            element.pos = (0, 0)

    # Reset selection status and tracking
    for img in all_memory_images:
        img['selected'] = False
        img['ever_selected'] = False
        img['click_count'] = 0

    total_clicks = 0
    
    # Create randomized display order (shuffle indices)
    display_order = list(range(MEMORY_POOL_SIZE))
    random.shuffle(display_order)
    print(f"Images randomized for display")

    # Update instruction text for Memory Set 1
    instruction_display.text = f"Click to select {MEMORY_SET_1_SIZE} images. Press SPACE when done. (ESC to quit)"

    recognition_complete = False

    while not recognition_complete:
        # Keep mouse always visible during recognition test
        update_mouse_visibility(mouse, auto_hide=False)
        
        # Draw all images in grid (using randomized order)
        for display_idx in range(len(display_order)):
            img_idx = display_order[display_idx]
            img = all_memory_images[img_idx]
            
            row = display_idx // grid_cols
            col = display_idx % grid_cols
            x_pos = start_x + col * image_spacing
            y_pos = start_y - row * image_spacing
            
            # Draw image elements at grid position
            for element in img['elements']:
                element.pos = (x_pos, y_pos)
                element.draw()
            
            # Draw selection border if selected
            if img['selected']:
                selection_border.pos = (x_pos, y_pos)
                selection_border.draw()
        
        # Update counter
        num_selected = sum(1 for img in all_memory_images if img['selected'])
        if num_selected == MEMORY_SET_1_SIZE:
            counter_text.text = f"Selected: {num_selected} / {MEMORY_SET_1_SIZE} - Press SPACE to continue"
            counter_text.color = 'green'
        else:
            counter_text.text = f"Selected: {num_selected} / {MEMORY_SET_1_SIZE}"
            counter_text.color = 'white'
        
        instruction_display.draw()
        counter_text.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        # Check for mouse clicks
        if mouse.getPressed()[0]:  # Left click
            mouse_pos = mouse.getPos()
            
            # First check if clicking on counter text to continue (when all selected)
            if num_selected == MEMORY_SET_1_SIZE:
                if is_text_clicked(counter_text, mouse):
                    print("User clicked CONTINUE (all shapes selected)")
                    recognition_complete = True
                    core.wait(0.3)  # Debounce
                    continue  # Skip image checking
            
            # Check which image was clicked (using randomized positions)
            for display_idx in range(len(display_order)):
                img_idx = display_order[display_idx]
                img = all_memory_images[img_idx]
                
                row = display_idx // grid_cols
                col = display_idx % grid_cols
                x_pos = start_x + col * image_spacing
                y_pos = start_y - row * image_spacing
                
                # Check if click is within image bounds
                if (abs(mouse_pos[0] - x_pos) < (70 * scale_x) and 
                    abs(mouse_pos[1] - y_pos) < 70):
                    img['selected'] = not img['selected']
                    if img['selected']:
                        img['ever_selected'] = True
                    img['click_count'] += 1
                    total_clicks += 1
                    core.wait(0.2)  # Debounce
                    break
        
        # Check for spacebar to finish
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys and num_selected == MEMORY_SET_1_SIZE:
            recognition_complete = True
        elif 'escape' in keys:
            win.close()
            core.quit()
        
        core.wait(0.01)

    # Record results
    memory_set_1_test_1_selected = [img['id'] for img in all_memory_images if img['selected']]
    memory_set_1_test_1_correct = [img_id for img_id in memory_set_1_test_1_selected 
                                    if img_id in memory_set_1_indices]
    memory_set_1_test_1_accuracy = len(memory_set_1_test_1_correct) / MEMORY_SET_1_SIZE * 100 if MEMORY_SET_1_SIZE > 0 else 0.0

    # SAVE ITERATION 1 STATE FOR EXCEL (before iteration 2 overwrites it!)
    memory_set_1_test_1_state = {}
    for img in all_memory_images:
        if img['id'] in range(MEMORY_SET_1_SIZE):  # Set 1 images only
            memory_set_1_test_1_state[img['id']] = {
                'selected': img['selected'],
                'changed': img['changed'],
                'clicks': img['click_count']
            }
    
    # Calculate detailed statistics
    # Renamed: Correct_Confirmed → Correct_Count, Incorrect_Confirmed → Incorrect_Count
    memory_set_1_test_1_correct_count = len(memory_set_1_test_1_correct)  # Correct selections count
    memory_set_1_test_1_incorrect_count = len(memory_set_1_test_1_selected) - memory_set_1_test_1_correct_count  # Incorrect selections count
    
    # Correct images clicked once (not changed)
    memory_set_1_test_1_correct_not_changed = sum(1 for img in all_memory_images 
                                                    if img['id'] in memory_set_1_indices 
                                                    and img['selected'] 
                                                    and img['click_count'] == 1)
    
    # Correct images clicked multiple times (changed)
    memory_set_1_test_1_correct_changed = sum(1 for img in all_memory_images 
                                               if img['id'] in memory_set_1_indices 
                                               and img['selected'] 
                                               and img['click_count'] > 1)

    # Incorrect images clicked once (not changed)
    memory_set_1_test_1_incorrect_not_changed = sum(1 for img in all_memory_images 
                                                     if img['id'] not in memory_set_1_indices 
                                                     and img['selected'] 
                                                     and img['click_count'] == 1)
    
    # Incorrect images clicked multiple times (changed)
    memory_set_1_test_1_incorrect_changed = sum(1 for img in all_memory_images 
                                                 if img['id'] not in memory_set_1_indices 
                                                 and img['selected'] 
                                                 and img['click_count'] > 1)
    
    # Total clicks on correct images (whether selected or not)
    memory_set_1_test_1_clicks_on_correct = sum(img['click_count'] for img in all_memory_images 
                                                 if img['id'] in memory_set_1_indices)
    
    # Total clicks on incorrect images (whether selected or not)
    memory_set_1_test_1_clicks_on_incorrect = sum(img['click_count'] for img in all_memory_images 
                                                   if img['id'] not in memory_set_1_indices)

    memory_set_1_test_1_total_clicks = total_clicks

    print(f"Memory Set 1 - Recognition Test Iteration 1 complete")
    print(f"Accuracy: {memory_set_1_test_1_accuracy:.1f}% ({memory_set_1_test_1_correct_count}/{MEMORY_SET_1_SIZE})")
    print(f"Total clicks: {memory_set_1_test_1_total_clicks}")
    
    # Mark Memory Set 1 Recognition 1 as completed
    test_sections[2]['completed'] = True
    current_section = 3  # Move to Memory Set 2 Study

# Update current_section for Memory Test 2 if Memory Test 1 was skipped
if not RUN_MEMORY_TEST_1 and RUN_MEMORY_TEST_2:
    # Memory Test 1 was skipped, so current_section is still -1
    # Set it to 3 (Memory Set 2 Study position in test_sections array)
    current_section = 3
    print(f"Memory Test 1 skipped - setting current_section to {current_section} for Memory Test 2")

# ===== STEP 12: MEMORY TEST 2 - STUDY PHASE INSTRUCTIONS =====
if RUN_MEMORY_TEST_2:
    print("\n" + "=" * 80)
    print("STEP 12: MEMORY TEST 2 - STUDY PHASE INSTRUCTIONS")
    print("=" * 80)
else:
    print("\n" + "=" * 80)
    print("STEP 12: MEMORY TEST 2 - STUDY PHASE INSTRUCTIONS SKIPPED")
    print("=" * 80)

if RUN_MEMORY_TEST_2:
    # Clear screen and wait
    copyright_text_small.draw()
    win.flip()
    core.wait(0.5)

    # Clear any lingering events
    event.clearEvents()
    core.wait(0.5)

    # Show instruction screen
    memory_2_instruction = visual.TextStim(
        win=win,
        text=(
            "=== MEMORY SET 2 - STUDY PHASE ===\n\n"
            f"You will now see {MEMORY_SET_2_SIZE} NEW unique images.\n\n"
            f"You will have {format_time_estimate(MEMORY_SET_2_STUDY_TIME)} to memorize these images.\n\n"
            "These are DIFFERENT images from Memory Set 1.\n\n"
            "Try to remember as many details as possible:\n"
            "- Shape\n"
            "- Color\n"
            "- Pattern\n\n"
            "Later, you will be asked to identify these images\n"
            "from the same pool of 30 images."
        ),
        color='white',
        height=int(42 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to begin studying',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    memory_2_instruction.draw()
    continue_instr.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()

    # Wait for spacebar
    print("Waiting for SPACE to start Memory Test 2 study phase...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        # Check for mouse clicks on instruction text
        if current_time - last_click_time > 0.3:
            if is_text_clicked(continue_instr, global_mouse):
                print("User clicked CONTINUE")
                waiting = False
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(quit_instr, global_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
        
        core.wait(0.01)

    # Clear events
    event.clearEvents()
    core.wait(0.3)

    # ===== STEP 13: MEMORY TEST 2 - REMEMBERING PERIOD =====
    print("\n" + "=" * 80)
    print(f"STEP 13: MEMORY TEST 2 - REMEMBERING PERIOD ({MEMORY_SET_2_SIZE} different images, {int(MEMORY_SET_2_STUDY_TIME/60)} minutes)")
    print("=" * 80)

    # Display all Memory Set 2 images at once for study period
    study_start = core.getTime()

    # Calculate optimal grid layout for Memory Set 2
    if MEMORY_SET_2_SIZE == 0:
        study_2_grid_cols = 1
        study_2_grid_rows = 0
    else:
        # Use 5 columns as standard, calculate rows needed
        study_2_grid_cols = min(5, MEMORY_SET_2_SIZE)  # Use fewer columns if less than 5 images
        study_2_grid_rows = (MEMORY_SET_2_SIZE + study_2_grid_cols - 1) // study_2_grid_cols

    study_2_image_spacing = 220
    # Center the grid horizontally
    study_2_start_x = -(study_2_grid_cols - 1) * study_2_image_spacing / 2
    # Center the grid vertically
    study_2_start_y = (study_2_grid_rows - 1) * study_2_image_spacing / 2

    print(f"Displaying all {MEMORY_SET_2_SIZE} Memory Set 2 images simultaneously ({study_2_grid_rows} rows x {study_2_grid_cols} cols) for {MEMORY_SET_2_STUDY_TIME} seconds...")

    while core.getTime() - study_start < MEMORY_SET_2_STUDY_TIME:
        elapsed = core.getTime() - study_start
        time_remaining = MEMORY_SET_2_STUDY_TIME - elapsed
        
        # Update mouse visibility (auto-hide during study)
        update_mouse_visibility(global_mouse, auto_hide=True)
        
        # Update timer
        timer_text.text = f"MEMORY SET 2 - STUDY PHASE\nTime Remaining: {int(time_remaining//60)}:{int(time_remaining%60):02d}"
        
        # Draw all Memory Set 2 images in grid
        for idx, img_data in enumerate(memory_set_2_images):
            row = idx // study_2_grid_cols
            col = idx % study_2_grid_cols
            x_pos = study_2_start_x + col * study_2_image_spacing
            y_pos = study_2_start_y - row * study_2_image_spacing
            
            # Draw image elements at grid position
            for element in img_data['elements']:
                element.pos = (x_pos, y_pos)
                element.draw()
        
        timer_text.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        # Check for escape
        keys = event.getKeys(['escape'])
        if 'escape' in keys:
            win.close()
            core.quit()
        
        core.wait(0.01)

    print("Memory Set 2 study phase complete")

    # Mark Memory Set 2 Study as completed
    test_sections[3]['completed'] = True
    current_section = 4  # Move to Audio Reaction Test

    # Show transition message
    transition_text_2 = visual.TextStim(
        win=win,
        text="Memory Set 2 study complete!\n\nMoving to Audio Reaction Test...",
        color='green',
        height=int(48 * scale_avg),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-450 * scale_y)),
        bold=True
    )
    
    transition_text_2.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()

    # Wait 2 seconds but allow ESC
    transition_start = core.getTime()
    while core.getTime() - transition_start < 2.0:
        keys = event.getKeys(['escape'])
        if 'escape' in keys:
            win.close()
            core.quit()
        core.wait(0.01)
else:
    print("\n" + "=" * 80)
    print("STEP 13: MEMORY TEST 2 - REMEMBERING PERIOD SKIPPED")
    print("=" * 80)
    
    # Skip Memory Set 2 sections in progress
    if current_section < 4:
        current_section = 4  # Skip to Audio RT
    
    # Show skip screen
    skip_screen = visual.TextStim(
        win=win,
        text=(
            "=== MEMORY SET 2 ===\n\n"
            "This test has been skipped.\n\n"
            "RUN_MEMORY_TEST_2 is set to False.\n\n"
            "Memory Set 2 study and recognition test will not run."
        ),
        color='yellow',
        height=int(48 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to continue',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to exit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    skip_screen.draw()
    continue_instr.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    print("Memory Test 2 skipped - waiting for user input...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        # Check for mouse clicks on instruction text
        if current_time - last_click_time > 0.3:
            if is_text_clicked(continue_instr, global_mouse):
                print("User clicked CONTINUE")
                waiting = False
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(quit_instr, global_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
        
        core.wait(0.01)

# ===== STEP 14: AUDIO REACTION TEST - INSTRUCTIONS =====
print("\n" + "=" * 80)
if RUN_AUDIO_TEST:
    print("STEP 14: AUDIO REACTION TEST INSTRUCTIONS")
else:
    print("STEP 14: AUDIO REACTION TEST SKIPPED")
print("=" * 80)

if RUN_AUDIO_TEST:
    # Clear screen and wait - PREVENT KEY CARRYOVER
    copyright_text_small.draw()
    win.flip()
    event.clearEvents()  # Clear any lingering key presses
    core.wait(1.0)  # Longer delay to prevent accidental advancement
    event.clearEvents()  # Clear again after wait
    
    # Clear any lingering events
    event.clearEvents()
    core.wait(0.5)
    
    # Calculate estimated time
    avg_interval = (INTERVAL_MIN + INTERVAL_MAX) / 2
    audio_est_time = PRE_EXPERIMENT_DELAY + (NUM_ITERATIONS * avg_interval)
    audio_est_mins = int(audio_est_time // 60)
    audio_est_secs = int(audio_est_time % 60)
    if audio_est_mins > 0:
        audio_time_str = f"{audio_est_mins} min {audio_est_secs} sec"
    else:
        audio_time_str = f"{audio_est_secs} sec"
    
    # Show comprehensive instruction screen for audio test
    audio_instruction_top = visual.TextStim(
        win=win,
        text=(
            "=== AUDIO REACTION TEST ===\n\n"
            "You will now begin the audio reaction time test.\n\n"
            "REACT TO THE RANDOMLY OCCURRING AUDIO\n\n"
            "Task: Press the SPACE BAR as quickly as possible\n"
            "when you hear the beep sound.\n\n"
            "Listen to the sound:"
        ),
        color='white',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(280 * scale_y)),
        wrapWidth=int(5070 * scale_x)
    )
    
    # Center instruction for playing sound (replaces the square in visual test)
    play_sound_center = visual.TextStim(
        win=win,
        text='Press K to play sound',
        color='yellow',
        height=int(40 * scale_avg),
        pos=(int(0 * scale_x), int(50 * scale_y)),
        bold=True
    )
    
    audio_instruction_bottom = visual.TextStim(
        win=win,
        text=(
            f"Number of test trials: {NUM_ITERATIONS}\n"
            f"Interval between sounds: {INTERVAL_MIN}-{INTERVAL_MAX} seconds\n"
            f"Delay before first sound: {PRE_EXPERIMENT_DELAY} seconds (system initialization)\n"
            f"Estimated time: ~{audio_time_str}"
        ),
        color='white',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-120 * scale_y)),
        wrapWidth=int(5070 * scale_x)
    )
    
    audio_instruction_bottom2 = visual.TextStim(
        win=win,
        text=(
            "There will be a silent delay before the first sound plays.\n"
            "This allows the system to initialize and ensures accurate timing."
        ),
        color='white',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-220 * scale_y)),
        wrapWidth=int(5070 * scale_x)
    )
    
    warning_text_audio = visual.TextStim(
        win=win,
        text=(
            "IMPORTANT: If you DO NOT hear an audio beep, DO NOT press SPACE.\n"
            "Only press SPACE when reacting to the actual audio beep stimulus."
        ),
        color='yellow',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-340 * scale_y)),
        wrapWidth=int(5070 * scale_x),
        bold=True
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE when ready to begin',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-700 * scale_y)),
        bold=True,
        wrapWidth=int(600 * scale_x)
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-700 * scale_y)),
        bold=True
    )
    
    # Play sound repeatedly until space is pressed
    print("Playing audio example continuously (press SPACE to continue)...")
    
    waiting_for_start = True
    beep_continuous.play()  # Start continuous loop
    
    while waiting_for_start:
        # Draw instructions
        audio_instruction_top.draw()
        play_sound_center.draw()
        audio_instruction_bottom.draw()
        audio_instruction_bottom2.draw()
        warning_text_audio.draw()
        continue_instr.draw()
        quit_instr.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        # Check for key presses (including k)
        keys = event.getKeys(['space', 'escape', 'k'])
        if 'space' in keys:
            beep_continuous.stop()  # Stop the continuous sound
            waiting_for_start = False
        elif 'k' in keys:
            # Replay the sound when 'k' is pressed
            beep_continuous.stop()
            beep_continuous.play()
        elif 'escape' in keys:
            beep_continuous.stop()
            win.close()
            core.quit()
        
        # Removed core.wait as it was causing the delay issues
    
    # IMMEDIATELY clear screen to black
    event.clearEvents()
    copyright_text_small.draw()
    win.flip()
    core.wait(0.1)

    # ===== STEP 15: AUDIO REACTION TEST =====
    print("\n" + "=" * 80)
    print("STEP 15: AUDIO REACTION TEST")
    print("=" * 80)
    
    print(f"Black screen delay: {PRE_EXPERIMENT_DELAY} seconds...")
    
    # Log delay section start
    log_section_boundary(performance_log, 'Audio Test - Pre-Delay', 'START', experiment_start_time)
    
    # Black screen delay - MINIMAL LOOP
    delay_start = core.getTime()
    target_delay_end = delay_start + PRE_EXPERIMENT_DELAY
    
    while core.getTime() < target_delay_end:
        copyright_text_small.draw()
        win.flip()
        frame_time = core.getTime()
        
        # Log frame with section info
        performance_log['frame_log'].append({
            'timestamp': frame_time - experiment_start_time,
            'frame_time': (frame_time - experiment_frame_times[-1]) * 1000 if experiment_frame_times else 0,
            'section': 'Audio Test - Pre-Delay',
            'events': []
        })
        
        # Check for dropped frames BEFORE appending
        if len(experiment_frame_times) > 0:
            frame_duration = frame_time - experiment_frame_times[-1]
            if frame_duration > (refresh_rate * 1.5):
                experiment_dropped_frames += 1
        
        experiment_frame_times.append(frame_time)
    
    # Log delay section end
    log_section_boundary(performance_log, 'Audio Test - Pre-Delay', 'END', experiment_start_time)
    
    print("Starting audio reaction test trials...")
    
    # Log section start
    log_section_boundary(performance_log, 'Audio Reaction Test', 'START', experiment_start_time)
    
    # Audio test main loop
    for trial in range(1, NUM_ITERATIONS + 1):
        trial_dropped_frames = 0
        trial_misclicks = 0
        
        # Wait random interval before playing sound
        interval = random.uniform(INTERVAL_MIN, INTERVAL_MAX)
        
        # Wait interval - OPTIMIZED MINIMAL LOOP (defer logging until after trial)
        interval_start = core.getTime()
        target_interval_end = interval_start + interval
        trial_frame_times = []  # Collect timestamps for post-trial processing
        
        while core.getTime() < target_interval_end:
            copyright_text_small.draw()
            win.flip()
            trial_frame_times.append(core.getTime())
        
        # Clear any previous key presses
        event.clearEvents()
        
        # Play continuous looping sound until user responds
        beep_continuous.play()
        trial_start = core.getTime()
        sound_start_time = trial_start  # Track when sound started for manual restart
        
        # Log audio stimulus
        log_performance_event(performance_log, 'AUDIO_STIMULUS', 
                             f'Audio beep played (Trial {trial})', 
                             experiment_start_time)
        
        # Track frame
        if len(experiment_frame_times) > 0:
            frame_duration = trial_start - experiment_frame_times[-1]
            if frame_duration > (refresh_rate * 1.5):
                experiment_dropped_frames += 1
                trial_dropped_frames += 1
        experiment_frame_times.append(trial_start)
        
        # Log frame for audio stimulus
        performance_log['frame_log'].append({
            'timestamp': trial_start - experiment_start_time,
            'frame_time': (trial_start - experiment_frame_times[-2]) * 1000 if len(experiment_frame_times) > 1 else 0,
            'section': f'Audio Test - Trial {trial} (Stimulus)',
            'events': ['AUDIO_PLAYED']
        })
        
        # Wait for response - MINIMAL LOOP with deferred logging
        response_made = False
        correct_reaction_time = 0
        key_press_times = []
        last_event_time = trial_start
        response_frame_time = 0  # Store frame time at moment of response
        
        # Deferred logging: Just collect timestamps during measurement
        frame_timestamp_buffer = []
        
        while not response_made:
            keys = event.getKeys(timeStamped=True)
            
            # CRITICAL: Manually restart sound if it's been playing for >1.9 seconds
            # This ensures continuous audio even if loops=-1 doesn't work properly
            current_time = core.getTime()
            if current_time - sound_start_time >= 1.9:  # Restart slightly before 2.0s duration
                beep_continuous.play()
                sound_start_time = current_time
            
            for key, timestamp in keys:
                if key == 'space':
                    # Correct response - STOP SOUND IMMEDIATELY
                    beep_continuous.stop()
                    interval = (timestamp - last_event_time) * 1000
                    key_press_times.append(interval)
                    correct_reaction_time = (timestamp - trial_start) * 1000
                    
                    # Capture the most recent frame time (frame immediately before response)
                    if len(experiment_frame_times) > 1:
                        response_frame_time = (experiment_frame_times[-1] - experiment_frame_times[-2]) * 1000
                    
                    response_made = True
                    # Log response event
                    log_performance_event(performance_log, 'USER_RESPONSE', 
                                         f'Space pressed (Trial {trial}, RT: {correct_reaction_time:.0f}ms)', 
                                         experiment_start_time)
                    event.clearEvents()
                    break
                elif key == 'escape':
                    beep_continuous.stop()
                    win.close()
                    core.quit()
                else:
                    # Incorrect key press - DO NOT STOP SOUND, let it continue
                    interval = (timestamp - last_event_time) * 1000
                    key_press_times.append(interval)
                    last_event_time = timestamp
                    trial_misclicks += 1
                    # Sound keeps playing until correct response
            
            # Keep black screen displayed - MINIMAL OVERHEAD
            current_frame_time = core.getTime()
            
            # DEFERRED: Just collect timestamp (fast!)
            frame_timestamp_buffer.append((current_frame_time, trial))
            
            # Check for dropped frames
            if len(experiment_frame_times) > 0:
                frame_duration = current_frame_time - experiment_frame_times[-1]
                if frame_duration > (refresh_rate * 1.5):
                    experiment_dropped_frames += 1
                    trial_dropped_frames += 1
            
            experiment_frame_times.append(current_frame_time)
            
            copyright_text_small.draw()
            win.flip()
        
        # PROCESS DEFERRED LOGS (after response collected)
        for frame_time, trial_num in frame_timestamp_buffer:
            if len(experiment_frame_times) > 0:
                frame_idx = experiment_frame_times.index(frame_time) if frame_time in experiment_frame_times else -1
                if frame_idx > 0:
                    frame_duration_ms = (experiment_frame_times[frame_idx] - experiment_frame_times[frame_idx-1]) * 1000
                else:
                    frame_duration_ms = 0
                
                performance_log['frame_log'].append({
                    'timestamp': frame_time - experiment_start_time,
                    'frame_time': frame_duration_ms,
                    'section': f'Audio Test - Trial {trial_num} (Response)',
                    'events': []
                })
        
        # DEFERRED PROCESSING - Process timestamps collected during waiting period
        # This adds zero overhead to the measurement loop
        trial_dropped_frames = 0
        for i, frame_time in enumerate(trial_frame_times):
            # Add to experiment frame times
            experiment_frame_times.append(frame_time)
            
            # Create performance log entry
            performance_log['frame_log'].append({
                'timestamp': frame_time - experiment_start_time,
                'frame_time': (frame_time - experiment_frame_times[-2]) * 1000 if len(experiment_frame_times) > 1 else 0,
                'section': 'Audio Test - Waiting',
                'events': []
            })
            
            # Check for dropped frames
            if len(experiment_frame_times) > 1:
                frame_duration = frame_time - experiment_frame_times[-2]
                if frame_duration > (refresh_rate * 1.5):
                    experiment_dropped_frames += 1
                    trial_dropped_frames += 1
        
        # Format interval times
        interval_list = ",".join([f"{t:.0f}" for t in key_press_times])
        
        # Store trial result
        audio_results.append({
            'trial': trial,
            'reaction_time': correct_reaction_time,
            'response_frame_time': response_frame_time,  # Frame time at moment of response
            'misclicks': trial_misclicks,
            'intervals': interval_list,
            'frame_drops': trial_dropped_frames
        })
        
        print(f"Audio test trial {trial}/{NUM_ITERATIONS} complete: {correct_reaction_time:.0f}ms")

    print("Audio reaction test complete")
    
    # Log section end
    log_section_boundary(performance_log, 'Audio Reaction Test', 'END', experiment_start_time)
    
    # Mark Audio Reaction Test as completed
    test_sections[4]['completed'] = True
    
    # PREVENT ACCIDENTAL SKIP after Audio RT (ensures user reads next test instructions)
    print("\n" + "=" * 80)
    print("INSTRUCTION CONFIRMATION AFTER AUDIO RT")
    print("=" * 80)
    
    confirm_text = visual.TextStim(
        win=win,
        text=(
            "Audio Reaction Time test complete.\n\n"
            "NEXT TEST:\n"
            "You will now see a Memory Recognition test.\n\n"
            "Read the instructions on the next screen carefully.\n\n"
            "Press K when ready to continue."
        ),
        color='yellow',
        height=int(42 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(0 * scale_y))
    )
    
    confirm_continue = visual.TextStim(
        win=win,
        text='Press K to continue',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(0 * scale_x), int(-400 * scale_y)),
        bold=True
    )
    
    confirm_text.draw()
    confirm_continue.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    # Wait for K - prevents accidental click-through (K less likely to be pressed accidentally than SPACE)
    event.clearEvents()
    core.wait(0.5)  # Extra delay to prevent immediate click-through
    event.clearEvents()
    
    waiting_confirm = True
    while waiting_confirm:
        keys = event.getKeys(['k', 'escape'])
        if 'k' in keys:
            print("User pressed K - continuing to Memory Test 2 Iteration 1")
            waiting_confirm = False
        elif 'escape' in keys:
            win.close()
            sys.exit(0)
        core.wait(0.01)
    
    current_section = 5  # Move to Memory Set 2 Recognition 1
else:
    # Audio test skipped - advance section appropriately
    if current_section < 5:
        current_section = 5  # Skip to Memory 2 Recognition (or further if Memory 2 also skipped)
    
    # Show skip screen
    print("\n" + "=" * 80)
    print("STEP 15: AUDIO REACTION TEST SKIPPED")
    print("=" * 80)
    
    skip_screen = visual.TextStim(
        win=win,
        text=(
            "=== AUDIO REACTION TEST ===\n\n"
            "This test has been skipped.\n\n"
            "RUN_AUDIO_TEST is set to False."
        ),
        color='yellow',
        height=int(48 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to continue',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to exit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    skip_screen.draw()
    continue_instr.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    print("Audio reaction test skipped - waiting for user input...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        # Check for mouse clicks on instruction text
        if current_time - last_click_time > 0.3:
            if is_text_clicked(continue_instr, global_mouse):
                print("User clicked CONTINUE")
                waiting = False
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(quit_instr, global_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
        
        core.wait(0.01)

# ===== STEP 16: MEMORY SET 2 - RECOGNITION TEST ITERATION 1 =====
if RUN_MEMORY_TEST_2:
    print("\n" + "=" * 80)
    print("STEP 16: MEMORY SET 2 - RECOGNITION TEST ITERATION 1")
    print("=" * 80)
else:
    print("\n" + "=" * 80)
    print("STEP 16: MEMORY SET 2 - RECOGNITION TEST ITERATION 1 SKIPPED")
    print("=" * 80)
    
    # Update current_section for progress bar
    if current_section < 6:
        current_section = 6  # Move to Memory Set 1 Recognition 2

# Initialize default values for when test is skipped
memory_set_2_test_1_selected = []
memory_set_2_test_1_correct = []  # Keep as list for sorted() in file output
memory_set_2_test_1_correct_count = 0  # Count for table
memory_set_2_test_1_incorrect_count = 0  # Count for table
memory_set_2_test_1_accuracy = 0.0
memory_set_2_test_1_correct_not_changed = 0
memory_set_2_test_1_correct_changed = 0
memory_set_2_test_1_incorrect_not_changed = 0
memory_set_2_test_1_incorrect_changed = 0
memory_set_2_test_1_clicks_on_correct = 0
memory_set_2_test_1_clicks_on_incorrect = 0
memory_set_2_test_1_total_clicks = 0

if RUN_MEMORY_TEST_2:
    # Clear screen and wait
    copyright_text_small.draw()
    win.flip()
    core.wait(0.5)

    # Clear any lingering events
    event.clearEvents()
    core.wait(0.5)

    # Calculate estimated time for recognition test (user-paced)
    # Formula: Each shape takes 15 seconds to remember + 5 seconds to select = 20 seconds
    recog_2_est_time = MEMORY_SET_2_SIZE * 20
    recog_2_est_mins = int(recog_2_est_time // 60)
    recog_2_est_secs = int(recog_2_est_time % 60)
    if recog_2_est_mins > 0:
        recog_2_time_str = f"{recog_2_est_mins} min {recog_2_est_secs} sec"
    else:
        recog_2_time_str = f"{recog_2_est_secs} sec"

    # Create example/practice image (not in the actual pool)
    # Use a distinctive pattern that's clearly different from pool images
    example_y_pos = -100  # Centered between instructions
    example_circle = visual.Circle(win, radius=60, fillColor='white', lineColor='black', lineWidth=3, pos=(0, example_y_pos))
    example_line = visual.Rect(win, width=int(10 * scale_x), height=int(100 * scale_avg), fillColor='black', lineColor='black', pos=(0, example_y_pos))
    example_border = visual.Rect(win, width=int(150 * scale_x), height=int(150 * scale_avg), lineColor='green', lineWidth=6, fillColor=None, pos=(0, example_y_pos))
    example_selected = False
    
    # Create mouse for example
    example_mouse = event.Mouse(visible=True, win=win)
    
    # Show instruction screen with interactive example
    recognition_2_instruction = visual.TextStim(
        win=win,
        text=(
            "=== MEMORY SET 2 - RECOGNITION TEST ===\n\n"
            f"You will see {MEMORY_POOL_SIZE} images in a grid.\n"
            f"Select the {MEMORY_SET_2_SIZE} images from MEMORY SET 2.\n\n"
            "Click to select/deselect. Green border = selected.\n\n"
            "TRY THE EXAMPLE BELOW:"
        ),
        color='white',
        height=int(38 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(260 * scale_y))
    )
    
    instruction_bottom = visual.TextStim(
        win=win,
        text=(
            f"Select exactly {MEMORY_SET_2_SIZE} images, then press SPACE.\n"
            f"Estimated time: ~{recog_2_time_str} (user-paced)"
        ),
        color='white',
        height=int(36 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(-380 * scale_y))
    )
    
    continue_instr_bottom = visual.TextStim(
        win=win,
        text='Press SPACE to begin test',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr_bottom = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    print("Showing interactive example - waiting for SPACE to start test...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    last_click_time = 0
    
    while waiting:
        # Check for spacebar to continue
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        
        # Check for mouse clicks on example image and instructions
        if example_mouse.getPressed()[0]:
            mouse_pos = example_mouse.getPos()
            current_time_mem = core.getTime()
            
            # Check if clicked on SPACE or ESC instructions first
            if is_text_clicked(continue_instr_bottom, example_mouse):
                print("User clicked BEGIN TEST")
                waiting = False
                core.wait(0.3)
                continue  # Skip rest of mouse checking
            
            if is_text_clicked(quit_instr_bottom, example_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
            
            # Debounce clicks (0.2 second delay)
            if current_time_mem - last_click_time > 0.2:
                # Check if click is on example image (centered at 0,0)
                if abs(mouse_pos[0]) < (75 * scale_x) and abs(mouse_pos[1] - example_y_pos) < 75:
                    example_selected = not example_selected
                    last_click_time = current_time_mem
        
        # Draw everything
        recognition_2_instruction.draw()
        
        # Draw example image at center
        example_circle.draw()
        example_line.draw()
        
        # Draw selection border if selected
        if example_selected:
            example_border.draw()
        
        instruction_bottom.draw()
        continue_instr_bottom.draw()
        quit_instr_bottom.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        core.wait(0.01)

    # Clear events
    event.clearEvents()
    core.wait(0.3)

    # Recognition test for Memory Set 2
    print("Starting Memory Set 2 - Recognition Test Iteration 1...")

    # Make mouse visible for recognition test
    mouse.setVisible(True)

    # Reset all image element positions to (0,0) before grid placement
    for img in all_memory_images:
        for element in img['elements']:
            element.pos = (0, 0)

    # Reset selection status and tracking
    for img in all_memory_images:
        img['selected'] = False
        img['ever_selected'] = False
        img['click_count'] = 0

    total_clicks = 0

    # CREATE NEW RANDOMIZED DISPLAY ORDER FOR MEMORY SET 2
    display_order_set2 = list(range(MEMORY_POOL_SIZE))
    random.shuffle(display_order_set2)
    print(f"Images randomized for Memory Set 2 recognition test")

    # Grid layout already calculated from first recognition test (same pool size)
    print(f"Recognition grid: {grid_rows} rows x {grid_cols} cols for {MEMORY_POOL_SIZE} images")

    # Update instruction text for Memory Set 2
    instruction_display.text = f"Click to select {MEMORY_SET_2_SIZE} images. Press SPACE when done. (ESC to quit)"

    recognition_complete = False

    while not recognition_complete:
        # Keep mouse always visible during recognition test
        update_mouse_visibility(mouse, auto_hide=False)
        
        # Draw all images in grid (using randomized order)
        for display_idx in range(len(display_order_set2)):
            img_idx = display_order_set2[display_idx]
            img = all_memory_images[img_idx]
            
            row = display_idx // grid_cols
            col = display_idx % grid_cols
            x_pos = start_x + col * image_spacing
            y_pos = start_y - row * image_spacing
            
            # Draw image elements at grid position
            for element in img['elements']:
                element.pos = (x_pos, y_pos)
                element.draw()
            
            # Draw selection border if selected
            if img['selected']:
                selection_border.pos = (x_pos, y_pos)
                selection_border.draw()
        
        # Update counter
        num_selected = sum(1 for img in all_memory_images if img['selected'])
        if num_selected == MEMORY_SET_2_SIZE:
            counter_text.text = f"Selected: {num_selected} / {MEMORY_SET_2_SIZE} - Press SPACE to continue"
            counter_text.color = 'green'
        else:
            counter_text.text = f"Selected: {num_selected} / {MEMORY_SET_2_SIZE}"
            counter_text.color = 'white'
        
        instruction_display.draw()
        counter_text.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        # Check for mouse clicks
        if mouse.getPressed()[0]:  # Left click
            mouse_pos = mouse.getPos()
            
            # First check if clicking on counter text to continue (when all selected)
            if num_selected == MEMORY_SET_2_SIZE:
                if is_text_clicked(counter_text, mouse):
                    print("User clicked CONTINUE (all shapes selected)")
                    recognition_complete = True
                    core.wait(0.3)  # Debounce
                    continue  # Skip image checking
            
            # Check which image was clicked (using randomized positions)
            for display_idx in range(len(display_order_set2)):
                img_idx = display_order_set2[display_idx]
                img = all_memory_images[img_idx]
                
                row = display_idx // grid_cols
                col = display_idx % grid_cols
                x_pos = start_x + col * image_spacing
                y_pos = start_y - row * image_spacing
                
                # Check if click is within image bounds
                if (abs(mouse_pos[0] - x_pos) < (70 * scale_x) and 
                    abs(mouse_pos[1] - y_pos) < 70):
                    img['selected'] = not img['selected']
                    if img['selected']:
                        img['ever_selected'] = True
                    img['click_count'] += 1
                    total_clicks += 1
                    core.wait(0.2)  # Debounce
                    break
        
        # Check for spacebar to finish
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys and num_selected == MEMORY_SET_2_SIZE:
            recognition_complete = True
        elif 'escape' in keys:
            win.close()
            core.quit()
        
        core.wait(0.01)

    # Record results for Memory Set 2 Iteration 1
    memory_set_2_test_1_selected = [img['id'] for img in all_memory_images if img['selected']]
    memory_set_2_test_1_correct = [img_id for img_id in memory_set_2_test_1_selected 
                                    if img_id in memory_set_2_indices]
    memory_set_2_test_1_accuracy = len(memory_set_2_test_1_correct) / MEMORY_SET_2_SIZE * 100 if MEMORY_SET_2_SIZE > 0 else 0.0

    # Calculate detailed statistics
    # Renamed: Correct_Confirmed → Correct_Count, Incorrect_Confirmed → Incorrect_Count
    memory_set_2_test_1_correct_count = len(memory_set_2_test_1_correct)  # Correct selections count
    memory_set_2_test_1_incorrect_count = len(memory_set_2_test_1_selected) - memory_set_2_test_1_correct_count  # Incorrect selections count

    # Correct images clicked once (not changed)
    memory_set_2_test_1_correct_not_changed = sum(1 for img in all_memory_images 
                                                    if img['id'] in memory_set_2_indices 
                                                    and img['selected'] 
                                                    and img['click_count'] == 1)
    
    # Correct images clicked multiple times (changed)
    memory_set_2_test_1_correct_changed = sum(1 for img in all_memory_images 
                                               if img['id'] in memory_set_2_indices 
                                               and img['selected'] 
                                               and img['click_count'] > 1)

    # Incorrect images clicked once (not changed)
    memory_set_2_test_1_incorrect_not_changed = sum(1 for img in all_memory_images 
                                                     if img['id'] not in memory_set_2_indices 
                                                     and img['selected'] 
                                                     and img['click_count'] == 1)
    
    # Incorrect images clicked multiple times (changed)
    memory_set_2_test_1_incorrect_changed = sum(1 for img in all_memory_images 
                                                 if img['id'] not in memory_set_2_indices 
                                                 and img['selected'] 
                                                 and img['click_count'] > 1)
    
    # Total clicks on correct images
    memory_set_2_test_1_clicks_on_correct = sum(img['click_count'] for img in all_memory_images 
                                                 if img['id'] in memory_set_2_indices)
    
    # Total clicks on incorrect images
    memory_set_2_test_1_clicks_on_incorrect = sum(img['click_count'] for img in all_memory_images 
                                                   if img['id'] not in memory_set_2_indices)

    memory_set_2_test_1_total_clicks = total_clicks

    print(f"Memory Set 2 - Recognition Test Iteration 1 complete")
    print(f"Accuracy: {memory_set_2_test_1_accuracy:.1f}% ({memory_set_2_test_1_correct_count}/{MEMORY_SET_2_SIZE})")
    print(f"Total clicks: {memory_set_2_test_1_total_clicks}")
    
    # Mark Memory Set 2 Recognition 1 as completed
    test_sections[5]['completed'] = True
    current_section = 6  # Move to Memory Set 1 Recognition 2

# ===== STEP 17: MEMORY SET 1 - RECOGNITION TEST ITERATION 2 =====
if RUN_MEMORY_TEST_1:
    print("\n" + "=" * 80)
    print("STEP 17: MEMORY SET 1 - RECOGNITION TEST ITERATION 2")
    print("=" * 80)
else:
    print("\n" + "=" * 80)
    print("STEP 17: MEMORY SET 1 - RECOGNITION TEST ITERATION 2 SKIPPED")
    print("=" * 80)
    
    # Show skip screen
    skip_screen = visual.TextStim(
        win=win,
        text=(
            "=== MEMORY SET 1 - RECOGNITION TEST #2 ===\n\n"
            "This test has been skipped.\n\n"
            "RUN_MEMORY_TEST_1 is set to False."
        ),
        color='yellow',
        height=int(48 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(50 * scale_y))
    )
    
    continue_instr = visual.TextStim(
        win=win,
        text='Press SPACE to save data',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr = visual.TextStim(
        win=win,
        text='Press ESC to exit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    skip_screen.draw()
    continue_instr.draw()
    quit_instr.draw()
    copyright_text_small.draw()
    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
    win.flip()
    
    print("Memory Test 1 Iteration 2 skipped - waiting for user input...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        # Check for mouse clicks on instruction text
        if current_time - last_click_time > 0.3:
            if is_text_clicked(continue_instr, global_mouse):
                print("User clicked CONTINUE")
                waiting = False
                last_click_time = current_time
                core.wait(0.2)
            elif is_text_clicked(quit_instr, global_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
        
        core.wait(0.01)

# Initialize default values for when test is skipped
memory_set_1_test_2_selected = []
memory_set_1_test_2_correct = []  # Keep as list for sorted() in file output
memory_set_1_test_2_correct_count = 0  # Count for table
memory_set_1_test_2_incorrect_count = 0  # Count for table
memory_set_1_test_2_accuracy = 0.0
memory_set_1_test_2_correct_not_changed = 0
memory_set_1_test_2_correct_changed = 0
memory_set_1_test_2_incorrect_not_changed = 0
memory_set_1_test_2_incorrect_changed = 0
memory_set_1_test_2_clicks_on_correct = 0
memory_set_1_test_2_clicks_on_incorrect = 0
memory_set_1_test_2_total_clicks = 0

if RUN_MEMORY_TEST_1:
    # Clear screen and wait
    copyright_text_small.draw()
    win.flip()
    core.wait(0.5)

    # Clear any lingering events
    event.clearEvents()
    core.wait(0.5)

    # Calculate estimated time for recognition test iteration 2 (user-paced)
    # Formula: Each shape takes 15 seconds to remember + 5 seconds to select = 20 seconds
    recog_iter2_est_time = MEMORY_SET_1_SIZE * 20
    recog_iter2_est_mins = int(recog_iter2_est_time // 60)
    recog_iter2_est_secs = int(recog_iter2_est_time % 60)
    if recog_iter2_est_mins > 0:
        recog_iter2_time_str = f"{recog_iter2_est_mins} min {recog_iter2_est_secs} sec"
    else:
        recog_iter2_time_str = f"{recog_iter2_est_secs} sec"

    # Create example/practice image (not in the actual pool)
    # Use a distinctive pattern that's clearly different from pool images
    example_y_pos = -100  # Centered between instructions
    example_circle = visual.Circle(win, radius=60, fillColor='white', lineColor='black', lineWidth=3, pos=(0, example_y_pos))
    example_line = visual.Rect(win, width=int(10 * scale_x), height=int(100 * scale_avg), fillColor='black', lineColor='black', pos=(0, example_y_pos))
    example_border = visual.Rect(win, width=int(150 * scale_x), height=int(150 * scale_avg), lineColor='green', lineWidth=6, fillColor=None, pos=(0, example_y_pos))
    example_selected = False
    
    # Create mouse for example
    example_mouse = event.Mouse(visible=True, win=win)
    
    # Show instruction screen with interactive example
    recognition_instruction_2 = visual.TextStim(
        win=win,
        text=(
            "=== MEMORY SET 1 - RECOGNITION TEST #2 ===\n\n"
            f"You will see {MEMORY_POOL_SIZE} images in a grid again.\n"
            f"Select the {MEMORY_SET_1_SIZE} images from Memory Set 1.\n\n"
            "Click to select/deselect. Green border = selected.\n\n"
            "TRY THE EXAMPLE BELOW:"
        ),
        color='white',
        height=int(38 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(260 * scale_y))
    )
    
    instruction_bottom = visual.TextStim(
        win=win,
        text=(
            f"Select exactly {MEMORY_SET_1_SIZE} images, then press SPACE.\n"
            f"Estimated time: ~{recog_iter2_time_str} (user-paced)"
        ),
        color='white',
        height=int(36 * scale_avg),
        wrapWidth=int(5070 * scale_x),
        pos=(int(0 * scale_x), int(-380 * scale_y))
    )
    
    continue_instr_bottom = visual.TextStim(
        win=win,
        text='Press SPACE to begin test',
        color='green',
        height=int(32 * scale_avg),
        pos=(int(-350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    quit_instr_bottom = visual.TextStim(
        win=win,
        text='Press ESC to quit',
        color='red',
        height=int(32 * scale_avg),
        pos=(int(350 * scale_x), int(-650 * scale_y)),
        bold=True
    )
    
    print("Showing interactive example - waiting for SPACE to start test...")
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    last_click_time = 0
    
    while waiting:
        # Check for spacebar to continue
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys:
            waiting = False
        elif 'escape' in keys:
            win.close()
            core.quit()
        
        # Check for mouse clicks on example image and instructions
        if example_mouse.getPressed()[0]:
            mouse_pos = example_mouse.getPos()
            current_time_mem = core.getTime()
            
            # Check if clicked on SPACE or ESC instructions first
            if is_text_clicked(continue_instr_bottom, example_mouse):
                print("User clicked BEGIN TEST")
                waiting = False
                core.wait(0.3)
                continue  # Skip rest of mouse checking
            
            if is_text_clicked(quit_instr_bottom, example_mouse):
                print("User clicked QUIT")
                win.close()
                core.quit()
            
            # Debounce clicks (0.2 second delay)
            if current_time_mem - last_click_time > 0.2:
                # Check if click is on example image (centered at 0,0)
                if abs(mouse_pos[0]) < (75 * scale_x) and abs(mouse_pos[1] - example_y_pos) < 75:
                    example_selected = not example_selected
                    last_click_time = current_time_mem
        
        # Draw everything
        recognition_instruction_2.draw()
        
        # Draw example image at center
        example_circle.draw()
        example_line.draw()
        
        # Draw selection border if selected
        if example_selected:
            example_border.draw()
        
        instruction_bottom.draw()
        continue_instr_bottom.draw()
        quit_instr_bottom.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        core.wait(0.01)

    # Clear events
    event.clearEvents()
    core.wait(0.3)

    # Recognition test #2
    print("Starting Memory Set 1 - Recognition Test Iteration 2...")

    # Make mouse visible for recognition test
    mouse.setVisible(True)

    # Reset all image element positions to (0,0) before grid placement
    for img in all_memory_images:
        for element in img['elements']:
            element.pos = (0, 0)

    # Reset selection status and tracking
    for img in all_memory_images:
        img['selected'] = False
        img['ever_selected'] = False
        img['click_count'] = 0

    total_clicks = 0

    # CREATE NEW RANDOMIZED DISPLAY ORDER FOR ITERATION 2
    display_order_iter2 = list(range(MEMORY_POOL_SIZE))
    random.shuffle(display_order_iter2)
    print(f"Images randomized for Memory Set 1 recognition test iteration 2")

    # Grid layout already calculated from first recognition test (same pool size)
    print(f"Recognition grid: {grid_rows} rows x {grid_cols} cols for {MEMORY_POOL_SIZE} images")

    # Update instruction text for Memory Set 1 Iteration 2
    instruction_display.text = f"Click to select {MEMORY_SET_1_SIZE} images. Press SPACE when done. (ESC to quit)"

    recognition_complete = False

    while not recognition_complete:
        # Keep mouse always visible during recognition test
        update_mouse_visibility(mouse, auto_hide=False)
        
        # Draw all images in grid (using randomized order)
        for display_idx in range(len(display_order_iter2)):
            img_idx = display_order_iter2[display_idx]
            img = all_memory_images[img_idx]
            
            row = display_idx // grid_cols
            col = display_idx % grid_cols
            x_pos = start_x + col * image_spacing
            y_pos = start_y - row * image_spacing
            
            # Draw image elements at grid position
            for element in img['elements']:
                element.pos = (x_pos, y_pos)
                element.draw()
            
            # Draw selection border if selected
            if img['selected']:
                selection_border.pos = (x_pos, y_pos)
                selection_border.draw()
        
        # Update counter
        num_selected = sum(1 for img in all_memory_images if img['selected'])
        if num_selected == MEMORY_SET_1_SIZE:
            counter_text.text = f"Selected: {num_selected} / {MEMORY_SET_1_SIZE} - Press SPACE to continue"
            counter_text.color = 'green'
        else:
            counter_text.text = f"Selected: {num_selected} / {MEMORY_SET_1_SIZE}"
            counter_text.color = 'white'
        
        instruction_display.draw()
        counter_text.draw()
        copyright_text_small.draw()
        draw_progress_bar(win, test_sections, current_section, copyright_text_small)
        win.flip()
        
        # Check for mouse clicks
        if mouse.getPressed()[0]:  # Left click
            mouse_pos = mouse.getPos()
            
            # First check if clicking on counter text to continue (when all selected)
            if num_selected == MEMORY_SET_1_SIZE:
                if is_text_clicked(counter_text, mouse):
                    print("User clicked CONTINUE (all shapes selected)")
                    recognition_complete = True
                    core.wait(0.3)  # Debounce
                    continue  # Skip image checking
            
            # Check which image was clicked (using randomized positions)
            for display_idx in range(len(display_order_iter2)):
                img_idx = display_order_iter2[display_idx]
                img = all_memory_images[img_idx]
                
                row = display_idx // grid_cols
                col = display_idx % grid_cols
                x_pos = start_x + col * image_spacing
                y_pos = start_y - row * image_spacing
                
                # Check if click is within image bounds
                if (abs(mouse_pos[0] - x_pos) < (70 * scale_x) and 
                    abs(mouse_pos[1] - y_pos) < 70):
                    img['selected'] = not img['selected']
                    if img['selected']:
                        img['ever_selected'] = True
                    img['click_count'] += 1
                    total_clicks += 1
                    core.wait(0.2)  # Debounce
                    break
        
        # Check for spacebar to finish
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if 'space' in keys and num_selected == MEMORY_SET_1_SIZE:
            recognition_complete = True
        elif 'escape' in keys:
            win.close()
            core.quit()
        
        core.wait(0.01)

    # Record results for Memory Set 1 Iteration 2
    memory_set_1_test_2_selected = [img['id'] for img in all_memory_images if img['selected']]
    memory_set_1_test_2_correct = [img_id for img_id in memory_set_1_test_2_selected 
                                    if img_id in memory_set_1_indices]
    memory_set_1_test_2_accuracy = len(memory_set_1_test_2_correct) / MEMORY_SET_1_SIZE * 100 if MEMORY_SET_1_SIZE > 0 else 0.0

    # SAVE ITERATION 2 STATE FOR EXCEL
    memory_set_1_test_2_state = {}
    for img in all_memory_images:
        if img['id'] in range(MEMORY_SET_1_SIZE):  # Set 1 images only
            memory_set_1_test_2_state[img['id']] = {
                'selected': img['selected'],
                'changed': img['changed'],
                'clicks': img['click_count']
            }

    # Calculate detailed statistics
    # Renamed: Correct_Confirmed → Correct_Count, Incorrect_Confirmed → Incorrect_Count
    memory_set_1_test_2_correct_count = len(memory_set_1_test_2_correct)  # Correct selections count
    memory_set_1_test_2_incorrect_count = len(memory_set_1_test_2_selected) - memory_set_1_test_2_correct_count  # Incorrect selections count

    # Correct images clicked once (not changed)
    memory_set_1_test_2_correct_not_changed = sum(1 for img in all_memory_images 
                                                    if img['id'] in memory_set_1_indices 
                                                    and img['selected'] 
                                                    and img['click_count'] == 1)
    
    # Correct images clicked multiple times (changed)
    memory_set_1_test_2_correct_changed = sum(1 for img in all_memory_images 
                                               if img['id'] in memory_set_1_indices 
                                               and img['selected'] 
                                               and img['click_count'] > 1)

    # Incorrect images clicked once (not changed)
    memory_set_1_test_2_incorrect_not_changed = sum(1 for img in all_memory_images 
                                                     if img['id'] not in memory_set_1_indices 
                                                     and img['selected'] 
                                                     and img['click_count'] == 1)
    
    # Incorrect images clicked multiple times (changed)
    memory_set_1_test_2_incorrect_changed = sum(1 for img in all_memory_images 
                                                 if img['id'] not in memory_set_1_indices 
                                                 and img['selected'] 
                                                 and img['click_count'] > 1)
    
    # Total clicks on correct images
    memory_set_1_test_2_clicks_on_correct = sum(img['click_count'] for img in all_memory_images 
                                                 if img['id'] in memory_set_1_indices)
    
    # Total clicks on incorrect images
    memory_set_1_test_2_clicks_on_incorrect = sum(img['click_count'] for img in all_memory_images 
                                                   if img['id'] not in memory_set_1_indices)

    memory_set_1_test_2_total_clicks = total_clicks

    print(f"Memory Set 1 - Recognition Test Iteration 2 complete")
    print(f"Accuracy: {memory_set_1_test_2_accuracy:.1f}% ({memory_set_1_test_2_correct_count}/{MEMORY_SET_1_SIZE})")
    print(f"Total clicks: {memory_set_1_test_2_total_clicks}")
    
    # Mark Memory Set 1 Recognition 2 as completed (final test)
    test_sections[6]['completed'] = True
    
    # Add delay to prevent accidental skip of completion screen
    processing_text = visual.TextStim(
        win=win,
        text="Memory Test 1 Recognition #2 complete!\n\nProcessing results...",
        color='green',
        height=int(42 * scale_avg),
        pos=(int(0 * scale_x), int(0 * scale_y))
    )
    processing_text.draw()
    copyright_text_small.draw()
    win.flip()
    
    print("Pausing for 2 seconds to prevent accidental completion screen skip...")
    event.clearEvents()  # Clear events before wait
    core.wait(2.0)
    event.clearEvents()  # Clear events after wait

# ===== STEP 18: SAVE ALL DATA TO FILE =====
print("\n" + "=" * 80)
print("STEP 18: SAVING ALL DATA TO FILE")
print("=" * 80)
print("Beginning file save process...")

# Save results to file immediately (don't wait for user input)
# Calculate experiment and combined metrics
try:
    print("Calculating metrics...")
    experiment_metrics = calculate_framerate_metrics(experiment_frame_times, expected_fps, filter_delays=True, delay_threshold_multiplier=10)
    combined_frame_times = frame_times + experiment_frame_times
    combined_metrics = calculate_framerate_metrics(combined_frame_times, expected_fps, filter_delays=True, delay_threshold_multiplier=10)
    total_frames = stability_test_frames + len(experiment_frame_times)
    total_dropped = stability_test_dropped + experiment_dropped_frames
    experiment_stability = (1 - (experiment_dropped_frames / len(experiment_frame_times))) * 100 if len(experiment_frame_times) > 0 else 100.0
    combined_stability = (1 - (total_dropped / total_frames)) * 100 if total_frames > 0 else 100.0
    print("Metrics calculated successfully")
except Exception as e:
    print(f"Error calculating metrics: {e}")
    # Set default values
    experiment_metrics = None
    combined_metrics = None
    total_frames = 0
    total_dropped = 0
    experiment_stability = 0
    combined_stability = 0

# Check if we have valid metrics
has_experiment_metrics = experiment_metrics is not None
has_combined_metrics = combined_metrics is not None

print("Writing results to file...")
try:
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        # Write header with metadata
        f.write("=" * 80 + "\n")
        f.write("REACTION TIME TEST RESULTS\n")
        f.write("(c) 2026 Ericson P. Kimbel, II | v0.0.495\n")
        f.write("=" * 80 + "\n")
    
        # ===== INFORMED CONSENT SECTION =====
        f.write("=" * 80 + "\n")
        f.write("INFORMED CONSENT\n")
        f.write("=" * 80 + "\n")
        f.write(f"Status: {consent_status}\n")
        if consent_status == "CONSENTED":
            f.write("Participant has voluntarily agreed to participate in this testing.\n")
            f.write(f"User typed: '{consent_input_text}'\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("\nCONSENT TEXT PRESENTED:\n")
            f.write(CONSENT_TEXT)
            f.write("\n")
        elif "DECLINED" in consent_status:
            f.write("Participant DECLINED consent.\n")
            f.write(f"User input: '{consent_input_text}'\n")
            f.write("This file should not exist - program should have exited.\n")
        else:
            f.write("*** SECTION SKIPPED ***\n")
            f.write("Consent screen was skipped (RUN_CONSENT_SCREEN = False).\n")
            f.write("No informed consent was obtained.\n")
        f.write("\n")
    
        # ===== PERFORMANCE OPTIMIZATION CHECKLIST SECTION =====
        f.write("=" * 80 + "\n")
        f.write("PERFORMANCE OPTIMIZATION CHECKLIST\n")
        f.write("=" * 80 + "\n")
        if RUN_PERFORMANCE_CHECKLIST:
            items_completed = sum(1 for checked in checklist_info.values() if checked)
            total_items = len(checklist_info)
            f.write(f"Optimizations completed: {items_completed}/{total_items}\n")
            for item, checked in checklist_info.items():
                status = "YES" if checked else "NO"
                f.write(f"  [{status}] {item}\n")
        else:
            f.write("*** SECTION SKIPPED ***\n")
            f.write("Performance checklist was skipped (RUN_PERFORMANCE_CHECKLIST = False).\n")
            f.write("No optimization information was collected.\n")
        f.write("\n")
    
        # ===== SUBJECT INFORMATION SECTION =====
        f.write("=" * 80 + "\n")
        f.write("SUBJECT INFORMATION\n")
        f.write("=" * 80 + "\n")
        if RUN_DATA_GATHERING:
            f.write(f"Name: {subject_info['Name']}\n")
            f.write(f"Age: {subject_info['Age']}\n")
            f.write(f"Sex: {subject_info['Sex']}\n")
            f.write(f"Subject Number: {subject_info['Subject Number']}\n")
            f.write(f"Session Number: {subject_info['Session Number']}\n")
            f.write(f"Sleep Apnea: {subject_info.get('Sleep Apnea', 'Not specified')}\n")
            f.write(f"Sleep Apnea Treatment: {subject_info.get('Sleep Apnea Treatment', 'N/A')}\n")
            # Extract health conditions key to avoid backslash in f-string
            health_key = 'Health conditions affecting cognition (ADHD, ADD, meds, etc. or "None")'
            f.write(f"Health Conditions: {subject_info.get(health_key, 'Not specified')}\n")
        else:
            f.write("*** SECTION SKIPPED ***\n")
            f.write("Data gathering was skipped (RUN_DATA_GATHERING = False).\n")
            f.write("Using default subject information:\n")
            f.write(f"Name: {subject_info['Name']}\n")
            f.write(f"Age: {subject_info['Age']}\n")
            f.write(f"Sex: {subject_info['Sex']}\n")
            f.write(f"Subject Number: {subject_info['Subject Number']}\n")
            f.write(f"Session Number: {subject_info['Session Number']}\n")
            f.write(f"Sleep Apnea: {subject_info.get('Sleep Apnea', 'Not specified')}\n")
            f.write(f"Sleep Apnea Treatment: {subject_info.get('Sleep Apnea Treatment', 'N/A')}\n")
            # Extract health conditions key to avoid backslash in f-string
            health_key = 'Health conditions affecting cognition (ADHD, ADD, meds, etc. or "None")'
            f.write(f"Health Conditions: {subject_info.get(health_key, 'Not specified')}\n")
        f.write(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Using over-ear headphones: {using_over_ear_headphones}\n")
        f.write(f"Using single monitor: {using_single_monitor}\n")
        f.write("\n")
    
        # ===== SYSTEM INFORMATION SECTION =====
        f.write("=" * 80 + "\n")
        f.write("SYSTEM INFORMATION (For Debugging Remote Testing)\n")
        f.write("=" * 80 + "\n")
        f.write("MONITOR/DISPLAY:\n")
        f.write(f"  Screen resolution: {system_info['screen_resolution_width']}x{system_info['screen_resolution_height']}\n")
        f.write(f"  Aspect ratio: {system_info['screen_aspect_ratio']:.3f} ")
        if system_info['screen_aspect_ratio'] > 1.7:
            f.write("(~16:9 or wider)\n")
        elif system_info['screen_aspect_ratio'] > 1.5:
            f.write("(~16:10)\n")
        elif system_info['screen_aspect_ratio'] > 1.3:
            f.write("(~4:3)\n")
        else:
            f.write("(narrow)\n")
        f.write(f"  Measured refresh rate: {system_info['measured_refresh_rate_hz']} Hz\n")
        f.write(f"  Frame period: {system_info['frame_period_ms']:.2f} ms\n")
        f.write(f"  Measured FPS (raw): {system_info['measured_fps']:.2f}\n")
        f.write("\n")
        f.write("UI SCALING APPLIED:\n")
        f.write(f"  Reference resolution: {system_info['reference_resolution']}\n")
        f.write(f"  Reference aspect ratio: {system_info['reference_aspect_ratio']:.3f} (16:10)\n")
        f.write(f"  UI scaling factor X: {system_info['ui_scaling_factor_x']:.3f}\n")
        f.write(f"  UI scaling factor Y: {system_info['ui_scaling_factor_y']:.3f}\n")
        f.write(f"  UI scaling factor AVG: {system_info['ui_scaling_factor_avg']:.3f}\n")
        f.write(f"  Aspect ratio match: {'Yes' if system_info['aspect_ratio_match'] else 'No'}\n")
        f.write("\n")
        f.write("EXPLANATION:\n")
        f.write("  All UI elements (fonts, positions, buttons) are dynamically scaled\n")
        f.write("  based on participant's screen resolution and aspect ratio.\n")
        f.write("  Scale factor 1.0 = reference screen (2560x1600, 13.4\" ROG Flow Z13)\n")
        f.write(f"  Scale factor {system_info['ui_scaling_factor_avg']:.3f} = participant's screen proportional scaling\n")
        f.write("\n")
    
        # ===== TEST CONFIGURATION =====
        f.write("=" * 80 + "\n")
        f.write("TEST CONFIGURATION\n")
        f.write("=" * 80 + "\n")
        f.write(f"Number of trials per test: {NUM_ITERATIONS}\n")
        f.write(f"Interval range: {INTERVAL_MIN}-{INTERVAL_MAX} seconds\n")
        f.write(f"Pre-experiment delay: {PRE_EXPERIMENT_DELAY} seconds\n")
        f.write(f"Framerate test duration: {FRAMERATE_TEST_DURATION} seconds\n")
        f.write(f"Memory pool size: {MEMORY_POOL_SIZE} images (shared by both memory sets)\n")
        f.write(f"Memory Set 1 study time: {MEMORY_SET_1_STUDY_TIME} seconds\n")
        f.write(f"Memory Set 1 size: {MEMORY_SET_1_SIZE} images\n")
        f.write(f"Memory Set 2 study time: {MEMORY_SET_2_STUDY_TIME} seconds\n")
        f.write(f"Memory Set 2 size: {MEMORY_SET_2_SIZE} images\n")
        if RUN_MEMORY_TEST_1 or RUN_MEMORY_TEST_2:
            f.write(f"Total unique memory images: {len(set(memory_set_1_indices + memory_set_2_indices))}\n")
        f.write(f"Consent screen run: {RUN_CONSENT_SCREEN}\n")
        f.write(f"Performance checklist run: {RUN_PERFORMANCE_CHECKLIST}\n")
        f.write(f"Data gathering run: {RUN_DATA_GATHERING}\n")
        f.write(f"Framerate test run: {RUN_FRAMERATE_TEST}\n")
        f.write(f"Keyboard test run: {RUN_KEYBOARD_TEST}\n")
        f.write(f"Audio verification run: {RUN_AUDIO_VERIFICATION}\n")
        if RUN_AUDIO_VERIFICATION:
            f.write(f"Selected audio frequency: {selected_frequency} Hz ({selected_sound.upper()})\n")
        else:
            f.write(f"Selected audio frequency: {selected_frequency} Hz (DEFAULT - {selected_sound.upper()})\n")
        f.write(f"Visual test run: {RUN_VISUAL_TEST}\n")
        f.write(f"Audio test run: {RUN_AUDIO_TEST}\n")
        f.write(f"Memory Test 1 run: {RUN_MEMORY_TEST_1}\n")
        f.write(f"Memory Test 2 run: {RUN_MEMORY_TEST_2}\n")
        f.write("=" * 80 + "\n\n")
    
        # ===== HARDWARE VALIDATION RESULTS =====
        f.write("=" * 80 + "\n")
        f.write("HARDWARE VALIDATION RESULTS\n")
        f.write("=" * 80 + "\n\n")
    
        # Write framerate stability test results
        f.write("FRAMERATE STABILITY TEST:\n")
        if RUN_FRAMERATE_TEST:
            f.write(f"Duration: {int(FRAMERATE_TEST_DURATION)} seconds\n")
            f.write(f"Total attempts: {len(all_framerate_attempts)}\n")
            f.write(f"Final attempt used: #{framerate_attempt_number}\n\n")
        
            # Write all framerate attempts
            for i, attempt in enumerate(all_framerate_attempts, 1):
                f.write(f"--- FRAMERATE TEST ATTEMPT #{attempt['attempt_number']} ---\n")
                f.write(f"Total frames rendered: {attempt['frames']}\n")
                f.write(f"Dropped frames: {attempt['dropped']}\n")
                f.write(f"Stability: {attempt['stability']:.2f}%\n")
                f.write(f"Average FPS: {attempt['avg_fps']:.2f}\n")
                if attempt['metrics']:
                    f.write(f"Average frame time: {attempt['metrics']['avg_frame_time']:.2f} ms\n")
                    f.write(f"Min frame time: {attempt['metrics']['min_frame_time']:.2f} ms\n")
                    f.write(f"Max frame time: {attempt['metrics']['max_frame_time']:.2f} ms\n")
                    f.write(f"Frame time std dev: {attempt['metrics']['frame_time_std']:.2f} ms\n")
                    f.write(f"Frame pacing (CV): {attempt['metrics']['frame_pacing_cv']:.2f}%\n")
                    f.write(f"99% FPS: {attempt['metrics']['fps_99']:.2f}\n")
                    f.write(f"1% FPS (1% lows): {attempt['metrics']['fps_1']:.2f}\n")
                    f.write(f"0.1% FPS (0.1% lows): {attempt['metrics']['fps_01']:.2f}\n")
                    f.write(f"Estimated input latency: {attempt['metrics']['estimated_input_latency']:.2f} ms\n")
                f.write("\n")
        
            # Note which attempt was the final one
            f.write(f"FINAL ATTEMPT (#{framerate_attempt_number}) METRICS:\n")
            f.write(f"Performance rating: {performance_rating}\n")
        else:
            f.write("*** SECTION SKIPPED ***\n")
            f.write("Framerate test was skipped (RUN_FRAMERATE_TEST = False).\n")
            f.write("No framerate stability data was collected.\n")
        f.write("\n")
    
        # Write keyboard hardware test results
        f.write("KEYBOARD HARDWARE TEST:\n")
        if RUN_KEYBOARD_TEST:
            f.write(f"Test type: Rapid Tapping - {int(KEYBOARD_TAPPING_DURATION)} seconds\n")
            f.write(f"Gap threshold: {gap_threshold:.2f} seconds (20% of test duration)\n")
            f.write(f"Total manual sessions: {len(all_keyboard_sessions)}\n")
            f.write(f"Final session used: #{keyboard_session_number}\n\n")
        
            # Write all sessions and their attempts
            f.write("ALL SESSIONS (Choice = manual G press | Forced = automatic 20% retry):\n")
            f.write("=" * 60 + "\n")
        
            global_attempt_counter = 0
            for session in all_keyboard_sessions:
                # Handle both int and string session numbers (REDO sessions are strings)
                session_num = session['session_number']
                if isinstance(session_num, str):
                    # Extract number from "X (REDO)" format
                    reason = "Redo"
                    session_display = session_num
                elif session_num > 1:
                    reason = "Choice"
                    session_display = session_num
                else:
                    reason = "Initial"
                    session_display = session_num
                    
                f.write(f"\nSESSION #{session_display} ({reason}):\n")
                f.write(f"  Total automatic retry attempts in this session: {len(session['all_attempts'])}\n")
            
                # Write each automatic attempt within this session
                for att in session['all_attempts']:
                    global_attempt_counter += 1
                    retry_type = "Forced" if not att['passed'] else "Passed"
                    f.write(f"\n  Attempt {global_attempt_counter} ({retry_type}):\n")
                    f.write(f"    Failure reason: {att['failure_reason']}\n")
                    f.write(f"    Total taps: {att['total_taps']}\n")
                    f.write(f"    Max gap: {att['max_interval']:.2f}s at position {att['max_interval_position']}\n")
                    f.write(f"    Passed: {att['passed']}\n")
            
                # Write session summary metrics (from final successful attempt)
                f.write(f"\n  Session #{session_display} Summary:\n")
                f.write(f"    Total taps: {session['total_taps']}\n")
                f.write(f"    Average tap rate: {session['avg_tap_rate']:.1f} taps/sec\n")
                f.write(f"    Maximum tap rate: {session['max_tap_rate']:.1f} taps/sec\n")
                f.write(f"    Average interval: {session['avg_tap_interval']:.2f} ms\n")
                f.write(f"    Minimum interval: {session['min_tap_interval']:.2f} ms\n")
                f.write(f"    Consistency (CV): {session['tap_cv']:.2f}%\n")
                f.write(f"    Estimated polling: {session['estimated_polling']}\n")
                f.write(f"    Rating: {session['keyboard_rating']}\n")
        
            f.write("\n" + "=" * 60 + "\n")
            f.write(f"FINAL SESSION (#{keyboard_session_number}) USED FOR ANALYSIS\n")
            f.write("=" * 60 + "\n\n")
        
            # Write final session's detailed metrics (already calculated above)
            f.write("FINAL SESSION DETAILED METRICS:\n")
            f.write("SUCCESSFUL ATTEMPT METRICS:\n")
            f.write(f"Total taps: {len(tap_events)}\n")
        
            # Check if threshold was met
            if len(tap_events) >= KEYBOARD_MIN_TAPS:
                f.write(f"Threshold status: PASSED (>= {KEYBOARD_MIN_TAPS} taps required)\n")
            else:
                f.write(f"Threshold status: NOT MET (need {KEYBOARD_MIN_TAPS}, got {len(tap_events)})\n")
        
            # Write metrics if we have at least 2 taps
            if len(tap_events) >= 2:
                f.write(f"Average tap rate: {avg_tap_rate:.1f} taps/sec\n")
                f.write(f"Maximum tap rate: {max_tap_rate:.1f} taps/sec\n")
                f.write(f"Average tap interval: {avg_tap_interval:.2f} ms\n")
                f.write(f"Minimum tap interval: {min_tap_interval:.2f} ms\n")
                f.write(f"Tap consistency (std dev): {tap_interval_std:.2f} ms\n")
                f.write(f"Tap consistency (CV): {tap_cv:.2f}%\n")
                f.write(f"Estimated polling rate: {estimated_polling}\n")
                f.write(f"Performance rating: {keyboard_rating}\n\n")
            
                # Write detailed tap intervals for analysis
                f.write("DETAILED TAP INTERVALS (time between each consecutive tap):\n")
                f.write("Tap# to Tap#  |  Interval (seconds)\n")
                f.write("-" * 40 + "\n")
                tap_intervals_for_file = [(tap_events[i] - tap_events[i-1]) for i in range(1, len(tap_events))]
                for i, interval in enumerate(tap_intervals_for_file, start=1):
                    f.write(f"Tap {i} to Tap {i+1}  |  {interval:.4f}s\n")
                f.write("\n")
            else:
                f.write(f"Insufficient taps to calculate metrics (need at least 2 taps)\n")
                f.write(f"Performance rating: {keyboard_rating}\n")
        else:
            f.write("*** SECTION SKIPPED ***\n")
            f.write("Keyboard test was skipped (RUN_KEYBOARD_TEST = False).\n")
            f.write("No keyboard hardware data was collected.\n")
        f.write("\n")
    
        # Write estimated reaction test latencies
        f.write("ESTIMATED REACTION TEST LATENCIES:\n")
        f.write(f"Distance to user: {DISTANCE_TO_USER} meters\n")
        f.write(f"Light travel time: {light_travel_time:.6f} ms (negligible)\n")
        f.write(f"Sound travel time: {sound_travel_time:.2f} ms\n")
        f.write(f"Display latency: {display_latency:.2f} ms (from framerate test)\n")
        f.write(f"Keyboard input latency: {keyboard_input_latency:.2f} ms (formula: min_tap_interval/2 + 2ms OS overhead)\n")
        f.write(f"Visual reaction estimated system latency: {visual_reaction_estimated_latency:.2f} ms\n")
        f.write(f"Audio reaction estimated system latency: {audio_reaction_estimated_latency:.2f} ms\n")
        f.write(f"Note: Estimated latency = Display + Keyboard + Travel time\n")
        f.write("\n")
    
        # Write experiment framerate results
        if has_experiment_metrics:
            f.write("EXPERIMENT FRAMERATE:\n")
            f.write(f"Total frames rendered: {len(experiment_frame_times)}\n")
            f.write(f"Dropped frames: {experiment_dropped_frames}\n")
            f.write(f"Stability: {experiment_stability:.2f}%\n")
            f.write(f"Average FPS: {experiment_metrics['avg_fps']:.2f}\n")
            f.write(f"Average frame time: {experiment_metrics['avg_frame_time']:.2f} ms\n")
            f.write(f"Min frame time: {experiment_metrics['min_frame_time']:.2f} ms\n")
            f.write(f"Max frame time: {experiment_metrics['max_frame_time']:.2f} ms\n")
            f.write(f"Frame time std dev: {experiment_metrics['frame_time_std']:.2f} ms\n")
            f.write(f"Frame pacing (CV): {experiment_metrics['frame_pacing_cv']:.2f}%\n")
            f.write(f"100% FPS (Max): {experiment_metrics['fps_100']:.2f}\n")
            f.write(f"99% FPS: {experiment_metrics['fps_99']:.2f}\n")
            f.write(f"1% FPS (1% lows): {experiment_metrics['fps_1']:.2f}\n")
            f.write(f"0.1% FPS (0.1% lows): {experiment_metrics['fps_01']:.2f}\n")
            f.write(f"Estimated input latency: {experiment_metrics['estimated_input_latency']:.2f} ms\n")
        else:
            f.write("EXPERIMENT FRAMERATE:\n")
            f.write("NO EXPERIMENT DATA - All reaction tests skipped\n")
        f.write("\n")
    
        # Write combined totals
        if has_combined_metrics:
            f.write("COMBINED TOTALS (Stability Test + Experiment):\n")
            f.write(f"Total frames rendered: {total_frames}\n")
            f.write(f"Total dropped frames: {total_dropped}\n")
            f.write(f"Stability: {combined_stability:.2f}%\n")
            f.write(f"Average FPS: {combined_metrics['avg_fps']:.2f}\n")
            f.write(f"Average frame time: {combined_metrics['avg_frame_time']:.2f} ms\n")
            f.write(f"Min frame time: {combined_metrics['min_frame_time']:.2f} ms\n")
            f.write(f"Max frame time: {combined_metrics['max_frame_time']:.2f} ms\n")
            f.write(f"Frame time std dev: {combined_metrics['frame_time_std']:.2f} ms\n")
            f.write(f"Frame pacing (CV): {combined_metrics['frame_pacing_cv']:.2f}%\n")
            f.write(f"100% FPS (Max): {combined_metrics['fps_100']:.2f}\n")
            f.write(f"99% FPS: {combined_metrics['fps_99']:.2f}\n")
            f.write(f"1% FPS (1% lows): {combined_metrics['fps_1']:.2f}\n")
            f.write(f"0.1% FPS (0.1% lows): {combined_metrics['fps_01']:.2f}\n")
            f.write(f"Estimated input latency: {combined_metrics['estimated_input_latency']:.2f} ms\n")
        else:
            f.write("COMBINED TOTALS (Stability Test + Experiment):\n")
            f.write("NO COMBINED DATA - No experiment frames recorded\n")
        f.write("=" * 80 + "\n\n")
    
        # Write Excel-friendly framerate metrics table
        # Helper function to safely get metric values
        def get_metric(metrics, key):
            if metrics is not None:
                return f"{metrics[key]:.2f}"
            else:
                return "N/A"
    
        f.write("FRAMERATE METRICS TABLE (Excel-friendly):\n")
        f.write("Metric\tStability_Test\tExperiment\tCombined\n")
        f.write("-" * 80 + "\n")
    
        f.write(f"Frames_Rendered\t{stability_test_frames}\t{len(experiment_frame_times) if has_experiment_metrics else 'N/A'}\t{total_frames if has_combined_metrics else 'N/A'}\n")
        f.write(f"Dropped_Frames\t{stability_test_dropped}\t{experiment_dropped_frames if has_experiment_metrics else 'N/A'}\t{total_dropped if has_combined_metrics else 'N/A'}\n")
        f.write(f"Stability_%\t{stability:.2f}\t{experiment_stability if has_experiment_metrics else 'N/A'}\t{combined_stability if has_combined_metrics else 'N/A'}\n")
        f.write(f"Avg_FPS\t{avg_fps:.2f}\t{get_metric(experiment_metrics, 'avg_fps')}\t{get_metric(combined_metrics, 'avg_fps')}\n")
        f.write(f"Avg_Frame_Time_ms\t{get_metric(stability_metrics, 'avg_frame_time')}\t{get_metric(experiment_metrics, 'avg_frame_time')}\t{get_metric(combined_metrics, 'avg_frame_time')}\n")
        f.write(f"Min_Frame_Time_ms\t{get_metric(stability_metrics, 'min_frame_time')}\t{get_metric(experiment_metrics, 'min_frame_time')}\t{get_metric(combined_metrics, 'min_frame_time')}\n")
        f.write(f"Max_Frame_Time_ms\t{get_metric(stability_metrics, 'max_frame_time')}\t{get_metric(experiment_metrics, 'max_frame_time')}\t{get_metric(combined_metrics, 'max_frame_time')}\n")
        f.write(f"Frame_Time_StdDev_ms\t{get_metric(stability_metrics, 'frame_time_std')}\t{get_metric(experiment_metrics, 'frame_time_std')}\t{get_metric(combined_metrics, 'frame_time_std')}\n")
        f.write(f"Frame_Pacing_CV_%\t{get_metric(stability_metrics, 'frame_pacing_cv')}\t{get_metric(experiment_metrics, 'frame_pacing_cv')}\t{get_metric(combined_metrics, 'frame_pacing_cv')}\n")
        f.write(f"100%_FPS\t{get_metric(stability_metrics, 'fps_100')}\t{get_metric(experiment_metrics, 'fps_100')}\t{get_metric(combined_metrics, 'fps_100')}\n")
        f.write(f"99%_FPS\t{get_metric(stability_metrics, 'fps_99')}\t{get_metric(experiment_metrics, 'fps_99')}\t{get_metric(combined_metrics, 'fps_99')}\n")
        f.write(f"1%_FPS\t{get_metric(stability_metrics, 'fps_1')}\t{get_metric(experiment_metrics, 'fps_1')}\t{get_metric(combined_metrics, 'fps_1')}\n")
        f.write(f"0.1%_FPS\t{get_metric(stability_metrics, 'fps_01')}\t{get_metric(experiment_metrics, 'fps_01')}\t{get_metric(combined_metrics, 'fps_01')}\n")
        f.write(f"Est_Input_Latency_ms\t{get_metric(stability_metrics, 'estimated_input_latency')}\t{get_metric(experiment_metrics, 'estimated_input_latency')}\t{get_metric(combined_metrics, 'estimated_input_latency')}\n")
        f.write("\n")
    
        # ===== MEMORY TEST RESULTS =====
        f.write("=" * 80 + "\n")
        f.write("MEMORY TEST RESULTS\n")
        f.write("=" * 80 + "\n\n")
    
        # Write Memory Set 1 results
        f.write("MEMORY SET 1:\n")
        if RUN_MEMORY_TEST_1:
            f.write(f"Study time: {MEMORY_SET_1_STUDY_TIME} seconds\n")
            f.write(f"Images to memorize: {MEMORY_SET_1_SIZE}\n")
            f.write(f"Pool size: {MEMORY_POOL_SIZE}\n")
            f.write(f"Target images (IDs): {sorted(memory_set_1_indices)}\n")
            f.write("\n")
            f.write("Recognition Test Iteration 1 (after visual test):\n")
            f.write(f"Selected (IDs): {sorted(memory_set_1_test_1_selected)}\n")
            f.write(f"Correct (IDs): {sorted(memory_set_1_test_1_correct)}\n")
            f.write(f"Accuracy: {memory_set_1_test_1_accuracy:.1f}%\n")
            f.write(f"Correct: {len(memory_set_1_test_1_correct)} / {MEMORY_SET_1_SIZE}\n")
            f.write("\n")
            f.write("Recognition Test Iteration 2 (after audio test):\n")
            f.write(f"Selected (IDs): {sorted(memory_set_1_test_2_selected)}\n")
            f.write(f"Correct (IDs): {sorted(memory_set_1_test_2_correct)}\n")
            f.write(f"Accuracy: {memory_set_1_test_2_accuracy:.1f}%\n")
            f.write(f"Correct: {len(memory_set_1_test_2_correct)} / {MEMORY_SET_1_SIZE}\n")
        else:
            f.write("*** SECTION SKIPPED ***\n")
            f.write("Memory Test 1 was skipped (RUN_MEMORY_TEST_1 = False).\n")
            f.write("No Memory Set 1 data was collected.\n")
        f.write("\n")
    
        # Write Memory Set 2 results
        f.write("MEMORY SET 2:\n")
        if RUN_MEMORY_TEST_2:
            f.write(f"Study time: {MEMORY_SET_2_STUDY_TIME} seconds\n")
            f.write(f"Images to memorize: {MEMORY_SET_2_SIZE}\n")
            f.write(f"Pool size: {MEMORY_POOL_SIZE} (same pool as Memory Set 1)\n")
            f.write(f"Target images (IDs): {sorted(memory_set_2_indices)}\n")
            f.write("\n")
            f.write("Recognition Test Iteration 1 (after audio test):\n")
            f.write(f"Selected (IDs): {sorted(memory_set_2_test_1_selected)}\n")
            f.write(f"Correct (IDs): {sorted(memory_set_2_test_1_correct)}\n")
            f.write(f"Accuracy: {memory_set_2_test_1_accuracy:.1f}%\n")
            f.write(f"Correct: {len(memory_set_2_test_1_correct)} / {MEMORY_SET_2_SIZE}\n")
        else:
            f.write("*** SECTION SKIPPED ***\n")
            f.write("Memory Test 2 was skipped (RUN_MEMORY_TEST_2 = False).\n")
            f.write("No Memory Set 2 data was collected.\n")
        f.write("\n")
    
        # Write detailed Memory Results table
        f.write("MEMORY RESULTS TABLE (Excel-friendly):\n")
        if RUN_MEMORY_TEST_1 or RUN_MEMORY_TEST_2:
            f.write("Test\tCorrect\tIncorrect\tCorrect_Not_Changed\tCorrect_Changed\tIncorrect_Not_Changed\tIncorrect_Changed\tClicks_On_Correct\tClicks_On_Incorrect\tTotal_Clicks\n")
            f.write("-" * 120 + "\n")
        else:
            f.write("*** ALL MEMORY TESTS SKIPPED ***\n")
            f.write("-" * 80 + "\n")
    
        if RUN_MEMORY_TEST_1:
            f.write(f"Memory_Set_1_Iteration_1\t{memory_set_1_test_1_correct_count}\t{memory_set_1_test_1_incorrect_count}\t{memory_set_1_test_1_correct_not_changed}\t{memory_set_1_test_1_correct_changed}\t{memory_set_1_test_1_incorrect_not_changed}\t{memory_set_1_test_1_incorrect_changed}\t{memory_set_1_test_1_clicks_on_correct}\t{memory_set_1_test_1_clicks_on_incorrect}\t{memory_set_1_test_1_total_clicks}\n")
            f.write(f"Memory_Set_1_Iteration_2\t{memory_set_1_test_2_correct_count}\t{memory_set_1_test_2_incorrect_count}\t{memory_set_1_test_2_correct_not_changed}\t{memory_set_1_test_2_correct_changed}\t{memory_set_1_test_2_incorrect_not_changed}\t{memory_set_1_test_2_incorrect_changed}\t{memory_set_1_test_2_clicks_on_correct}\t{memory_set_1_test_2_clicks_on_incorrect}\t{memory_set_1_test_2_total_clicks}\n")
        else:
            f.write("Memory_Set_1_Iteration_1\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\n")
            f.write("Memory_Set_1_Iteration_2\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\n")
    
        if RUN_MEMORY_TEST_2:
            f.write(f"Memory_Set_2_Iteration_1\t{memory_set_2_test_1_correct_count}\t{memory_set_2_test_1_incorrect_count}\t{memory_set_2_test_1_correct_not_changed}\t{memory_set_2_test_1_correct_changed}\t{memory_set_2_test_1_incorrect_not_changed}\t{memory_set_2_test_1_incorrect_changed}\t{memory_set_2_test_1_clicks_on_correct}\t{memory_set_2_test_1_clicks_on_incorrect}\t{memory_set_2_test_1_total_clicks}\n")
        else:
            f.write("Memory_Set_2_Iteration_1\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\tCANCELLED\n")
    
        f.write("\n")
    
        # ===== REACTION TIME TEST RESULTS =====
        f.write("=" * 80 + "\n")
        f.write("REACTION TIME TEST RESULTS\n")
        f.write("=" * 80 + "\n\n")
    
        # Write visual reaction time data
        f.write("VISUAL REACTION TIME TEST:\n")
        if RUN_VISUAL_TEST and len(visual_results) > 0:
            # Calculate INDIVIDUAL error ranges for each trial
            f.write("TRIAL-BY-TRIAL DATA WITH INDIVIDUAL ERROR RANGES:\n")
            f.write("(Error = Frame time at response + Input latency - UNIQUE PER TRIAL)\n")
            f.write("Trial\tRT(ms)\tRT_Low(ms)\tRT_High(ms)\tError(ms)\tFrame_Time(ms)\tInput_Latency(ms)\tMisclicks\tFrame_Drops\n")
            f.write("-" * 100 + "\n")
            
            for result in visual_results:
                rt = result['reaction_time']
                
                # Use the ACTUAL frame time at the moment of this trial's response
                frame_time_error = result.get('response_frame_time', 1000.0 / expected_fps)
                
                # Input latency (from keyboard test)
                input_latency_error = keyboard_input_latency if 'keyboard_input_latency' in locals() else 10.0
                
                # Total error for THIS SPECIFIC TRIAL
                total_error = frame_time_error + input_latency_error
                
                # Calculate bounds
                rt_low = max(0, rt - total_error)  # Ensure no negative values
                rt_high = rt + total_error
                
                f.write(f"{result['trial']}\t{rt:.1f}\t{rt_low:.1f}\t{rt_high:.1f}\t±{total_error:.1f}\t{frame_time_error:.1f}\t{input_latency_error:.1f}\t{result['misclicks']}\t{result['frame_drops']}\n")
            
            f.write("\n")
            f.write("EXCEL-FRIENDLY FORMAT (Copy columns below for graphing):\n")
            f.write("Trial\tRT\tRT_Low\tRT_High\n")
            for result in visual_results:
                rt = result['reaction_time']
                frame_time_error = result.get('response_frame_time', 1000.0 / expected_fps)
                input_latency_error = keyboard_input_latency if 'keyboard_input_latency' in locals() else 10.0
                total_error = frame_time_error + input_latency_error
                rt_low = max(0, rt - total_error)
                rt_high = rt + total_error
                f.write(f"{result['trial']}\t{rt:.1f}\t{rt_low:.1f}\t{rt_high:.1f}\n")
            f.write("\n")
            
            f.write("OLD FORMAT (For reference - includes intervals):\n")
            f.write("Trial\tReaction_Time(ms)\tMisclicks\tInterval_Times(ms)\tFrame_Drops\n")
            f.write("-" * 80 + "\n")
            for result in visual_results:
                f.write(f"{result['trial']}\t{result['reaction_time']:.0f}\t{result['misclicks']}\t{result['intervals']}\t{result['frame_drops']}\n")
            f.write("\n")
        else:
            if not RUN_VISUAL_TEST:
                f.write("*** SECTION SKIPPED ***\n")
                f.write("Visual reaction test was skipped (RUN_VISUAL_TEST = False).\n")
                f.write("No visual reaction time data was collected.\n")
            else:
                f.write("*** NO DATA ***\n")
                f.write("Visual reaction test was enabled but no data was collected.\n")
            f.write("\n")
    
        # Write audio reaction time data
        f.write("AUDIO REACTION TIME TEST:\n")
        if RUN_AUDIO_TEST and len(audio_results) > 0:
            # Calculate INDIVIDUAL error ranges for each trial
            f.write("TRIAL-BY-TRIAL DATA WITH INDIVIDUAL ERROR RANGES:\n")
            f.write("(Error = Frame time at response + Input latency - UNIQUE PER TRIAL)\n")
            f.write("Trial\tRT(ms)\tRT_Low(ms)\tRT_High(ms)\tError(ms)\tFrame_Time(ms)\tInput_Latency(ms)\tMisclicks\tFrame_Drops\n")
            f.write("-" * 100 + "\n")
            
            for result in audio_results:
                rt = result['reaction_time']
                
                # Use the ACTUAL frame time at the moment of this trial's response
                frame_time_error = result.get('response_frame_time', 1000.0 / expected_fps)
                
                # Input latency (from keyboard test)
                input_latency_error = keyboard_input_latency if 'keyboard_input_latency' in locals() else 10.0
                
                # Total error for THIS SPECIFIC TRIAL
                total_error = frame_time_error + input_latency_error
                
                # Calculate bounds
                rt_low = max(0, rt - total_error)  # Ensure no negative values
                rt_high = rt + total_error
                
                f.write(f"{result['trial']}\t{rt:.1f}\t{rt_low:.1f}\t{rt_high:.1f}\t±{total_error:.1f}\t{frame_time_error:.1f}\t{input_latency_error:.1f}\t{result['misclicks']}\t{result['frame_drops']}\n")
            
            f.write("\n")
            f.write("EXCEL-FRIENDLY FORMAT (Copy columns below for graphing):\n")
            f.write("Trial\tRT\tRT_Low\tRT_High\n")
            for result in audio_results:
                rt = result['reaction_time']
                frame_time_error = result.get('response_frame_time', 1000.0 / expected_fps)
                input_latency_error = keyboard_input_latency if 'keyboard_input_latency' in locals() else 10.0
                total_error = frame_time_error + input_latency_error
                rt_low = max(0, rt - total_error)
                rt_high = rt + total_error
                f.write(f"{result['trial']}\t{rt:.1f}\t{rt_low:.1f}\t{rt_high:.1f}\n")
            f.write("\n")
            
            f.write("OLD FORMAT (For reference - includes intervals):\n")
            f.write("Trial\tReaction_Time(ms)\tMisclicks\tInterval_Times(ms)\tFrame_Drops\n")
            f.write("-" * 80 + "\n")
            for result in audio_results:
                f.write(f"{result['trial']}\t{result['reaction_time']:.0f}\t{result['misclicks']}\t{result['intervals']}\t{result['frame_drops']}\n")
            f.write("\n")
        else:
            if not RUN_AUDIO_TEST:
                f.write("*** SECTION SKIPPED ***\n")
                f.write("Audio reaction test was skipped (RUN_AUDIO_TEST = False).\n")
                f.write("No audio reaction time data was collected.\n")
            else:
                f.write("*** NO DATA ***\n")
                f.write("Audio reaction test was enabled but no data was collected.\n")
            f.write("\n")
    
        # ===== COMPREHENSIVE PERFORMANCE ANALYSIS =====
        f.write("=" * 80 + "\n")
        f.write("COMPREHENSIVE PERFORMANCE ANALYSIS\n")
        f.write("=" * 80 + "\n")
        f.write("NOTE: All tables below use TAB separators for easy Excel copy-paste.\n")
        f.write("To import: Select table rows, copy, paste into Excel, use 'Text to Columns' if needed.\n")
        f.write("=" * 80 + "\n\n")
    
        # Calculate extreme frame threshold (frames > 2x expected)
        expected_frame_time = 1000.0 / expected_fps
        extreme_threshold = expected_frame_time * 2.0
    
        # Analyze frame log for extremes
        extreme_frames = []
        for entry in performance_log['frame_log']:
            if entry['frame_time'] > extreme_threshold:
                extreme_frames.append(entry)
                performance_log['extreme_frames'].append({
                    'timestamp': entry['timestamp'],
                    'frame_time': entry['frame_time'],
                    'section': entry['section'],
                    'severity': 'HIGH' if entry['frame_time'] > extreme_threshold * 2 else 'MODERATE'
                })
    
        # TABLE 1: EXTREME FRAME TIMES
        f.write("=" * 80 + "\n")
        f.write("TABLE 1: EXTREME FRAME TIMES\n")
        f.write("=" * 80 + "\n")
        if extreme_frames:
            f.write(f"Threshold: >{extreme_threshold:.2f} ms (2x expected frame time)\n")
            f.write(f"Total extreme frames: {len(extreme_frames)}\n")
            f.write(f"Percentage of total frames: {len(extreme_frames)/len(performance_log['frame_log'])*100:.2f}%\n\n")
            f.write("--- COPY FROM HERE (include header) ---\n")
            f.write("Timestamp_sec\tFrame_Time_ms\tSection\tSeverity\n")
            for entry in performance_log['extreme_frames']:
                f.write(f"{entry['timestamp']:.3f}\t{entry['frame_time']:.3f}\t{entry['section']}\t{entry['severity']}\n")
            f.write("--- COPY TO HERE ---\n\n")
        else:
            f.write("No extreme frame times detected - excellent performance!\n\n")
    
        # TABLE 2: ALL FRAME TIMES WITH INDIVIDUAL ERROR RANGES
        f.write("=" * 80 + "\n")
        f.write("TABLE 2: ALL FRAME TIMES WITH INDIVIDUAL ERROR RANGES\n")
        f.write("=" * 80 + "\n")
        if performance_log['frame_log']:
            # Calculate expected frame time
            expected_frame_time_ms = 1000.0 / expected_fps
            delay_threshold = expected_frame_time_ms * 10  # 10x expected frame time
            
            # Filter actual frames for statistics
            actual_frame_times = [entry['frame_time'] for entry in performance_log['frame_log'] 
                                 if entry['frame_time'] < delay_threshold]
            
            if len(actual_frame_times) > 1:
                frame_std = statistics.stdev(actual_frame_times)
                frame_mean = statistics.mean(actual_frame_times)
            else:
                frame_std = 0
                frame_mean = expected_frame_time_ms
            
            f.write(f"Total frames logged: {len(performance_log['frame_log'])}\n")
            f.write(f"Actual frames (excluding delays >{delay_threshold:.1f}ms): {len(actual_frame_times)}\n")
            f.write(f"Delay threshold: {delay_threshold:.1f}ms (10x expected frame time of {expected_frame_time_ms:.2f}ms)\n")
            f.write(f"Frame time std dev: {frame_std:.3f} ms (from actual frames)\n")
            f.write(f"Expected frame time: {expected_frame_time_ms:.3f} ms\n")
            f.write(f"Error method: Individual per frame (deviation from expected)\n\n")
            
            f.write("EXCEL-FRIENDLY FORMAT (Copy table below for graphing with error bars):\n")
            f.write("Frame_Number\tFrame_Time_ms\tFrame_Time_Low\tFrame_Time_High\tError_Range\tSection\n")
            
            for idx, entry in enumerate(performance_log['frame_log'], 1):
                ft = entry['frame_time']
                
                if ft < delay_threshold:  # Actual frame
                    # Individual error for this frame = absolute deviation from expected
                    # This gives each frame its own error based on how far it deviates
                    deviation = abs(ft - expected_frame_time_ms)
                    error = deviation if deviation > 0 else frame_std  # Use deviation, or std dev if zero
                    ft_low = max(0, ft - error)  # Ensure no negative values
                    ft_high = ft + error
                else:  # Intentional delay between trials
                    error = 0  # No error bars on delays
                    ft_low = ft
                    ft_high = ft
                
                f.write(f"{idx}\t{ft:.3f}\t{ft_low:.3f}\t{ft_high:.3f}\t±{error:.3f}\t{entry['section']}\n")
            
            f.write("\n")
        else:
            f.write("No frame data logged.\n\n")
    
        # TABLE 3: EVENT LOG
        f.write("=" * 80 + "\n")
        f.write("TABLE 3: EVENT LOG (Stimulus & Response Occurrences)\n")
        f.write("=" * 80 + "\n")
        if performance_log['event_log']:
            f.write(f"Total events logged: {len(performance_log['event_log'])}\n\n")
            f.write("--- COPY FROM HERE (include header) ---\n")
            f.write("Timestamp_sec\tEvent_Type\tDescription\n")
            for log_event in performance_log['event_log']:
                f.write(f"{log_event['timestamp']:.3f}\t{log_event['event_type']}\t{log_event['description']}\n")
            f.write("--- COPY TO HERE ---\n\n")
        else:
            f.write("No events logged (visual/audio tests may have been skipped).\n\n")
    
        # TABLE 3: SECTION PERFORMANCE SUMMARY
        f.write("=" * 80 + "\n")
        f.write("TABLE 3: SECTION PERFORMANCE SUMMARY\n")
        f.write("=" * 80 + "\n")
        if performance_log['section_log']:
            f.write(f"Total sections logged: {len([s for s in performance_log['section_log'] if s['end_time'] is not None])}\n\n")
            f.write("--- COPY FROM HERE (include header) ---\n")
            f.write("Section\tStart_sec\tEnd_sec\tDuration_sec\tTotal_Frames\tAvg_FPS\n")
            for section in performance_log['section_log']:
                if section['end_time'] is not None:
                    duration = section['end_time'] - section['start_time']
                    # Count frames in this section
                    section_frames = [f for f in performance_log['frame_log'] 
                                     if section['start_time'] <= f['timestamp'] <= section['end_time']]
                    num_frames = len(section_frames)
                    avg_fps = num_frames / duration if duration > 0 else 0
                    f.write(f"{section['section']}\t{section['start_time']:.3f}\t{section['end_time']:.3f}\t{duration:.3f}\t{num_frames}\t{avg_fps:.2f}\n")
            f.write("--- COPY TO HERE ---\n\n")
        else:
            f.write("No section data logged.\n\n")
    
        # TABLE 4: COMPLETE FRAME TIME LOG
        f.write("=" * 80 + "\n")
        f.write("TABLE 4: COMPLETE FRAME TIME LOG (Every Frame)\n")
        f.write("=" * 80 + "\n")
        f.write(f"Total frames logged: {len(performance_log['frame_log'])}\n")
        f.write("This data can be used to graph FPS over time, frame time over time, etc.\n")
        f.write("For graphing in Excel: Copy table, paste, create chart with Timestamp as X-axis.\n\n")
        if performance_log['frame_log']:
            f.write("--- COPY FROM HERE (include header) ---\n")
            f.write("Timestamp_sec\tFrame_Time_ms\tSection\tEvents\n")
            for entry in performance_log['frame_log']:
                events_str = ','.join(entry['events']) if entry['events'] else ''
                f.write(f"{entry['timestamp']:.3f}\t{entry['frame_time']:.3f}\t{entry['section']}\t{events_str}\n")
            f.write("--- COPY TO HERE ---\n\n")
        else:
            f.write("No frame log data available.\n\n")
    
        f.write("=" * 80 + "\n")
        f.write("END OF PERFORMANCE ANALYSIS\n")
        f.write("=" * 80 + "\n")
        f.write("\nEXCEL IMPORT INSTRUCTIONS:\n")
        f.write("1. Select text between 'COPY FROM HERE' and 'COPY TO HERE' markers\n")
        f.write("2. Copy (Ctrl+C)\n")
        f.write("3. Paste into Excel (Ctrl+V)\n")
        f.write("4. If data appears in one column, use 'Data > Text to Columns' > Delimited > Tab\n")
        f.write("5. Create charts using timestamp columns as X-axis\n")
        f.write("=" * 80 + "\n")


        print(f"\n*** RESULTS SAVED SUCCESSFULLY TO: {OUTPUT_FILE} ***")

except Exception as file_error:
    print(f"\n!!! ERROR WRITING RESULTS FILE: {file_error} !!!")
    print(f"Error type: {type(file_error).__name__}")
    import traceback
    traceback.print_exc()
    print(f"\nAttempting to save partial results...")
    
    # Try to save at least basic info
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("REACTION TIME TEST RESULTS (PARTIAL - ERROR OCCURRED)\n")
            f.write("=" * 80 + "\n")
            f.write(f"ERROR: {str(file_error)}\n")
            f.write(f"Data may be incomplete due to error during file writing.\n")
            f.write("=" * 80 + "\n")
        print(f"Partial results saved to: {OUTPUT_FILE}")
    except:
        print("Could not save even partial results")
    
# Export to additional formats (CSV and Excel)
print("\n" + "=" * 80)
print("EXPORTING TO ADDITIONAL FORMATS")
print("=" * 80)

# Prepare memory test data for Excel export
memory_set_1_test_1_dict = None
memory_set_1_test_2_dict = None
memory_set_2_test_1_dict = None

if 'all_memory_images' in locals() and all_memory_images:
    # Create dictionaries from SAVED memory states for Excel export
    try:
        # Memory Set 1 - Test 1 data (use saved state)
        if 'memory_set_1_test_1_state' in locals():
            memory_set_1_test_1_dict = {}
            for img_id, state in memory_set_1_test_1_state.items():
                was_correct = img_id in memory_set_1_images_indices if 'memory_set_1_images_indices' in locals() else False
                memory_set_1_test_1_dict[img_id] = {
                    'correct': was_correct,
                    'selected': state['selected'],
                    'changed': state['changed'],
                    'clicks': state['clicks'],
                    'selection_correct': (was_correct and state['selected']) or (not was_correct and not state['selected'])
                }
        
        # Memory Set 1 - Test 2 data (use saved state)
        if 'memory_set_1_test_2_state' in locals():
            memory_set_1_test_2_dict = {}
            for img_id, state in memory_set_1_test_2_state.items():
                was_correct = img_id in memory_set_1_images_indices if 'memory_set_1_images_indices' in locals() else False
                memory_set_1_test_2_dict[img_id] = {
                    'correct': was_correct,
                    'selected': state['selected'],
                    'changed': state['changed'],
                    'clicks': state['clicks'],
                    'selection_correct': (was_correct and state['selected']) or (not was_correct and not state['selected'])
                }
        
        # Memory Set 2 data
        if 'memory_set_2_test_1_selected' in locals():
            memory_set_2_test_1_dict = {}
            for img in all_memory_images:
                if img['id'] >= MEMORY_SET_1_SIZE and img['id'] < MEMORY_SET_1_SIZE + MEMORY_SET_2_SIZE:  # Set 2 images
                    was_correct = img['id'] in memory_set_2_images_indices if 'memory_set_2_images_indices' in locals() else False
                    memory_set_2_test_1_dict[img['id']] = {
                        'correct': was_correct,
                        'selected': img.get('selected', False),
                        'changed': img.get('changed', False),
                        'clicks': img.get('click_count', 0),
                        'selection_correct': (was_correct and img.get('selected')) or (not was_correct and not img.get('selected'))
                    }
    except Exception as e:
        print(f"Note: Could not prepare memory data for Excel export: {e}")

# CSV Export
write_csv_exports(OUTPUT_FILE, visual_results, audio_results, subject_info, system_info, 
                  expected_fps, keyboard_input_latency)

# Excel Export
write_excel_export(OUTPUT_FILE, visual_results, audio_results, subject_info, system_info,
                   expected_fps, keyboard_input_latency, 
                   memory_set_1_test_1_dict, memory_set_1_test_2_dict, memory_set_2_test_1_dict,
                   checklist_info if 'checklist_info' in locals() else None,
                   stability_metrics if 'stability_metrics' in locals() else None,
                   all_framerate_attempts if 'all_framerate_attempts' in locals() else None,
                   all_keyboard_sessions if 'all_keyboard_sessions' in locals() else None,
                   performance_log if 'performance_log' in locals() else None,
                   NUM_ITERATIONS, INTERVAL_MIN, INTERVAL_MAX, FRAMERATE_TEST_DURATION,
                   MEMORY_SET_1_SIZE, MEMORY_SET_1_STUDY_TIME, MEMORY_SET_2_SIZE, MEMORY_SET_2_STUDY_TIME,
                   using_over_ear_headphones if 'using_over_ear_headphones' in locals() else "N/A",
                   using_single_monitor if 'using_single_monitor' in locals() else "N/A")

print("\n" + "=" * 80)
print("✓ ALL DATA FILES SAVED SUCCESSFULLY!")
print("=" * 80)
print(f"\nYour results are in the folder:")
print(f"  {output_folder_name}/")
print(f"\nFolder location:")
print(f"  {output_folder_path}")
print(f"\nFiles in folder:")
print(f"  - reaction_data_sub{subject_number}_session{session_number}_{timestamp}.txt")
print(f"  - reaction_data_sub{subject_number}_session{session_number}_{timestamp}_visual_rt.csv")
print(f"  - reaction_data_sub{subject_number}_session{session_number}_{timestamp}_audio_rt.csv")
print(f"  - reaction_data_sub{subject_number}_session{session_number}_{timestamp}.xls")
print(f"\nTO SUBMIT RESULTS:")
print(f"  1. Go to your Downloads folder")
print(f"  2. Find the folder: {output_folder_name}/")
print(f"  3. Right-click the folder → 'Send to' → 'Compressed (zipped) folder'")
print(f"  4. Email the .zip file to your researcher")
print(f"\nOR simply send the entire folder!")

print(f"\n*** FILE WRITING COMPLETED ***")

# FORCE A PAUSE - Give system time to finish file writing
print("Pausing to ensure file writing complete...")
core.wait(1.0)

# CRITICAL MARKER - If you don't see this, code didn't reach completion screen section
print("\n" + "#" * 80)
print("#" * 80)
print("### ENTERING COMPLETION SCREEN SECTION - CODE REACHED THIS POINT ###")
print("#" * 80)
print("#" * 80)
import sys
sys.stdout.flush()  # Force console output

# IMMEDIATE VISUAL CONFIRMATION - Show something on screen IMMEDIATELY
print("Showing immediate visual marker on screen...")
print("IF YOU DON'T SEE 'COMPLETION SCREEN LOADING...' ON WINDOW, THERE'S A PROBLEM")
try:
    # Clear screen first
    copyright_text_small.draw()
    win.flip()
    core.wait(0.1)
    
    immediate_marker = visual.TextStim(
        win=win,
        text="COMPLETION SCREEN LOADING...",
        color='yellow',
        height=int(60 * scale_avg),
        pos=(int(0 * scale_x), int(0 * scale_y))
    )
    immediate_marker.draw()
    copyright_text_small.draw()
    win.flip()
    print("✓ Immediate marker displayed on screen - YOU SHOULD SEE YELLOW TEXT")
    core.wait(1.0)  # Show for full second
except Exception as e:
    print(f"✗ Could not show immediate marker: {e}")
    import traceback
    traceback.print_exc()

# ===== COMPLETION SCREEN - GUARANTEED DISPLAY =====
print("\n" + "=" * 80)
print("DISPLAYING EXPERIMENT COMPLETION SCREEN")
print("=" * 80)
sys.stdout.flush()

# Verify critical variables exist
print("Checking critical variables...")
print(f"  win exists: {win is not None}")
try:
    print(f"  win.size: {win.size}")
except:
    print(f"  win.size: ERROR getting size")

print(f"  test_sections exists: {'test_sections' in dir()}")
print(f"  current_section exists: {'current_section' in dir()}")
print(f"  copyright_text_small exists: {'copyright_text_small' in dir()}")

# Aggressively clear and reset window state
print("Clearing window state...")
try:
    win.flip()
    print("✓ First flip successful")
    core.wait(0.2)
    win.flip()
    print("✓ Second flip successful")
except Exception as e:
    print(f"✗ Warning during window clear: {e}")

# CRITICAL: Re-import event module in case it was overwritten by a loop variable
from psychopy import event as psychopy_event
event = psychopy_event
print(f"Event module type: {type(event)}")
print(f"Event has clearEvents: {hasattr(event, 'clearEvents')}")

event.clearEvents()
core.wait(0.5)
event.clearEvents()
print("✓ Events cleared")

# Clear any lingering key presses before showing completion screen
print("\n" + "=" * 80)
print("CREATING COMPLETION SCREEN")
print("=" * 80)

try:
    print("Attempt 1: Creating simple completion screen first...")
    
    # Simplest possible completion screen - larger text
    simple_text = visual.TextStim(
        win=win,
        text=f"EXPERIMENT COMPLETE\n\nAll tests finished!\n\nYour results are saved in:\n{output_folder_name}/\n\n(Located in your Downloads folder)\n\nPlease send this ONE FOLDER to your researcher.\n\nThank you for participating!",
        color='white',
        height=int(60 * scale_avg),
        pos=(int(0 * scale_x), int(100 * scale_y)),
        wrapWidth=int(1800 * scale_x)
    )
    
    exit_text = visual.TextStim(
        win=win,
        text='Press SPACE or ESC to exit',
        color='green',
        height=int(48 * scale_avg),
        pos=(int(0 * scale_x), int(-400 * scale_y)),
        bold=True,
        wrapWidth=int(1200 * scale_x)
    )
    
    simple_text.draw()
    exit_text.draw()
    print("✓ Simple text drawn")
    
    copyright_text_small.draw()
    win.flip()
    print("✓ Window flipped - SCREEN SHOULD BE VISIBLE NOW")
    
    # Wait for user
    event.clearEvents()
    core.wait(1.0)
    event.clearEvents()
    
    print("Waiting for SPACE or ESC...")
    print("COMPLETION SCREEN SHOULD BE VISIBLE - waiting for user input...")
    
    global_mouse.setVisible(True)  # Show mouse for clicking instructions
    waiting = True
    last_click_time = 0
    refresh_counter = 0
    while waiting:
        keys = event.getKeys(['space', 'escape'])
        current_time = core.getTime()
        
        if keys:
            print(f"User pressed: {keys[0]}")
            waiting = False
        
        # Refresh screen every 30 frames to ensure it stays visible
        refresh_counter += 1
        if refresh_counter >= 30:
            simple_text.draw()
            exit_text.draw()
            copyright_text_small.draw()
            win.flip()
            refresh_counter = 0
        
        # Check for mouse clicks on instruction text
        if current_time - last_click_time > 0.3:
            if is_text_clicked(exit_text, global_mouse):
                print("User clicked EXIT button")
                waiting = False
                last_click_time = current_time
                core.wait(0.2)
        
        core.wait(0.01)
    
    print("Simple completion screen successful - exiting...")
    
    # User interacted with completion screen - close and exit here
    win.close()
    sys.exit(0)  # Clean exit without loading iohub

except Exception as e1:
    print(f"\n✗ Simple screen failed: {e1}")
    print("Trying detailed completion screen...")
    
    try:
        event.clearEvents()
        core.wait(1.0)
        event.clearEvents()
        
        print("Creating detailed completion screen elements...")
        
        # Show completion message
        completion_text = visual.TextStim(
            win=win,
            text=(
                "=== EXPERIMENT COMPLETE ===\n\n"
                "ALL TESTS COMPLETE!\n\n"
                f"Your results are saved in folder:\n"
                f"{output_folder_name}/\n\n"
                "(Located in your Downloads folder)\n\n"
                "Please send this ONE FOLDER to your researcher.\n\n"
                "Thank you for participating!"
            ),
            color='white',
            height=int(48 * scale_avg),
            wrapWidth=int(6000 * scale_x),  # Wide enough for title to fit on one line
            pos=(int(0 * scale_x), int(150 * scale_y))
        )
        print(f"Completion text created: {completion_text is not None}")
    
        # Copyright for completion screen (small, bottom right)
        copyright_large = visual.TextStim(
            win=win,
            text="© 2026 Ericson P. Kimbel, II | v0.0.495",
            color=[0.5, 0.5, 0.5],
            height=int(16 * scale_avg),
            pos=(win.size[0]/2 - 10, -win.size[1]/2 + 10),
            anchorHoriz='right',
            anchorVert='bottom'
        )
        print(f"Copyright text created: {copyright_large is not None}")
    
        exit_instr = visual.TextStim(
            win=win,
            text='Press SPACE or ESC to exit',
            color='green',
            height=int(36 * scale_avg),
            pos=(int(0 * scale_x), int(-650 * scale_y)),
            bold=True
        )
        print(f"Exit instruction created: {exit_instr is not None}")
    
        print("Drawing completion screen elements...")
    
        # Draw each element with error checking
        try:
            completion_text.draw()
            print("✓ Completion text drawn")
        except Exception as e:
            print(f"✗ Error drawing completion text: {e}")
    
        try:
            exit_instr.draw()
            print("✓ Exit instruction drawn")
        except Exception as e:
            print(f"✗ Error drawing exit instruction: {e}")
    
        try:
            copyright_large.draw()
            print("✓ Copyright drawn")
        except Exception as e:
            print(f"✗ Error drawing copyright: {e}")
    
        try:
            draw_progress_bar(win, test_sections, current_section, copyright_text_small)
            print("✓ Progress bar drawn")
        except Exception as e:
            print(f"✗ Error drawing progress bar: {e}")
            print("Continuing without progress bar...")
    
        # FORCE DISPLAY - multiple flips to ensure it shows
        print("Flipping window to display completion screen (attempt 1)...")
        win.flip()
        print("First flip complete")
    
        core.wait(0.1)
    
        print("Flipping window again (attempt 2)...")
        win.flip()
        print("*** COMPLETION SCREEN DISPLAYED SUCCESSFULLY! ***")
    
        # Clear events before waiting
        event.clearEvents()
        core.wait(1.5)  # Longer wait to ensure user can read completion message
        event.clearEvents()  # Clear again
    
        # Wait for any key to exit - use manual loop for better control
        print("\n" + "=" * 80)
        print("WAITING FOR USER TO PRESS SPACE OR ESC TO EXIT")
        print("=" * 80)
        print("Completion screen is visible - waiting for user input...")
    
        waiting_to_exit = True
        exit_timeout = core.getTime() + 300  # 5 minute timeout
        last_click_time = 0
        refresh_counter = 0
        while waiting_to_exit:
            keys = event.getKeys(['space', 'escape'])
            current_time = core.getTime()
            
            if keys:
                print(f"User pressed: {keys[0]}")
                waiting_to_exit = False
            elif core.getTime() > exit_timeout:
                print("Timeout reached - exiting automatically")
                waiting_to_exit = False
            
            # Check for mouse clicks on exit instruction
            if current_time - last_click_time > 0.3:
                if is_text_clicked(exit_instr, global_mouse):
                    print("User clicked EXIT button")
                    waiting_to_exit = False
                    last_click_time = current_time
                    core.wait(0.2)
            
            # Refresh screen every 30 frames
            refresh_counter += 1
            if refresh_counter >= 30:
                try:
                    completion_text.draw()
                    exit_instr.draw()
                    copyright_large.draw()
                    draw_progress_bar(win, test_sections, current_section, copyright_text_small)
                    copyright_text_small.draw()
                    win.flip()
                    refresh_counter = 0
                except:
                    pass  # Continue even if refresh fails
            
            core.wait(0.01)
    
        print("User confirmed - exiting...")
    
    except Exception as e2:
        print(f"\n*** ERROR DISPLAYING DETAILED SCREEN: {e2} ***")

        print(f"Error type: {type(e).__name__}")

        print(f"Error details: {str(e)}")

        import traceback

        traceback.print_exc()

        print("\nAttempting to show simple completion message...")

    
    try:
        # Clear screen and try simpler approach
        print("Clearing screen for fallback...")
        win.flip()
        core.wait(0.2)
        
        # Try a simpler completion screen
        print("Creating simple completion screen...")
        simple_complete = visual.TextStim(
            win=win,
            text="EXPERIMENT COMPLETE\n\nPress any key to exit",
            color='green',
            height=int(60 * scale_avg),
            pos=(int(0 * scale_x), int(0 * scale_y))
        )
        simple_complete.draw()
        copyright_text_small.draw()
        win.flip()
        print("Simple completion screen displayed - waiting for key press...")
        
        waiting_simple = True
        last_click_time = 0
        refresh_counter = 0
        while waiting_simple:
            keys = event.getKeys()
            current_time = core.getTime()
            
            if keys:
                print(f"User pressed: {keys[0]}")
                waiting_simple = False
            
            # Check for mouse clicks on the completion text
            if current_time - last_click_time > 0.3:
                if is_text_clicked(simple_complete, global_mouse):
                    print("User clicked completion screen - exiting")
                    waiting_simple = False
                    last_click_time = current_time
                    core.wait(0.2)
            
            # Refresh screen every 30 frames
            refresh_counter += 1
            if refresh_counter >= 30:
                simple_complete.draw()
                copyright_text_small.draw()
                win.flip()
                refresh_counter = 0
            
            core.wait(0.01)
        
        print("User pressed key - exiting...")
        win.close()
        sys.exit(0)  # Clean exit without loading iohub
        
    except Exception as e2:
        print(f"Could not display simple completion screen: {e2}")
        traceback.print_exc()
        print("Displaying text-only message and exiting after 5 seconds...")
        print("\n" + "=" * 80)
        print("EXPERIMENT COMPLETE - ALL DATA SAVED")
        print("=" * 80)
        core.wait(5.0)
        win.close()
        sys.exit(0)  # Clean exit without loading iohub

print("Experiment complete - final cleanup")
win.close()
sys.exit(0)  # Clean exit without loading iohub

if RUN_FRAMERATE_TEST:
    print(f"\nStability Test ({int(FRAMERATE_TEST_DURATION)}s):")
    print(f"  Frames rendered: {stability_test_frames}")
    print(f"  Dropped frames: {stability_test_dropped}")
    print(f"  Stability: {stability:.2f}%")
    print(f"  Avg FPS: {avg_fps:.2f} | 99%: {stability_metrics['fps_99']:.2f} | 1%: {stability_metrics['fps_1']:.2f} | 0.1%: {stability_metrics['fps_01']:.2f}")
    print(f"  Avg frame time: {stability_metrics['avg_frame_time']:.2f} ms")
    print(f"  Input latency: {stability_metrics['estimated_input_latency']:.2f} ms")
else:
    print(f"\nStability Test: SKIPPED")

if RUN_KEYBOARD_TEST:
    print(f"\nKeyboard Hardware Test (Rapid Tapping - {int(KEYBOARD_TAPPING_DURATION)}s):")
    if len(tap_events) >= KEYBOARD_MIN_TAPS:
        print(f"  Total taps: {len(tap_events)}")
        print(f"  Avg tap rate: {avg_tap_rate:.1f} taps/sec (max: {max_tap_rate:.1f})")
        print(f"  Avg interval: {avg_tap_interval:.2f} ms (min: {min_tap_interval:.2f} ms)")
        print(f"  Consistency: {tap_interval_std:.2f} ms (CV: {tap_cv:.2f}%)")
        print(f"  Estimated polling: {estimated_polling}")
    else:
        print(f"  TEST FAILED - Insufficient taps ({len(tap_events)}/{KEYBOARD_MIN_TAPS})")
    
    print(f"  Overall rating: {keyboard_rating}")
else:
    print(f"\nKeyboard Hardware Test: SKIPPED")

# Show estimated reaction test latencies
print(f"\nEstimated Reaction Test Latencies:")
print(f"  Display latency: {display_latency:.2f} ms")
print(f"  Keyboard latency: {keyboard_input_latency:.2f} ms (min_interval/2 + 2ms OS)")
print(f"  Sound travel (0.3m): {sound_travel_time:.2f} ms")
print(f"  Visual reaction estimated: {visual_reaction_estimated_latency:.2f} ms")
print(f"  Audio reaction estimated: {audio_reaction_estimated_latency:.2f} ms")

if has_experiment_metrics:
    print(f"\nExperiment:")
    print(f"  Frames rendered: {len(experiment_frame_times)}")
    print(f"  Dropped frames: {experiment_dropped_frames}")
    print(f"  Stability: {experiment_stability:.2f}%")
    print(f"  Avg FPS: {experiment_metrics['avg_fps']:.2f} | 99%: {experiment_metrics['fps_99']:.2f} | 1%: {experiment_metrics['fps_1']:.2f} | 0.1%: {experiment_metrics['fps_01']:.2f}")
    print(f"  Avg frame time: {experiment_metrics['avg_frame_time']:.2f} ms")
    print(f"  Input latency: {experiment_metrics['estimated_input_latency']:.2f} ms")
else:
    print(f"\nExperiment: NO DATA (All reaction tests skipped)")

if has_combined_metrics:
    print(f"\nCombined Totals:")
    print(f"  Total frames: {total_frames}")
    print(f"  Total dropped: {total_dropped}")
    print(f"  Stability: {combined_stability:.2f}%")
    print(f"  Avg FPS: {combined_metrics['avg_fps']:.2f} | 99%: {combined_metrics['fps_99']:.2f} | 1%: {combined_metrics['fps_1']:.2f} | 0.1%: {combined_metrics['fps_01']:.2f}")
    print(f"  Avg frame time: {combined_metrics['avg_frame_time']:.2f} ms")
    print(f"  Input latency: {combined_metrics['estimated_input_latency']:.2f} ms")
else:
    print(f"\nCombined Totals: NO DATA")

if RUN_MEMORY_TEST_1:
    print(f"\nMemory Set 1 Results:")
    print(f"  Target images: {sorted(memory_set_1_indices)}")
    print(f"  Recognition Test Iteration 1 (after visual test):")
    print(f"    Accuracy: {memory_set_1_test_1_accuracy:.1f}% ({memory_set_1_test_1_correct_confirmed}/{MEMORY_SET_1_SIZE})")
    print(f"    Correct confirmed: {memory_set_1_test_1_correct_confirmed}, Incorrect confirmed: {memory_set_1_test_1_incorrect_confirmed}")
    print(f"    Correct not changed: {memory_set_1_test_1_correct_not_changed}, Incorrect not changed: {memory_set_1_test_1_incorrect_not_changed}")
    print(f"    Total clicks: {memory_set_1_test_1_total_clicks}")
    print(f"  Recognition Test Iteration 2 (after audio test):")
    print(f"    Accuracy: {memory_set_1_test_2_accuracy:.1f}% ({memory_set_1_test_2_correct_confirmed}/{MEMORY_SET_1_SIZE})")
    print(f"    Correct confirmed: {memory_set_1_test_2_correct_confirmed}, Incorrect confirmed: {memory_set_1_test_2_incorrect_confirmed}")
    print(f"    Correct not changed: {memory_set_1_test_2_correct_not_changed}, Incorrect not changed: {memory_set_1_test_2_incorrect_not_changed}")
    print(f"    Total clicks: {memory_set_1_test_2_total_clicks}")
else:
    print(f"\nMemory Set 1 Results: TEST CANCELLED")

if RUN_MEMORY_TEST_2:
    print(f"\nMemory Set 2 Results:")
    print(f"  Target images: {sorted(memory_set_2_indices)}")
    print(f"  Recognition Test Iteration 1 (after audio test):")
    print(f"    Accuracy: {memory_set_2_test_1_accuracy:.1f}% ({memory_set_2_test_1_correct_confirmed}/{MEMORY_SET_2_SIZE})")
    print(f"    Correct confirmed: {memory_set_2_test_1_correct_confirmed}, Incorrect confirmed: {memory_set_2_test_1_incorrect_confirmed}")
    print(f"    Correct not changed: {memory_set_2_test_1_correct_not_changed}, Incorrect not changed: {memory_set_2_test_1_incorrect_not_changed}")
    print(f"    Total clicks: {memory_set_2_test_1_total_clicks}")
else:
    print(f"\nMemory Set 2 Results: TEST CANCELLED")

if RUN_VISUAL_TEST and len(visual_results) > 0:
    print(f"\nVisual Reaction Time Data:")
    print(f"{'Trial':<8}{'RT(ms)':<15}{'Misclicks':<12}{'Interval Times(ms)':<30}{'Frame Drops':<12}")
    print("-" * 80)
    for result in visual_results:
        print(f"{result['trial']:<8}{result['reaction_time']:<15.0f}{result['misclicks']:<12}{result['intervals']:<30}{result['frame_drops']:<12}")

if RUN_AUDIO_TEST and len(audio_results) > 0:
    print(f"\nAudio Reaction Time Data:")
    print(f"{'Trial':<8}{'RT(ms)':<15}{'Misclicks':<12}{'Interval Times(ms)':<30}{'Frame Drops':<12}")
    print("-" * 80)
    for result in audio_results:
        print(f"{result['trial']:<8}{result['reaction_time']:<15.0f}{result['misclicks']:<12}{result['intervals']:<30}{result['frame_drops']:<12}")

print("\n" + "=" * 80)
print("ALL DATA SAVED SUCCESSFULLY")
print("=" * 80)

# NOTE: Window closing is handled in completion screen section
# DO NOT add win.close() or core.quit() here - it will prevent completion screen from displaying