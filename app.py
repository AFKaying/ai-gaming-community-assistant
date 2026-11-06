"""A local dashboard for reviewing AI drafted community replies."""

import json
from pathlib import Path

import ollama
import streamlit as st


DRAFTS_FILE = Path(__file__).with_name("drafts.json")
GUIDE_FILE = Path(__file__).with_name("community_guide.md")


def load_draft_queue():
    if not DRAFTS_FILE.exists():
        return []

    try:
        saved_drafts = json.loads(DRAFTS_FILE.read_text(encoding="utf-8"))
        return saved_drafts if isinstance(saved_drafts, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_draft_queue():
    DRAFTS_FILE.write_text(
        json.dumps(st.session_state["draft_queue"], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def save_draft_edit(index):
    st.session_state["draft_queue"][index]["reply"] = st.session_state[
        f"draft_reply_{index + 1}"
    ]
    save_draft_queue()


st.set_page_config(page_title="AI Community Assistant", page_icon="🎮")
st.title("🎮 AI Community Assistant")
st.write("Draft helpful replies for a fictional gaming community.")

st.info(
    "This prototype uses a model running on your computer. "
    "Review and edit every draft before sharing it."
)
st.caption("Drafts and review statuses are saved locally in this project folder.")

if "draft_queue" not in st.session_state:
    st.session_state["draft_queue"] = load_draft_queue()
elif st.session_state["draft_queue"] and not DRAFTS_FILE.exists():
    save_draft_queue()

community_message = st.text_area(
    "Community member's message",
    placeholder="Example: My game freezes whenever I launch it",
    height=120,
)

if st.button("Generate draft", type="primary", disabled=not community_message.strip()):
    with st.spinner("The local AI is preparing a draft..."):
        try:
            community_guide = GUIDE_FILE.read_text(encoding="utf-8")
            response = ollama.chat(
                model="qwen3:1.7b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You help moderators of a fictional gaming Discord community. "
                            "Read the member's message, choose a category (Event question, "
                            "Account help, Bug report, or General message), and draft a short, "
                            "kind reply. Ask one follow-up question only when needed to help; "
                            "never ask for information already provided in the reply. Use only the facts "
                            "in the COMMUNITY GUIDE below. Do not invent event times, policies, "
                            "or support steps. If the guide does not contain an answer, say a "
                            "moderator can confirm it, and do not infer where or when updates "
                            "will be shared. Do not promise account recovery or that the team will "
                            "investigate, fix, escalate, or reply by a certain time. Never ask "
                            "users to share or check passwords, security codes, email addresses, "
                            "or other private account details. For login problems, ask only for "
                            "a non-sensitive description of the error, or say a human moderator "
                            "can share the approved recovery steps. Do not invent recovery steps. "
                            "If the issue needs a decision or private support, say a human moderator can follow up. Label the result as "
                            "Category and Suggested reply. This is a draft for moderator review."
                            f"\n\nCOMMUNITY GUIDE:\n{community_guide}"
                        ),
                    },
                    {"role": "user", "content": community_message},
                ],
            )
            st.session_state["draft_queue"].append(
                {
                    "message": community_message,
                    "reply": response.message.content,
                    "status": "Needs review",
                }
            )
            save_draft_queue()
        except Exception as error:
            st.error(
                "I couldn't reach the local AI. Check that Ollama is open and "
                "that the qwen3:1.7b model has finished downloading."
            )
            st.caption(f"Details: {error}")

if st.session_state["draft_queue"]:
    st.subheader("Review queue")
    queue = st.session_state["draft_queue"]
    needs_review = sum(item["status"] == "Needs review" for item in queue)
    reviewed = sum(item["status"] == "Reviewed" for item in queue)
    st.write(f"{len(queue)} drafts · {needs_review} need review · {reviewed} reviewed")

    for number, item in enumerate(queue, start=1):
        st.markdown(f"### Draft {number} · {item['status']}")
        st.caption(f"Member message: {item['message']}")
        st.text_area(
            "Edit the draft before using it",
            value=item["reply"],
            key=f"draft_reply_{number}",
            height=160,
            disabled=item["status"] == "Reviewed",
            on_change=save_draft_edit,
            args=(number - 1,),
        )

        if item["status"] == "Needs review":
            if st.button("Mark as reviewed", key=f"mark_reviewed_{number}"):
                item["reply"] = st.session_state[f"draft_reply_{number}"]
                item["status"] = "Reviewed"
                save_draft_queue()
                st.rerun()
        elif st.button("Reopen for review", key=f"reopen_review_{number}"):
            item["status"] = "Needs review"
            save_draft_queue()
            st.rerun()

    st.caption("This prototype does not send messages to Discord.")

st.divider()
st.caption("Learning project · AI suggestions need human review")
