from enum import Enum
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

class EvidenceFormat(str, Enum):
    RAW = "RAW"
    E01 = "E01"
    VMDK = "VMDK"
    VHD = "VHD"
    ISO = "ISO"
    UNKNOWN = "UNKNOWN"

class PartitionInfo(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    index: int
    start_offset: int
    length: int
    description: str
    filesystem_type: Optional[str] = None

class EvidenceMetadata(BaseModel):
    format: EvidenceFormat
    size: int
    path: Path
    partitions: List[PartitionInfo] = []
