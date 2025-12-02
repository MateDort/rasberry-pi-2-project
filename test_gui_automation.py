#!/usr/bin/env python3
"""
Test GUI automation capabilities on macOS.
Tests: mouse movement, clicking, typing, scrolling, screen capture.
"""

import pyautogui
import time
import subprocess
from pathlib import Path

print("🖱️  Testing GUI Automation Capabilities")
print("=" * 60)

# Safety settings
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5

def test_mouse_movement():
    """Test mouse movement."""
    print("\n1. Testing Mouse Movement...")
    try:
        current_pos = pyautogui.position()
        print(f"   Current position: {current_pos}")
        
        # Move to center of screen
        screen_width, screen_height = pyautogui.size()
        center_x, center_y = screen_width // 2, screen_height // 2
        print(f"   Moving to center: ({center_x}, {center_y})")
        pyautogui.moveTo(center_x, center_y, duration=1)
        
        new_pos = pyautogui.position()
        print(f"   New position: {new_pos}")
        print("   ✅ Mouse movement successful!")
        return True
    except Exception as e:
        print(f"   ❌ Mouse movement failed: {e}")
        return False

def test_mouse_click():
    """Test mouse clicking."""
    print("\n2. Testing Mouse Clicking...")
    try:
        # Get current position
        pos = pyautogui.position()
        print(f"   Clicking at: {pos}")
        pyautogui.click()
        print("   ✅ Mouse click successful!")
        return True
    except Exception as e:
        print(f"   ❌ Mouse click failed: {e}")
        return False

def test_keyboard_typing():
    """Test keyboard typing."""
    print("\n3. Testing Keyboard Typing...")
    try:
        # Open TextEdit to test typing
        print("   Opening TextEdit...")
        subprocess.run(["open", "-a", "TextEdit"], check=True)
        time.sleep(2)
        
        # Type test text
        test_text = "Hello from Agent-S test!"
        print(f"   Typing: '{test_text}'")
        pyautogui.write(test_text, interval=0.1)
        time.sleep(1)
        
        print("   ✅ Keyboard typing successful!")
        return True
    except Exception as e:
        print(f"   ❌ Keyboard typing failed: {e}")
        return False

def test_scrolling():
    """Test scrolling."""
    print("\n4. Testing Scrolling...")
    try:
        # Try to scroll in current window
        print("   Scrolling down...")
        pyautogui.scroll(-3)  # Scroll down
        time.sleep(0.5)
        
        print("   Scrolling up...")
        pyautogui.scroll(3)  # Scroll up
        time.sleep(0.5)
        
        print("   ✅ Scrolling successful!")
        return True
    except Exception as e:
        print(f"   ❌ Scrolling failed: {e}")
        return False

def test_screen_capture():
    """Test screen capture."""
    print("\n5. Testing Screen Capture...")
    try:
        screenshot_path = Path.home() / "Desktop" / "test_screenshot.png"
        print(f"   Capturing screenshot to: {screenshot_path}")
        screenshot = pyautogui.screenshot()
        screenshot.save(str(screenshot_path))
        
        if screenshot_path.exists():
            print(f"   ✅ Screenshot saved successfully! ({screenshot_path.stat().st_size} bytes)")
            return True
        else:
            print("   ❌ Screenshot file not found!")
            return False
    except Exception as e:
        print(f"   ❌ Screen capture failed: {e}")
        return False

def test_app_control():
    """Test opening and controlling applications."""
    print("\n6. Testing Application Control...")
    try:
        # Test opening Safari
        print("   Opening Safari...")
        subprocess.run(["open", "-a", "Safari"], check=True)
        time.sleep(3)
        
        # Check if Safari is running
        result = subprocess.run(
            ["pgrep", "-f", "Safari"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("   ✅ Safari opened successfully!")
            return True
        else:
            print("   ❌ Safari not found in running processes")
            return False
    except Exception as e:
        print(f"   ❌ Application control failed: {e}")
        return False

def main():
    """Run all GUI automation tests."""
    print("\n⚠️  Make sure you have granted Accessibility permissions!")
    print("   System Settings > Privacy & Security > Accessibility")
    input("   Press Enter to continue...")
    
    results = []
    results.append(("Mouse Movement", test_mouse_movement()))
    results.append(("Mouse Click", test_mouse_click()))
    results.append(("Keyboard Typing", test_keyboard_typing()))
    results.append(("Scrolling", test_scrolling()))
    results.append(("Screen Capture", test_screen_capture()))
    results.append(("App Control", test_app_control()))
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {test_name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n   🎉 All GUI automation tests passed!")
        print("   ✅ Your Mac is ready for Agent-S control!")
    else:
        print("\n   ⚠️  Some tests failed. Check permissions and try again.")
        print("   💡 Make sure Accessibility permissions are granted in System Settings")

if __name__ == "__main__":
    main()

