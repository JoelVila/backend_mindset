
class OCRAdapter:
    _reader = None

    @classmethod
    def get_reader(cls):
        if cls._reader is None:
            import easyocr
            # Initialize strictly for Spanish as per context implies
            cls._reader = easyocr.Reader(['es'])
        return cls._reader

    def extract_text(self, image_content):
        """
        Extracts text from image content (bytes or path).
        Returns a list of strings found.
        """
        try:
            reader = self.get_reader()
            result = reader.readtext(image_content, detail=0)
            return result
        except Exception as e:
            print(f"OCR Error: {e}")
            return []
