import json
import os
from datetime import datetime
from typing import Dict, Any

# Import structured output types
try:
    from agents.insight_extractor import SegmentAnalysis, MultiSegmentAnalysis
except ImportError:
    # Fallback if imports fail
    SegmentAnalysis = None
    MultiSegmentAnalysis = None

def extract_structured_insights(insight_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract insights from structured output format
    """
    # Check if we have structured analysis
    if "structured_analysis" in insight_result:
        structured_analysis = insight_result["structured_analysis"]
        
        # Handle MultiSegmentAnalysis object
        if hasattr(structured_analysis, 'segments'):
            segments_insights = []
            for segment in structured_analysis.segments:
                segments_insights.append({
                    "segment_number": segment.segment_number,
                    "segment_name": segment.segment_name,
                    "summary": segment.summary,
                    "key_insights": segment.key_insights,
                    "actionable_takeaways": segment.actionable_takeaways
                })
            
            return {
                "total_segments": structured_analysis.total_segments,
                "segments": segments_insights,
                "format": "structured"
            }
        
        # Handle dictionary format
        elif isinstance(structured_analysis, dict) and "segments" in structured_analysis:
            return {
                "total_segments": structured_analysis.get("total_segments", 0),
                "segments": structured_analysis.get("segments", []),
                "format": "structured"
            }
    
    # Fallback to old format
    return {
        "output": insight_result.get("output", "No insights available"),
        "format": "text"
    }

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
        
        # Extract structured insights
        structured_insights = extract_structured_insights(insight_result)
        
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
            "structured_insights": structured_insights,
            "insights_summary": structured_insights.get("output", "Structured insights available in structured_insights section"),
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
        
        # Extract structured insights
        structured_insights = extract_structured_insights(insight_result)
        
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
        
        # Add AI insights - handle both structured and text format
        summary_content += "\n## AI-Generated Insights\n\n"
        
        if structured_insights.get("format") == "structured":
            # Display structured insights
            segments_insights = structured_insights.get("segments", [])
            if segments_insights:
                for segment_insight in segments_insights:
                    segment_num = segment_insight.get("segment_number", "Unknown")
                    segment_name = segment_insight.get("segment_name", f"Segment {segment_num}")
                    summary = segment_insight.get("summary", "No summary available")
                    key_insights = segment_insight.get("key_insights", [])
                    takeaways = segment_insight.get("actionable_takeaways", [])
                    
                    summary_content += f"### {segment_name}\n\n"
                    summary_content += f"**Summary**: {summary}\n\n"
                    
                    if key_insights:
                        summary_content += "**Key Insights**:\n"
                        for insight in key_insights:
                            summary_content += f"- {insight}\n"
                        summary_content += "\n"
                    
                    if takeaways:
                        summary_content += "**Actionable Takeaways**:\n"
                        for takeaway in takeaways:
                            summary_content += f"- {takeaway}\n"
                        summary_content += "\n"
                    
                    summary_content += "---\n\n"
            else:
                summary_content += "No structured insights available\n\n"
        else:
            # Fallback to text format
            summary_content += f"{structured_insights.get('output', 'No insights available')}\n\n"
        
        summary_content += "*This analysis was generated automatically using AI agents and may require human review for accuracy.*\n"
        
        # Save to markdown file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"\n📝 Summary saved to: {filepath}")
        print(f"📄 File size: {os.path.getsize(filepath) / 1024:.1f} KB")
        
        return filepath
        
    except Exception as e:
        print(f"❌ Failed to save summary: {str(e)}")
        return ""
