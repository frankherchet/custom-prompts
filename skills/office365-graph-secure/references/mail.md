# Mail

Use this reference for Outlook mail tasks: inbox reads, sender filters,
full-text or KQL message search, draft workflows, attachments, and send-mail.

Primary docs:

- List messages:
  https://learn.microsoft.com/en-us/graph/api/user-list-messages?view=graph-rest-1.0
- Use `$search` query parameter:
  https://learn.microsoft.com/en-us/graph/search-query-parameter
- Message resource:
  https://learn.microsoft.com/en-us/graph/api/resources/message?view=graph-rest-1.0
- Outlook create/send messages overview:
  https://learn.microsoft.com/en-us/graph/outlook-create-send-messages

## Read This For

- unread inbox summaries
- "which emails came in within the last N days"
- "show mail from sender X"
- keyword or KQL message search
- sending mail
- drafts and small attachments

## Common Scopes

- `/me/messages`: `Mail.ReadBasic`
- `/me/messages` with richer properties or body content: `Mail.Read`
- `/me/messages?$search="..."`: `Mail.ReadBasic` or `Mail.Read`
- `/me/sendMail`: `Mail.Send`

## Common Flows

Check the current user:

- Endpoint:
  `GET /me`

List unread inbox items:

- Endpoint:
  `GET /me/mailFolders/Inbox/messages?$filter=isRead eq false`
- Good fields:
  `subject,from,receivedDateTime,isRead,webLink`

List messages from one sender:

- Endpoint:
  `GET /me/messages?$filter=from/emailAddress/address eq 'user@example.com'`
- Good fields:
  `subject,from,receivedDateTime,webLink`

List messages from the last 2 days:

- Endpoint:
  `GET /me/messages?$filter=receivedDateTime ge 2026-04-18T00:00:00Z`
- Good fields:
  `subject,from,receivedDateTime,isRead,webLink`

Search messages with full-text or KQL:

- Endpoint:
  `GET /me/messages?$search="hello world"`
- Good fields:
  `subject,from,receivedDateTime,bodyPreview,webLink`

Send mail directly:

- Endpoint:
  `POST /me/sendMail`

Create a draft:

- Endpoint:
  `POST /me/messages`

Update an existing draft:

- Endpoint:
  `PATCH /me/messages/{message-id}`

Send an existing draft:

- Endpoint:
  `POST /me/messages/{message-id}/send`

Add a small attachment to a draft:

- Endpoint:
  `POST /me/messages/{message-id}/attachments`

## Recommended Recipes

Unread inbox items:

```bash
python3 skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path '/me/mailFolders/Inbox/messages?$filter=isRead%20eq%20false&$top=10&$select=subject,from,receivedDateTime,isRead,webLink'
```

Messages from one sender:

```bash
python3 skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path "/me/messages?\$filter=from/emailAddress/address%20eq%20'user@example.com'&\$top=20&\$select=subject,from,receivedDateTime,webLink"
```

Message search:

```bash
python3 skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path '/me/messages?$search=\"hello world\"&$select=subject,from,receivedDateTime,bodyPreview,webLink'
```

Send mail:

```bash
python3 skills/office365-graph-secure/scripts/graph_secure.py request \
  --method POST \
  --path /me/sendMail \
  --body-file /absolute/path/to/send-mail.json
```

## Search Guidance

- Microsoft documents KQL-style message search terms like `from:alice`,
  `subject:budget`, `attachment:file.pdf`, and quoted full-text search.
- Prefer `$search` when the user asks for keyword matching.
- Prefer `$filter` when the question is about sender, time window, or simple
  structured predicates.
- When using `/me/messages?$search=...`, prefer compact fields such as
  `subject`, `from`, `receivedDateTime`, `bodyPreview`, and `webLink`.

## Message Composition

Most useful message fields when creating or updating a draft:

- `subject`
- `body`
- `toRecipients`
- `ccRecipients`
- `bccRecipients`
- `replyTo`
- `importance`
- `from`
- `sender`
- `internetMessageHeaders`

Body shape:

```json
{
  "contentType": "HTML",
  "content": "<p>Hello</p>"
}
```

Recipient shape:

```json
{
  "emailAddress": {
    "address": "person@example.com",
    "name": "Person Example"
  }
}
```

Minimal message payload:

```json
{
  "subject": "Subject line",
  "body": {
    "contentType": "HTML",
    "content": "<p>Hello from Graph.</p>"
  },
  "toRecipients": [
    {
      "emailAddress": {
        "address": "recipient@example.com",
        "name": "Recipient Example"
      }
    }
  ]
}
```

Attachment example under 3 MB:

```json
{
  "@odata.type": "#microsoft.graph.fileAttachment",
  "name": "notes.txt",
  "contentType": "text/plain",
  "contentBytes": "SGVsbG8gZnJvbSBHcmFwaC4="
}
```

## Important Behavior

- Microsoft documents that message bodies returned by list operations are HTML
  by default.
- When using `$filter` and `$orderby` together on messages, Microsoft warns
  about `InefficientFilter` if the sort/filter properties are not aligned.
- A draft has `isDraft = true`.
- Drafts are usually stored in the `Drafts` folder.
- Sent messages are usually stored in `Sent Items`.
- `body` can be HTML or text.
- Custom Internet headers can be added only when creating a message and must
  start with `x-`.
- The total combined number of `toRecipients`, `ccRecipients`, and
  `bccRecipients` is limited by Exchange Online sending limits.
- For files larger than 3 MB, use an upload session instead of posting the
  attachment directly.

## Failure Hints

- `403` on `/me/messages` usually means the token lacks `Mail.ReadBasic` or
  `Mail.Read`.
- `403` on `/me/sendMail` usually means the token lacks `Mail.Send`.
- Mail search failures on `/me/messages?$search=...` can also be caused by
  invalid message-search syntax, not only by missing permissions.
