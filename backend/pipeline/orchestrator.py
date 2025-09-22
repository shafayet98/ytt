# Fix the import - use the correct function names
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import create_video_processor_agent, create_insight_extraction_agent
from utils.file_saver import save_analysis_results, save_analysis_summary



def run_complete_pipeline(video_url: str):
    """
    Run the complete pipeline: VideoProcessorAgent -> InsightExtractionAgent
    """
    print("Starting Complete YouTube Analysis Pipeline")
    print("=" * 70)
    print(f"Video URL: {video_url}")
    print()
    
    # Step 1: Run VideoProcessorAgent
    print("PHASE 1: Video Processing & Segmentation")
    print("=" * 50)
    
    agent_1_result = run_video_processor_pipeline(video_url)
    
    if not agent_1_result:
        print("Pipeline failed at VideoProcessorAgent")
        return None
    
    # Extract segments data from Agent 1 result
    segments_data = None
    if agent_1_result.get("intermediate_steps"):
        for action, observation in agent_1_result["intermediate_steps"]:
            if action.tool == 'make_segments' and isinstance(observation, dict) and observation.get('success'):
                segments_data = observation.get('segments', [])
                break
    
    if not segments_data:
        print("No segments data found from VideoProcessorAgent")
        return None
    
    print(f"\n VideoProcessorAgent completed - {len(segments_data)} segments created")
    
    # Step 2: Run InsightExtractionAgent
    print("\n PHASE 2: Insight Extraction & Storytelling")
    print("=" * 50)
    
    agent_2_result = run_insight_extraction_pipeline(segments_data)
    
    if not agent_2_result:
        print("Pipeline failed at InsightExtractionAgent")
        return None
    
    # Step 3: Prepare Final Results
    final_results = {
        "video_processor_result": agent_1_result,
        "insight_extraction_result": agent_2_result,
        "segments_data": segments_data
    }
    
    # Step 4: Save Results to Files
    print("\n💾 SAVING RESULTS TO FILES")
    print("=" * 50)
    
    # Save detailed JSON results
    json_filepath = save_analysis_results(final_results)
    
    # Save human-readable summary
    summary_filepath = save_analysis_summary(final_results)
    
    # Step 5: Display Final Results
    print("\n✅ COMPLETE PIPELINE SUCCESS!")
    print("=" * 50)
    print("✅ VideoProcessorAgent: Fetched transcript and created segments")
    print("✅ InsightExtractionAgent: Extracted insights and created stories")
    
    if json_filepath:
        print(f"✅ Detailed results saved: {json_filepath}")
    if summary_filepath:
        print(f"✅ Summary saved: {summary_filepath}")
    
    return final_results


def run_insight_extraction_pipeline(segments_data):
    """
    Run InsightExtractionAgent with segments data
    """
    print("\n Starting InsightExtractionAgent")
    print("=" * 50)
    
    try:
        # Create the agent
        agent = create_insight_extraction_agent()
        
        # Prepare input for the agent
        input_text = f"""Please analyze these video segments and extract insights with storytelling:

SEGMENTS TO PROCESS:
{segments_data}

For each segment:
1. Determine if chunking is needed based on content size
2. Process the content (chunked or whole) to extract insights
3. Create a meaningful segment name based on actual content
4. Provide engaging summary and key takeaways
5. Return structured analysis

Please process all segments and provide comprehensive insights."""
        
        # Run the agent
        result = agent.invoke({"input": input_text})
        
        print("\n InsightExtractionAgent completed successfully!")
        print("INSIGHTS EXTRACTED:")
        print("-" * 30)
        
        # Display the agent's output
        print(f"Analysis Result: {result['output'][:500]}...")
        
        return result
        
    except Exception as e:
        print(f"InsightExtractionAgent failed: {str(e)}")
        return None


def run_video_processor_pipeline(video_url: str):
    """
    Run VideoProcessorAgent with a YouTube URL
    """
    print("Starting VideoProcessorAgent")
    print("=" * 50)
    print(f"Video URL: {video_url}")
    print()

    try:
        # Create the agent
        agent = create_video_processor_agent()
        
        # Run the agent
        input_text = f"Please process this YouTube video and create 5 segments: {video_url}"
        result = agent.invoke({"input": input_text})
        
        print("\n VideoProcessorAgent completed successfully!")
        print("AGENT OUTPUT:")
        print("-" * 30)
        
        # Regular agent output
        print(f"Result: {result['output']}")
        
        if result.get("intermediate_steps"):
            print("\n🔧 TOOL CALLS MADE:")
            print("-" * 30)
            for i, (action, observation) in enumerate(result["intermediate_steps"]):
                print(f"Step {i+1}: {action.tool}")
                if isinstance(observation, dict) and observation.get('success'):
                    if action.tool == 'get_video_transcript':
                        print(f"   Got transcript with {observation.get('total_snippets', 0)} snippets")
                        print(f"    Duration: {observation.get('metadata', {}).get('total_duration', 0):.1f} seconds")
                    elif action.tool == 'make_segments':
                        print(f"   Created {observation.get('total_segments', 0)} segments")
                        segments = observation.get('segments', [])
                        for seg in segments[:3]:  # Show first 3 segments
                            print(f"     - {seg.get('name', 'N/A')}: {seg.get('estimated_tokens', 0)} tokens")
        
        return result
        
    except Exception as e:
        print(f"❌ VideoProcessorAgent failed: {str(e)}")
        return None