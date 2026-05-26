import pytsk3
from fornnn.evidence.base import PartitionInfo

class VolumeManager:
    """
    Handles partition and volume detection using pytsk3.
    """

    def __init__(self, image_handle: pytsk3.Img_Info):
        self.image_handle = image_handle

    def get_partitions(self) -> list[PartitionInfo]:
        partitions = []
        try:
            volume_info = pytsk3.Volume_Info(self.image_handle)
            for part in volume_info:
                partitions.append(PartitionInfo(
                    index=part.addr,
                    start_offset=part.start * volume_info.info.block_size,
                    length=part.len * volume_info.info.block_size,
                    description=part.desc.decode('utf-8', errors='replace'),
                    filesystem_type=None # Will be inferred later
                ))
        except Exception:
            # Not a partitioned image (or unsupported layout), treat as single volume
            partitions.append(PartitionInfo(
                index=0,
                start_offset=0,
                length=self.image_handle.get_size(),
                description="Raw Data / Single Partition",
                filesystem_type=None
            ))
            
        return partitions
