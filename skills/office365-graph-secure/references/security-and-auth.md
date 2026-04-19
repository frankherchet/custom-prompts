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
- `/me/messages?$search="..."`: `Mail.ReadBasic` or `Mail.Read`
- `/me/sendMail`: `Mail.Send`
- `/me/calendar/calendarView`: `Calendars.ReadBasic`
- `/me/events`: `Calendars.Read`
- `/me/joinedTeams`: `Team.ReadBasic.All`
- `/teams/{team-id}/primaryChannel`: `Channel.ReadBasic.All`
- `/sites/root` or `/sites/{hostname}:/{relative-path}`: `Sites.Read.All`
- `/sites/{siteId}/drives`: `Files.Read` or `Sites.Read.All`
- `/sites/{site-id}/drive/root/search(q='...')`: `Files.Read` or
  `Sites.Read.All`
- `/sites/{site-id}/lists/{list-id}/items`: `Sites.Read.All`
- `/sites/{site-id}/pages` and `/sites/{site-id}/pages/{page-id}`:
  `Sites.Read.All`
- `/sites/{site-id}/pages/{page-id}/microsoft.graph.sitePage/webparts`:
  `Sites.Read.All`
- `/sites/{site-id}/sites`: `Sites.Read.All`
- `/search/query` for SharePoint entities: `Sites.Read.All` or `Files.Read.All`
- `/me/drive`: `Files.Read`
- `/me/memberOf`: `User.Read`

Prefer the narrowest scope that satisfies the task.

## Mail Notes

For Outlook mail tasks, also read:

- `references/mail.md`

That reference covers:

- inbox queries
- sender filters
- message `$search` and KQL usage
- send, draft, and small-attachment flows

## Calendar Notes

For Outlook calendar tasks, also read:

- `references/calendar.md`

That reference covers:

- calendar window queries
- tomorrow-style schedule lookups
- event master listing
- timezone handling

## Teams Notes

For Teams resource-model and workflow tasks, also read:

- `references/teams.md`

That reference covers:

- team, channel, and chat routing
- common Teams management and messaging flows
- send-message patterns
- when to read the deeper `references/teams-api.md` file

## SharePoint Search Notes

For SharePoint, OneDrive for Business, document-library, or list-search tasks,
also read:

- `references/sharepoint-search.md`

That reference covers:

- the relationship between `site`, `drive`, `driveItem`, and `listItem`
- search flows for one site versus broader SharePoint discovery
- Microsoft Search request bodies for `site`, `driveItem`, and `listItem`
- safer result collection patterns for SharePoint content

## SharePoint Page Notes

For SharePoint page, webpart, or subsite tasks, also read:

- `references/sharepoint-pages.md`

That reference covers:

- the difference between `baseSitePage` and `sitePage`
- page metadata, layout, and webpart retrieval
- subsite discovery flows

## Common Failure Patterns

- `ErrorAccessDenied` on `/me/messages`:
  the token is valid but missing `Mail.ReadBasic` or `Mail.Read`
- `ErrorAccessDenied` on `/me/joinedTeams`:
  the token is valid but missing `Team.ReadBasic.All`
- `ErrorAccessDenied` on `/sites/root`:
  the token is valid but missing `Sites.Read.All`
- `ErrorAccessDenied` on `/sites/{site-id}/drive/root/search(...)`:
  the token is valid but missing `Files.Read` or `Sites.Read.All`
- `ErrorAccessDenied` on `/sites/{site-id}/lists/{list-id}/items`:
  the token is valid but missing `Sites.Read.All`
- `ErrorAccessDenied` on `/sites/{site-id}/pages...`:
  the token is valid but missing `Sites.Read.All`
- `ErrorAccessDenied` on `/search/query` for SharePoint entity types:
  the token is valid but missing `Sites.Read.All` or `Files.Read.All`
- `InvalidAuthenticationToken`:
  token is expired, malformed, or for the wrong audience
- `429`:
  throttling; check `retry-after`

## Source URLs

- https://learn.microsoft.com/en-us/graph/use-the-api
- https://learn.microsoft.com/en-us/graph/permissions-reference
