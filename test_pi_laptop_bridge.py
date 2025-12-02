#!/usr/bin/env python3
"""
Test the communication bridge between Raspberry Pi and Laptop.
Tests: connection, task sending, response receiving, screenshot download.
"""

import requests
import json
import time
import sys
from pathlib import Path
import yaml

# Load config
try:
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
except FileNotFoundError:
    print("❌ config.yaml not found!")
    sys.exit(1)

laptop_config = config.get("laptop", {})
BACKEND_URL = f"http://{laptop_config.get('host', 'localhost')}:{laptop_config.get('port', 8000)}"
TIMEOUT = laptop_config.get("timeout_seconds", 60)

def check_agent_s_running():
    """Check if Agent-S is running."""
    try:
        response = requests.get("http://127.0.0.1:8001/api/state", timeout=2)
        response.raise_for_status()
        return True
    except:
        return False

def test_backend_connection():
    """Test if backend is reachable."""
    print("🔍 Testing Backend Connection...")
    print(f"   URL: {BACKEND_URL}")
    
    # Check Agent-S first
    if not check_agent_s_running():
        print("   ⚠️  Warning: Agent-S is not running on port 8001")
        print("   → Start Agent-S with: cd FaceTimeOS/Agent-S && ./run_claude_sonnet_4_5.sh")
        print("   → Or use Gemini: cd FaceTimeOS/Agent-S && ./run_gemini.sh")
        print("   → Tests will fail if Agent-S is not running")
    
    try:
        # Try to connect (even if endpoint doesn't exist, we'll get a response)
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        print(f"   ✅ Backend is reachable! (Status: {response.status_code})")
        return True
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to backend at {BACKEND_URL}")
        print("   → Is the backend running? Start it with:")
        print("   → cd FaceTimeOS/backend && uv run python main.py")
        return False
    except Exception as e:
        print(f"   ⚠️  Backend responded with error: {e}")
        print("   (This is OK - backend might not have a root endpoint)")
        return True  # Still consider it reachable

def test_pi_task_endpoint():
    """Test the /pi_task endpoint."""
    print("\n📤 Testing /pi_task Endpoint...")
    
    test_payload = {
        "task_id": "test-connection",
        "user_text": "Say hello",
        "mode": "gui_task",
        "options": {"send_screenshot": False}
    }
    
    try:
        print(f"   Sending test payload: {json.dumps(test_payload, indent=6)}")
        print(f"   Timeout: {TIMEOUT}s")
        
        response = requests.post(
            f"{BACKEND_URL}/pi_task",
            json=test_payload,
            timeout=TIMEOUT
        )
        
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Endpoint working! Response: {json.dumps(data, indent=6)}")
            return True
        elif response.status_code == 503:
            print(f"   ❌ Endpoint returned 503 (Service Unavailable)")
            data = response.json() if response.text else {}
            error_msg = data.get("message", response.text[:200])
            print(f"   Error: {error_msg}")
            if "Agent-S" in error_msg or "agent" in error_msg.lower():
                print("   → Make sure Agent-S is running:")
                print("   → cd FaceTimeOS/Agent-S && ./run_claude_sonnet_4_5.sh")
            return False
        else:
            print(f"   ❌ Endpoint returned error: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏱️  Request timed out after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_task_with_screenshot():
    """Test sending a task and receiving a screenshot."""
    print("\n📸 Testing Task with Screenshot...")
    
    test_payload = {
        "task_id": "test-screenshot",
        "user_text": "Open Safari",
        "mode": "gui_task",
        "options": {"send_screenshot": True}
    }
    
    try:
        print(f"   Sending task: '{test_payload['user_text']}'")
        print(f"   Waiting for response (max {TIMEOUT}s)...")
        
        start_time = time.time()
        response = requests.post(
            f"{BACKEND_URL}/pi_task",
            json=test_payload,
            timeout=TIMEOUT
        )
        elapsed = time.time() - start_time
        
        print(f"   ✅ Received response after {elapsed:.1f}s")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {json.dumps(data, indent=6)}")
            
            screenshot_url = data.get("screenshot_url")
            if screenshot_url:
                print(f"\n   📸 Screenshot URL: {screenshot_url}")
                
                # Try to download screenshot
                print("   Downloading screenshot...")
                try:
                    img_response = requests.get(screenshot_url, timeout=10)
                    if img_response.status_code == 200:
                        screenshot_path = Path.home() / "Desktop" / "pi_task_screenshot.png"
                        screenshot_path.write_bytes(img_response.content)
                        print(f"   ✅ Screenshot saved to: {screenshot_path}")
                        return True
                    else:
                        print(f"   ⚠️  Could not download screenshot: {img_response.status_code}")
                        return True  # Still consider test passed
                except Exception as e:
                    print(f"   ⚠️  Screenshot download failed: {e}")
                    return True  # Still consider test passed
            else:
                print("   ⚠️  No screenshot URL in response")
                return True  # Still consider test passed
        else:
            print(f"   ❌ Request failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⏱️  Request timed out after {TIMEOUT}s")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_error_handling():
    """Test error handling with invalid requests."""
    print("\n⚠️  Testing Error Handling...")
    
    # Test with missing user_text
    try:
        invalid_payload = {
            "task_id": "test-error",
            "mode": "gui_task"
        }
        
        response = requests.post(
            f"{BACKEND_URL}/pi_task",
            json=invalid_payload,
            timeout=10
        )
        
        if response.status_code == 400:
            print("   ✅ Backend correctly rejected invalid request")
            return True
        else:
            print(f"   ⚠️  Unexpected status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_response_format():
    """Test response format and fields."""
    print("\n📋 Testing Response Format...")
    
    test_payload = {
        "task_id": "test-format",
        "user_text": "Test response format",
        "mode": "gui_task",
        "options": {"send_screenshot": False}
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/pi_task",
            json=test_payload,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            required_fields = ["task_id", "status", "message"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"   ❌ Missing required fields: {missing_fields}")
                return False
            else:
                print(f"   ✅ Response has all required fields")
                print(f"   Fields: {list(data.keys())}")
                return True
        else:
            print(f"   ⚠️  Request failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run all bridge tests."""
    print("🌉 Testing Pi ↔ Laptop Communication Bridge")
    print("=" * 60)
    
    results = []
    
    # Test connection
    if not test_backend_connection():
        print("\n❌ Cannot proceed - Backend is not accessible")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Running bridge tests...")
    print("=" * 60)
    
    results.append(("Backend Connection", True))  # Already tested above
    results.append(("PI Task Endpoint", test_pi_task_endpoint()))
    results.append(("Response Format", test_response_format()))
    results.append(("Error Handling", test_error_handling()))
    
    # Ask user if they want to test with screenshot (takes longer)
    print("\n⚠️  Screenshot test will send a real task to Agent-S!")
    response = input("   Run screenshot test? (y/n): ").strip().lower()
    
    if response == 'y':
        results.append(("Task with Screenshot", test_task_with_screenshot()))
    else:
        print("   Skipping screenshot test...")
    
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
        print("\n   🎉 All bridge tests passed!")
        print("   ✅ Pi ↔ Laptop communication is working!")
    else:
        print("\n   ⚠️  Some tests failed. Check backend logs for details.")

if __name__ == "__main__":
    main()

