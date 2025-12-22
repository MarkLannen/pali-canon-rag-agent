# Sutta Pitaka AI Agent - Implementation Plan

## Current State (as of Dec 21, 2024)

### What's Working
- ChromaDB vector store with 1,043 chunks from Majjhima Nikaya (152 suttas)
- SuttaCentral API integration for fetching suttas
- Document processor for chunking suttas
- Basic query engine with dynamic top-k based on model type
- Streamlit UI at `app.py`
- Multi-model support (Ollama, Anthropic, Google, OpenAI)
- Dynamic retrieval: 5 chunks for local models, 20 for cloud models

### What Was Done (Dec 19)
1. Renamed project from `pali-canon-rag-agent` to `sutta-pitaka-rag-agent`
2. Updated all code references (collection name, class names, UI text)
3. Re-ingested MN data with new collection name `sutta_pitaka`
4. Updated system prompt to require inline citations
5. Made prompt stricter to only reference retrieved context (no LLM hallucination)

### What Was Done (Dec 21)
1. Renamed "RAG Agent" to "AI Agent" throughout UI and codebase
2. Renamed `rag_agent.py` to `ai_agent.py`
3. Fixed Gemini model IDs (removed `models/` prefix)
4. Made top_k dynamic based on model provider:
   - Local models (Ollama): 5 chunks - works within context limits
   - Cloud models: 20 chunks - leverages larger context windows
5. Added `.env` file support for API keys

### Current Limitation
Single-pass retrieval is insufficient for comprehensive scholarly queries. Furthermore, the agent has no "memory"—it performs the same expensive search every time a question is repeated.

---

## Goal: Reflective Agentic Iterative Search

Build an AI agent that iteratively searches the entire Sutta Pitaka until it has gathered comprehensive information, and **persists that knowledge** in a long-term memory store to "learn" over time.

### How It Should Work

1. User asks: "Give me a synopsis of all the ways the Buddha described karma"
2. **Recall Phase:** Agent checks a "Wisdom" collection to see if it has researched this before.
3. **Search Phase:** If no memory exists, agent performs initial broad search (top 20-30 results).
4. **Iterative Phase:** Agent analyzes results, identifies gaps, and generates refined queries.
5. **Synthesis Phase:** Agent aggregates findings into a comprehensive, well-cited answer.
6. **Learning Phase:** Agent saves the final synthesis back into its memory for future use.

---

## Implementation Plan

### Phase 1: Extend Ingestion (Ingest Full Sutta Pitaka)

**Files to modify:** `src/config.py`, `ingest.py`, `src/ingestion/suttacentral.py`

1. Add support for all nikayas (DN, SN, AN, KN).
2. Implement **Recursive Character Splitting** in `processor.py` to better handle formulaic/repetitive text in SN/AN.
3. Add batch ingestion command: `python ingest.py --all`
4. Estimate: ~5,400 suttas total, likely 30,000-50,000 chunks

### Phase 2: Increase Retrieval Capacity ✅ DONE

**Files modified:** `src/config.py`, `src/retrieval/query_engine.py`

1. ✅ Made top_k dynamic based on model type (5 for local, 20 for cloud)
2. ✅ Added `SIMILARITY_TOP_K_LOCAL` and `SIMILARITY_TOP_K_CLOUD` config options
3. ✅ `get_top_k_for_model()` helper function selects appropriate value
4. TODO: Add metadata filtering (by nikaya, by topic tags if available)

### Phase 3: Build Iterative AI Agent with Memory

**New file:** `src/agent/iterative_agent.py`

```python
class SuttaPitakaAgent:
    """
    AI Agent that iteratively searches and remembers findings.
    """
    def __init__(self, vector_store, llm):
        self.vector_store = vector_store
        self.llm = llm
        self.memory = AgentMemory(vector_store) # Persistence layer
        self.max_iterations = 5

    def search(self, query: str) -> AgentResponse:
        # 1. Check if we've already 'learned' this
        wisdom = self.memory.recall(query)
        if wisdom: return wisdom

        # 2. Iterative search loop
        all_passages = []
        for i in range(self.max_iterations):
            new_passages = self._retrieve(query)
            all_passages.extend(new_passages)
            analysis = self._analyze_coverage(query, all_passages)
            if analysis.is_complete: break
            query = analysis.next_query

        # 3. Synthesize and save to memory
        response = self._synthesize(query, all_passages)
        self.memory.save(query, response)
        return response
```

### Phase 4: Analysis & Synthesis Prompts

1. **Analysis Prompt (Gap Identification):**
   - "Identify what is missing from these passages to fully answer [Query]. Generate a refined search term."

2. **Synthesis Prompt (Scholarly Output):**
   - "Construct a thematic response using ONLY the retrieved passages. Cite every sutta."

### Phase 5: Update UI

1. Add progress indicator: "Searching... Step 2/5... Recalling from memory..."
2. Add a "Clear Agent Memory" button in the sidebar for debugging/resetting.
3. Consider adding "search depth" setting (quick vs thorough)

### Phase 6: Long-Term Memory (The "Learning" Layer)

**New file:** `src/agent/memory.py`

1. Create a dedicated ChromaDB collection `agent_wisdom`.
2. Implement `save_learned_insight()`: Stores the final LLM synthesis with metadata (original query, suttas cited).
3. Implement `recall_relevant_wisdom()`: Performs a similarity search on the `agent_wisdom` collection before starting a new search.

### Phase 7: Rename Project ✅ DONE

Update remaining references from "RAG" terminology to "Sutta Pitaka AI Agent":
- ✅ Updated UI titles and descriptions
- ✅ Renamed `rag_agent.py` to `ai_agent.py`
- ✅ Updated docstrings

### Phase 8: Search-Only Mode (For Counting Queries)

**New file:** `src/retrieval/search_mode.py`

For questions like "how many suttas mention X" or "list all suttas about Y", the iterative agent isn't ideal. Need a pure search mode that:

1. Performs exhaustive vector search (high top_k, e.g., 100-500)
2. Returns list of matching suttas without LLM synthesis
3. Groups results by sutta (not by chunk)
4. Shows relevance scores and snippet previews

**Use cases:**
- "How many suttas in the Majjhima Nikaya describe the Buddha's enlightenment?"
- "List all suttas that mention the five aggregates"
- "Which suttas discuss the four noble truths?"

**UI integration:**
- Add "Search Mode" toggle in sidebar (Answer vs. Search)
- Search mode shows results as a browsable list, not a synthesized answer
- Optional: Allow clicking a result to ask a follow-up question about that sutta

---

## Technical Considerations

### Context Window
- With 30-50 passages, use a **Map-Reduce** synthesis strategy to avoid hitting token limits.

### Deduplication
- Track `chunk_id` during iterations to ensure the agent doesn't process the same text twice in one session.

### Persistence
- Ensure the `agent_wisdom` collection is persisted to disk so "learning" survives application restarts.

---

## File Structure After Implementation

```
sutta-pitaka-ai-agent/
├── app.py                      # Streamlit UI
├── ingest.py                   # CLI for ingestion
├── .env                        # API keys (GOOGLE_API_KEY, etc.)
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── ai_agent.py         # Current simple agent (quick queries)
│   │   ├── iterative_agent.py  # NEW: Iterative search agent
│   │   └── memory.py           # NEW: Agent memory/wisdom persistence
│   ├── config.py               # Settings (dynamic top_k, NIKAYA_RANGES)
│   ├── indexing/
│   │   └── vector_store.py     # ChromaDB (no changes needed)
│   ├── ingestion/
│   │   ├── suttacentral.py     # API client (extend for SN/AN/KN)
│   │   └── processor.py        # Document chunking (no changes needed)
│   └── retrieval/
│       ├── query_engine.py     # Query engine (dynamic top_k)
│       └── search_mode.py      # NEW: Pure search for counting queries
└── chroma_db/                  # Vector database (includes agent_wisdom collection)
```

---

## Quick Start Commands

```bash
# Navigate to project
cd /Users/markl1/Documents/AI-Agents/sutta-pitaka-ai-agent

# Activate virtual environment
source venv/bin/activate

# Run the current app (for testing)
streamlit run app.py

# Check current ingestion status
python ingest.py --status

# Stop streamlit when done
pkill -f streamlit
```

---

## Next Steps (Priority Order)

### Immediate: Phase 3 - Iterative Agent with Memory
1. Create `src/agent/memory.py` with AgentMemory class
2. Create `src/agent/iterative_agent.py`
3. Implement multi-pass search with gap analysis
4. Add progress callbacks for UI updates
5. Test "Search -> Save -> Recall" loop with a single query

### Then: Phase 8 - Search-Only Mode
1. Create `src/retrieval/search_mode.py`
2. Implement exhaustive search with sutta grouping
3. Add UI toggle for Answer vs. Search mode

### Later: Phase 1 - Full Sutta Pitaka Ingestion
1. Extend SuttaCentral API client for DN, SN, AN, KN
2. Handle complex nested structures (SN, AN)
3. Batch ingest all ~10,000+ suttas
