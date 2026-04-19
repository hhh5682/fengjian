"""
Ollama AI client.
使用 HTTP API 与 Ollama 通信，避免每次都重新启动模型。
"""
from __future__ import annotations

import json
import re
import requests
from typing import Any, Dict, Optional


class OllamaClient:
    def __init__(
        self,
        model: str = "qwen3:0.6b",
        base_url: str = "http://localhost:11434",
        timeout: int = 300,
    ) -> None:
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    def is_ready(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def query(self, prompt: str, expect_json: bool = False) -> str:
        """
        通过 HTTP API 查询 Ollama，复用已启动的模型会话。
        """
        if not prompt:
            raise ValueError("prompt is required")

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            output = (data.get("response") or "").strip()
            
            if not output:
                raise RuntimeError("empty ollama response")

            return self._extract_json_text(output) if expect_json else output
        except requests.exceptions.Timeout:
            raise RuntimeError(f"ollama query timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"cannot connect to ollama at {self.base_url}. "
                f"Make sure ollama is running: ollama serve"
            )
        except Exception as e:
            raise RuntimeError(f"ollama query failed: {str(e)}")

    def query_json(self, prompt: str) -> Dict[str, Any]:
        text = self.query(prompt, expect_json=True)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON from ollama: {text}") from exc

        if not isinstance(data, dict):
            raise ValueError("ollama JSON response must be an object")

        return data

    def safe_query_json(self, prompt: str, fallback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            return self.query_json(prompt)
        except Exception:
            return fallback or {}

    @staticmethod
    def _extract_json_text(text: str) -> str:
        fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
        if fenced:
            return fenced.group(1)

        object_match = re.search(r"\{.*\}", text, re.DOTALL)
        if object_match:
            return object_match.group(0)

        return text
