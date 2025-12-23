"""Pali-English dictionary using SuttaCentral data."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

from ..config import CACHE_PATH


@dataclass
class DictionaryEntry:
    """A Pali dictionary entry."""

    term: str
    definitions: list[str]
    grammar: Optional[str] = None
    pronunciation: Optional[str] = None
    cross_references: Optional[list[str]] = None

    def format(self) -> str:
        """Format entry for display."""
        output = f"**{self.term}**"
        if self.grammar:
            output += f" ({self.grammar})"
        output += "\n"
        for i, defn in enumerate(self.definitions, 1):
            # Clean HTML tags from definitions
            clean_defn = re.sub(r'<[^>]+>', '', defn)
            output += f"  {i}. {clean_defn}\n"
        return output


class PaliDictionary:
    """
    Pali-English dictionary using SuttaCentral's dictionary data.

    The dictionary is fetched from the SuttaCentral API and cached locally
    for fast lookups.
    """

    API_URL = "https://suttacentral.net/api/dictionaries/lookup?from=pli&to=en"
    CACHE_FILE = "pali_dictionary.json"

    def __init__(self, use_cache: bool = True):
        """
        Initialize the Pali dictionary.

        Args:
            use_cache: Whether to cache the dictionary locally
        """
        self.use_cache = use_cache
        self.cache_path = CACHE_PATH / self.CACHE_FILE
        self._entries: dict[str, DictionaryEntry] = {}
        self._loaded = False

    def _load_from_cache(self) -> bool:
        """Load dictionary from cache if available."""
        if not self.use_cache or not self.cache_path.exists():
            return False

        try:
            with open(self.cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._parse_entries(data)
                return True
        except (json.JSONDecodeError, IOError):
            return False

    def _save_to_cache(self, data: list[dict]) -> None:
        """Save dictionary data to cache."""
        if not self.use_cache:
            return

        CACHE_PATH.mkdir(parents=True, exist_ok=True)
        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    def _parse_entries(self, data: list[dict]) -> None:
        """Parse API response into DictionaryEntry objects."""
        for item in data:
            term = item.get("entry", "").lower()
            if not term:
                continue

            entry = DictionaryEntry(
                term=term,
                definitions=item.get("definition", []),
                grammar=item.get("grammar"),
                pronunciation=item.get("pronunciation"),
                cross_references=item.get("xr"),
            )
            self._entries[term] = entry

    def load(self) -> bool:
        """
        Load the dictionary (from cache or API).

        Returns:
            True if loaded successfully, False otherwise
        """
        if self._loaded:
            return True

        # Try cache first
        if self._load_from_cache():
            self._loaded = True
            return True

        # Fetch from API
        try:
            response = requests.get(self.API_URL, timeout=60)
            response.raise_for_status()
            data = response.json()

            self._parse_entries(data)
            self._save_to_cache(data)
            self._loaded = True
            return True

        except requests.RequestException as e:
            print(f"Error fetching dictionary: {e}")
            return False

    def lookup(self, term: str) -> Optional[DictionaryEntry]:
        """
        Look up a Pali term.

        Args:
            term: The Pali term to look up

        Returns:
            DictionaryEntry if found, None otherwise
        """
        if not self._loaded:
            self.load()

        # Normalize term
        term = term.lower().strip()

        # Direct lookup
        if term in self._entries:
            return self._entries[term]

        # Try without diacritics variations
        # Common substitutions: ā->a, ī->i, ū->u, ṁ->m, ṅ->n, ñ->n, ṭ->t, ḍ->d, ṇ->n, ḷ->l
        return None

    def search(self, pattern: str, limit: int = 20) -> list[DictionaryEntry]:
        """
        Search for terms matching a pattern.

        Args:
            pattern: Regex pattern or prefix to search for
            limit: Maximum number of results

        Returns:
            List of matching DictionaryEntry objects
        """
        if not self._loaded:
            self.load()

        results = []
        pattern_lower = pattern.lower()

        # First try prefix match
        for term, entry in self._entries.items():
            if term.startswith(pattern_lower):
                results.append(entry)
                if len(results) >= limit:
                    break

        # If few results, try substring match
        if len(results) < limit:
            for term, entry in self._entries.items():
                if pattern_lower in term and entry not in results:
                    results.append(entry)
                    if len(results) >= limit:
                        break

        return results

    def get_entry_count(self) -> int:
        """Get the number of dictionary entries."""
        if not self._loaded:
            self.load()
        return len(self._entries)

    def is_loaded(self) -> bool:
        """Check if the dictionary is loaded."""
        return self._loaded
