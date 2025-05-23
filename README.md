# Book2Anki - Book to Anki Flashcards Generator

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![Screenshot](/assets/screenshot.png)

Convert eBooks (PDF/EPUB/TXT) into Anki flashcards with definitions, pronunciations, and examples from Oxford Advanced Learner's Dictionary.


## Table of Contents
- [Features](#features-)
- [Installation](#installation)
  - [Command Line](#command-line)
  - [GUI](#gui-graphical-user-interface)
    - [Windows Installer](#windows-installer)
    - [Linux Installer](#linux-installer) 
- [Usage](#usage-)
  - [Basic Usage](#basic-usage)
  - [Advanced Options](#advanced-options)
- [Error Reporting and Suggestions](#error-reporting-and-suggestions-)


## Features
-  Extract words from PDF, EPUB, and TXT files
-  Fetch definitions, pronunciations, examples, and audio from Oxford Advanced Learner's Dictionary
-  Generate Anki decks with multiple card types (words, idioms, phrasal verbs)
-  Configurable word filtering:
   - Minimum word length
   - CEFR level exclusion
-  Automatic caching of dictionary lookups
-  Automatic exclusion of previously extracted words
-  Customizable deck style (edit: [shared_style.css](/config/templates/shared_style.css))

> [!NOTE]
> This program generates all forms of a word, not just the exact word found in the book. This means that different forms (e.g., verb, noun, etc.) will also be included.
> Additionally, the *Words* deck is the most important one, as it covers essential vocabulary. The *Idioms* and *Phrasal Verbs* decks are optional and can be used based on your learning preferences.



## Installation

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
1. Get your package from [Download](https://github.com/ahm4dmajid/book2anki/releases/) section
2. Run the installer and follow the on-screen instructions.

> [!WARNING]
> Windows may flag the installer as a virus. This is a false positive caused by heuristic analysis. The installer is safe to use.

#### Linux Installer
*(comming soon)*


## Usage
### Basic Usage
```
python book2anki.py input_book.pdf --output my_anki_deck
```

### Advanced Options
```
python book2anki.py input_book.epub \
  --output deck_name \
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

## Error Reporting and Suggestions
If you encounter any issues or have suggestions for improvement, please:

1. Open an issue on GitHub Issues.
2. Email me at a.maged@proton.me

Your feedback is highly appreciated! 


