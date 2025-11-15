// Configuration
// Use relative URL to work with nginx proxy in production
const API_BASE_URL = window.location.port === '8080'
    ? '/api'  // Production: through nginx proxy
    : 'http://localhost:5000/api';  // Development: direct to Flask

// State
let jobs = [];
let stats = {};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
});

async function initializeApp() {
    await checkS3Status();
    await loadStats();
    await loadJobs();

    // Auto-refresh every 5 seconds
    setInterval(async () => {
        await loadStats();
        await loadJobs();
    }, 5000);
}

function setupEventListeners() {
    // S3 Configuration
    document.getElementById('toggleS3Config').addEventListener('click', toggleS3ConfigForm);
    document.getElementById('s3ConfigForm').addEventListener('submit', handleS3Configuration);

    // Upload Form
    document.getElementById('uploadForm').addEventListener('submit', handleFileUpload);
    document.getElementById('midiFile').addEventListener('change', handleFileSelect);

    // Jobs
    document.getElementById('refreshJobs').addEventListener('click', loadJobs);
    document.getElementById('statusFilter').addEventListener('change', loadJobs);
}

// S3 Functions
function toggleS3ConfigForm() {
    const form = document.getElementById('s3ConfigForm');
    form.classList.toggle('hidden');
}

async function checkS3Status() {
    try {
        const response = await fetch(`${API_BASE_URL}/s3/status`);
        const data = await response.json();

        const statusBadge = document.getElementById('s3StatusBadge');
        if (data.configured) {
            statusBadge.textContent = `✓ Connected to ${data.bucket_name}`;
            statusBadge.classList.add('configured');
        } else {
            statusBadge.textContent = 'Not Configured';
            statusBadge.classList.remove('configured');
        }
    } catch (error) {
        console.error('Failed to check S3 status:', error);
    }
}

async function handleS3Configuration(e) {
    e.preventDefault();

    const data = {
        aws_access_key_id: document.getElementById('awsAccessKeyId').value,
        aws_secret_access_key: document.getElementById('awsSecretAccessKey').value,
        region_name: document.getElementById('awsRegion').value,
        bucket_name: document.getElementById('s3BucketName').value
    };

    try {
        const response = await fetch(`${API_BASE_URL}/s3/config`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            alert('S3 configured successfully!');
            await checkS3Status();
            document.getElementById('s3ConfigForm').classList.add('hidden');
            document.getElementById('s3ConfigForm').reset();
        } else {
            alert(`Failed to configure S3: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

// Upload Functions
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        const uploadContent = document.querySelector('.upload-content p');
        uploadContent.textContent = `Selected: ${file.name}`;
    }
}

async function handleFileUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById('midiFile');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('song_id', document.getElementById('songId').value);
    formData.append('title', document.getElementById('songTitle').value);
    formData.append('genre', document.getElementById('songGenre').value);
    formData.append('source', document.getElementById('songSource').value);
    formData.append('auto_upload_s3', document.getElementById('autoUploadS3').checked);

    // Show loading state
    const submitBtn = document.querySelector('#uploadForm button[type="submit"]');
    const btnText = document.getElementById('uploadBtnText');
    const spinner = document.getElementById('uploadSpinner');

    submitBtn.disabled = true;
    btnText.textContent = 'Processing...';
    spinner.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            alert('File uploaded and processed successfully!');
            document.getElementById('uploadForm').reset();
            document.querySelector('.upload-content p').textContent = 'Click or drag MIDI file to upload';
            await loadStats();
            await loadJobs();
        } else {
            alert(`Upload failed: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    } finally {
        submitBtn.disabled = false;
        btnText.textContent = 'Upload and Convert';
        spinner.classList.add('hidden');
    }
}

// Stats Functions
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();

        document.getElementById('statTotal').textContent = data.total;
        document.getElementById('statCompleted').textContent = data.completed;
        document.getElementById('statPending').textContent = data.pending + data.processing;
        document.getElementById('statFailed').textContent = data.failed;
        document.getElementById('statS3').textContent = data.uploaded_to_s3;

        stats = data;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

// Jobs Functions
async function loadJobs() {
    try {
        const status = document.getElementById('statusFilter').value;
        let url = `${API_BASE_URL}/jobs?limit=50`;

        if (status) {
            url += `&status=${status}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        jobs = data.jobs;
        renderJobs(jobs);
    } catch (error) {
        console.error('Failed to load jobs:', error);
    }
}

function renderJobs(jobs) {
    const container = document.getElementById('jobsContainer');

    if (jobs.length === 0) {
        container.innerHTML = '<p class="empty-state">No jobs found. Upload a MIDI file to get started!</p>';
        return;
    }

    container.innerHTML = jobs.map(job => createJobItem(job)).join('');

    // Attach event listeners
    jobs.forEach(job => {
        const downloadBtn = document.getElementById(`download-${job.id}`);
        const uploadBtn = document.getElementById(`upload-s3-${job.id}`);
        const deleteBtn = document.getElementById(`delete-${job.id}`);

        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => downloadJobOutput(job.id));
        }

        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => uploadJobToS3(job.id));
        }

        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => deleteJob(job.id));
        }
    });
}

function createJobItem(job) {
    const createdDate = new Date(job.created_at).toLocaleString();
    const completedDate = job.completed_at ? new Date(job.completed_at).toLocaleString() : 'N/A';

    let actions = '';
    if (job.status === 'completed') {
        actions = `
            <button id="download-${job.id}" class="btn btn-primary btn-small">Download JSON</button>
            ${!job.s3_key && stats.s3_configured ? `<button id="upload-s3-${job.id}" class="btn btn-success btn-small">Upload to S3</button>` : ''}
        `;
    }

    actions += `<button id="delete-${job.id}" class="btn btn-danger btn-small">Delete</button>`;

    const s3Badge = job.s3_key ? '<span class="s3-badge">☁️ In S3</span>' : '';

    return `
        <div class="job-item status-${job.status}">
            <div class="job-header">
                <div>
                    <div class="job-title">${job.title || job.filename}</div>
                    ${s3Badge}
                </div>
                <span class="job-status ${job.status}">${job.status}</span>
            </div>

            <div class="job-meta">
                <div class="job-meta-item">
                    <strong>File:</strong> ${job.filename}
                </div>
                <div class="job-meta-item">
                    <strong>ID:</strong> ${job.song_id || 'N/A'}
                </div>
                <div class="job-meta-item">
                    <strong>Genre:</strong> ${job.genre}
                </div>
                <div class="job-meta-item">
                    <strong>Source:</strong> ${job.source}
                </div>
                <div class="job-meta-item">
                    <strong>Created:</strong> ${createdDate}
                </div>
                <div class="job-meta-item">
                    <strong>Completed:</strong> ${completedDate}
                </div>
            </div>

            ${job.error_message ? `<div class="error-message">Error: ${job.error_message}</div>` : ''}

            <div class="job-actions">
                ${actions}
            </div>
        </div>
    `;
}

async function downloadJobOutput(jobId) {
    try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/output`);

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `job_${jobId}.json`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } else {
            const error = await response.json();
            alert(`Download failed: ${error.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function uploadJobToS3(jobId) {
    if (!confirm('Upload this job output to S3?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/upload-s3`, {
            method: 'POST'
        });

        const result = await response.json();

        if (result.success) {
            alert('File uploaded to S3 successfully!');
            await loadJobs();
        } else {
            alert(`Upload failed: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job? This cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
            method: 'DELETE'
        });

        const result = await response.json();

        if (result.success) {
            await loadStats();
            await loadJobs();
        } else {
            alert(`Delete failed: ${result.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}
