#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def main():
    # Get the directory where this script is located
    script_dir = Path(__file__).parent.absolute()
    venv_python = script_dir / "venv" / "bin" / "python"
    
    # Check if we're already running in the virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # Already in venv, just import and run
        import uvicorn
        from app.main import app
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    else:
        # Not in venv, check if venv exists and restart with venv python
        if venv_python.exists():
            print(f"🔄 Switching to virtual environment...")
            print(f"📍 Using: {venv_python}")
            
            # Change to script directory
            os.chdir(script_dir)
            
            # Restart this script with venv python
            os.execv(str(venv_python), [str(venv_python)] + sys.argv)
        else:
            print("❌ Virtual environment not found!")
            print(f"Expected venv at: {venv_python}")
            print("Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
            sys.exit(1)

if __name__ == "__main__":
    main() 