from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, EmailStr
from typing import List, Tuple
import re
import requests


app = FastAPI(title="Open edX Report Generator")

# Static and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


def login_to_lms(lms_url: str, auth_email: str, auth_password: str) -> Tuple[requests.Session, str]:
    """
    Log in to the LMS and return a (session, csrftoken).
    Raises HTTPException on failure.
    """
    session = requests.Session()
    login = session.get(f"{lms_url}/login")
    csrftoken = login.cookies.get("csrftoken")
    auth_r = session.post(
        f"{lms_url}/api/user/v1/account/login_session/",
        data={
            "email": auth_email,
            "password": auth_password,
        },
        headers={
            "X-CSRFToken": csrftoken,
            "referer": f"{lms_url}/login",
        },
    )
    if not auth_r.ok:
        raise HTTPException(status_code=401, detail="Invalid login, check credentials and permissions.")
    return session, csrftoken


def generate_report_url_data(course_id: str, lms_url: str, report: str, additional_info: List[str]) -> Tuple[str, dict]:
    """Map report type to endpoint and payload."""
    if report == "get_students_profile":
        return f"{lms_url}/courses/{course_id}/instructor/api/get_students_features/csv", {}
    elif report == "get_students_who_may_enroll":
        return f"{lms_url}/courses/{course_id}/instructor/api/get_students_who_may_enroll", {}
    elif report == "get_student_anonymized_ids":
        return f"{lms_url}/courses/{course_id}/instructor/api/get_anon_ids", {}
    elif report == "calculate_grades":
        return f"{lms_url}/courses/{course_id}/instructor/api/calculate_grades_csv", {}
    elif report == "problem_grade_report":
        return f"{lms_url}/courses/{course_id}/instructor/api/problem_grade_report", {}
    elif report == "ora_data_report":
        return f"{lms_url}/courses/{course_id}/instructor/api/export_ora2_data", {}
    elif report == "ora_summary_report":
        return f"{lms_url}/courses/{course_id}/instructor/api/export_ora2_summary", {}
    elif report == "get_problem_responses":
        data = {"problem_location": additional_info[0]} if additional_info else {}
        return f"{lms_url}/courses/{course_id}/instructor/api/get_problem_responses", data
    # NAU custom reports
    elif report == "export_course_certificates":
        return f"{lms_url}/nau-openedx-extensions/certificate-export/courses/{course_id}/csv", {}
    elif report == "export_course_certificates_pdfs":
        return f"{lms_url}/nau-openedx-extensions/certificate-export/courses/{course_id}/pdf", {}
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported report '{report}'")


def generate_report_for_course(session: requests.Session, csrftoken: str, lms_url: str, course_id: str, report: str, additional_info: List[str]) -> Tuple[bool, str]:
    """Submit report generation request for a single course. Returns (success, message)."""
    url, data = generate_report_url_data(course_id, lms_url, report, additional_info)
    try:
        report_r = session.post(
            url,
            headers={
                "X-CSRFToken": csrftoken,
                "referer": f"{lms_url}/login",
            },
            cookies={"csrftoken": csrftoken},
            data=data,
            timeout=30,
        )
        if not report_r.ok:
            return False, f"{course_id}: Failed ({report_r.status_code}) - {report_r.text[:300]}"
        return True, f"{course_id}: Submitted successfully"
    except requests.RequestException as exc:
        return False, f"{course_id}: Error - {exc}"


class GeneratePayload(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
    lms_url: str = Field(min_length=1)
    report: str = Field(min_length=1)
    courses_input: str = Field(description="One course per line. Optional extra info separated by space/comma/semicolon.")


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/generate")
def generate(payload: GeneratePayload):
    # Parse courses lines
    lines = [ln.strip() for ln in payload.courses_input.splitlines() if ln.strip()]
    if not lines:
        raise HTTPException(status_code=400, detail="Please provide at least one course ID.")

    parsed: List[Tuple[str, List[str]]] = []
    for line in lines:
        columns = re.split(',|;|\\s+', line)
        course_id = columns[0]
        additional_info = columns[1:]
        parsed.append((course_id, additional_info))

    try:
        session, csrftoken = login_to_lms(payload.lms_url, payload.email, payload.password)
    except HTTPException:
        # propagate login error
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error while logging in.")

    results = []
    success_count = 0
    for course_id, additional_info in parsed:
        ok, msg = generate_report_for_course(
            session, csrftoken, payload.lms_url, course_id, payload.report, additional_info
        )
        results.append({"course_id": course_id, "success": ok, "message": msg})
        if ok:
            success_count += 1

    return JSONResponse({
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "results": results,
        "note": "Reports are submitted. Download them later from the LMS Instructor Data Download tab.",
    })


@app.post("/api/generate-multipart")
async def generate_multipart(
    email: str = Form(...),
    password: str = Form(...),
    lms_url: str = Form(...),
    report: str = Form(...),
    courses_input: str = Form(""),
    courses_file: UploadFile | None = File(None),
):
    # Parse courses from textarea
    lines = [ln.strip() for ln in courses_input.splitlines() if ln.strip()]

    # Parse courses from uploaded file if present
    if courses_file is not None:
        try:
            content_bytes = await courses_file.read()
            text = content_bytes.decode("utf-8", errors="ignore")
            file_lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            lines.extend(file_lines)
        finally:
            await courses_file.close()

    # De-duplicate while preserving order
    seen = set()
    unique_lines = []
    for ln in lines:
        if ln not in seen:
            seen.add(ln)
            unique_lines.append(ln)

    if not unique_lines:
        raise HTTPException(status_code=400, detail="Please provide at least one course ID.")

    parsed: List[Tuple[str, List[str]]] = []
    for line in unique_lines:
        columns = re.split(',|;|\\s+', line)
        course_id = columns[0]
        additional_info = columns[1:]
        parsed.append((course_id, additional_info))

    try:
        session, csrftoken = login_to_lms(lms_url, email, password)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error while logging in.")

    results = []
    success_count = 0
    for course_id, additional_info in parsed:
        ok, msg = generate_report_for_course(
            session, csrftoken, lms_url, course_id, report, additional_info
        )
        results.append({"course_id": course_id, "success": ok, "message": msg})
        if ok:
            success_count += 1

    return JSONResponse({
        "total": len(results),
        "success": success_count,
        "failed": len(results) - success_count,
        "results": results,
        "note": "Reports are submitted. Download them later from the LMS Instructor Data Download tab.",
    })



