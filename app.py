"""A local dashboard for reviewing AI drafted community replies."""

import json
from pathlib import Path

import ollama
import streamlit as st


DRAFTS_FILE = Path(__file__).with_name("drafts.json")
GUIDE_FILE = Path(__file__).with_name("community_guide.md")
CATEGORY_ACCOUNT_HELP = "Account help"
ACCOUNT_HELP_REPLY = (
    "Please use the game's official account recovery or support process. "
    "If you'd like a moderator to help, share only the non-sensitive error message."
)
CATEGORY_GUIDANCE = {
    "Event question": (
        "Answer using event facts from the community guide only. If the guide omits a date "
        "or detail, say so and refer the member to a moderator."
    ),
    "Bug report": (
        "Ask for the platform, game version, what happened, and the steps before the issue. "
        "Do not promise a fix or investigation."
    ),
    "General message": (
        "Ask one brief clarifying question or suggest a human moderator follow up. "
        "Do not assume what the issue is."
    ),
}


def load_draft_queue():
    if not DRAFTS_FILE.exists():
        return []

    try:
        saved_drafts = json.loads(DRAFTS_FILE.read_text(encoding="utf-8"))
        return saved_drafts if isinstance(saved_drafts, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def classify_message(message):
    text = message.casefold()

    if any(term in text for term in ("login", "log in", "sign in", "sign-in", "account", "password")):
        return "Account help"
    if any(term in text for term in ("event", "community night", "tournament")):
        return "Event question"
    if any(term in text for term in ("bug", "crash", "freeze", "error", "glitch")):
        return "Bug report"
    return "General message"


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


def save_draft_feedback(index, feedback):
    st.session_state["draft_queue"][index]["feedback"] = feedback
    save_draft_queue()


st.set_page_config(page_title="AI Community Assistant", page_icon="🎮")
st.title("🎮 AI Community Assistant")
st.write("Draft helpful replies for a fictional gaming community.")

st.info(
    "This prototype uses a model running on your computer. "
    "Account-help messages use an approved safety reply. "
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
    category = classify_message(community_message)
    with st.spinner("Preparing a moderator draft..."):
        try:
            if category == CATEGORY_ACCOUNT_HELP:
                reply_text = ACCOUNT_HELP_REPLY
            else:
                community_guide = GUIDE_FILE.read_text(encoding="utf-8")
                response = ollama.chat(
                    model="qwen3:1.7b",
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You help moderators of a fictional gaming Discord community. "
                                f"The app selected the category: {category}. Keep this category and "
                                "do not reclassify the message. Follow this category guidance exactly: "
                                f"{CATEGORY_GUIDANCE[category]} "
                                "Write a short, kind reply. Use only facts in the COMMUNITY GUIDE. "
                                "Do not invent event times, policies, or support steps. If the guide "
                                "omits an answer, say a moderator can confirm it. Do not promise the "
                                "team will investigate, fix, escalate, or reply by a certain time. Never "
                                "ask for passwords, security codes, email addresses, or private account "
                                "details. Ask a follow-up only when needed, and never repeat information "
                                "already provided. Output only the suggested reply text, without a "
                                "category heading. This is a draft for moderator review."
                                f"\n\nCOMMUNITY GUIDE:\n{community_guide}"
                            ),
                        },
                        {"role": "user", "content": community_message},
                    ],
                )
                reply_text = response.message.content.strip()
                reply_lines = reply_text.splitlines()
                if reply_lines and reply_lines[0].strip().casefold().startswith("category:"):
                    reply_text = "\n".join(reply_lines[1:]).strip()
                if reply_text.casefold().startswith("suggested reply:"):
                    reply_text = reply_text.partition(":")[2].strip()

            st.session_state["draft_queue"].append(
                {
                    "message": community_message,
                    "reply": f"Category: {category}\nSuggested reply: {reply_text}",
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
    st.caption("Drafts needing review appear first, newest at the top.")

    display_order = sorted(
        range(len(queue)),
        key=lambda index: (queue[index]["status"] == "Reviewed", -index),
    )
    for index in display_order:
        item = queue[index]
        number = index + 1
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

        st.caption("Was this draft helpful?")
        helpful_column, changes_column = st.columns(2)
        with helpful_column:
            helpful_selected = item.get("feedback") == "Helpful"
            helpful_label = "✓ Helpful" if helpful_selected else "Helpful"
            if st.button(
                helpful_label,
                key=f"helpful_{number}",
                type="secondary",
            ):
                save_draft_feedback(number - 1, "Helpful")
                st.rerun()
        with changes_column:
            changes_selected = item.get("feedback") == "Needs changes"
            changes_label = "✓ Needs changes" if changes_selected else "Needs changes"
            if st.button(
                changes_label,
                key=f"needs_changes_{number}",
                type="secondary",
            ):
                save_draft_feedback(number - 1, "Needs changes")
                st.rerun()
        if item.get("feedback") == "Helpful":
            st.success("Feedback saved on this computer: Helpful")
        elif item.get("feedback") == "Needs changes":
            st.warning("Feedback saved on this computer: Needs changes")

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
