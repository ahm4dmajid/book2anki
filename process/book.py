# src/book2anki/process/book.py
import os
import fitz
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from textblob import Word, TextBlob
from tqdm import tqdm
from pathlib import Path
from typing import ClassVar, List, Set, Optional

class BookProcessor:
    CEFR_ORDER: ClassVar[List[str]] = ['A1', 'A2', 'B1', 'B2', 'C1']
    
    def __init__(self) -> None:
        # Path configuration
        self.config_dir: Path = Path(__file__).parent.parent / 'config'
        self.stopwords_file: Path = self.config_dir / 'stopwords.txt'
        self.known_words_file: Path = self.config_dir / 'known_words.txt'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.default_stopwords: Set[str] = self._load_stopwords()
        self.known_words: Set[str] = self._load_known_words()

        # Add CEFR directory path
        self.cefr_dir: Path = self.config_dir / 'cefr'
        self.cefr_dir.mkdir(parents=True, exist_ok=True)

        # Add names file path
        self.names_file: Path = self.config_dir / 'names.txt'
        self.names: Set[str] = self._load_names()

    def extract_words(
        self,
        file_path: str,
        lemmatize: bool = False,
        min_length: int = 3,
        exclude_up_to: Optional[str] = None,
        exclude_names: bool = False
    ) -> List[str]:
        """Extract words from text using regex pattern"""
        text = self.process_book(file_path)
        all_words: List[str] = TextBlob(text).words
        # text = self._normalize_apostrophes(text)
        seen: Set[str] = set()
        words: List[str] = []

        excluded_words = self.default_stopwords.copy()
        excluded_words.update(self.known_words)
        if exclude_up_to:
            exclude_up_to = exclude_up_to.upper()
            if exclude_up_to not in self.CEFR_ORDER:
                raise ValueError(f"Invalid CEFR level: {exclude_up_to}. Use one of {self.CEFR_ORDER}")

            cutoff_index = self.CEFR_ORDER.index(exclude_up_to)
            levels_to_exclude = self.CEFR_ORDER[:cutoff_index + 1]
            excluded_words.update(self._load_cefr_words(levels_to_exclude))

        if exclude_names:
            excluded_words.update(self.names)
            
        for word in tqdm(all_words, desc="Extracting words"):
            lemma = self._lemmatize_word(word) if lemmatize else word.lower()
            
            if (not lemma.isalpha() or
                lemma in excluded_words or
                lemma in seen or
                len(lemma) < min_length):
                continue
            
            seen.add(lemma)
            words.append(lemma)
        return (words, len(all_words))

    def process_book(self, file_path: str) -> str:
        """Main method to process different book formats"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            return self._process_pdf(file_path)
        elif ext == '.epub':
            return self._process_epub(file_path)
        elif ext == '.txt':
            return self._process_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _process_pdf(self, path: str) -> str:
        """Process PDF files using PyMuPDF"""
        text: List[str] = []
        with fitz.open(path) as doc:
            for page in doc:
                text.append(page.get_text())
        return "\n".join(text)

    def _process_epub(self, path: str) -> str:
        """Process EPUB files using ebooklib and BeautifulSoup"""
        book = epub.read_epub(path, {"ignore_ncx": True})
        text: List[str] = []
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text.append(soup.get_text('\n', strip=True))
        
        return "\n".join(text)

    def _process_txt(self, path: str) -> str:
        """Process plain text files"""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
        
    def _load_stopwords(self) -> Set[str]:
        """Load stopwords from config file"""
        stopwords: Set[str] = set()
        if self.stopwords_file.exists():
            with open(self.stopwords_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word:
                        stopwords.add(word)
        return stopwords

    def _load_known_words(self) -> Set[str]:
        """Load known words from config file"""
        known_words: Set[str] = set()
        if self.known_words_file.exists():
            with open(self.known_words_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word:
                        known_words.add(word)
        return known_words

    def _load_names(self) -> Set[str]:
        """Load names from names.txt file"""
        names: Set[str] = set()
        if self.names_file.exists():
            with open(self.names_file, 'r', encoding='utf-8') as f:
                for line in f:
                    name = line.strip().lower()
                    if name:
                        names.add(name)
        return names

    def _load_cefr_words(self, levels: List[str]) -> Set[str]:
        """Load words from specified CEFR level files"""
        cefr_words: Set[str] = set()
        for level in levels:
            level_file = self.cefr_dir / f"{level}.txt"
            if level_file.exists():
                with open(level_file, 'r', encoding='utf-8') as f:
                    cefr_words.update(line.strip().lower() for line in f if line.strip())
        return cefr_words

    def _lemmatize_word(self, word: str) -> str:
        """Enhanced lemmatization with POS priority"""
        word = word.strip().lower()
        w = Word(word)
        pos_order = ['v', 'a', 'r']

        for pos_code in pos_order:
            lemma = w.lemmatize(pos_code)
            if lemma != word:
                return lemma
        
        # Fallback to default noun if no changes
        return w.lemmatize()
