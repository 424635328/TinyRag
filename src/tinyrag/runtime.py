from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Callable, Deque, Dict, List, Optional

from .config import RagConfig
from .context_compressor import (
    ContextCompressor,
    Message,
    MessageType,
    CompressionResult,
    message_to_dict,
    dict_to_message,
)
from .rag import (
    SUPPORTED_KNOWLEDGE_SUFFIXES,
    RagEngine,
    build_rag_chain,
    describe_knowledge_snapshot,
    list_knowledge_files,
)


@dataclass
class ConversationTurn:
    user_question: str
    rewritten_question: str
    answer: str
    entities: List[str] = field(default_factory=list)


@dataclass
class ConversationSession:
    turns: Deque[ConversationTurn] = field(default_factory=lambda: deque(maxlen=6))
    entities: Deque[str] = field(default_factory=lambda: deque(maxlen=12))
    updated_at: Optional[str] = None


class RagRuntime:
    def __init__(
        self,
        config: RagConfig,
        chain_builder: Optional[Callable[[RagConfig], object]] = None,
        enable_context_compression: bool = True,
        target_compression_ratio: float = 0.5,
    ) -> None:
        self.config = config
        self._chain_builder = chain_builder or build_rag_chain
        self._engine = None
        self._snapshot = None
        self._last_reloaded_at = None
        self._lock = Lock()
        self._sessions = {}
        self._session_lock = Lock()
        self._enable_context_compression = enable_context_compression
        self._compressor = ContextCompressor(
            target_compression_ratio=target_compression_ratio,
            min_messages_to_compress=4,
            max_messages=12
        )
        self._last_compression_result: Optional[CompressionResult] = None

    def _current_snapshot(self):
        return describe_knowledge_snapshot(self.config.knowledge_path)

    def ensure_engine(self):
        with self._lock:
            snapshot = self._current_snapshot()
            reloaded = self._engine is None or snapshot != self._snapshot
            if reloaded:
                self._engine = self._chain_builder(self.config)
                self._snapshot = snapshot
                self._last_reloaded_at = datetime.now().isoformat(timespec="seconds")
            return self._engine, reloaded

    def _get_session(self, session_id: str) -> ConversationSession:
        with self._session_lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = ConversationSession()
            return self._sessions[session_id]

    def reset_session(self, session_id: str) -> None:
        with self._session_lock:
            self._sessions.pop(session_id, None)

    def _session_to_messages(self, session: ConversationSession) -> List[Message]:
        messages = []
        for turn in session.turns:
            messages.append(Message(
                role=MessageType.USER,
                content=turn.user_question
            ))
            messages.append(Message(
                role=MessageType.ASSISTANT,
                content=turn.answer
            ))
        return messages

    def _messages_to_turns(self, messages: List[Message]) -> List[Dict]:
        turns = []
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                user_msg = messages[i]
                assistant_msg = messages[i + 1]
                turns.append({
                    "user_question": user_msg.content,
                    "rewritten_question": user_msg.content,
                    "answer": assistant_msg.content,
                    "entities": []
                })
        return turns

    def _session_turns(self, session: ConversationSession):
        if not self._enable_context_compression or len(session.turns) < 4:
            return [
                {
                    "user_question": turn.user_question,
                    "rewritten_question": turn.rewritten_question,
                    "answer": turn.answer,
                    "entities": list(turn.entities),
                }
                for turn in session.turns
            ]
        
        messages = self._session_to_messages(session)
        compression_result = self._compressor.compress(messages)
        self._last_compression_result = compression_result
        return self._messages_to_turns(compression_result.compressed_messages)

    def _session_entities(self, session: ConversationSession):
        return list(session.entities)

    def _update_session(self, session: ConversationSession, result: dict) -> None:
        turn = ConversationTurn(
            user_question=result["question"],
            rewritten_question=result["rewritten_question"],
            answer=result["answer"],
            entities=list(result.get("entities", [])),
        )
        session.turns.append(turn)

        for entity in result.get("entities", []):
            normalized = entity.strip()
            if not normalized:
                continue
            if normalized in session.entities:
                session.entities.remove(normalized)
            session.entities.appendleft(normalized)

        session.updated_at = datetime.now().isoformat(timespec="seconds")

    def invoke(self, question: str, session_id: str = "default", debug: bool = False) -> Dict[str, object]:
        engine, reloaded = self.ensure_engine()
        session = self._get_session(session_id)
        prepared = engine.prepare(
            question,
            history_turns=self._session_turns(session),
            recent_entities=self._session_entities(session),
        )
        answer = engine.generate(prepared)
        result = {
            "question": prepared.original_question,
            "rewritten_question": prepared.rewritten_question,
            "answer": answer,
            "provider": self.config.llm_provider,
            "reloaded": reloaded,
            "entities": prepared.entities,
            "evidence": prepared.evidence,
            "debug": prepared.debug if debug else None,
        }
        self._update_session(session, result)
        return result

    def stream(self, question: str, session_id: str = "default", debug: bool = False):
        engine, reloaded = self.ensure_engine()
        session = self._get_session(session_id)
        prepared = engine.prepare(
            question,
            history_turns=self._session_turns(session),
            recent_entities=self._session_entities(session),
        )

        def event_stream():
            yield {
                "type": "start",
                "provider": self.config.llm_provider,
                "question": prepared.original_question,
                "rewritten_question": prepared.rewritten_question,
                "reloaded": reloaded,
                "recent_entities": self._session_entities(session),
            }

            chunks = []
            try:
                for chunk in engine.stream_generate(prepared):
                    chunks.append(chunk)
                    yield {"type": "token", "content": chunk}
            except Exception as exc:
                yield {"type": "error", "detail": "RAG 流式调用失败: {0}".format(exc)}
                return

            answer = "".join(chunks).strip()
            if not answer:
                answer = "抱歉，参考资料中未提供相关信息。"

            result = {
                "question": prepared.original_question,
                "rewritten_question": prepared.rewritten_question,
                "answer": answer,
                "provider": self.config.llm_provider,
                "reloaded": reloaded,
                "entities": prepared.entities,
                "evidence": prepared.evidence,
                "debug": prepared.debug if debug else None,
            }
            self._update_session(session, result)

            yield {
                "type": "end",
                "provider": self.config.llm_provider,
                "question": prepared.original_question,
                "reloaded": reloaded,
                "rewritten_question": prepared.rewritten_question,
                "entities": prepared.entities,
                "evidence": prepared.evidence,
                "debug": prepared.debug if debug else None,
            }

        return event_stream()

    def get_status(self) -> Dict[str, object]:
        files = list_knowledge_files(self.config.knowledge_path)
        status = {
            "provider": self.config.llm_provider,
            "knowledge_path": str(self.config.knowledge_path),
            "knowledge_files": [str(path).replace("\\", "/") for path in files],
            "knowledge_file_count": len(files),
            "supported_extensions": list(SUPPORTED_KNOWLEDGE_SUFFIXES),
            "last_reloaded_at": self._last_reloaded_at,
            "session_count": len(self._sessions),
            "context_compression_enabled": self._enable_context_compression,
        }
        
        if self._last_compression_result:
            status["compression"] = {
                "compression_ratio": self._last_compression_result.compression_ratio,
                "original_tokens": self._last_compression_result.original_token_count,
                "compressed_tokens": self._last_compression_result.compressed_token_count,
                "semantic_similarity": self._last_compression_result.semantic_similarity_estimate,
                "strategy_used": self._last_compression_result.strategy_used,
            }
        
        return status
