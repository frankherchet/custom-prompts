---
name: morning-briefing
description: >
  Manual slash-invocable morning briefing workflow for Office 365. Use when the
  user explicitly wants a secretary-style summary of today's agenda, important
  meetings, urgent unread email, or likely preparation needs.
argument-hint: "[optional date or special focus]"
disable-model-invocation: true
---

# Morning Briefing

Use this skill only as the manual slash-command entry point for the morning
briefing workflow.

Do not duplicate Microsoft Graph capability or authentication logic here. Use
the existing `office365-graph-secure` skill for all Graph access.

Read the shared workflow reference first:

- `../../references/morning-briefing-workflow.md`

Then use:

- `../office365-graph-secure/SKILL.md`

Read Office 365 references only as needed:

- `../office365-graph-secure/references/calendar.md`
- `../office365-graph-secure/references/mail.md`
- `../office365-graph-secure/references/security-and-auth.md` only for auth or
  permission failures

Return the result as a concise briefing, not a raw API dump.
