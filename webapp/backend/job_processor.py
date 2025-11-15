"""
Job processor for converting MIDI files to JSON
"""

import sys
from pathlib import Path

# Add parent directory to path to import miditoolkit
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from miditoolkit import MidiJsonGenerator


def process_midi_file(job_id, file_path, output_folder, song_id=None, title=None, genre=None, source=None):
    """
    Process a MIDI file and convert it to JSON.

    Args:
        job_id: Job ID for tracking
        file_path: Path to the MIDI file
        output_folder: Folder to save output
        song_id: Optional song ID
        title: Optional song title
        genre: Optional genre
        source: Optional source

    Returns:
        str: Path to the output JSON file

    Raises:
        Exception: If processing fails
    """
    try:
        # Generate output filename
        input_filename = Path(file_path).stem
        output_filename = f"{job_id}_{input_filename}.json"
        output_path = Path(output_folder) / output_filename

        # Load MIDI and generate JSON
        generator = MidiJsonGenerator.from_file(file_path)

        # Use song_id as job_id if not provided
        if not song_id:
            song_id = str(job_id).zfill(4)

        # Use filename as title if not provided
        if not title:
            title = Path(file_path).stem

        # Generate and save JSON
        generator.save_json(
            str(output_path),
            song_id=song_id,
            title=title,
            genre=genre or 'Unknown',
            source=source or 'Upload'
        )

        return str(output_path)

    except Exception as e:
        raise Exception(f"MIDI processing failed: {str(e)}")
