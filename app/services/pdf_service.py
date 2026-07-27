import fitz


class PDFService:

    @staticmethod
    def extract_text(file_path):

        text = ""

        document = fitz.open(file_path)

        for page in document:

            text += page.get_text()

        document.close()

        return text