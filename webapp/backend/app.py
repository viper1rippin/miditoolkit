"""
MIDI to JSON Converter Web Application
Backend API with S3 integration and job tracking
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from pathlib import Path
import traceback

from database import db, Job, JobStatus
from s3_manager import S3Manager
from job_processor import process_midi_file

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jobs.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Create folders
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Initialize database
db.init_app(app)

# Initialize S3 manager
s3_manager = S3Manager()

# Create tables
with app.app_context():
    db.create_all()


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mid', 'midi'}


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        's3_configured': s3_manager.is_configured()
    })


@app.route('/api/s3/config', methods=['POST'])
def configure_s3():
    """Configure S3 credentials and bucket."""
    try:
        data = request.json

        s3_manager.configure(
            aws_access_key_id=data.get('aws_access_key_id'),
            aws_secret_access_key=data.get('aws_secret_access_key'),
            region_name=data.get('region_name', 'us-east-1'),
            bucket_name=data.get('bucket_name')
        )

        # Test connection
        if s3_manager.test_connection():
            return jsonify({
                'success': True,
                'message': 'S3 configured successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to S3'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/s3/status', methods=['GET'])
def s3_status():
    """Get S3 configuration status."""
    return jsonify({
        'configured': s3_manager.is_configured(),
        'bucket_name': s3_manager.bucket_name if s3_manager.is_configured() else None,
        'region': s3_manager.region_name if s3_manager.is_configured() else None
    })


@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload MIDI file and create conversion job."""
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']

        # Check if file is selected
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Check if file is allowed
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only .mid and .midi files are allowed'}), 400

        # Get metadata from form
        song_id = request.form.get('song_id', '')
        title = request.form.get('title', '')
        genre = request.form.get('genre', 'Unknown')
        source = request.form.get('source', 'Upload')
        auto_upload_s3 = request.form.get('auto_upload_s3', 'false').lower() == 'true'

        # Secure filename
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"

        # Save file
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        # Create job in database
        job = Job(
            filename=filename,
            file_path=file_path,
            song_id=song_id or None,
            title=title or None,
            genre=genre,
            source=source,
            status=JobStatus.PENDING,
            auto_upload_s3=auto_upload_s3
        )

        db.session.add(job)
        db.session.commit()

        # Process the file (in a real production app, this would be async)
        try:
            output_path = process_midi_file(
                job_id=job.id,
                file_path=file_path,
                output_folder=app.config['OUTPUT_FOLDER'],
                song_id=song_id,
                title=title,
                genre=genre,
                source=source
            )

            job.output_path = output_path
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()

            # Auto-upload to S3 if configured
            if auto_upload_s3 and s3_manager.is_configured():
                try:
                    s3_key = s3_manager.upload_file(output_path, f"json/{Path(output_path).name}")
                    job.s3_key = s3_key
                    job.s3_uploaded_at = datetime.utcnow()
                except Exception as e:
                    job.error_message = f"S3 upload failed: {str(e)}"

            db.session.commit()

            return jsonify({
                'success': True,
                'job_id': job.id,
                'message': 'File processed successfully'
            })

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.session.commit()

            return jsonify({
                'success': False,
                'job_id': job.id,
                'error': str(e)
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs with optional filtering."""
    try:
        # Get query parameters
        status = request.args.get('status')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)

        # Build query
        query = Job.query

        if status:
            query = query.filter_by(status=JobStatus[status.upper()])

        # Get total count
        total = query.count()

        # Get jobs
        jobs = query.order_by(Job.created_at.desc()).limit(limit).offset(offset).all()

        return jsonify({
            'jobs': [job.to_dict() for job in jobs],
            'total': total,
            'limit': limit,
            'offset': offset
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get job details."""
    try:
        job = Job.query.get_or_404(job_id)
        return jsonify(job.to_dict())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/<int:job_id>/output', methods=['GET'])
def download_output(job_id):
    """Download job output file."""
    try:
        job = Job.query.get_or_404(job_id)

        if job.status != JobStatus.COMPLETED:
            return jsonify({'error': 'Job not completed'}), 400

        if not job.output_path or not os.path.exists(job.output_path):
            return jsonify({'error': 'Output file not found'}), 404

        return send_file(
            job.output_path,
            mimetype='application/json',
            as_attachment=True,
            download_name=f"{Path(job.output_path).name}"
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/<int:job_id>/upload-s3', methods=['POST'])
def upload_to_s3(job_id):
    """Upload job output to S3."""
    try:
        if not s3_manager.is_configured():
            return jsonify({'error': 'S3 not configured'}), 400

        job = Job.query.get_or_404(job_id)

        if job.status != JobStatus.COMPLETED:
            return jsonify({'error': 'Job not completed'}), 400

        if not job.output_path or not os.path.exists(job.output_path):
            return jsonify({'error': 'Output file not found'}), 404

        # Upload to S3
        s3_key = s3_manager.upload_file(
            job.output_path,
            f"json/{Path(job.output_path).name}"
        )

        # Update job
        job.s3_key = s3_key
        job.s3_uploaded_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            's3_key': s3_key,
            'message': 'File uploaded to S3 successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job and its files."""
    try:
        job = Job.query.get_or_404(job_id)

        # Delete files
        if job.file_path and os.path.exists(job.file_path):
            os.remove(job.file_path)

        if job.output_path and os.path.exists(job.output_path):
            os.remove(job.output_path)

        # Delete from database
        db.session.delete(job)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Job deleted successfully'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics."""
    try:
        total = Job.query.count()
        pending = Job.query.filter_by(status=JobStatus.PENDING).count()
        processing = Job.query.filter_by(status=JobStatus.PROCESSING).count()
        completed = Job.query.filter_by(status=JobStatus.COMPLETED).count()
        failed = Job.query.filter_by(status=JobStatus.FAILED).count()

        uploaded_to_s3 = Job.query.filter(Job.s3_key.isnot(None)).count()

        return jsonify({
            'total': total,
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed,
            'uploaded_to_s3': uploaded_to_s3,
            's3_configured': s3_manager.is_configured()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
