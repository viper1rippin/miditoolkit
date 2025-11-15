"""
Database models for job tracking
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()


class JobStatus(enum.Enum):
    """Job status enumeration."""
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'


class Job(db.Model):
    """Job model for tracking MIDI conversion jobs."""
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    output_path = db.Column(db.String(512))

    # Metadata
    song_id = db.Column(db.String(100))
    title = db.Column(db.String(255))
    genre = db.Column(db.String(100))
    source = db.Column(db.String(100))

    # Status
    status = db.Column(db.Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    error_message = db.Column(db.Text)

    # S3 integration
    auto_upload_s3 = db.Column(db.Boolean, default=False)
    s3_key = db.Column(db.String(512))
    s3_uploaded_at = db.Column(db.DateTime)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)

    def to_dict(self):
        """Convert job to dictionary."""
        return {
            'id': self.id,
            'filename': self.filename,
            'song_id': self.song_id,
            'title': self.title,
            'genre': self.genre,
            'source': self.source,
            'status': self.status.value,
            'error_message': self.error_message,
            'auto_upload_s3': self.auto_upload_s3,
            's3_key': self.s3_key,
            's3_uploaded_at': self.s3_uploaded_at.isoformat() if self.s3_uploaded_at else None,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'has_output': self.output_path is not None
        }

    def __repr__(self):
        return f'<Job {self.id}: {self.filename} - {self.status.value}>'
