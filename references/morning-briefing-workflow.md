# Morning Briefing Workflow

Use this workflow for a secretary-style Office 365 start-of-day briefing such
as:

- what's on today
- which meetings matter most
- which unread mails likely need action soon
- whether the user likely needs to prepare something

## Core Rule

Use the existing `office365-graph-secure` skill as the only Microsoft Graph
capability layer. Do not invent a second auth flow, a second Graph wrapper, or
duplicate Office 365 domain knowledge here.

## Security

- Never ask the user to paste a token into chat.
- Never pass a token on the command line.
- Only use `skills/office365-graph-secure/scripts/graph_secure.py` for Graph
  calls.
- Keep the token-file-only model intact through `MS_GRAPH_ACCESS_TOKEN_FILE`.

## Workflow

1. Use `office365-graph-secure`.
2. Read only the needed references from that skill, usually:
   - `skills/office365-graph-secure/references/calendar.md`
   - `skills/office365-graph-secure/references/mail.md`
   - `skills/office365-graph-secure/references/security-and-auth.md` only when
     auth or scope failures occur
3. If the environment looks uncertain, run:

```bash
python3 skills/office365-graph-secure/scripts/graph_secure.py doctor
```

4. For today's agenda, query `/me/calendar/calendarView` for the relevant local
   day window.
5. For urgent mail candidates, query unread Inbox mail from a recent time
   window, usually the last 2 days unless the user asks otherwise.
6. Return a concise briefing, not a raw API dump.
7. If a call fails and the skill is missing guidance, tell the user what should
   be improved in the skill.

## Calendar Query

Prefer `/me/calendar/calendarView` with compact fields such as:

- `subject`
- `bodyPreview`
- `organizer`
- `attendees`
- `start`
- `end`
- `location`
- `importance`
- `responseStatus`
- `webLink`

Use `Prefer: outlook.timezone="..."` when the user's local timezone matters.

## Mail Query

Prefer unread Inbox mail with compact fields such as:

- `subject`
- `from`
- `receivedDateTime`
- `importance`
- `flag`
- `bodyPreview`
- `inferenceClassification`
- `toRecipients`
- `ccRecipients`
- `webLink`

## Reasoning Rules

Be conservative. Do not overstate urgency or importance.

When ranking meetings, weigh signals like:

- high importance
- organizer relevance
- external attendees
- starts soon
- response still pending
- subject or preview suggests a customer, decision, incident, interview, or review

When ranking mail, weigh signals like:

- high importance
- sender relevance
- urgent wording
- direct recipient versus CC
- recent arrival
- focused inbox classification
- flagged message

De-prioritize obvious newsletters, automated notifications, and low-signal bulk
messages when that can be inferred safely.

## Output Shape

Default to these sections:

1. Today's agenda
2. Important meetings
3. Emails that may need prompt response
4. Preparation notes

For each important item, include a short reason.

If the data is insufficient to conclude that something is important or requires
preparation, say that explicitly.
