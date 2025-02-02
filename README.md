# Book2Anki - Book to Anki Flashcards Generator

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![Screenshot](https://private-user-images.githubusercontent.com/175677947/408862996-c6a1bcdf-a352-4379-a761-85be94e713c6.png?jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3Mzg0OTY0MzgsIm5iZiI6MTczODQ5NjEzOCwicGF0aCI6Ii8xNzU2Nzc5NDcvNDA4ODYyOTk2LWM2YTFiY2RmLWEzNTItNDM3OS1hNzYxLTg1YmU5NGU3MTNjNi5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUwMjAyJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MDIwMlQxMTM1MzhaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT02NjQyNzkzZWMwZWFjMmM2ZTY0ZmYxNDAzYmY1MWZkMTMwYWMyZWY0MWIzNzc3YmQ3NGY0N2Y3YjM4ZGRlOTExJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.VqYs-6a3dkfCf5d-Zos_SH8wQfJ84HsUA__GVXLTLIA)
Convert eBooks (PDF/EPUB/TXT) into Anki flashcards with definitions, pronunciations, and examples from Oxford Advanced Learner's Dictionary.


## Table of Contents
- [Features](#features-)
- [Installation](#installation)
  - [Command Line](#command-line)
  - [GUI](#gui-graphical-user-interface)
    - [Windows Installer](#windows-installer)
    - [Linux Installer](#linux-installer) *(comming soon)*
- [Usage](#usage-)
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

> [!NOTE]
> This program generates all forms of a word, not just the exact word found in the book. This means that different forms (e.g., verb, noun, etc.) will also be included.
> Additionally, the *Words* deck is the most important one, as it covers essential vocabulary. The *Idioms* and *Phrasal Verbs* decks are optional and can be used based on your learning preferences.

## Installation ⚙️

### Command Line
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
    python -m textblob.download_corpora
    ```
### GUI (Graphical User Interface)

#### Windows Installer
Get your package from [Download](https://github.com/ahm4dmajid/book2anki/releases/) section

#### Linux Installer


## Usage 🚀
### Basic Usage
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


