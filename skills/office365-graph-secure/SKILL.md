---
name: office365-graph-secure
description: >
  Use Microsoft Graph to communicate with Office 365 and Microsoft 365 through
  bundled Python scripts that keep OAuth tokens and client secrets out of the
  model context. Use when an agent must read or write mail, calendar, files,
  users, Teams, SharePoint, or other Graph resources without exposing tokens.
---

# Office 365 Graph Secure

Use this skill when the task requires Office 365 or Microsoft 365 access through
Microsoft Graph.

## Security Rules

- Never ask the user to paste an access token, refresh token, or client secret
  into chat.
- Never print or inspect secret-bearing environment variables such as
  `MS_GRAPH_CLIENT_SECRET`.
- Never pass tokens or client secrets on the command line, in JSON payloads, or
  in files that you later read back into the model.
- Only use the bundled Python script for authentication and Graph calls. It
  reads credentials from environment variables, token files, browser-login
  cache, or device-code flow, and it redacts token-shaped strings from output.
- Never add an `Authorization` header manually. The script injects it internally.

## Supported Auth Modes

- `client-credentials`
  Use for daemon or app-only access. Requires Microsoft Graph application
  permissions and admin consent. This mode uses the OAuth 2.0 client
  credentials flow with `https://graph.microsoft.com/.default`.
- `device-code`
  Use for delegated user access, such as `/me/messages`, `/me/events`,
  `/me/drive`, or user-context mail send. This mode shows a verification URL
  and code, then polls until the user finishes sign-in.
- `browser-login`
  Use for delegated user access with a browser sign-in and localhost callback.
  The script opens the Microsoft login page, completes OAuth 2.0 authorization
  code flow with PKCE, and stores a local token cache with owner-only
  permissions for later reuse and refresh.
- `access-token-env`
  Use when a token is already present in the local shell environment as
  `MS_GRAPH_ACCESS_TOKEN`. This is suitable for quick local testing when the
  token was obtained outside the chat and outside the model context.
- `access-token-file`
  Use when a token is stored in a local file referenced by
  `MS_GRAPH_ACCESS_TOKEN_FILE`. The script requires owner-only permissions on
  that file and accepts either a raw token string or JSON with
  `{"access_token":"..."}`.

## Required Environment Variables

For `client-credentials`:

- `MS_GRAPH_TENANT_ID`
- `MS_GRAPH_CLIENT_ID`
- `MS_GRAPH_CLIENT_SECRET`

For `device-code`:

- `MS_GRAPH_TENANT_ID`
- `MS_GRAPH_CLIENT_ID`

For `browser-login`:

- `MS_GRAPH_TENANT_ID`
- `MS_GRAPH_CLIENT_ID`

For `access-token-env`:

- `MS_GRAPH_ACCESS_TOKEN`

For `access-token-file`:

- `MS_GRAPH_ACCESS_TOKEN_FILE`

Optional:

- `MS_GRAPH_AUTH_MODE`
- `MS_GRAPH_API_VERSION`
- `MS_GRAPH_TIMEOUT_SEC`
- `MS_GRAPH_USER_AGENT`
- `MS_GRAPH_SCOPES`
- `MS_GRAPH_REDIRECT_URI`
- `MS_GRAPH_TOKEN_CACHE_FILE`
- `MS_GRAPH_BROWSER_TIMEOUT_SEC`
- `MS_GRAPH_ACCESS_TOKEN`
- `MS_GRAPH_ACCESS_TOKEN_FILE`

## Workflow

1. Choose auth mode in this order:
   - If `MS_GRAPH_ACCESS_TOKEN_FILE` is already configured and the task only
     needs a current delegated token, use `access-token-file`.
   - Otherwise, if browser-login is configured in Entra and the task is
     delegated, use `browser-login`.
   - Otherwise, if delegated auth is needed and browser-login is not available,
     use `device-code`.
   - Use `access-token-env` only for short-lived manual testing.
   - Use `client-credentials` only for daemon/app-only Graph endpoints that do
     not require `/me/...`.
2. Run the doctor command first to confirm the required env vars exist without
   printing any secret values.
3. Choose the least-privilege scope before requesting a new token.
4. Call Microsoft Graph through the bundled script.
5. Share only the sanitized response fields back to the user.
6. If the API returns `@odata.nextLink`, follow it with another `request` call
   against that absolute next-link URL.

## Scope Cheat Sheet

Use these delegated scopes as the default starting point:

- `/me` or profile basics: `User.Read`
- `/me/messages` or inbox queries: `Mail.Read`
- `/me/sendMail`: `Mail.Send`
- `/me/events`: `Calendars.Read`
- `/me/drive` or OneDrive reads: `Files.Read`
- `/me/memberOf`: `User.Read`

Escalate scopes only when the endpoint or operation requires it.

## Agent Recipes

Use these patterns before improvising:

- Check current user:
  `request --path /me`
- List unread inbox items:
  `request --path '/me/mailFolders/Inbox/messages?$filter=isRead%20eq%20false&$top=10&$select=subject,from,receivedDateTime,isRead,webLink'`
- Read upcoming events:
  `request --path '/me/events?$top=10&$select=subject,start,end,location,webLink'`
- Inspect OneDrive root:
  `request --path /me/drive/root`
- Follow paging:
  reuse the exact `@odata.nextLink` value as `--path 'https://graph.microsoft.com/...'`

## Commands

Check configuration:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py doctor \
  --auth-mode client-credentials
```

App-only request example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --auth-mode client-credentials \
  --method GET \
  --path '/users?$top=5'
```

Delegated request example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --auth-mode device-code \
  --scope User.Read \
  --scope Mail.Read \
  --method GET \
  --path '/me/messages?$top=10'
```

Browser login example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py login \
  --scope User.Read
```

Browser login request example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --auth-mode browser-login \
  --method GET \
  --path /me
```

Environment token example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --auth-mode access-token-env \
  --method GET \
  --path /me
```

File token example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --auth-mode access-token-file \
  --method GET \
  --path /me
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
  --auth-mode device-code \
  --scope Mail.Send \
  --method POST \
  --path /me/sendMail \
  --body-file /absolute/path/to/send-mail.json
```

Use `--graph-version beta` only when the user explicitly needs preview APIs.
Default to `v1.0` for production-safe behavior.

## Entra App Registration For Browser Login

For `browser-login`, configure the app registration with:

- `Allow public client flows = Yes`
- Delegated Microsoft Graph permission such as `User.Read`
- A mobile/desktop redirect URI matching `MS_GRAPH_REDIRECT_URI`

Default redirect URI used by the script:

- `http://127.0.0.1:8765/callback`

If you change it, update the app registration and `MS_GRAPH_REDIRECT_URI` to the
same exact value.

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
- Use `--header KEY=VALUE` for safe extra headers like `Prefer`, but never
  attempt to set `Authorization`.
- Use `--body-file` or `--body-json` for JSON request bodies.
- For `access-token-file`, keep the file outside the repo and restrict it to
  owner-only permissions such as `chmod 600`.
- Use `scripts/manage_token_file.py` to create or rotate the token file safely
  without putting the token on the command line.
- For `browser-login`, the token cache defaults to
  `~/.config/codex-secrets/ms-graph-auth.json`.

## Failure Handling

- `401`: token expired, malformed, or wrong audience. Refresh or replace the
  token, then retry.
- `403`: token is valid but missing Graph permissions or consent. Check the
  scope needed for the endpoint.
- `404`: verify the resource path and whether the endpoint is available for the
  signed-in user or auth mode.
- `429`: honor `retry-after` from the response metadata before retrying.
- `@odata.nextLink`: do not reconstruct it manually; pass it back exactly.
- For `Mail.Read` failures on `/me/messages`, the token usually has `User.Read`
  but not mail scopes.

Read these references when needed:

- `references/api-docs.md`
- `references/security-and-auth.md`
- `references/research-notes.md`
