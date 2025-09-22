from typing import Dict, List, Any
from pydantic import BaseModel

# Pydantic model for chunk analysis structured output
class ChunkAnalysis(BaseModel):
    insights: List[str]
    summary: str
    quotes: List[str]
    takeaways: List[str]
    themes: List[str]

def extract_video_id(url: str) -> str:
    """Simple video ID extraction"""
    # Handle most common YouTube URL formats
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[1].split('?')[0]
    elif 'watch?v=' in url:
        return url.split('watch?v=')[1].split('&')[0]
    else:
        return url  # Assume it's already a video ID

def process_single_chunk(chunk_text: str, chunk_num: int, total_chunks: int, segment_info: str = ""):
    """
    Process a single chunk of text to extract insights using LLM.
    """
    try:
        import os
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        
        load_dotenv()
        
        # Initialize LLM with structured output
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            openai_api_key=os.getenv("OPENAI_API_KEY")
        ).with_structured_output(ChunkAnalysis)
        
        # Create analysis prompt
        prompt = f"""Analyze this video transcript chunk and extract insights:

        CONTEXT: This is chunk {chunk_num} of {total_chunks} from {segment_info}

        TRANSCRIPT CHUNK:
        {chunk_text}

        Please provide:
        1. 3-5 key insights from this content
        2. A concise summary (2-3 sentences)  
        3. 1-2 notable quotes if any stand out (empty list if none)
        4. 2-3 actionable takeaways
        5. Main themes/topics covered

        Extract meaningful, specific insights rather than generic statements.
        """

        # Get structured LLM response
        analysis = llm.invoke(prompt)
        
        return {
            "success": True,
            "chunk_number": chunk_num,
            "insights": analysis.insights,
            "summary": analysis.summary,
            "quotes": analysis.quotes,
            "takeaways": analysis.takeaways,
            "themes": analysis.themes,
            "word_count": len(chunk_text.split()),
            "processing_notes": f"LLM processed chunk {chunk_num} of {total_chunks}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to process chunk {chunk_num}: {str(e)}",
            "insights": [],
            "summary": ""
        }

def process_single_segment(transcript_snippets: List[Dict], segment_range: tuple) -> Dict[str, Any]:
    """
    Process a single segment in parallel
    
    Args:
        transcript_snippets: List of all transcript snippets
        segment_range: Tuple of (id, start_time, end_time, duration)
        
    Returns:
        Dictionary with single segment data
    """
    segment_id, start_time, end_time, duration = segment_range
    
    # Get snippets that fall within this time range
    segment_snippets = []
    for snippet in transcript_snippets:
        snippet_start = snippet['start']
        snippet_end = snippet['end']
        
        # Include snippet if it overlaps with segment time range
        if (snippet_start < end_time and snippet_end > start_time):
            segment_snippets.append(snippet)
    
    # Combine text from all snippets in this segment
    segment_content = " ".join([s['text'] for s in segment_snippets])
    
    return {
        "id": segment_id,
        "name": f"Segment {segment_id}",
        "start_time": start_time,
        "end_time": end_time,
        "duration": duration,
        "content": segment_content,
        "snippet_count": len(segment_snippets),
        "character_count": len(segment_content),
        "estimated_tokens": len(segment_content) // 4
    }