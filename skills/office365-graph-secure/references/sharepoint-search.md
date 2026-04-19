# SharePoint Search And Collection

Use this reference when the task is to search SharePoint, OneDrive for
Business, or SharePoint document libraries and collect structured information
back for the user.

Primary docs:

- Working with files in Microsoft Graph:
  https://learn.microsoft.com/en-us/graph/api/resources/onedrive?view=graph-rest-1.0
- SharePoint API overview:
  https://learn.microsoft.com/en-us/graph/api/resources/sharepoint?view=graph-rest-1.0
- site resource:
  https://learn.microsoft.com/en-us/graph/api/resources/site?view=graph-rest-1.0
- Get site:
  https://learn.microsoft.com/en-us/graph/api/site-get?view=graph-rest-1.0
- drive resource:
  https://learn.microsoft.com/en-us/graph/api/resources/drive?view=graph-rest-1.0
- driveItem resource:
  https://learn.microsoft.com/en-us/graph/api/resources/driveitem?view=graph-rest-1.0
- Search driveItems within a drive:
  https://learn.microsoft.com/en-us/graph/api/driveitem-search?view=graph-rest-1.0
- List children of a driveItem:
  https://learn.microsoft.com/en-us/graph/api/driveitem-list-children?view=graph-rest-1.0
- List items:
  https://learn.microsoft.com/en-us/graph/api/listitem-list?view=graph-rest-1.0
- Get listItem:
  https://learn.microsoft.com/en-us/graph/api/listitem-get?view=graph-rest-1.0
- Microsoft Search for OneDrive and SharePoint:
  https://learn.microsoft.com/en-us/graph/search-concept-files
- `POST /search/query`:
  https://learn.microsoft.com/en-us/graph/api/search-query?view=graph-rest-1.0

## Core Model

Important resource relationships:

- A SharePoint site is a `site`.
- SharePoint document libraries are `drive` resources.
- Files and folders inside a document library are `driveItem` resources.
- SharePoint lists are `list` resources, and rows/items are `listItem`
  resources.
- A site's default document library is available under `/sites/{site-id}/drive`.
- All document libraries for a site are available under `/sites/{site-id}/drives`.

## Preferred Search Strategy

Use the narrowest search flow that matches the task:

1. If the site is known, resolve it first with:
   `GET /sites/{hostname}:/{server-relative-path}`
2. If the task is about documents in that site, search the site's default
   document library with:
   `GET /sites/{site-id}/drive/root/search(q='{terms}')`
3. If the task is about a known folder, traverse by path or list children:
   `GET /sites/{site-id}/drive/root:/Folder:/children`
4. If the task is about SharePoint lists, enumerate or fetch `listItem`
   objects with `expand=fields(...)`.
5. If the task is broader than one site or one drive, use:
   `POST /search/query`

## Common Flows

Resolve a SharePoint site by path:

- Endpoint:
  `GET /sites/{hostname}:/{server-relative-path}`

Get the site's default document library:

- Endpoint:
  `GET /sites/{site-id}/drive`

List all document libraries for a site:

- Endpoint:
  `GET /sites/{site-id}/drives`

Search within a site's default document library:

- Endpoint:
  `GET /sites/{site-id}/drive/root/search(q='{terms}')`
- Notes:
  use `$select` and `$top` to keep results compact
  matches can include filename, metadata, and file content

List folder contents:

- Endpoint:
  `GET /sites/{site-id}/drive/root:/Folder:/children`

Read SharePoint list items with selected fields:

- Endpoint:
  `GET /sites/{site-id}/lists/{list-id}/items?expand=fields(select=Title,Modified)`

Read one SharePoint list item with fields:

- Endpoint:
  `GET /sites/{site-id}/lists/{list-id}/items/{item-id}?expand=fields`

Run broader SharePoint search:

- Endpoint:
  `POST /search/query`
- Good entity types:
  `site`
  `driveItem`
  `listItem`

## Minimal Payloads

Broad search for SharePoint files:

```json
{
  "requests": [
    {
      "entityTypes": ["driveItem"],
      "query": {
        "queryString": "quarterly budget"
      },
      "from": 0,
      "size": 10,
      "fields": [
        "name",
        "webUrl",
        "createdBy",
        "lastModifiedDateTime",
        "parentReference"
      ]
    }
  ]
}
```

Search SharePoint list items:

```json
{
  "requests": [
    {
      "entityTypes": ["listItem"],
      "query": {
        "queryString": "contract renewal"
      },
      "from": 0,
      "size": 10,
      "fields": [
        "title",
        "webUrl"
      ]
    }
  ]
}
```

Search SharePoint sites:

```json
{
  "requests": [
    {
      "entityTypes": ["site"],
      "query": {
        "queryString": "benefits portal"
      },
      "from": 0,
      "size": 10
    }
  ]
}
```

## Information Collection Guidance

When collecting information for the user, prefer returning:

- site `displayName`, `id`, `webUrl`
- drive `id`, `name`, `driveType`, `webUrl`
- driveItem `name`, `id`, `webUrl`, `parentReference`, `lastModifiedDateTime`
- listItem selected `fields`, `webUrl`, `createdDateTime`, `lastModifiedDateTime`
- search hit `summary` snippets when returned by Microsoft Search

Avoid returning:

- raw bearer tokens
- manually constructed authorization headers
- `@microsoft.graph.downloadUrl` unless the user explicitly asks for a direct
  download link

## Important Behavior

- The OneDrive/Files model in Microsoft Graph also covers SharePoint document
  libraries.
- A SharePoint document library is represented as a `drive` with
  `driveType=documentLibrary`.
- `GET /sites/{site-id}/drive/root/search(q='{terms}')` is scoped to that
  site's default document library.
- `POST /search/query` is broader and is better for cross-site discovery.
- `GET /sites/{site-id}/lists/{list-id}/items` supports `expand=fields(...)`
  and filtering on fields.
- List-item filtering works best on indexed columns.
- Graph paging can appear via `@odata.nextLink`; follow it exactly instead of
  rebuilding the request manually.

## Agent Guidance

Prefer:

- site-path resolution first when the user knows the SharePoint URL or path
- drive search for document-library discovery inside one site
- list-item reads when the user asks about structured SharePoint list data
- Microsoft Search when the user asks to "search SharePoint" without knowing
  the exact site or library

Do not jump straight to broad tenant search if the user has already given a
specific site path.

When reporting search results, summarize concise metadata first and only fetch
deeper item details for the strongest hits or the items the user asks about.
