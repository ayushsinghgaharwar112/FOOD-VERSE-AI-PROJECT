# Vercel Serverless Function Entry Point
import sys
from pathlib import Path

# Add project root to sys.path so 'backend' module is discoverable
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from backend.main import app

# Vercel looks for 'app' or handler in api/index.py
