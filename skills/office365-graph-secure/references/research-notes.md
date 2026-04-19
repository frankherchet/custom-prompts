# Research Notes

Date: 2026-04-19

## Microsoft Graph Core API Usage

Source:
https://learn.microsoft.com/en-us/graph/use-the-api

Takeaways:

- Microsoft Graph is a REST API rooted at `https://graph.microsoft.com`.
- Requests use `{method} /{version}/{resource}` plus optional query parameters.
- `v1.0` is the production version; `beta` is preview and can break.
- Large result sets page through `@odata.nextLink`.
- Permissions vary by resource and action; write operations often need stronger
  permissions than reads.

## Permissions Reference

Source:
https://learn.microsoft.com/en-us/graph/permissions-reference

Takeaways:

- Least-privilege delegated scopes exist for common Graph endpoints.
- `Mail.ReadBasic`, `Calendars.ReadBasic`, `Team.ReadBasic.All`, and
  `Sites.Read.All` are the key read-oriented scopes used by this skill.
- Permission mismatches are a common cause of `403 ErrorAccessDenied`.
