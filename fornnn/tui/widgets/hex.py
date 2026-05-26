from rich.text import Text
from textual.widgets import Static
from textual.containers import VerticalScroll
from textual.reactive import reactive

class HexViewer(VerticalScroll):
    """
    A scrollable hex viewer widget.
    Uses standard Rich colors for compatibility.
    """
    can_focus = True
    data = reactive(b"")

    def compose(self):
        yield Static(id="hex-content")

    def watch_data(self, data: bytes) -> None:
        content = self.query_one("#hex-content", Static)
        content.update(self._render_hex(data))

    def _render_hex(self, data: bytes) -> Text:
        if not data:
            return Text("No data", style="gray")

        text = Text()
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            
            # Offset (Magenta)
            text.append(f"{i:08x}: ", style="bold magenta")
            
            # Hex bytes (Green)
            hex_part = " ".join(f"{b:02x}" for b in chunk)
            text.append(f"{hex_part:<48} ", style="green")
            
            # ASCII part (Cyan)
            ascii_part = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            text.append(f"|{ascii_part}|", style="cyan")
            text.append("\n")
            
        return text
