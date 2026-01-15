import os
import typer
from typing import Optional
from rich.console import Console
from rich.prompt import Prompt
from dotenv import load_dotenv

# Initialize Typer app and Rich console
app = typer.Typer(help="Gemini Local Translator CLI")
console = Console()

# Load environment variables
load_dotenv()

@app.command()
def translate(
    filename: str = typer.Argument(..., help="Path to the file to be translated"),
    target_lang: str = typer.Option("Traditional Chinese", "--target-lang", "-l", help="Target language for translation"),
    model: str = typer.Option("flash", "--model", "-m", help="Gemini model to use: 'flash' or 'pro'"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="Google Gemini API Key")
):
    """
    Translates a document (PDF, DOCX, MD) using Google Gemini.
    """

    # 1. API Key Handling
    key = api_key or os.getenv("GOOGLE_API_KEY")
    if not key:
        console.print("[bold yellow]API Key not found in environment variables.[/bold yellow]")
        key = Prompt.ask("Please enter your Google Gemini API Key", password=True)

    if not key:
        console.print("[bold red]Error: API Key is required to proceed.[/bold red]")
        raise typer.Exit(code=1)

    os.environ["GOOGLE_API_KEY"] = key

    # 2. File Validation
    if not os.path.exists(filename):
        console.print(f"[bold red]Error: File '{filename}' not found.[/bold red]")
        raise typer.Exit(code=1)

    console.print(f"[bold green]Starting translation for:[/bold green] {filename}")
    console.print(f"Target Language: {target_lang}")
    console.print(f"Model: {model}")

    # Initialize Gemini Client
    try:
        from src.services.gemini import GeminiClient
        client = GeminiClient(model_name=model)
    except Exception as e:
        console.print(f"[bold red]Error initializing Gemini Client: {e}[/bold red]")
        raise typer.Exit(code=1)

    # Route to appropriate handler based on file extension
    ext = os.path.splitext(filename)[1].lower()
    output_file = None

    try:
        with console.status("[bold green]Processing...[/bold green]", spinner="dots"):
            if ext == ".md":
                from src.handlers.markdown import MarkdownHandler
                handler = MarkdownHandler(client, target_lang)
                output_file = handler.process(filename)
            elif ext == ".docx":
                from src.handlers.docx import DocxHandler
                handler = DocxHandler(client, target_lang)
                output_file = handler.process(filename)
            elif ext == ".pdf":
                from src.handlers.pdf import PdfHandler
                handler = PdfHandler(client, target_lang)
                output_file = handler.process(filename)
            else:
                console.print(f"[bold red]Error: Unsupported file format '{ext}'. Supported formats: .md, .docx, .pdf[/bold red]")
                raise typer.Exit(code=1)

        if output_file:
             console.print(f"[bold green]Translation completed successfully![/bold green]")
             console.print(f"Output saved to: {output_file}")

    except Exception as e:
        console.print(f"[bold red]An error occurred during translation: {e}[/bold red]")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
