# Teams API

Use this reference when the task is about Microsoft Teams resources rather than
generic SharePoint or mail access.

Primary docs:

- Teams API overview:
  https://learn.microsoft.com/en-us/graph/api/resources/teams-api-overview?view=graph-rest-1.0
- Team resource:
  https://learn.microsoft.com/en-us/graph/api/resources/team?view=graph-rest-1.0
- Channel resource:
  https://learn.microsoft.com/en-us/graph/api/resources/channel?view=graph-rest-1.0
- chatMessage resource:
  https://learn.microsoft.com/en-us/graph/api/resources/chatmessage
- Create teams and manage members:
  https://learn.microsoft.com/en-us/graph/teams-create-group-and-team

## Core Model

Important resource relationships:

- A Microsoft Team is backed by a Microsoft 365 group.
- The team ID is the same as the backing group ID.
- Team conversations are represented through `channel` and `chatMessage`
  resources.
- Group conversations in Outlook are different resources and are not the same
  as Teams channel chat.

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

## Important Behavior

- Team creation is not always immediate; treat `POST /teams` as asynchronous.
- Teams APIs are tightly related to Microsoft 365 groups.
- Files inside standard channels are backed by SharePoint.
- Some write operations are only supported for work or school accounts and
  often require delegated permissions that are different from the basic read
  scopes used for discovery.
- Sending chat or channel messages is a different capability from reading team
  names and descriptions.

## Polling Rule

The Teams API overview explicitly warns against aggressive polling.

- Do not poll Teams resources in a tight loop.
- If you need frequent change detection, prefer change notifications or
  resource-specific delta patterns where supported.
- For ordinary user-driven refreshes, one-off `GET` requests are fine.

## Agent Guidance

Prefer:

- `/me/joinedTeams` for discovery tied to the signed-in user
- `/teams/{team-id}` once you already know the team ID
- `/teams/{team-id}/channels` for channel discovery inside a known team
- `/teams/{team-id}/channels/{channel-id}/messages` for channel conversation
  access

When the user says "Teams API", clarify whether they mean:

- team and channel management
- reading or sending channel messages
- chats versus channels
- meetings, presence, or calls

If a write operation fails, check whether the token is missing a Teams-specific
delegated permission before assuming the endpoint or payload is wrong.
