
import sys
import os
import unittest
from PIL import Image, ImageDraw, ImageFont
import io

# Add project root to path
sys.path.append(os.getcwd())

try:
    from app.services.biometric_service import BiometricService
    import easyocr
    import torch
except ImportError as e:
    print(f"CRITICAL: Failed to import dependencies: {e}")
    sys.exit(1)

class TestBiometricsAndOCR(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("\n--- Setting up Test Environment ---")
        # Paths to generated face images
        cls.face_a_path = "C:/Users/User/.gemini/antigravity/brain/b589cb0d-5cea-4ef7-ba73-258552d12c88/face_a_passport_1769071328144.png"
        cls.face_c_path = "C:/Users/User/.gemini/antigravity/brain/b589cb0d-5cea-4ef7-ba73-258552d12c88/face_c_distinct_1769071815497.png"
        
        # Check if files exist
        if not os.path.exists(cls.face_a_path):
            raise FileNotFoundError(f"Face A not found at {cls.face_a_path}")
        if not os.path.exists(cls.face_c_path):
             raise FileNotFoundError(f"Face C not found at {cls.face_c_path}")
             
        cls.biometric_service = BiometricService()
        cls.ocr_reader = easyocr.Reader(['es'], gpu=False) # Force CPU for compatibility
        
    def test_1_ocr_extraction(self):
        print("\n[Test 1] Testing OCR with synthetic image...")
        
        # Create an image with a number
        img = Image.new('RGB', (1500, 150), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        
        # Try to use Arial font
        try:
           font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 60)
        except Exception as e:
           print(f"Warning: Could not load arial.ttf: {e}. Using default.")
           font = None
           
        text_to_find = "Colegiado: 99887766"
        d.text((20, 40), text_to_find, fill=(0, 0, 0), font=font)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        
        # Run OCR
        result = self.ocr_reader.readtext(img_bytes, detail=0)
        full_text = " ".join(result)
        print(f"   OCR Output: '{full_text}'")
        
        # Verify
        self.assertIn("99887766", full_text.replace(" ", ""), "OCR should find the colegiado number")
        print("   [SUCCESS] OCR extracted number correctly.")

    def test_2_biometric_match(self):
        print("\n[Test 2] Testing Biometric Match (Same Face)...")
        
        # Read files
        with open(self.face_a_path, "rb") as f:
            img_a_bytes = f.read()
            
        result = self.biometric_service.verify_identity(img_a_bytes, img_a_bytes)
        
        print(f"   Match Result: Verified={result.get('verified')}, Distance={result.get('distance')}, Confidence={result.get('confidence_score')}")
        
        self.assertTrue(result.get('verified'), "Same image should match")
        self.assertLess(result.get('distance'), 0.4, "Distance should be very low for identical images")
        print("   [SUCCESS] Biometric confirmed match.")

    def test_3_biometric_mismatch(self):
        print("\n[Test 3] Testing Biometric Mismatch (Different Faces)...")
        
        with open(self.face_a_path, "rb") as fa:
            img_a_bytes = fa.read()
        with open(self.face_c_path, "rb") as fc:
            img_c_bytes = fc.read()
            
        result = self.biometric_service.verify_identity(img_a_bytes, img_c_bytes)
        
        print(f"   Mismatch Result: Verified={result.get('verified')}, Distance={result.get('distance')}, Confidence={result.get('confidence_score')}")
        
        self.assertFalse(result.get('verified'), "Different faces should NOT match")
        self.assertGreater(result.get('distance'), 0.7, "Distance should be high for different faces")
        print("   [SUCCESS] Biometric correctly rejected mismatch.")

if __name__ == '__main__':
    unittest.main()
