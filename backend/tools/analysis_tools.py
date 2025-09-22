import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.tools import tool
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import Dict, List, Any
import concurrent.futures
from functools import partial

from utils.helpers import process_single_chunk
from config.settings import DEFAULT_MAX_TOKENS, CHUNK_OVERLAP

@tool
def text_splitter(content: str, max_tokens: int = 50000) -> Dict[str, Any]:
    """
    Split large segment content into manageable chunks for processing.
    
    Args:
        content: Text content to split
        max_tokens: Maximum tokens per chunk (default: 50,000)
        
    Returns:
        Dictionary with chunks and metadata
    """
    try:
        if not content or not content.strip():
            return {
                "success": False,
                "error": "No content provided to split",
                "chunks": [],
                "total_chunks": 0
            }
        
        # Rough estimate: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        
        # Check if splitting is needed
        if len(content) <= max_chars:
            return {
                "success": True,
                "needs_splitting": False,
                "chunks": [content],
                "total_chunks": 1,
                "original_length": len(content),
                "estimated_tokens": len(content) // 4
            }
        
        # Split the content using LangChain's text splitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=max_chars,
            chunk_overlap=1000,  # Small overlap to maintain context
            separators=["\n\n", "\n", ". ", "! ", "? ", " "]  # Natural boundaries
        )
        
        chunks = splitter.split_text(content)
        
        return {
            "success": True,
            "needs_splitting": True,
            "chunks": chunks,
            "total_chunks": len(chunks),
            "original_length": len(content),
            "estimated_tokens": len(content) // 4,
            "chunk_sizes": [len(chunk) for chunk in chunks],
            "chunk_tokens": [len(chunk) // 4 for chunk in chunks]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to split content: {str(e)}",
            "chunks": [],
            "total_chunks": 0
        }

@tool
def process_chunks_parallel(chunks: List[str], segment_info: str = "") -> Dict[str, Any]:
    """
    Process multiple text chunks simultaneously and combine insights.
    This is the core of our hybrid parallel processing approach.
    
    Args:
        chunks: List of text chunks to process
        segment_info: Optional context about the segment (e.g., "Segment 1: 0-120s")
        
    Returns:
        Dictionary with combined insights and analysis
    """
    try:
        if not chunks:
            return {
                "success": False,
                "error": "No chunks provided to process",
                "insights": [],
                "combined_summary": ""
            }
        
        if len(chunks) == 1:
            # Single chunk - process directly
            chunk_result = process_single_chunk(chunks[0], 1, len(chunks), segment_info)
            return {
                "success": True,
                "chunk_results": [chunk_result],
                "combined_insights": chunk_result["insights"],
                "combined_summary": chunk_result["summary"],
                "notable_quotes": chunk_result.get("quotes", []),
                "actionable_takeaways": chunk_result.get("takeaways", []),
                "processing_method": "single_chunk"
            }
        
        # Multiple chunks - process in parallel
        print(f"🔄 Processing {len(chunks)} chunks in parallel...")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(chunks), 5)) as executor:
            # Create tasks for each chunk
            future_to_chunk = {
                executor.submit(process_single_chunk, chunk, i+1, len(chunks), segment_info): i 
                for i, chunk in enumerate(chunks)
            }
            
            # Collect results
            chunk_results = [None] * len(chunks)  # Maintain order
            for future in concurrent.futures.as_completed(future_to_chunk):
                chunk_index = future_to_chunk[future]
                chunk_results[chunk_index] = future.result()
        
        # Combine all chunk results
        combined_insights = []
        combined_summaries = []
        all_quotes = []
        all_takeaways = []
        
        for result in chunk_results:
            if result and result.get("success"):
                combined_insights.extend(result.get("insights", []))
                combined_summaries.append(result.get("summary", ""))
                all_quotes.extend(result.get("quotes", []))
                all_takeaways.extend(result.get("takeaways", []))
        
        # Create final combined summary
        final_summary = " ".join(combined_summaries)
        
        return {
            "success": True,
            "chunk_results": chunk_results,
            "combined_insights": combined_insights[:10],  # Top 10 insights
            "combined_summary": final_summary,
            "notable_quotes": all_quotes[:5],  # Top 5 quotes
            "actionable_takeaways": all_takeaways[:7],  # Top 7 takeaways
            "processing_method": f"parallel_processing_{len(chunks)}_chunks",
            "total_chunks_processed": len(chunks)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to process chunks in parallel: {str(e)}",
            "insights": [],
            "combined_summary": ""
        }