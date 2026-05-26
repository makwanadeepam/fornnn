import typer
from typing import Optional
from fornnn.app import ForNnnApp

app = typer.Typer(help="fornnn - Terminal Forensic File Manager")

@app.command()
def main(
    image_path: Optional[str] = typer.Argument(None, help="Path to the forensic image file"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
):
    """
    Launch the fornnn forensic file manager.
    """
    forensic_app = ForNnnApp(image_path=image_path)
    forensic_app.run()

if __name__ == "__main__":
    app()
