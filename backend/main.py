from youtube_transcript_api import YouTubeTranscriptApi
from langchain.tools import tool
from typing import Dict, List, Any
import re

# for agent
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
import os

from pydantic import BaseModel

import asyncio
import concurrent.futures
from functools import partial

# Load environment variables
load_dotenv()


import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline import run_complete_pipeline

# Update main function
def main():
    """
    Main function to test the complete pipeline
    """
    print("🎬 YouTube Video Analysis System - Complete Pipeline")
    print("=" * 60)

    test_url = "https://www.youtube.com/watch?v=TK9dl48fsAI"
    
    print("Testing Complete Pipeline (Agent 1 + Agent 2)...")
    result = run_complete_pipeline(test_url)
    
    if result:
        print("\n✨ Complete pipeline test completed successfully!")
    else:
        print("\n❌ Complete pipeline test failed!")

if __name__ == "__main__":
    main()