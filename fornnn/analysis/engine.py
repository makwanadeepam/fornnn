import hashlib
import math
import magic
from typing import Dict, Any, List, Optional

class ArtifactEngine:
    """
    Minimal engine for calculating file metadata.
    """

    def __init__(self):
        self._magic = magic.Magic(uncompress=True)

    def analyze_file(self, data: bytes) -> Dict[str, Any]:
        if not data:
            return {}

        return {
            "hashes": self.calculate_hashes(data),
            "entropy": self.calculate_entropy(data),
            "mime": self.detect_mime(data),
        }

    def calculate_hashes(self, data: bytes) -> Dict[str, str]:
        return {
            "md5": hashlib.md5(data).hexdigest(),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    def calculate_entropy(self, data: bytes) -> float:
        if not data: return 0.0
        entropy = 0
        length = len(data)
        for x in range(256):
            p_x = float(data.count(x)) / length
            if p_x > 0:
                entropy += - p_x * math.log(p_x, 2)
        return entropy

    def detect_mime(self, data: bytes) -> str:
        try:
            return self._magic.from_buffer(data)
        except Exception:
            return "unknown"
