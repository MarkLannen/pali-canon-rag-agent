"""Streamlit UI for the Sutta Pitaka AI Agent."""

import streamlit as st

from src.agent import SuttaPitakaAgent, AgentPhase, AgentProgress
from src.config import get_default_model, SEARCH_TOP_K_DEFAULT, SEARCH_TOP_K_MAX
from src.dictionary import (
    PaliDictionary,
    PaliTextSearch,
    DPPNDictionary,
    EnglishToPaliDictionary,
)
from src.retrieval import SuttaSearchEngine


# Page configuration
st.set_page_config(
    page_title="Sutta Pitaka AI Agent",
    page_icon="📿",
    layout="wide",
)


def init_session_state():
    """Initialize session state variables."""
    if "agent" not in st.session_state:
        st.session_state.agent = SuttaPitakaAgent()
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "model_id" not in st.session_state:
        st.session_state.model_id = get_default_model().id
    if "pali_dict" not in st.session_state:
        st.session_state.pali_dict = PaliDictionary()
    if "pali_search" not in st.session_state:
        st.session_state.pali_search = PaliTextSearch()
    if "sutta_search" not in st.session_state:
        st.session_state.sutta_search = SuttaSearchEngine()
    if "dppn_dict" not in st.session_state:
        st.session_state.dppn_dict = DPPNDictionary()
    if "eng_pali_dict" not in st.session_state:
        st.session_state.eng_pali_dict = EnglishToPaliDictionary()


def render_sidebar():
    """Render the sidebar with settings."""
    with st.sidebar:
        st.title("Settings")

        # Model selection
        st.subheader("LLM Model")

        available_models = st.session_state.agent.get_available_models()

        if not available_models:
            st.error("No models available. Check Ollama or add API keys.")
        else:
            model_options = {m.id: m.display_name for m in available_models}
            current_model_id = st.session_state.model_id
            model_ids = list(model_options.keys())

            if current_model_id not in model_ids:
                current_model_id = model_ids[0]

            current_index = model_ids.index(current_model_id)

            selected_model_id = st.selectbox(
                "Choose model:",
                options=model_ids,
                format_func=lambda x: model_options[x],
                index=current_index,
            )

            current_model = next(
                (m for m in available_models if m.id == selected_model_id), None
            )
            if current_model:
                st.caption(current_model.description)
                if current_model.is_free:
                    st.caption("💚 Free (runs locally)")

            if selected_model_id != st.session_state.model_id:
                st.session_state.model_id = selected_model_id
                try:
                    st.session_state.agent.set_model(selected_model_id)
                    st.success(f"Switched to {model_options[selected_model_id]}")
                except ValueError as e:
                    st.error(str(e))

        # Status
        st.divider()
        st.subheader("Status")

        if st.session_state.agent.is_ready():
            doc_count = st.session_state.agent.get_document_count()
            st.success(f"Ready - {doc_count:,} chunks indexed")
        else:
            st.warning("No suttas indexed yet")
            st.info("Run `python ingest.py --nikaya mn` to index suttas")

        # Memory status
        st.divider()
        st.subheader("Agent Memory")
        memory_count = st.session_state.agent.get_memory_count()
        st.info(f"{memory_count} learned insight{'s' if memory_count != 1 else ''}")

        if memory_count > 0:
            if st.button("Clear Memory", use_container_width=True):
                st.session_state.agent.clear_memory()
                st.rerun()

        # Clear chat button
        st.divider()
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        # About section
        st.divider()
        st.subheader("About")
        st.markdown("""
        **Sutta Pitaka AI Agent**

        Ask questions about the Sutta Pitaka.
        The agent iteratively searches for
        comprehensive answers and remembers
        insights for future queries.

        Data source: [SuttaCentral](https://suttacentral.net)
        """)


def render_pali_tools():
    """Render the Pali tools tab."""
    st.header("Pali Tools 📚")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Term Search",
        "Pali → English",
        "English → Pali",
        "Proper Names (DPPN)",
    ])

    with tab1:
        st.subheader("Search Pali Terms in Suttas")
        st.caption("Find how many times a Pali term appears across the suttas")

        pali_term = st.text_input(
            "Enter Pali term:",
            placeholder="e.g., nirodha, dukkha, satipaṭṭhāna",
            key="pali_search_term",
        )

        if pali_term:
            with st.spinner("Searching..."):
                result = st.session_state.pali_search.search(pali_term, limit=50)

            st.success(result.format_summary())

            if result.matches:
                # Show by sutta
                st.subheader("Occurrences by Sutta")
                counts = st.session_state.pali_search.count_occurrences(pali_term)
                sorted_counts = sorted(counts.items(), key=lambda x: -x[1])

                # Show first 15 results
                for sutta_uid, count in sorted_counts[:15]:
                    st.write(f"**{sutta_uid}**: {count} occurrence{'s' if count != 1 else ''}")

                # Show remaining results in expander
                if len(sorted_counts) > 15:
                    remaining = sorted_counts[15:]
                    with st.expander(f"View all {len(sorted_counts)} suttas (+{len(remaining)} more)"):
                        for sutta_uid, count in remaining:
                            st.write(f"**{sutta_uid}**: {count} occurrence{'s' if count != 1 else ''}")

                # Show sample matches
                with st.expander("View Sample Matches"):
                    for match in result.matches[:10]:
                        st.markdown(f"**{match.segment_id}**")
                        st.text(f"Pali: {match.pali_text[:200]}...")
                        st.text(f"Eng:  {match.english_text[:200]}...")
                        st.divider()

    with tab2:
        st.subheader("Pali-English Dictionary")
        st.caption("Look up Pali terms and their meanings")

        # Ensure dictionary is loaded
        if not st.session_state.pali_dict.is_loaded():
            with st.spinner("Loading dictionary..."):
                st.session_state.pali_dict.load()
            st.caption(f"Dictionary loaded: {st.session_state.pali_dict.get_entry_count():,} entries")

        dict_term = st.text_input(
            "Enter Pali term:",
            placeholder="e.g., bodhi, nibbāna, saṅkhāra",
            key="dict_lookup_term",
        )

        if dict_term:
            # Try direct lookup first
            entry = st.session_state.pali_dict.lookup(dict_term)

            if entry:
                st.markdown(entry.format())
            else:
                # Search for similar terms
                results = st.session_state.pali_dict.search(dict_term, limit=10)
                if results:
                    st.warning(f"No exact match for '{dict_term}'. Similar terms:")
                    for r in results:
                        with st.expander(r.term):
                            st.markdown(r.format())
                else:
                    st.error(f"No entries found for '{dict_term}'")

    with tab3:
        st.subheader("English-Pali Dictionary")
        st.caption("Find Pali terms for English words")

        # Ensure dictionary is loaded
        if not st.session_state.eng_pali_dict.is_loaded():
            with st.spinner("Building reverse index from Pali dictionary..."):
                st.session_state.eng_pali_dict.load()
            st.caption(
                f"Index built: {st.session_state.eng_pali_dict.get_word_count():,} English words"
            )

        eng_term = st.text_input(
            "Enter English word:",
            placeholder="e.g., suffering, mindfulness, enlightenment",
            key="eng_pali_lookup_term",
        )

        if eng_term:
            # Try direct lookup first
            entry = st.session_state.eng_pali_dict.lookup(eng_term)

            if entry:
                st.success(f"Found {len(entry.pali_terms)} Pali terms for '{eng_term}'")
                for i, item in enumerate(entry.pali_terms, 1):
                    term = item["term"]
                    defn = item.get("definition", "")
                    grammar = item.get("grammar", "")

                    # Clean HTML from definition
                    import re
                    clean_defn = re.sub(r'<[^>]+>', '', defn)

                    with st.expander(f"{i}. {term}" + (f" ({grammar})" if grammar else "")):
                        st.markdown(f"**{term}**")
                        st.write(clean_defn[:500] if len(clean_defn) > 500 else clean_defn)
            else:
                # Search for similar terms
                results = st.session_state.eng_pali_dict.search(eng_term, limit=10)
                if results:
                    st.warning(f"No exact match for '{eng_term}'. Similar words:")
                    for r in results:
                        with st.expander(f"{r.english_word} ({len(r.pali_terms)} Pali terms)"):
                            for item in r.pali_terms[:5]:
                                st.write(f"• **{item['term']}**")
                else:
                    st.error(f"No entries found for '{eng_term}'")

    with tab4:
        st.subheader("Dictionary of Pali Proper Names (DPPN)")
        st.caption("Look up people, places, and concepts in the Pali Canon")

        # Ensure dictionary is loaded
        if not st.session_state.dppn_dict.is_loaded():
            with st.spinner("Loading DPPN dictionary..."):
                st.session_state.dppn_dict.load()
            entry_count = st.session_state.dppn_dict.get_entry_count()
            types = st.session_state.dppn_dict.get_types()
            type_summary = ", ".join(f"{k}: {v}" for k, v in sorted(types.items()))
            st.caption(f"DPPN loaded: {entry_count:,} entries ({type_summary})")

        dppn_term = st.text_input(
            "Enter name:",
            placeholder="e.g., Sāriputta, Rājagaha, Vesālī",
            key="dppn_lookup_term",
        )

        if dppn_term:
            # Try direct lookup first
            entry = st.session_state.dppn_dict.lookup(dppn_term)

            if entry:
                st.markdown(entry.format())

                # Show sutta references if any
                refs = entry.get_references()
                if refs:
                    with st.expander(f"Sutta References ({len(refs)})"):
                        for ref in sorted(refs)[:30]:
                            st.write(f"• [{ref}](https://suttacentral.net/{ref})")
            else:
                # Search for similar terms
                results = st.session_state.dppn_dict.search(dppn_term, limit=10)
                if results:
                    st.warning(f"No exact match for '{dppn_term}'. Similar names:")
                    for r in results:
                        type_label = f" ({r.entry_type})" if r.entry_type else ""
                        with st.expander(f"{r.word}{type_label}"):
                            st.markdown(r.format())
                else:
                    st.error(f"No entries found for '{dppn_term}'")


def render_search():
    """Render the sutta search interface."""
    st.header("Search Suttas 🔍")
    st.caption("Find all suttas that mention a topic (no AI synthesis)")

    # Search input
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(
            "Search query:",
            placeholder="e.g., mindfulness, dependent origination, four noble truths",
            key="sutta_search_query",
        )
    with col2:
        top_k = st.number_input(
            "Max results:",
            min_value=50,
            max_value=SEARCH_TOP_K_MAX,
            value=SEARCH_TOP_K_DEFAULT,
            step=50,
            key="sutta_search_top_k",
        )

    if query:
        with st.spinner(f"Searching {top_k} passages..."):
            results = st.session_state.sutta_search.search(query, top_k=top_k)

        if results.sutta_count == 0:
            st.warning("No matching suttas found. Try different search terms.")
        else:
            # Summary
            st.success(f"Found **{results.sutta_count} suttas** ({results.total_chunks} matching passages)")

            # Results grouped by sutta
            for i, sutta in enumerate(results.results):
                # Show first 20 without expander, rest in "Show more"
                if i < 20:
                    with st.expander(
                        f"**{sutta.sutta_uid}** - {sutta.title} "
                        f"(score: {sutta.best_score:.3f}, {sutta.match_count} matches)"
                    ):
                        for snippet in sutta.snippets:
                            st.markdown(f"*{snippet['segment_range']}* (score: {snippet['score']:.3f})")
                            st.text(snippet["text"])
                            st.divider()

            # Show remaining results
            if results.sutta_count > 20:
                remaining = results.results[20:]
                with st.expander(f"Show {len(remaining)} more suttas..."):
                    for sutta in remaining:
                        st.markdown(
                            f"**{sutta.sutta_uid}** - {sutta.title} "
                            f"(score: {sutta.best_score:.3f}, {sutta.match_count} matches)"
                        )


def render_chat():
    """Render the chat interface."""
    st.header("Ask the Agent 💬")
    st.caption("Ask questions about the Sutta Pitaka")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant":
                # Show memory indicator
                if message.get("from_memory"):
                    st.caption("📚 Recalled from memory")

                # Show sources in expander
                citations = message.get("citations", [])
                if citations:
                    with st.expander(f"View Sources ({len(citations)})"):
                        for i, c in enumerate(citations, 1):
                            st.markdown(f"**{i}. {c['title']}** ({c['sutta_uid']}: {c['segment_range']})")
                            st.markdown(f"*Score: {c['score']:.3f}*")
                            st.text(c["text"][:500] + "..." if len(c["text"]) > 500 else c["text"])
                            st.divider()

    # Chat input
    if prompt := st.chat_input("Ask about the Sutta Pitaka..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            if not st.session_state.agent.is_ready():
                response_text = "No suttas have been indexed yet. Please run `python ingest.py --nikaya mn` first."
                st.markdown(response_text)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "citations": [],
                })
            else:
                # Create progress placeholder
                progress_placeholder = st.empty()

                def update_progress(progress: AgentProgress):
                    """Update the progress display."""
                    phase_icons = {
                        AgentPhase.RECALL: "🧠",
                        AgentPhase.SEARCH: "🔍",
                        AgentPhase.ANALYZE: "📊",
                        AgentPhase.SYNTHESIZE: "✍️",
                        AgentPhase.LEARN: "💾",
                        AgentPhase.COMPLETE: "✅",
                    }
                    icon = phase_icons.get(progress.phase, "⏳")

                    if progress.phase == AgentPhase.COMPLETE:
                        progress_placeholder.empty()
                    else:
                        progress_placeholder.info(
                            f"{icon} {progress.message} "
                            f"(Step {progress.iteration}/{progress.max_iterations})"
                        )

                # Set up progress callback
                st.session_state.agent.set_progress_callback(update_progress)

                try:
                    result = st.session_state.agent.research(prompt)

                    # Clear progress
                    progress_placeholder.empty()

                    # Show answer
                    st.markdown(result.answer)

                    # Show memory indicator
                    if result.from_memory:
                        st.caption("📚 Recalled from memory")

                    # Show sources
                    citations = [
                        {
                            "sutta_uid": c.sutta_uid,
                            "segment_range": c.segment_range,
                            "title": c.title,
                            "text": c.text_snippet,
                            "score": c.score,
                        }
                        for c in result.citations
                    ]

                    if citations:
                        with st.expander(f"View Sources ({len(citations)})"):
                            for i, c in enumerate(citations, 1):
                                st.markdown(f"**{i}. {c['title']}** ({c['sutta_uid']}: {c['segment_range']})")
                                st.markdown(f"*Score: {c['score']:.3f}*")
                                st.text(c["text"][:500] + "..." if len(c["text"]) > 500 else c["text"])
                                st.divider()

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result.answer,
                        "citations": citations,
                        "from_memory": result.from_memory,
                    })

                except Exception as e:
                    progress_placeholder.empty()
                    error_msg = f"Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "citations": [],
                    })


def main():
    """Main application entry point."""
    init_session_state()

    # Main title
    st.title("Sutta Pitaka AI Agent 📿")

    # Create tabs for main content
    tab_chat, tab_search, tab_pali = st.tabs(["💬 Chat", "🔍 Search", "📚 Pali Tools"])

    with tab_chat:
        render_chat()

    with tab_search:
        render_search()

    with tab_pali:
        render_pali_tools()

    # Render sidebar
    render_sidebar()


if __name__ == "__main__":
    main()
