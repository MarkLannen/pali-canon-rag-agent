# Sutta Pitaka AI Agent - Implementation Plan

## Current State (as of Dec 27, 2024)

### What's Working
- ChromaDB vector store with embeddings (**5,763 chunks from 4,050 suttas**)
- SuttaCentral API integration with **dynamic sutta discovery**
- **Full Sutta Pitaka ingestion support** (DN, MN, SN, AN, KN)
- **Resume capability** for interrupted ingestion
- Document processor for chunking suttas
- **Iterative AI Agent** with multi-pass search and gap analysis
- **Agent Memory** - persists learned insights in `agent_wisdom` collection
- **Pali Dictionary** - 142K entries from SuttaCentral API
- **English-to-Pali Dictionary** - reverse index with 36K English words
- **Dictionary of Pali Proper Names (DPPN)** - 1,367 entries (persons, places, things)
- **Pali Term Search** - search for Pali terms across cached suttas
- Streamlit UI with Chat, Search, and Pali Tools tabs
- **Enhanced Search Mode** - exhaustive search grouped by sutta (no LLM)
- Multi-model support (Ollama, Anthropic, Google, OpenAI)
- Dynamic retrieval: 5 chunks for local models, 20 for cloud models
- Progress indicators during research phases

### What Was Done (Dec 27)
1. **Phase 10: Additional Dictionaries** ✅
   - Created `src/dictionary/english_to_pali.py` - reverse index from Pali dictionary
   - Created `src/dictionary/dppn.py` - Dictionary of Pali Proper Names
   - Updated Pali Tools UI with 4 tabs: Term Search, Pali→English, English→Pali, DPPN
   - **36,502 English words** indexed for reverse lookup
   - **1,367 DPPN entries** (994 persons, 347 places, 26 things)

### What Was Done (Dec 24)
1. **Phase 1: Full Sutta Pitaka Ingestion** ✅
   - Created `src/ingestion/sutta_discovery.py` - dynamic sutta discovery via API
   - Created `src/ingestion/progress_tracker.py` - resume capability
   - Updated `src/config.py` with ALL_NIKAYAS, KN_COLLECTIONS, ALL_COLLECTIONS
   - Updated `src/ingestion/suttacentral.py` with discovery integration
   - Updated `ingest.py` with extended CLI (`--all`, `--kn`, `--dry-run`, `--no-resume`)
   - Fixed metadata size issue in `processor.py` (truncate long segment_ids)
   - **4,050 suttas ingested** → **5,763 chunks** in vector store:
     - DN: 34, MN: 152, SN: 1,819, AN: 1,408
     - KN: kp(9), dhp(26), ud(80), iti(112), snp(73), thag(264), thig(73)

2. **Phase 8: Enhanced Search Mode** ✅
   - Created `src/retrieval/sutta_search.py` - exhaustive search with grouping
   - Added "Search" tab to UI (between Chat and Pali Tools)
   - High top_k (200-500) retrieval without LLM synthesis
   - Results grouped by sutta with relevance scores and snippets
   - Configurable search depth via UI slider

### What Was Done (Dec 22)
1. **Phase 3 & 6: Iterative Agent with Memory** ✅
   - Created `src/agent/iterative_agent.py` with `SuttaPitakaAgent`
   - Created `src/agent/memory.py` with `AgentMemory` class
   - Multi-pass search with LLM-driven gap analysis
   - Persists synthesized answers in `agent_wisdom` ChromaDB collection
   - Recalls relevant prior research before new searches

2. **Phase 4: Analysis & Synthesis Prompts** ✅
   - Gap analysis prompt identifies missing information
   - Synthesis prompt constructs thematic, well-cited responses

3. **Phase 5: UI Updates** ✅
   - Progress indicator showing research phases (Recall → Search → Analyze → Synthesize → Learn)
   - "Clear Memory" button in sidebar
   - Memory status display

4. **Consolidated Agents**
   - Removed `ai_agent.py` (simple RAG agent)
   - `SuttaPitakaAgent` now handles all queries (iterative by default)

5. **Phase 9: Pali Dictionary & Term Search** ✅ (NEW)
   - Created `src/dictionary/pali_dictionary.py` - dictionary lookup
   - Created `src/dictionary/pali_search.py` - term search across suttas
   - UI: "Pali Tools" tab with Term Search and Dictionary sub-tabs
   - Example: "nirodha" → 231 occurrences across 49 suttas

### What Was Done (Dec 21)
1. Renamed "RAG Agent" to "AI Agent" throughout UI and codebase
2. Fixed Gemini model IDs (removed `models/` prefix)
3. Made top_k dynamic based on model provider
4. Added `.env` file support for API keys

### What Was Done (Dec 19)
1. Renamed project from `pali-canon-rag-agent` to `sutta-pitaka-rag-agent`
2. Updated all code references (collection name, class names, UI text)
3. Re-ingested MN data with new collection name `sutta_pitaka`
4. Updated system prompt to require inline citations
5. Made prompt stricter to only reference retrieved context

---

## Completed Phases

### Phase 1: Extend Ingestion (Full Sutta Pitaka) ✅ DONE

**Files created:** `src/ingestion/sutta_discovery.py`, `src/ingestion/progress_tracker.py`

- ✅ Dynamic sutta discovery via SuttaCentral suttaplex API
- ✅ Support for all nikayas (DN, MN, SN, AN) and KN collections
- ✅ Resume capability for interrupted ingestion
- ✅ Progress tracking in `cache/ingestion_progress/`
- ✅ Extended CLI: `--all`, `--nikaya`, `--kn`, `--dry-run`, `--status`, `--clear-progress`
- ✅ 4,050 suttas available (Sujato translations)

### Phase 2: Increase Retrieval Capacity ✅ DONE

- ✅ Made top_k dynamic based on model type (5 for local, 20 for cloud)
- ✅ Added `SIMILARITY_TOP_K_LOCAL` and `SIMILARITY_TOP_K_CLOUD` config options
- ✅ `get_top_k_for_model()` helper function selects appropriate value

### Phase 3: Build Iterative AI Agent with Memory ✅ DONE

**Files created:** `src/agent/iterative_agent.py`, `src/agent/memory.py`

- ✅ `SuttaPitakaAgent` class with multi-pass search
- ✅ Gap analysis to identify missing information
- ✅ Deduplication of retrieved chunks
- ✅ Progress callbacks for UI updates

### Phase 4: Analysis & Synthesis Prompts ✅ DONE

- ✅ Gap analysis prompt in `iterative_agent.py`
- ✅ Synthesis prompt for scholarly output with citations

### Phase 5: Update UI ✅ DONE

- ✅ Progress indicator showing research phases
- ✅ "Clear Agent Memory" button in sidebar
- ✅ Memory status display
- ✅ "Recalled from memory" indicator

### Phase 6: Long-Term Memory ✅ DONE

**File created:** `src/agent/memory.py`

- ✅ Dedicated ChromaDB collection `agent_wisdom`
- ✅ `save()` stores synthesized answers with metadata
- ✅ `recall()` searches for similar prior queries

### Phase 7: Rename Project ✅ DONE

- ✅ Updated UI titles and descriptions
- ✅ Consolidated to single `SuttaPitakaAgent` class
- ✅ Updated docstrings

### Phase 9: Pali Dictionary & Term Search ✅ DONE

**Files created:** `src/dictionary/pali_dictionary.py`, `src/dictionary/pali_search.py`

- ✅ Pali-English dictionary with 142K entries from SuttaCentral API
- ✅ Pali term search across cached suttas
- ✅ Occurrence counts by sutta
- ✅ UI: "Pali Tools" tab with Term Search and Dictionary

---

### Phase 8: Enhanced Search Mode ✅ DONE

**Files created:** `src/retrieval/sutta_search.py`

- ✅ Exhaustive vector search (high top_k: 200-500)
- ✅ Returns list of matching suttas without LLM synthesis
- ✅ Groups results by sutta (not by chunk)
- ✅ Shows relevance scores and snippet previews
- ✅ UI: "Search" tab between Chat and Pali Tools

---

### Phase 10: Additional Dictionaries ✅ DONE

**Files created:** `src/dictionary/english_to_pali.py`, `src/dictionary/dppn.py`

- ✅ English-to-Pali reverse index (36,502 English words)
- ✅ DPPN dictionary from SuttaCentral GitHub (1,367 entries)
- ✅ UI: Pali Tools expanded to 4 tabs
- ✅ Entry types classified: person, place, thing

---

## All Phases Complete!

The Sutta Pitaka AI Agent now has all planned features implemented.

---

## File Structure (Current)

```
sutta-pitaka-ai-agent/
├── app.py                      # Streamlit UI (Chat + Pali Tools tabs)
├── ingest.py                   # CLI for ingestion (extended)
├── .env                        # API keys
├── PLAN.md                     # This file
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── iterative_agent.py  # Main agent with memory
│   │   └── memory.py           # Agent wisdom persistence
│   ├── dictionary/
│   │   ├── __init__.py
│   │   ├── pali_dictionary.py    # Pali-English dictionary
│   │   ├── english_to_pali.py    # English-to-Pali reverse index (NEW)
│   │   ├── dppn.py               # Dict of Pali Proper Names (NEW)
│   │   └── pali_search.py        # Pali term search
│   ├── config.py               # Settings (incl. ALL_NIKAYAS, KN_COLLECTIONS)
│   ├── indexing/
│   │   └── vector_store.py     # ChromaDB
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── suttacentral.py     # API client with discovery
│   │   ├── sutta_discovery.py  # Dynamic sutta discovery (NEW)
│   │   ├── progress_tracker.py # Resume capability (NEW)
│   │   └── processor.py        # Document chunking
│   └── retrieval/
│       ├── query_engine.py     # Query engine
│       └── sutta_search.py     # Exhaustive search with grouping (NEW)
├── chroma_db/                  # Vector database
│   ├── sutta_pitaka/           # Main sutta embeddings
│   └── agent_wisdom/           # Learned insights
└── cache/
    ├── suttas/                     # Cached sutta JSON files
    ├── ingestion_progress/         # Progress tracking
    ├── pali_dictionary.json        # Pali-English dictionary cache
    ├── english_to_pali_index.json  # English-to-Pali reverse index (NEW)
    └── dppn_dictionary.json        # DPPN cache (NEW)
```

---

## Quick Start Commands

```bash
# Navigate to project
cd /Users/markl1/Documents/AI-Agents/sutta-pitaka-ai-agent

# Activate virtual environment
source venv/bin/activate

# Run the app
streamlit run app.py

# Check current ingestion status
python ingest.py --status

# Ingest the full Sutta Pitaka (with resume support)
python ingest.py --all

# Ingest a specific nikaya
python ingest.py --nikaya sn

# Ingest a sub-collection
python ingest.py --nikaya sn12

# Ingest a KN collection
python ingest.py --kn snp

# Dry run to see what would be ingested
python ingest.py --dry-run --all

# Stop streamlit when done
pkill -f streamlit
```

---

## Future Enhancements (Optional)

These are ideas for future development:

1. **Metadata filtering** - Filter search results by nikaya, topic tags
2. **Export research results** - Save agent responses and citations
3. **Compare passages** - Side-by-side comparison of parallel suttas
4. **Pali grammar tools** - Verb conjugation, noun declension lookup
5. **Sutta bookmarks** - Save and organize favorite passages
