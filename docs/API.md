# The citenorm REST API (v1)

An HTTP front end to the resolver, for sites and tools that don't run Python. Standard library
only (WSGI). Built 2026-11-25; not yet deployed (see "Deploying").

## Endpoints

| Method and path | What |
|---|---|
| `GET /v1/resolve?q=<citation>&conventions=common\|strict` | Resolve one citation |
| `POST /v1/resolve` with `{"citations": [...], "conventions": "common"}` | Resolve up to 50, results in order |
| `GET /v1/explain?q=<citation>&conventions=...` | Why it was linked or left unlinked: the `explain()` trace |
| `GET /v1/health` | `{ok, api, version, code}` (`code` is the resolver's code fingerprint) |
| `GET /v1/openapi.json` | The OpenAPI 3.1 description |

```bash
curl 'https://<host>/v1/resolve?q=Hilchos%20Eidus%204:1'
# {"citation": "Hilchos Eidus 4:1", "status": "linked",
#  "url": "https://www.sefaria.org/Mishneh_Torah,_Testimony.4.1",
#  "ref": "Mishneh Torah, Testimony 4:1", "convention": null}

curl -X POST 'https://<host>/v1/resolve' -H 'Content-Type: application/json' \
     -d '{"citations": ["Berachos 5a", "Shmuel 23:8", "YD 289"], "conventions": "strict"}'
```

## Results

| `status` | Meaning | Cached? |
|---|---|---|
| `linked` | `url` and `ref` are set | yes |
| `unlinked` | can't be linked without guessing (no work named, ambiguous, not on Sefaria) | yes |
| `unavailable` | Sefaria couldn't be reached; try again later | **no** |
| `deferred` | (batch only) this request's or this minute's budget of new lookups is used up; send those citations again | no |

`convention` names the Sefaria convention a reading relies on (`bare_section`, `mishnah`,
`short_alias`; see the README). With `conventions=strict` such citations come back `unlinked`,
with `convention` still set so you can tell why.

## Errors

JSON `{"error": {"code", "message"}}` with an HTTP status: `400` (`missing_q`, `too_long`,
`bad_conventions`, `bad_citations`, `too_many`, `bad_json`), `401` (`bad_key`), `404`,
`405`, `413`, `429` (`rate_limited`, with `Retry-After: 60`), `500`.

## Limits

Per minute, per client (by IP address, or by API key):

| | all citations | new (uncached) lookups | explains |
|---|---|---|---|
| no key | 300 | 30 | 10 |
| with `X-API-Key` | 3,000 | 120 | 60 |

Plus 120 new lookups a minute across all clients, which protects Sefaria. A request does at
most 10 new lookups; the rest of a batch comes back `deferred`. Cached answers are cheap: send
them as often as you like within the "all" limit. Clients are identified by `REMOTE_ADDR` only;
`X-Forwarded-For` is ignored, since a client can set it to anything.

## Versioning

`/v1/` never changes incompatibly: endpoints and fields may be **added**, never removed or
renamed, and a status keeps its meaning. A consumer pins the git tag `api-v1`
(`docs/RELEASING.md`); a breaking change would be `/v2/` alongside `/v1/`.

Answers are cached per version of the resolver code (`code` in `/v1/health` and the
`X-Citenorm-Code` header), so a deploy never serves answers computed by older code.

## Browsers

CORS is open (`Access-Control-Allow-Origin: *`; `X-API-Key` allowed), so a page on any site
can call the API directly.

## Running it

```bash
citenorm-api --port 8780        # local: http://127.0.0.1:8780/v1/health
```

Any WSGI server can host `citenorm.api:application` (cPanel's Python apps, gunicorn, uWSGI,
...). Configuration by environment:

| Variable | Default | Meaning |
|---|---|---|
| `CITENORM_API_DATA` | `~/.cache/citenorm/api` | folder for the SQLite file (answers, rate counters) |
| `CITENORM_API_KEYS` | none | file of API keys, one per line: `key  label` |
| `CITENORM_API_SALT` | derived | salt for hashing client addresses |
| `CITENORM_CACHE` | `~/.cache/citenorm` | Sefaria's title list |

Nothing about a request is logged by the app; the database holds citations and answers, and
hashed client identifiers for about two minutes.

## Deploying (open)

Where it runs is not decided yet. When it is: tag the commit `api-v1` on the first public
deploy, and `prod-YYYY-MM-DD` on each deploy (`docs/RELEASING.md`).

## Not in v1 yet

`POST /v1/link-text`: running text in, citations linked out. It needs a citation detector (see
`docs/ROADMAP.md`) and will be added to v1 without changing anything above.
