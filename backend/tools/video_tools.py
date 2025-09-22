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
def get_video_transcript(video_url: str) -> Dict[str, Any]:
    """
    Fetch YouTube video transcript and metadata.
    
    Args:
        video_url: YouTube video URL or video ID
        
    Returns:
        Dictionary containing transcript snippets, metadata, and full transcript text
    """
    try:
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

        # Create full transcript text
        full_transcript = " ".join([snippet.text for snippet in snippets])

        # Calculate total duration (from last snippet)
        total_duration = snippets[-1].start + snippets[-1].duration if snippets else 0

        # Basic metadata
        metadata = {
            "video_id": video_id,
            "total_duration": total_duration,
            "title": f"Video {video_id}",
            "channel": "Unknown",
            "description": "No description available",
            "total_characters": len(full_transcript),
            "estimated_tokens": len(full_transcript) // 4  # Rough estimate
        }

        result = {
            "transcript_snippets": transcript_snippets,
            "metadata": metadata,
            "full_transcript": full_transcript,
            "total_snippets": len(transcript_snippets),
            "success": True
        }
        
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get YouTube transcript: {str(e)}",
            "transcript_snippets": [],
            "metadata": {},
            "full_transcript": "",
            "total_snippets": 0
        }


@tool
def make_segments(transcript_snippets: List[Dict], total_duration: float, num_segments: int = 5) -> Dict[str, Any]:
    """
    Create time-based segments from transcript snippets with parallel processing.
    
    Args:
        transcript_snippets: List of transcript snippets with timing info
        total_duration: Total video duration in seconds
        num_segments: Number of segments to create (default: 5)
        
    Returns:
        Dictionary with segments containing content and timing info
    """
    try:
        
        # Validation with better error messages
        if not transcript_snippets:
            return {
                "success": False,
                "error": "No transcript snippets provided",
                "segments": [],
                "total_segments": 0
            }
        
        if not isinstance(transcript_snippets, list):
            return {
                "success": False,
                "error": f"transcript_snippets must be a list, got {type(transcript_snippets)}",
                "segments": [],
                "total_segments": 0
            }
            
        if not isinstance(total_duration, (int, float)) or total_duration <= 0:
            return {
                "success": False,
                "error": f"total_duration must be a positive number, got {type(total_duration)}: {total_duration}",
                "segments": [],
                "total_segments": 0
            }
        
        # Calculate segment duration
        segment_duration = total_duration / num_segments
        
        # Create segment time ranges
        segment_ranges = []
        for i in range(num_segments):
            start_time = i * segment_duration
            end_time = (i + 1) * segment_duration
            segment_ranges.append((i + 1, start_time, end_time, segment_duration))
        
        # Process segments in parallel
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
        
        return {
            "success": True,
            "segments": segments,
            "total_segments": num_segments,
            "segment_duration": segment_duration,
            "segmentation_strategy": f"Time-based ({num_segments} segments) - Parallel Processing"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create segments: {str(e)}",
            "segments": [],
            "total_segments": 0
        }