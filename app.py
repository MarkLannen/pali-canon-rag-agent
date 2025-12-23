"""Streamlit UI for the Sutta Pitaka AI Agent."""

import streamlit as st

from src.agent import SuttaPitakaAgent, AgentPhase, AgentProgress
from src.config import get_default_model


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


def render_chat():
    """Render the chat interface."""
    st.title("Sutta Pitaka AI Agent 📿")
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
    render_sidebar()
    render_chat()


if __name__ == "__main__":
    main()
