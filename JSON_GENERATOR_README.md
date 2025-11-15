# MIDI to JSON Metadata Generator

A powerful tool for extracting comprehensive metadata from MIDI files and exporting it in a structured JSON format.

## Features

The JSON generator extracts the following metadata from MIDI files:

- **Basic Information**: Song ID, title, genre, source
- **Musical Properties**: Tempo (BPM), key signature, time signature
- **Track Details**:
  - Lane number (track index)
  - MIDI program number (0-127)
  - Instrument name (General MIDI mapping)
  - Track role (Melody, Harmony, Bass, Rhythm, Accompaniment)
- **Latent Tags**:
  - Arrangement complexity (low, medium, high)
  - Layer count (number of active tracks)
  - Polyphony (0-1 normalized, average simultaneous notes)

## Installation

The JSON generator is included in the miditoolkit package:

```bash
pip install -e .
```

## Usage

### Command-Line Interface

The easiest way to use the JSON generator is through the command-line tool:

```bash
# Basic usage - print JSON to console
python midi_to_json.py song.mid

# Save to file
python midi_to_json.py song.mid -o output.json

# Specify metadata
python midi_to_json.py song.mid \
  --id "0011" \
  --title "My Song" \
  --genre "Pop" \
  --source "MuseScore" \
  -o metadata.json

# Compact JSON (no indentation)
python midi_to_json.py song.mid --compact
```

#### Command-Line Options

- `input`: Path to the input MIDI file (required)
- `-o, --output`: Path to save the JSON output (optional, prints to stdout if not specified)
- `--id, --song-id`: Song ID (default: filename)
- `--title`: Song title (default: filename without extension)
- `--genre`: Music genre (default: "Unknown")
- `--source`: Source of the MIDI file (default: "MIDI")
- `--indent`: JSON indentation level (default: 2)
- `--compact`: Output compact JSON (no indentation)

### Python API

#### Method 1: Convenience Function

```python
from miditoolkit import midi_to_json

metadata = midi_to_json(
    "path/to/song.mid",
    song_id="0011",
    title="Cruel Angel's Thesis",
    genre="Anime / J-Pop",
    source="MuseScore"
)

print(metadata)
```

#### Method 2: Generator Class

```python
from miditoolkit import MidiJsonGenerator

# Create generator from file
generator = MidiJsonGenerator.from_file("path/to/song.mid")

# Generate metadata
metadata = generator.generate_json(
    song_id="0011",
    title="Cruel Angel's Thesis",
    genre="Anime / J-Pop",
    source="MuseScore"
)

# Or get as JSON string
json_string = generator.to_json_string(
    song_id="0011",
    title="Cruel Angel's Thesis",
    genre="Anime / J-Pop",
    source="MuseScore",
    indent=2
)

# Or save directly to file
generator.save_json(
    "output.json",
    song_id="0011",
    title="Cruel Angel's Thesis",
    genre="Anime / J-Pop",
    source="MuseScore"
)
```

#### Method 3: From Existing MidiFile Object

```python
from miditoolkit import MidiFile, MidiJsonGenerator

# Load MIDI file
midi = MidiFile("path/to/song.mid")

# Create generator from existing MidiFile
generator = MidiJsonGenerator(midi)

# Generate metadata
metadata = generator.generate_json(
    song_id="0011",
    title="Cruel Angel's Thesis"
)
```

### Custom Analysis

You can also use the generator's individual methods for custom analysis:

```python
from miditoolkit import MidiJsonGenerator

generator = MidiJsonGenerator.from_file("path/to/song.mid")

# Get individual components
tempo = generator.get_tempo_bpm()
key = generator.get_key_signature()
time_sig = generator.get_time_signature()

# Get track metadata
tracks = generator.get_tracks_metadata()
for track in tracks:
    print(f"Lane {track['lane']}: {track['program_name']} ({track['role']})")

# Get latent tags
latent = generator.get_latent_tags()
print(f"Complexity: {latent['arrangement_complexity']}")
print(f"Polyphony: {latent['polyphony']}")

# Access underlying MidiFile object
midi = generator.midi
print(f"Ticks per beat: {midi.ticks_per_beat}")
```

## Output Format

The generated JSON follows this structure:

```json
{
  "song_id": "0011",
  "title": "Cruel Angel's Thesis",
  "genre": "Anime / J-Pop",
  "tempo_bpm": 130,
  "key": "C Major",
  "time_signature": "4/4",
  "tracks": [
    {
      "lane": 0,
      "program_number": 0,
      "program_name": "Acoustic Grand Piano",
      "role": "Melody"
    },
    {
      "lane": 1,
      "program_number": 48,
      "program_name": "Strings Ensemble",
      "role": "Harmony"
    },
    {
      "lane": 2,
      "program_number": 24,
      "program_name": "Nylon Guitar",
      "role": "Accompaniment"
    }
  ],
  "latent_tags": {
    "arrangement_complexity": "medium",
    "layer_count": 3,
    "polyphony": 0.72
  },
  "source": "MuseScore"
}
```

## Track Role Detection

The generator automatically detects track roles based on several heuristics:

- **Rhythm**: Drum tracks (MIDI channel 10)
- **Bass**: Bass instruments (programs 32-39) or tracks with average pitch < 50
- **Melody**: High pitch range (avg > 60), wide pitch span (> 12 semitones), moderate note density
- **Harmony**: High polyphony (multiple simultaneous notes, indicating chords)
- **Accompaniment**: Everything else (supporting instruments)

## Latent Tags

### Arrangement Complexity

Determined by the number of active tracks and total notes:

- **Low**: ≤2 tracks or <100 notes
- **Medium**: ≤4 tracks or <500 notes
- **High**: >4 tracks or ≥500 notes

### Polyphony

Calculated as the average number of simultaneous notes across all non-drum tracks, normalized to 0-1 range (capped at 10 simultaneous notes).

## Examples

See `examples/json_generator_example.py` for comprehensive usage examples including:

1. Basic usage with convenience function
2. Using the MidiJsonGenerator class
3. Custom analysis with individual methods
4. Saving to file
5. Accessing the underlying MIDI object

Run the examples:

```bash
cd examples
python json_generator_example.py
```

## API Reference

### MidiJsonGenerator Class

#### Constructor

- `MidiJsonGenerator(midi_file: MidiFile)`: Create generator from MidiFile object
- `MidiJsonGenerator.from_file(filepath: str)`: Create generator by loading MIDI file

#### Methods

- `get_tempo_bpm() -> int`: Get primary tempo in BPM
- `get_key_signature() -> str`: Get key signature (e.g., "C Major", "Am")
- `get_time_signature() -> str`: Get time signature (e.g., "4/4")
- `get_tracks_metadata() -> List[Dict]`: Get metadata for all tracks
- `get_latent_tags() -> Dict`: Calculate latent tags
- `calculate_overall_polyphony() -> float`: Calculate normalized polyphony (0-1)
- `calculate_arrangement_complexity() -> str`: Determine complexity ("low", "medium", "high")
- `generate_json(...) -> Dict`: Generate complete metadata dictionary
- `to_json_string(...) -> str`: Generate formatted JSON string
- `save_json(output_path, ...) -> None`: Save JSON to file

### Convenience Function

```python
def midi_to_json(
    midi_path: str,
    song_id: Optional[str] = None,
    title: Optional[str] = None,
    genre: Optional[str] = None,
    source: str = "MIDI"
) -> Dict[str, Any]
```

## Technical Details

### General MIDI Mapping

The generator includes a complete General MIDI program number (0-127) to instrument name mapping. This ensures accurate instrument identification for all standard MIDI files.

### Note Analysis

- Polyphony is calculated by tracking note-on and note-off events over time
- Track roles are detected using pitch statistics, note density, and polyphony analysis
- All calculations handle edge cases (empty tracks, no tempo/key signature, etc.)

### Type Conversion

The generator automatically converts NumPy types to native Python types for JSON serialization, ensuring compatibility across all platforms.

## License

MIT License - Same as miditoolkit
