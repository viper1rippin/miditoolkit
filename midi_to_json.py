#!/usr/bin/env python3
"""Command-line tool to convert MIDI files to structured JSON metadata.

This tool extracts comprehensive metadata from MIDI files including:
- Song information (tempo, key, time signature)
- Track details (instruments, roles)
- Latent tags (complexity, polyphony)
"""

import argparse
import sys
import os
from pathlib import Path

try:
    from miditoolkit import MidiJsonGenerator
except ImportError:
    # If running from source directory
    sys.path.insert(0, str(Path(__file__).parent))
    from miditoolkit import MidiJsonGenerator


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description='Convert MIDI files to structured JSON metadata',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate JSON and print to console
  python midi_to_json.py song.mid

  # Save to a file
  python midi_to_json.py song.mid -o output.json

  # Specify metadata
  python midi_to_json.py song.mid --id 0011 --title "My Song" --genre "Pop"

  # Process with custom source
  python midi_to_json.py song.mid --source "MuseScore" -o metadata.json
        """
    )

    parser.add_argument(
        'input',
        type=str,
        help='Path to the input MIDI file'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Path to save the JSON output (if not specified, prints to stdout)'
    )

    parser.add_argument(
        '--id', '--song-id',
        dest='song_id',
        type=str,
        default=None,
        help='Song ID (default: auto-generated from filename)'
    )

    parser.add_argument(
        '--title',
        type=str,
        default=None,
        help='Song title (default: filename without extension)'
    )

    parser.add_argument(
        '--genre',
        type=str,
        default='Unknown',
        help='Music genre (default: Unknown)'
    )

    parser.add_argument(
        '--source',
        type=str,
        default='MIDI',
        help='Source of the MIDI file (default: MIDI)'
    )

    parser.add_argument(
        '--indent',
        type=int,
        default=2,
        help='JSON indentation level (default: 2)'
    )

    parser.add_argument(
        '--compact',
        action='store_true',
        help='Output compact JSON (no indentation)'
    )

    parser.add_argument(
        '--detect-roles',
        action='store_true',
        help='Use heuristic role detection instead of original MIDI track names'
    )

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"Error: Input file '{args.input}' not found", file=sys.stderr)
        sys.exit(1)

    # Generate song_id from filename if not provided
    if args.song_id is None:
        filename = Path(args.input).stem
        # Try to extract numeric ID from filename, or use filename
        args.song_id = filename

    # Generate title from filename if not provided
    if args.title is None:
        args.title = Path(args.input).stem

    # Set indent to None for compact output
    indent = None if args.compact else args.indent

    try:
        # Load MIDI and generate JSON
        print(f"Loading MIDI file: {args.input}", file=sys.stderr)
        generator = MidiJsonGenerator.from_file(args.input)

        print("Generating JSON metadata...", file=sys.stderr)
        json_string = generator.to_json_string(
            song_id=args.song_id,
            title=args.title,
            genre=args.genre,
            source=args.source,
            indent=indent,
            use_detected_roles=args.detect_roles
        )

        # Output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_string)
            print(f"JSON saved to: {args.output}", file=sys.stderr)
        else:
            print(json_string)

        print("Done!", file=sys.stderr)

    except Exception as e:
        print(f"Error processing MIDI file: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
