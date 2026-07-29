import os
from typing import Dict, Any
from app.services.pdf_service import PDFService
from app.services.ppt_service import PPTService


class DocumentService:
    """Enhanced document service with accurate metadata extraction."""

    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract text from document."""
        try:
            extension = os.path.splitext(file_path)[1].lower()

            if extension == ".pdf":
                return PDFService.extract_text(file_path)
            elif extension in [".ppt", ".pptx"]:
                return PPTService.extract_text(file_path)
            return ""
        except Exception as e:
            print(f"[DocumentService] Error extracting text: {str(e)}")
            return ""

    @staticmethod
    def extract_text_with_metadata(file_path: str) -> Dict[str, Any]:
        """Extract text with accurate page/slide numbers and metadata."""
        try:
            extension = os.path.splitext(file_path)[1].lower()

            if extension == ".pdf":
                return PDFService.extract_text_with_metadata(file_path)
            elif extension in [".ppt", ".pptx"]:
                return PPTService.extract_text_with_metadata(file_path)
            
            return {'text': '', 'pages': [], 'total_pages': 0, 'metadata': {}}
        except Exception as e:
            print(f"[DocumentService] Error extracting text with metadata: {str(e)}")
            return {'text': '', 'pages': [], 'total_pages': 0, 'metadata': {}}

    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """Get file information."""
        try:
            return {
                'filename': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'extension': os.path.splitext(file_path)[1].lower()
            }
        except Exception as e:
            print(f"[DocumentService] Error getting file info: {str(e)}")
            return {}