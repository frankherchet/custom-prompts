# Calendar

Use this reference for Outlook calendar tasks: upcoming schedules, tomorrow's
meetings, time-window queries, event listing, and event creation.

Primary docs:

- List calendarView:
  https://learn.microsoft.com/en-us/graph/api/user-list-calendarview?view=graph-rest-1.0
- List events:
  https://learn.microsoft.com/en-us/graph/api/user-list-events?view=graph-rest-1.0

## Read This For

- "what are the meetings for tomorrow"
- schedule summaries in a bounded time window
- event master listing
- event creation

## Common Scopes

- `/me/calendar/calendarView`: `Calendars.ReadBasic`
- `/me/events`: `Calendars.Read`
- `POST /me/events`: `Calendars.ReadWrite`

## Common Flows

Read upcoming events in a time window:

- Endpoint:
  `GET /me/calendar/calendarView?startDateTime=...&endDateTime=...`
- Use when:
  the user wants occurrences inside a concrete window

List tomorrow's meetings:

- Endpoint:
  `GET /me/calendar/calendarView?startDateTime=...&endDateTime=...`
- Use when:
  the user wants tomorrow's actual meeting instances

List event masters with selected fields:

- Endpoint:
  `GET /me/events?$select=subject,body,bodyPreview,organizer,attendees,start,end,location`
- Use when:
  the user wants event objects instead of expanded calendar instances

Create an event:

- Endpoint:
  `POST /me/events`

## Recommended Recipes

Calendar view:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --header 'Prefer=outlook.timezone="Europe/Berlin"' \
  --path '/me/calendar/calendarView?startDateTime=2026-04-19T00:00:00Z&endDateTime=2026-04-26T00:00:00Z&$top=10&$select=subject,start,end,location,webLink'
```

Tomorrow's meetings:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --header 'Prefer=outlook.timezone="Europe/Berlin"' \
  --path '/me/calendar/calendarView?startDateTime=2026-04-20T00:00:00Z&endDateTime=2026-04-21T00:00:00Z&$top=20&$select=subject,start,end,organizer,location,webLink'
```

Event masters:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method GET \
  --header 'Prefer=outlook.body-content-type="text"' \
  --path '/me/events?$select=subject,body,bodyPreview,organizer,attendees,start,end,location,webLink&$top=20'
```

Create event:

```bash
python3 custom-prompts/skills/office365-graph-secure/scripts/graph_secure.py request \
  --method POST \
  --path /me/events \
  --body-file /absolute/path/to/create-event.json
```

## Timezone Guidance

- Prefer `/calendarView` over `/events` when you need expanded occurrences in a
  fixed time window.
- Microsoft documents that the timezone offset in `startDateTime` and
  `endDateTime` controls how the query bounds are interpreted.
- `Prefer: outlook.timezone="Europe/Berlin"` controls how the response times are
  returned.
- `Prefer: outlook.body-content-type="text"` is useful when event bodies should
  come back as plain text rather than HTML.

## Failure Hints

- `403` on `/me/calendar/calendarView` usually means the token lacks
  `Calendars.ReadBasic` or stronger.
- `403` on `/me/events` usually means the token lacks `Calendars.Read` for reads
  or `Calendars.ReadWrite` for writes.
