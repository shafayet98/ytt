import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline import run_complete_pipeline

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import threading
import uuid
import json
from datetime import datetime
import queue
import time

# Get absolute path to frontend/static directory
backend_dir = os.path.dirname(os.path.abspath(__file__))
static_folder = os.path.join(os.path.dirname(backend_dir), 'frontend', 'static')

print(f"🔍 Static folder path: {static_folder}")
print(f"✅ Static folder exists: {os.path.exists(static_folder)}")

app = Flask(__name__, static_folder=static_folder, static_url_path='/static')
CORS(app)  # Enable CORS for frontend communication

# Store job status and results
jobs = {}
# Store progress messages for each job
job_progress = {}

class ProgressCapture:
    def __init__(self, job_id):
        self.job_id = job_id
        self.original_stdout = sys.stdout
        
        # Simple whitelist of messages you want to stream
        self.important_messages = [
            "🎬 Processing video",
            "📊 Fetched",
            "🔄 Processing",
            "✅ Created",
            "✅ Segment",
            "Starting VideoProcessorAgent",
            "VideoProcessorAgent completed",
            "Starting Structured InsightExtractionAgent",
            "InsightExtractionAgent completed",
            "PHASE 1:",
            "PHASE 2:",
            "💾 SAVING RESULTS",
            "💾 Analysis results saved",
            "📝 Summary saved",
            "✅ COMPLETE PIPELINE SUCCESS"
        ]
    
    def __enter__(self):
        sys.stdout = self
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
    
    def write(self, text):
        self.original_stdout.write(text)
        self.original_stdout.flush()
        
        text = text.strip()
        
        # Only capture if it contains any of our important keywords
        if any(keyword in text for keyword in self.important_messages):
            if self.job_id not in job_progress:
                job_progress[self.job_id] = queue.Queue()
            
            job_progress[self.job_id].put({
                'timestamp': datetime.now().isoformat(),
                'message': text,
                'type': 'progress'
            })
    
    def flush(self):
        self.original_stdout.flush()

def process_video_async(job_id, video_url, callback_level="clean"):
    """Process video in background thread with selective progress capture"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Starting video analysis..."
        
        # Initialize progress queue
        job_progress[job_id] = queue.Queue()
        
        # Add initial progress message
        job_progress[job_id].put({
            'timestamp': datetime.now().isoformat(),
            'message': '🚀 Initializing YouTube Analysis Pipeline',
            'type': 'progress'
        })
        
        # Capture only meaningful progress messages during pipeline execution
        with ProgressCapture(job_id):
            result = run_complete_pipeline(video_url, callback_level=callback_level)
        
        if result:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["message"] = "Analysis completed successfully!"
            jobs[job_id]["result"] = result
            
            # Add completion message
            job_progress[job_id].put({
                'timestamp': datetime.now().isoformat(),
                'message': '🎉 Analysis completed successfully!',
                'type': 'completion'
            })
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["message"] = "Analysis failed. Please try again."
            
            job_progress[job_id].put({
                'timestamp': datetime.now().isoformat(),
                'message': '❌ Analysis failed. Please try again.',
                'type': 'error'
            })
            
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Error: {str(e)}"
        
        job_progress[job_id].put({
            'timestamp': datetime.now().isoformat(),
            'message': f'💥 Error: {str(e)}',
            'type': 'error'
        })

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/api/progress/<job_id>')
def stream_progress(job_id):
    """Server-Sent Events endpoint for real-time progress updates"""
    def generate():
        # Wait a bit for the job to initialize if it doesn't exist yet
        max_wait_time = 5  # seconds
        wait_interval = 0.5  # seconds
        waited = 0
        
        while job_id not in job_progress and waited < max_wait_time:
            time.sleep(wait_interval)
            waited += wait_interval
        
        if job_id not in job_progress:
            yield f"data: {json.dumps({'error': 'Job not found or not started yet'})}\n\n"
            return
            
        progress_queue = job_progress[job_id]
        
        try:
            while True:
                try:
                    # Get message with timeout
                    message = progress_queue.get(timeout=2)
                    yield f"data: {json.dumps(message)}\n\n"
                    
                    # If this is a completion or error message, close the stream
                    if message.get('type') in ['completion', 'error']:
                        break
                        
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
                    # Check if job is completed or failed
                    if job_id in jobs:
                        job_status = jobs[job_id]["status"]
                        if job_status in ['completed', 'failed']:
                            break
                            
        except GeneratorExit:
            # Client disconnected
            pass
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e), 'type': 'error'})}\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control'
        }
    )

@app.route('/debug-static')
def debug_static():
    """Debug static file setup"""
    import os
    
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(os.path.dirname(backend_dir), 'frontend', 'static')
    
    files = []
    if os.path.exists(static_dir):
        files = os.listdir(static_dir)
    
    return jsonify({
        "backend_dir": backend_dir,
        "static_dir": static_dir,
        "static_exists": os.path.exists(static_dir),
        "files": files,
        "flask_static_folder": app.static_folder
    })

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