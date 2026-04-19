---
name: office365-graph-secure
description: >
  Use Microsoft Graph to communicate with Office 365 and Microsoft 365 through
  bundled Python scripts that keep access tokens out of the model context by
  reading them only from a local token file. Use when an agent must read or
  write mail, calendar, files, users, Teams, SharePoint, or other Graph
  resources without exposing tokens.
---

# Office 365 Graph Secure

Use this skill when the task requires Office 365 or Microsoft 365 access through
Microsoft Graph.

## Security Rules

- Never ask the user to paste an access token into chat.
- Never pass tokens on the command line, in JSON payloads, or in files that you
  later read back into the model.
- Only use the bundled Python script for Graph calls. It reads the access token
  only from `MS_GRAPH_ACCESS_TOKEN_FILE` and redacts token-shaped strings from
  output.
- Never add an `Authorization` header manually. The script injects it internally.

## Authentication

The only supported authentication method is `access-token-file`.

- Store the token in a local file referenced by `MS_GRAPH_ACCESS_TOKEN_FILE`.
- The script requires owner-only permissions on that file.
- The file may contain either a raw token string or JSON with
  `{"access_token":"..."}`.

## Required Environment Variables

- `MS_GRAPH_ACCESS_TOKEN_FILE`

Optional:

- `MS_GRAPH_API_VERSION`
- `MS_GRAPH_TIMEOUT_SEC`
- `MS_GRAPH_USER_AGENT`

## Workflow

1. Make sure `MS_GRAPH_ACCESS_TOKEN_FILE` points to the local token file.
2. Run the doctor command first to confirm the required env var exists without
   printing any secret values.
3. Ensure the token already contains the least-privilege Graph scopes needed for
   the task.
4. Call Microsoft Graph through the bundled script.
5. Share only the sanitized response fields back to the user.
6. If the API returns `@odata.nextLink`, follow it with another `request` call
   against that absolute next-link URL.

## Scope Cheat Sheet

Use these delegated scopes as the default starting point:

- `/me` or profile basics: `User.Read`
- `/me/messages` or inbox queries: `Mail.ReadBasic`
- `/me/messages` when message body or richer properties are required: `Mail.Read`
- `/me/sendMail`: `Mail.Send`
- `/me/calendar/calendarView` or upcoming events: `Calendars.ReadBasic`
- `/me/events` when fuller calendar data is required: `Calendars.Read`
- `/me/joinedTeams`: `Team.ReadBasic.All`
- `/teams/{team-id}/primaryChannel` or channel lookups: `Channel.ReadBasic.All`
- `/sites/root` or `/sites/{hostname}:/{relative-path}`: `Sites.Read.All`
- `/sites/{siteId}/drives`: `Files.Read` or `Sites.Read.All`
- `/me/drive` or OneDrive reads: `Files.Read`
- `/me/memberOf`: `User.Read`

Escalate scopes only when the endpoint or operation requires it.

## Agent Recipes

Use these patterns before improvising:

- Mail: check current user:
  `request --path /me`
- Mail: list unread inbox items:
  `request --path '/me/mailFolders/Inbox/messages?$filter=isRead%20eq%20false&$top=10&$select=subject,from,receivedDateTime,isRead,webLink'`
- Mail: send a message:
  `request --method POST --path /me/sendMail --body-file /absolute/path/to/send-mail.json`
- Calendar: read upcoming events in a time window:
  `request --path '/me/calendar/calendarView?startDateTime=2026-04-19T00:00:00Z&endDateTime=2026-04-26T00:00:00Z&$top=10&$select=subject,start,end,location,webLink' --header 'Prefer=outlook.timezone=\"Europe/Berlin\"'`
- Calendar: create an event:
  `request --method POST --path /me/events --body-file /absolute/path/to/create-event.json`
- Teams: list joined teams:
  `request --path /me/joinedTeams`
- Teams: get the General channel for a team:
  `request --path '/teams/{team-id}/primaryChannel?$select=id,displayName,webUrl'`
- SharePoint: get the tenant root site:
  `request --path '/sites/root?$select=id,displayName,webUrl'`
- SharePoint: get a site by path:
  `request --path '/sites/{hostname}:/{server-relative-path}?$select=id,displayName,webUrl'`
- SharePoint: list document libraries for a site:
  `request --path '/sites/{site-id}/drives?$top=10&$select=id,name,webUrl,driveType'`
- Follow paging:
  reuse the exact `@odata.nextLink` value as `--path 'https://graph.microsoft.com/...'`

## Commands

Check configuration:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py doctor \
  # requires MS_GRAPH_ACCESS_TOKEN_FILE to be set
```

Basic request example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path '/me/messages?$top=10'
```

Create or update the local token file safely:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/manage_token_file.py \
  --print-export
```

Create or update the token file from stdin:

```bash
printf '%s' 'YOUR_TOKEN_HERE' | \
python3 custom-prompts/skills/office365-graph-secure/scripts/manage_token_file.py \
  --stdin \
  --print-export
```

Send mail example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method POST \
  --path /me/sendMail \
  --body-file /absolute/path/to/send-mail.json
```

Calendar view example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --header 'Prefer=outlook.timezone="Europe/Berlin"' \
  --path '/me/calendar/calendarView?startDateTime=2026-04-19T00:00:00Z&endDateTime=2026-04-26T00:00:00Z&$top=10&$select=subject,start,end,location,webLink'
```

Teams example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path /me/joinedTeams
```

SharePoint example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path '/sites/root?$select=id,displayName,webUrl'
```

Use `--graph-version beta` only when the user explicitly needs preview APIs.
Default to `v1.0` for production-safe behavior.

## Request Construction Notes

- Graph requests follow the documented pattern:
  `{HTTP method} https://graph.microsoft.com/{version}/{resource}?{query}`
- The script accepts:
  - relative Graph paths such as `/me/messages?$top=10`
  - versioned paths such as `/beta/teams`
  - absolute `https://graph.microsoft.com/...` next links
- Prefer `$select` to reduce payload size and token exposure risk in returned
  content.
- Prefer `$top` on list endpoints to keep responses small and manageable.
- For calendar time-window queries, prefer `/calendarView` over `/events` when
  you need expanded occurrences within a concrete date range.
- For SharePoint under delegated auth, prefer `/sites/root` or
  `/sites/{hostname}:/{relative-path}` over `/sites`, because listing all sites
  is not generally available for delegated auth.
- Use `--header KEY=VALUE` for safe extra headers like `Prefer`, but never
  attempt to set `Authorization`.
- Use `--body-file` or `--body-json` for JSON request bodies.
- Keep the token file outside the repo and restrict it to owner-only
  permissions such as `chmod 600`.
- Use `scripts/manage_token_file.py` to create or rotate the token file safely
  without putting the token on the command line.

## Failure Handling

- `401`: token expired, malformed, or wrong audience. Refresh or replace the
  token, then retry.
- `403`: token is valid but missing Graph permissions or consent. Check the
  scope needed for the endpoint.
- `404`: verify the resource path and whether the endpoint is available for the
  signed-in user or auth mode.
- `429`: honor `retry-after` from the response metadata before retrying.
- `@odata.nextLink`: do not reconstruct it manually; pass it back exactly.
- For mail failures on `/me/messages`, the token often has `User.Read` but not
  `Mail.ReadBasic` or `Mail.Read`.
- For Teams failures on `/me/joinedTeams`, the token often lacks
  `Team.ReadBasic.All`.
- For SharePoint failures on `/sites/root` or site-path lookups, the token
  often lacks `Sites.Read.All`.

Read these references when needed:

- `references/api-docs.md`
- `references/security-and-auth.md`
- `references/research-notes.md`
