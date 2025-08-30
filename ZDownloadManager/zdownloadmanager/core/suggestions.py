"""Integration with OpenRouter to provide file suggestions.

This module offers a simple wrapper around the OpenRouter chat completion
endpoint. It is used to retrieve contextual information about files (e.g.
descriptions of programs) by asking an AI model. The API key and whether
suggestions should be enabled are configured in ``Config``. If the key is
missing or suggestions are disabled, the functions return ``None``.
"""
from __future__ import annotations

from typing import Generator, Optional
import json
from pathlib import Path

import requests

from .config import Config


def _cache_file(config: Config) -> Path:
    return config.cache_dir / "suggestion_cache.json"


def read_cache(config: Config) -> dict[str, str]:
    """Return cached suggestions as a dictionary.

    If no cache is present or the file is corrupted, an empty dictionary is
    returned.
    """
    cache_path = _cache_file(config)
    if not cache_path.exists():
        return {}
    try:
        return json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def clear_cache(config: Config) -> bool:
    """Remove the suggestions cache file.

    Returns ``True`` if a cache file existed and was deleted.
    """
    cache_path = _cache_file(config)
    if cache_path.exists():
        try:
            cache_path.unlink()
            return True
        except OSError:
            return False
    return False


def get_suggestion(config: Config, question: str, *, model: Optional[str] = None) -> Optional[str]:
    """Ask OpenRouter for a suggestion about ``question``.

    Returns a string if a suggestion was retrieved, otherwise ``None``.
    Caches suggestions on disk keyed by the exact question. The model can be
    overridden via the ``model`` parameter; otherwise the configuration's
    ``openrouter_model`` is used.
    """
    cache_path = _cache_file(config)
    cache: dict[str, str] = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}
    if question in cache:
        return cache[question]
    if not config.suggestions_enabled:
        return None
    api_key = config.openrouter_api_key
    if not api_key:
        return None
    model_name = model or config.openrouter_model
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": question}],
            "stream": False,
            "temperature": config.openrouter_temperature,
            "max_tokens": config.openrouter_max_tokens,
            "top_p": config.openrouter_top_p,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code != 200:
            return None
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return None
        message = choices[0].get("message", {})
        answer = message.get("content")
        if answer:
            cache[question] = answer
            try:
                cache_path.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
            except OSError:
                pass
        return answer
    except Exception:
        # On any error, fail silently
        return None


def stream_suggestion(
    config: Config, question: str, *, model: Optional[str] = None
) -> Generator[str, None, Optional[str]]:
    """Stream a suggestion from OpenRouter for ``question``.

    Yields chunks of the response as they arrive and returns the full answer at the
    end. The final answer is cached on disk like :func:`get_suggestion`.
    """

    cache_path = _cache_file(config)
    cache: dict[str, str] = {}
    if cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cache = {}
    if question in cache:
        yield cache[question]
        return cache[question]
    if not config.suggestions_enabled:
        return None
    api_key = config.openrouter_api_key
    if not api_key:
        return None
    model_name = model or config.openrouter_model
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": question}],
        "stream": True,
        "temperature": config.openrouter_temperature,
        "max_tokens": config.openrouter_max_tokens,
        "top_p": config.openrouter_top_p,
    }
    answer_parts: list[str] = []
    try:
        with requests.post(url, headers=headers, json=payload, stream=True, timeout=60) as resp:
            if resp.status_code != 200:
                return None
            buffer = ""
            for chunk in resp.iter_content(chunk_size=1024, decode_unicode=True):
                buffer += chunk
                while True:
                    line_end = buffer.find("\n")
                    if line_end == -1:
                        break
                    line = buffer[:line_end].strip()
                    buffer = buffer[line_end + 1 :]
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data == "[DONE]":
                        answer = "".join(answer_parts)
                        if answer:
                            cache[question] = answer
                            try:
                                cache_path.write_text(
                                    json.dumps(cache, indent=2) + "\n", encoding="utf-8"
                                )
                            except OSError:
                                pass
                        return answer
                    try:
                        obj = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = obj.get("choices", [{}])[0].get("delta", {}).get("content")
                    if delta:
                        answer_parts.append(delta)
                        yield delta
    except Exception:
        return None
    return None
