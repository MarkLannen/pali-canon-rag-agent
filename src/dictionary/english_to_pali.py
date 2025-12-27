"""English-to-Pali reverse dictionary built from SuttaCentral data."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..config import CACHE_PATH
from .pali_dictionary import PaliDictionary


@dataclass
class EnglishToPaliEntry:
    """An English word with its Pali equivalents."""

    english_word: str
    pali_terms: list[dict] = field(default_factory=list)
    # Each dict has: {term: str, definition: str, grammar: str|None}

    def format(self) -> str:
        """Format entry for display."""
        output = f"**{self.english_word}**\n\n"
        for i, item in enumerate(self.pali_terms, 1):
            term = item["term"]
            defn = item.get("definition", "")
            grammar = item.get("grammar", "")

            output += f"{i}. **{term}**"
            if grammar:
                output += f" ({grammar})"
            if defn:
                # Clean HTML and truncate long definitions
                clean_defn = re.sub(r'<[^>]+>', '', defn)
                if len(clean_defn) > 150:
                    clean_defn = clean_defn[:150] + "..."
                output += f"\n   {clean_defn}"
            output += "\n"
        return output


class EnglishToPaliDictionary:
    """
    English-to-Pali reverse dictionary.

    This dictionary is built by creating a reverse index from the
    Pali-English dictionary. It extracts key English words from
    definitions and maps them back to their Pali terms.
    """

    CACHE_FILE = "english_to_pali_index.json"

    def __init__(self, use_cache: bool = True):
        """
        Initialize the English-to-Pali dictionary.

        Args:
            use_cache: Whether to cache the reverse index locally
        """
        self.use_cache = use_cache
        self.cache_path = CACHE_PATH / self.CACHE_FILE
        self._index: dict[str, list[dict]] = {}
        self._loaded = False
        self._pali_dict = PaliDictionary(use_cache=use_cache)

    def _load_from_cache(self) -> bool:
        """Load reverse index from cache if available."""
        if not self.use_cache or not self.cache_path.exists():
            return False

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                self._index = json.load(f)
                return True
        except (json.JSONDecodeError, IOError):
            return False

    def _save_to_cache(self) -> None:
        """Save reverse index to cache."""
        if not self.use_cache:
            return

        CACHE_PATH.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, ensure_ascii=False)

    def _extract_english_words(self, definition: str) -> list[str]:
        """
        Extract meaningful English words from a definition.

        Args:
            definition: The definition text (may contain HTML)

        Returns:
            List of extracted English words
        """
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', ' ', definition)

        # Remove grammatical notation in brackets
        clean = re.sub(r'\[[^\]]+\]', '', clean)

        # Extract text in bold (usually the main translation)
        bold_matches = re.findall(r'\*\*([^*]+)\*\*', definition)
        bold_text = ' '.join(bold_matches)

        # Also extract from <b> tags
        b_matches = re.findall(r'<b>([^<]+)</b>', definition)
        bold_text += ' ' + ' '.join(b_matches)

        # Process the bold text first (these are the primary meanings)
        words = set()

        # Extract words from bold text
        for word in re.findall(r'\b[a-zA-Z]{3,}\b', bold_text.lower()):
            if not self._is_stopword(word):
                words.add(word)

        # Also extract from the full cleaned text, but be more selective
        for word in re.findall(r'\b[a-zA-Z]{4,}\b', clean.lower()):
            if not self._is_stopword(word):
                words.add(word)

        return list(words)

    def _is_stopword(self, word: str) -> bool:
        """Check if a word is a stopword (common word to ignore)."""
        stopwords = {
            # Common English words
            'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'this', 'that', 'these', 'those', 'it', 'its', 'with', 'from',
            'for', 'on', 'of', 'to', 'in', 'at', 'by', 'as', 'into', 'onto',
            'upon', 'about', 'after', 'before', 'between', 'through', 'during',
            'under', 'over', 'above', 'below', 'up', 'down', 'out', 'off',
            'away', 'back', 'here', 'there', 'where', 'when', 'how', 'why',
            'what', 'which', 'who', 'whom', 'whose', 'than', 'then', 'so',
            'very', 'just', 'only', 'also', 'even', 'still', 'already', 'yet',
            'now', 'always', 'never', 'often', 'sometimes', 'usually',
            'not', 'no', 'yes', 'all', 'any', 'some', 'each', 'every', 'both',
            'few', 'more', 'most', 'other', 'another', 'such', 'same',
            'one', 'two', 'three', 'four', 'five', 'first', 'second', 'third',
            # Grammar terms
            'noun', 'verb', 'adj', 'adv', 'prep', 'conj', 'pron', 'masc',
            'fem', 'neut', 'sing', 'plur', 'nom', 'acc', 'gen', 'dat', 'inst',
            'abl', 'loc', 'voc', 'pres', 'past', 'fut', 'perf', 'imper',
            'part', 'inf', 'ger', 'caus', 'pass', 'act', 'mid', 'opt',
            'indic', 'subj', 'cond', 'abs', 'stem', 'root', 'prefix', 'suffix',
            'lit', 'literally', 'see', 'also', 'comm', 'commentary',
            # Common Pali grammar abbreviations
            'pp', 'prp', 'fpp', 'ptp', 'nt', 'mfn',
        }
        return word in stopwords

    def _build_index(self) -> None:
        """Build the reverse index from the Pali-English dictionary."""
        # Ensure Pali dictionary is loaded
        if not self._pali_dict.load():
            return

        # Build reverse index
        for term, entry in self._pali_dict._entries.items():
            for definition in entry.definitions:
                words = self._extract_english_words(definition)
                for word in words:
                    if word not in self._index:
                        self._index[word] = []

                    # Add this Pali term as a match for the English word
                    self._index[word].append({
                        "term": entry.term,
                        "definition": definition,
                        "grammar": entry.grammar,
                    })

        # Sort entries by term for consistency
        for word in self._index:
            self._index[word] = sorted(
                self._index[word],
                key=lambda x: x["term"]
            )[:50]  # Limit to 50 Pali terms per English word

    def load(self) -> bool:
        """
        Load the dictionary (from cache or build from Pali dictionary).

        Returns:
            True if loaded successfully, False otherwise
        """
        if self._loaded:
            return True

        # Try cache first
        if self._load_from_cache():
            self._loaded = True
            return True

        # Build from Pali dictionary
        self._build_index()
        if self._index:
            self._save_to_cache()
            self._loaded = True
            return True

        return False

    def lookup(self, english_word: str) -> Optional[EnglishToPaliEntry]:
        """
        Look up an English word to find Pali equivalents.

        Args:
            english_word: The English word to look up

        Returns:
            EnglishToPaliEntry if found, None otherwise
        """
        if not self._loaded:
            self.load()

        word = english_word.lower().strip()

        if word in self._index:
            return EnglishToPaliEntry(
                english_word=word,
                pali_terms=self._index[word]
            )

        return None

    def search(self, pattern: str, limit: int = 20) -> list[EnglishToPaliEntry]:
        """
        Search for English words matching a pattern.

        Args:
            pattern: String to search for (prefix or substring)
            limit: Maximum number of results

        Returns:
            List of matching EnglishToPaliEntry objects
        """
        if not self._loaded:
            self.load()

        results = []
        pattern_lower = pattern.lower()

        # First try prefix match
        for word in sorted(self._index.keys()):
            if word.startswith(pattern_lower):
                results.append(EnglishToPaliEntry(
                    english_word=word,
                    pali_terms=self._index[word]
                ))
                if len(results) >= limit:
                    break

        # If few results, try substring match
        if len(results) < limit:
            for word in sorted(self._index.keys()):
                if pattern_lower in word:
                    entry = EnglishToPaliEntry(
                        english_word=word,
                        pali_terms=self._index[word]
                    )
                    if entry not in results:
                        results.append(entry)
                        if len(results) >= limit:
                            break

        return results

    def get_word_count(self) -> int:
        """Get the number of English words in the index."""
        if not self._loaded:
            self.load()
        return len(self._index)

    def is_loaded(self) -> bool:
        """Check if the dictionary is loaded."""
        return self._loaded
