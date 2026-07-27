import os

from app.services.pdf_service import PDFService
from app.services.ppt_service import PPTService


class DocumentService:

    @staticmethod
    def extract_text(file_path):

        extension = os.path.splitext(file_path)[1].lower()

        if extension == ".pdf":

            return PDFService.extract_text(file_path)

        elif extension == ".ppt":

            return PPTService.extract_text(file_path)

        elif extension == ".pptx":

            return PPTService.extract_text(file_path)

        return ""