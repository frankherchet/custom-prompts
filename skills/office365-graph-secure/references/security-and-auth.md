# Security And Auth Notes

This skill is built around Microsoft Graph and Microsoft identity platform
guidance, with extra constraints to keep secrets out of the model context.

## Relevant Microsoft Guidance

- Microsoft Graph request pattern:
  `https://graph.microsoft.com/{version}/{resource}?{query-parameters}`
- Preferred production API version:
  `v1.0`
- Preview API version:
  `beta`
- Graph pagination:
  follow `@odata.nextLink`
- Least-privilege rule:
  request only the Graph permissions needed for the task

## Security Contract Of This Skill

- Tokens are read only inside `scripts/graph_secure.py`.
- Tokens and secrets are never accepted on the command line.
- The script rejects manual `Authorization` headers.
- Token-like strings are redacted from stdout and stderr.
- The doctor command reports only presence or absence of required env vars.
- The only supported token source is `MS_GRAPH_ACCESS_TOKEN_FILE`.
- The token file must live in a regular file with owner-only permissions.
- `scripts/manage_token_file.py` writes the token file atomically and enforces
  a dedicated secret directory with owner-only permissions.

## Maintenance Expectation

If this skill fails because the documentation is wrong, a recipe is missing, or
the script does not cover a needed safe path, the agent should tell the user
what to improve in the skill and propose a concrete fix instead of only
reporting the runtime error.

## Auth Mode Selection

The only supported auth path is `access-token-file`.

Use it when:

- a token was already obtained outside the skill
- you can keep the token out of chat and out of CLI args
- the token can be stored in a private local file

## Common Delegated Scopes

Default endpoint-to-scope map:

- `/me`: `User.Read`
- `/me/messages`: `Mail.ReadBasic`
- `/me/messages` for fuller content: `Mail.Read`
- `/me/sendMail`: `Mail.Send`
- `/me/calendar/calendarView`: `Calendars.ReadBasic`
- `/me/events`: `Calendars.Read`
- `/me/joinedTeams`: `Team.ReadBasic.All`
- `/teams/{team-id}/primaryChannel`: `Channel.ReadBasic.All`
- `/sites/root` or `/sites/{hostname}:/{relative-path}`: `Sites.Read.All`
- `/sites/{siteId}/drives`: `Files.Read` or `Sites.Read.All`
- `/me/drive`: `Files.Read`
- `/me/memberOf`: `User.Read`

Prefer the narrowest scope that satisfies the task.

## Message Composition Notes

For Outlook mail composition tasks, also read:

- `references/message-resource.md`

That reference covers:

- `message` payload structure
- the difference between `sendMail` and draft creation
- updating and sending drafts
- adding small attachments to drafts

## Common Failure Patterns

- `ErrorAccessDenied` on `/me/messages`:
  the token is valid but missing `Mail.ReadBasic` or `Mail.Read`
- `ErrorAccessDenied` on `/me/joinedTeams`:
  the token is valid but missing `Team.ReadBasic.All`
- `ErrorAccessDenied` on `/sites/root`:
  the token is valid but missing `Sites.Read.All`
- `InvalidAuthenticationToken`:
  token is expired, malformed, or for the wrong audience
- `429`:
  throttling; check `retry-after`

## Source URLs

- https://learn.microsoft.com/en-us/graph/use-the-api
- https://learn.microsoft.com/en-us/graph/permissions-reference
