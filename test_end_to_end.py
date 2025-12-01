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
from utils.serper_client import SerperClient, format_search_response, format_news_response, format_weather_response
from utils.laptop_client import LaptopBackendConfig, send_laptop_task


def test_intent_classification():
    """Test intent classification."""
    print("\n=== Testing Intent Classification ===")
    
    test_cases = [
        ("open Safari and go to google.com", "laptop_action"),
        ("what's the weather in New York", "weather"),
        ("latest news about AI", "news"),
        ("search for Python tutorials", "search"),
        ("what is the capital of France", "local_qa"),
    ]
    
    for text, expected in test_cases:
        intent, confidence = classify_intent(text)
        status = "✓" if intent == expected else "✗"
        print(f"{status} '{text}' → {intent} (confidence: {confidence:.2f}, expected: {expected})")


def test_serper_integration():
    """Test Serper API integration."""
    print("\n=== Testing Serper API Integration ===")
    
    # Load config
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    serper_key = config.get("apis", {}).get("serper_api_key")
    if not serper_key:
        print("⚠️  SERPER_API_KEY not configured - skipping Serper tests")
        return
    
    serper = SerperClient(api_key=serper_key)
    
    # Test search
    print("\n1. Testing search...")
    result = serper.search("Python programming", num_results=2)
    if "error" not in result:
        response = format_search_response(result)
        print(f"   Response: {response[:200]}...")
    else:
        print(f"   Error: {result['error']}")
    
    # Test news
    print("\n2. Testing news...")
    result = serper.search_news("technology")
    if "error" not in result:
        response = format_news_response(result)
        print(f"   Response: {response[:200]}...")
    else:
        print(f"   Error: {result['error']}")
    
    # Test weather
    print("\n3. Testing weather...")
    result = serper.search_weather("San Francisco")
    if "error" not in result:
        response = format_weather_response(result)
        print(f"   Response: {response}")
    else:
        print(f"   Error: {result['error']}")


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
        test_serper_integration()
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

