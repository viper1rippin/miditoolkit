# MIDI to JSON Converter Web Application

A modern web application for converting MIDI files to structured JSON metadata with integrated AWS S3 storage support.

![MIDI Converter Dashboard](https://img.shields.io/badge/status-ready-green)

## Features

- 🎵 **MIDI to JSON Conversion**: Convert MIDI files to structured JSON with comprehensive metadata
- ☁️ **AWS S3 Integration**: One-click upload to Amazon S3 buckets
- 📊 **Real-time Statistics**: Track ongoing, completed, failed, and uploaded jobs
- 🔄 **Auto-refresh Dashboard**: Live updates every 5 seconds
- 📥 **Batch Processing**: Upload and manage multiple files
- 🎨 **Modern UI**: Clean, responsive interface
- 🐳 **Docker Ready**: Easy deployment with Docker Compose
- 🔐 **Secure**: Industry-standard AWS SDK integration

## Screenshots

### Dashboard
- Real-time statistics display
- Job status monitoring (Pending, Processing, Completed, Failed)
- S3 upload tracking

### Features
- Drag-and-drop file upload
- Automatic metadata extraction
- One-click S3 integration
- Download processed JSON files

## Architecture

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────┐
│  Frontend (Nginx)│ ──▶ │  Backend (Flask) │ ──▶ │  Database   │
│   Static Files   │      │   RESTful API    │      │  (SQLite)   │
└─────────────────┘      └──────────────────┘      └─────────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │   AWS S3        │
                         │   File Storage  │
                         └─────────────────┘
```

## Prerequisites

### Option 1: Docker (Recommended)
- Docker 20.10+
- Docker Compose 1.29+

### Option 2: Manual Installation
- Python 3.9+
- Node.js 16+ (for development)
- pip
- virtualenv (recommended)

## Quick Start with Docker

### 1. Clone the Repository

```bash
cd miditoolkit/webapp
```

### 2. Configure Environment (Optional)

```bash
cp .env.example .env
# Edit .env with your AWS credentials (optional - can configure via UI)
nano .env
```

### 3. Start the Application

```bash
docker-compose up -d
```

### 4. Access the Application

Open your browser and navigate to:
- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:5000/api/health

### 5. Configure S3 (Optional)

You can configure S3 in two ways:

**A. Via Web UI (Recommended for first-time setup):**
1. Open http://localhost:8080
2. Click "Configure S3" button
3. Enter your AWS credentials and bucket name
4. Click "Save S3 Configuration"

**B. Via Environment Variables:**
Edit `.env` file before starting Docker:
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

## Manual Installation

### Backend Setup

```bash
cd webapp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install miditoolkit from parent directory
pip install -e ..

# Create required directories
mkdir -p backend/uploads backend/outputs

# Run backend
python backend/app.py
```

Backend will start on http://localhost:5000

### Frontend Setup

```bash
# Frontend is static files - just serve with any web server
cd frontend

# Option 1: Python HTTP server
python -m http.server 8080

# Option 2: Node.js HTTP server
npx http-server -p 8080

# Option 3: Nginx (configure proxy to backend:5000)
```

Frontend will be available at http://localhost:8080

## AWS S3 Setup

### 1. Create an S3 Bucket

```bash
# Using AWS CLI
aws s3 mb s3://your-midi-bucket --region us-east-1
```

Or create via AWS Console:
1. Go to S3 service
2. Click "Create bucket"
3. Enter bucket name (e.g., `my-midi-json-bucket`)
4. Choose region
5. Keep default settings or configure as needed
6. Click "Create bucket"

### 2. Create IAM User with S3 Access

1. Go to IAM service in AWS Console
2. Click "Users" → "Add user"
3. Username: `midi-converter-app`
4. Access type: ✓ Programmatic access
5. Attach policy: `AmazonS3FullAccess` (or create custom policy below)
6. Complete wizard and **save Access Key ID and Secret Access Key**

### 3. Custom IAM Policy (More Secure)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name",
        "arn:aws:s3:::your-bucket-name/*"
      ]
    }
  ]
}
```

### 4. Configure in Application

Use the web UI to configure S3:
1. Access Key ID: `AKIA...`
2. Secret Access Key: `wJalr...`
3. Region: `us-east-1` (or your bucket's region)
4. Bucket Name: `your-bucket-name`

## Usage Guide

### 1. Upload MIDI File

1. Click or drag a MIDI file to the upload area
2. (Optional) Enter metadata:
   - Song ID
   - Title
   - Genre
   - Source
3. (Optional) Check "Automatically upload to S3"
4. Click "Upload and Convert"

### 2. Monitor Jobs

The dashboard automatically refreshes and shows:
- **Total Jobs**: All conversion jobs
- **Completed**: Successfully processed files
- **Pending**: Jobs waiting or in progress
- **Failed**: Jobs that encountered errors
- **Uploaded to S3**: Files successfully uploaded to S3

### 3. Manage Jobs

For each job, you can:
- **Download JSON**: Download the converted JSON file
- **Upload to S3**: Manually upload to S3 (if not auto-uploaded)
- **Delete**: Remove job and associated files

### 4. Filter Jobs

Use the status filter to view:
- All jobs
- Pending jobs
- Processing jobs
- Completed jobs
- Failed jobs

## API Endpoints

### Health Check
```http
GET /api/health
```

### S3 Configuration
```http
GET /api/s3/status
POST /api/s3/config
```

### File Upload
```http
POST /api/upload
```

### Jobs Management
```http
GET /api/jobs
GET /api/jobs/:id
DELETE /api/jobs/:id
POST /api/jobs/:id/upload-s3
GET /api/jobs/:id/output
```

### Statistics
```http
GET /api/stats
```

## Configuration

### Backend Configuration

Edit `backend/app.py` or use environment variables:

```python
# File size limit (default: 50MB)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Upload folder
app.config['UPLOAD_FOLDER'] = 'uploads'

# Output folder
app.config['OUTPUT_FOLDER'] = 'outputs'
```

### Frontend Configuration

Edit `frontend/app.js`:

```javascript
// API base URL
const API_BASE_URL = 'http://localhost:5000/api';

// Auto-refresh interval (milliseconds)
setInterval(loadData, 5000);  // 5 seconds
```

## Deployment to Production

### Using Docker Compose (Recommended)

```bash
# 1. Set production environment
export FLASK_ENV=production

# 2. Configure AWS credentials in .env
nano .env

# 3. Start services
docker-compose up -d

# 4. View logs
docker-compose logs -f

# 5. Stop services
docker-compose down
```

### Using systemd (Linux)

Create `/etc/systemd/system/midi-converter.service`:

```ini
[Unit]
Description=MIDI to JSON Converter Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/midi-converter/webapp
Environment="PATH=/var/www/midi-converter/webapp/venv/bin"
ExecStart=/var/www/midi-converter/webapp/venv/bin/python backend/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable midi-converter
sudo systemctl start midi-converter
```

### Nginx Configuration (Production)

Create `/etc/nginx/sites-available/midi-converter`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Frontend
    location / {
        root /var/www/midi-converter/webapp/frontend;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        client_max_body_size 50M;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/midi-converter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Port 5000 already in use
sudo lsof -i :5000

# 2. Missing dependencies
pip install -r requirements.txt

# 3. Database permissions
chmod 644 backend/jobs.db
```

### S3 Upload Failing

```bash
# Test AWS credentials
aws s3 ls s3://your-bucket-name

# Common issues:
# 1. Wrong region
# 2. Insufficient permissions
# 3. Bucket doesn't exist
```

### Frontend Not Loading

```bash
# Check backend is running
curl http://localhost:5000/api/health

# Check CORS settings in backend/app.py
# Update API_BASE_URL in frontend/app.js
```

## Development

### Run in Development Mode

```bash
# Backend with auto-reload
export FLASK_ENV=development
python backend/app.py

# Frontend with live reload
cd frontend
npx live-server
```

### Run Tests

```bash
# Backend tests
pytest backend/tests/

# Integration tests
python backend/test_integration.py
```

## Security Considerations

1. **Never commit AWS credentials** to version control
2. Use **IAM policies with minimum required permissions**
3. Enable **S3 bucket encryption**
4. Use **HTTPS in production**
5. Configure **CORS properly** for your domain
6. Set **strong SECRET_KEY** for Flask
7. Implement **rate limiting** for production use
8. Regular **security updates** for dependencies

## Performance Tuning

### For High Volume

1. **Use Redis** for task queue instead of synchronous processing
2. **Add Celery** workers for background processing
3. **Increase workers** in Docker Compose
4. **Use PostgreSQL** instead of SQLite
5. **Enable caching** for API responses
6. **CDN** for frontend static files

Example with Celery:
```bash
# Add to docker-compose.yml
redis:
  image: redis:alpine
worker:
  build: .
  command: celery -A backend.tasks worker
```

## License

MIT License - Same as miditoolkit

## Support

For issues and questions:
1. Check this README
2. Review API documentation
3. Check backend logs: `docker-compose logs backend`
4. Open an issue on GitHub

## Acknowledgments

- Built on [miditoolkit](https://github.com/YatingMusic/miditoolkit)
- Uses AWS SDK (boto3)
- Flask web framework
- Modern CSS and JavaScript
