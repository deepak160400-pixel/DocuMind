from typing import List, Tuple, Dict, Any
import re


class Chunker:
    """Enhanced chunker with accurate page tracking and overlap."""

    def __init__(
        self,
        chunk_size: int = 500,
        overlap: int = 100
    ):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_text(self, text: str) -> List[str]:
        """Legacy split method."""
        if not text:
            return []
        return self._split_with_overlap(text)

    def split_text_with_metadata(
        self, 
        text: str, 
        pages: List[Dict] = None
    ) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Split text into chunks with accurate page metadata.
        """
        if not text:
            return [], []

        if pages and len(pages) > 0:
            return self._chunk_by_pages(pages)
        
        return self._chunk_full_text(text)

    def _chunk_by_pages(self, pages: List[Dict]) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Chunk text page by page for accurate page number tracking."""
        chunks = []
        metadata = []
        chunk_index = 0

        for page_data in pages:
            page_num = page_data.get('page_num', 'Unknown')
            page_text = page_data.get('text', '').strip()
            
            if not page_text:
                continue
            
            page_text = self._clean_text(page_text)
            page_chunks = self._split_with_overlap(page_text)
            
            for chunk in page_chunks:
                if chunk.strip():
                    chunks.append(chunk.strip())
                    metadata.append({
                        'chunk_index': chunk_index,
                        'chunk_size': len(chunk),
                        'document_name': None,
                        'page': page_num,
                        'section': f'Page {page_num}',
                        'page_exact': True,
                        'text_preview': chunk[:100]
                    })
                    chunk_index += 1

        if not chunks:
            full_text = ' '.join([p.get('text', '') for p in pages])
            return self._chunk_full_text(full_text)
        
        return chunks, metadata

    def _chunk_full_text(self, text: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Fallback method: chunk full text with estimated page numbers."""
        text = self._clean_text(text)
        raw_chunks = self._split_with_overlap(text)
        
        chunks = []
        metadata = []
        
        for i, chunk in enumerate(raw_chunks):
            chunks.append(chunk)
            metadata.append({
                'chunk_index': i,
                'chunk_size': len(chunk),
                'document_name': None,
                'page': 'Unknown',
                'section': 'Unknown',
                'page_exact': False,
                'text_preview': chunk[:100]
            })
        
        return chunks, metadata

    def _split_with_overlap(self, text: str) -> List[str]:
        """Split text with overlap and smart boundaries."""
        if not text:
            return []

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size

            # Try to end at a sentence boundary
            if end < text_length:
                segment = text[start:min(end + 50, text_length)]
                # Try various sentence boundaries
                boundaries = [
                    segment.rfind('. '),
                    segment.rfind('! '),
                    segment.rfind('? '),
                    segment.rfind('\n\n'),
                    segment.rfind('.'),
                    segment.rfind('!'),
                    segment.rfind('?')
                ]
                sentence_end = max(boundaries)
                if sentence_end != -1 and sentence_end < len(segment) - 10:
                    end = start + sentence_end + 1

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start += self.chunk_size - self.overlap

            if start >= text_length:
                break

            if start + self.chunk_size >= text_length:
                remaining = text[start:].strip()
                if remaining:
                    chunks.append(remaining)
                break

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = text.strip()
        return text