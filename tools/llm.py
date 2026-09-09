"""
Shared LLM client (Ollama running Qwen). Kept in one place so every
tool/node talks to the model the same way.
"""
import sys
import json
import re
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from langchain_ollama import ChatOllama
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, LLM_TEMPERATURE

_llm = None


def get_llm(temperature: float = LLM_TEMPERATURE):
    global _llm
    if _llm is None or _llm.temperature != temperature:
        _llm = ChatOllama(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL, temperature=temperature)
    return _llm


def call_llm(prompt: str, system: str = "", temperature: float = LLM_TEMPERATURE) -> str:
    llm = get_llm(temperature)
    messages = []
    if system:
        messages.append(("system", system))
    messages.append(("human", prompt))
    response = llm.invoke(messages)
    return response.content


def call_llm_json(prompt: str, system: str = "", temperature: float = 0.2) -> dict | list:
    """
    Calls the LLM and parses JSON out of the response, tolerating markdown
    code fences or minor extra text around the JSON payload.
    """
    raw = call_llm(prompt, system=system, temperature=temperature)
    cleaned = re.sub(r"^```(json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fall back to extracting the first {...} or [...] block
        match = re.search(r"(\[.*\]|\{.*\})", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise ValueError(f"Could not parse JSON from LLM response:\n{raw}")
