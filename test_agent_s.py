#!/usr/bin/env python3
"""Quick test to verify Agent-S is running and responding."""

import requests
import sys

AGENT_S_URL = "http://127.0.0.1:8001"

def test_agent_s():
    print("🔍 Testing Agent-S connection...")
    print(f"   URL: {AGENT_S_URL}")
    
    # Test 1: Check if Agent-S is reachable
    try:
        response = requests.get(f"{AGENT_S_URL}/api/state", timeout=5)
        if response.status_code == 200:
            print("✅ Agent-S is running and responding!")
            state = response.json()
            print(f"   State: {state}")
            return True
        else:
            print(f"❌ Agent-S returned status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Agent-S!")
        print("   → Is Agent-S running? Start it with:")
        print("   → cd FaceTimeOS/Agent-S && ./run_claude_sonnet_4_5.sh")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_agent_s()
    sys.exit(0 if success else 1)

