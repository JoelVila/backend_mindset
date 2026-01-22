import sys
import platform
import struct

print(f"Python Version: {sys.version}")
print(f"Platform: {platform.platform()}")
print(f"Architecture: {struct.calcsize('P') * 8} bit")
