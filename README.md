# NAU LMS Report Extractor

A minimal FastAPI web app that logs into an Open edX LMS with a course-team account and submits report-generation jobs for one or many courses. It wraps the original terminal script (`generate_reports.py`) with a simple HTML/CSS/JS UI for non-technical users.

<img width="800" alt="image" src="https://github.com/user-attachments/assets/3c48224d-fa2e-41d7-926c-4506112b6c7a" />

## What it does
- Authenticates to the LMS (account must have `data_researcher` permissions in the course).
- Submits report jobs for each provided course ID.
- Supports pasting course IDs or uploading a `courses.txt` file.
- Shows a per-course success/failure summary.
- Generated report files remain in the LMS (Instructor → Data Download). This app does not download files.

### Supported reports
- get_students_profile
- get_students_who_may_enroll
- get_student_anonymized_ids
- calculate_grades
- problem_grade_report
- ora_data_report
- ora_summary_report
- get_problem_responses (optionally requires a problem block id)
- export_course_certificates (NAU custom)
- export_course_certificates_pdfs (NAU custom)

## Quickstart

### Using Make (recommended)
```bash
make init
```
This will:
- Create a virtualenv at `.venv`
- Install dependencies from `requirements.txt`
- Start the server at http://0.0.0.0:8000

Change the port if needed:
```bash
make run PORT=9000
```

### Manual setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Then open http://localhost:8000 in your browser.

## How to use
1. Open the app in a browser.
2. Fill LMS URL, email, password, and choose a report.
3. Provide course IDs:
   - Paste one course per line in the textarea; or
   - Upload a `courses.txt` file (one line per course). You can mix both; duplicates are removed.
4. Click “Submit Reports”.
5. Check the results list for each course. Download generated files later in the LMS Instructor area.

### Courses file format
- One course per line:
```
course-v1:ORG+COURSE+RUN
```
- For `get_problem_responses`, optionally append a problem block id on the same line, separated by space/comma/semicolon:
```
course-v1:ORG+COURSE+RUN block-v1:ORG+COURSE+RUN+type@problem+block@abcdef
```

## Common failures and fixes
- 401 Unauthorized when submitting:
  - Wrong email/password or the account lacks course permissions (needs Instructor/Data Researcher for that course).
  - Verify you can access Instructor → Data Download in the course.

- 403 Forbidden or error from LMS:
  - The user may not have rights in that course, the course ID is wrong, or the report isn’t enabled.

- Temporary account lock (~30 minutes):
  - Triggered by too many requests quickly. Wait and try later.

- Startup validation errors:
  - Missing `email-validator` or `python-multipart`. Install via `pip install -r requirements.txt`.

- Network/SSL issues:
  - Confirm the LMS URL (e.g., `https://lms.example.com`). Configure proxies if required via `HTTP_PROXY`/`HTTPS_PROXY`.

## Security
- Credentials are sent to this app and used server-side to authenticate to your LMS. Run this in a trusted environment.
- For production, serve over HTTPS and restrict access (VPN, firewall, or SSO in front).

## Project structure
- App entrypoint: `app/main.py`
- Templates: `templates/index.html`
- Static: `static/style.css`, `static/app.js`
- Original CLI script: `generate_reports.py`

## License
MIT (or your organization’s standard license)
