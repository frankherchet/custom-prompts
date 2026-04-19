# Teams

Use this reference for Teams tasks: joined teams, channels, chats, team details,
channel messaging, and chat messaging.

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

## Read This For

- "send a message to a Teams channel"
- team discovery
- channel discovery
- chat discovery
- chat versus channel routing

## Common Scopes

- `/me/joinedTeams`: `Team.ReadBasic.All`
- `/teams/{team-id}/primaryChannel`: `Channel.ReadBasic.All`
- `/teams/{team-id}` settings reads: `TeamSettings.Read.All`
- `/teams`: `Team.Create`
- `/me/chats` or `/chats/{chat-id}`: `Chat.ReadBasic`
- `/chats/{chat-id}/messages`: `Chat.Read`
- `/chats`: `Chat.Create`
- `/teams/{team-id}/channels/{channel-id}/messages`: delegated Teams send
  permission such as `ChannelMessage.Send`
- `/chats/{chat-id}/messages` send chat message:
  the current Microsoft Learn send-message page also lists
  `ChannelMessage.Send`

## Common Flows

List joined teams:

- Endpoint:
  `GET /me/joinedTeams`

Get team details:

- Endpoint:
  `GET /teams/{team-id}`

Get the General channel:

- Endpoint:
  `GET /teams/{team-id}/primaryChannel`

Create a channel:

- Endpoint:
  `POST /teams/{team-id}/channels`

Send a channel message:

- Endpoint:
  `POST /teams/{team-id}/channels/{channel-id}/messages`

List chats:

- Endpoint:
  `GET /me/chats`

Get chat details:

- Endpoint:
  `GET /chats/{chat-id}`

Create a chat:

- Endpoint:
  `POST /chats`

List chat messages:

- Endpoint:
  `GET /chats/{chat-id}/messages`

Send a chat message:

- Endpoint:
  `POST /chats/{chat-id}/messages`

## Recommended Recipes

Joined teams:

```bash
python3 skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path /me/joinedTeams
```

List chats:

```bash
python3 skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path '/me/chats?$top=10&$expand=lastMessagePreview'
```

Send a channel message:

```bash
python3 skills/office365-graph-secure/scripts/graph_secure.py request \
  --method POST \
  --path '/teams/{team-id}/channels/{channel-id}/messages' \
  --body-file /absolute/path/to/send-channel-message.json
```

Send a chat message:

```bash
python3 skills/office365-graph-secure/scripts/graph_secure.py request \
  --method POST \
  --path '/chats/{chat-id}/messages' \
  --body-file /absolute/path/to/send-chat-message.json
```

## Routing Rule

- Use `/teams/.../channels/...` for team-channel workflows.
- Use `/chats/...` for direct or group chat workflows.
- If the user says "Teams message" and the target type is unclear, determine
  whether they mean a channel or a direct/group chat before sending.

## Important Behavior

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
- Team/channel and chat resources are different parts of the Teams model.
- Team creation is asynchronous.
- Creating a one-on-one chat does not create duplicates; Graph returns the
  existing chat if one already exists between the same two members.
- Channel messages and chat messages use different resource paths even when the
  payload shape is similar.
- Files inside standard channels are backed by SharePoint.
- Listing chats with `$expand=members` currently returns at most 25 expanded
  members per chat response.
- Listing messages in a chat supports `$top`, `$orderby`, and constrained
  `$filter` on `createdDateTime` or `lastModifiedDateTime`.
- For chat message reads that include event/system messages, the
  `Prefer: include-unknown-enum-members` header can be useful.
- The Teams API overview explicitly warns against aggressive polling. Do not
  poll Teams resources in a tight loop.

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

Send a simple channel or chat message:

```json
{
  "body": {
    "contentType": "html",
    "content": "Hello from Microsoft Graph."
  }
}
```

## Failure Hints

- `403` on `/me/joinedTeams` usually means the token lacks `Team.ReadBasic.All`.
- `403` on `/me/chats` or `/chats/{chat-id}/messages` usually means the token
  lacks `Chat.ReadBasic` or `Chat.Read`.
- `403` on `/chats` creation usually means the token lacks `Chat.Create`.
- `403` on channel-message or chat-message sends usually means the token lacks
  the required Teams delegated send permission.
