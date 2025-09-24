// YouTube Analysis System Frontend
class YouTubeAnalyzer {
    constructor() {
        this.currentJobId = null;
        this.statusInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadRecentJobs();
    }

    bindEvents() {
        const form = document.getElementById('analysisForm');
        form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const videoUrl = document.getElementById('videoUrl').value;
        const callbackLevel = document.getElementById('callbackLevel').value;
        
        if (!videoUrl) {
            this.showError('Please enter a YouTube URL');
            return;
        }

        this.startAnalysis(videoUrl, callbackLevel);
    }

    async startAnalysis(videoUrl, callbackLevel) {
        try {
            this.showStatus('Submitting analysis request...', 'processing');
            this.disableForm(true);

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
                this.showStatus(`Analysis started! Job ID: ${data.job_id}`, 'processing');
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

    startStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
        }

        this.statusInterval = setInterval(() => {
            this.checkJobStatus();
        }, 2000); // Check every 2 seconds

        // Check immediately
        this.checkJobStatus();
    }

    async checkJobStatus() {
        if (!this.currentJobId) return;

        try {
            const response = await fetch(`/api/status/${this.currentJobId}`);
            const data = await response.json();

            if (response.ok) {
                this.updateStatus(data);

                if (data.status === 'completed') {
                    this.showResults(data);
                    this.stopStatusPolling();
                    this.disableForm(false);
                } else if (data.status === 'failed') {
                    this.showError(data.message);
                    this.stopStatusPolling();
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

    updateStatus(data) {
        const statusClass = `status-${data.status}`;
        const emoji = this.getStatusEmoji(data.status);
        
        this.showStatus(`${emoji} ${data.message}`, data.status);
    }

    getStatusEmoji(status) {
        const emojis = {
            'queued': '⏳',
            'processing': '🔄',
            'completed': '✅',
            'failed': '❌'
        };
        return emojis[status] || '📊';
    }

    showStatus(message, status) {
        const statusSection = document.getElementById('statusSection');
        const statusContent = document.getElementById('statusContent');
        
        statusSection.classList.remove('hidden');
        
        const statusClass = `status-${status}`;
        statusContent.innerHTML = `
            <div class="border-l-4 p-4 ${statusClass}">
                <div class="flex items-center">
                    ${status === 'processing' ? '<div class="loading-spinner mr-4"></div>' : ''}
                    <p class="font-medium">${message}</p>
                </div>
            </div>
        `;
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
        this.loadRecentJobs(); // Refresh recent jobs
    }

    showError(message) {
        this.showStatus(`❌ Error: ${message}`, 'failed');
    }

    disableForm(disabled) {
        const btn = document.getElementById('analyzeBtn');
        const inputs = document.querySelectorAll('#analysisForm input, #analysisForm select');
        
        btn.disabled = disabled;
        inputs.forEach(input => input.disabled = disabled);
        
        if (disabled) {
            btn.textContent = '🔄 Processing...';
            btn.classList.add('pulse');
        } else {
            btn.textContent = '🚀 Analyze Video';
            btn.classList.remove('pulse');
        }
    }

    async loadRecentJobs() {
        try {
            const response = await fetch('/api/jobs');
            const data = await response.json();
            
            if (response.ok && data.jobs) {
                this.displayRecentJobs(data.jobs);
            }
        } catch (error) {
            console.error('Failed to load recent jobs:', error);
        }
    }

    displayRecentJobs(jobs) {
        const recentJobsDiv = document.getElementById('recentJobs');
        
        if (jobs.length === 0) {
            recentJobsDiv.innerHTML = '<p class="text-gray-500">No recent analyses</p>';
            return;
        }

        const html = jobs.slice(0, 5).map(job => {
            const emoji = this.getStatusEmoji(job.status);
            const statusClass = `status-${job.status}`;
            const date = new Date(job.created_at).toLocaleString();
            
            return `
                <div class="border-l-4 p-3 mb-2 ${statusClass}">
                    <div class="flex justify-between items-center">
                        <div>
                            <p class="font-medium">${emoji} ${job.message}</p>
                            <p class="text-sm opacity-75">${job.video_url}</p>
                        </div>
                        <div class="text-sm opacity-75">
                            ${date}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        recentJobsDiv.innerHTML = html;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new YouTubeAnalyzer();
});
