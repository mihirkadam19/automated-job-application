# Indeed Automated Apply Backend

This backend lets one Indeed account get logged in a single time and then have an automated agent search for jobs and apply to them, using Playwright to drive a real browser. It never stores anything about the candidate as a person, only enough about each job and each attempt to track its status over time. Whenever the automation runs into something it should not decide on its own, such as a captcha or a sensitive screening question, it stops and hands control back to a person instead of guessing.

## How to use the API

### POST /sessions

Opens a plain browser window at Indeeds login page and creates a new session record marked as needing verification. Takes no request body.

```bash
curl -X POST http://localhost:8000/sessions
```

### POST /sessions/import

Takes cookies exported from that window (or from any already logged in browser) and stores them encrypted against a session, marking it active. Pass session_id to activate a row created by POST /sessions, or leave it out to create a new row from scratch. storage_state accepts either Playwrights own shape or a plain array of cookie objects exported by a browser extension.

```bash
curl -X POST http://localhost:8000/sessions/import \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "the id returned by POST /sessions, or leave this out",
    "storage_state": {
      "cookies": [ ... ],
      "origins": []
    }
  }'
```

### GET /sessions

Lists every session. Takes no body, and accepts an optional status query parameter such as active or needs_verification.

```bash
curl http://localhost:8000/sessions
curl "http://localhost:8000/sessions?status=active"
```

### GET /sessions/{session_id}

Returns one session. Takes no body.

```bash
curl http://localhost:8000/sessions/the_session_id
```

### POST /sessions/{session_id}/refresh

Opens a browser with the stored session and checks whether it is still logged in. browser_mode is optional and defaults to playwright.

```bash
curl -X POST http://localhost:8000/sessions/the_session_id/refresh \
  -H "Content-Type: application/json" \
  -d '{"browser_mode": "playwright"}'
```

### POST /jobs/search

Opens a browser with a stored session and searches Indeed, returning the results directly without saving them anywhere. Only session_id and query are required, everything else has a default.

```bash
curl -X POST http://localhost:8000/jobs/search \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "the session id",
    "query": "python developer",
    "location": "Remote",
    "limit": 5,
    "headless": true,
    "browser_mode": "playwright"
  }'
```

### POST /applications

Creates or reuses an application record for a job under a session and runs the automated apply flow against it. session_id, job_url, job_title, company, and profile are required. profile is a plain object of whatever candidate facts the apply flow and the screening question logic need, it is never saved.

```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "the session id",
    "job_url": "https://www.indeed.com/viewjob?jk=exampleJobId",
    "job_title": "Backend Engineer",
    "company": "Example Company",
    "external_job_id": "exampleJobId",
    "profile": {
      "full_name": "Jane Doe",
      "email": "jane@example.com",
      "phone": "5551234567",
      "work_authorized": true,
      "requires_sponsorship": false,
      "has_security_clearance": false,
      "desired_salary": 90000
    },
    "resume_path": "/path/to/resume.pdf",
    "headless": true,
    "browser_mode": "playwright"
  }'
```

### GET /applications

Lists applications, optionally filtered by session_id and status query parameters.

```bash
curl http://localhost:8000/applications
curl "http://localhost:8000/applications?session_id=the_session_id&status=manual_action_required"
```

### GET /applications/{application_id}

Returns one application. Takes no body.

```bash
curl http://localhost:8000/applications/the_application_id
```

### POST /applications/{application_id}/resume

Reopens a stalled application (one already marked manual action required) in a visible browser so a person can finish it by hand. profile is required again here since nothing about the candidate was saved from the original attempt.

```bash
curl -X POST http://localhost:8000/applications/the_application_id/resume \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "full_name": "Jane Doe",
      "email": "jane@example.com"
    },
    "resume_path": "/path/to/resume.pdf",
    "browser_mode": "os_chrome"
  }'
```

## Project structure

```
backend/
  main.py                        creates the FastAPI app and registers routers
  requirements.txt
  .env.example                   template for the required environment values
  app/
    config.py                    loads settings from the environment
    api/
      sessions.py                endpoints for creating, importing, and refreshing a session
      jobs.py                    endpoint for searching Indeed with a restored session
      applications.py            endpoints for creating, listing, and resuming an application
    services/
      session_service.py         orchestrates login capture, import, and refresh
      job_search_service.py      orchestrates restoring a session and running a search
      application_service.py     orchestrates running and resuming an application
    automation/
      browser_manager.py         launches the actual browser, either through Playwright or as a plain Chrome process
      login_capture.py           opens the plain browser window used for manual login
      job_search.py              searches Indeed using a restored session
      apply_flow.py              drives the multi step apply wizard
      screening_answers.py       extracts and answers employer screening questions
      challenge_detection.py     recognizes captcha, verification, and blocked pages
      storage_state_crypto.py    encrypts and decrypts the stored session cookies
    db/
      base.py                    database engine and session setup
      models.py                  the IndeedSession, Application, and Checkpoint tables
      init_db.py                 creates the tables on startup
  storage/
    app.db                       the SQLite database file
```

## How to run

A real installation of Chrome is required on the machine running this backend, since the automation drives that actual browser rather than a bundled one.

From inside the backend folder, create a virtual environment and install the dependencies.

```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
playwright install chromium
```

Copy the example environment file and fill in the two required values, a generated Fernet key for encrypting sessions and an Anthropic API key for answering open ended screening questions.

```bash
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Once the environment file is filled in, start the server.

```bash
uvicorn main:app --reload
```

The interactive API docs are then available in a browser at the address printed by uvicorn, normally on port 8000, at the docs path.

## Overall architecture

This backend is a FastAPI module split into three layers. The api layer holds thin routers that validate a request and call a service. The services layer owns the database transaction and decides what status an application or session should move to. The automation layer holds the actual Playwright code that opens a browser and drives Indeed, and it has no knowledge of the database or the HTTP layer at all.

Underneath these layers sits a small SQLAlchemy setup on SQLite with three tables. IndeedSession holds one row per captured login, mainly an encrypted blob of browser cookies and a status such as active or needs verification. Application holds one row per job a user has applied to, with a status such as pending, submitted, failed, or manual action required, plus an attempt count and the last error seen. Checkpoint holds a record of a specific moment where automation stopped and a human was needed, such as a captcha or a one time code, linked back to either a session or an application.

The candidate profile itself (name, contact details, work history, resume location, yes or no facts like work authorization) is never written to the database. It is only ever passed in memory on the request that needs it, used to fill out a form or answer a question, and then discarded. Only job title, company, and job url are stored on an application, never anything about the candidate.

Below are the actual workflows the automation layer carries out, each one triggered by one of the endpoints above.

### Login workflow

1. A request to create a session opens a plain, unmodified Chrome window directly at Indeeds login page and creates a session record marked as needing verification.
2. The person logs in normally inside that window, exactly as they would on their own.
3. Once logged in, the person exports the resulting cookies using a browser extension.
4. Those cookies are sent to the import endpoint, which encrypts them and marks the session active.

```bash
curl -X POST http://localhost:8000/sessions

curl -X POST http://localhost:8000/sessions/import \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "the id returned above",
    "storage_state": {
      "cookies": [ ... ],
      "origins": []
    }
  }'
```

### Session refresh workflow

1. A refresh request decrypts the cookies stored for that session.
2. A browser is opened using those cookies and a page that only a logged in account can reach is visited.
3. Whether that page actually loads as logged in decides if the session stays active or moves back to needing verification.
4. The browser is closed immediately once that check is done.

```bash
curl -X POST http://localhost:8000/sessions/the_session_id/refresh \
  -H "Content-Type: application/json" \
  -d '{"browser_mode": "playwright"}'
```

### Job search workflow

1. A search request decrypts the session it is tied to.
2. A browser is opened with that session already logged in, and Indeeds search page is visited with the requested query and location.
3. The job cards shown on that page are read into a plain list holding each jobs title, company, location, and url.
4. The browser is closed and that list is returned directly in the response. Nothing from this step is saved anywhere.

```bash
curl -X POST http://localhost:8000/jobs/search \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "the session id",
    "query": "python developer",
    "location": "Remote",
    "limit": 5,
    "headless": true,
    "browser_mode": "playwright"
  }'
```

### Apply workflow

1. A request to create an application looks up an existing record for that job under that session, or creates a new one if this is the first attempt.
2. A browser is opened with the session restored and the job page is loaded.
3. The flow works through whatever steps Indeeds own apply wizard presents for that job, choosing or uploading a resume, answering screening questions, and reaching the final review page.
4. If every step completes cleanly, the submit button is pressed and the application is marked submitted.
5. If a challenge appears or a question cannot be answered safely, the run stops there, the application is marked as needing manual action, and a checkpoint record is written describing what caused the stop.

```bash
curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "the session id",
    "job_url": "https://www.indeed.com/viewjob?jk=exampleJobId",
    "job_title": "Backend Engineer",
    "company": "Example Company",
    "profile": {
      "full_name": "Jane Doe",
      "email": "jane@example.com",
      "phone": "5551234567",
      "work_authorized": true
    },
    "resume_path": "/path/to/resume.pdf",
    "headless": true,
    "browser_mode": "os_chrome"
  }'
```

### Resume workflow

1. A resume request only makes sense for an application already marked as needing manual action, and is rejected otherwise.
2. The same apply flow is run again, this time in a visible browser, picking up from the same point that caused the earlier stall.
3. Rather than stopping the instant something cannot be resolved on its own, this run leaves the browser open and waits for the person watching it to finish that step by hand.
4. Once the browser is closed, the last page reached decides whether the application becomes submitted or is recorded as still needing manual action.

```bash
curl -X POST http://localhost:8000/applications/the_application_id/resume \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "full_name": "Jane Doe",
      "email": "jane@example.com"
    },
    "resume_path": "/path/to/resume.pdf",
    "browser_mode": "os_chrome"
  }'
```

## How the browser session is stored and restored

Logging in is never automated, for the reason described above. Because nothing is attached to that plain window, the backend has no way to see when login finishes on its own, which is why the person exports their cookies afterward instead.

On import, those cookies are encrypted using Fernet and only that encrypted value is written to the session row in the database. No plain cookie ever touches disk. From that point forward, no browser process is kept running at all between requests. Every later operation that needs to act as a logged in user, whether searching jobs, applying to one, or resuming one, decrypts that stored value and opens a brand new browser using it, then closes the browser completely once the operation finishes. The single encrypted row in the database is the only thing that persists between calls, and a session can be refreshed at any time to confirm it is still valid.

## How manual verification and failures are handled

While automation is running, every page it lands on is checked for known signs of a challenge. This includes captcha widgets, Cloudflares verification page, and one time code fields asking for something sent by email or text. If a normal automated run hits one of these and it does not clear on its own within a short window, the run stops there rather than trying to guess or bypass it. For an apply run, the application is marked manual action required, and a checkpoint record is created describing what kind of challenge was seen. A search hitting the same kind of challenge has no application to attach that record to, since nothing about a search is saved, so it simply marks the underlying session as needing verification and reports the challenge back in the response, leaving a fresh login import or refresh as the way to clear it.

A separate endpoint lets an operator resume that stalled application, as described in the resume workflow above. It reopens a real, visible browser using the same stored session and continues the same flow from where it left off, waiting for a human to actually finish clearing the challenge or answering whatever question caused the stall.

Playwright is the default way a browser gets launched, and it is the one more likely to get flagged and shown a captcha in the first place. If a session workflow (login, refresh, or search) or the apply workflow reports back that it hit a captcha, the fix is to run that same request again in headed mode, meaning headless set to false and browser_mode set to os_chrome, so a real visible browser opens and a person can clear the challenge directly. This has been confirmed to work in practice, a search that was blocked every time in the default headless mode went through as soon as it was retried headed this way.

```bash
curl -X POST http://localhost:8000/jobs/search \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "the session id",
    "query": "python developer",
    "location": "Remote",
    "limit": 5,
    "headless": false,
    "browser_mode": "os_chrome"
  }'

curl -X POST http://localhost:8000/applications \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "the session id",
    "job_url": "https://www.indeed.com/viewjob?jk=exampleJobId",
    "job_title": "Backend Engineer",
    "company": "Example Company",
    "profile": {
      "full_name": "Jane Doe",
      "email": "jane@example.com"
    },
    "resume_path": "/path/to/resume.pdf",
    "headless": false,
    "browser_mode": "os_chrome"
  }'
```

Screening questions get similar caution. Anything considered sensitive, such as work authorization, visa status, security clearance, criminal history, or demographic questions, is never answered by the language model. It is either filled in directly from an explicit field already present in the candidate profile, or the whole form is left untouched and the application is marked manual action required. Only open ended questions with no sensitive meaning are answered automatically. Any unexpected error during a run, such as a network failure or a page that no longer matches what the automation expects, marks the application failed with the underlying error message recorded, and nothing is retried automatically. A person always has to trigger the next attempt.

## How the solution could be extended to support multiple users

The current design assumes a single account and a single operator, but nothing about the shape of the data prevents scaling it up. A users table could be added with its own identifier, and every session, application, and checkpoint row would carry a reference to which user it belongs to, with every query in the services layer filtered by that reference. An authentication layer, such as an API key or a token checked on each request, would sit in front of the existing routers to establish who is calling.

The encryption approach would also need to change slightly. Today one shared key encrypts every sessions cookies. With many users, that key could still be shared as long as every lookup is properly scoped to the right user, or it could be strengthened by deriving a separate key per user from one master secret, so that even a compromised value cannot be decrypted without knowing exactly whose it is.

Running many users at once also raises resource questions that do not exist for one operator. Each apply or search call opens a real browser, so a limit on how many can run at the same time would be needed to avoid overwhelming the host machine. As request volume grows past what a single process handling requests inline can comfortably manage, the apply flow could move onto a proper background job queue instead of running inside the request itself, and the database could move from SQLite to something like Postgres that handles many simultaneous writers more gracefully.
