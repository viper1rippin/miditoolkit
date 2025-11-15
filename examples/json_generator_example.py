#!/usr/bin/env python3
"""Example script demonstrating the MIDI to JSON metadata generator.

This script shows how to use the MidiJsonGenerator to extract
comprehensive metadata from MIDI files.
"""

from miditoolkit import MidiFile, MidiJsonGenerator, midi_to_json
import json


def example_1_basic_usage():
    """Example 1: Basic usage with convenience function."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)

    # Use the convenience function
    metadata = midi_to_json(
        "../tests/testcases/One_track_MIDIs/Maestro_1.mid",
        song_id="0001",
        title="Maestro Example",
        genre="Classical",
        source="MAESTRO Dataset"
    )

    print(json.dumps(metadata, indent=2))
    print()


def example_2_generator_class():
    """Example 2: Using the MidiJsonGenerator class directly."""
    print("=" * 60)
    print("Example 2: Using MidiJsonGenerator Class")
    print("=" * 60)

    # Load MIDI file
    midi_path = "../tests/testcases/One_track_MIDIs/Maestro_1.mid"

    # Create generator from file
    generator = MidiJsonGenerator.from_file(midi_path)

    # Or create from existing MidiFile object
    # midi = MidiFile(midi_path)
    # generator = MidiJsonGenerator(midi)

    # Generate metadata
    metadata = generator.generate_json(
        song_id="0002",
        title="Piano Solo",
        genre="Classical",
        source="Example"
    )

    print(f"Tempo: {metadata['tempo_bpm']} BPM")
    print(f"Key: {metadata['key']}")
    print(f"Time Signature: {metadata['time_signature']}")
    print(f"Number of tracks: {len(metadata['tracks'])}")
    print(f"Polyphony: {metadata['latent_tags']['polyphony']}")
    print()


def example_3_custom_analysis():
    """Example 3: Custom analysis using the generator methods."""
    print("=" * 60)
    print("Example 3: Custom Analysis")
    print("=" * 60)

    midi_path = "../tests/testcases/Multitrack_MIDIs/Funkytown.mid"
    generator = MidiJsonGenerator.from_file(midi_path)

    # Get individual components
    print(f"Tempo: {generator.get_tempo_bpm()} BPM")
    print(f"Key: {generator.get_key_signature()}")
    print(f"Time Signature: {generator.get_time_signature()}")
    print()

    # Analyze tracks
    print("Track Analysis:")
    tracks = generator.get_tracks_metadata()
    for track in tracks:
        print(f"  Lane {track['lane']}: {track['program_name']} ({track['role']})")
    print()

    # Get latent tags
    latent = generator.get_latent_tags()
    print(f"Arrangement Complexity: {latent['arrangement_complexity']}")
    print(f"Layer Count: {latent['layer_count']}")
    print(f"Overall Polyphony: {latent['polyphony']}")
    print()


def example_4_save_to_file():
    """Example 4: Save JSON to file."""
    print("=" * 60)
    print("Example 4: Save to File")
    print("=" * 60)

    midi_path = "../tests/testcases/Multitrack_MIDIs/Funkytown.mid"
    generator = MidiJsonGenerator.from_file(midi_path)

    # Save as JSON file
    output_path = "/tmp/funkytown_metadata.json"
    generator.save_json(
        output_path,
        song_id="0011",
        title="Funkytown",
        genre="Disco / Pop",
        source="Example"
    )

    print(f"Metadata saved to: {output_path}")
    print()


def example_5_access_midi_object():
    """Example 5: Access underlying MIDI object for custom processing."""
    print("=" * 60)
    print("Example 5: Access Underlying MIDI Object")
    print("=" * 60)

    midi_path = "../tests/testcases/One_track_MIDIs/Maestro_1.mid"
    generator = MidiJsonGenerator.from_file(midi_path)

    # Access the underlying MidiFile object
    midi = generator.midi

    print(f"Ticks per beat: {midi.ticks_per_beat}")
    print(f"Max tick: {midi.max_tick}")
    print(f"Number of instruments: {len(midi.instruments)}")
    print(f"Number of tempo changes: {len(midi.tempo_changes)}")

    # Access individual instruments
    for i, inst in enumerate(midi.instruments):
        print(f"\nInstrument {i}:")
        print(f"  Program: {inst.program}")
        print(f"  Name: {inst.name}")
        print(f"  Is drum: {inst.is_drum}")
        print(f"  Number of notes: {len(inst.notes)}")

        if inst.notes:
            pitches = [note.pitch for note in inst.notes]
            print(f"  Pitch range: {min(pitches)} - {max(pitches)}")

    print()


def main():
    """Run all examples."""
    print("\n")
    print("#" * 60)
    print("# MIDI to JSON Metadata Generator Examples")
    print("#" * 60)
    print("\n")

    example_1_basic_usage()
    example_2_generator_class()
    example_3_custom_analysis()
    example_4_save_to_file()
    example_5_access_midi_object()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()
