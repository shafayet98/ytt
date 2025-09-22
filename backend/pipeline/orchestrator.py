# Fix the import - use the correct function names
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import create_video_processor_agent, create_insight_extraction_agent
from agents.insight_extractor import process_segment_with_structured_output, MultiSegmentAnalysis
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
    # Extract segments data from Agent 1 result
    segments_data = None
    if agent_1_result.get("intermediate_steps"):
        for action, observation in agent_1_result["intermediate_steps"]:
            if action.tool == 'process_video_and_segment' and isinstance(observation, dict) and observation.get('success'):
                segments_data = observation.get('segments', [])
                break
    
    if not segments_data:
        print("No segments data found from VideoProcessorAgent")
        return None
    
    print(f"\n VideoProcessorAgent completed - {len(segments_data)} segments created")
    
    # Step 2: Run InsightExtractionAgent with Structured Output
    print("\n PHASE 2: Insight Extraction & Storytelling (Structured)")
    print("=" * 50)
    
    agent_2_result = run_structured_insight_extraction_pipeline(segments_data)
    
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

def run_structured_insight_extraction_pipeline(segments_data):
    """
    Run InsightExtractionAgent with structured output for each segment
    """
    print("\n Starting Structured InsightExtractionAgent")
    print("=" * 50)
    
    try:
        import concurrent.futures
        from typing import List
        
        print(f"📊 Processing {len(segments_data)} segments with structured output...")
        
        # Process segments in parallel with structured output
        def process_single_segment_structured(segment_data, index):
            segment_number = index + 1
            print(f"🔄 Processing Segment {segment_number}...")
            return process_segment_with_structured_output(segment_data, segment_number)
        
        # Use ThreadPoolExecutor to process segments in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(segments_data), 3)) as executor:
            # Submit all segment processing tasks
            future_to_segment = {
                executor.submit(process_single_segment_structured, segment, i): i 
                for i, segment in enumerate(segments_data)
            }
            
            # Collect results in order
            segment_analyses = [None] * len(segments_data)
            for future in concurrent.futures.as_completed(future_to_segment):
                segment_index = future_to_segment[future]
                try:
                    result = future.result()
                    segment_analyses[segment_index] = result
                    print(f"✅ Segment {segment_index + 1} completed: {result.segment_name}")
                except Exception as e:
                    print(f"❌ Segment {segment_index + 1} failed: {str(e)}")
        
        # Filter out any None results
        valid_analyses = [analysis for analysis in segment_analyses if analysis is not None]
        
        # Create the final structured result
        structured_result = MultiSegmentAnalysis(
            segments=valid_analyses,
            total_segments=len(valid_analyses)
        )
        
        print(f"\n✅ Structured InsightExtractionAgent completed!")
        print(f"📊 Successfully processed {len(valid_analyses)}/{len(segments_data)} segments")
        print("STRUCTURED RESULTS:")
        print("-" * 30)
        
        # Display summary of results
        for analysis in valid_analyses:
            print(f"📝 {analysis.segment_name}")
            print(f"   📊 {len(analysis.key_insights)} insights, {len(analysis.actionable_takeaways)} takeaways")
        
        return {
            "structured_analysis": structured_result,
            "success": True,
            "total_segments_processed": len(valid_analyses),
            "processing_method": "structured_parallel"
        }
        
    except Exception as e:
        print(f"❌ Structured InsightExtractionAgent failed: {str(e)}")
        return None


# old approach
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
        # print(f"Analysis Result: {result['output'][:500]}...")
        
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
        # print(f"Result: {result['output']}")
        
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