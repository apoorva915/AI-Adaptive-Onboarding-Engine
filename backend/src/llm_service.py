from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Literal

import requests
from dotenv import load_dotenv

from .prompts import get_skill_extraction_prompt

# Auto-load `backend/.env` so local development "just works" without `setx`/exporting env vars.
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)

logger = logging.getLogger(__name__)

if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)


def _extract_json_object(text: str) -> str:
    """
    Best-effort extraction of a JSON object from a model response.
    Supports responses that wrap JSON in ```json fences.
    """
    if not text:
        return "{}"

    # Remove code fences if present.
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1).strip()
        return candidate if candidate else "{}"

    # Otherwise try to locate the first {...} block.
    obj = re.search(r"(\{[\s\S]*\})", text)
    return obj.group(1) if obj else "{}"


def _parse_llm_skills_payload(payload: str) -> List[Dict[str, Any]]:
    """
    Expected shape:
      { "skills": [ {..skill fields..} ] }
    """
    candidate = _extract_json_object(payload)
    parsed = json.loads(candidate)
    if isinstance(parsed, dict) and isinstance(parsed.get("skills"), list):
        return parsed["skills"]
    if isinstance(parsed, list):
        return parsed
    return []


def extract_skills_with_llm(text: str, mode: Literal["resume", "jd"]) -> List[Dict[str, Any]]:
    """
    Calls an LLM to extract skills from input text.

    Returns:
      Parsed list under `skills` (fallback: []).
    """
    if not text or not text.strip():
        return []

    prompt = get_skill_extraction_prompt(text=text, mode=mode)

    timeout_s = int(os.getenv("LLM_TIMEOUT_S", "30"))
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    # Prefer OpenAI if both keys exist.
    if openai_key:
        return _extract_skills_openai(prompt=prompt, mode=mode, api_key=openai_key, timeout_s=timeout_s)
    if gemini_key:
        return _extract_skills_gemini(prompt=prompt, mode=mode, api_key=gemini_key, timeout_s=timeout_s)

    logger.warning("No LLM API key set (OPENAI_API_KEY or GEMINI_API_KEY). Returning empty skills.")
    return []


def _extract_skills_openai(prompt: str, mode: str, api_key: str, timeout_s: int) -> List[Dict[str, Any]]:
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    url = "https://api.openai.com/v1/chat/completions"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload: Dict[str, Any] = {
        "model": model,
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }

    # Force JSON when supported.
    payload["response_format"] = {"type": "json_object"}

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return _parse_llm_skills_payload(content)
    except Exception as exc:
        logger.warning("OpenAI extraction failed (%s). Retrying without response_format.", exc)
        # Fallback: retry without forcing json_object in case the model doesn't support it.
        try:
            payload.pop("response_format", None)
            resp = requests.post(url, headers=headers, json=payload, timeout=timeout_s)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return _parse_llm_skills_payload(content)
        except Exception as exc2:
            logger.exception("OpenAI extraction retry failed: %s", exc2)
            return []


def _extract_skills_gemini(prompt: str, mode: str, api_key: str, timeout_s: int) -> List[Dict[str, Any]]:
    model = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=timeout_s)
        resp.raise_for_status()
        data = resp.json()
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        return _parse_llm_skills_payload(text)
    except Exception as exc:
        logger.exception("Gemini extraction failed: %s", exc)
        return []

