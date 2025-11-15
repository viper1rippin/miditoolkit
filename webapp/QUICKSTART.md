# Quick Start Guide

Get your MIDI to JSON Converter running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- (Optional) AWS S3 bucket for cloud storage

## Step 1: Start the Application

```bash
cd webapp
./start.sh
```

That's it! The script will:
- ✓ Check dependencies
- ✓ Build Docker containers
- ✓ Start all services
- ✓ Display access URLs

## Step 2: Access the Web Interface

Open your browser:
```
http://localhost:8080
```

You should see the MIDI to JSON Converter dashboard with:
- Statistics panel (Total, Completed, Pending, Failed, S3 Uploads)
- Upload section
- Jobs list

## Step 3: (Optional) Configure AWS S3

### Method A: Via Web UI (Easiest)

1. Click the **"Configure S3"** button in the web interface
2. Enter your AWS credentials:
   - AWS Access Key ID
   - AWS Secret Access Key
   - AWS Region (e.g., `us-east-1`)
   - S3 Bucket Name
3. Click **"Save S3 Configuration"**
4. You should see "✓ Connected to your-bucket-name"

### Method B: Via Environment File

1. Stop the application: `./stop.sh`
2. Edit `.env` file:
   ```bash
   nano .env
   ```
3. Add your AWS credentials:
   ```
   AWS_ACCESS_KEY_ID=AKIA...
   AWS_SECRET_ACCESS_KEY=wJalr...
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=my-midi-bucket
   ```
4. Restart: `./start.sh`

## Step 4: Convert Your First MIDI File

1. **Upload a File**
   - Click or drag a MIDI file to the upload area
   - The file will be highlighted in blue

2. **Add Metadata (Optional)**
   - Song ID: e.g., `0001`
   - Title: e.g., `My First Song`
   - Genre: e.g., `Pop`
   - Source: e.g., `MuseScore`

3. **Configure Upload**
   - Check "Automatically upload to S3" if you want auto-upload
   - (S3 must be configured first)

4. **Convert**
   - Click **"Upload and Convert"**
   - Watch the progress in real-time

5. **Download Result**
   - Once completed, click **"Download JSON"** on the job
   - Or if auto-upload was enabled, it's already in S3!

## Common Commands

```bash
# Start the application
./start.sh

# Stop the application
./stop.sh

# View logs
docker-compose logs -f

# View only backend logs
docker-compose logs -f backend

# Restart after changes
docker-compose restart

# Rebuild after code changes
docker-compose up -d --build

# Clean everything (removes data!)
docker-compose down -v
```

## Accessing Different Services

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:8080 | Main web interface |
| Backend API | http://localhost:5000/api | REST API |
| Health Check | http://localhost:5000/api/health | Status check |
| Stats Endpoint | http://localhost:5000/api/stats | Job statistics |

## Example JSON Output

After converting a MIDI file, you'll get JSON like this:

```json
{
  "song_id": "0001",
  "title": "Mr. Blue Sky",
  "genre": "Rock",
  "tempo_bpm": 175,
  "key": "F Major",
  "time_signature": "4/4",
  "tracks": [
    {
      "lane": 0,
      "program_number": 73,
      "program_name": "Flute",
      "role": "Melody"
    },
    {
      "lane": 1,
      "program_number": 0,
      "program_name": "Acoustic Grand Piano",
      "role": "Piano"
    }
  ],
  "latent_tags": {
    "arrangement_complexity": "high",
    "layer_count": 9,
    "polyphony": 0.34
  },
  "source": "Upload"
}
```

## Troubleshooting

### Application won't start

```bash
# Check Docker is running
docker ps

# Check port availability
lsof -i :8080
lsof -i :5000

# View error logs
docker-compose logs
```

### Can't access the web interface

1. Make sure Docker containers are running:
   ```bash
   docker-compose ps
   ```

2. Both `backend` and `frontend` should be "Up"

3. Try restarting:
   ```bash
   ./stop.sh
   ./start.sh
   ```

### S3 upload fails

1. **Check credentials**
   - Are they correct?
   - Try them with AWS CLI: `aws s3 ls s3://your-bucket`

2. **Check bucket region**
   - Must match the region in configuration

3. **Check IAM permissions**
   - User needs `s3:PutObject` permission

4. **Test in web UI**
   - The configuration form will test the connection

### File upload fails

1. **Check file size**
   - Maximum 50MB by default
   - Shown in upload hint

2. **Check file format**
   - Must be `.mid` or `.midi`

3. **Check backend logs**
   ```bash
   docker-compose logs backend
   ```

## Next Steps

- ✓ Upload and convert MIDI files
- ✓ Download JSON outputs
- ✓ Upload to S3 for cloud storage
- ✓ Monitor job statistics

For more details, see [README.md](README.md)

## Getting Help

1. Check the full [README.md](README.md)
2. View logs: `docker-compose logs -f`
3. Check API health: http://localhost:5000/api/health
4. Open an issue on GitHub

---

**Enjoy converting MIDI files to JSON! 🎵→📄**
