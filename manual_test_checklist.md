# Manual test checklist

Use fictional messages only. For each case, click **Generate draft**, review the output, and mark the draft reviewed only after a human has checked it.

## AI behavior

| Example message | Expected result | Result |
| --- | --- | --- |
| `My game freezes whenever I launch it` | Bug report; asks for useful troubleshooting details without promising a fix. | Checked during build |
| `I can't log in to my account` | Account help; asks for a non-sensitive error description, never asks for credentials. | Checked during build |
| `When is Community Night?` | Event question; uses Friday at 7:00 PM UTC and `#party-lobby` from the community guide. | Checked during build |
| `When is the next monthly tournament?` | Does not invent a date; points to a moderator in `#tournament-desk`. | Checked during build; response included a little extra filler |
| `Can someone help me?` | General message; asks for context or suggests a moderator follow-up. | Checked during build |

## Dashboard behavior

- [ ] Edit a draft, mark it reviewed, and confirm the counts update.
- [ ] Reopen a reviewed draft and confirm its status returns to **Needs review**.
- [x] Restart the dashboard and confirm saved drafts and statuses remain in the queue.
- [ ] Confirm the app does not send messages to Discord.
- [ ] Confirm `drafts.json` stays out of Git status before sharing the project.

## Notes

- AI wording can vary between runs, even for the same message. Review meaning and safety, not exact phrasing.
- The local model can miss or partially follow instructions. Keep a human moderator responsible for decisions and messages.
- The current guide is fictional and lives in `community_guide.md`.
