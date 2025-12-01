"""
Serper API client for search, news, and weather queries.

Serper API provides Google search results, news, and can be used for weather queries.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class SerperClient:
    """Client for Serper API (Google search, news, weather)."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Serper client.
        
        Args:
            api_key: Serper API key. If None, reads from SERPER_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        if not self.api_key:
            logger.warning("Serper API key not provided - search features will be disabled")
        self.base_url = "https://google.serper.dev"

    def search(self, query: str, num_results: int = 3) -> Dict[str, Any]:
        """
        Perform a general Google search.
        
        Args:
            query: Search query
            num_results: Number of results to return (default: 3)
            
        Returns:
            Dict with 'results' (list of search results) and 'answerBox' if available
        """
        if not self.api_key:
            return {"error": "Serper API key not configured", "results": []}

        payload = {
            "q": query,
            "num": num_results,
        }

        try:
            response = requests.post(
                f"{self.base_url}/search",
                json=payload,
                headers={"X-API-KEY": self.api_key},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            
            # Extract top results
            results = []
            if "organic" in data:
                for item in data["organic"][:num_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "link": item.get("link", ""),
                    })
            
            # Include answer box if available (for quick answers)
            answer_box = data.get("answerBox", {})
            
            return {
                "results": results,
                "answerBox": answer_box,
                "query": query,
            }
        except requests.RequestException as e:
            logger.error(f"Serper search failed: {e}")
            return {"error": str(e), "results": []}

    def search_news(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Search for news articles.
        
        Args:
            query: News search query
            num_results: Number of articles to return (default: 5)
            
        Returns:
            Dict with 'news' (list of news articles)
        """
        if not self.api_key:
            return {"error": "Serper API key not configured", "news": []}

        # Add "news" or "latest news" to query if not present
        news_query = query
        if "news" not in query.lower() and "latest" not in query.lower():
            news_query = f"latest news {query}"

        payload = {
            "q": news_query,
            "num": num_results,
            "type": "news",
        }

        try:
            response = requests.post(
                f"{self.base_url}/news",
                json=payload,
                headers={"X-API-KEY": self.api_key},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            
            news = []
            if "news" in data:
                for item in data["news"][:num_results]:
                    news.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "source": item.get("source", ""),
                        "date": item.get("date", ""),
                        "link": item.get("link", ""),
                    })
            
            return {
                "news": news,
                "query": news_query,
            }
        except requests.RequestException as e:
            logger.error(f"Serper news search failed: {e}")
            return {"error": str(e), "news": []}

    def search_weather(self, location: str) -> Dict[str, Any]:
        """
        Search for weather information.
        
        Args:
            location: Location name (e.g., "New York", "London, UK")
            
        Returns:
            Dict with weather information from answer box
        """
        if not self.api_key:
            return {"error": "Serper API key not configured"}

        query = f"weather in {location}"

        try:
            # Use regular search - weather queries usually return answer boxes
            result = self.search(query, num_results=1)
            
            if "answerBox" in result and result["answerBox"]:
                answer = result["answerBox"]
                return {
                    "location": location,
                    "temperature": answer.get("temperature", ""),
                    "condition": answer.get("weather", ""),
                    "humidity": answer.get("humidity", ""),
                    "wind": answer.get("wind", ""),
                    "answer": answer.get("answer", ""),
                }
            elif result.get("results"):
                # Fallback: extract from first result snippet
                snippet = result["results"][0].get("snippet", "")
                return {
                    "location": location,
                    "answer": snippet,
                }
            else:
                return {
                    "error": "No weather information found",
                    "location": location,
                }
        except Exception as e:
            logger.error(f"Weather search failed: {e}")
            return {"error": str(e), "location": location}


def format_search_response(result: Dict[str, Any]) -> str:
    """Format a search result into a spoken response."""
    if "error" in result:
        return f"Sorry, I couldn't search: {result['error']}"
    
    # Check for answer box (quick answer)
    if "answerBox" in result and result["answerBox"]:
        answer = result["answerBox"].get("answer") or result["answerBox"].get("snippet", "")
        if answer:
            return answer
    
    # Format top results
    results = result.get("results", [])
    if not results:
        return "I couldn't find any results for that search."
    
    response_parts = []
    for i, item in enumerate(results[:2], 1):  # Top 2 results
        title = item.get("title", "")
        snippet = item.get("snippet", "")[:100]  # Limit snippet length
        if snippet:
            response_parts.append(f"{snippet}")
    
    return ". ".join(response_parts) if response_parts else "Found results, but couldn't summarize them."


def format_news_response(result: Dict[str, Any]) -> str:
    """Format news results into a spoken response."""
    if "error" in result:
        return f"Sorry, I couldn't fetch news: {result['error']}"
    
    news = result.get("news", [])
    if not news:
        return "I couldn't find any recent news on that topic."
    
    headlines = []
    for item in news[:3]:  # Top 3 headlines
        title = item.get("title", "")
        if title:
            headlines.append(title)
    
    if headlines:
        return f"Here are the latest headlines: {'; '.join(headlines)}"
    return "Found news articles, but couldn't extract headlines."


def format_weather_response(result: Dict[str, Any]) -> str:
    """Format weather result into a spoken response."""
    if "error" in result:
        return f"Sorry, I couldn't get weather: {result['error']}"
    
    location = result.get("location", "that location")
    
    # Try structured data first
    if "temperature" in result and result["temperature"]:
        temp = result["temperature"]
        condition = result.get("condition", "")
        return f"The weather in {location} is {temp} with {condition}."
    
    # Fallback to answer text
    if "answer" in result and result["answer"]:
        return f"Weather in {location}: {result['answer']}"
    
    return f"I couldn't get weather information for {location}."

