import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from youtube_transcript_api import YouTubeTranscriptApi
from langchain.tools import tool
from typing import Dict, List, Any
import concurrent.futures
from functools import partial

from utils.helpers import extract_video_id, process_single_segment


@tool
def process_video_and_segment(video_url: str, num_segments: int = 5) -> Dict[str, Any]:
    """
    Combined tool: Fetch YouTube transcript and create segments in one efficient step.
    Agent never processes the raw transcript data - only receives final segments.
    
    Args:
        video_url: YouTube video URL or video ID
        num_segments: Number of segments to create (default: 5)
        
    Returns:
        Dictionary with video metadata and segmented content
    """
    try:
        print(f"Processing video and creating segments...")
        
        # Step 1: Get transcript (internal - no agent involvement)
        video_id = extract_video_id(video_url)
        
        # Create API instance and fetch transcript
        youtube_transcript_api = YouTubeTranscriptApi()
        transcript = youtube_transcript_api.fetch(video_id)
        
        # Get the transcript snippets
        snippets = transcript.snippets
        
        transcript_snippets = []
        for snippet in snippets:
            transcript_snippets.append({
                "text": snippet.text,
                "start": snippet.start,
                "duration": snippet.duration,
                "end": snippet.start + snippet.duration
            })
        
        # Calculate total duration
        total_duration = snippets[-1].start + snippets[-1].duration if snippets else 0
        
        print(f"Fetched {len(transcript_snippets)} transcript snippets ({total_duration:.1f}s)")
        
        # Step 2: Create segments immediately (internal - with parallel processing)
        if not transcript_snippets:
            return {
                "success": False,
                "error": "No transcript snippets found",
                "video_metadata": {},
                "segments": []
            }
        
        # Calculate segment duration
        segment_duration = total_duration / num_segments
        
        # Create segment time ranges
        segment_ranges = []
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration
            segment_ranges.append((i + 1, start_time, end_time, segment_duration))
        
        print(f"Processing segments in parallel...")
        
        # Process segments in parallel (keeping your preferred approach)
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_segments) as executor:
            # Create partial function with transcript_snippets
            process_segment_func = partial(process_single_segment, transcript_snippets)
            
            # Submit all segment processing tasks
            future_to_segment = {
                executor.submit(process_segment_func, segment_range): segment_range 
                for segment_range in segment_ranges
            }
            
            # Collect results
            segments = []
            for future in concurrent.futures.as_completed(future_to_segment):
                segment_data = future.result()
                segments.append(segment_data)
        
        # Sort segments by ID to maintain order
        segments.sort(key=lambda x: x['id'])
        
        # Create clean metadata (no massive transcript data)
        video_metadata = {
            "video_id": video_id,
            "total_duration": total_duration,
            "title": f"Video {video_id}",
            "channel": "Unknown",
            "description": "No description available",
            "total_snippets": len(transcript_snippets),
            "estimated_tokens": sum(seg.get('estimated_tokens', 0) for seg in segments)
        }
        
        print(f"Created all the segments successfully")
        
        # Return only clean, manageable data for the agent
        return {
            "success": True,
            "video_metadata": video_metadata,
            "segments": segments,
            "total_segments": num_segments,
            "segment_duration": segment_duration,
            "processing_strategy": f"Combined processing with {num_segments} parallel segments",
            "performance_note": "No agent data overload - processed internally"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to process video and create segments: {str(e)}",
            "video_metadata": {},
            "segments": [],
            "total_segments": 0
        }