import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from fornnn.evidence.vfs.base import VFS, VFSNode, FileType

class LocalVFS(VFS):
    """
    VFS implementation for local directories.
    """
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self._fs = None # Not a pytsk3 FS

    def list_directory(self, path: str = "/") -> List[VFSNode]:
        full_path = self.root_path / path.lstrip("/")
        if not full_path.is_dir():
            return []

        nodes = []
        try:
            for entry in os.scandir(full_path):
                nodes.append(self._entry_to_node(entry, path))
        except Exception:
            pass
        return nodes

    def _entry_to_node(self, entry: os.DirEntry, parent_path: str) -> VFSNode:
        stat = entry.stat()
        file_type = FileType.FILE
        if entry.is_dir():
            file_type = FileType.DIR
        elif entry.is_symlink():
            file_type = FileType.LINK

        name = entry.name
        full_path = f"{parent_path.rstrip('/')}/{name}"

        return VFSNode(
            name=name,
            path=full_path,
            size=stat.st_size,
            type=file_type,
            mtime=datetime.fromtimestamp(stat.st_mtime),
            atime=datetime.fromtimestamp(stat.st_atime),
            ctime=datetime.fromtimestamp(stat.st_ctime),
            inode=stat.st_ino
        )

    def read_file(self, path: str, offset: int = 0, length: int = -1) -> bytes:
        full_path = self.root_path / path.lstrip("/")
        try:
            with open(full_path, "rb") as f:
                f.seek(offset)
                if length == -1:
                    return f.read()
                return f.read(length)
        except Exception:
            return b""
