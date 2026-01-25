"""Text chunking strategies for RAG."""

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """A chunk of text with metadata."""

    content: str
    index: int
    start_char: int
    end_char: int
    metadata: dict | None = None


class BaseChunker(ABC):
    """Base text chunker."""

    @abstractmethod
    def chunk(self, text: str) -> list[TextChunk]:
        """Split text into chunks."""
        pass


class FixedSizeChunker(BaseChunker):
    """
    Fixed-size chunking with overlap.
    Simple but effective for most use cases.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = " ",
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def chunk(self, text: str) -> list[TextChunk]:
        """Split text into fixed-size chunks with overlap."""
        if not text:
            return []

        words = text.split(self.separator)
        chunks = []
        start_idx = 0
        char_pos = 0

        while start_idx < len(words):
            # Get words for this chunk
            end_idx = start_idx + self.chunk_size
            chunk_words = words[start_idx:end_idx]
            chunk_text = self.separator.join(chunk_words)

            # Calculate character positions
            start_char = char_pos
            end_char = start_char + len(chunk_text)

            chunks.append(TextChunk(
                content=chunk_text,
                index=len(chunks),
                start_char=start_char,
                end_char=end_char,
            ))

            # Move start position (with overlap)
            move = max(1, self.chunk_size - self.chunk_overlap)
            start_idx += move
            char_pos += len(self.separator.join(words[start_idx - move:start_idx]))

        return chunks


class SemanticChunker(BaseChunker):
    """
    Semantic chunking based on natural boundaries.
    Respects paragraph and sentence boundaries.
    """

    def __init__(
        self,
        max_chunk_size: int = 1000,
        min_chunk_size: int = 100,
        overlap_sentences: int = 1,
    ):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_sentences = overlap_sentences

    def _split_into_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs."""
        paragraphs = re.split(r"\n\s*\n", text)
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences."""
        # Simple sentence splitter (works for most cases)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk(self, text: str) -> list[TextChunk]:
        """Split text respecting semantic boundaries."""
        if not text:
            return []

        paragraphs = self._split_into_paragraphs(text)
        chunks = []
        current_chunk = []
        current_length = 0
        char_pos = 0
        previous_sentences: list[str] = []

        for para in paragraphs:
            # If paragraph is too long, split into sentences
            if len(para) > self.max_chunk_size:
                sentences = self._split_into_sentences(para)

                for sentence in sentences:
                    if current_length + len(sentence) > self.max_chunk_size and current_chunk:
                        # Save current chunk
                        chunk_text = " ".join(current_chunk)
                        chunks.append(TextChunk(
                            content=chunk_text,
                            index=len(chunks),
                            start_char=char_pos,
                            end_char=char_pos + len(chunk_text),
                        ))
                        char_pos += len(chunk_text) + 1

                        # Start new chunk with overlap
                        previous_sentences = current_chunk[-self.overlap_sentences:]
                        current_chunk = previous_sentences.copy()
                        current_length = sum(len(s) for s in current_chunk)

                    current_chunk.append(sentence)
                    current_length += len(sentence) + 1

            elif current_length + len(para) > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = "\n\n".join(current_chunk)
                chunks.append(TextChunk(
                    content=chunk_text,
                    index=len(chunks),
                    start_char=char_pos,
                    end_char=char_pos + len(chunk_text),
                ))
                char_pos += len(chunk_text) + 2

                # Start new chunk (no overlap for paragraphs)
                current_chunk = [para]
                current_length = len(para)

            else:
                current_chunk.append(para)
                current_length += len(para) + 2

        # Don't forget the last chunk
        if current_chunk and current_length >= self.min_chunk_size:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(TextChunk(
                content=chunk_text,
                index=len(chunks),
                start_char=char_pos,
                end_char=char_pos + len(chunk_text),
            ))

        return chunks


class RecursiveChunker(BaseChunker):
    """
    Recursive chunking with multiple separators.
    Tries to split on larger boundaries first.
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: list[str] | None = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " "]

    def _split_text(
        self,
        text: str,
        separators: list[str],
    ) -> list[str]:
        """Recursively split text."""
        if not separators:
            return [text]

        separator = separators[0]
        remaining_separators = separators[1:]

        splits = text.split(separator)

        result = []
        for split in splits:
            if len(split) <= self.chunk_size:
                result.append(split)
            elif remaining_separators:
                result.extend(self._split_text(split, remaining_separators))
            else:
                # Force split at chunk_size
                for i in range(0, len(split), self.chunk_size - self.chunk_overlap):
                    result.append(split[i:i + self.chunk_size])

        return result

    def _merge_splits(self, splits: list[str], separator: str) -> list[str]:
        """Merge splits to reach target chunk size."""
        merged = []
        current = []
        current_length = 0

        for split in splits:
            if current_length + len(split) + len(separator) > self.chunk_size and current:
                merged.append(separator.join(current))
                # Keep overlap
                overlap_text = separator.join(current)
                overlap_start = max(0, len(overlap_text) - self.chunk_overlap)
                overlap = overlap_text[overlap_start:]
                current = [overlap] if overlap else []
                current_length = len(overlap)

            current.append(split)
            current_length += len(split) + len(separator)

        if current:
            merged.append(separator.join(current))

        return merged

    def chunk(self, text: str) -> list[TextChunk]:
        """Split text recursively."""
        if not text:
            return []

        # Split recursively
        splits = self._split_text(text, self.separators)

        # Merge small splits
        merged = self._merge_splits(splits, " ")

        # Create chunks
        chunks = []
        char_pos = 0

        for i, content in enumerate(merged):
            chunks.append(TextChunk(
                content=content,
                index=i,
                start_char=char_pos,
                end_char=char_pos + len(content),
            ))
            char_pos += len(content) + 1

        return chunks


def get_chunker(
    strategy: str = "semantic",
    **kwargs,
) -> BaseChunker:
    """Get chunker by strategy name."""
    chunkers = {
        "fixed": FixedSizeChunker,
        "semantic": SemanticChunker,
        "recursive": RecursiveChunker,
    }

    chunker_class = chunkers.get(strategy, SemanticChunker)
    return chunker_class(**kwargs)
