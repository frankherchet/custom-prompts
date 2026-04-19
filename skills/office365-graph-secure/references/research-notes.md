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

## App-Only Access

Source:
https://learn.microsoft.com/en-us/graph/auth-v2-service

Takeaways:

- App-only access uses the OAuth 2.0 client credentials flow.
- The token request goes to
  `https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token`.
- For Microsoft Graph app permissions, the token request uses
  `scope=https://graph.microsoft.com/.default`.
- This mode is appropriate for service-to-service automation.

## Scopes And Least Privilege

Source:
https://learn.microsoft.com/en-us/entra/identity-platform/scopes-oidc

Takeaways:

- If the resource identifier is omitted from the scope, Microsoft Graph is
  assumed.
- Least privilege matters; only request the delegated scopes or application
  permissions required for the task.
- `.default` is required for client credentials and maps to the permissions
  already granted to the app registration.

## Device Code Flow

Source:
https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-device-code

Takeaways:

- Device code flow is appropriate for CLI and headless tools.
- The user signs in on a second device using a verification URL and short code.
- This flow keeps the login interaction outside the CLI process.
- It is a good fit for delegated Graph access from an agent-driven terminal.

## Authorization Code Flow With PKCE

Source:
https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow

Takeaways:

- Authorization code flow with PKCE is appropriate for browser-based delegated
  sign-in from a local client.
- The client sends a `code_challenge` at authorization time and the matching
  `code_verifier` at token exchange time.
- Redirect URIs must exactly match the registered app configuration.
- A localhost redirect URI is the right fit for a local CLI that opens the
  browser and receives the callback directly.
