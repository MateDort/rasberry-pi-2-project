"""
LLM-based intent classifier for routing user requests.

Uses local LLM to intelligently decide if a task requires GUI automation on the Mac
or can be handled locally on the Pi.
"""

from __future__ import annotations

import logging
from typing import Literal, Tuple, Optional

logger = logging.getLogger(__name__)

# Intent type - simplified to just two options
IntentType = Literal["laptop_action", "local_qa"]

# System prompt for intent classification
INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a voice assistant system.

The user has a Raspberry Pi voice assistant that can:
- Answer questions locally using its own LLM
- Delegate complex GUI tasks to a Mac computer via Agent-S

Your job is to determine if the user's request requires GUI automation on the Mac (laptop_action) or can be answered locally (local_qa).

A task requires laptop_action if it involves:
- Opening applications, websites, or files
- Clicking, typing, or interacting with GUI elements
- Multi-step workflows that require visual interaction
- Accessing files/apps on the Mac (like Notes app, Messages, etc.)
- Complex tasks like "go to website X and login", "text someone", "open app and do Y"
- Any task that requires seeing the screen and interacting with it

A task can be local_qa if it:
- Is a simple question that can be answered with knowledge
- Doesn't require opening apps or interacting with GUI
- Can be answered with information alone

Examples:
- "go to blackboard life university and login" → laptop_action (requires opening browser, navigating, typing)
- "text my girlfriend that song I sent to my brother" → laptop_action (requires opening Messages, finding contacts, sending)
- "what is the weather" → local_qa (can be answered with information)
- "what is Python" → local_qa (knowledge question)
- "open Safari" → laptop_action (requires opening application)
- "what time is it" → local_qa (can be answered locally)

Respond with ONLY one word: "laptop_action" or "local_qa"
Do not include any explanation, just the intent type."""


def classify_intent(
    text: str, 
    llm: Optional[object] = None
) -> Tuple[IntentType, float]:
    """
    Classify user intent using LLM.
    
    Args:
        text: User's spoken or typed text
        llm: Optional LLM instance (LlamaInference). If None, defaults to local_qa.
        
    Returns:
        Tuple of (intent_type, confidence)
        confidence is always 1.0 for LLM-based classification
    """
    if not text or not text.strip():
        return "local_qa", 0.0
    
    # If no LLM provided, default to local_qa (fallback)
    if llm is None:
        logger.warning("No LLM provided for intent classification, defaulting to local_qa")
        return "local_qa", 0.5
    
    try:
        # Use LLM to classify intent
        response = llm.generate(
            question=text,
            system_prompt=INTENT_CLASSIFICATION_PROMPT,
            max_tokens=10  # Just need one word response
        )
        
        # Clean and normalize response
        response = response.strip().lower()
        
        # Extract intent from response
        if "laptop_action" in response or "laptop" in response:
            intent = "laptop_action"
            confidence = 1.0
        elif "local_qa" in response or "local" in response:
            intent = "local_qa"
            confidence = 1.0
        else:
            # Fallback: check for common laptop action indicators
            laptop_indicators = [
                "open", "go to", "login", "text", "message", "send", 
                "click", "type", "navigate", "website", "app", "application"
            ]
            if any(indicator in text.lower() for indicator in laptop_indicators):
                intent = "laptop_action"
                confidence = 0.8
            else:
                intent = "local_qa"
                confidence = 0.8
        
        logger.info(f"LLM classified intent: {intent} (confidence: {confidence:.2f}) for: {text[:50]}")
        return intent, confidence
        
    except Exception as e:
        logger.error(f"Error during LLM intent classification: {e}")
        # Fallback to simple heuristic
        text_lower = text.lower()
        laptop_indicators = [
            "open", "go to", "login", "text", "message", "send",
            "click", "type", "navigate", "website", "app"
        ]
        if any(indicator in text_lower for indicator in laptop_indicators):
            return "laptop_action", 0.7
        return "local_qa", 0.7


def is_laptop_action(text: str, llm: Optional[object] = None) -> bool:
    """Quick check if text is a laptop action."""
    intent, confidence = classify_intent(text, llm)
    return intent == "laptop_action" and confidence > 0.5
