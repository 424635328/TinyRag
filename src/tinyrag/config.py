from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class RagConfig:
    knowledge_path: Path
    embedding_model_name: str
    embedding_device: str
    chunk_size: int
    chunk_overlap: int
    retriever_k: int
    temperature: float
    llm_provider: str
    ollama_model: str
    ollama_base_url: Optional[str]
    deepseek_model: str
    deepseek_base_url: str
    deepseek_api_key: Optional[str]

    @classmethod
    def from_env(cls) -> "RagConfig":
        return cls(
            knowledge_path=Path(os.getenv("KNOWLEDGE_PATH", "knowledge")),
            embedding_model_name=os.getenv(
                "EMBEDDING_MODEL_NAME",
                "BAAI/bge-small-zh-v1.5",
            ),
            embedding_device=os.getenv("EMBEDDING_DEVICE", "auto"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "150")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "30")),
            retriever_k=int(os.getenv("RETRIEVER_K", "2")),
            temperature=float(os.getenv("TEMPERATURE", "0.1")),
            llm_provider=os.getenv("LLM_PROVIDER", "ollama").lower(),
            ollama_model=os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b"),
            ollama_base_url=os.getenv("OLLAMA_BASE_URL"),
            deepseek_model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            deepseek_base_url=os.getenv(
                "DEEPSEEK_BASE_URL",
                "https://api.deepseek.com",
            ),
            deepseek_api_key=os.getenv("DEEPSEEK_API_KEY"),
        )
