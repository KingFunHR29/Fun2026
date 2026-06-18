# services.py

import requests

# ==================================================
# LOGIN APIs
# ==================================================

LOGIN_URL_MAIN = "https://backend.subhartidistance.com/student/login"
LOGIN_URL_BACKUP = "https://backendnew.subhartidistance.com/student/login"

# ==================================================
# EXAM APIs
# ==================================================

EXAM_URL_MAIN = (
    "https://backend.subhartidistance.com/student/schedule-exam-subjects"
)

EXAM_URL_BACKUP = (
    "https://backendnew.subhartidistance.com/student/schedule-exam-subjects"
)

# ==================================================
# COMMON HEADERS
# ==================================================

BASE_HEADERS = {
    "accept": "application/json",
    "content-type": "application/json",
    "device": "WEB",
    "origin": "https://student.subhartidistance.com",
    "referer": "https://student.subhartidistance.com/",
    "user-agent": (
        "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/143.0.0.0 Mobile Safari/537.36"
    ),
}


# ==================================================
# LOGIN STUDENT
# ==================================================

def login_student(username, password):
    """
    Login student from main api first
    then backup api.

    Returns:
    (
        response_json,
        api_used
    )
    """

    payload = {
        "username": username,
        "password": str(password).split(".")[0],
    }
    print(payload)
    # -----------------------------
    # MAIN API
    # -----------------------------
    try:

        response = requests.post(
            LOGIN_URL_MAIN,
            json=payload,
            headers=BASE_HEADERS,
            timeout=20,
        )

        data = (
            response.json()
            if response.content
            else {}
        )

        if data.get("status") == "success":
            return data, "MAIN_API"

    except Exception:
        pass

    # -----------------------------
    # BACKUP API
    # -----------------------------
    try:

        response = requests.post(
            LOGIN_URL_BACKUP,
            json=payload,
            headers=BASE_HEADERS,
            timeout=20,
        )

        data = (
            response.json()
            if response.content
            else {}
        )

        if data.get("status") == "success":
            return data, "BACKUP_API"

        return data, "FAILED"

    except Exception as e:

        return {
            "status": "error",
            "message": str(e),
        }, "FAILED"


# ==================================================
# EXAM SCHEDULE
# ==================================================

def fetch_exam_schedule(
    token,
    student_id,
):
    """
    Fetch exam schedule

    Returns:
    (
        exams,
        api_used
    )
    """

    headers = BASE_HEADERS.copy()

    headers["authorization"] = f"Bearer {token}"

    headers["userid"] = str(student_id)

    # -----------------------------
    # MAIN API
    # -----------------------------
    try:

        response = requests.get(
            EXAM_URL_MAIN,
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        exams = (
            data
            .get("data", {})
            .get("data", [])
        )

        if exams:
            return exams, "MAIN_API"

    except Exception:
        pass

    # -----------------------------
    # BACKUP API
    # -----------------------------
    try:

        response = requests.get(
            EXAM_URL_BACKUP,
            headers=headers,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        exams = (
            data
            .get("data", {})
            .get("data", [])
        )

        if exams:
            return exams, "BACKUP_API"

    except Exception:
        pass

    return [], "NO_EXAM"


# ==================================================
# HELPER FUNCTION
# ==================================================

def parse_exam(exam):
    """
    Convert api response
    into readable format
    """

    subject = exam.get(
        "subject",
        {}
    )

    start_time = (
        f"{exam.get('start_hour')}:" +
        f"{exam.get('start_minute')} "
        f"{exam.get('start_meridiem')}"
    )

    end_time = (
        f"{exam.get('end_hour')}:" +
        f"{exam.get('end_minute')} "
        f"{exam.get('end_meridiem')}"
    )

    return {
        "exam_id": exam.get("id"),
        "question_id": exam.get("unique_id"),
        "subject": subject.get("name"),
        "exam_date": exam.get("date"),
        "start_time": start_time,
        "end_time": end_time,
        "exam_type": exam.get(
            "subject_exam_type"
        ),
    }