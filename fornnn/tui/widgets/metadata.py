from textual.widgets import Static, Button
from textual.reactive import reactive
from textual.containers import Vertical, Horizontal
from rich.markup import escape
from fornnn.evidence.vfs.base import VFSNode, FileType
from fornnn.evidence.base import PartitionInfo, EvidenceMetadata

class MetadataPanel(Vertical):
    """
    Displays metadata with a theme-aware layout.
    Values are escaped to prevent MarkupErrors.
    """
    node = reactive(None)
    extra_info = reactive({})

    CSS = """
    MetadataPanel {
        layout: vertical;
        background: $surface;
        color: $text;
        padding: 1 2;
    }
    #metadata-text {
        height: 1fr;
        overflow-y: scroll;
        border: solid $primary-muted;
        padding: 1;
        background: $boost;
    }
    #button-row {
        height: 5;
        width: 100%;
        content-align: center middle;
        margin-top: 1;
    }
    #extract-btn { 
        background: $success; 
        color: $text;
        width: 32;
        height: 3;
        text-style: bold;
        border: none;
    }
    #extract-btn:hover { background: $success-lighten-1; }
    """

    def compose(self):
        yield Static("No item selected", id="metadata-text")
        with Horizontal(id="button-row"):
            yield Button("EXTRACT", id="extract-btn")

    def watch_node(self, node) -> None:
        self.extra_info = {}
        self._update_display()

    def watch_extra_info(self, info: dict) -> None:
        self._update_display()

    def _update_display(self) -> None:
        text_widget = self.query_one("#metadata-text", Static)
        extract_btn = self.query_one("#extract-btn", Button)
        
        if not self.node:
            text_widget.update("[italic $text-muted]No item selected[/]")
            extract_btn.display = False
            return

        extract_btn.display = True

        if isinstance(self.node, VFSNode):
            md = [
                f"[bold cyan]Name:[/bold cyan] {escape(str(self.node.name))}",
                f"[bold cyan]Path:[/bold cyan] {escape(str(self.node.path))}",
                f"[bold magenta]Size:[/bold magenta] {escape(str(self.node.size))} bytes",
                f"[bold red]Modified:[/bold red] {escape(str(self.node.mtime))}",
            ]
            if self.extra_info:
                md.append(f"[bold yellow]MIME:[/bold yellow] {escape(str(self.extra_info.get('mime', '...')))}")
                md.append(f"[bold yellow]Entropy:[/bold yellow] {self.extra_info.get('entropy', 0.0):.4f}")
                hashes = self.extra_info.get('hashes', {})
                if hashes:
                    md.append(f"[bold green]MD5:[/bold green] {escape(str(hashes.get('md5')))}")
                    md.append(f"[bold green]SHA256:[/bold green] {escape(str(hashes.get('sha256')))}")
        elif isinstance(self.node, PartitionInfo):
            md = [
                f"[bold magenta]FULL PARTITION {self.node.index}[/bold magenta]",
                f"[bold cyan]Description:[/bold cyan] {escape(str(self.node.description))}",
                f"[bold magenta]Start Offset:[/bold magenta] {escape(str(self.node.start_offset))}",
                f"[bold magenta]Length:[/bold magenta] {escape(str(self.node.length))} bytes",
                "",
                "[italic yellow]Note: Extraction will dump the entire filesystem.[/]"
            ]
        elif isinstance(self.node, EvidenceMetadata):
            md = [
                f"[bold cyan]IMAGE ROOT[/bold cyan]",
                f"[bold cyan]File:[/bold cyan] {escape(str(self.node.path.name))}",
                f"[bold magenta]Total Size:[/bold magenta] {escape(str(self.node.size))} bytes",
                f"[bold yellow]Format:[/bold yellow] {escape(str(self.node.format))}",
                f"[bold magenta]Partitions Found:[/bold magenta] {len(self.node.partitions)}",
                "",
                "[italic yellow]Select a partition or folder to explore content.[/]"
            ]
            extract_btn.display = False # Don't extract the whole image file (already on disk)
        else:
            md = [f"Selected: {escape(str(self.node))}"]

        text_widget.update("\n".join(md))
