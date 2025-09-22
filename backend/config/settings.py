import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0
DEFAULT_MAX_TOKENS = 50000

# Video processing settings
DEFAULT_SEGMENTS = 5
CHUNK_OVERLAP = 1000