#!/usr/bin/env python3
"""
Test Agent-S capabilities: vision, task understanding, and execution.
Tests if Agent-S can see the screen, understand tasks, and execute them.
"""

import requests
import json
import time
import sys
from pathlib import Path

AGENT_S_URL = "http://127.0.0.1:8001"

def test_agent_s_connection():
    """Test if Agent-S is running and accessible."""
    print("🔍 Testing Agent-S Connection...")
    try:
        response = requests.get(f"{AGENT_S_URL}/api/state", timeout=5)
        response.raise_for_status()
        state = response.json()
        print(f"   ✅ Agent-S is running!")
        print(f"   Status: {json.dumps(state, indent=6)}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to Agent-S at {AGENT_S_URL}")
        print("   → Is Agent-S running? Start it with:")
        print("   → cd FaceTimeOS/Agent-S && ./run_claude_sonnet_4_5.sh")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_simple_task(task_text, expected_behavior):
    """Test a simple task with Agent-S."""
    print(f"\n📋 Testing Task: '{task_text}'")
    print(f"   Expected: {expected_behavior}")
    
    try:
        # Send task to Agent-S
        print("   Sending task to Agent-S...")
        response = requests.post(
            f"{AGENT_S_URL}/api/chat",
            json={"prompt": task_text},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        print(f"   ✅ Task accepted: {json.dumps(result, indent=6)}")
        
        # Poll for completion
        print("   Waiting for task completion (max 60s)...")
        start_time = time.time()
        max_wait = 60
        
        while time.time() - start_time < max_wait:
            state_response = requests.get(f"{AGENT_S_URL}/api/state", timeout=5)
            state_response.raise_for_status()
            state = state_response.json()
            
            # Handle different response structures
            agent_state = state.get("state", {})
            if not agent_state and isinstance(state, dict):
                agent_state = state
            
            is_running = agent_state.get("running", False) if agent_state else False
            current_prompt = agent_state.get("prompt", "") if agent_state else ""
            prompt_str = str(current_prompt)[:50] if current_prompt else ""
            
            elapsed = int(time.time() - start_time)
            print(f"   [{elapsed}s] Status: {'Running' if is_running else 'Idle'}, Prompt: {prompt_str}...")
            
            if not is_running:
                print(f"   ✅ Task completed after {elapsed}s")
                return True
            
            time.sleep(2)
        
        print(f"   ⏱️  Task timed out after {max_wait}s")
        return False
        
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_vision_capability():
    """Test if Agent-S can see and understand the screen."""
    print("\n👁️  Testing Vision Capability...")
    
    task = "Look at the screen and tell me what application is currently open. Just describe what you see."
    return test_simple_task(task, "Agent-S should describe the current screen")

def test_simple_action():
    """Test a simple action task."""
    print("\n⚡ Testing Simple Action...")
    
    task = "Open Safari"
    return test_simple_task(task, "Safari should open")

def test_complex_task():
    """Test a more complex task."""
    print("\n🧠 Testing Complex Task Understanding...")
    
    task = "Open Safari and navigate to google.com"
    return test_simple_task(task, "Safari should open and navigate to Google")

def test_state_monitoring():
    """Test if we can monitor Agent-S state in real-time."""
    print("\n📊 Testing State Monitoring...")
    
    try:
        print("   Monitoring Agent-S state for 10 seconds...")
        for i in range(5):
            response = requests.get(f"{AGENT_S_URL}/api/state", timeout=5)
            response.raise_for_status()
            state = response.json()
            
            # Handle different response structures
            if state is None:
                print(f"   [{i*2}s] Warning: Empty response")
                time.sleep(2)
                continue
                
            # Try different possible response structures
            agent_state = state.get("state", {})
            if not agent_state and isinstance(state, dict):
                # Maybe state itself is the agent state
                agent_state = state
            
            running = agent_state.get('running', False) if agent_state else False
            prompt = agent_state.get('prompt', 'None') if agent_state else 'None'
            prompt_str = str(prompt)[:50] if prompt else 'None'
            
            print(f"   [{i*2}s] Running: {running}, Prompt: {prompt_str}")
            time.sleep(2)
        
        print("   ✅ State monitoring successful!")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Agent-S capability tests."""
    print("🤖 Testing Agent-S Capabilities")
    print("=" * 60)
    
    # First check connection
    if not test_agent_s_connection():
        print("\n❌ Cannot proceed - Agent-S is not accessible")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Running capability tests...")
    print("=" * 60)
    
    results = []
    
    # Test state monitoring (non-intrusive)
    results.append(("State Monitoring", test_state_monitoring()))
    
    # Ask user if they want to run action tests
    print("\n⚠️  Action tests will control your Mac!")
    response = input("   Run action tests? (y/n): ").strip().lower()
    
    if response == 'y':
        results.append(("Vision Capability", test_vision_capability()))
        time.sleep(2)
        results.append(("Simple Action", test_simple_action()))
        time.sleep(2)
        results.append(("Complex Task", test_complex_task()))
    else:
        print("   Skipping action tests...")
    
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
        print("\n   🎉 All Agent-S capability tests passed!")
    else:
        print("\n   ⚠️  Some tests failed. Check Agent-S logs for details.")

if __name__ == "__main__":
    main()

