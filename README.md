# Book2Anki - Book to Anki Flashcards Generator

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Convert eBooks (PDF/EPUB/TXT) into Anki flashcards with definitions, pronunciations, and examples from Oxford Advanced Learner's Dictionary.


## Table of Contents
- [Features](#features)
- [Installation](#installation)
  - [Command Line](#prerequisites)
  - [GUI](#gui-installation) *(Coming Soon)*
- [Usage](#usage)
  - [Basic Usage](#basic-usage)
  - [Advanced Options](#advanced-options)


## Features ✨
- 📚 Extract words from PDF, EPUB, and TXT files
- 🏫 Fetch definitions, pronunciations, examples, and audio from Oxford Advanced Learner's Dictionary
- 🎴 Generate Anki decks with multiple card types (words, idioms, phrasal verbs)
- 🔍 Configurable word filtering:
  - Minimum word length
  - CEFR level exclusion
- 📁 Automatic caching of dictionary lookups
- 🌐 Automatic exclusion of previously extracted words

## Installation ⚙️

### Commmand Line
#### Prerequisites
- Python 3.9 or newer
- pip package manager
- Internet connection (for dictionary lookups)

1. **Clone repository**:
   ```
   git clone https://github.com/ahm4dmajid/book2anki
   cd book2anki
   ```
   
2. **Install dependencies** (Recommended: Create a virtual environment):
    ```
    pip install -r requirements.txt
    ```
### GUI (Graphical User Interface)


## Usage 🚀
### Basice Usage
```
python book2anki.py input_book.pdf --output my_anki_deck.apkg
```

### Advanced Options
```
python book2anki.py input_book.epub \
  --output advanced_cards.apkg \
  --min-length 5 \
  --exclude-up-to B2 \
  --max-concurrent 20
```


| Option |	Description | Default |
| ------ | ------------ | ------- |
| `-o, --output` |	Output file path |	`outputs/{input_book}.apkg` |
| `--min-length` |	Minimum word length to include |	3 |
| `--exclude-up-to` |	Exclude words up to CEFR level (A1 - C1)	| None |
| `--max-concurrent` | | 20 |


