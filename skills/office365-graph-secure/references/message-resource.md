# Message Resource

Use this reference when the task is about composing, drafting, updating, or
sending Outlook mail through the Microsoft Graph `message` resource.

Primary docs:

- Message resource:
  https://learn.microsoft.com/en-us/graph/api/resources/message?view=graph-rest-1.0
- Outlook mail workflow overview:
  https://learn.microsoft.com/en-us/graph/outlook-create-send-messages

## Core Fields

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

## Minimal Message Payload

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

## Common Flows

Create and send immediately:

- Endpoint:
  `POST /me/sendMail`
- Body:
  `{"message": { ...message payload... }}`

Create a draft first:

- Endpoint:
  `POST /me/messages`
- Body:
  the message payload itself

Update a draft:

- Endpoint:
  `PATCH /me/messages/{message-id}`
- Body:
  partial message fields such as `subject`, `body`, or recipients

Send an existing draft:

- Endpoint:
  `POST /me/messages/{message-id}/send`
- Body:
  none

Add a small attachment to a draft:

- Endpoint:
  `POST /me/messages/{message-id}/attachments`
- Body:
  a `fileAttachment`, `itemAttachment`, or `referenceAttachment` payload

## Attachment Example Under 3 MB

```json
{
  "@odata.type": "#microsoft.graph.fileAttachment",
  "name": "notes.txt",
  "contentType": "text/plain",
  "contentBytes": "SGVsbG8gZnJvbSBHcmFwaC4="
}
```

For files larger than 3 MB, use an upload session instead of posting the
attachment directly.

## Important Behavior

- A draft has `isDraft = true`.
- Drafts are usually stored in the `Drafts` folder.
- Sent messages are usually stored in `Sent Items`.
- `body` can be HTML or text.
- Custom Internet headers can be added only when creating a message and must
  start with `x-`.
- The total combined number of `toRecipients`, `ccRecipients`, and
  `bccRecipients` is limited by Exchange Online sending limits.

## Agent Guidance

Prefer:

- `POST /me/sendMail` when the user wants to send immediately
- draft creation plus patch plus send when the user wants review, attachments,
  iterative edits, or explicit draft control

If the user asks to "create a message", clarify whether they mean:

- create a draft message, or
- send a message immediately
