from typing import List


class Chunker:

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 100
    ):

        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_text(
        self,
        text: str
    ) -> List[str]:

        if not text:
            return []

        chunks = []

        start = 0

        while start < len(text):

            end = start + self.chunk_size

            chunk = text[start:end]

            chunks.append(chunk.strip())

            start += self.chunk_size - self.overlap

        return chunks