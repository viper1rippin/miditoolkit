"""MIDI to JSON Metadata Generator

This module provides functionality to extract comprehensive metadata from MIDI files
and export it in a structured JSON format.
"""

import json
from typing import Dict, List, Any, Optional
import numpy as np
from collections import defaultdict

from .midi.parser import MidiFile
from .constants import PROGRAM_NUMBER_TO_INSTRUMENT_NAME


def convert_numpy_types(obj):
    """Recursively convert numpy types to native Python types.

    Args:
        obj: Object to convert

    Returns:
        Object with numpy types converted to Python types
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj


class MidiJsonGenerator:
    """Generate structured JSON metadata from MIDI files."""

    def __init__(self, midi_file: MidiFile):
        """Initialize the generator with a MidiFile object.

        Args:
            midi_file: A loaded MidiFile object
        """
        self.midi = midi_file

    @classmethod
    def from_file(cls, filepath: str) -> 'MidiJsonGenerator':
        """Create a generator by loading a MIDI file.

        Args:
            filepath: Path to the MIDI file

        Returns:
            MidiJsonGenerator instance
        """
        midi = MidiFile(filepath)
        return cls(midi)

    def get_tempo_bpm(self) -> int:
        """Get the primary tempo in BPM.

        Returns the first tempo change or default tempo (120 BPM).
        """
        if self.midi.tempo_changes:
            return int(round(self.midi.tempo_changes[0].tempo))
        return 120

    def get_key_signature(self) -> str:
        """Get the key signature.

        Returns:
            Key signature as string (e.g., "C Major", "A minor")
        """
        if not self.midi.key_signature_changes:
            return "C Major"  # Default

        key_sig = self.midi.key_signature_changes[0]
        key_name = key_sig.key_name

        # Determine if major or minor
        if key_sig.key_number < 12:
            # Major key
            return f"{key_name} Major"
        else:
            # Minor key
            return f"{key_name}"

    def get_time_signature(self) -> str:
        """Get the time signature.

        Returns:
            Time signature as string (e.g., "4/4", "3/4")
        """
        if not self.midi.time_signature_changes:
            return "4/4"  # Default

        ts = self.midi.time_signature_changes[0]
        return f"{ts.numerator}/{ts.denominator}"

    def detect_track_role(self, instrument, all_instruments: List) -> str:
        """Detect the role of a track based on its characteristics.

        Args:
            instrument: The Instrument object to analyze
            all_instruments: List of all instruments for context

        Returns:
            Role string: "Melody", "Harmony", "Bass", "Rhythm", or "Accompaniment"
        """
        if instrument.is_drum:
            return "Rhythm"

        if not instrument.notes:
            return "Accompaniment"

        # Get pitch statistics
        pitches = [note.pitch for note in instrument.notes]
        avg_pitch = np.mean(pitches)
        pitch_range = max(pitches) - min(pitches) if pitches else 0

        # Bass instruments (low pitch range)
        if 32 <= instrument.program <= 39:  # Bass program numbers
            return "Bass"

        # If average pitch is very low, likely bass
        if avg_pitch < 50:
            return "Bass"

        # Calculate note density (notes per second)
        if self.midi.max_tick > 0:
            duration_ticks = self.midi.max_tick
            duration_seconds = duration_ticks / (self.midi.ticks_per_beat * self.get_tempo_bpm() / 60)
            note_density = len(instrument.notes) / duration_seconds if duration_seconds > 0 else 0
        else:
            note_density = 0

        # Melody typically has:
        # - Higher pitch
        # - Wide pitch range
        # - Moderate note density
        if avg_pitch > 60 and pitch_range > 12 and note_density > 1:
            return "Melody"

        # Harmony typically has:
        # - Multiple simultaneous notes (chords)
        # - Medium pitch range
        polyphony = self._calculate_track_polyphony(instrument)
        if polyphony > 1.5:
            return "Harmony"

        # Default to accompaniment
        return "Accompaniment"

    def _calculate_track_polyphony(self, instrument) -> float:
        """Calculate average polyphony (simultaneous notes) for a track.

        Args:
            instrument: The Instrument object

        Returns:
            Average number of simultaneous notes
        """
        if not instrument.notes:
            return 0.0

        # Create a timeline of note events
        events = []
        for note in instrument.notes:
            events.append((note.start, 1))   # Note on
            events.append((note.end, -1))    # Note off

        # Sort by time
        events.sort()

        # Calculate polyphony over time
        current_polyphony = 0
        polyphony_samples = []

        for time, delta in events:
            current_polyphony += delta
            polyphony_samples.append(current_polyphony)

        if polyphony_samples:
            return np.mean(polyphony_samples)
        return 0.0

    def calculate_overall_polyphony(self) -> float:
        """Calculate overall polyphony across all tracks.

        Returns:
            Average polyphony (0-1 normalized)
        """
        if not self.midi.instruments:
            return 0.0

        # Get all note events across all instruments
        all_events = []
        for instrument in self.midi.instruments:
            if instrument.is_drum:
                continue  # Skip drum tracks for polyphony calculation
            for note in instrument.notes:
                all_events.append((note.start, 1))
                all_events.append((note.end, -1))

        if not all_events:
            return 0.0

        # Sort by time
        all_events.sort()

        # Calculate polyphony over time
        current_polyphony = 0
        max_polyphony = 0
        polyphony_samples = []

        for time, delta in all_events:
            current_polyphony += delta
            max_polyphony = max(max_polyphony, current_polyphony)
            polyphony_samples.append(current_polyphony)

        if max_polyphony == 0:
            return 0.0

        # Normalize by max polyphony (capped at 10 for reasonable scaling)
        avg_polyphony = np.mean(polyphony_samples)
        normalized = min(avg_polyphony / 10.0, 1.0)

        return round(normalized, 2)

    def calculate_arrangement_complexity(self) -> str:
        """Determine arrangement complexity level.

        Returns:
            "low", "medium", or "high"
        """
        layer_count = len([inst for inst in self.midi.instruments if inst.notes])

        # Calculate note density
        total_notes = sum(len(inst.notes) for inst in self.midi.instruments)

        if layer_count <= 2 or total_notes < 100:
            return "low"
        elif layer_count <= 4 or total_notes < 500:
            return "medium"
        else:
            return "high"

    def get_tracks_metadata(self, use_detected_roles: bool = False) -> List[Dict[str, Any]]:
        """Get metadata for all tracks.

        Args:
            use_detected_roles: If True, use heuristic role detection instead of
                              original MIDI track names. Default: False (use original names)

        Returns:
            List of track metadata dictionaries
        """
        tracks = []

        for lane, instrument in enumerate(self.midi.instruments):
            # Get program name from General MIDI mapping
            program_name = PROGRAM_NUMBER_TO_INSTRUMENT_NAME.get(
                instrument.program,
                "Percussion" if instrument.is_drum else f"Program {instrument.program}"
            )

            # Get role from original MIDI track name, or detect if requested
            if use_detected_roles:
                role = self.detect_track_role(instrument, self.midi.instruments)
            else:
                # Use the original MIDI track name as the role
                role = instrument.name if instrument.name else "Untitled"

            track_info = {
                "lane": lane,
                "program_number": instrument.program,
                "program_name": program_name,
                "role": role
            }

            tracks.append(track_info)

        return tracks

    def get_latent_tags(self) -> Dict[str, Any]:
        """Calculate latent tags for the MIDI file.

        Returns:
            Dictionary of latent tags
        """
        layer_count = len([inst for inst in self.midi.instruments if inst.notes])

        return {
            "arrangement_complexity": self.calculate_arrangement_complexity(),
            "layer_count": layer_count,
            "polyphony": self.calculate_overall_polyphony()
        }

    def generate_json(
        self,
        song_id: Optional[str] = None,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        source: str = "MIDI",
        use_detected_roles: bool = False
    ) -> Dict[str, Any]:
        """Generate complete JSON metadata.

        Args:
            song_id: Optional song identifier
            title: Optional song title
            genre: Optional genre classification
            source: Source of the MIDI file (default: "MIDI")
            use_detected_roles: If True, detect roles using heuristics instead of
                              using original MIDI track names (default: False)

        Returns:
            Dictionary containing all metadata
        """
        metadata = {
            "song_id": song_id or "0000",
            "title": title or "Untitled",
            "genre": genre or "Unknown",
            "tempo_bpm": self.get_tempo_bpm(),
            "key": self.get_key_signature(),
            "time_signature": self.get_time_signature(),
            "tracks": self.get_tracks_metadata(use_detected_roles),
            "latent_tags": self.get_latent_tags(),
            "source": source
        }

        return metadata

    def to_json_string(
        self,
        song_id: Optional[str] = None,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        source: str = "MIDI",
        indent: int = 2,
        use_detected_roles: bool = False
    ) -> str:
        """Generate JSON metadata as a formatted string.

        Args:
            song_id: Optional song identifier
            title: Optional song title
            genre: Optional genre classification
            source: Source of the MIDI file
            indent: JSON indentation level (default: 2)
            use_detected_roles: If True, detect roles using heuristics instead of
                              using original MIDI track names (default: False)

        Returns:
            Formatted JSON string
        """
        metadata = self.generate_json(song_id, title, genre, source, use_detected_roles)
        # Convert numpy types to native Python types for JSON serialization
        metadata = convert_numpy_types(metadata)
        return json.dumps(metadata, indent=indent, ensure_ascii=False)

    def save_json(
        self,
        output_path: str,
        song_id: Optional[str] = None,
        title: Optional[str] = None,
        genre: Optional[str] = None,
        source: str = "MIDI",
        indent: int = 2,
        use_detected_roles: bool = False
    ) -> None:
        """Save JSON metadata to a file.

        Args:
            output_path: Path to save the JSON file
            song_id: Optional song identifier
            title: Optional song title
            genre: Optional genre classification
            source: Source of the MIDI file
            indent: JSON indentation level (default: 2)
            use_detected_roles: If True, detect roles using heuristics instead of
                              using original MIDI track names (default: False)
        """
        json_string = self.to_json_string(song_id, title, genre, source, indent, use_detected_roles)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(json_string)


def midi_to_json(
    midi_path: str,
    song_id: Optional[str] = None,
    title: Optional[str] = None,
    genre: Optional[str] = None,
    source: str = "MIDI",
    use_detected_roles: bool = False
) -> Dict[str, Any]:
    """Convenience function to generate JSON from a MIDI file path.

    Args:
        midi_path: Path to the MIDI file
        song_id: Optional song identifier
        title: Optional song title
        genre: Optional genre classification
        source: Source of the MIDI file
        use_detected_roles: If True, detect roles using heuristics instead of
                          using original MIDI track names (default: False)

    Returns:
        Dictionary containing all metadata
    """
    generator = MidiJsonGenerator.from_file(midi_path)
    return generator.generate_json(song_id, title, genre, source, use_detected_roles)
