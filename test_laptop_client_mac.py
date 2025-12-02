#!/usr/bin/env python3
"""
Simple test script for Mac to test laptop client integration
without requiring Pi-specific dependencies (audio, STT, LLM).
"""

import yaml
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.intent_classifier import classify_intent
from utils.laptop_client import LaptopBackendConfig, send_laptop_task
import uuid


def test_intent_classification():
    """Test intent classification."""
    print("\n=== Testing Intent Classification ===")
    print("Note: Without LLM, uses fallback heuristics")
    
    test_cases = [
        ("open Safari and go to google.com", "laptop_action"),
        ("go to blackboard life university and login", "laptop_action"),
        ("text my girlfriend that song", "laptop_action"),
        ("what is Python", "local_qa"),
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
    
    # Test a simple task that Agent-S can actually complete
    print("\nSending test task to laptop...")
    print("Note: This may take 60-300 seconds as the backend waits for Agent-S to complete the task.")
    print("      Using 'Open Safari' instead of 'Move mouse' (Agent-S doesn't have move_mouse function)")
    result = send_laptop_task(
        laptop_config,
        task_id="test-mac",
        user_text="Open Safari",
        mode="gui_task",
        options={"send_screenshot": True},
    )
    
    print(f"Status: {result['status']}")
    print(f"Message: {result.get('message', 'N/A')}")
    if result.get('screenshot_url'):
        print(f"Screenshot: {result['screenshot_url']}")
    else:
        print("No screenshot URL")


def interactive_test():
    """Interactive mode to test different commands."""
    print("\n=== Interactive Test Mode ===")
    print("Type commands to test intent classification and routing")
    print("Type 'quit' to exit\n")
    
    # Load config
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    laptop_config = LaptopBackendConfig.from_config(config) if config.get("laptop", {}).get("host") else None
    
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input or user_input.lower() == 'quit':
                break
            
            # Classify intent (without LLM, uses fallback heuristics)
            intent, confidence = classify_intent(user_input, llm=None)
            print(f"Intent: {intent} (confidence: {confidence:.2f})")
            
            # Route based on intent - simplified to just two paths
            if intent == "laptop_action" and laptop_config:
                print("→ Routing to laptop...")
                result = send_laptop_task(
                    laptop_config,
                    task_id=str(uuid.uuid4()),
                    user_text=user_input,
                    mode="gui_task",
                    options={"send_screenshot": True},
                )
                print(f"Status: {result['status']}")
                print(f"Message: {result.get('message', 'N/A')}")
            else:
                print(f"→ Would be handled locally (local_qa)")
                print(f"   Note: In production, this would use the LLM to answer")
            
            print()
            
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Run all tests."""
    print("🧪 Mac Test Suite for Pi-to-Mac Integration")
    print("=" * 50)
    
    try:
        test_intent_classification()
        test_laptop_task()
        
        print("\n" + "=" * 50)
        print("✅ All automated tests completed!")
        print("\nWould you like to try interactive mode? (y/n)")
        response = input().strip().lower()
        if response == 'y':
            interactive_test()
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

