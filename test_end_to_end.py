#!/usr/bin/env python3
"""
End-to-end test script for Pi → Mac laptop agent communication.

Tests:
1. Intent classification
2. Laptop task routing
3. Serper API integration (search, news, weather)
4. Local LLM fallback
"""

import yaml
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.intent_classifier import classify_intent
from utils.laptop_client import LaptopBackendConfig, send_laptop_task


def test_intent_classification():
    """Test intent classification."""
    print("\n=== Testing Intent Classification ===")
    print("Note: Without LLM, uses fallback heuristics")
    
    test_cases = [
        ("open Safari and go to google.com", "laptop_action"),
        ("go to blackboard life university and login", "laptop_action"),
        ("text my girlfriend that song", "laptop_action"),
        ("what is the capital of France", "local_qa"),
        ("what time is it", "local_qa"),
    ]
    
    for text, expected in test_cases:
        intent, confidence = classify_intent(text, llm=None)  # No LLM, uses fallback
        status = "✓" if intent == expected else "✗"
        print(f"{status} '{text}' → {intent} (confidence: {confidence:.2f}, expected: {expected})")


# Serper integration removed - using LLM for all classification


def test_laptop_task():
    """Test laptop task routing."""
    print("\n=== Testing Laptop Task Routing ===")
    
    # Load config
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    laptop_config = LaptopBackendConfig.from_config(config)
    
    print(f"Laptop backend: {laptop_config.base_url}")
    
    # Test a simple task
    print("\nSending test task to laptop...")
    result = send_laptop_task(
        laptop_config,
        task_id="test-e2e",
        user_text="Move the mouse to the center of the screen.",
        mode="gui_task",
        options={"send_screenshot": True},
    )
    
    print(f"Status: {result['status']}")
    print(f"Message: {result.get('message', 'N/A')}")
    if result.get('screenshot_url'):
        print(f"Screenshot: {result['screenshot_url']}")
    else:
        print("No screenshot URL")


def main():
    """Run all tests."""
    print("🧪 End-to-End Integration Tests")
    print("=" * 50)
    
    try:
        test_intent_classification()
        test_laptop_task()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("\nNext steps:")
        print("1. Make sure Agent-S is running on your Mac")
        print("2. Make sure FaceTimeOS backend is running on your Mac")
        print("3. Run the main assistant: python main.py")
        print("4. Try saying: 'open Safari' or 'what's the weather'")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

