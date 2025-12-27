"""Dictionary of Pali Proper Names (DPPN) using SuttaCentral data."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

from ..config import CACHE_PATH


@dataclass
class DPPNEntry:
    """A DPPN dictionary entry for a proper name."""

    word: str
    text: str  # HTML formatted text
    entry_type: Optional[str] = None  # person, place, etc.

    def format(self) -> str:
        """Format entry for display (clean HTML for terminal/markdown)."""
        # Extract entry type from HTML class if present
        type_match = re.search(r"class='(\w+)'", self.text)
        entry_type = type_match.group(1) if type_match else None

        # Clean HTML tags but preserve structure
        clean_text = self.text
        # Convert <p> to newlines
        clean_text = re.sub(r'<p>', '\n', clean_text)
        clean_text = re.sub(r'</p>', '', clean_text)
        # Convert <i> to markdown italic
        clean_text = re.sub(r'<i>([^<]+)</i>', r'*\1*', clean_text)
        # Convert <b> to markdown bold
        clean_text = re.sub(r'<b>([^<]+)</b>', r'**\1**', clean_text)
        # Extract sutta references
        clean_text = re.sub(
            r"<a class='ref' href='([^']+)'>([^<]+)</a>",
            r'[\2](\1)',
            clean_text
        )
        # Remove remaining HTML tags
        clean_text = re.sub(r'<[^>]+>', '', clean_text)
        # Clean up whitespace
        clean_text = re.sub(r'\n\s*\n', '\n\n', clean_text)
        clean_text = clean_text.strip()

        output = f"**{self.word}**"
        if entry_type:
            output += f" ({entry_type})"
        output += f"\n\n{clean_text}"
        return output

    def get_references(self) -> list[str]:
        """Extract sutta references from the entry."""
        # Find all sutta references in the HTML
        refs = re.findall(r"href='https://suttacentral\.net/([^/']+)", self.text)
        return list(set(refs))


class DPPNDictionary:
    """
    Dictionary of Pali Proper Names using SuttaCentral's DPPN data.

    The DPPN is fetched from SuttaCentral's GitHub repository and cached locally.
    It contains information about people, places, and other proper names
    mentioned in the Pali Canon.
    """

    # Raw GitHub URL for the DPPN dictionary
    GITHUB_URL = "https://raw.githubusercontent.com/suttacentral/sc-data/main/dictionaries/complex/en/pli2en_dppn.json"
    CACHE_FILE = "dppn_dictionary.json"

    def __init__(self, use_cache: bool = True):
        """
        Initialize the DPPN dictionary.

        Args:
            use_cache: Whether to cache the dictionary locally
        """
        self.use_cache = use_cache
        self.cache_path = CACHE_PATH / self.CACHE_FILE
        self._entries: dict[str, DPPNEntry] = {}
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
        """Parse JSON data into DPPNEntry objects."""
        for item in data:
            word = item.get("word", "").strip()
            if not word:
                continue

            # Extract entry type from HTML class
            text = item.get("text", "")
            type_match = re.search(r"class='(\w+)'", text)
            entry_type = type_match.group(1) if type_match else None

            entry = DPPNEntry(
                word=word,
                text=text,
                entry_type=entry_type,
            )
            # Store with lowercase key for case-insensitive lookup
            self._entries[word.lower()] = entry

    def load(self) -> bool:
        """
        Load the dictionary (from cache or GitHub).

        Returns:
            True if loaded successfully, False otherwise
        """
        if self._loaded:
            return True

        # Try cache first
        if self._load_from_cache():
            self._loaded = True
            return True

        # Fetch from GitHub
        try:
            response = requests.get(self.GITHUB_URL, timeout=60)
            response.raise_for_status()
            data = response.json()

            self._parse_entries(data)
            self._save_to_cache(data)
            self._loaded = True
            return True

        except requests.RequestException as e:
            print(f"Error fetching DPPN dictionary: {e}")
            return False

    def lookup(self, term: str) -> Optional[DPPNEntry]:
        """
        Look up a proper name.

        Args:
            term: The proper name to look up

        Returns:
            DPPNEntry if found, None otherwise
        """
        if not self._loaded:
            self.load()

        # Normalize term
        term_lower = term.lower().strip()

        # Direct lookup
        if term_lower in self._entries:
            return self._entries[term_lower]

        return None

    def search(self, pattern: str, limit: int = 20) -> list[DPPNEntry]:
        """
        Search for proper names matching a pattern.

        Args:
            pattern: String to search for (prefix or substring)
            limit: Maximum number of results

        Returns:
            List of matching DPPNEntry objects
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

    def search_by_type(
        self, entry_type: str, limit: int = 50
    ) -> list[DPPNEntry]:
        """
        Search for entries by type (person, place, etc.).

        Args:
            entry_type: The type to search for
            limit: Maximum number of results

        Returns:
            List of matching DPPNEntry objects
        """
        if not self._loaded:
            self.load()

        results = []
        for entry in self._entries.values():
            if entry.entry_type == entry_type:
                results.append(entry)
                if len(results) >= limit:
                    break

        return results

    def get_entry_count(self) -> int:
        """Get the number of dictionary entries."""
        if not self._loaded:
            self.load()
        return len(self._entries)

    def get_types(self) -> dict[str, int]:
        """Get counts of each entry type."""
        if not self._loaded:
            self.load()

        type_counts: dict[str, int] = {}
        for entry in self._entries.values():
            t = entry.entry_type or "unknown"
            type_counts[t] = type_counts.get(t, 0) + 1
        return type_counts

    def is_loaded(self) -> bool:
        """Check if the dictionary is loaded."""
        return self._loaded
