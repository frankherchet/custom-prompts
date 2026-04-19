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
- App-only auth:
  client credentials flow against
  `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`
  with scope `https://graph.microsoft.com/.default`
- Delegated auth for CLI/headless work:
  device code flow
- Least-privilege rule:
  request only the Graph permissions needed for the task

## Security Contract Of This Skill

- Tokens are acquired only inside `scripts/graph_secure.py`.
- Client secrets are read only from process environment variables.
- Tokens and secrets are never accepted on the command line.
- The script rejects manual `Authorization` headers.
- Token-like strings are redacted from stdout and stderr.
- The doctor command reports only presence or absence of required env vars.
- Default behavior is stateless: tokens stay in process memory and are not
  persisted to disk by this skill.
- Optional manual token sources are:
  - `MS_GRAPH_ACCESS_TOKEN` via `access-token-env`
  - `MS_GRAPH_ACCESS_TOKEN_FILE` via `access-token-file`
- File-based tokens must live in a regular file with owner-only permissions.
- `scripts/manage_token_file.py` writes the token file atomically and enforces
  a dedicated secret directory with owner-only permissions.
- `browser-login` uses OAuth 2.0 authorization code flow with PKCE against a
  localhost redirect URI and stores the token cache in a private local JSON
  file.

## Auth Mode Selection

Preferred order for agents:

- `access-token-file` when a valid delegated token is already stored locally
- `browser-login` when delegated auth is needed and the app registration exists
- `device-code` when delegated auth is needed but browser-login is unavailable
- `access-token-env` only for short-lived manual testing
- `client-credentials` only for app-only endpoints

Use `client-credentials` when:

- the task is daemon-style or tenant-wide
- the endpoint supports application permissions
- no signed-in user context is required

Use `device-code` when:

- the endpoint requires `/me/...`
- mail/calendar/file actions must happen on behalf of a user
- delegated permissions are the natural least-privilege choice

Use `browser-login` when:

- you want a normal browser sign-in instead of a device code
- you want token refresh and cache reuse across requests
- you can configure a localhost redirect URI in the app registration

Use `access-token-env` or `access-token-file` when:

- a token was already obtained outside the skill
- you need a simple local handoff without re-running login
- you can keep the token out of chat, out of CLI args, and out of repo files

## Common Delegated Scopes

Default endpoint-to-scope map:

- `/me`: `User.Read`
- `/me/messages`: `Mail.Read`
- `/me/sendMail`: `Mail.Send`
- `/me/events`: `Calendars.Read`
- `/me/drive`: `Files.Read`
- `/me/memberOf`: `User.Read`

Prefer the narrowest scope that satisfies the task.

## Common Failure Patterns

- `invalid_client`:
  wrong app ID, tenant, or client secret
- `interaction_required` or consent errors:
  delegated permission or admin consent is missing
- `Authorization_RequestDenied`:
  the app registration lacks the needed Graph permission
- `ErrorAccessDenied` on `/me/messages`:
  the token is valid but missing `Mail.Read`
- `InvalidAuthenticationToken`:
  token is expired, malformed, or for the wrong audience
- `429`:
  throttling; check `retry-after`

## Browser Login App Setup

For `browser-login`, configure the Entra app registration with:

- public client flows enabled
- delegated Graph scopes such as `User.Read`
- a redirect URI matching `MS_GRAPH_REDIRECT_URI`

Default redirect URI:

- `http://127.0.0.1:8765/callback`

## Source URLs

- https://learn.microsoft.com/en-us/graph/use-the-api
- https://learn.microsoft.com/en-us/graph/auth-v2-service
- https://learn.microsoft.com/en-us/entra/identity-platform/scopes-oidc
- https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code
- https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow
