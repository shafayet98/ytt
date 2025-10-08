# TL;DW (Too Long; Didn't Watch)

An intelligent AI-powered system that analyzes YouTube videos and extracts structured insights, summaries, and actionable takeaways in real-time.

![TL;DW Demo](https://img.shields.io/badge/Status-Active-green) ![Python](https://img.shields.io/badge/Python-3.11-blue) ![LangChain](https://img.shields.io/badge/LangChain-Latest-orange) ![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-red)

## 🎯 Overview

TL;DW is an agentic system designed to process long-form YouTube content (podcasts, lectures, educational videos) and provide structured analysis. The system can handle videos of any length, including 3+ hour content, by intelligently segmenting and processing transcripts in parallel.

## Demo

https://github.com/shafayet98/ytt/tree/main/demo/Demo2.mp4

### Key Features

- ⚡ **Real-time Processing**: Live progress updates via Server-Sent Events
- 🧠 **Intelligent Segmentation**: Automatically creates 5 meaningful segments
- 🔄 **Parallel Processing**: Handles multiple segments simultaneously
- 📊 **Structured Output**: Consistent, reliable results using Pydantic models
- 🎨 **Responsive UI**: Beautiful grid layout that adapts to any screen
- 🛠️ **Smart Tool Usage**: Automatically handles large content with chunking

## 🏗️ Architecture

### Multi-Agent System

The system consists of two specialized agents:

1. **VideoProcessorAgent**
   - Extracts YouTube transcript
   - Creates intelligent segments
   - Tool: `process_video_and_segment`

2. **InsightExtractionAgent**
   - Analyzes segments for insights
   - Handles both small and large content
   - Tools: `text_splitter`, `process_chunks_parallel`

### Processing Flow

```
YouTube URL → VideoProcessorAgent → 5 Segments → InsightExtractionAgent → Structured Analysis
                                                        ↓
                                    Small Segment → Direct Processing
                                    Large Segment → Tool-Assisted Processing
                                                        ↓
                                            Parallel Analysis → Frontend Display
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API Key
- Pipenv (recommended) or pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ytt
   ```

2. **Install dependencies**
   ```bash
   # Using Pipenv (recommended)
   pipenv install
   pipenv shell

   # Or using pip
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file in the root directory
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

4. **Run the application**
   ```bash
   cd backend
   python main.py
   ```

5. **Access the application**
   - Open your browser and go to `http://localhost:8000`
   - Enter a YouTube URL and click "Analyze"

## 📁 Project Structure

```
ytt/
├── backend/
│   ├── agents/
│   │   ├── video_processor.py      # VideoProcessorAgent implementation
│   │   └── insight_extractor.py    # InsightExtractionAgent implementation
│   ├── tools/
│   │   ├── video_tools.py          # YouTube processing tools
│   │   └── analysis_tools.py       # Text analysis tools
│   ├── pipeline/
│   │   └── orchestrator.py         # Main pipeline orchestration
│   ├── utils/
│   │   ├── helpers.py              # Utility functions
│   │   ├── file_saver.py           # Result saving utilities
│   │   └── custom_callbacks.py     # LangChain callback handlers
│   ├── config/
│   │   └── settings.py             # Configuration settings
│   └── main.py                     # Flask application entry point
├── frontend/
│   ├── index.html                  # Main HTML page
│   └── static/
│       ├── script.js               # Frontend JavaScript
│       └── style.css               # Styling and responsive design
├── outputs/                        # Generated analysis files
├── Pipfile                         # Python dependencies
└── README.md                       # This file
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

### Settings

Modify `backend/config/settings.py` to customize:

```python
DEFAULT_MODEL = "gpt-4o-mini"           # OpenAI model
DEFAULT_TEMPERATURE = 0                 # LLM temperature
DEFAULT_MAX_TOKENS = 50000             # Max tokens per chunk
DEFAULT_SEGMENTS = 5                   # Number of segments to create
CHUNK_OVERLAP = 1000                   # Overlap between chunks
```

## 🛠️ Technical Details

### Agent Design

#### VideoProcessorAgent
- **Purpose**: Extract and segment YouTube transcripts
- **Tools**: `process_video_and_segment`
- **Output**: 5 structured segments with metadata

#### InsightExtractionAgent
- **Purpose**: Extract insights from segments
- **Processing Logic**:
  - Segments < 40k tokens → Direct LLM processing
  - Segments > 40k tokens → Tool-assisted chunking + parallel processing
- **Tools**: `text_splitter`, `process_chunks_parallel`
- **Output**: Structured `SegmentAnalysis` objects

### Data Models

```python
class SegmentAnalysis(BaseModel):
    segment_number: int
    segment_name: str                    # Meaningful name (not "Segment X")
    summary: str                         # 2-3 sentence engaging summary
    key_insights: List[str]              # 3-5 key insights
    actionable_takeaways: List[str]      # 2-3 actionable items

class MultiSegmentAnalysis(BaseModel):
    segments: List[SegmentAnalysis]
    total_segments: int
```

### Real-time Updates

The system uses Server-Sent Events (SSE) to provide real-time progress updates:

- Progress message filtering with whitelist patterns
- Automatic connection management and retry logic
- Clean error handling and fallback to polling

## 📊 Performance

- **Processing Speed**: 3h 34min video analyzed in 28 seconds
- **Parallel Processing**: Up to 3 segments processed simultaneously
- **Memory Efficient**: Intelligent chunking for large content
- **Scalable**: Handles videos of any length

## 🎨 Frontend Features

### Responsive Design
- **Desktop**: 5-column grid with staggered margins
- **Tablet**: 2-3 column adaptive layout
- **Mobile**: Single column stack

### Real-time Progress
- Live progress messages with timestamps
- Visual progress indicators
- Auto-scrolling message feed

### Modern UI
- Tailwind CSS styling
- Lucide icons
- Smooth animations and transitions

## 🔍 API Endpoints

### Core Endpoints

- `POST /api/analyze` - Start video analysis
- `GET /api/status/<job_id>` - Get job status and results
- `GET /api/progress/<job_id>` - SSE stream for real-time updates
- `GET /api/jobs` - List all jobs
- `GET /api/health` - Health check

### Example Usage

```javascript
// Start analysis
const response = await fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        video_url: 'https://www.youtube.com/watch?v=...',
        callback_level: 'clean'
    })
});

// Get results
const status = await fetch(`/api/status/${job_id}`);
const data = await status.json();
```

## 🧪 Testing

Run the test file to verify functionality:

```bash
cd backend
python test_file_saver.py
```

## 📝 Output Files

The system generates two types of output files in the `outputs/` directory:

1. **Detailed JSON** (`youtube_analysis_YYYYMMDD_HHMMSS.json`)
   - Complete analysis data
   - Agent execution details
   - Metadata and timestamps

2. **Human-readable Summary** (`youtube_summary_YYYYMMDD_HHMMSS.md`)
   - Formatted markdown summary
   - Key insights and takeaways
   - Easy to read and share

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) for the agent framework
- [OpenAI](https://openai.com/) for the language models
- [YouTube Transcript API](https://github.com/jdepoix/youtube-transcript-api) for transcript extraction
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [Lucide](https://lucide.dev/) for icons

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page
2. Create a new issue with detailed information
3. Include error logs and system information

---

**Built with ❤️ using LangChain, OpenAI, and modern web technologies**
