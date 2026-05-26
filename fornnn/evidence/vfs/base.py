import pytsk3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

class FileType(Enum):
    FILE = "f"
    DIR = "d"
    LINK = "l"
    SPECIAL = "s"
    DELETED = "x"
    UNKNOWN = "?"

@dataclass
class VFSNode:
    name: str
    path: str
    size: int
    type: FileType
    mtime: Optional[datetime] = None
    atime: Optional[datetime] = None
    ctime: Optional[datetime] = None
    crtime: Optional[datetime] = None
    is_deleted: bool = False
    inode: int = 0

class VFS:
    """
    Virtual File System layer for forensic images.
    """
    def __init__(self, image_handle: pytsk3.Img_Info, offset: int = 0):
        self.image_handle = image_handle
        self.offset = offset
        self._fs: Optional[pytsk3.FS_Info] = None
        self._open_fs()

    def _open_fs(self):
        try:
            self._fs = pytsk3.FS_Info(self.image_handle, offset=self.offset)
        except Exception as e:
            # Handle unsupported filesystem
            self._fs = None

    def list_directory(self, path: str = "/") -> List[VFSNode]:
        if not self._fs:
            return []

        nodes = []
        try:
            directory = self._fs.open_dir(path=path)
            for entry in directory:
                if not hasattr(entry, "info") or not entry.info.name:
                    continue
                
                name = entry.info.name.name.decode('utf-8', errors='replace')
                if name in [".", ".."]:
                    continue

                nodes.append(self._entry_to_node(entry, path))
        except Exception:
            pass
        
        return nodes

    def _entry_to_node(self, entry: pytsk3.File, parent_path: str) -> VFSNode:
        info = entry.info
        meta = info.meta
        
        file_type = FileType.UNKNOWN
        if info.name.type == pytsk3.TSK_FS_NAME_TYPE_DIR:
            file_type = FileType.DIR
        elif info.name.type == pytsk3.TSK_FS_NAME_TYPE_REG:
            file_type = FileType.FILE

        is_deleted = False
        if info.name.flags == pytsk3.TSK_FS_NAME_FLAG_UNALLOC:
            is_deleted = True
            file_type = FileType.DELETED

        name = info.name.name.decode('utf-8', errors='replace')
        full_path = f"{parent_path.rstrip('/')}/{name}"

        return VFSNode(
            name=name,
            path=full_path,
            size=meta.size if meta else 0,
            type=file_type,
            mtime=datetime.fromtimestamp(meta.mtime) if meta and meta.mtime else None,
            atime=datetime.fromtimestamp(meta.atime) if meta and meta.atime else None,
            ctime=datetime.fromtimestamp(meta.ctime) if meta and meta.ctime else None,
            crtime=datetime.fromtimestamp(meta.crtime) if meta and meta.crtime else None,
            is_deleted=is_deleted,
            inode=meta.addr if meta else 0
        )

    def read_file(self, path: str, offset: int = 0, length: int = -1) -> bytes:
        if not self._fs:
            return b""
        
        try:
            file_obj = self._fs.open(path)
            if length == -1:
                length = file_obj.info.meta.size
            return file_obj.read_random(offset, length)
        except Exception:
            return b""
