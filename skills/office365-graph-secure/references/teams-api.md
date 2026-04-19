# Teams API

Use this reference when the task is about Microsoft Teams resources rather than
generic SharePoint or mail access.

Primary docs:

- Teams API overview:
  https://learn.microsoft.com/en-us/graph/api/resources/teams-api-overview?view=graph-rest-1.0
- Team resource:
  https://learn.microsoft.com/en-us/graph/api/resources/team?view=graph-rest-1.0
- Chat resource:
  https://learn.microsoft.com/en-us/graph/api/resources/chat?view=graph-rest-1.0
- Channel resource:
  https://learn.microsoft.com/en-us/graph/api/resources/channel?view=graph-rest-1.0
- chatMessage resource:
  https://learn.microsoft.com/en-us/graph/api/resources/chatmessage?view=graph-rest-1.0
- List chats:
  https://learn.microsoft.com/en-us/graph/api/chat-list?view=graph-rest-1.0
- Create chat:
  https://learn.microsoft.com/en-us/graph/api/chat-post?view=graph-rest-1.0
- List messages in a chat:
  https://learn.microsoft.com/en-us/graph/api/chat-list-messages?view=graph-rest-1.0
- Send chatMessage in a channel or a chat:
  https://learn.microsoft.com/en-us/graph/api/chatmessage-post?view=graph-rest-1.0
- Create teams and manage members:
  https://learn.microsoft.com/en-us/graph/teams-create-group-and-team

## Core Model

Important resource relationships:

- A Microsoft Team is backed by a Microsoft 365 group.
- The team ID is the same as the backing group ID.
- Team channel conversations are represented through `channel` and
  `chatMessage` resources.
- Direct and group chats are represented through `chat` and `chatMessage`
  resources.
- Group conversations in Outlook are different resources and are not the same
  as Teams channel chat.
- A `chatMessage` can belong either to a channel or to a chat.
- `replyToId` applies only to channel-thread messages, not chat messages.

Core Teams resources:

- `team`
- `channel`
- `chat`
- `chatMessage`
- `group`

## Common Use Cases

The Teams overview groups common scenarios like this:

- create and manage teams, groups, and channels
- add tabs or install apps
- create channels and chats and send/receive chat messages
- use tags inside a team
- online meetings and presence
- calls and call records

This skill focuses primarily on:

- `team`
- `chat`
- `channel`
- `chatMessage`

## Common Flows

Read joined teams:

- Endpoint:
  `GET /me/joinedTeams`

Get team details:

- Endpoint:
  `GET /teams/{team-id}`

Create a team:

- Endpoint:
  `POST /teams`
- Note:
  team creation is asynchronous and returns a `teamsAsyncOperation`

Create a channel:

- Endpoint:
  `POST /teams/{team-id}/channels`

List the signed-in user's chats:

- Endpoint:
  `GET /me/chats`

Get chat details:

- Endpoint:
  `GET /chats/{chat-id}`

Create a chat:

- Endpoint:
  `POST /chats`
- Notes:
  every participant must be listed in the `members` collection
  only one one-on-one chat can exist between the same two members

List chat messages:

- Endpoint:
  `GET /chats/{chat-id}/messages`

Send a message in an existing chat:

- Endpoint:
  `POST /chats/{chat-id}/messages`

Send a root message in a channel:

- Endpoint:
  `POST /teams/{team-id}/channels/{channel-id}/messages`

Read channel messages:

- Endpoint:
  `GET /teams/{team-id}/channels/{channel-id}/messages`

Manage team membership:

- Endpoints:
  `POST /teams/{team-id}/members`
  `DELETE /teams/{team-id}/members/{membership-id}`
  `PATCH /teams/{team-id}/members/{membership-id}`

## Minimal Payloads

Create a basic team:

```json
{
  "template@odata.bind": "https://graph.microsoft.com/v1.0/teamsTemplates('standard')",
  "displayName": "Engineering",
  "description": "Engineering collaboration team"
}
```

Create a one-on-one chat:

```json
{
  "chatType": "oneOnOne",
  "members": [
    {
      "@odata.type": "#microsoft.graph.aadUserConversationMember",
      "roles": ["owner"],
      "user@odata.bind": "https://graph.microsoft.com/v1.0/users('USER_ID_1')"
    },
    {
      "@odata.type": "#microsoft.graph.aadUserConversationMember",
      "roles": ["owner"],
      "user@odata.bind": "https://graph.microsoft.com/v1.0/users('USER_ID_2')"
    }
  ]
}
```

Create a channel:

```json
{
  "displayName": "Launch Planning",
  "description": "Planning and coordination for launch"
}
```

Send a simple channel message:

```json
{
  "body": {
    "contentType": "html",
    "content": "Hello from Microsoft Graph."
  }
}
```

Send a simple chat message:

```json
{
  "body": {
    "contentType": "html",
    "content": "Hello from Microsoft Graph."
  }
}
```

## Important Behavior

- Team creation is not always immediate; treat `POST /teams` as asynchronous.
- Teams APIs are tightly related to Microsoft 365 groups.
- Chats are not the same resource as team channels.
- `chatType` distinguishes `oneOnOne`, `group`, and `meeting` chats.
- Creating a one-on-one chat does not create duplicates; Graph returns the
  existing chat if one already exists between the same two members.
- Files inside standard channels are backed by SharePoint.
- Some write operations are only supported for work or school accounts and
  often require delegated permissions that are different from the basic read
  scopes used for discovery.
- Sending chat or channel messages is a different capability from reading team
  names and descriptions.
- The current Microsoft Learn send-message page documents
  `ChannelMessage.Send` as the least-privileged delegated permission for both
  channel sends and chat sends. Follow the live docs when the token is minted.
- Listing chats with `$expand=members` currently returns at most 25 expanded
  members per chat response.
- Listing messages in a chat supports `$top`, `$orderby`, and constrained
  `$filter` on `createdDateTime` or `lastModifiedDateTime`.
- For chat message reads that include event/system messages, the
  `Prefer: include-unknown-enum-members` header can be useful.

## Polling Rule

The Teams API overview explicitly warns against aggressive polling.

- Do not poll Teams resources in a tight loop.
- If you need frequent change detection, prefer change notifications or
  resource-specific delta patterns where supported.
- For ordinary user-driven refreshes, one-off `GET` requests are fine.

## Agent Guidance

Prefer:

- `/me/joinedTeams` for discovery tied to the signed-in user
- `/me/chats` for direct-message, group-chat, or meeting-chat discovery
- `/chats/{chat-id}` once you already know the chat ID
- `/chats/{chat-id}/messages` for chat history or sending into an existing chat
- `/teams/{team-id}` once you already know the team ID
- `/teams/{team-id}/channels` for channel discovery inside a known team
- `/teams/{team-id}/channels/{channel-id}/messages` for channel conversation
  access

When the user says "Teams API", clarify whether they mean:

- team and channel management
- reading or sending channel messages
- reading or sending direct/group chat messages
- chats versus channels
- meetings, presence, or calls

If a write operation fails, check whether the token is missing a Teams-specific
delegated permission before assuming the endpoint or payload is wrong.

Do not assume a person-to-person Teams conversation lives under a `team` or a
`channel`. For direct messaging and group chat, use `chat` endpoints first.
