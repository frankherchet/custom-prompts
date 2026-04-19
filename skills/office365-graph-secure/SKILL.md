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

## Skill Maintenance Rule

If the skill appears wrong, incomplete, outdated, or missing a safe workflow,
do not stop at the immediate runtime error. Tell the user what part of the
skill should be improved and propose a concrete fix.

When proposing a skill fix:

- state what failed or was missing
- explain whether the problem is in `SKILL.md`, a reference file, or a script
- propose the smallest useful change that would prevent the problem next time
- if you can already infer the correct improvement, offer to patch the skill
  directly
- keep the token-file-only security model intact unless the user explicitly
  asks to redesign it

## Scope Cheat Sheet

Use these delegated scopes as the default starting point:

- `/me` or profile basics: `User.Read`
- `/me/messages` or inbox queries: `Mail.ReadBasic`
- `/me/messages` when message body or richer properties are required: `Mail.Read`
- `/me/messages?$search="..."`: `Mail.ReadBasic` or `Mail.Read`
- `/me/sendMail`: `Mail.Send`
- `/me/calendar/calendarView` or upcoming events: `Calendars.ReadBasic`
- `/me/events` when fuller calendar data is required: `Calendars.Read`
- `/me/joinedTeams`: `Team.ReadBasic.All`
- `/me/chats` or `/chats/{chat-id}`: `Chat.ReadBasic`
- `/chats/{chat-id}/messages` reads: `Chat.Read`
- `/chats` create chat: `Chat.Create`
- `/teams/{team-id}/primaryChannel` or channel lookups: `Channel.ReadBasic.All`
- `/teams/{team-id}` team settings reads: `TeamSettings.Read.All`
- `/teams` create team: `Team.Create`
- `/teams/{team-id}/channels/{channel-id}/messages` send channel message:
  Teams-specific delegated send permissions such as `ChannelMessage.Send`
- `/chats/{chat-id}/messages` send chat message:
  the current Microsoft Learn send-message page also lists
  `ChannelMessage.Send`
- `/sites/root` or `/sites/{hostname}:/{relative-path}`: `Sites.Read.All`
- `/sites/{siteId}/drives`: `Files.Read` or `Sites.Read.All`
- `/sites/{site-id}/drive/root/search(q='...')`: `Files.Read` or `Sites.Read.All`
- `/sites/{site-id}/lists/{list-id}/items`: `Sites.Read.All`
- `/sites/{site-id}/pages` or `/sites/{site-id}/pages/microsoft.graph.sitePage`:
  `Sites.Read.All`
- `/sites/{site-id}/pages/{page-id}` or
  `/sites/{site-id}/pages/{page-id}/microsoft.graph.sitePage/webparts`:
  `Sites.Read.All`
- `/sites/{site-id}/sites`: `Sites.Read.All`
- `/search/query` for SharePoint content search:
  Microsoft Learn lists `Sites.Read.All` and `Files.Read.All` among supported
  delegated permissions for this API; use the narrowest permission that fits
  the entity type you are searching
- `/me/drive` or OneDrive reads: `Files.Read`
- `/me/memberOf`: `User.Read`

Escalate scopes only when the endpoint or operation requires it.

## Agent Recipes

Use these patterns before improvising:

- Mail: check current user:
  `request --path /me`
- Mail: list unread inbox items:
  `request --path '/me/mailFolders/Inbox/messages?$filter=isRead%20eq%20false&$top=10&$select=subject,from,receivedDateTime,isRead,webLink'`
- Mail: list messages from one sender:
  `request --path "/me/messages?\$filter=from/emailAddress/address%20eq%20'user@example.com'&\$top=20&\$select=subject,from,receivedDateTime,webLink"`
- Mail: search messages with full-text or KQL:
  `request --path '/me/messages?$search=\"hello world\"&$select=subject,from,receivedDateTime,bodyPreview,webLink'`
- Mail: send a message:
  `request --method POST --path /me/sendMail --body-file /absolute/path/to/send-mail.json`
- Mail: create a draft message:
  `request --method POST --path /me/messages --body-file /absolute/path/to/create-draft.json`
- Mail: update an existing draft:
  `request --method PATCH --path '/me/messages/{message-id}' --body-file /absolute/path/to/update-draft.json`
- Mail: send an existing draft:
  `request --method POST --path '/me/messages/{message-id}/send'`
- Mail: add a small attachment to a draft:
  `request --method POST --path '/me/messages/{message-id}/attachments' --body-file /absolute/path/to/add-attachment.json`
- Calendar: read upcoming events in a time window:
  `request --path '/me/calendar/calendarView?startDateTime=2026-04-19T00:00:00Z&endDateTime=2026-04-26T00:00:00Z&$top=10&$select=subject,start,end,location,webLink' --header 'Prefer=outlook.timezone=\"Europe/Berlin\"'`
- Calendar: list tomorrow's meetings:
  `request --path '/me/calendar/calendarView?startDateTime=2026-04-20T00:00:00Z&endDateTime=2026-04-21T00:00:00Z&$top=20&$select=subject,start,end,organizer,location,webLink' --header 'Prefer=outlook.timezone=\"Europe/Berlin\"'`
- Calendar: list event masters with selected fields:
  `request --path '/me/events?$select=subject,body,bodyPreview,organizer,attendees,start,end,location,webLink&$top=20' --header 'Prefer=outlook.body-content-type=\"text\"'`
- Calendar: create an event:
  `request --method POST --path /me/events --body-file /absolute/path/to/create-event.json`
- Teams: list joined teams:
  `request --path /me/joinedTeams`
- Teams chat: list chats:
  `request --path '/me/chats?$top=10&$expand=lastMessagePreview'`
- Teams chat: get chat details:
  `request --path '/chats/{chat-id}?$select=id,chatType,topic,webUrl,lastUpdatedDateTime'`
- Teams chat: create a chat:
  `request --method POST --path /chats --body-file /absolute/path/to/create-chat.json`
- Teams chat: list messages:
  `request --path '/chats/{chat-id}/messages?$top=10'`
- Teams chat: list messages with system-event expansion:
  `request --path '/chats/{chat-id}/messages?$top=10' --header 'Prefer=include-unknown-enum-members'`
- Teams chat: send a message:
  `request --method POST --path '/chats/{chat-id}/messages' --body-file /absolute/path/to/send-chat-message.json`
- Teams: get team details:
  `request --path '/teams/{team-id}?$select=id,displayName,description,webUrl'`
- Teams: get the General channel for a team:
  `request --path '/teams/{team-id}/primaryChannel?$select=id,displayName,webUrl'`
- Teams: create a channel:
  `request --method POST --path '/teams/{team-id}/channels' --body-file /absolute/path/to/create-channel.json`
- Teams: send a channel message:
  `request --method POST --path '/teams/{team-id}/channels/{channel-id}/messages' --body-file /absolute/path/to/send-channel-message.json`
- SharePoint: get the tenant root site:
  `request --path '/sites/root?$select=id,displayName,webUrl'`
- SharePoint: get a site by path:
  `request --path '/sites/{hostname}:/{server-relative-path}?$select=id,displayName,webUrl'`
- SharePoint: list document libraries for a site:
  `request --path '/sites/{site-id}/drives?$top=10&$select=id,name,webUrl,driveType'`
- SharePoint: search within a site's default document library:
  `request --path "/sites/{site-id}/drive/root/search(q='quarterly budget')?$top=10&$select=id,name,webUrl,parentReference,lastModifiedDateTime"`
- SharePoint: list folder children by path inside a site drive:
  `request --path "/sites/{site-id}/drive/root:/Shared Documents/Folder:/children?$top=20&$select=id,name,webUrl,folder,file,lastModifiedDateTime"`
- SharePoint: list SharePoint list items with selected fields:
  `request --path "/sites/{site-id}/lists/{list-id}/items?expand=fields(select=Title,Modified,Editor)&$top=20"`
- SharePoint: get one SharePoint list item with fields:
  `request --path "/sites/{site-id}/lists/{list-id}/items/{item-id}?expand=fields"`
- SharePoint pages: list site pages:
  `request --path '/sites/{site-id}/pages/microsoft.graph.sitePage?$top=20&$select=id,name,title,webUrl,lastModifiedDateTime'`
- SharePoint pages: get one page:
  `request --path '/sites/{site-id}/pages/{page-id}/microsoft.graph.sitePage?$select=id,name,title,description,webUrl,lastModifiedDateTime'`
- SharePoint pages: get page content layout:
  `request --path '/sites/{site-id}/pages/{page-id}/microsoft.graph.sitePage?$expand=canvasLayout'`
- SharePoint pages: list webparts:
  `request --path '/sites/{site-id}/pages/{page-id}/microsoft.graph.sitePage/webparts'`
- SharePoint: list subsites under a site:
  `request --path '/sites/{site-id}/sites?$select=id,displayName,webUrl'`
- SharePoint: cross-search sites, files, or list items with Microsoft Search:
  `request --method POST --path /search/query --body-file /absolute/path/to/sharepoint-search.json`
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

Create draft message example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method POST \
  --path /me/messages \
  --body-file /absolute/path/to/create-draft.json
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

Add small attachment to draft example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method POST \
  --path '/me/messages/{message-id}/attachments' \
  --body-file /absolute/path/to/add-attachment.json
```

Mail search example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path '/me/messages?$search=\"hello world\"&$select=subject,from,receivedDateTime,bodyPreview,webLink'
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

Teams chat example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path '/me/chats?$top=10&$expand=lastMessagePreview'
```

Teams send-message example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method POST \
  --path '/teams/{team-id}/channels/{channel-id}/messages' \
  --body-file /absolute/path/to/send-channel-message.json
```

SharePoint example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path '/sites/root?$select=id,displayName,webUrl'
```

SharePoint search example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path "/sites/{site-id}/drive/root/search(q='quarterly budget')?\$top=10&\$select=id,name,webUrl,parentReference,lastModifiedDateTime"
```

Microsoft Search example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method POST \
  --path /search/query \
  --body-file /absolute/path/to/sharepoint-search.json
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
- When using `/me/messages?$search=...`, prefer returning compact fields such as
  `subject`, `from`, `receivedDateTime`, `bodyPreview`, and `webLink`.
- Microsoft documents KQL-style message search terms like `from:alice`,
  `subject:budget`, and plain quoted full-text search. Prefer `$search` over
  improvised client-side filtering when the user asks for keyword search.
- For `/me/messages` filters, prefer server-side predicates on
  `receivedDateTime` and `from/emailAddress/address` when the question is about
  time windows or a sender.
- For calendar time-window queries, prefer `/calendarView` over `/events` when
  you need expanded occurrences within a concrete date range.
- For "meetings tomorrow" or other bounded schedule questions, use
  `/me/calendar/calendarView` with exact `startDateTime` and `endDateTime`
  values for the user-facing day in the intended timezone.
- `Prefer: outlook.timezone="Europe/Berlin"` affects the response timezone, but
  Microsoft documents that the timezone offset in `startDateTime` and
  `endDateTime` controls how those query bounds are interpreted.
- `Prefer: outlook.body-content-type="text"` is useful when you need plain-text
  event or message bodies instead of HTML-heavy payloads.
- For SharePoint under delegated auth, prefer `/sites/root` or
  `/sites/{hostname}:/{relative-path}` over `/sites`, because listing all sites
  is not generally available for delegated auth.
- For SharePoint information gathering, prefer this sequence:
  resolve the site, enumerate drives or lists, run the narrowest search that
  fits the task, then fetch only the fields needed for the final summary.
- Use `/sites/{site-id}/drive/root/search(q='...')` when the user already knows
  the target site and you want document-library search scoped to that site.
- Use `POST /search/query` when the user needs broader SharePoint discovery
  across `site`, `driveItem`, or `listItem` entities.
- After locating a file hit, prefer `webUrl`, `name`, `parentReference`,
  timestamps, and selected metadata over downloading raw file content unless
  the user explicitly asks for file bytes.
- Do not surface `@microsoft.graph.downloadUrl` by default. The docs describe it
  as a short-lived unauthenticated download URL, so treat it as sensitive output
  and only expose it if the user explicitly asks for a direct download link.
- Use `--header KEY=VALUE` for safe extra headers like `Prefer`, but never
  attempt to set `Authorization`.
- Use `--body-file` or `--body-json` for JSON request bodies.
- Keep the token file outside the repo and restrict it to owner-only
  permissions such as `chmod 600`.
- Use `scripts/manage_token_file.py` to create or rotate the token file safely
  without putting the token on the command line.
- For message composition, read `references/message-resource.md` before creating
  draft/send payloads from scratch.
- For Teams resource-model and workflow questions, read `references/teams-api.md`
  before inventing team/channel/chat payloads from scratch.
- For SharePoint, document-library, or OneDrive/drive search tasks, read
  `references/sharepoint-search.md` before inventing search payloads or
  traversal flows from scratch.
- For SharePoint page discovery or page-content extraction tasks, read
  `references/sharepoint-pages.md` before inventing page or webpart endpoints
  from scratch.
- Do not confuse Teams direct or group chats with team channels. Use `/chats`
  for direct/group chat workflows and `/teams/.../channels/...` for channel
  workflows.

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
- For mail search failures on `/me/messages?$search=...`, the token often lacks
  `Mail.ReadBasic` or `Mail.Read`, or the query needs to be expressed in valid
  message-search syntax instead of arbitrary OData.
- For Teams failures on `/me/joinedTeams`, the token often lacks
  `Team.ReadBasic.All`.
- For Teams chat failures on `/me/chats` or `/chats/{chat-id}/messages`, the
  token often lacks `Chat.ReadBasic` or `Chat.Read`.
- For Teams chat creation failures on `/chats`, the token often lacks
  `Chat.Create`.
- For Teams write failures on channel-message or channel-creation endpoints, the
  token often lacks Teams-specific delegated write permissions.
- For Teams send-message failures on `/chats/{chat-id}/messages`, check the
  current delegated send permission documented by Microsoft Learn when the
  token was minted.
- For SharePoint drive-search failures on `/sites/{site-id}/drive/root/search`,
  the token often lacks `Files.Read` or `Sites.Read.All`.
- For SharePoint list-item failures on `/sites/{site-id}/lists/{list-id}/items`,
  the token often lacks `Sites.Read.All`.
- For SharePoint page or webpart failures on `/sites/{site-id}/pages...`, the
  token often lacks `Sites.Read.All`.
- For Microsoft Search failures on `/search/query`, the token often lacks a
  broader delegated scope such as `Sites.Read.All` or `Files.Read.All` for the
  requested SharePoint entity types.
- For SharePoint failures on `/sites/root` or site-path lookups, the token
  often lacks `Sites.Read.All`.
- If a failure exposes a missing recipe, misleading instruction, or incomplete
  guidance in this skill, propose a concrete skill improvement to the user.

Read these references when needed:

- `references/api-docs.md`
- `references/message-resource.md`
- `references/security-and-auth.md`
- `references/sharepoint-pages.md`
- `references/sharepoint-search.md`
- `references/teams-api.md`
- `references/research-notes.md`
