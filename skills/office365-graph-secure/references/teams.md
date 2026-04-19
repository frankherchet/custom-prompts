# Teams

Use this reference for Teams tasks: joined teams, channels, chats, team details,
channel messaging, and chat messaging.

Primary docs:

- Teams API detail:
  `references/teams-api.md`
- Teams API overview:
  https://learn.microsoft.com/en-us/graph/api/resources/teams-api-overview?view=graph-rest-1.0

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
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path /me/joinedTeams
```

List chats:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --path '/me/chats?$top=10&$expand=lastMessagePreview'
```

Send a channel message:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method POST \
  --path '/teams/{team-id}/channels/{channel-id}/messages' \
  --body-file /absolute/path/to/send-channel-message.json
```

Send a chat message:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
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

- Team/channel and chat resources are different parts of the Teams model.
- Team creation is asynchronous.
- Channel messages and chat messages use different resource paths even when the
  payload shape is similar.
- For deeper resource-model and payload details, read `references/teams-api.md`.

## Failure Hints

- `403` on `/me/joinedTeams` usually means the token lacks `Team.ReadBasic.All`.
- `403` on `/me/chats` or `/chats/{chat-id}/messages` usually means the token
  lacks `Chat.ReadBasic` or `Chat.Read`.
- `403` on `/chats` creation usually means the token lacks `Chat.Create`.
- `403` on channel-message or chat-message sends usually means the token lacks
  the required Teams delegated send permission.
