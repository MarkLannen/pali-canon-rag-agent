"""Pali text search across cached suttas."""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from ..config import CACHE_PATH


@dataclass
class PaliMatch:
    """A match of a Pali term in a sutta."""

    sutta_uid: str
    segment_id: str
    pali_text: str
    english_text: str
    match_term: str
    match_count: int  # Number of times the term appears in this segment


@dataclass
class PaliSearchResult:
    """Result of a Pali term search."""

    term: str
    total_occurrences: int
    sutta_count: int
    matches: list[PaliMatch]

    def format_summary(self) -> str:
        """Format a summary of the search results."""
        return (
            f"**{self.term}** appears {self.total_occurrences} time(s) "
            f"across {self.sutta_count} sutta(s)"
        )

    def format_by_sutta(self) -> str:
        """Format results grouped by sutta."""
        output = self.format_summary() + "\n\n"

        # Group by sutta
        by_sutta: dict[str, list[PaliMatch]] = {}
        for match in self.matches:
            if match.sutta_uid not in by_sutta:
                by_sutta[match.sutta_uid] = []
            by_sutta[match.sutta_uid].append(match)

        for sutta_uid, matches in sorted(by_sutta.items()):
            count = sum(m.match_count for m in matches)
            output += f"**{sutta_uid}** ({count} occurrence{'s' if count != 1 else ''})\n"

        return output


class PaliTextSearch:
    """
    Search for Pali terms across cached sutta texts.

    This searches the raw Pali root text from cached SuttaCentral data,
    allowing researchers to find occurrences of specific Pali terms.
    """

    def __init__(self, cache_dir: Path = None):
        """
        Initialize the Pali text search.

        Args:
            cache_dir: Directory containing cached sutta JSON files
        """
        self.cache_dir = cache_dir or (CACHE_PATH / "suttas")

    def _iter_cached_suttas(self) -> Iterator[tuple[Path, dict]]:
        """Iterate over all cached sutta files."""
        if not self.cache_dir.exists():
            return

        for json_file in sorted(self.cache_dir.glob("*.json")):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    yield json_file, data
            except (json.JSONDecodeError, IOError):
                continue

    def search(
        self,
        term: str,
        case_sensitive: bool = False,
        whole_word: bool = False,
        limit: int = 100,
    ) -> PaliSearchResult:
        """
        Search for a Pali term across all cached suttas.

        Args:
            term: The Pali term to search for
            case_sensitive: Whether to match case
            whole_word: Whether to match whole words only
            limit: Maximum number of segment matches to return

        Returns:
            PaliSearchResult with matches and counts
        """
        matches = []
        total_occurrences = 0
        suttas_with_matches = set()

        # Build regex pattern
        flags = 0 if case_sensitive else re.IGNORECASE
        if whole_word:
            pattern = re.compile(rf'\b{re.escape(term)}\b', flags)
        else:
            pattern = re.compile(re.escape(term), flags)

        for _, sutta_data in self._iter_cached_suttas():
            root_text = sutta_data.get("root_text", {})
            translation_text = sutta_data.get("translation_text", {})

            if not root_text:
                continue

            # Get sutta UID from first segment
            first_key = next(iter(root_text.keys()), "")
            sutta_uid = first_key.split(":")[0] if ":" in first_key else "unknown"

            sutta_match_count = 0

            for seg_id, pali_text in root_text.items():
                if not pali_text:
                    continue

                # Find all matches in this segment
                segment_matches = pattern.findall(pali_text)
                if segment_matches:
                    match_count = len(segment_matches)
                    total_occurrences += match_count
                    sutta_match_count += match_count

                    if len(matches) < limit:
                        english_text = translation_text.get(seg_id, "")
                        matches.append(PaliMatch(
                            sutta_uid=sutta_uid,
                            segment_id=seg_id,
                            pali_text=pali_text,
                            english_text=english_text,
                            match_term=segment_matches[0],  # First match form
                            match_count=match_count,
                        ))

            if sutta_match_count > 0:
                suttas_with_matches.add(sutta_uid)

        return PaliSearchResult(
            term=term,
            total_occurrences=total_occurrences,
            sutta_count=len(suttas_with_matches),
            matches=matches,
        )

    def count_occurrences(self, term: str, case_sensitive: bool = False) -> dict[str, int]:
        """
        Count occurrences of a term by sutta.

        Args:
            term: The Pali term to count
            case_sensitive: Whether to match case

        Returns:
            Dictionary mapping sutta_uid to occurrence count
        """
        result = self.search(term, case_sensitive=case_sensitive, limit=10000)

        counts: dict[str, int] = {}
        for match in result.matches:
            if match.sutta_uid not in counts:
                counts[match.sutta_uid] = 0
            counts[match.sutta_uid] += match.match_count

        return counts

    def get_cached_sutta_count(self) -> int:
        """Get the number of cached suttas available for search."""
        count = 0
        for _ in self._iter_cached_suttas():
            count += 1
        return count
