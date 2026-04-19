"""
Doubao (豆包) AI client using Ark API.
Compatible interface with OllamaClient for drop-in replacement.
"""
from __future__ import annotations

import json
import re
import requests
from typing import Any, Dict, Optional


class DoubaoClient:
    def __init__(
        self,
        api_key: str = "ark-24cbc423-c86d-47c4-9f84-088a374ca8e8-e0f80",
        endpoint_id: str = "ep-20260417195236-hkhdx",
        timeout: int = 300,
    ) -> None:
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.timeout = timeout
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3"

    def is_ready(self) -> bool:
        """Check if Doubao API is accessible."""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False

    def query(self, prompt: str, expect_json: bool = False) -> str:
        """
        Query Doubao API with the given prompt.
        Compatible with OllamaClient.query() interface.
        """
        if not prompt:
            raise ValueError("prompt is required")

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.endpoint_id,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2048,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            
            # Extract content from response
            if "choices" not in data or not data["choices"]:
                raise RuntimeError("empty doubao response")
            
            output = data["choices"][0].get("message", {}).get("content", "").strip()
            
            if not output:
                raise RuntimeError("empty doubao response content")

            return self._extract_json_text(output) if expect_json else output
        except requests.exceptions.Timeout:
            raise RuntimeError(f"doubao query timed out after {self.timeout} seconds")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"cannot connect to doubao api. "
                f"Make sure your network is accessible and API key is valid."
            )
        except Exception as e:
            raise RuntimeError(f"doubao query failed: {str(e)}")

    def query_json(self, prompt: str) -> Dict[str, Any]:
        """Query and parse JSON response."""
        text = self.query(prompt, expect_json=True)
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON from doubao: {text}") from exc

        if not isinstance(data, dict):
            raise ValueError("doubao JSON response must be an object")

        return data

    def safe_query_json(
        self, prompt: str, fallback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Safely query JSON with fallback."""
        try:
            return self.query_json(prompt)
        except Exception:
            return fallback or {}

    @staticmethod
    def _extract_json_text(text: str) -> str:
        """Extract JSON from text response."""
        fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
        if fenced:
            return fenced.group(1)

        object_match = re.search(r"\{.*\}", text, re.DOTALL)
        if object_match:
            return object_match.group(0)

        return text