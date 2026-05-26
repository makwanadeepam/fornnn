import os
import pytsk3
from pathlib import Path
from typing import Optional
from fornnn.evidence.base import EvidenceFormat, EvidenceMetadata, PartitionInfo
from fornnn.evidence.formats.sources import RawSource, E01Source
from fornnn.evidence.volume import VolumeManager

class EvidenceManager:
    """
    Handles automatic detection and opening of forensic evidence.
    """

    @staticmethod
    def detect_format(path: Path) -> EvidenceFormat:
        if not path.exists():
            return EvidenceFormat.UNKNOWN

        if path.is_dir():
            return EvidenceFormat.RAW # Treat directory as "raw" for now or add a DIR format

        suffix = path.suffix.lower()
        
        # Simple suffix-based detection
        if suffix in [".e01", ".ex01"]:
            return EvidenceFormat.E01
        elif suffix in [".raw", ".dd", ".img", ".001"]:
            return EvidenceFormat.RAW
        elif suffix == ".vmdk":
            return EvidenceFormat.VMDK
        elif suffix in [".vhd", ".vhdx"]:
            return EvidenceFormat.VHD
        elif suffix == ".iso":
            return EvidenceFormat.ISO
        
        return EvidenceFormat.UNKNOWN

    def load_evidence(self, path_str: str) -> EvidenceMetadata:
        path = Path(path_str)
        fmt = self.detect_format(path)
        
        image_handle: Optional[pytsk3.Img_Info] = None
        
        if fmt == EvidenceFormat.E01:
            image_handle = E01Source.open(path)
        elif fmt == EvidenceFormat.RAW:
            image_handle = RawSource(path)
        else:
            # Fallback to RawSource for unknown/generic formats for now
            image_handle = RawSource(path)

        vol_mgr = VolumeManager(image_handle)
        partitions = vol_mgr.get_partitions()

        metadata = EvidenceMetadata(
            format=fmt,
            size=image_handle.get_size(),
            path=path,
            partitions=partitions
        )
        
        return metadata
