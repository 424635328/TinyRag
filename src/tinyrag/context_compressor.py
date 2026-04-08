from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum


class MessageType(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    role: MessageType
    content: str
    timestamp: Optional[float] = None
    metadata: Optional[Dict] = None


@dataclass
class MessageImportance:
    message: Message
    importance_score: float
    key_entities: List[str]
    key_topics: List[str]
    semantic_keywords: List[str]
    is_context_critical: bool


@dataclass
class CompressionResult:
    original_messages: List[Message]
    compressed_messages: List[Message]
    compression_ratio: float
    original_token_count: int
    compressed_token_count: int
    semantic_similarity_estimate: float
    strategy_used: str


class ContextCompressor:
    def __init__(
        self,
        target_compression_ratio: float = 0.5,
        min_messages_to_compress: int = 4,
        max_messages: int = 12,
    ):
        self.target_compression_ratio = target_compression_ratio
        self.min_messages_to_compress = min_messages_to_compress
        self.max_messages = max_messages
        
        self.question_keywords = {
            "什么", "为什么", "怎样", "怎么", "如何", "多少", "哪里", "哪个",
            "谁", "何时", "何地", "what", "why", "how", "how much", "how many",
            "where", "which", "who", "when", "is", "are", "do", "does", "did"
        }
        
        self.context_keywords = {
            "然后", "接着", "之后", "所以", "因此", "那么", "这样的话", "综上所述",
            "基于此", "由此可见", "也就是说", "换句话说", "同样地", "类似地",
            "furthermore", "moreover", "in addition", "however", "therefore",
            "thus", "hence", "consequently", "in conclusion"
        }
        
        self.stop_words = {
            "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
            "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有",
            "看", "好", "自己", "这", "the", "a", "an", "is", "are", "was", "were",
            "be", "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "shall", "should", "can", "could", "may", "might", "must",
            "ought", "i", "you", "he", "she", "it", "we", "they"
        }

    def extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z][a-zA-Z0-9]*', text.lower())
        keywords = [word for word in words if word not in self.stop_words and len(word) >= 2]
        
        word_count = {}
        for word in keywords:
            word_count[word] = word_count.get(word, 0) + 1
        
        sorted_keywords = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_keywords[:20]]

    def extract_entities(self, text: str) -> List[str]:
        entities = []
        
        proper_nouns = re.findall(r'[A-Z][a-zA-Z0-9-_]+(?:\s+[A-Z][a-zA-Z0-9-_]+)*', text)
        entities.extend([n.strip() for n in proper_nouns if len(n.strip()) >= 2])
        
        quoted_terms = re.findall(r'["“]([^"”]+)["”]', text)
        entities.extend([q.strip() for q in quoted_terms if len(q.strip()) >= 2])
        
        chinese_nouns = re.findall(r'[\u4e00-\u9fa5]{2,}(?:的[\u4e00-\u9fa5]{2,})*', text)
        entities.extend([n.strip() for n in chinese_nouns if len(n.strip()) >= 2])
        
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity.lower() not in seen:
                seen.add(entity.lower())
                unique_entities.append(entity)
        
        return unique_entities[:15]

    def is_question(self, text: str) -> bool:
        text_lower = text.lower().strip()
        if any(q in text_lower for q in ["?", "？"]):
            return True
        if any(text_lower.startswith(q) for q in self.question_keywords):
            return True
        return False

    def is_context_critical(self, message: Message) -> bool:
        text = message.content.lower()
        
        if message.role == MessageType.USER:
            if self.is_question(text):
                return True
        
        if any(keyword in text for keyword in self.context_keywords):
            return True
        
        if len(text.split()) < 5 and len(text) < 30:
            return False
        
        return True

    def calculate_importance(self, message: Message, all_messages: List[Message], index: int) -> MessageImportance:
        text = message.content
        keywords = self.extract_keywords(text)
        entities = self.extract_entities(text)
        
        importance_score = 0.0
        
        recency_factor = min(1.0, (index + 1) / len(all_messages))
        importance_score += recency_factor * 2.0
        
        if message.role == MessageType.USER:
            importance_score += 1.5
            if self.is_question(text):
                importance_score += 1.0
        
        if message.role == MessageType.ASSISTANT:
            importance_score += 1.0
        
        if len(keywords) >= 3:
            importance_score += 0.5
        if len(entities) >= 2:
            importance_score += 0.5
        
        if len(text) > 200:
            importance_score += 0.3
        
        is_critical = self.is_context_critical(message)
        if is_critical:
            importance_score += 1.0
        
        topics = [k for k in keywords if k not in self.stop_words][:10]
        
        return MessageImportance(
            message=message,
            importance_score=importance_score,
            key_entities=entities,
            key_topics=topics,
            semantic_keywords=keywords,
            is_context_critical=is_critical
        )

    def summarize_message(self, message: Message, max_length: int = 150) -> str:
        text = message.content.strip()
        
        if len(text) <= max_length:
            return text
        
        sentences = re.split(r'[。！？.!?\n]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return text[:max_length] + "…"
        
        summary = sentences[0]
        if len(summary) > max_length:
            summary = summary[:max_length] + "…"
        
        return summary

    def compress_by_importance(
        self,
        messages: List[Message],
        target_count: Optional[int] = None
    ) -> List[Message]:
        if len(messages) <= self.min_messages_to_compress:
            return messages
        
        if target_count is None:
            target_count = max(self.max_messages, int(len(messages) * self.target_compression_ratio))
        
        scored_messages = []
        for idx, msg in enumerate(messages):
            scored = self.calculate_importance(msg, messages, idx)
            scored_messages.append((scored, idx))
        
        scored_messages.sort(key=lambda x: (-x[0].importance_score, x[1]))
        
        kept_indices = set()
        kept_count = 0
        
        for scored, idx in scored_messages:
            if kept_count >= target_count:
                break
            kept_indices.add(idx)
            kept_count += 1
        
        if len(messages) >= 1 and (len(messages) - 1) not in kept_indices:
            kept_indices.add(len(messages) - 1)
        
        if len(messages) >= 2 and (len(messages) - 2) not in kept_indices:
            kept_indices.add(len(messages) - 2)
        
        compressed = []
        for idx, msg in enumerate(messages):
            if idx in kept_indices:
                if not self.is_context_critical(msg) and len(msg.content) > 300:
                    compressed_msg = Message(
                        role=msg.role,
                        content=self.summarize_message(msg),
                        timestamp=msg.timestamp,
                        metadata=msg.metadata
                    )
                    compressed.append(compressed_msg)
                else:
                    compressed.append(msg)
        
        return compressed

    def count_tokens(self, text: str) -> int:
        chinese_chars = len(re.findall(r'[\u4e00-\u9fa5]', text))
        other_tokens = len(re.findall(r'[a-zA-Z0-9]+|[^\s\w]', text))
        return chinese_chars + other_tokens

    def compress(
        self,
        messages: List[Message],
        strategy: str = "importance"
    ) -> CompressionResult:
        original_text = " ".join([m.content for m in messages])
        original_tokens = self.count_tokens(original_text)
        
        if strategy == "importance":
            compressed_messages = self.compress_by_importance(messages)
        else:
            compressed_messages = self.compress_by_importance(messages)
        
        compressed_text = " ".join([m.content for m in compressed_messages])
        compressed_tokens = self.count_tokens(compressed_text)
        
        compression_ratio = 1.0
        if original_tokens > 0:
            compression_ratio = compressed_tokens / original_tokens
        
        semantic_similarity = self._estimate_semantic_similarity(messages, compressed_messages)
        
        return CompressionResult(
            original_messages=messages,
            compressed_messages=compressed_messages,
            compression_ratio=compression_ratio,
            original_token_count=original_tokens,
            compressed_token_count=compressed_tokens,
            semantic_similarity_estimate=semantic_similarity,
            strategy_used=strategy
        )

    def _estimate_semantic_similarity(
        self,
        original: List[Message],
        compressed: List[Message]
    ) -> float:
        if not original or not compressed:
            return 0.0
        
        original_keywords = set()
        for msg in original:
            original_keywords.update(self.extract_keywords(msg.content))
        
        compressed_keywords = set()
        for msg in compressed:
            compressed_keywords.update(self.extract_keywords(msg.content))
        
        if not original_keywords:
            return 1.0
        
        intersection = original_keywords & compressed_keywords
        keyword_similarity = len(intersection) / len(original_keywords)
        
        retention_ratio = len(compressed) / len(original)
        
        combined_similarity = (keyword_similarity * 0.7) + (retention_ratio * 0.3)
        
        return min(1.0, max(0.0, combined_similarity))


def dict_to_message(data: Dict) -> Message:
    role_map = {
        "user": MessageType.USER,
        "assistant": MessageType.ASSISTANT,
        "system": MessageType.SYSTEM
    }
    return Message(
        role=role_map.get(data.get("role", "user"), MessageType.USER),
        content=data.get("content", ""),
        timestamp=data.get("timestamp"),
        metadata=data.get("metadata")
    )


def message_to_dict(msg: Message) -> Dict:
    return {
        "role": msg.role.value,
        "content": msg.content,
        "timestamp": msg.timestamp,
        "metadata": msg.metadata
    }
