# Sutta Pitaka AI Agent - Implementation Plan

## Current State (as of Dec 19, 2024)

### What's Working
- ChromaDB vector store with 1,043 chunks from Majjhima Nikaya (152 suttas)
- SuttaCentral API integration for fetching suttas
- Document processor for chunking suttas
- Basic query engine (retrieves top-k similar chunks)
- Streamlit UI at `app.py`
- Multi-model support (Ollama, Anthropic, Google, OpenAI)

### What Was Done Today
1. Renamed project from `pali-canon-rag-agent` to `sutta-pitaka-rag-agent`
2. Updated all code references (collection name, class names, UI text)
3. Re-ingested MN data with new collection name `sutta_pitaka`
4. Updated system prompt to require inline citations
5. Made prompt stricter to only reference retrieved context (no LLM hallucination)

### Current Limitation
The current system only retrieves top 5 chunks per query. For comprehensive scholarly queries like "describe all ways Buddha taught about karma," this is insufficient.

---

## Goal: Agentic Iterative Search

Build an AI agent that iteratively searches the entire Sutta Pitaka until it has gathered comprehensive information on a topic.

### How It Should Work
1. User asks: "Give me a synopsis of all the ways the Buddha described karma"
2. Agent performs initial broad search (top 20-30 results)
3. Agent analyzes results, identifies sub-topics and gaps
4. Agent generates refined queries to find more passages
5. Agent continues until topic is exhausted or sufficient evidence gathered
6. Agent aggregates all findings into comprehensive, well-cited answer

---

## Implementation Plan

### Phase 1: Extend Ingestion (Ingest Full Sutta Pitaka)

**Files to modify:** `src/config.py`, `ingest.py`, `src/ingestion/suttacentral.py`

1. Add support for all nikayas:
   - DN (Digha Nikaya): 34 suttas - simple range like MN
   - SN (Samyutta Nikaya): ~2,900 suttas - complex nested structure
   - AN (Anguttara Nikaya): ~2,300 suttas - organized by number (1s, 2s, 3s, etc.)
   - KN (Khuddaka Nikaya): Multiple texts (Dhammapada, Sutta Nipata, etc.)

2. Update `NIKAYA_RANGES` in config.py to handle complex structures

3. Add batch ingestion command: `python ingest.py --all`

4. Estimate: ~5,400 suttas total, likely 30,000-50,000 chunks

### Phase 2: Increase Retrieval Capacity

**Files to modify:** `src/config.py`, `src/retrieval/query_engine.py`

1. Increase `SIMILARITY_TOP_K` from 5 to 20-30
2. Add configurable retrieval parameters
3. Consider adding metadata filtering (by nikaya, by topic tags if available)

### Phase 3: Build Iterative AI Agent

**New file:** `src/agent/iterative_agent.py`

```python
class SuttaPitakaAgent:
    """
    AI Agent that iteratively searches until topic is exhausted.
    """

    def __init__(self, vector_store, llm):
        self.vector_store = vector_store
        self.llm = llm
        self.retrieved_ids = set()  # Track what we've seen
        self.max_iterations = 5
        self.passages_per_iteration = 20

    def search(self, query: str) -> AgentResponse:
        """
        Iteratively search and aggregate results.
        """
        all_passages = []
        current_query = query

        for i in range(self.max_iterations):
            # Retrieve passages (excluding already seen)
            new_passages = self._retrieve(current_query, exclude=self.retrieved_ids)

            if not new_passages:
                break  # No more relevant content

            all_passages.extend(new_passages)
            self.retrieved_ids.update(p.id for p in new_passages)

            # Ask LLM: Is there more to find? What refined query?
            analysis = self._analyze_coverage(query, all_passages)

            if analysis.is_complete:
                break

            current_query = analysis.next_query

        # Generate final comprehensive answer
        return self._synthesize(query, all_passages)
```

### Phase 4: Update Prompts for Iterative Agent

**Files to modify:** `src/retrieval/query_engine.py` or new prompt file

1. **Analysis Prompt** - Determines if more searching is needed:
   ```
   Given the original question and retrieved passages, determine:
   1. Have we found comprehensive coverage of this topic?
   2. Are there related aspects not yet covered?
   3. What refined query would find additional relevant passages?
   ```

2. **Synthesis Prompt** - Creates final comprehensive answer:
   ```
   Using ALL the passages below, provide a comprehensive scholarly answer.
   Organize by theme/subtopic if appropriate.
   Cite every sutta referenced (e.g., MN1, SN56.11, AN4.5).
   ```

### Phase 5: Update UI

**Files to modify:** `app.py`

1. Add progress indicator for iterative search ("Searching... found 45 relevant passages")
2. Show iteration count and passages found
3. Consider adding "search depth" setting (quick vs thorough)

### Phase 6: Rename Project (Optional)

Update remaining references from "RAG" terminology to "Sutta Pitaka AI Agent":
- Update class names if desired
- Update UI titles and descriptions
- Update docstrings

---

## Technical Considerations

### Token Limits
- With 50+ passages, context can exceed token limits
- Solution: Summarize passages before final synthesis, or use map-reduce approach

### Cost
- Multiple LLM calls per query (analysis + synthesis)
- Consider caching common queries
- Offer "quick" vs "thorough" search modes

### Deduplication
- Same passage might be retrieved by different queries
- Track by chunk ID to avoid duplicates

### Performance
- Full Sutta Pitaka will be ~50k chunks
- ChromaDB handles this fine, but queries may be slower
- Consider adding indexes on metadata fields

---

## File Structure After Implementation

```
sutta-pitaka-rag-agent/
├── app.py                      # Streamlit UI
├── ingest.py                   # CLI for ingestion
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── rag_agent.py        # Current simple agent (keep for quick queries)
│   │   └── iterative_agent.py  # NEW: Iterative search agent
│   ├── config.py               # Settings (update NIKAYA_RANGES)
│   ├── indexing/
│   │   └── vector_store.py     # ChromaDB (no changes needed)
│   ├── ingestion/
│   │   ├── suttacentral.py     # API client (extend for SN/AN/KN)
│   │   └── processor.py        # Document chunking (no changes needed)
│   └── retrieval/
│       └── query_engine.py     # Query engine (increase top_k)
└── chroma_db/                  # Vector database
```

---

## Quick Start Commands

```bash
# Navigate to project
cd /Users/markl1/Documents/AI-Agents/sutta-pitaka-rag-agent

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

## Next Session: Suggested Starting Point

1. Start by increasing `SIMILARITY_TOP_K` to 20 in `src/config.py`
2. Test with current MN data to see improved retrieval
3. Then begin implementing the iterative agent in Phase 3
