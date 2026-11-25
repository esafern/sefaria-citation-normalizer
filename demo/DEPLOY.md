# Deploying the citation-linker demo on girsa.net

For girsa-demo-operator. This is a separate, self-contained web app; it doesn't touch the
Girsa demo at app.girsa.net or its wrapper. The one change to existing Girsa files is an
optional footer link on the home page (section 6), which is a visible change and needs the
reviewer's go.

## 1. What it is

A page where a visitor pastes Torah citations ("Berachos 5a", "SA OC 271:1") and gets
Sefaria links, or a plain explanation of why a citation stays unlinked. Source:
https://github.com/esafern/sefaria-citation-normalizer (`demo/`, plus the `citenorm` package).

- Python 3.10+, **standard library only** (the host's 3.13 is fine). No pip installs.
- A WSGI app: `passenger_wsgi.py` exposes `application`.
- It calls **www.sefaria.org over HTTPS** (outbound), paced at 0.25 s between requests.
- State: one SQLite file plus Sefaria's title list (about 3 MB) in a data folder, safe with
  forked workers that share no memory.

## 2. The archive

`dist/citenorm-demo-<commit>.tar.gz` (built by `python3 demo/build.py` from a clean commit)
contains one folder, `citenorm-demo/`:

```
passenger_wsgi.py   app.py   check_demo.py   DEPLOY.md   VERSION   LICENSE (MIT)
static/   index.html, powered-by-sefaria-white.png, powered-by-sefaria-blue.png
citenorm/ __init__.py, resolve.py, rules.py, shared_dialect.py, cli.py
```

It contains binary files (the two badges), so per your README it goes up as one archive
uploaded by the reviewer through cPanel's File Manager, to the home folder.

## 3. Suggested setup

- **URL:** `https://girsa.net/cite/` (cPanel, Setup Python App: domain girsa.net, URL
  `cite`). A subdomain (`cite.girsa.net`) also works but needs the reviewer to add it in
  Spaceship's dashboard. The page uses relative links, so any path works.
- **App root:** e.g. `~/citenorm_app` (the extracted `citenorm-demo/` folder).
- **Startup file / entry point:** `passenger_wsgi.py` / `application`.
- **Environment:**
  - `CITENORM_DEMO_DATA=~/citenorm_demo_data`: keep it outside the app root, so an upgrade
    doesn't wipe the answer cache. Default if unset: `~/citenorm_demo_data`.
  - `CITENORM_DEMO_SALT=<any random string>`: used to hash visitor IPs for rate limiting.
    Optional; a fixed default is derived otherwise.
- **No cron.** Nothing needs resetting; the cache only grows by one small row per new
  citation anyone tries.

## 4. Load, limits and privacy

- Per visitor: 20 new (uncached) citations a minute and 120 in all. Across all visitors: 60
  new citations a minute. Beyond that the page says "please wait a minute" (HTTP 429).
- One citation per request; the page loops. A new citation takes about 1-20 s (it may need
  several requests to Sefaria); a cached one is instant.
- The app writes no request log. The cache holds citations and their answers only. Rate
  limiting keeps a salted hash of the IP for about two minutes.

## 5. Checks

On a copy first, then live:

```bash
cd ~/citenorm_app
CITENORM_DEMO_DATA=/tmp/citenorm_check python3 app.py 8765 &     # local copy
python3 check_demo.py http://127.0.0.1:8765/
python3 check_demo.py https://girsa.net/cite/                    # live
```

`check_demo.py` checks the health endpoint, the page, both badges, and 7 citations with
known answers (including one that must stay unlinked and the strict setting). It exits 1 on
any mismatch.

**Run it once right after each deploy:** the first lookup after a fresh install also downloads
Sefaria's title list (about 3 MB), so it takes about 25 s; the check absorbs that, so no
visitor waits for it. After that, new citations take about 1-20 s and cached ones are instant.

**What goes public:** the page contains no email addresses or home-folder paths (the build
refuses them). It does name the GitHub repository, whose URL includes the account name
`esafern`. If your public-content check refuses that, the reviewer decides.

**Rollback:** stop or remove the Python app in cPanel; the home page link (if added) comes out
with its own commit.

## 6. The home-page link (proposed; needs the reviewer's go)

The reviewer wants a link that **doesn't distract from the video**. Proposal: one short item
in the existing footer, after the copyright, in the footer's own muted color and size. No
button, no image, **no Powered-by badge** (the reviewer, 2026-11-25: no badge on the home page;
the badge stays on the demo page itself), nothing above the fold. In `handover/web/site/index.html`:

```html
<footer>
  <span data-for="en">© 2026 Girsa · <a href="/cite/">Citation linker for Sefaria</a></span><span data-for="he" lang="he" dir="rtl" hidden>© 2026 גירסא · <a href="/cite/">קישור מראי מקומות לספריא (באנגלית)</a></span>
</footer>
```

and one line of CSS so the link keeps the footer's muted color instead of the browser's
blue:

```css
footer a { color: inherit; text-underline-offset: 2px; }
```

The Hebrew label says "link citations to Sefaria (in English)", since the tool reads English
citations; the reviewer may prefer other words. The look of the page is girsa-ui-steward's,
so it may want to weigh in on the CSS line.
