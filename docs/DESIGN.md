# Niko's Corny Joke Machine — As-Built Design

**Document status:** Living design document  
**System status:** Existing production application  
**Production URL:** https://nikoscornyjokemachine.com  
**Last reviewed:** 2026-08-28

## 1. Purpose

Niko's Corny Joke Machine (NCJM) is a community-maintained joke archive. It lets visitors discover jokes, find related jokes by tag or submitter, react to jokes, and submit new material. Submitted jokes enter a moderation queue before appearing in the public random-joke experience.

This is an as-built design document. It records the behavior and architecture of the existing application so that future changes can be evaluated against an explicit baseline. It describes the current system rather than proposing a complete rewrite.

## 2. Product goals

The application should:

- Make viewing a random joke immediate and frictionless.
- Preserve stable links to individual jokes.
- Let visitors explore the collection through tags and submitter names.
- Accept community submissions without allowing them directly into the public collection.
- Give visitors a lightweight way to rate a joke.
- Support both concise setup/punchline jokes and jokes whose humor depends on longer-form writing, performance, or supporting context.
- Present the collection well on phones, tablets, and desktop screens while retaining the site's distinctive visual personality.
- Let visitors opt into receiving a joke on a recurring schedule.
- Measure product usage well enough to guide redesign and feature decisions.
- Assist moderators with automated tag suggestions and conservative NSFW detection.
- Give maintainers efficient moderation and catalog-management tools.
- Offer a machine-readable API when the API feature is enabled.
- Remain small enough to operate and maintain as a personal site.

## 3. Non-goals

The current application is not designed to provide:

- Visitor accounts or public profiles.
- Personalized recommendations or reaction histories.
- Real-time updates.
- Comments, discussion threads, or social-network features.
- Automatic joke approval.
- A full-text search engine. Search is limited to tags and submitter names.
- Per-reaction audit records. Only a deduplication fingerprint and aggregate counts are retained.
- Guaranteed authorship or ownership verification for submitted content.
- Hosting uploaded audio or video. Rich jokes may reference supported third-party media, but NCJM does not initially operate a media-hosting service.

## 4. Actors and permissions

### 4.1 Anonymous visitor

An anonymous visitor can:

- View a random approved joke.
- Open a joke by numeric ID or slug.
- Search by tag or submitter name.
- Submit a joke for moderation after passing reCAPTCHA.
- React to a joke once per IP-address and user-agent combination.
- Use public API read endpoints when the API is enabled.

### 4.2 Authenticated API client

An authenticated API client can perform API write operations, including creating and editing jokes and tags, soft-deleting jokes, and recording reactions. Authentication is provided through OAuth2 or a Django session.

### 4.3 Staff administrator

A staff administrator uses Django Admin to:

- Review, edit, approve, and unapprove jokes.
- Soft-delete or permanently delete jokes.
- Search and filter the joke catalog.
- Find untagged jokes and orphaned tags.
- Manage tags and joke/tag relationships.
- Use staff-only API capabilities, including viewing unapproved jokes and hard deletion.

## 5. Functional design

### 5.1 Random joke experience

The root route, `/`, selects one random joke where `is_approved=True` and `is_deleted=False`. By default, jokes tagged `nsfw` are excluded from random selection. A visitor may explicitly enable NSFW jokes with the content-preference control described in Section 13. The page displays:

- Setup and punchline.
- Joke ID, submitter, and submission date.
- Linked tags.
- Configured reaction choices and current totals.
- Instructions for loading another joke.
- Navigation and collection statistics.

Both the setup and punchline link back to `/`, so selecting either loads another random joke. Refreshing the page has the same effect.

### 5.2 Stable joke URLs

Individual jokes have two public URL forms:

- `/id/<id>/`
- `/slug/<slug>/`

The slug is generated from the setup. When a setup changes, the slug is regenerated. If the desired slug is already in use, a numeric suffix is appended.

If the requested joke is soft-deleted, the site substitutes a random approved joke. A missing ID or slug returns HTTP 404.

### 5.3 Search and discovery

`/search/?q=<term>` searches:

- Tags containing the term, case-insensitively.
- Submitter names containing the term, case-insensitively.

Results are deduplicated, ordered newest-first, and paginated at ten jokes per page. Each result links to both the numeric and slug form of the joke URL. Tags and submitter names throughout the site link back into this search.

Search intentionally does not search joke setup or punchline text in the current implementation.

### 5.4 Joke submission

`/add-a-joke/` accepts:

- Submitter name.
- Setup.
- Punchline.
- Optional space-separated tags.
- Optional email address used only to notify the submitter if this joke is approved.
- An invisible reCAPTCHA response.

All text fields are trimmed and required except tags. Submitter names that impersonate site administration, use the example placeholder name, or contain an email address are rejected. Tags are normalized to lowercase and must satisfy the `Tag` model's validation rules.

A successful submission creates an unapproved joke and preserves the submitter name in the next blank form. Moderation is therefore required before the joke enters the random public rotation. When an approval notification is requested, the site verifies the address before retaining it for that purpose and erases it after notification or expiry as described in Section 15.5.

### 5.5 Reactions

The canonical reaction set is configured through `NCJM_ALLOWED_REACTIONS`, with a built-in default of:

| Emoji | Meaning |
|---|---|
| 😠 | angry |
| 🥱 | boring |
| 🫤 | meh |
| 🙄 | eyeroll |
| 🤣 | hilarious |
| 🤩 | amazing |

Each joke stores aggregate reaction counts in a JSON object. A separate `ReactionTracker` record stores the joke, IP address, and user agent used for a reaction. A uniqueness constraint prevents that fingerprint from reacting to the same joke more than once, regardless of which reaction was selected.

The server validates that the requested emoji is part of the configured reaction set. The browser updates the displayed count after a successful request and alerts the visitor when the reaction is rejected.

### 5.6 Moderation and deletion

New jokes default to unapproved. Administrators can approve or unapprove jokes individually or in bulk.

Normal deletion is soft deletion: `is_deleted` is set to `True`, retaining the record for administrative use. Hard deletion permanently removes the joke. When a joke is hard-deleted, tags used by no other jokes are also removed.

The default joke list in Django Admin hides soft-deleted jokes unless the deleted-state filter is explicitly used.

### 5.7 JSON API

API routes are mounted only when `NCJM_API_ENABLED` is enabled. The versioned base path is `/api/v1/`.

| Method and route | Behavior | Access |
|---|---|---|
| `GET /reactions/options/` | Return the canonical reaction choices | Public |
| `GET /jokes/` | List visible jokes; filter by submitter or tag | Public |
| `POST /jokes/` | Create a joke | Authenticated |
| `GET /jokes/random/` | Return one random visible joke | Public |
| `GET /jokes/<id>/` | Return one visible joke | Public |
| `PATCH/PUT /jokes/<id>/` | Edit a joke | Authenticated |
| `DELETE /jokes/<id>/` | Soft-delete; `?hard=true` requests permanent deletion | Authenticated; staff for hard delete |
| `POST /jokes/<id>/reactions/` | Record one reaction | Authenticated |
| `GET /tags/` | List tags | Public |
| `POST /tags/` | Create a tag | Authenticated |
| `GET/PATCH/DELETE /tags/<id>/` | Retrieve or modify a tag | Read public; writes authenticated |
| `GET /tags/<tag>/jokes/` | List visible jokes with a tag | Public |
| `GET /submitters/` | List submitters with visible-joke counts | Public |
| `GET /submitters/<name>/jokes/` | List visible jokes by submitter | Public |

List endpoints use page-number pagination with a default page size of 20. Anonymous requests are throttled at 120 per hour and authenticated requests at 1,000 per hour.

Handled API errors use a common envelope:

```json
{
  "error": {
    "status": 400,
    "code": "validation_error",
    "message": "Bad request.",
    "details": {}
  }
}
```

## 6. Data model

### 6.1 Joke

The primary aggregate contains:

- Creation timestamp.
- Approval and soft-deletion flags.
- Setup and punchline.
- Submitter name.
- Unique generated slug.
- Many-to-many tags through `JokeTag`.
- A JSON mapping of allowed reaction emojis to aggregate counts.

The model enforces different setup and punchline values, supported reaction keys, and non-negative integer reaction counts.

### 6.2 Tag

A tag has a unique lowercase label and creation timestamp. Tag text must contain at least three characters and is checked for case-insensitive uniqueness.

### 6.3 JokeTag

`JokeTag` is the explicit many-to-many join between jokes and tags. Each joke/tag pairing is unique and records when the relationship was created.

### 6.4 ReactionTracker

`ReactionTracker` records a joke, IP address, user agent, and timestamp. The combination of joke, IP address, and user agent is unique. Deleting a joke cascades to its trackers.

## 7. System architecture

### 7.1 Current application architecture

The application is a single Django deployment:

```text
Browser / API client
        |
        v
Host Caddy (TLS termination and canonical redirect)
        |
        v
Internal Nginx (static files and reverse proxy)
        |
        v
Gunicorn
        |
        v
Django
  |-- ncjm_site: templates, forms, public views, browser reaction endpoint
  |-- api: DRF serializers, endpoints, authentication, error contract
  |-- ncjm: models, admin, settings, migrations
        |
        v
Database configured by DATABASE_URL
```

Static CSS and JavaScript are collected at image-build time and baked into the internal Nginx image. Django is packaged in a non-root Python 3.12 container and run by Gunicorn. The production Compose definition publishes internal Nginx only on a configurable loopback port, keeps PostgreSQL private, and leaves public TLS and certificate renewal to host infrastructure.

### 7.2 Target hosted architecture

NCJM may run on a host that also runs unrelated services, but it must remain entirely unaware of them. The NCJM repository, configuration, network, data model, and deployment procedure contain no other application names, domains, ports, credentials, service discovery, or operational assumptions. Co-location is solely a host-infrastructure concern.

One host-level Caddy instance outside the NCJM project exclusively owns public ports 80 and 443, terminates TLS, applies the canonical-domain redirect, and routes NCJM requests by hostname:

```text
Internet
   |
   v
Caddy :80/:443
   |-- nikoscornyjokemachine.com ----> NCJM private upstream
   |-- www.nikoscornyjokemachine.com -> canonical redirect
   `-- other host routes ------------> outside NCJM's boundary

NCJM Compose project
   |-- Django/Gunicorn
   `-- NCJM-private data services
```

NCJM must not permanently publish ports 80 or 443, and its database may not be exposed publicly. It keeps its own Compose project name, environment file, private network, database/storage volumes, deployment procedure, and restart policy. Deploying or restarting NCJM must not require knowledge of or changes to any unrelated project.

Caddy must preserve the original `Host` and forwarded HTTPS information. Django must trust only the known proxy boundary, use `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`, and configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for the actual HTTPS hostnames. This also resolves incorrect `http://` absolute URLs generated behind the current proxy.

The canonical NCJM hostname is the apex `nikoscornyjokemachine.com`; `www.nikoscornyjokemachine.com` permanently redirects to the apex while preserving the request URI. This behavior is configured explicitly in Caddy rather than relying on DNS or application-side accidents.

### 7.3 Caddy placement options

The existing droplet must be inspected before selecting either topology. Do not run two proxies that compete for ports 80 and 443.

**Host systemd Caddy:** Caddy runs directly on the host. NCJM publishes Gunicorn or an application-local proxy only on a distinct loopback address such as `127.0.0.1:8001`. The port is a placeholder to resolve against the live listener inventory and is private NCJM deployment configuration.

**Containerized Caddy:** Caddy joins a host-managed external Docker network, conventionally `web`. Only Caddy and NCJM's web-facing service join that network from the NCJM project. Caddy proxies to an NCJM-specific network alias, so the application port need not be published on the host. The NCJM database remains attached only to the NCJM-private network. The external proxy network is an infrastructure interface, not an application-level dependency on its other participants.

The chosen pattern should match the proxy already present on the droplet. If Caddy is already installed as a host service, prefer loopback-bound upstreams. If the established infrastructure proxy is containerized, prefer the shared external-network pattern.

### 7.4 Health-check contract

NCJM will expose an internal `GET /health/` endpoint for container health checks and deployment verification. It returns a small JSON response and no application or environment details:

```json
{"status": "ok"}
```

The endpoint returns HTTP 200 only when Django can service the request. The initial liveness check does not query external services. A separate readiness check may later verify database connectivity if the deployment system can distinguish readiness from liveness. Health requests are excluded from Google Analytics and routine access-log noise where practical.

### 7.5 Pre-change server audit and cutover

Before changing the production Compose file, Nginx, Certbot, DNS, firewall, or Caddy configuration, inspect and record:

- Running containers, Compose projects, images, and restart policies.
- Every process listening on public and loopback ports.
- Existing host-level Nginx, Caddy, Apache, and Certbot services and timers.
- Firewall and DigitalOcean cloud-firewall rules.
- Available RAM, swap, disk space, and Docker volume usage.
- DNS records for the NCJM apex and `www` hostnames.
- The exact NCJM checkout, environment-file location, database engine/storage, static-file path, and deployment commands.
- Current TLS certificate ownership and renewal mechanism.

Use a staged cutover:

1. Establish and test Caddy without changing the live hostname route.
2. Reconfigure NCJM to a private upstream and verify `/health/` locally.
3. Add the NCJM Caddy route and canonical redirect, then validate headers, static assets, CSRF, and absolute HTTPS URLs.
4. Remove NCJM's direct 80/443 publication and retire its application-local TLS renewal only after Caddy is serving valid certificates.
Keep a tested rollback path to the previous NCJM proxy configuration throughout cutover. Avoid unnecessary interruption to existing NCJM traffic.

## 8. Configuration

Runtime configuration is environment-based. Important settings include:

- `DATABASE_URL`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CORS_ORIGIN_WHITELIST`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `NCJM_API_ENABLED`
- `NCJM_ALLOWED_REACTIONS` (optional JSON override)
- `RECAPTCHA_PUBLIC_KEY`
- `RECAPTCHA_PRIVATE_KEY`

The API feature flag controls both the `/api/` and `/oauth2/` route trees.

## 9. Security and abuse controls

The current design uses:

- Django CSRF protection for browser POST requests.
- Invisible reCAPTCHA for public joke submission.
- OAuth2 or Django session authentication for API writes.
- Staff authorization for permanent API deletion and visibility of unapproved API records.
- Per-client API throttling.
- Reaction deduplication by IP address and user agent.
- Nginx user-agent filtering for a configured set of bots and scanners.
- Environment variables for secrets and deployment-specific settings.

Reaction fingerprints contain personal/telemetry data and should be handled as operationally sensitive data even though they do not identify a registered account.

## 10. Testing strategy

The existing automated suite covers:

- Template discovery.
- Accessible labels for reaction controls.
- Public API visibility rules.
- API authentication requirements.
- Joke and tag serialization.
- Reaction validation and duplicate conflicts.
- Reaction configuration normalization.
- Soft- versus hard-deletion authorization.
- Tag and submitter API queries.
- The API error envelope.

Future regression coverage should prioritize the public visibility boundary, submission flow, stable URLs, search pagination, concurrent reactions, and production configuration.

## 11. Operational expectations

- Production should run with `DJANGO_DEBUG=False`.
- Database migrations and static collection must run as part of deployment.
- In the current deployment, TLS certificates are renewed by Certbot and consumed by Nginx. In the target shared-droplet deployment, the single host-level Caddy instance owns TLS and certificate renewal for both applications.
- Only Caddy publishes public HTTP/HTTPS ports in the target architecture; application upstreams bind to loopback or a private shared proxy network.
- NCJM retains its own Compose project, environment file, private network, database, volumes, deployment procedure, and restart policy, with no references to unrelated applications.
- Database ports and application upstream ports are not exposed to the public network.
- The API should be deliberately enabled or disabled through its feature flag.
- Moderators should periodically review the approval queue and orphan filters.
- Database and certificate data require backups outside the application container.

## 12. Future design: rich jokes

### 12.1 Product concept

A rich joke is a joke that benefits from a presentation other than the site's current setup/punchline pair. It may be long, but length alone does not define it. Examples include:

- A shaggy-dog story with a title and continuous narrative.
- A joke whose setup is several paragraphs and whose ending is part of the same narrative.
- A monologue, sketch, song, or spoken performance represented by an audio or video link.
- A traditional joke accompanied by a transcript, attribution, translation, performance notes, alternate wording, or explanatory liner notes.

The distinction is therefore structural:

- A **classic joke** has a setup followed by a punchline.
- A **rich joke** has a title and a primary text document, with optional notes and linked media.

“Classic” replaces the experimental branch's term “corny joke,” because both formats belong in Niko's Corny Joke Machine and either format may be corny. “Rich joke” replaces “long joke,” because a short performed or annotated joke may still require the richer representation.

### 12.2 Experience goals

Rich jokes should:

- Preserve the immediacy of the random-joke experience for classic jokes.
- Provide comfortable long-form reading with paragraphs, lists, emphasis, quotations, and section breaks.
- Let the telling be primary when an audio or video performance is available.
- Keep a readable text representation for accessibility, search, moderation, and link longevity.
- Allow editorial context without mixing it into the joke itself.
- Work when third-party media is unavailable, blocked, removed, or unsupported.
- Share the existing approval, deletion, tagging, submitter, slug, and reaction behavior.

### 12.3 Rich joke content

A rich joke contains:

- **Title:** Required short identifying text used for headings and slug generation.
- **Body:** Required long-form text. For linked performances this acts as a transcript or close textual representation; for written jokes it is the joke itself.
- **Liner notes:** Optional public editorial context, such as provenance, telling advice, alternate wording, translation notes, or credits.
- **Spoiler notes:** Optional public content hidden behind an explicit reveal control, such as an explanation or discussion of the punchline.
- **Media links:** Zero or more ordered links to supported third-party performances or related material.

The body and notes use a deliberately limited Markdown subset. Stored source remains plain text; rendered HTML is generated with raw HTML disabled and sanitized before display. The first release should support paragraphs, line breaks, emphasis, strong emphasis, block quotes, and lists. Images, arbitrary HTML, scripts, iframes, and user-authored embed markup are not accepted.

The transcript does not need to be a legally exact transcript in the first release, but the submission UI should ask contributors to identify material that is partial, approximate, translated, or adapted. This can initially be stated in liner notes rather than represented by another field.

### 12.4 Media behavior

Media is an enhancement, never the only usable representation of a rich joke.

For each media link, the application stores the original URL, display order, an optional contributor-supplied label, and normalized provider metadata. The first supported providers should be YouTube and SoundCloud. Additional providers can be added through provider adapters without changing the joke schema.

The server must:

1. Parse the URL using an allowlisted provider adapter.
2. Require HTTPS and a recognized provider hostname.
3. Extract and store a stable provider identifier where possible.
4. Produce the canonical embed URL itself.
5. Reject credentials, local-network targets, `javascript:` URLs, arbitrary iframe markup, and unrecognized providers.

The browser initially shows a normal outbound link and an optional privacy-conscious embed. Third-party players should use the most privacy-preserving supported domain and parameters—for example YouTube's privacy-enhanced embed—and should be lazy-loaded. The UI must identify the provider and make clear that playing embedded media contacts that third party. A plain link remains available when embedding fails.

The system should not fetch arbitrary submitted URLs during the request that creates a joke. This avoids server-side request forgery and keeps submission reliable. Provider metadata can be derived locally from the URL or fetched later by a tightly constrained background process if that capability becomes necessary.

### 12.5 Presentation and navigation

The random homepage may select either format. Classic jokes retain their large setup/punchline presentation. Rich jokes use a reading-oriented layout with:

- Title at the top.
- Optional media player or media-link group.
- Body rendered as a long-form article.
- Liner notes in a visually distinct section.
- Spoiler notes collapsed by default using an accessible disclosure control.
- The existing metadata, tags, reactions, navigation, and statistics below the content.

Clicking inside a long body must not unexpectedly navigate away. Only an explicit “another joke” control should request a new random joke on the rich layout. Stable ID and slug URLs continue to address both formats.

Search results add a format indicator and use the setup for classic jokes or title for rich jokes. A later full-text-search project may index rich titles, bodies, and notes; that is not required for the first rich-joke release.

### 12.6 Submission and moderation

The submission page begins with a clear format choice:

- **Classic:** setup and punchline.
- **Rich:** title, body/transcript, optional liner notes, optional spoiler notes, and media links.

Changing the format reveals the appropriate fields without maintaining two completely separate submission workflows. Both formats share submitter, tags, captcha, validation messages, and success behavior.

Moderators must be able to preview rendered Markdown and media presentation without approving the joke. Admin lists should show the joke format and a common display title. Media URLs and rendered outbound links must remain visibly inspectable during review.

The first release should limit the number of media links per joke to a small configured value, initially three, to keep pages focused and reduce moderation overhead.

### 12.7 Data-model implementation

The initial `split-joke-model-into-corny-and-long-jokes` branch explored Django multi-table inheritance with `JokeBase`, `CornyJoke`, and `LongJoke`. It established several valuable requirements: shared joke metadata, type-specific templates and forms, Markdown-capable transcript/notes fields, and provider validation. It should be treated as a prototype rather than merged directly because it predates the current API and reaction work and contains incomplete migration and model behavior.

The recommended implementation evolves the existing `Joke` table in place. This reduces migration risk, preserves every joke ID and foreign key, and avoids polymorphic queryset/downcasting complexity in the homepage, search, admin, reactions, and API.

Add these fields to `Joke`:

| Field | Type | Purpose |
|---|---|---|
| `format` | short enum/string | `classic` or `rich`; indexed; defaults to `classic` |
| `title` | nullable short text | Required for rich jokes; absent for classic jokes |
| `body` | nullable text | Required Markdown source for rich jokes |
| `liner_notes` | blank text | Optional Markdown source shown after the body |
| `spoiler_notes` | blank text | Optional Markdown source collapsed by default |

Retain `setup` and `punchline`, but allow them to be null at the database level. Add a database check constraint, backed by model/form/serializer validation:

- `classic` requires nonblank `setup` and `punchline`, with rich fields empty.
- `rich` requires nonblank `title` and `body`, with setup and punchline empty.

Add a `JokeMedia` model:

| Field | Type | Purpose |
|---|---|---|
| `joke` | foreign key | Owning joke; cascade on permanent deletion |
| `position` | positive integer | Stable display order within the joke |
| `url` | URL | Contributor-supplied canonical or share URL |
| `provider` | short enum/string | Normalized provider such as `youtube` or `soundcloud` |
| `provider_key` | short text | Provider-specific video, track, or set identifier |
| `label` | optional short text | Accessible human-readable label |
| `created_at` | timestamp | Audit and maintenance timestamp |

Enforce uniqueness on `(joke, position)` and, where useful, `(joke, provider, provider_key)`. Do not store third-party embed HTML.

Add common model properties or methods:

- `display_title`: setup for classic jokes, title for rich jokes.
- `content_for_slug`: the same type-aware value used to generate the initial slug.
- `clean()`: enforce the format-specific field contract and media-independent content requirements.
- A centralized public visibility queryset/manager used by every public surface.

Slugs should become immutable on this release so rich-joke edits do not break shared links. Existing slugs and numeric IDs remain unchanged.

### 12.8 API implementation

The joke read representation adds `format` and exposes a discriminated content object while retaining current top-level fields during a compatibility period:

```json
{
  "id": 812,
  "format": "rich",
  "content": {
    "title": "The Aristocrats",
    "body": "A family walks into a talent agent's office...",
    "liner_notes": "Traditionally improvised by the teller.",
    "spoiler_notes": "The humor depends on contrast with the final line."
  },
  "media": [
    {
      "provider": "youtube",
      "url": "https://www.youtube.com/watch?v=example",
      "label": "Recorded performance",
      "position": 1
    }
  ]
}
```

Write validation uses `format` as the discriminator. Classic requests require `setup` and `punchline`; rich requests require `title` and `body`. Unsupported or malformed media URLs return field-specific validation errors through the existing error envelope.

During the compatibility period, classic responses continue to populate `setup` and `punchline`. Clients should migrate to `format` plus `content`. A future API version may remove the duplicated legacy shape, but rich-joke support alone does not require a version break.

### 12.9 Migration and delivery plan

Implement rich jokes in small reversible stages:

1. **Schema foundation:** Add `format` and nullable rich fields with all existing rows defaulted to `classic`. Add `JokeMedia`. Do not change public rendering yet.
2. **Domain layer:** Add format-aware validation, display helpers, immutable slug behavior, provider adapters, and shared public-visibility queries.
3. **Read paths:** Update admin, homepage, stable URLs, search, and API serializers to read both formats. Add rich templates and Markdown rendering.
4. **Moderation:** Add rich-joke admin editing and preview. Verify that unapproved rich jokes are inaccessible outside staff surfaces.
5. **Write paths:** Add the format-switching public form and API writes. Keep media limits and provider allowlists server-controlled.
6. **Production rollout:** Deploy read support before enabling public rich submissions. Create and approve a staff-authored rich joke as a production smoke test, then enable the submission option.
7. **Follow-up:** Consider full-text search, additional providers, transcript status, attribution fields, and historical slug redirects based on actual use.

The data migration should not copy existing setup/punchline content into `body`: all existing records are valid classic jokes. The experimental branch's migration must not be reused unchanged because the active branch has newer schema and API migrations.

### 12.10 Acceptance criteria

- Every existing joke retains its ID, slug, tags, reactions, approval state, deletion state, and submitter after migration.
- Existing classic joke pages and API representations continue to work.
- An approved rich joke can be selected randomly and opened by ID or slug.
- An unapproved rich joke cannot be found through any anonymous page or API route.
- A rich joke remains readable and navigable with JavaScript disabled and with all third-party media blocked.
- Markdown cannot inject raw HTML, scripts, unsafe links, or arbitrary embeds.
- YouTube and SoundCloud links are normalized and rendered through provider-owned code paths.
- Unsupported media URLs receive a clear validation error and are never fetched by the application server during submission.
- Media has accessible labeling, keyboard-operable controls, and a normal outbound-link fallback.
- Reactions, tags, soft deletion, hard deletion, pagination, and moderation behave the same for both formats.
- Automated tests cover model constraints, migrations, provider parsing, sanitization, public visibility, forms, templates, admin behavior, and API compatibility.

## 13. Future design: NSFW random-joke preference

### 13.1 Product behavior

Some jokes are classified by the existing `nsfw` tag. These jokes must not appear in the homepage's random-joke slot unless the visitor explicitly chooses to include them.

The homepage provides an accessible toggle labeled **Include NSFW jokes**. Its behavior is:

- Off by default for a visitor with no saved preference.
- Off means the random pool excludes every joke carrying the `nsfw` tag.
- On means NSFW jokes are eligible for random selection alongside all other visible jokes; it does not request an NSFW joke specifically.
- Changing the toggle saves the preference and immediately loads a new joke from the newly selected pool.
- The selected state persists across visits in the same browser.
- Turning the toggle off while viewing a randomly selected NSFW joke immediately replaces it with a safe joke when one is available.
- The preference applies equally to classic and rich jokes.

This feature is a content preference, not an age-verification system. It reduces surprise but does not certify content safety or the visitor's age.

### 13.2 Scope of filtering

The first release applies the preference to random selection on:

- The server-rendered homepage.
- The API random-joke endpoint.

Stable `/id/` and `/slug/` links remain reachable so shared URLs do not become context-dependent or appear broken. Search results may continue to include NSFW jokes because a search is an intentional discovery action, but every NSFW result and joke page must display a clear **NSFW** label before the punchline, body, or embedded media.

The API list endpoint retains its existing catalog behavior in the first release. It should expose whether a joke is NSFW so clients can implement their own filtering. A later privacy/content-controls project may extend safe-by-default behavior to search and list endpoints, but that expansion should be a deliberate compatibility decision.

### 13.3 Classification rule

A joke is NSFW when it has a tag whose normalized `tag_text` is exactly `nsfw`, case-insensitively. Classification is derived from the existing tag relation rather than copied into another boolean field.

This avoids two sources of truth and lets moderators classify or declassify a joke through existing tag management. Exact matching prevents tags such as `not-nsfw` from being treated as NSFW.

Add a domain-level queryset method rather than scattering tag predicates across views:

```python
Joke.objects.publicly_visible().for_content_preference(include_nsfw=False)
```

Conceptually, safe-only filtering is:

```python
queryset.exclude(tags__tag_text__iexact="nsfw")
```

The resulting queryset must use `distinct()` whenever joins could duplicate jokes. The visibility method continues to enforce approval and soft-deletion rules; the content-preference method only adjusts NSFW eligibility.

### 13.4 Preference storage and request flow

Because random selection happens on the server, the preference must be available with every homepage request. Store it in a signed, first-party cookie rather than browser `localStorage` so the initial response is correct without client-side replacement or flashing hidden content.

Recommended cookie behavior:

- Name: `ncjm_include_nsfw`.
- Values: signed `true` or `false`; missing, invalid, or expired values resolve to `false`.
- Lifetime: one year.
- Attributes: `Secure`, `SameSite=Lax`, and `Path=/`.
- `HttpOnly` may be enabled because server-rendered forms do not require JavaScript to read the preference.
- The cookie contains only the content preference and no user identifier.

The toggle is a small POST form protected by CSRF. Post to a dedicated route such as `/preferences/nsfw/` with the desired boolean value. The view validates the value, sets the signed cookie, and redirects to a safe local `next` location or `/`. It must not accept arbitrary external redirect targets.

JavaScript may progressively enhance the control, but the form must work without JavaScript. The preference update endpoint does not require an account.

### 13.5 Random selection implementation

The homepage view should:

1. Read and validate the signed preference cookie.
2. Build the shared publicly visible queryset.
3. Exclude the exact `nsfw` tag unless the preference is enabled.
4. Select a random eligible joke.
5. Pass `include_nsfw` and `joke_is_nsfw` to the template.
6. Render the normal empty state if the selected pool contains no jokes.

Avoid duplicating this logic in the API. Introduce a small domain/service function that accepts a queryset and `include_nsfw` value, or expose both operations through the shared queryset class.

For the API random endpoint, use an explicit query parameter:

```text
GET /api/v1/jokes/random/?include_nsfw=true
```

The parameter defaults to false and is parsed strictly using the API's standard boolean validation. Unlike the browser preference, the API value is request-scoped and is not stored in a cookie. The response includes `is_nsfw` as a derived read-only field.

### 13.6 Template and accessibility behavior

The toggle should appear near the “another joke” control rather than inside the reaction choices. Use a native checkbox or switch semantics with a persistent text label; color alone must not indicate the state.

When the current joke is NSFW:

- Render a visible `NSFW` badge near its title or setup.
- Put the label before rich media and long-form content in document order.
- Include the classification in accessible text.
- Do not autoplay linked media.

The initial version does not blur or hide the selected content after the visitor has enabled NSFW jokes. If a warning/reveal screen is later added, it must work with a keyboard and assistive technology and must not rely solely on hover.

### 13.7 Moderation behavior

Moderators classify content by applying the normalized `nsfw` tag. The admin joke list should expose an `is_nsfw` indicator and an NSFW filter so classification can be audited efficiently.

Deleting or renaming the canonical `nsfw` tag changes classification immediately. To reduce accidental policy changes, the admin should warn before renaming or deleting that tag when it is attached to jokes. A future implementation may protect designated system tags, but that is not required for the first release.

### 13.8 Statistics

The existing total approved-joke count remains the total catalog count. Add no second number unless it materially helps visitors. If an eligible-pool count is later displayed, its label must distinguish “jokes available with this preference” from total approved jokes.

The queue count is unaffected by the visitor's NSFW preference.

### 13.9 Delivery plan

1. Add the shared visibility and NSFW-preference queryset methods with unit tests.
2. Add the derived `is_nsfw` property/serializer field and admin indicator/filter.
3. Update homepage random selection to default to safe-only.
4. Add the signed-cookie preference endpoint and progressively enhanced toggle.
5. Add the visible NSFW badge to stable pages and search results.
6. Apply safe-by-default behavior and the explicit override to the API random endpoint.
7. Deploy with a smoke test covering anonymous defaults, both toggle states, persistence, and a catalog containing only NSFW jokes.

### 13.10 Acceptance criteria

- A new visitor never receives an NSFW-tagged joke from the homepage random pool.
- Enabling the toggle makes both safe and NSFW jokes eligible.
- Disabling it prevents subsequent random selection of NSFW jokes.
- The preference survives refreshes and later visits in the same browser.
- A missing, expired, malformed, or tampered preference cookie fails closed to safe-only mode.
- Direct ID and slug links remain stable and visibly label NSFW content.
- Search results visibly identify NSFW jokes before a visitor follows the link.
- Classic and rich jokes follow identical classification rules.
- The API random endpoint is safe-only unless `include_nsfw=true` is supplied.
- The API exposes a derived `is_nsfw` value without introducing a second classification field in the database.
- The feature works without JavaScript and the toggle is keyboard- and screen-reader-operable.
- No preference endpoint permits an external redirect.
- Empty eligible pools render a defined empty state rather than invalid page data or JavaScript.

## 14. Future design: responsive site redesign

### 14.1 Goals

The redesign should modernize presentation and mobile behavior without turning NCJM into a generic content site. The joke remains the dominant object on every page. The existing directness, bold typography, lowercase voice, blue/gray palette, and low-friction “another joke” interaction are part of the product identity and should inform—not prevent—the redesign.

The redesign must:

- Work from small phone screens through wide desktop displays.
- Keep classic jokes immediately scannable and make rich jokes comfortable to read.
- Make “another joke,” NSFW preference, reactions, tags, and submission easy to operate by touch and keyboard.
- Establish consistent components for buttons, forms, messages, tables, badges, disclosures, and media.
- Meet WCAG 2.2 AA as the practical accessibility target.
- Avoid layout shifts and unnecessary JavaScript.
- Preserve stable URLs and server-rendered functionality.

### 14.2 Information architecture

The primary navigation should contain:

- Another joke / home.
- Submit a joke.
- Search or browse.
- The NSFW preference.

Donation and creator links remain available but should not compete with the joke itself. On small screens, secondary links may move into the footer or a compact menu, provided the menu works without pointer-hover behavior.

Classic joke pages retain strong visual separation between setup and punchline. Rich joke pages use a narrower reading measure, restrained typography, and explicit sections for media, transcript/body, liner notes, and spoiler notes.

### 14.3 Responsive implementation

Start mobile-first using the existing server-rendered templates and plain CSS. Introduce design tokens as CSS custom properties for color, type scale, spacing, borders, content widths, and focus states. Prefer modern layout primitives such as Grid, Flexbox, `min()`, `max()`, and `clamp()` over device-specific positioning.

Initial responsive targets are behavioral rather than tied to specific devices:

- **Compact:** single-column layout, touch-sized controls, wrapped metadata, scrollable or card-based search results.
- **Medium:** expanded navigation and more horizontal room for metadata and forms.
- **Wide:** constrained reading widths rather than scaling joke text indefinitely.

Add `<meta name="viewport" content="width=device-width, initial-scale=1">`. Remove fixed form widths and large fixed font sizes that overflow narrow screens. Search tables should either reflow into labeled result cards on compact screens or provide an intentionally accessible horizontal container.

JavaScript remains progressive enhancement. Random selection, forms, NSFW preference, reaction submission, notes disclosure, and media fallbacks must retain a server-rendered path wherever practical.

### 14.4 Design and delivery process

1. Add analytics instrumentation and capture a pre-redesign baseline.
2. Inventory every existing template state, including empty, validation-error, duplicate-reaction, long-content, and pagination states.
3. Create reusable base components and design tokens without changing information architecture.
4. Redesign the homepage and both classic/rich joke presentations mobile-first.
5. Redesign search, submission, and admin-adjacent moderation previews.
6. Test keyboard navigation, screen readers, zoom, reduced motion, high contrast, long unbroken text, and representative mobile viewports.
7. Compare post-release analytics and performance with the baseline.

### 14.5 Acceptance criteria

- No supported public page requires horizontal viewport scrolling at 320 CSS pixels, except an explicitly contained data region with an accessible alternative.
- Interactive targets are large enough for touch and have visible keyboard focus.
- Text remains readable at 200% zoom and browser text enlargement.
- Classic and rich joke layouts handle very short and very long content without overlap or clipping.
- Core navigation and forms work without JavaScript.
- Automated template tests and browser-level viewport tests cover the principal routes and states.
- The redesign does not change stable joke URLs or public visibility rules.

## 15. Future design: Joke of the Day subscriptions

### 15.1 Delivery channels

“Joke of the Day” is a recurring publishing feature rather than a single transport. Delivery should be introduced in this order:

1. **RSS/Atom feed:** Lowest operational and privacy cost. Readers pull the daily joke through a feed reader; no subscriber data is stored.
2. **Email:** Broadly accessible and reliable. NCJM sends one message per configured schedule through a transactional email provider.
3. **Web push:** Optional later channel for visitors who want browser/device notifications. It requires service-worker, subscription-key, browser-permission, and endpoint-expiration handling.

SMS, messaging apps, and social-network posting are not part of the initial design. They add cost, account/provider dependencies, and jurisdiction-specific consent requirements without establishing demand first.

### 15.2 Daily edition

Generate one canonical `DailyJokeEdition` for each publication date rather than randomly selecting a different joke for every subscriber. An edition records:

- Publication date and status (`scheduled`, `published`, `failed`, or `cancelled`).
- Selected joke.
- Selection timestamp and selection method.
- Optional editorial subject/title and introduction.
- Publication timestamps for each enabled channel.

The default selection pool contains approved, non-deleted, non-NSFW jokes. An NSFW recurring edition is out of scope initially; a simple daily message should never surprise a subscriber with explicit material. A joke should not repeat until the eligible catalog has been exhausted, with recent appearances tracked through editions.

Edition URLs point to the stable joke page with campaign parameters suitable for aggregate analytics. If a joke is soft-deleted before publication, the publishing job selects a replacement. Once sent, the edition record remains as an audit record even if the joke is later removed.

### 15.3 Email subscription model

Add a `JokeSubscription` model containing:

- Normalized email address, stored only for delivery.
- Status (`pending`, `active`, `unsubscribed`, `bounced`, or `complained`).
- Preferred timezone and delivery window, if per-timezone delivery is enabled.
- Created, confirmed, unsubscribed, and last-sent timestamps.
- Random confirmation and unsubscribe token digests rather than raw reusable tokens.
- Consent source/version for operational auditing.

Use confirmed double opt-in: submitting an address creates a pending subscription and sends a confirmation link. No daily jokes are sent until confirmation. Every message contains a one-click unsubscribe link that does not require login. Bounce and complaint webhooks disable delivery.

Email addresses are operationally sensitive. They must not appear in analytics, application logs, URLs after confirmation, LLM requests, or public administration exports. The privacy notice must describe the email provider and retention behavior.

### 15.4 Scheduling and delivery implementation

The first implementation can use idempotent Django management commands invoked by the host scheduler:

- `build_daily_joke_edition`: safely creates or retrieves the edition for a date.
- `send_daily_joke_email`: sends the edition in bounded batches and records per-subscription outcomes.
- `publish_daily_joke_feed`: exposes the current and recent editions as RSS/Atom.
- `send_joke_approval_notifications`: sends verified requests queued by approval transitions and performs expiry/redaction cleanup.

Commands must be safe to retry. Use database uniqueness constraints for edition date and recipient/edition delivery records. Do not depend on an in-process timer inside Gunicorn.

If volume, retries, or multiple schedules outgrow host cron/systemd timers, introduce a task queue such as Celery only then. Email should be sent through a provider API with authenticated sending domains, bounce/complaint webhooks, rate limits, and a sandbox mode for development.

Web push, if added, stores a subscriber's push endpoint and encryption keys separately from email subscriptions. Permission is requested only after an explicit visitor action; never on initial page load. Expired or rejected endpoints are removed or disabled automatically.

### 15.5 One-time joke approval notification

The public submission form may include an optional email field labeled **Email me if this joke is approved**. This is a one-time transactional notification, not a mailing-list subscription.

The abuse-resistant flow is:

1. The visitor submits a joke and optional notification address.
2. NCJM creates the unapproved joke and a pending notification request.
3. NCJM emails a time-limited verification link to that address.
4. Following the link confirms that the address owner wants the notification.
5. When a moderator changes the joke from unapproved to approved, an idempotent job sends one approval message containing the stable joke URL.
6. After successful delivery, NCJM deletes or cryptographically erases the address within a short configured period, initially seven days.
7. Unverified requests expire and are erased, initially after seven days. Verified requests for jokes that remain pending expire and are erased after a longer documented limit, initially 180 days.

Verification prevents the submission form from becoming a tool for sending unwanted approval messages to arbitrary addresses. It also gives the recipient a link to cancel the notification before approval.

Add a `JokeApprovalNotification` model containing:

- Joke foreign key.
- Status (`pending_verification`, `waiting_for_approval`, `queued`, `sent`, `cancelled`, `expired`, `bounced`, or `failed`).
- Normalized email address stored with application-level encryption while delivery remains possible.
- A keyed email digest for idempotency and abuse controls; it must not be usable as a public identifier.
- Verification and cancellation token digests, never raw reusable tokens.
- Requested, verified, queued, sent, cancelled, and expiry timestamps.
- Consent-copy version and sanitized delivery outcome.

The encryption key belongs in secret storage rather than the database. Operational views show a masked address and notification status. Application logs, analytics, moderation exports, and LLM requests exclude the address and secret tokens.

Approval notification must be triggered by an actual approval-state transition, including bulk admin approval and API approval—not merely by an admin form view. Queue it through a shared domain service or an `on_commit` handler so every approval path behaves consistently. Delivery runs out of band through the same email-provider integration as subscriptions and is safe to retry. Re-approving a previously approved joke must not send another message for an already completed request.

The approval message contains the joke's stable URL and basic site identity. It does not include analytics identifiers tied to the address, an automatic daily-subscription enrollment, or other marketing content.

The initial feature notifies only on approval. Rejected, deleted, or indefinitely queued jokes do not generate a status email; their notification requests expire and their addresses are erased according to the retention rules. A later rejection-notification feature would require an explicit product decision and updated consent copy.

### 15.6 Relationship to subscriptions

The submission page may separately offer **Also send me the Joke of the Day**, but it must be unchecked by default and clearly distinct from the one-time approval notification. Selecting it starts the normal subscription double-opt-in flow.

The same verification email may confirm both purposes only when the page clearly listed both choices and the visitor explicitly selected both. Internally, NCJM records consent and lifecycle state separately for approval notification and recurring delivery. Cancelling one does not cancel or activate the other.

If an active subscriber uses the same address for approval notification, the system may avoid sending a redundant verification message after securely matching the normalized address, but it still creates a separate one-time notification request. An approval address must never be added to `JokeSubscription` merely because it was supplied with a joke.

### 15.7 Subscription analytics

Track aggregate events such as subscription started, confirmation completed, unsubscribe completed, edition delivered, edition link opened through a normal page visit, bounce, and complaint. Do not send email addresses, confirmation tokens, unsubscribe tokens, or push endpoints to Google Analytics.

Open-tracking pixels are not required. Delivery-provider events and on-site visits provide enough operational signal without covert per-message tracking.

### 15.8 Acceptance criteria

- The feed publishes one stable daily edition and validates as RSS or Atom.
- Email requires confirmed double opt-in and supports one-click unsubscribe.
- A safe joke is selected once per edition and shared by all recipients.
- A retry cannot generate a second edition or duplicate a successful delivery.
- Deleted or newly ineligible jokes are replaced before unsent publication.
- No NSFW joke is delivered by the initial recurring channels.
- Subscriber addresses and secret tokens are excluded from URLs, analytics, and LLM requests.
- Bounce and complaint signals stop future delivery.
- Subscription and delivery functions can be tested without contacting a production email provider.
- A submitter can request one approval notification without joining a recurring subscription.
- Approval notification requires control-of-address verification and includes a cancellation path.
- Every approval path queues at most one notification, and retrying delivery cannot duplicate a successful message.
- Unverified, cancelled, expired, and successfully delivered notification addresses are erased according to the documented retention schedule.
- Rejection, indefinite moderation, soft deletion, and re-approval do not leak the address or cause an unintended message.

## 16. Priority initiative: product analytics

### 16.1 Purpose and priority

Google Analytics should be implemented before the redesign and other major feature releases. It provides the baseline needed to determine how visitors currently discover jokes, use search and reactions, submit content, change the NSFW preference, and return to the site. Analytics is an observability tool for product decisions; it must not become a dependency for application behavior.

Use a production Google Analytics 4 property with separate development/test handling. The measurement ID is supplied through environment configuration and omitted entirely when analytics is disabled.

### 16.2 Measurement plan

Track page views plus a small, documented event vocabulary:

| Event | When it occurs | Allowed parameters |
|---|---|---|
| `random_joke_view` | A random joke is rendered | joke format, NSFW eligibility state; avoid joke text |
| `another_joke` | Visitor explicitly requests another joke | source control, joke format |
| `reaction_attempt` | A reaction control is used | reaction label, joke format |
| `reaction_result` | Server accepts or rejects a reaction | result category; no IP or user-agent |
| `search` | Search results are requested | result count and coarse query category; do not send raw query text |
| `joke_submission_result` | Submission succeeds or fails | joke format and result category |
| `nsfw_preference_changed` | Preference is changed | enabled/disabled |
| `media_opened` | A rich-joke media link/player is activated | provider and joke format |
| `subscription_step` | Subscription state advances | channel and nonidentifying step |

Do not send submitter names, joke setup/body text, search queries, email addresses, URLs containing secret tokens, IP addresses, user-agent strings, form error text, or any other user-provided free text as event names or parameters.

### 16.3 Implementation

- Add `GA_MEASUREMENT_ID` and `GA_ENABLED` environment settings.
- Render the analytics script from one base-template partial only when enabled.
- Establish a strict Content Security Policy allowance for the required Google endpoints rather than broadly allowing third-party scripts.
- Centralize browser event emission in one small JavaScript module with a no-op behavior when analytics is unavailable.
- Emit server-known classifications such as joke format and NSFW state into safe `data-*` attributes; never serialize the whole joke into analytics code.
- Exclude local development, automated tests, admin pages, moderation previews, and health checks.
- Mark internal maintainer traffic for exclusion through GA configuration where practical.
- Define and version the event vocabulary in this document before adding new events.

Where consent is legally required, analytics storage remains disabled until the visitor makes a consent choice. The site must remain fully functional when analytics is blocked or declined. The privacy notice must identify Google Analytics, describe the categories collected, and explain the visitor's controls.

### 16.4 Reporting baseline

Before beginning the visual redesign, collect enough representative production data to establish:

- Device and viewport distribution.
- Landing pages and referral channels.
- Random-joke continuation rate.
- Search usage and result engagement.
- Reaction and submission conversion rates.
- Mobile versus desktop error or abandonment differences.
- Core Web Vitals and page-load trends.

Record the baseline date range and dashboard definitions so the post-redesign comparison uses the same calculations.

### 16.5 Acceptance criteria

- Production page views and documented events appear in GA4 with expected parameters.
- Development, test, admin, and preview traffic is not collected.
- No user-authored text, personal data, reaction fingerprints, or subscription secrets are sent.
- The application behaves identically when analytics scripts are blocked.
- Consent behavior and the privacy notice match the deployment jurisdictions and configuration.
- Event names and parameters are covered by automated rendering/unit tests where possible and verified with a production-safe debug procedure.
- A dated pre-redesign baseline dashboard exists before redesign rollout.

## 17. Future design: LLM-assisted submission moderation

### 17.1 Purpose and boundaries

After a new joke is submitted, NCJM may ask a remote large-language-model service to suggest tags and assess whether the joke should carry the `nsfw` tag. This is decision support for moderators, not autonomous moderation.

The LLM must never:

- Approve, publish, reject, edit, or delete a joke by itself.
- Remove an existing NSFW classification.
- Receive the submitter name, email address, IP address, user agent, captcha data, reaction data, cookies, or analytics identifiers.
- Delay or prevent a valid joke submission when the provider is unavailable.
- Follow instructions contained in joke text as system or developer instructions.

The submitted joke is untrusted content. The moderation prompt treats it strictly as quoted data and requests a schema-constrained response.

### 17.2 Requested analysis

For classic jokes, send only setup and punchline. For rich jokes, send title, body/transcript, and—only if needed for classification—public liner/spoiler notes. Media files and remote media pages are not fetched or transcribed in the first implementation.

Request structured output containing:

- Suggested normalized tags, limited to a configured maximum.
- Existing-tag matches where the supplied candidate vocabulary is sufficiently small.
- An NSFW classification such as `unlikely`, `uncertain`, or `likely`.
- Category flags useful to moderation, such as sexual content, graphic violence, hateful content, drugs, or strong language.
- Confidence values and a short moderator-facing rationale.
- Prompt/schema version and model identifier for reproducibility.

The rationale is private moderation metadata and must never be displayed as an authoritative explanation to the submitter or public.

### 17.3 Conservative NSFW policy

The `nsfw` tag remains the product's source of truth. Recommended automation policy:

- `likely`: automatically add the `nsfw` tag while the joke remains unapproved, and flag the classification for moderator confirmation.
- `uncertain`: do not change tags automatically; highlight the joke for moderator review.
- `unlikely`: do not add or remove the tag.

A moderator can always add or remove `nsfw`. Reanalysis may add a conservative flag but must not silently remove a moderator-applied tag. All automatic and moderator changes should be auditable.

Suggested topical tags are presented for moderator acceptance and are not automatically attached in the first release. This prevents uncontrolled vocabulary growth, incorrect classification, and tags derived from adversarial instructions in the joke.

### 17.4 Processing architecture

Submission succeeds and commits to the database before analysis begins. Create a `JokeModerationAnalysis` record with:

- Joke foreign key.
- Status (`pending`, `running`, `completed`, `failed`, or `superseded`).
- Provider, model identifier, prompt version, and schema version.
- Requested and completed timestamps.
- Structured tag suggestions, NSFW result, category flags, confidence, and rationale.
- Sanitized failure category and retry count.
- A fingerprint of the analyzed joke content so stale results can be detected after edits.

Run analysis outside the web request through an idempotent management command scheduled frequently by the host. As with subscriptions, adopt a task queue later only if latency or throughput warrants it. Use timeouts, bounded retries with backoff, concurrency limits, and a daily cost ceiling. Failure leaves the joke in the normal moderation queue.

Before applying a result, verify that its content fingerprint still matches the joke. An edited joke queues new analysis and marks the old result superseded. Only one current completed analysis is shown by default in admin, with history available for auditing.

### 17.5 Provider abstraction and configuration

Keep provider-specific code behind a small moderation-client interface. Configuration includes:

- Feature-enabled flag.
- Provider and model name.
- Secret API credential.
- Request timeout and retry limit.
- Daily request/token budget.
- Prompt/schema version.
- Confidence threshold for conservatively adding `nsfw`.
- Maximum number of suggested tags.

API credentials remain in environment/secret storage and are never exposed to the browser, database analysis payload, logs, or error pages. Logs contain joke IDs and operational status, not full joke text or provider responses.

### 17.6 Privacy and contributor notice

Sending joke text to a remote provider is a third-party data transfer. The submission page and privacy notice must state that submitted joke content may be processed by an automated external service for tagging and content-safety review. Provider selection must account for data retention, training-use terms, regional processing, security, and deletion controls.

Minimize transmitted data to the joke fields needed for analysis. Do not include database IDs unless operationally necessary; use an ephemeral request identifier when correlation is required. Define a retention period for raw provider responses and prefer storing only validated structured results.

### 17.7 Admin experience

The moderation screen shows:

- Analysis state and age.
- Suggested existing and new tags.
- NSFW classification, confidence, category flags, and rationale.
- Whether `nsfw` was applied automatically.
- Content-changed/stale status.
- Controls to accept selected tags, classify NSFW, dismiss suggestions, or request reanalysis.

The interface must clearly label all results as automated suggestions. Moderator actions are recorded separately from model output.

### 17.8 Evaluation and rollout

Before automatic NSFW tagging is enabled, run the system in shadow mode on a representative, moderator-labeled evaluation set. Measure:

- Precision and recall for the existing `nsfw` tag.
- False-safe errors, which are the highest-risk failure.
- False-positive rate and moderator override rate.
- Tag suggestion acceptance rate and duplicate/synonym rate.
- Provider latency, failures, and cost per submission.
- Performance differences between classic and rich jokes.

Roll out in stages: offline evaluation, production suggestions visible only to moderators, conservative automatic NSFW tagging of unapproved jokes, then periodic quality review. Changing the model or prompt version requires a new evaluation rather than assuming equivalent behavior.

### 17.9 Acceptance criteria

- Submission completes successfully when the remote provider is slow or unavailable.
- Only the minimum joke content is transmitted; identity, telemetry, captcha, subscription, and analytics data are excluded.
- Responses are schema-validated before storage or action.
- Joke text cannot alter the system instructions or requested output contract.
- Stale analysis is never applied after joke content changes.
- The model cannot approve, publish, reject, delete, or silently remove NSFW classification.
- Automatic NSFW tagging is disabled until shadow-mode evaluation meets documented thresholds.
- Moderator overrides and automated changes are auditable.
- Costs, timeouts, retries, and concurrency are bounded.
- Contributor-facing notices accurately describe remote automated processing.

## 18. Recommended feature sequence

The current recommended order balances safety, learning value, and infrastructure cost:

1. Fix the P1/P2 visibility, reaction, HTTPS, and empty-state defects in Appendix A.
2. Add Google Analytics with a privacy-reviewed measurement plan and capture the pre-redesign baseline.
3. Implement the NSFW random-joke preference and classification labels.
4. Deliver the responsive redesign, including rich-joke-ready components.
5. Implement rich-joke schema and read support, followed by moderated submission support.
6. Introduce LLM suggestions in shadow mode, then moderator-visible assistance.
7. Publish the Joke of the Day RSS/Atom feed.
8. Add confirmed-opt-in email delivery and one-time joke approval notifications after operational email and privacy workflows are ready.
9. Consider web push and additional delivery/media providers only after usage demonstrates demand.

## Appendix A: Current known issues

This register records confirmed defects and significant implementation risks found during the 2026-08-28 review. Priorities are relative to this application: P1 is urgent, P2 is important, and P3 is maintenance or polish.

### A.1 Public visibility boundary is inconsistent — P1

**Status:** Confirmed in code.  
**Affected areas:** Search and stable joke URLs.

The random homepage and public API restrict visitors to approved, non-deleted jokes. The HTML search view filters only on `is_deleted=False`, so queued jokes can appear in search. Direct ID and slug lookups also fetch a joke without checking approval, allowing anyone who knows or discovers the URL to view an unapproved joke.

**Desired behavior:** Apply one shared public-visibility queryset to the homepage, search, stable URLs, tag/submitter discovery, and public API.

### A.2 Production API does not match the checked-out design — P2

**Status:** Confirmed against production on 2026-08-28.

The checked-out `api-rewrite` branch documents and implements `/api/v1/`, but the live reaction-options endpoint returns HTTP 404. Production is likely running a revision without these routes or has `NCJM_API_ENABLED` disabled.

**Desired behavior:** Decide whether the API is a production feature. If it is, deploy and smoke-test it; if it is not, mark it explicitly as unavailable in public documentation.

### A.3 Search generates HTTP links on an HTTPS site — P2

**Status:** Confirmed against production on 2026-08-28.

Search-result links built with `request.build_absolute_uri()` use `http://nikoscornyjokemachine.com/...` even though the page is served over HTTPS. Nginx supplies `X-Forwarded-Proto`, but Django is not configured with `SECURE_PROXY_SSL_HEADER`.

**Desired behavior:** Configure trusted proxy HTTPS handling or use relative URLs for internal links.

### A.4 Reaction recording is not atomic — P2

**Status:** Confirmed in code.

Creating the deduplication record and incrementing the JSON aggregate are separate operations without a database transaction or row lock. Concurrent requests can lose count increments, and a failure between operations can leave a tracker without the matching count.

**Desired behavior:** Perform duplicate enforcement and count mutation in one atomic transaction with an appropriate lock or move counts to rows that support atomic database increments.

### A.5 Browser reaction endpoint has incomplete error handling — P2

**Status:** Confirmed in code.

The endpoint does not explicitly handle malformed JSON, missing jokes, invalid emojis, model validation failures, or database integrity races. Some failures can therefore produce HTML error responses or HTTP 500, while the JavaScript always expects JSON. Non-POST requests redirect instead of returning a method error.

**Desired behavior:** Validate input consistently and always return an intentional JSON response with an appropriate HTTP status.

### A.6 Empty public catalog breaks homepage assumptions — P2

**Status:** Confirmed by inspection.

If no approved, non-deleted joke exists, the homepage renders with `joke=None`. The template accesses joke fields and emits `const joke_id = ;`, which is invalid JavaScript.

**Desired behavior:** Render a defined empty-state page and disable reaction controls when there is no visible joke.

### A.7 Reaction identity is easy to evade and may merge unrelated visitors — P3

**Status:** Known design limitation.

IP address plus user agent is not a stable person identifier. Visitors can react again after changing network or browser identity, while multiple people behind the same address with the same browser signature can block one another.

**Desired behavior:** Accept this explicitly as approximate abuse prevention or replace it with a privacy-conscious signed visitor token. Define a retention policy for stored IP addresses and user agents.

### A.8 Slugs are not permanent when joke text changes — P3

**Status:** Confirmed in code.

Editing a setup regenerates its slug, invalidating previously shared slug URLs. Numeric ID links remain stable.

**Desired behavior:** Keep slugs immutable after creation or retain redirects from historical slugs.

### A.9 Tag parsing and help text are inconsistent — P3

**Status:** Confirmed in code and UI.

The form field says tags are comma-separated, its placeholder shows a space-separated example, and the page instructions and save implementation use spaces. Multi-word tags cannot be entered through the public form even though the data model permits them.

**Desired behavior:** Choose and document one parsing format, then share normalization logic between the form and API serializer.

### A.10 Production data cutover is not yet complete — P2

**Status:** Tooling implemented and rehearsed; production migration intentionally not performed.

The production design now declares private PostgreSQL storage and provides guarded SQLite migration tooling. The live database engine, SQLite schema lineage, backup path, and every writer still require confirmation during the host audit. The repository developer database belongs to the experimental long-joke branch and is not compatible with the active one-liner schema without an explicit preservation migration.

**Desired behavior:** Rehearse from a fresh production snapshot, preserve any rich-joke records through an approved schema decision, complete the write-frozen cutover, and retain the frozen SQLite source and PostgreSQL checkpoints through the recovery window.

### A.11 Local development environment is not reproducible as checked out — P3

**Status:** Confirmed on 2026-08-28.

The ignored `.venv` directory points to a Python installation that is no longer available, so the test suite cannot currently run from that environment. The repository supplies dependencies and containers but no single bootstrap command or automated test workflow.

**Desired behavior:** Recreate the virtual environment and add a documented, repeatable setup/test command or CI workflow.

### A.12 Minor markup and navigation defects — P3

**Status:** Confirmed in templates.

- `joke_tags.html` contains an unmatched closing `</li>`.
- The footer's “Add a new joke” link points to `/` instead of `/add-a-joke/`.
- Some CSS class names differ between hyphen/underscore forms, reducing styling consistency.
- The base template lacks a viewport meta tag, limiting mobile layout behavior.

**Desired behavior:** Correct the markup and links, normalize class naming, and add responsive layout coverage.

### A.13 Current proxy stack cannot coexist with a second application — P2

**Status:** Addressed in checked-in configuration; live-host cutover still requires inspection.

The production Compose definition now publishes internal Nginx only to a configurable loopback port and contains no Certbot service. The legacy live deployment may still publish 80/443 until the audited cutover occurs.

**Desired behavior:** After auditing the live server, make the established host-level Caddy instance the exclusive owner of ports 80/443. Expose NCJM only through a loopback-bound port or shared private proxy network, preserve application-private networking, and retire redundant Nginx/Certbot responsibilities through a staged cutover.

### A.14 No internal health endpoint — P3

**Status:** Implemented and container-tested.

NCJM exposes a minimal `/health/` JSON liveness endpoint. Compose also checks PostgreSQL independently and internal Nginx exposes `/nginx-health`.

**Desired behavior:** Add the minimal `/health/` JSON contract from Section 7.4, exclude it from analytics, and use it in container and deployment checks.

## Appendix B: Near-term remediation order

1. Enforce a single public-visibility rule everywhere.
2. Make reaction writes atomic and harden the browser reaction endpoint.
3. Resolve the production/API feature-state mismatch.
4. Correct HTTPS URL generation.
5. Add homepage empty-state behavior.
6. Restore a reproducible test environment and add regression tests for items 1–5.
7. Audit the shared droplet and migrate NCJM behind the single host-level Caddy proxy without competing for ports 80/443.
8. Resolve remaining deployment ambiguity, privacy retention, slug policy, and UI polish items.
