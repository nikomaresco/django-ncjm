# django-ncjm

Niko's Corny Joke Machine is a Django application for sharing, browsing, and reacting to jokes.
It includes a website UI and a versioned JSON API.

Production: https://nikoscornyjokemachine.com

## What This Project Does

- Stores jokes with setup, punchline, submitter name, tags, and reaction counts.
- Supports approval and soft deletion workflows.
- Provides public read endpoints and authenticated write endpoints.
- Tracks reactions with deduplication per IP + user-agent fingerprint.

## Tech Stack

- Python 3.12
- Django 5.1
- Django REST Framework
- OAuth2 Toolkit for API auth

## Local Development

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Provide environment variables in a .env file (database, Django secret key, API toggle, and related settings).
	- Optional: override the allowed reaction set using NCJM_ALLOWED_REACTIONS as JSON.
	- Example:

```env
NCJM_ALLOWED_REACTIONS=[{"emoji":"😠","label":"angry"},{"emoji":"🥱","label":"boring"},{"emoji":"🫤","label":"meh"},{"emoji":"🙄","label":"eyeroll"},{"emoji":"🤣","label":"hilarious"},{"emoji":"🤩","label":"amazing"}]
```
4. Run migrations:

```bash
python ncjm/manage.py migrate
```

5. Start the server:

```bash
python ncjm/manage.py runserver
```

## Google Analytics 4

Analytics is disabled unless it is explicitly enabled. Configure the production
environment with the Measurement ID from the site's GA4 web data stream:

```env
GA_ENABLED=True
GA_MEASUREMENT_ID=G-XXXXXXXXXX
```

Keep `GA_ENABLED=False` in local development and automated test environments.
When enabled, the public site records page views and a limited set of events for
random jokes, searches, submissions, reactions, and requests for another joke.
User-authored joke and search text is not included in event parameters.

## Production deployment

The deployment-ready stack uses a non-root Gunicorn image, an internal Nginx
image with baked static files, and a private PostgreSQL service. Internal Nginx
binds only to loopback by default so a host-managed reverse proxy can own public
ports 80 and 443.

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the host audit, environment,
health checks, resource limits, release and rollback commands, and the rehearsed
SQLite-to-PostgreSQL migration process. Do not run the production database
cutover without completing the rehearsal and write-freeze checklist.

## API Overview

Base URL (production): https://nikoscornyjokemachine.com/api/v1/

Authentication model:
- Read endpoints are public.
- Write endpoints require authentication.

Reaction metadata endpoint:
- GET /reactions/options/
	- Public endpoint returning the canonical allowed reaction set.
	- Each item includes emoji and label.

### Jokes

- GET /jokes/
	- List jokes (paginated)
	- Public sees approved + non-deleted jokes
	- Query params:
		- submitter=<name>
		- tag=<tag_text>
		- approved=<true|false> (staff only)

- POST /jokes/
	- Create joke
	- Requires auth
	- JSON body:

```json
{
	"setup": "What do you call a fake noodle?",
	"punchline": "An impasta.",
	"submitter_name": "grace",
	"is_approved": false,
	"tags": [{ "tag_text": "food" }, { "tag_text": "pun" }]
}
```

- GET /jokes/random/
	- Fetch a random visible joke

- GET /jokes/{id}/
	- Retrieve a joke by id

- PATCH /jokes/{id}/
	- Update a joke
	- Requires auth

- DELETE /jokes/{id}/
	- Soft delete by default
	- Requires auth
	- Optional query param hard=true performs hard delete for staff users only

- POST /jokes/{id}/reactions/
	- Add reaction to a joke
	- Requires auth
	- Only standardized reactions from /reactions/options/ are accepted.
	- JSON body:

```json
{
	"emoji": "🤣"
}
```

### Tags

- GET /tags/
	- List tags (paginated)

- POST /tags/
	- Create tag
	- Requires auth

- GET /tags/{id}/
	- Retrieve tag by id

- PATCH /tags/{id}/
	- Update tag
	- Requires auth

- DELETE /tags/{id}/
	- Delete tag
	- Requires auth

- GET /tags/{tag_text}/jokes/
	- List jokes for a tag (paginated)

### Submitters

- GET /submitters/
	- List submitters with joke_count (paginated)

- GET /submitters/{submitter_name}/jokes/
	- List jokes for a submitter (paginated)

## Consistent Error Contract

All handled API errors return the same envelope shape:

```json
{
	"error": {
		"status": 400,
		"code": "validation_error",
		"message": "Bad request.",
		"details": {
			"setup": ["This field is required."]
		}
	}
}
```

Common status codes:

- 400 validation_error
- 401 not_authenticated
- 403 permission_denied
- 404 not_found
- 409 conflict
- 429 throttled

## Running API Tests

```bash
python ncjm/manage.py test api -v 2
```
