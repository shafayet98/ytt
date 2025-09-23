import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))



from pipeline import run_complete_pipeline

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading
import uuid
import json
from datetime import datetime



app = Flask(__name__)
CORS(app)  # Enable CORS for frontend communication

# Store job status and results
jobs = {}

def process_video_async(job_id, video_url, callback_level="clean"):
    """Process video in background thread"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Starting video analysis..."
        
        # Run the complete pipeline
        result = run_complete_pipeline(video_url, callback_level=callback_level)
        
        if result:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["message"] = "Analysis completed successfully!"
            jobs[job_id]["result"] = result
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["message"] = "Analysis failed. Please try again."
            
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Error: {str(e)}"




@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('../frontend', 'index.html')



@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files (CSS, JS)"""
    return send_from_directory('../frontend/static', filename)

@app.route('/api/analyze', methods=['POST'])
def analyze_video():
    """Start video analysis"""
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        callback_level = data.get('callback_level', 'clean')
        
        if not video_url:
            return jsonify({"error": "video_url is required"}), 400
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Initialize job status
        jobs[job_id] = {
            "status": "queued",
            "message": "Analysis queued...",
            "created_at": datetime.now().isoformat(),
            "video_url": video_url
        }
        
        # Start processing in background thread
        thread = threading.Thread(
            target=process_video_async, 
            args=(job_id, video_url, callback_level)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "message": "Analysis started. Use job_id to check status."
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status and results"""
    if job_id not in jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = jobs[job_id]
    response = {
        "job_id": job_id,
        "status": job["status"],
        "message": job["message"],
        "created_at": job["created_at"]
    }
    
    # Include results if completed
    if job["status"] == "completed" and "result" in job:
        # Extract structured insights for frontend
        insight_result = job["result"].get("insight_extraction_result", {})
        if "structured_analysis" in insight_result:
            structured_analysis = insight_result["structured_analysis"]
            if hasattr(structured_analysis, 'segments'):
                response["insights"] = [
                    {
                        "segment_number": seg.segment_number,
                        "segment_name": seg.segment_name,
                        "summary": seg.summary,
                        "key_insights": seg.key_insights,
                        "actionable_takeaways": seg.actionable_takeaways
                    }
                    for seg in structured_analysis.segments
                ]
                response["total_segments"] = structured_analysis.total_segments
    
    return jsonify(response)



@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs"""
    job_list = []
    for job_id, job_data in jobs.items():
        job_list.append({
            "job_id": job_id,
            "status": job_data["status"],
            "message": job_data["message"],
            "created_at": job_data["created_at"],
            "video_url": job_data.get("video_url", "")
        })
    
    return jsonify({"jobs": job_list})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "YouTube Analysis API is running",
        "timestamp": datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("🚀 Starting YouTube Analysis API Server")
    print("📡 API will be available at: http://localhost:8000")
    print("🌐 Frontend will be available at: http://localhost:8000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=8000)


# Update main function
# def main():
#     """
#     Main function to test the complete pipeline with different callback levels
#     """
#     print("🎬 YouTube Video Analysis System - Complete Pipeline")
#     print("=" * 60)

#     test_url = "https://www.youtube.com/watch?v=pdJQ8iVTwj8"
    
#     # Choose callback level: "minimal", "clean", "detailed", or "none"
#     callback_level = "detailed"  # Change this to test different levels
    
#     print(f"Testing Complete Pipeline with '{callback_level}' callbacks...")
#     result = run_complete_pipeline(test_url, callback_level=callback_level)
    
#     if result:
#         print("\n✨ Complete pipeline test completed successfully!")
#     else:
#         print("\n❌ Complete pipeline test failed!")

# if __name__ == "__main__":
#     main()