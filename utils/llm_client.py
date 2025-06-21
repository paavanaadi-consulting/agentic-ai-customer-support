import openai
import asyncio
from typing import Any, Dict

# Gemini
try:
    import google.generativeai as genai
except ImportError:
    genai = None
# Claude
try:
    import anthropic
except ImportError:
    anthropic = None

def set_openai_api_key(api_key: str):
    openai.api_key = api_key

def set_gemini_api_key(api_key: str):
    if genai:
        genai.configure(api_key=api_key)

def set_claude_api_key(api_key: str):
    if anthropic:
        global _claude_client
        _claude_client = anthropic.Anthropic(api_key=api_key)
    else:
        global _claude_client
        _claude_client = None

async def call_chatgpt(prompt: str, model: str = "gpt-3.5-turbo", extra_args: Dict[str, Any] = None) -> str:
    extra_args = extra_args or {}
    loop = asyncio.get_event_loop()
    def call():
        completion = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            **extra_args
        )
        return completion.choices[0].message["content"]
    return await loop.run_in_executor(None, call)

async def call_gemini(prompt: str, model: str = "gemini-pro", extra_args: Dict[str, Any] = None) -> str:
    if not genai:
        raise ImportError("google-generativeai is not installed")
    loop = asyncio.get_event_loop()
    def call():
        m = genai.GenerativeModel(model)
        return m.generate_content(prompt).text
    return await loop.run_in_executor(None, call)

async def call_claude(prompt: str, model: str = "claude-3-opus-20240229", extra_args: Dict[str, Any] = None) -> str:
    global _claude_client
    if not anthropic or _claude_client is None:
        raise ImportError("anthropic is not installed or API key not set")
    loop = asyncio.get_event_loop()
    def call():
        resp = _claude_client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.content[0].text
    return await loop.run_in_executor(None, call)
