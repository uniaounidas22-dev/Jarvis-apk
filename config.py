"""
Configuração local do JARVIS.

Guarda a chave da API (Groq) e outras preferências num arquivo JSON
dentro da pasta de dados do próprio app (user_data_dir do Kivy).
Assim a chave nunca fica escrita dentro do código-fonte.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict


class AppConfig:
    def __init__(self, base_dir: str):
        self.path = os.path.join(base_dir, "jarvis_config.json")
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if not os.path.exists(self.path):
            self._data = {}
            return

        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                self._data = json.load(handle)
        except (OSError, ValueError):
            self._data = {}

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self._data, handle, ensure_ascii=False, indent=2)

    @property
    def groq_api_key(self) -> str:
        return str(self._data.get("groq_api_key", ""))

    @groq_api_key.setter
    def groq_api_key(self, value: str) -> None:
        self._data["groq_api_key"] = value.strip()
        self.save()

    @property
    def has_api_key(self) -> bool:
        return bool(self.groq_api_key)
