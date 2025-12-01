#!/usr/bin/env python3
"""Quick test to verify macOS permissions for GUI automation."""
import pyautogui
import time

print("Testing macOS GUI automation permissions...")
print("If you see the mouse move, permissions are working!")

# Get current mouse position
current_x, current_y = pyautogui.position()
print(f"Current mouse position: ({current_x}, {current_y})")

# Try to move mouse (small movement)
try:
    pyautogui.moveRel(50, 50, duration=0.5)
    print("✓ Mouse movement successful!")
except Exception as e:
    print(f"✗ Mouse movement failed: {e}")
    print("  → Check System Settings → Privacy & Security → Accessibility")
    print("  → Make sure your terminal app is enabled")

# Try to click
try:
    pyautogui.click()
    print("✓ Mouse click successful!")
except Exception as e:
    print(f"✗ Mouse click failed: {e}")

# Try to type
try:
    pyautogui.write("test", interval=0.1)
    print("✓ Keyboard input successful!")
except Exception as e:
    print(f"✗ Keyboard input failed: {e}")
    print("  → Check System Settings → Privacy & Security → Accessibility")

print("\nIf all tests passed, Agent-S should be able to control your Mac!")

