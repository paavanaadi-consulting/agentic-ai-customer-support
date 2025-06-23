import pytest
import asyncio
from utils import llm_client

@pytest.mark.asyncio
async def test_call_chatgpt(monkeypatch):
    class DummyResponse:
        class Choice:
            def __init__(self):
                self.message = {"content": "Hello from ChatGPT!"}
        choices = [Choice()]
    def dummy_create(**kwargs):
        return DummyResponse()
    monkeypatch.setattr(llm_client.openai.ChatCompletion, "create", dummy_create)
    result = await llm_client.call_chatgpt("Say hello")
    assert result == "Hello from ChatGPT!"

@pytest.mark.asyncio
async def test_call_gemini(monkeypatch):
    if not llm_client.genai:
        pytest.skip("google-generativeai not installed")
    class DummyModel:
        def generate_content(self, prompt):
            class DummyText:
                text = "Hello from Gemini!"
            return DummyText()
    monkeypatch.setattr(llm_client.genai, "GenerativeModel", lambda model: DummyModel())
    result = await llm_client.call_gemini("Say hello")
    assert result == "Hello from Gemini!"

@pytest.mark.asyncio
async def test_call_claude(monkeypatch):
    if not llm_client.anthropic:
        pytest.skip("anthropic not installed")
    class DummyClient:
        class Messages:
            def create(self, **kwargs):
                class DummyContent:
                    content = [type("obj", (), {"text": "Hello from Claude!"})()]
                return DummyContent()
        messages = Messages()
    monkeypatch.setattr(llm_client, "_claude_client", DummyClient())
    result = await llm_client.call_claude("Say hello")
    assert result == "Hello from Claude!"