#!/usr/bin/env python
"""Fetch a suggestion from OpenRouter for a given prompt."""
from __future__ import annotations

import argparse
import os
import sys
import requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Request an AI suggestion")
    parser.add_argument("prompt", help="Prompt to send to the model")
    parser.add_argument("--model", default="openai/gpt-4o", help="OpenRouter model to use")
    parser.add_argument("--temperature", type=float, default=1.0, help="Sampling temperature")
    parser.add_argument("--max-tokens", type=int, default=256, dest="max_tokens", help="Maximum tokens to generate")
    args = parser.parse_args()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.prompt}],
        "stream": False,
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    msg = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    print(msg)


if __name__ == "__main__":
    main()
