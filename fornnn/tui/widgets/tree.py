import pytsk3
from rich.text import Text
from rich.markup import escape
from textual.widgets import Tree
from fornnn.evidence.vfs.base import VFS, FileType, VFSNode
from fornnn.evidence.vfs.local import LocalVFS
from fornnn.evidence.base import EvidenceMetadata, PartitionInfo
from fornnn.analysis.engine import ArtifactEngine
from typing import Optional

class ForensicDirectoryTree(Tree):
    """
    A Tree widget with high-visibility selection cursor using default theming.
    """
    def __init__(self, metadata: EvidenceMetadata, artifact_engine: ArtifactEngine, *args, **kwargs):
        self.metadata = metadata
        self.artifact_engine = artifact_engine
        self.image_handle: Optional[pytsk3.Img_Info] = None
        self._open_image()
        
        super().__init__(self.metadata.path.name, data=self.metadata, *args, **kwargs)
        self.show_guides = True
        self.guide_depth = 2

    def _open_image(self):
        from fornnn.evidence.formats.sources import RawSource, E01Source
        from fornnn.evidence.base import EvidenceFormat
        import pytsk3
        
        if self.metadata.path.is_dir():
            return

        try:
            if self.metadata.format == EvidenceFormat.E01:
                self.image_handle = E01Source.open(self.metadata.path)
            else:
                self.image_handle = RawSource(self.metadata.path)
        except Exception:
            pass

    def on_mount(self) -> None:
        if self.metadata.path.is_dir():
            vfs = LocalVFS(self.metadata.path)
            self.root.data = vfs
            self._load_directory(self.root, vfs)
        else:
            self._load_partitions(self.root)
        self.root.expand()

    def _load_partitions(self, node):
        if not self.metadata.partitions:
            vfs = VFS(self.image_handle, offset=0)
            node.data = vfs 
            self._load_directory(node, vfs)
            return

        for part in self.metadata.partitions:
            label = f"Part {part.index}: {part.description}"
            node.add(label, data=part, allow_expand=True)

    def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        node = event.node
        if node.children:
            return

        data = node.data
        if isinstance(data, PartitionInfo):
            vfs = VFS(self.image_handle, offset=data.start_offset)
            node.data = vfs 
            if vfs._fs:
                self._load_directory(node, vfs)
            else:
                node.add("[bold $error]No Filesystem Found[/]", allow_expand=False)
        elif isinstance(data, VFSNode) and data.type == FileType.DIR:
            vfs = self._find_vfs(node)
            if vfs:
                self._load_directory(node, vfs)

    def _load_directory(self, node, vfs: VFS):
        path = "/"
        if isinstance(node.data, VFSNode):
            path = str(node.data.path)
            
        nodes = vfs.list_directory(path)
        if not nodes:
            node.add("(Empty)", allow_expand=False)
            return

        nodes.sort(key=lambda x: (x.type != FileType.DIR, x.name.lower()))
        
        for vfs_node in nodes:
            if isinstance(vfs, LocalVFS):
                if self.artifact_engine.is_ignored(vfs_node.path.lstrip("/")):
                    continue
            node.add(
                vfs_node.name,
                data=vfs_node,
                allow_expand=(vfs_node.type == FileType.DIR)
            )

    async def locate_node(self, node_data: VFSNode, vfs: VFS):
        path_segments = node_data.path.lstrip("/").split("/")
        curr_node = self.root
        if not self.metadata.path.is_dir():
            target_offset = vfs.offset
            for child in self.root.children:
                if (isinstance(child.data, PartitionInfo) and child.data.start_offset == target_offset) or \
                   (isinstance(child.data, VFS) and child.data.offset == target_offset):
                    if isinstance(child.data, PartitionInfo):
                        child.data = VFS(self.image_handle, offset=target_offset)
                    curr_node = child
                    break
        
        for segment in path_segments:
            if not segment: continue
            if not curr_node.is_expanded: curr_node.expand()
            found = False
            for child in curr_node.children:
                if isinstance(child.data, VFSNode) and child.data.name == segment:
                    curr_node = child
                    found = True
                    break
            if not found: break
        
        self.select_node(curr_node)
        self.scroll_to_node(curr_node)
        self.focus()

    def _find_vfs(self, node) -> Optional[VFS]:
        curr = node
        while curr:
            if isinstance(curr.data, (VFS, LocalVFS)):
                return curr.data
            if isinstance(curr.data, PartitionInfo):
                vfs = VFS(self.image_handle, offset=curr.data.start_offset)
                curr.data = vfs
                return vfs
            curr = curr.parent
        return None

    def _find_vfs_path(self, path: str) -> Optional[VFS]:
        for tn in self.walk():
            if isinstance(tn.data, (VFS, LocalVFS)):
                return tn.data
        return None

    def render_label(self, node, base_style, control_style) -> Text:
        label = node.label
        if isinstance(label, str):
            if "[" in label and "]" in label:
                node_label = Text.from_markup(label)
            else:
                node_label = Text(label)
        else:
            node_label = label.copy()
            
        data = node.data
        
        # Add selection cursor
        if node == self.cursor_node:
            node_label = Text(">>> ", style="bold magenta") + node_label
        
        if isinstance(data, VFSNode):
            if data.type == FileType.DIR:
                node_label.stylize("bold blue")
            elif getattr(data, "is_deleted", False):
                node_label.stylize("strike red")
            elif data.type == FileType.FILE:
                node_label.stylize("green")
        elif isinstance(data, (PartitionInfo, VFS, EvidenceMetadata)):
            node_label.stylize("bold cyan")
                
        return node_label
