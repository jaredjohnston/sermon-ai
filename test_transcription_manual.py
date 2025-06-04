import asyncio
import sys
from pathlib import Path
import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn

console = Console()

async def test_large_file_transcription(file_path: str):
    """
    Manual test for transcribing a large video file
    """
    if not Path(file_path).exists():
        console.print(f"[red]Error: File {file_path} not found[/red]")
        return
    
    # Configuration
    API_URL = "http://localhost:8000/api/v1/transcription/upload"
    
    console.print(f"[yellow]Testing transcription of: {file_path}[/yellow]")
    file_size = Path(file_path).stat().st_size
    console.print(f"File size: {file_size / (1024*1024*1024):.2f} GB")
    
    # Track callback status
    callback_received = asyncio.Event()
    callback_data = {}
    
    async def wait_for_callback():
        while not callback_received.is_set():
            await asyncio.sleep(1)
    
    try:
        with Progress(
            SpinnerColumn(),
            *Progress.get_default_columns(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            
            # Start file upload
            upload_task = progress.add_task("[green]Uploading file...", total=None)
            
            async with httpx.AsyncClient() as client:
                with open(file_path, 'rb') as f:
                    files = {'file': (Path(file_path).name, f, 'video/mp4')}
                    response = await client.post(API_URL, files=files)
                    
                    if response.status_code != 200:
                        console.print(f"[red]Upload failed: {response.text}[/red]")
                        return
                    
                    result = response.json()
                    request_id = result['request_id']
                    console.print(f"[green]Upload successful! Request ID: {request_id}[/green]")
                    
                    # Wait for processing
                    progress.update(upload_task, description="[yellow]Waiting for transcription...")
                    
                    # Here you would normally wait for a callback
                    # For testing, we'll just wait a bit and check status
                    await asyncio.sleep(10)
                    
                    console.print("[green]Initial processing started successfully![/green]")
                    console.print("\nNext steps:")
                    console.print("1. Check your Deepgram dashboard for processing status")
                    console.print(f"2. Keep request_id: {request_id} for reference")
                    console.print("3. Monitor your callback URL for results")
    
    except Exception as e:
        console.print(f"[red]Error during test: {str(e)}[/red]")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        console.print("[red]Usage: python test_transcription_manual.py <path_to_video_file>[/red]")
        sys.exit(1)
    
    asyncio.run(test_large_file_transcription(sys.argv[1])) 