// YouTube Analysis System Frontend
class YouTubeAnalyzer {
    constructor() {
        this.currentJobId = null;
        this.statusInterval = null;
        this.eventSource = null;
        this.jobCompleted = false; // Track if job is completed
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        const form = document.getElementById('analysisForm');
        form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const videoUrl = document.getElementById('videoUrl').value;
        const callbackLevel = 'clean';
        
        if (!videoUrl) {
            this.showError('Please enter a YouTube URL');
            return;
        }

        this.startAnalysis(videoUrl, callbackLevel);
    }

    async startAnalysis(videoUrl, callbackLevel) {
        try {
            this.disableForm(true);
            this.clearPreviousResults();
            this.jobCompleted = false; // Reset completion flag

            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_url: videoUrl,
                    callback_level: callbackLevel
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.currentJobId = data.job_id;
                
                // Wait a moment for backend to initialize, then start progress stream
                setTimeout(() => {
                    this.startProgressStream();
                }, 500); // 500ms delay
                
                this.startStatusPolling();
            } else {
                this.showError(data.error || 'Failed to start analysis');
                this.disableForm(false);
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
            this.disableForm(false);
        }
    }

    startProgressStream(retryCount = 0) {
        if (this.eventSource) {
            this.eventSource.close();
        }

        // Don't start SSE if job is already completed
        if (this.jobCompleted) {
            console.log('Job already completed, skipping SSE connection');
            return;
        }

        // Show progress section
        this.showProgressSection();

        // Connect to Server-Sent Events stream
        this.eventSource = new EventSource(`/api/progress/${this.currentJobId}`);
        
        this.eventSource.onopen = () => {
            console.log('SSE connection opened successfully');
        };
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                // Skip heartbeat messages
                if (data.type === 'heartbeat') {
                    return;
                }
                
                if (data.type === 'progress') {
                    this.addProgressMessage(data.message, data.timestamp);
                } else if (data.type === 'completion') {
                    this.addProgressMessage(data.message, data.timestamp, 'success');
                    this.jobCompleted = true; // Mark job as completed
                } else if (data.type === 'error') {
                    this.addProgressMessage(data.message, data.timestamp, 'error');
                    this.jobCompleted = true; // Mark job as completed (failed)
                }
            } catch (e) {
                console.error('Error parsing SSE data:', e);
            }
        };

        this.eventSource.onerror = (error) => {
            console.log('SSE connection error/close event');
            
            // Check the ready state to understand what happened
            if (this.eventSource.readyState === EventSource.CONNECTING) {
                console.log('SSE is connecting...');
            } else if (this.eventSource.readyState === EventSource.CLOSED) {
                console.log('SSE connection closed');
                
                // Only retry if the job is NOT completed and we haven't exceeded retry limit
                if (!this.jobCompleted && retryCount < 3) {
                    const retryDelay = (retryCount + 1) * 1000; // 1s, 2s, 3s
                    console.log(`Job not completed, retrying SSE connection in ${retryDelay}ms (attempt ${retryCount + 1}/3)`);
                    
                    setTimeout(() => {
                        this.startProgressStream(retryCount + 1);
                    }, retryDelay);
                } else if (this.jobCompleted) {
                    console.log('Job completed, SSE connection closed normally');
                } else {
                    console.log('Max SSE retry attempts reached, falling back to polling only');
                    this.addProgressMessage('⚠️ Real-time updates unavailable, using polling fallback', new Date().toISOString(), 'info');
                }
            }
        };
    }

    showProgressSection() {
        const statusSection = document.getElementById('statusSection');
        const statusContent = document.getElementById('statusContent');
        
        statusSection.classList.remove('hidden');
        statusContent.innerHTML = `
            <div class="progress-container">
                <h3 class="text-lg font-semibold mb-4 flex items-center">
                    <div class="loading-spinner mr-3"></div>
                    Real-time Progress
                </h3>
                <div id="progressMessages" class="space-y-2 max-h-96 overflow-y-auto bg-gray-50 p-4 rounded-lg">
                    <!-- Progress messages will appear here -->
                </div>
            </div>
        `;
    }

    addProgressMessage(message, timestamp, type = 'info') {
        const progressMessages = document.getElementById('progressMessages');
        if (!progressMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `progress-message ${type} fade-in`;
        
        const time = new Date(timestamp).toLocaleTimeString();
        const typeIcon = this.getMessageIcon(type);
        
        messageDiv.innerHTML = `
            <div class="flex items-start space-x-2">
                <span class="message-icon">${typeIcon}</span>
                <div class="flex-1">
                    <div class="message-text">${this.escapeHtml(message)}</div>
                    <div class="message-time">${time}</div>
                </div>
            </div>
        `;

        progressMessages.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        progressMessages.scrollTop = progressMessages.scrollHeight;
    }

    getMessageIcon(type) {
        const icons = {
            'info': '📊',
            'progress': '🔄',
            'success': '✅',
            'error': '❌'
        };
        return icons[type] || '📝';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    startStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }

        this.statusInterval = setInterval(() => {
            this.checkJobStatus();
        }, 3000); // Check every 3 seconds

        // Check immediately
        this.checkJobStatus();
    }

    async checkJobStatus() {
        if (!this.currentJobId) return;

        try {
            const response = await fetch(`/api/status/${this.currentJobId}`);
            const data = await response.json();

            if (response.ok) {
                if (data.status === 'completed') {
                    this.jobCompleted = true; // Mark as completed
                    this.showResults(data);
                    this.stopStatusPolling();
                    this.closeProgressStream();
                    this.disableForm(false);
                } else if (data.status === 'failed') {
                    this.jobCompleted = true; // Mark as completed (failed)
                    this.showError(data.message);
                    this.stopStatusPolling();
                    this.closeProgressStream();
                    this.disableForm(false);
                }
            }
        } catch (error) {
            console.error('Status check failed:', error);
        }
    }

    stopStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }

    closeProgressStream() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }

    clearPreviousResults() {
        const statusSection = document.getElementById('statusSection');
        const resultsSection = document.getElementById('resultsSection');
        
        statusSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
        this.jobCompleted = false; // Reset completion flag
    }

    showResults(data) {
        if (!data.insights) return;

        const resultsSection = document.getElementById('resultsSection');
        const resultsContent = document.getElementById('resultsContent');
        
        resultsSection.classList.remove('hidden');
        
        let html = `
            <div class="mb-6">
                <h3 class="text-lg font-semibold text-gray-700 mb-2">
                    📈 Analysis Summary
                </h3>
                <p class="text-gray-600">
                    Successfully analyzed ${data.total_segments} segments with structured insights.
                </p>
            </div>
        `;

        data.insights.forEach((segment, index) => {
            html += `
                <div class="insight-card fade-in" style="animation-delay: ${index * 0.1}s">
                    <h3>📝 ${segment.segment_name}</h3>
                    <p><strong>Summary:</strong> ${segment.summary}</p>
                    
                    <div class="grid md:grid-cols-2 gap-4">
                        <div>
                            <h4 class="font-semibold text-gray-700 mb-2">💡 Key Insights</h4>
                            <ul class="insight-list">
                                ${segment.key_insights.map(insight => `<li>${insight}</li>`).join('')}
                            </ul>
                        </div>
                        
                        <div>
                            <h4 class="font-semibold text-gray-700 mb-2">🎯 Actionable Takeaways</h4>
                            <ul class="insight-list takeaway-list">
                                ${segment.actionable_takeaways.map(takeaway => `<li>${takeaway}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
            `;
        });

        resultsContent.innerHTML = html;
    }

    showError(message) {
        const statusSection = document.getElementById('statusSection');
        const statusContent = document.getElementById('statusContent');
        
        statusSection.classList.remove('hidden');
        statusContent.innerHTML = `
            <div class="border-l-4 border-red-500 bg-red-50 p-4">
                <div class="flex items-center">
                    <span class="text-red-500 mr-2">❌</span>
                    <p class="font-medium text-red-700">Error: ${message}</p>
                </div>
            </div>
        `;
    }

    disableForm(disabled) {
        const btn = document.getElementById('analyzeBtn');
        const inputs = document.querySelectorAll('#analysisForm input, #analysisForm select');
        
        btn.disabled = disabled;
        inputs.forEach(input => input.disabled = disabled);
        
        if (disabled) {
            btn.textContent = 'Processing...';
            btn.classList.add('pulse');
        } else {
            btn.textContent = 'Analyze';
            btn.classList.remove('pulse');
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeAnalyzer();
});
