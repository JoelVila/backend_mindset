import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

print("1. Testing library imports...")
try:
    import easyocr
    print("   [SUCCESS] EasyOCR imported successfully.")
except ImportError as e:
    print(f"   [FAIL] Could not import EasyOCR: {e}")
except Exception as e:
    print(f"   [FAIL] Error importing EasyOCR: {e}")

print("\n2. Testing COPC Adapter logic...")
try:
    from app.adapters.copc_adapter import CopcAdapter
    adapter = CopcAdapter()
    
    # Test valid lookalike (but randomly generated so likely not found)
    test_num = "123456"
    print(f"   Verifying number: {test_num}...")
    result = adapter.verify(test_num)
    print(f"   Result keys: {list(result.keys())}")
    print(f"   Verified status: {result.get('verified')}")
    print(f"   Message: {result.get('msg')}")
    
    if "No se encontró" in result.get("msg", ""):
        print("   [SUCCESS] Adapter correctly handled a non-existent number.")
    
except Exception as e:
    print(f"   [FAIL] Adapter test failed: {e}")
