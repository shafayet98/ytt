#!/usr/bin/env python3
"""
Test script for updated file_saver with structured output
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.file_saver import save_analysis_summary, save_analysis_results, extract_structured_insights
from agents.insight_extractor import SegmentAnalysis, MultiSegmentAnalysis

def create_sample_structured_results():
    """Create sample structured results for testing"""
    
    # Create sample segment analyses
    segment1 = SegmentAnalysis(
        segment_number=1,
        segment_name="Introduction to Islamic Teachings",
        summary="This segment introduces fundamental Islamic concepts and the importance of reading Surah Al-Kahf on Fridays for spiritual protection and blessings.",
        key_insights=[
            "Surah Al-Kahf provides protection from one Friday to another",
            "Regular recitation brings spiritual blessings and guidance",
            "The Prophet advised consistent reading of this chapter"
        ],
        actionable_takeaways=[
            "Make reading Surah Al-Kahf part of your Friday routine",
            "Set aside dedicated time for spiritual reflection"
        ]
    )
    
    segment2 = SegmentAnalysis(
        segment_number=2,
        segment_name="The Story of Iblis and Pride",
        summary="This segment explores the story of Iblis (Satan) and how pride led to his downfall, serving as a warning against arrogance and the importance of humility.",
        key_insights=[
            "Pride was the root cause of Iblis's rebellion against Allah",
            "The concept of intrinsic merit can lead to spiritual downfall",
            "Humility is essential for spiritual growth and obedience"
        ],
        actionable_takeaways=[
            "Practice humility in daily interactions",
            "Avoid comparing yourself to others based on perceived superiority"
        ]
    )
    
    # Create multi-segment analysis
    multi_analysis = MultiSegmentAnalysis(
        segments=[segment1, segment2],
        total_segments=2
    )
    
    # Create sample results structure
    sample_results = {
        "video_processor_result": {
            "output": "Video processing completed",
            "intermediate_steps": [
                (
                    type('Action', (), {'tool': 'get_video_transcript'}),
                    {
                        'success': True,
                        'metadata': {
                            'video_id': 'test123',
                            'title': 'Islamic Teachings: Surah Al-Kahf',
                            'channel': 'Islamic Learning',
                            'total_duration': 2112.2,
                            'estimated_tokens': 5059
                        }
                    }
                )
            ]
        },
        "insight_extraction_result": {
            "structured_analysis": multi_analysis,
            "success": True,
            "total_segments_processed": 2,
            "processing_method": "structured_parallel"
        },
        "segments_data": [
            {
                "id": 1,
                "name": "Segment 1",
                "start_time": 0.0,
                "end_time": 422.4,
                "duration": 422.4,
                "content": "Sample content for segment 1...",
                "snippet_count": 132,
                "character_count": 4531,
                "estimated_tokens": 1132
            },
            {
                "id": 2,
                "name": "Segment 2", 
                "start_time": 422.4,
                "end_time": 844.9,
                "duration": 422.5,
                "content": "Sample content for segment 2...",
                "snippet_count": 144,
                "character_count": 5104,
                "estimated_tokens": 1276
            }
        ]
    }
    
    return sample_results

def test_extract_structured_insights():
    """Test the extract_structured_insights function"""
    print("🧪 Testing extract_structured_insights function")
    print("=" * 50)
    
    sample_results = create_sample_structured_results()
    insight_result = sample_results["insight_extraction_result"]
    
    structured_insights = extract_structured_insights(insight_result)
    
    print(f"✅ Format: {structured_insights.get('format')}")
    print(f"✅ Total segments: {structured_insights.get('total_segments')}")
    print(f"✅ Number of segment insights: {len(structured_insights.get('segments', []))}")
    
    if structured_insights.get("segments"):
        first_segment = structured_insights["segments"][0]
        print(f"✅ First segment name: {first_segment.get('segment_name')}")
        print(f"✅ First segment insights count: {len(first_segment.get('key_insights', []))}")
    
    return structured_insights

def test_file_saving():
    """Test the file saving functionality"""
    print(f"\n🧪 Testing file saving with structured output")
    print("=" * 50)
    
    sample_results = create_sample_structured_results()
    
    try:
        # Test JSON saving
        print("📄 Testing JSON save...")
        json_path = save_analysis_results(sample_results, "test_outputs")
        if json_path:
            print(f"✅ JSON saved successfully: {json_path}")
        
        # Test Markdown saving
        print("📝 Testing Markdown save...")
        md_path = save_analysis_summary(sample_results, "test_outputs")
        if md_path:
            print(f"✅ Markdown saved successfully: {md_path}")
            
            # Read and display a preview of the markdown
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"\n📋 Markdown Preview (first 500 chars):")
                print("-" * 30)
                print(content[:500] + "...")
        
        return True
        
    except Exception as e:
        print(f"❌ File saving test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Updated File Saver with Structured Output")
    print("=" * 60)
    
    # Test structured insights extraction
    insights = test_extract_structured_insights()
    
    # Test file saving
    success = test_file_saving()
    
    if success:
        print(f"\n✅ All tests passed! File saver now supports structured output.")
        print(f"📁 Check the 'test_outputs' directory for generated files.")
    else:
        print(f"\n❌ Some tests failed. Please check the implementation.")
