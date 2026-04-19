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
- Never add an `Authorization` header manually. The script injects it
  internally.

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

## Core Workflow

1. Make sure `MS_GRAPH_ACCESS_TOKEN_FILE` points to the local token file.
2. Run the doctor command first to confirm the required env var exists without
   printing any secret values.
3. Start with the one domain reference that best matches the task.
4. Ensure the token already contains the least-privilege Graph scopes needed
   for the endpoint.
5. Call Microsoft Graph through the bundled script.
6. Return only the sanitized fields needed for the user-facing answer.
7. If the API returns `@odata.nextLink`, pass that exact absolute URL back as
   `--path` instead of rebuilding it manually.

## Domain Routing

Read only the relevant reference for the current task. Do not bulk-load all
references by default.

Start with one domain reference:

- Mail:
  Read `references/mail.md` for inbox queries, sender filters, message
  `$search`, drafts, attachments, and send-mail.
- Calendar:
  Read `references/calendar.md` for time-window queries, tomorrow-style meeting
  lookups, event listing, and timezone handling.
- Teams:
  Read `references/teams.md` for teams, channels, chats, and message-sending
  workflows.
- SharePoint search:
  Read `references/sharepoint-search.md` for sites, drives, driveItems,
  listItems, and `/search/query`.
- SharePoint pages:
  Read `references/sharepoint-pages.md` for pages, page layout,
  `canvasLayout`, webparts, and subsites.

Read shared references only when needed:

- Shared auth and common failure patterns:
  Read `references/security-and-auth.md` for scope mapping, auth constraints,
  and common access-denied patterns.
- Canonical API description URLs:
  Read `references/api-docs.md` only when the task needs the official Microsoft
  API description link.
- General verification context:
  Read `references/research-notes.md` only when earlier research context is
  actually useful.

Open additional references only if:

- the first domain reference points to them, or
- the task genuinely spans multiple domains

Do not load all references just because they exist.

## Commands

Check configuration:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py doctor
```

Basic request example:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path /me
```

Create or update the local token file safely:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/manage_token_file.py \
  --print-export
```

Create or update the token file from stdin:

Use `--stdin` only for non-interactive tooling that already holds the token
outside chat and outside shell history. Do not put the token directly in the
shell command line.

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
- Use `--header KEY=VALUE` for safe extra headers like `Prefer`, but never
  attempt to set `Authorization`.
- Use `--body-file` or `--body-json` for JSON request bodies.
- Keep the token file outside the repo and restrict it to owner-only
  permissions such as `chmod 600`.
- Use `scripts/manage_token_file.py` to create or rotate the token file safely
  without putting the token on the command line.
- Read the domain reference before improvising endpoint-specific payloads.

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

## Failure Handling

- `401`: token expired, malformed, or wrong audience. Refresh or replace the
  token, then retry.
- `403`: token is valid but missing Graph permissions or consent. Check the
  scope needed for the endpoint.
- `404`: verify the resource path and whether the endpoint is available for the
  signed-in user or auth mode.
- `429`: honor `retry-after` from the response metadata before retrying.
- `@odata.nextLink`: do not reconstruct it manually; pass it back exactly.
- Read `references/security-and-auth.md` for endpoint-to-scope mappings and
  domain-specific failure patterns.
- If a failure exposes a missing recipe, misleading instruction, or incomplete
  guidance in this skill, propose a concrete skill improvement to the user.
