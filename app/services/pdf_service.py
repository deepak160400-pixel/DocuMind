import fitz
from typing import Dict, Any, List


class PDFService:
    """PDF service with accurate page-level metadata extraction."""

    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract all text from PDF."""
        text = ""
        document = fitz.open(file_path)
        for page in document:
            text += page.get_text()
        document.close()
        return text

    @staticmethod
    def extract_text_with_metadata(file_path: str) -> Dict[str, Any]:
        """
        Extract text with accurate page numbers and metadata.
        
        Each page's text is extracted with its exact page number.
        """
        document = fitz.open(file_path)
        pages = []
        full_text = ""

        for page_num, page in enumerate(document, 1):
            page_text = page.get_text()
            full_text += page_text + "\n"
            
            pages.append({
                'page_num': page_num,
                'text': page_text,
                'page_size': page.rect,
            })

        # Get document metadata
        doc_metadata = {}
        try:
            if document.metadata:
                doc_metadata = {
                    'title': document.metadata.get('title', ''),
                    'author': document.metadata.get('author', ''),
                    'subject': document.metadata.get('subject', ''),
                    'keywords': document.metadata.get('keywords', ''),
                    'creator': document.metadata.get('creator', ''),
                    'producer': document.metadata.get('producer', ''),
                    'creation_date': document.metadata.get('creationDate', ''),
                    'mod_date': document.metadata.get('modDate', ''),
                }
        except:
            pass

        document.close()

        return {
            'text': full_text,
            'pages': pages,
            'total_pages': len(pages),
            'metadata': doc_metadata
        }