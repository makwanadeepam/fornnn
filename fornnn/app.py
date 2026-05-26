from pathlib import Path
from typing import Optional, List, Union
import os
from functools import partial

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Tree, Button
from textual.containers import Horizontal, Vertical

from fornnn.evidence.manager import EvidenceManager
from fornnn.evidence.vfs.base import VFS, FileType, VFSNode
from fornnn.evidence.base import PartitionInfo, EvidenceMetadata
from fornnn.tui.widgets.tree import ForensicDirectoryTree
from fornnn.tui.widgets.hex import HexViewer
from fornnn.tui.widgets.metadata import MetadataPanel
from fornnn.analysis.engine import ArtifactEngine

class ForNnnApp(App):
    """
    A forensic browser with dynamic theming and high-visibility cursor.
    Uses Textual's built-in theme engine.
    """
    
    # Available themes to cycle through
    THEMES = ["dracula", "monokai", "nord", "tokyo-night", "textual"]
    theme = "dracula"

    CSS = """
    Screen {
        layout: vertical;
    }

    #main-container {
        height: 1fr;
    }

    #left-pane {
        width: 30%;
        border-right: solid $primary;
    }
    
    #left-pane:hover { border-right: solid $accent; }
    #left-pane:focus { border-right: solid $accent; }

    .tree--cursor {
        background: $primary-muted 30%;
        text-style: bold;
    }

    #right-pane {
        width: 70%;
        layout: vertical;
    }

    #metadata-panel {
        height: 50%;
        border-bottom: solid $primary;
    }

    #hex-viewer {
        height: 50%;
        padding: 1;
    }
    
    #hex-viewer:focus { border: solid $accent; }
    
    #hex-content {
        width: 100%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("t", "toggle_theme", "Theme"),
    ]

    def __init__(self, image_path: Optional[str] = None):
        super().__init__()
        self.image_path = str(Path(image_path).resolve()) if image_path else None
        self.metadata = None
        self.artifact_engine = ArtifactEngine()
        self._load_evidence()

    def _load_evidence(self):
        if not self.image_path: return
        try:
            mgr = EvidenceManager()
            self.metadata = mgr.load_evidence(self.image_path)
        except Exception as e:
            self.notify(f"Load failed: {str(e)}", severity="error")

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            if self.metadata:
                yield ForensicDirectoryTree(self.metadata, self.artifact_engine, id="left-pane")
            else:
                yield Static("[bold red]No evidence loaded[/]", id="left-pane")
            
            with Vertical(id="right-pane"):
                yield MetadataPanel(id="metadata-panel")
                yield HexViewer(id="hex-viewer")
        yield Footer()

    def on_mount(self) -> None:
        try:
            self.query_one(ForensicDirectoryTree).focus()
        except Exception:
            pass

    def action_toggle_theme(self) -> None:
        """Cycle through available Textual themes reactively."""
        try:
            curr_idx = self.THEMES.index(self.theme)
        except ValueError:
            curr_idx = 0
            
        next_idx = (curr_idx + 1) % len(self.THEMES)
        new_theme = self.THEMES[next_idx]
        self.theme = new_theme
        self.notify(f"Theme: {new_theme.upper()}", title="UI Update")

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Update UI on highlight."""
        data = event.node.data
        if data:
            self._update_ui_for_node(data, event.node)

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle explicit selection."""
        data = event.node.data
        if data:
            self._update_ui_for_node(data, event.node)

    def _update_ui_for_node(self, node: Union[VFSNode, PartitionInfo, EvidenceMetadata], tree_node=None):
        self.query_one(MetadataPanel).node = node
        tree = self.query_one(ForensicDirectoryTree)

        # Show hex for all selections
        hex_data = b""
        if isinstance(node, VFSNode):
            vfs = tree._find_vfs(tree_node) if tree_node else tree._find_vfs_path("")
            if vfs:
                hex_data = vfs.read_file(str(node.path), length=4096)
                if node.type != FileType.DIR:
                    self.run_worker(self.analyze_file_async(node, vfs), thread=True)
        elif isinstance(node, PartitionInfo):
            if tree.image_handle:
                try:
                    hex_data = tree.image_handle.read(node.start_offset, 4096)
                except Exception:
                    hex_data = b"Error: Could not read partition data"
        elif isinstance(node, EvidenceMetadata):
            if tree.image_handle:
                try:
                    hex_data = tree.image_handle.read(0, 4096)
                except Exception:
                    hex_data = b"Error: Could not read image header"
        
        self.query_one(HexViewer).data = hex_data

    async def analyze_file_async(self, node: VFSNode, vfs: VFS):
        path = str(node.path)
        data = vfs.read_file(path, length=min(node.size, 512 * 1024))
        results = self.artifact_engine.analyze_file(data)
        self.query_one(MetadataPanel).extra_info = results

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "extract-btn":
            panel = self.query_one(MetadataPanel)
            node = panel.node
            if not node: return
            
            tree = self.query_one(ForensicDirectoryTree)
            vfs = None
            if isinstance(node, PartitionInfo):
                 vfs = VFS(tree.image_handle, offset=node.start_offset)
            else:
                for tree_node in tree.walk():
                    if tree_node.data == node:
                        vfs = tree._find_vfs(tree_node)
                        break
            
            if vfs:
                self.run_worker(partial(self.extract_recursive_async, node, vfs), thread=True)

    def extract_recursive_async(self, node: Union[VFSNode, PartitionInfo], vfs: VFS):
        try:
            base_out_path = Path(os.getcwd())
            if isinstance(node, PartitionInfo):
                root_name = f"Partition_{node.index}"
                self.notify(f"Dumping Partition {node.index}...")
                self._extract_vfs_path(vfs, "/", base_out_path / root_name)
            elif isinstance(node, VFSNode):
                if node.type == FileType.FILE:
                    self._save_vfs_file(vfs, node, base_out_path)
                else:
                    self.notify(f"Extracting {node.name}...")
                    self._extract_vfs_path(vfs, node.path, base_out_path / node.name)
            self.notify("Extraction complete", title="Success")
        except Exception as e:
            self.notify(f"Extraction failed: {str(e)}", severity="error")

    def _extract_vfs_path(self, vfs: VFS, vfs_path: str, local_path: Path):
        local_path.mkdir(parents=True, exist_ok=True)
        nodes = vfs.list_directory(vfs_path)
        for node in nodes:
            if node.type == FileType.FILE:
                self._save_vfs_file(vfs, node, local_path)
            elif node.type == FileType.DIR:
                self._extract_vfs_path(vfs, node.path, local_path / node.name)

    def _save_vfs_file(self, vfs: VFS, node: VFSNode, local_parent: Path):
        data = vfs.read_file(str(node.path))
        out_path = local_parent / node.name
        count = 1
        orig_out_path = out_path
        while out_path.exists():
            out_path = orig_out_path.parent / f"{orig_out_path.stem}_{count}{out_path.suffix}"
            count += 1
        with open(out_path, "wb") as f:
            f.write(data)

if __name__ == "__main__":
    app = ForNnnApp()
    app.run()
