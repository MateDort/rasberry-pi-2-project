#!/usr/bin/env python3
"""
Interactive Pi-side test for intent classification and Pi ↔ laptop delegation.

Goal:
- Let you type arbitrary queries (simulating speech on the Pi)
- Show how the Pi's LLM classifies the intent: laptop_action vs local_qa
- For laptop_action, actually send the task to the Mac via /pi_task and show the result
- For local_qa, answer locally using the TinyLlama LLM (no laptop involved)

Usage (on Pi or Mac, from project root):
    python3 test_pi_intent_interactive.py
"""

from __future__ import annotations

import sys
import yaml
import logging
from pathlib import Path

# Ensure project root is on sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from llm.llama_inference import LlamaInference
from utils.intent_classifier import classify_intent
from utils.laptop_client import LaptopBackendConfig, send_laptop_task


def load_config(config_path: str = "config.yaml") -> dict:
    """Load YAML config with basic error handling."""
    path = Path(config_path)
    if not path.exists():
        print(f"❌ Config file not found: {config_path}")
        sys.exit(1)
    try:
        with path.open("r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"❌ Failed to load config.yaml: {e}")
        sys.exit(1)


def init_llm(config: dict) -> LlamaInference:
    """Initialize the local LLM the same way main.py does."""
    llm_config = config.get("llm", {})
    model_path = llm_config.get("model_path")
    if not model_path:
        print("❌ LLM model_path not specified in config.llm.model_path")
        sys.exit(1)

    print(f"🧠 Loading local LLM from: {model_path}")
    llm = LlamaInference(
        model_path=model_path,
        temperature=llm_config.get("temperature", 0.7),
        max_tokens=llm_config.get("max_tokens", 150),
        top_p=llm_config.get("top_p", 0.9),
        repeat_penalty=llm_config.get("repeat_penalty", 1.1),
        context_window=llm_config.get("context_window", 2048),
    )
    return llm


def init_laptop_config(config: dict) -> LaptopBackendConfig | None:
    """Initialize laptop backend config if present."""
    laptop_cfg = config.get("laptop", {}) or {}
    host = laptop_cfg.get("host")
    if not host:
        print("⚠️  Laptop backend not configured in config.yaml (laptop.host missing)")
        print("    → Laptop tasks will be skipped; only local_qa will run.")
        return None

    backend = LaptopBackendConfig.from_config(config)
    print(f"💻 Laptop backend configured: {backend.base_url} (timeout {backend.timeout_seconds}s)")
    return backend


def interactive_loop(llm: LlamaInference, laptop_cfg: LaptopBackendConfig | None) -> None:
    """Main REPL loop to test intent classification and delegation."""
    print("\n=== Pi Intent & Laptop Delegation Interactive Test ===")
    print("Type a request as you would speak to the Pi.")
    print("The system will:")
    print("  1) Classify intent: laptop_action vs local_qa")
    print("  2) For laptop_action: send to Mac via /pi_task and show result")
    print("  3) For local_qa: answer using local TinyLlama on the Pi")
    print("Type 'quit' or press Ctrl+C to exit.\n")

    while True:
        try:
            text = input("You: ").strip()
            if not text:
                continue
            if text.lower() in {"quit", "exit"}:
                break

            # 1) Intent classification
            if llm is None:
                # Heuristic-only mode (dev/Mac without local LLM):
                # decide laptop_action vs local_qa using simple keyword cues.
                text_lower = text.lower()
                laptop_indicators = [
                    "open",
                    "go to",
                    "login",
                    "log in",
                    "text ",
                    "message",
                    "send ",
                    "click",
                    "type",
                    "navigate",
                    "website",
                    "browser",
                    "safari",
                    "chrome",
                    "notes",
                    "write in",
                    "write down",
                ]
                if any(ind in text_lower for ind in laptop_indicators):
                    intent, confidence = "laptop_action", 0.8
                else:
                    intent, confidence = "local_qa", 0.5
            else:
                # Full LLM-based classifier (used on the Pi)
                intent, confidence = classify_intent(text, llm)
            print(f"→ Intent: {intent} (confidence: {confidence:.2f})")

            # 2) Route based on intent
            if intent == "laptop_action":
                if not laptop_cfg:
                    print("⚠️  Laptop backend is not configured; cannot send laptop_action.")
                    print("    (Set laptop.host/port in config.yaml to enable this.)\n")
                    continue

                print("💻 Routing to laptop via /pi_task ...")
                from uuid import uuid4

                task_id = f"pi-intent-{uuid4().hex[:8]}"
                try:
                    result = send_laptop_task(
                        laptop_cfg,
                        task_id=task_id,
                        user_text=text,
                        mode="gui_task",
                        options={"send_screenshot": True},
                    )
                except Exception as e:
                    print(f"❌ Error sending task to laptop: {e}\n")
                    continue

                status = result.get("status", "unknown")
                message = result.get("message", "")
                screenshot_url = result.get("screenshot_url")

                print(f"   Laptop status: {status}")
                if message:
                    print(f"   Laptop message: {message}")
                if screenshot_url:
                    print(f"   Laptop screenshot: {screenshot_url}")
                print()

            else:  # local_qa
                print("🧠 Handling locally on Pi (local_qa)...")
                if llm is None:
                    print(
                        "   (Local TinyLlama is not loaded on this machine, "
                        "but on the real Pi this would be answered by the local LLM.)\n"
                    )
                else:
                    try:
                        answer = llm.generate(text)
                        print(f"Pi answer:\n{answer}\n")
                    except Exception as e:
                        print(f"❌ Error from local LLM: {e}\n")

        except KeyboardInterrupt:
            print("\nExiting.")
            break
        except EOFError:
            print("\nEOF received, exiting.")
            break


def main() -> None:
    # Keep logs minimal for interactive use
    logging.basicConfig(level=logging.INFO)

    config = load_config("config.yaml")

    # TEMP (Mac/dev only): Skip loading the local LLM and use heuristic fallback
    # This avoids needing the TinyLlama .gguf on this machine while still testing
    # the Pi → laptop routing and /pi_task behavior.
    llm = None
    laptop_cfg = init_laptop_config(config)

    interactive_loop(llm, laptop_cfg)


if __name__ == "__main__":
    main()


