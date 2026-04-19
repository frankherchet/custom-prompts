# SharePoint Pages

Use this reference when the task is about SharePoint site pages, page content,
page metadata, webparts, or subsite discovery rather than files in document
libraries.

Primary docs:

- site resource:
  https://learn.microsoft.com/en-us/graph/api/resources/site?view=graph-rest-1.0
- List subsites for a site:
  https://learn.microsoft.com/en-us/graph/api/site-list-subsites?view=graph-rest-1.0
- baseSitePage resource:
  https://learn.microsoft.com/en-us/graph/api/resources/basesitepage?view=graph-rest-1.0
- List baseSitePages:
  https://learn.microsoft.com/en-us/graph/api/basesitepage-list?view=graph-rest-1.0
- Get baseSitePage:
  https://learn.microsoft.com/en-us/graph/api/basesitepage-get?view=graph-rest-1.0
- sitePage resource:
  https://learn.microsoft.com/en-us/graph/api/resources/sitepage?view=graph-rest-1.0
- List sitePage:
  https://learn.microsoft.com/en-us/graph/api/sitepage-list?view=graph-rest-1.0
- Get sitePage:
  https://learn.microsoft.com/en-us/graph/api/sitepage-get?view=graph-rest-1.0
- List webparts:
  https://learn.microsoft.com/en-us/graph/api/webpart-list?view=graph-rest-1.0

## Core Model

Important resource relationships:

- A SharePoint site is a `site`.
- The pages library on a site exposes `baseSitePage` objects under
  `/sites/{site-id}/pages`.
- Normal modern pages are `sitePage` objects, which are a subtype of
  `baseSitePage`.
- Page content can be exposed through `canvasLayout`.
- Page components can be exposed through `webparts`.
- Subsites are returned from `/sites/{site-id}/sites`.

## Common Flows

List pages in a site:

- Generic pages collection:
  `GET /sites/{site-id}/pages`
- Normal site pages:
  `GET /sites/{site-id}/pages/microsoft.graph.sitePage`

Get one page:

- Generic page:
  `GET /sites/{site-id}/pages/{page-id}`
- Normal site page:
  `GET /sites/{site-id}/pages/{page-id}/microsoft.graph.sitePage`

Get a page with content layout:

- Endpoint:
  `GET /sites/{site-id}/pages/{page-id}/microsoft.graph.sitePage?$expand=canvasLayout`

List webparts for a page:

- Endpoint:
  `GET /sites/{site-id}/pages/{page-id}/microsoft.graph.sitePage/webparts`

List subsites for a site:

- Endpoint:
  `GET /sites/{site-id}/sites`

## Preferred Patterns

Prefer:

- `/pages/microsoft.graph.sitePage` when the task is clearly about modern site
  pages
- `/pages/{page-id}/microsoft.graph.sitePage?$expand=canvasLayout` when the
  user wants page content or structure
- `/pages/{page-id}/microsoft.graph.sitePage/webparts` when the user wants page
  components and not just top-level metadata
- `/sites/{site-id}/sites` when the user wants child sites or site hierarchy

## Information Collection Guidance

When collecting page information for the user, prefer returning:

- page `id`, `name`, `title`, `description`, `webUrl`
- `lastModifiedDateTime`
- `promotionKind` when relevant
- summarized `canvasLayout` structure
- webpart type, id, and useful text/configuration fields

Avoid returning:

- unnecessary OData metadata
- full large page payloads when a compact summary is enough

## Important Behavior

- `GET /sites/{site-id}/pages/{page-id}` returns a generic `baseSitePage`.
- `GET /sites/{site-id}/pages/{page-id}/microsoft.graph.sitePage` returns the
  normal modern page subtype with site-page-specific properties.
- Microsoft documents `$expand=canvasLayout` to include page content and layout
  in the site page response.
- Page and webpart operations in v1.0 require `Sites.Read.All` for delegated
  read access.

## Agent Guidance

If the user asks:

- "what pages are on this site?" -> list `sitePage` objects first
- "what is on this page?" -> get the `sitePage` with `?$expand=canvasLayout`
- "what webparts does this page contain?" -> call the webparts endpoint
- "what child sites exist under this site?" -> call `/sites/{site-id}/sites`
