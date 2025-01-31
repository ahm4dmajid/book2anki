# src/book2anki/generate/anki.py
from pathlib import Path
import genanki
import hashlib
import aiohttp
import aiofiles
import asyncio
from tqdm.asyncio import tqdm_asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass

from core.utils import AsyncRateLimiter  
from scrape.oald import Word, WordNotFound

# ---------- Template Configuration ----------
@dataclass
class TemplateConfig:
    name: str
    model_id: int
    fields: List[str]
    front_template: str
    back_template: str
    css_file: str

WORD_MODEL = TemplateConfig(
    name="Words Model",
    model_id=1892270111,
    fields=['Word', 'PartOfSpeech', 'Meanings', 'US_IPA', 'US_Audio'],
    front_template='words_front.html',
    back_template='words_back.html',
    css_file='shared_style.css'
)

IDIOM_MODEL = TemplateConfig(
    name="Idioms Model",
    model_id=1892270112,
    fields=['Idiom', 'Definition', 'Examples'],
    front_template='idioms_front.html',
    back_template='idioms_back.html',
    css_file='shared_style.css'
)

PHRASAL_MODEL = TemplateConfig(
    name="Phrasal Verbs Model",
    model_id=1892270113,
    fields=['Verb', 'Definitions'],
    front_template='phrasal_front.html',
    back_template='phrasal_back.html',
    css_file='shared_style.css'
)

# ---------- Template Loader ----------
class TemplateLoader:
    def __init__(self, template_dir: Path = Path("config/templates")):
        self.template_dir = template_dir
        
    def _read_file(self, path: str) -> str:
        full_path = self.template_dir / path
        if not full_path.exists():
            raise FileNotFoundError(f"Template file {full_path} not found")
        return full_path.read_text(encoding='utf-8')

    def load_model(self, config: TemplateConfig) -> genanki.Model:
        return genanki.Model(
            model_id=config.model_id,
            name=config.name,
            fields=[{'name': field} for field in config.fields],
            templates=[{
                'name': 'Card 1',
                'qfmt': self._read_file(config.front_template),
                'afmt': self._read_file(config.back_template),
            }],
            css=self._read_file(config.css_file)
        )

    def load_all_models(self) -> Dict[str, genanki.Model]:
        return {
            'words': self.load_model(WORD_MODEL),
            'idioms': self.load_model(IDIOM_MODEL),
            'phrasal': self.load_model(PHRASAL_MODEL)
        }

# ---------- Media Downloader ----------
class MediaDownloader:    
    def __init__(self, cache_dir: Path = Path.home() / ".cache/book2anki/media_cache", max_concurrent: int = 10):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.url_to_filename = {}
        self.session = None
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiter = AsyncRateLimiter(20, 1.0)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Accept-Language": "en-US,en;q=0.9"
        }

    async def download_audio(self, url: str) -> Optional[str]:
        if not url:
            return None
            
        if url in self.url_to_filename:
            return self.url_to_filename[url]

        async with self.semaphore:
            for attempt in range(3):
                try:
                    await self.rate_limiter.wait()
                    filename = hashlib.md5(url.encode()).hexdigest() + ".mp3"
                    filepath = self.cache_dir / filename

                    if not filepath.exists():
                        async with self.session.get(url, headers=self.headers, timeout=20) as response:
                            response.raise_for_status()
                            content = await response.read()
                            async with aiofiles.open(filepath, "wb") as f:
                                await f.write(content)

                    self.url_to_filename[url] = filename
                    return filename
                    
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    if attempt == 2:
                        print(f"Download failed after 3 attempts: {str(e)}")
                        return None
                    await asyncio.sleep(1 * (attempt + 1))

        return None

# ---------- Main Anki Generator ----------
class AnkiGenerator:
    def __init__(
            self,
            deck_name: str = "Ebook Deck",
            cache_dir: Path = Path.home() / ".cache/book2anki/media_cache",
            max_concurrent: int = 20
    ):
        self.main_deck, self.words_deck, self.idioms_deck, self.phrasal_deck = self._create_decks(deck_name)
        self.models = TemplateLoader().load_all_models()
        self.media_downloader = MediaDownloader(cache_dir, max_concurrent)
        self.media_files = []
        self.media_lock = asyncio.Lock()
        self.word_semaphore = asyncio.Semaphore(max_concurrent)
        self.valid_words = 0

    def _create_decks(self, base_name: str) -> tuple:
        main_id = self._generate_deck_id(base_name)
        return (
            genanki.Deck(main_id, base_name),
            genanki.Deck(self._generate_deck_id(f"{base_name}::Words"), f"{base_name}::Words"),
            genanki.Deck(self._generate_deck_id(f"{base_name}::Idioms"), f"{base_name}::Idioms"),
            genanki.Deck(self._generate_deck_id(f"{base_name}::Phrasal Verbs"), f"{base_name}::Phrasal Verbs")
        )

    def _generate_deck_id(self, name: str) -> int:
        return int(hashlib.md5(name.encode()).hexdigest()[:8], 16) % 10**10

    async def generate_deck(self, words: List[str], output_path: Path) -> None:
        async with aiohttp.ClientSession() as session:
            self.media_downloader.session = session

            tasks = [self._process_word(session, word) for word in words]
            results = await tqdm_asyncio.gather(*tasks, desc="Processing words")

            # Parallelize entry processing
            entry_tasks = []
            for entries in filter(None, results):
                for entry in entries:
                    entry_tasks.append(self._process_entry(entry))

            await tqdm_asyncio.gather(*entry_tasks, desc="Creating notes")

            media_set = set(self.media_files)
            media_list = list(media_set)

            # Split package creation
            package = genanki.Package([self.main_deck, self.words_deck, self.idioms_deck, self.phrasal_deck])
            package.media_files = media_list

            await self._write_package_in_chunks(package, output_path)
            return self.valid_words
        
    async def _write_package_in_chunks(self, package, output_path):
        """Workaround for genanki's blocking write operation"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            lambda: package.write_to_file(str(output_path))
        )
    
    async def _process_word(self, session: aiohttp.ClientSession, word_str: str) -> Optional[List[Dict]]:
        async with self.word_semaphore:
            try:
                word = Word(word_str)
                await word.initialize()
                self.valid_words += 1
                return word.entries
            except WordNotFound:
                # print(f"Word not found: {word_str}")
                return None
            except Exception as e:
                print(f"Error processing {word_str}: {e}")
                return None

    async def _process_entry(self, entry: Dict) -> None:
        await self._process_main_entry(entry)
        await self._process_idioms(entry.get('idioms', []))
        await self._process_phrasal_verbs(entry.get('phrasal_verbs', []))

    async def _process_main_entry(self, entry: Dict) -> None:
        try:
            us_pron = entry.get('pronunciations', {}).get('us', {})
            us_audio = await self._safe_download(us_pron.get('audio'))

            note_fields = [
                entry.get('headword', ''),
                entry.get('part_of_speech', ''),
                self._format_meanings(entry.get('meanings', [])),
                us_pron.get('ipa', ''),
                f"[sound:{us_audio}]" if us_audio else ""
            ]
            
            note = genanki.Note(model=self.models['words'], fields=note_fields)
            self.words_deck.add_note(note)
            
        except Exception as e:
            print(f"Error processing main entry: {str(e)}")

    async def _process_idioms(self, idioms: List[Dict]) -> None:
        for idiom in idioms:
            self.idioms_deck.add_note(genanki.Note(
                model=self.models['idioms'],
                fields=[
                    idiom['idiom'],
                    idiom['definition'],
                    self._format_idiom_examples(idiom['examples'])
                ]
            ))

    async def _process_phrasal_verbs(self, phrasal_verbs: List[Dict]) -> None:
        for pv in phrasal_verbs:
            self.phrasal_deck.add_note(genanki.Note(
                model=self.models['phrasal'],
                fields=[
                    pv['phrasal_verb'],
                    self._format_phrasal_definitions(pv['senses'])
                ]
            ))

    async def _safe_download(self, url: str) -> str:
        if not url:
            return ""
        try:
            filename = await self.media_downloader.download_audio(url)
            if filename:
                async with self.media_lock:
                    self.media_files.append(str(self.media_downloader.cache_dir / filename))
                return filename
            return ""
        except Exception as e:
            print(f"Audio download failed: {e}")
            return ""

    def _format_meanings(self, meanings: List[Dict]) -> str:
        html = []
        for idx, meaning in enumerate(meanings, 1):
            definition = meaning.get('definition', '')
            examples = meaning.get('examples', [])
            level = meaning.get('level', '')
            
            examples_html = "".join(
                f'<li class="example">{ex}</li>' 
                for ex in examples
            ) if examples else ""
            
            html.append(f"""
                <div class="meaning-container">
                    <div class="meaning-header">
                        <span class="meaning-text definition-text">{definition}</span>
                    </div>
                    {f'<ul class="examples-list">{examples_html}</ul>' if examples else ''}
                </div>
            """)
        return "".join(html)

    def _format_phrasal_definitions(self, senses: List[Dict]) -> str:
        html = []
        for idx, sense in enumerate(senses, 1):
            definition = sense.get('definition', '')
            examples = sense.get('examples', [])
            level = sense.get('level', '')
            
            examples_html = "".join(
                f'<li class="example">{ex}</li>' 
                for ex in examples
            ) if examples else ""
            
            html.append(f"""
                <div class="meaning-container">
                    <div class="sense-header">
                        <span class="sense-definition definition-text">{definition}</span>
                        {f'<span class="cefr">{level}</span>' if level else ''}
                    </div>
                    {f'<ul class="examples-list">{examples_html}</ul>' if examples else ''}
                </div>
            """)
        return "".join(html)

    def _format_idiom_examples(self, examples: List[str]) -> str:
        if not examples:
            return ""
        return "<ul class='examples-list'>" + "".join(f'<li class="example">{ex}</li>' for ex in examples) + "</ul>"

