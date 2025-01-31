import asyncio
import sys
from pathlib import Path
import argparse
from typing import List

from process.book import BookProcessor
from generate.anki import AnkiGenerator

DEFAULT_MIN_LENGTH = 3
DEFAULT_MAX_CONCURRENT = 20

def main() -> None:
    try:
        args = parse_args()
        validate_input(args.input)

        output_path = handle_output_path(args)

        processor = BookProcessor()
        words, valid_words = processor.extract_words(
            args.input,
            lemmatize=True,
            exclude_names=True,
            min_length=args.min_length,
            exclude_up_to=args.exclude_up_to
        )

        if not valid_words:
            sys.exit("\nNo valid words found in input file")

        generator = AnkiGenerator(
            deck_name=output_path.stem,
            max_concurrent=args.max_concurrent
        )

        valid_processed_words = asyncio.run(generator.generate_deck(words, output_path))
        if not valid_processed_words or not words:
            sys.exit("\nAll words are already known! Yay!")

        update_known_words(words)

        print(f"\nDeck generated successfully: {output_path.resolve()}")
        
    except KeyboardInterrupt:
        sys.exit("\n\nOperation aborted by user")
    except Exception as e:
        sys.exit(f"Error: {str(e)}")

def validate_input(input_path: Path) -> None:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file {input_path} not found")
    if input_path.stat().st_size == 0:
        raise ValueError("Input file is empty")
        
def parse_args():
    parser = argparse.ArgumentParser(
        description='Generate Anki decks from word lists',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        'input',
        type=Path,
        help='Input text file with one word per line'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=Path,
        help='Output file name (without extension)',
        default=None
    )
    
    parser.add_argument(
        '--exclude-up-to',
        choices=BookProcessor.CEFR_ORDER,
        help='Exclude entries with levels up to this',
        default=None
    )
    
    parser.add_argument(
        '--min-length',
        type=int,
        help='Minimum length of words to include',
        default=DEFAULT_MIN_LENGTH
    )
    
    parser.add_argument(
        '--max-concurrent',
        type=int,
        help='Maximum concurrent downloads',
        default=DEFAULT_MAX_CONCURRENT
    )
    
    args = parser.parse_args()
    if args.min_length < 1:
        parser.error("--min-length must be at least 1")

    if args.max_concurrent < 1:
        parser.error("--max-concurrent must be at least 1")
    return args

def handle_output_path(args) -> Path:
    if args.output:
        # Check if output is just a filename (no parent directories)
        if args.output.parent == Path('.'):
            # Use outputs directory
            outputs_dir = Path('outputs')
            outputs_dir.mkdir(parents=True, exist_ok=True)
            output_path = outputs_dir / args.output.name
        else:
            output_path = args.output

        # Add extension and ensure parent directories exist
        output_path = output_path.with_suffix('.apkg')
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        # Default to outputs directory
        outputs_dir = Path('outputs')
        outputs_dir.mkdir(parents=True, exist_ok=True)
        output_path = outputs_dir / f"{args.input.stem}.apkg"

    return output_path

def update_known_words(new_words: List[str]):
    try:
        config_dir = Path('config')
        config_dir.mkdir(exist_ok=True)
        known_path = config_dir / 'known_words.txt'
        
        existing = set()
        if known_path.exists():
            existing = set(known_path.read_text(encoding='utf-8').splitlines())
            
        new_unique = set(new_words) - existing
        if new_unique:
            with known_path.open('a', encoding='utf-8') as f:
                f.write('\n'.join(new_unique) + '\n')
    except Exception as e:
        print(f"Warning: Could not update known words: {str(e)}")
    

if __name__ == '__main__':
    main()
