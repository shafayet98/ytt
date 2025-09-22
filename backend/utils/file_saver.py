import json
import os
from datetime import datetime
from typing import Dict, Any

def save_analysis_results(results: Dict[str, Any], output_dir: str = "outputs") -> str:
    """
    Save the final analysis results to a JSON file.
    
    Args:
        results: Complete pipeline results
        output_dir: Directory to save the output file
        
    Returns:
        Path to the saved file
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"youtube_analysis_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)
        
        # Extract relevant data for saving
        segments_data = results.get("segments_data", [])
        insight_result = results.get("insight_extraction_result", {})
        video_result = results.get("video_processor_result", {})
        
        # Get video metadata if available
        video_metadata = {}
        if video_result.get("intermediate_steps"):
            for action, observation in video_result["intermediate_steps"]:
                if action.tool == 'get_video_transcript' and observation.get('success'):
                    video_metadata = observation.get('metadata', {})
                    break
        
        # Structure the final output
        final_output = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_segments": len(segments_data),
                "video_duration": video_metadata.get("total_duration", 0),
                "video_id": video_metadata.get("video_id", "unknown"),
                "processing_status": "completed"
            },
            "video_info": {
                "title": video_metadata.get("title", "Unknown"),
                "channel": video_metadata.get("channel", "Unknown"),
                "duration_seconds": video_metadata.get("total_duration", 0),
                "estimated_tokens": video_metadata.get("estimated_tokens", 0)
            },
            "segments": segments_data,
            "insights_summary": insight_result.get("output", "No insights available"),
            "raw_results": {
                "video_processor_output": video_result.get("output", ""),
                "insight_extractor_output": insight_result.get("output", "")
            }
        }
        
        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Analysis results saved to: {filepath}")
        print(f"📊 File size: {os.path.getsize(filepath) / 1024:.1f} KB")
        
        return filepath
        
    except Exception as e:
        print(f"❌ Failed to save results: {str(e)}")
        return ""

def save_analysis_summary(results: Dict[str, Any], output_dir: str = "outputs") -> str:
    """
    Save a human-readable summary of the analysis.
    
    Args:
        results: Complete pipeline results
        output_dir: Directory to save the output file
        
    Returns:
        Path to the saved summary file
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"youtube_summary_{timestamp}.md"
        filepath = os.path.join(output_dir, filename)
        
        # Extract data
        segments_data = results.get("segments_data", [])
        insight_result = results.get("insight_extraction_result", {})
        video_result = results.get("video_processor_result", {})
        
        # Get video metadata
        video_metadata = {}
        if video_result.get("intermediate_steps"):
            for action, observation in video_result["intermediate_steps"]:
                if action.tool == 'get_video_transcript' and observation.get('success'):
                    video_metadata = observation.get('metadata', {})
                    break
        
        # Create markdown summary
        summary_content = f"""# YouTube Video Analysis Summary

## Video Information
- **Video ID**: {video_metadata.get('video_id', 'Unknown')}
- **Title**: {video_metadata.get('title', 'Unknown')}
- **Channel**: {video_metadata.get('channel', 'Unknown')}
- **Duration**: {video_metadata.get('total_duration', 0):.1f} seconds ({video_metadata.get('total_duration', 0)/60:.1f} minutes)
- **Analysis Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Analysis Overview
- **Total Segments**: {len(segments_data)}
- **Processing Status**: Completed Successfully
- **Estimated Tokens**: {video_metadata.get('estimated_tokens', 0):,}

## Segment Breakdown
"""
        
        # Add segment details
        for i, segment in enumerate(segments_data, 1):
            duration_min = segment.get('duration', 0) / 60
            summary_content += f"""
### Segment {i}: {segment.get('name', f'Segment {i}')}
- **Time Range**: {segment.get('start_time', 0):.1f}s - {segment.get('end_time', 0):.1f}s ({duration_min:.1f} minutes)
- **Content Length**: {segment.get('character_count', 0):,} characters
- **Estimated Tokens**: {segment.get('estimated_tokens', 0):,}
- **Snippet Count**: {segment.get('snippet_count', 0)}

**Content Preview**: {segment.get('content', 'No content available')[:200]}...

---
"""
        
        # Add AI insights
        summary_content += f"""
## AI-Generated Insights

{insight_result.get('output', 'No insights available')}

---

*This analysis was generated automatically using AI agents and may require human review for accuracy.*
"""
        
        # Save to markdown file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"\n📝 Summary saved to: {filepath}")
        print(f"📄 File size: {os.path.getsize(filepath) / 1024:.1f} KB")
        
        return filepath
        
    except Exception as e:
        print(f"❌ Failed to save summary: {str(e)}")
        return ""
