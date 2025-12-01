"""
Simple intent classifier for routing user requests.

Uses rule-based keyword matching to classify intents:
- laptop_action: Tasks that require GUI automation on the Mac
- weather: Weather queries
- news: News queries
- search: General search queries
- local_qa: General questions answered by local LLM
"""

from __future__ import annotations

import logging
from typing import Literal, Tuple

logger = logging.getLogger(__name__)

# Intent type
IntentType = Literal["laptop_action", "weather", "news", "search", "local_qa"]


# Keywords for laptop actions (GUI tasks on Mac)
LAPTOP_ACTION_KEYWORDS = [
    "open", "close", "launch", "start", "run", "execute",
    "vs code", "vscode", "code editor", "editor",
    "spotify", "music", "play song", "play music",
    "safari", "browser", "chrome", "firefox",
    "mail", "email", "send email", "compose",
    "notes", "notepad", "text editor",
    "figma", "design", "sketch",
    "terminal", "command", "shell",
    "fix", "debug", "code", "program",
    "order", "buy", "purchase", "shop",
    "click", "type", "move mouse", "screenshot",
    "laptop", "mac", "computer",
]

# Keywords for weather queries
WEATHER_KEYWORDS = [
    "weather", "temperature", "forecast", "rain", "snow", "sunny",
    "cloudy", "wind", "humidity", "degrees", "celsius", "fahrenheit",
    "hot", "cold", "warm", "cool",
]

# Keywords for news queries
NEWS_KEYWORDS = [
    "news", "headlines", "latest", "recent", "breaking",
    "article", "story", "report", "update",
]

# Keywords for search queries
SEARCH_KEYWORDS = [
    "search", "find", "look up", "google", "what is", "who is",
    "where is", "when is", "how to", "tell me about",
    "information about", "details about",
]


def classify_intent(text: str) -> Tuple[IntentType, float]:
    """
    Classify user intent from text.
    
    Args:
        text: User's spoken or typed text
        
    Returns:
        Tuple of (intent_type, confidence)
        confidence is a simple score (0.0 to 1.0) based on keyword matches
    """
    if not text or not text.strip():
        return "local_qa", 0.0
    
    text_lower = text.lower()
    
    # Count keyword matches for each intent
    laptop_score = sum(1 for keyword in LAPTOP_ACTION_KEYWORDS if keyword in text_lower)
    weather_score = sum(1 for keyword in WEATHER_KEYWORDS if keyword in text_lower)
    news_score = sum(1 for keyword in NEWS_KEYWORDS if keyword in text_lower)
    search_score = sum(1 for keyword in SEARCH_KEYWORDS if keyword in text_lower)
    
    # Determine intent based on highest score
    scores = {
        "laptop_action": laptop_score,
        "weather": weather_score,
        "news": news_score,
        "search": search_score,
    }
    
    max_intent = max(scores.items(), key=lambda x: x[1])
    
    # If no strong match, default to local_qa
    if max_intent[1] == 0:
        return "local_qa", 0.0
    
    # Calculate confidence (normalized score)
    total_keywords = len(LAPTOP_ACTION_KEYWORDS) + len(WEATHER_KEYWORDS) + len(NEWS_KEYWORDS) + len(SEARCH_KEYWORDS)
    confidence = min(1.0, max_intent[1] / 3.0)  # Cap at 1.0, normalize by 3
    
    return max_intent[0], confidence


def is_laptop_action(text: str) -> bool:
    """Quick check if text is a laptop action."""
    intent, confidence = classify_intent(text)
    return intent == "laptop_action" and confidence > 0.0

