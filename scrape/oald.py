# src/book2anki/scrape/oald.py
from bs4 import BeautifulSoup
import aiohttp
import asyncio
import aiofiles
import hashlib
from pathlib import Path
import json
from typing import Dict, List
from core.utils import AsyncRateLimiter

class WordNotFound(Exception):
    """Word not found in dictionary"""
    pass

class Word:
    BASE_URL = "https://www.oxfordlearnersdictionaries.com/definition/english/"
    MAX_ENTRIES = 5  
    CACHE_DIR = Path.home() / ".cache/book2anki/word_cache"
    CACHE_VERSION = "v1" 

    HEADWORD_CLASS = "headword"
    POS_CLASS = "pos"
    PHONS_BR_CLASS = "phons_br"
    PHONS_NA_CLASS = "phons_n_am"
    PHON_CLASS = "phon"
    SOUND_CLASS = "sound"
    SENSE_CLASS = "sense"
    DEF_CLASS = "def"
    EXAMPLE_CLASS = "x"
    IDIOMS_CLASS = "idioms"
    IDM_CLASS = "idm"
    PHRASAL_VERBS_CLASS = "phrasal_verb_links"
    PV_CLASS = "pv"
    
    RATE_LIMITER = AsyncRateLimiter(max_calls=100, period=1.0)  
    PV_SEMAPHORE = asyncio.Semaphore(10)

    def __init__(self, word: str):
        self.HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Accept-Language": "en-US,en;q=0.9"
        }
        self.word = word.strip().lower()
        self.entries = []

    async def initialize(self):
        """Load cached data or fetch fresh"""
        cache_path = await self._get_cache_path()
        if not await self._try_load_cached_data():
            async with aiohttp.ClientSession(headers=self.HEADERS) as session:
                await self.fetch_word(session)
                await self._cache_processed_data()

    async def _get_cache_path(self) -> Path:
        cache_key = f"{self.word}_{self.CACHE_VERSION}"
        filename = hashlib.md5(cache_key.encode()).hexdigest() + ".json"
        return self.CACHE_DIR / filename

    async def _try_load_cached_data(self) -> bool:
        cache_path = await self._get_cache_path()
        if not cache_path.exists():
            return False
        try:
            async with aiofiles.open(cache_path, "r") as f:
                self.entries = json.loads(await f.read())
                return True
        except Exception as e:
            print(f"Cache load failed: {str(e)}")
            return False

    async def _cache_processed_data(self):
        cache_path = await self._get_cache_path()
        try:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(cache_path, "w", encoding="utf-8") as f:
                await f.write(json.dumps(self.entries, ensure_ascii=False))
        except Exception as e:
            print(f"Cache save failed: {str(e)}")

    async def fetch_word(self, session: aiohttp.ClientSession):
        """Main fetch method with proper session handling"""
        tasks = [self._fetch_variation(session, f"{self.BASE_URL}{self.word}_{i}") 
                for i in range(1, self.MAX_ENTRIES+1)]
        results = await asyncio.gather(*tasks)
        
        process_tasks = []
        for soup in results:
            if self._is_valid_entry(soup):
                process_tasks.append(self._process_entry(soup, session))
        
        self.entries = await asyncio.gather(*process_tasks)

        if not self.entries:
            raise WordNotFound(f"Word '{self.word}' not found")

    async def _fetch_variation(self, session: aiohttp.ClientSession, url: str):
        """Fetch individual variation with rate limiting"""
        await self.RATE_LIMITER.wait()
        try:
            async with session.get(url, allow_redirects=True) as response:
                if response.status == 200:
                    return BeautifulSoup(await response.text(), 'lxml')
                return None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None

    async def get_phrasal_verbs(self, soup: BeautifulSoup, session: aiohttp.ClientSession):
        """Fetch phrasal verbs with proper URL resolution"""
        section = soup.find("aside", class_=self.PHRASAL_VERBS_CLASS)
        if not section:
            return []

        pv_links = {}
        for li in section.find_all("li", class_="li"):
            if a_tag := li.find("a", class_="Ref"):
                verb = a_tag.find("span", class_="xh")
                href = a_tag.get("href")
                if verb and href:
                    full_url = href 
                    pv_links[verb.text.strip()] = full_url

        tasks = [self._fetch_pv_data(session, verb, url) for verb, url in pv_links.items()]
        results = await asyncio.gather(*tasks)
        
        return [{"phrasal_verb": verb, "senses": data} for verb, data in results if data]

    async def _fetch_pv_data(self, session: aiohttp.ClientSession, verb: str, url: str):
        async with self.PV_SEMAPHORE:
            try:
                async with session.get(url) as response:
                    response.raise_for_status()
                    soup = BeautifulSoup(await response.text(), 'lxml')
                    return (verb, self._parse_pv_page(soup))
            except Exception as e:
                print(f"Failed to fetch phrasal verb {verb}: {str(e)}")
                return (verb, None)

    def _parse_pv_page(self, soup: BeautifulSoup):
        senses = soup.find_all("li", class_=self.SENSE_CLASS)
        return [self._parse_pv_sense(sense) for sense in senses]

    def _parse_pv_sense(self, sense: BeautifulSoup):
        definition = sense.find("span", class_=self.DEF_CLASS)
        examples = sense.find_all("span", class_=self.EXAMPLE_CLASS)
        return {
            "definition": definition.text.strip() if definition else "",
            "examples": [ex.text.strip() for ex in examples],
            "level": self._extract_cefr_level(sense)
        }

    def _is_valid_entry(self, soup: BeautifulSoup) -> bool:
        return bool(
            soup and
            soup.find("h1", class_=self.HEADWORD_CLASS) and
            soup.find("span", class_=self.POS_CLASS)
        )
    
    def get_headword(self, soup: BeautifulSoup):
        headword = soup.find("h1", class_=self.HEADWORD_CLASS)
        return headword.text.strip() if headword else None

    def get_part_of_speech(self, soup):
        pos = soup.find("span", class_=self.POS_CLASS)
        return pos.text.strip() if pos else None

    def get_pronunciation(self, soup, region_class):
        pron = soup.find("div", class_=region_class)
        if not pron:
            return {"ipa": "", "audio": ""}
        ipa = pron.find("span", class_=self.PHON_CLASS)
        audio = pron.find("div", class_=self.SOUND_CLASS)
        return {
            "ipa": ipa.text.strip() if ipa else "",
            "audio": audio["data-src-mp3"] if audio and "data-src-mp3" in audio.attrs else "",
        }

    def get_pronunciations(self, soup):
        return {
            "uk": self.get_pronunciation(soup, self.PHONS_BR_CLASS),
            "us": self.get_pronunciation(soup, self.PHONS_NA_CLASS),
        }

    def get_meanings(self, soup):
        senses_container = soup.find("ol")
        if not senses_container:
            return []
        return [self._parse_sense(sense) for sense in senses_container.find_all("li", class_=self.SENSE_CLASS)]

    def _parse_sense(self, sense):
        return {
            "definition": sense.find("span", class_=self.DEF_CLASS).text.strip() if sense.find("span", class_=self.DEF_CLASS) else "",
            "examples": [ex.text.strip() for ex in sense.find_all("span", class_=self.EXAMPLE_CLASS)],
            "level": self._extract_cefr_level(sense)
        }

    def _extract_cefr_level(self, sense_element):
        symbols_div = sense_element.find("div", class_="symbols")
        if not symbols_div:
            return ""
        level_span = symbols_div.find("span", class_=lambda x: x and x.startswith("ox3ksym_"))
        return level_span["class"][-1].split("_")[-1].upper() if level_span else ""

    def get_idioms(self, soup):
        idioms_section = soup.find("div", class_=self.IDIOMS_CLASS)
        if not idioms_section:
            return []
        return [self._parse_idiom(idiom) for idiom in idioms_section.find_all("span", class_=self.IDM_CLASS)]

    def _parse_idiom(self, idiom):
        idiom_text = idiom.text.strip()
        definition_section = idiom.find_next("ol", class_="sense_single")
        def_text = definition_section.find("span", class_=self.DEF_CLASS)
        return {
            "idiom": idiom_text,
            "definition": def_text.text.strip(), #[def_text.text.strip() for def_text in definition_section.find_all("span", class_=self.DEF_CLASS)] if definition_section else [],
            "examples": [ex.text.strip() for ex in definition_section.find_all("span", class_=self.EXAMPLE_CLASS)] if definition_section else []
        }
    
    async def _process_entry(self, soup: BeautifulSoup, session: aiohttp.ClientSession) -> Dict:
        try:
            return {
                "headword": self.get_headword(soup),
                "part_of_speech": self.get_part_of_speech(soup),
                "pronunciations": self.get_pronunciations(soup),
                "meanings": self.get_meanings(soup),
                "idioms": self.get_idioms(soup),
                "phrasal_verbs": await self.get_phrasal_verbs(soup, session)
            }
        except Exception as e:
            # print(f"Error processing entry: {str(e)}")
            return {}

    def get_word_info(self) -> list:
        return self.entries

