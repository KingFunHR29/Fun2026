import requests

# =====================================================
# Base URLs (Try backendnew first, then backend)
# =====================================================

BASE_URLS = [
    "https://backendnew.subhartidistance.com",
    "https://backend.subhartidistance.com",
]

TIMEOUT = 20


# =====================================================
# Common Headers
# =====================================================

def headers(token, user_id):
    return {
        "accept": "application/json",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "device": "WEB",
        "userid": str(user_id),
    }


# =====================================================
# Request Helper
# =====================================================

def request_api(method, endpoint, **kwargs):
    """
    Tries backendnew first.
    If it fails, automatically tries backend.
    """

    last_error = None

    for base_url in BASE_URLS:
        url = f"{base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                timeout=TIMEOUT,
                **kwargs
            )

            if response.ok:
                return response

            # Retry on these status codes
            if response.status_code in [404, 500, 502, 503]:
                print(
                    f"[INFO] {response.status_code} from {base_url}. Trying next server..."
                )
                continue

            return response

        except requests.exceptions.RequestException as e:
            print(f"[ERROR] {base_url}: {e}")
            last_error = e

    raise Exception(f"All servers failed. Last error: {last_error}")


# =====================================================
# API Functions
# =====================================================

def exam_status(token, user_id, exam_id):
    urls = [
        "https://backendnew.subhartidistance.com",
        "https://backend.subhartidistance.com"
    ]

    for base_url in urls:
        try:
            response = requests.get(
                f"{base_url}/student/exam-status/{exam_id}?session_id=1",
                headers=headers(token, user_id),
                timeout=20
            )

            # Success
            if response.status_code == 200:
                return response.json()

            # If not found on this server, try the next one
            if response.status_code == 404:
                continue

        except requests.exceptions.RequestException:
            continue

    # If both servers return 404 or are unreachable
    return {
        "status": "pending"
    }


def schedule_exam(token, user_id, question_paper_id):
    custom_headers = headers(token, user_id)
    custom_headers.update({
        "accept-language": "en-US,en;q=0.6",
        "origin": "https://student.subhartidistance.com",
        "referer": "https://student.subhartidistance.com/",
    })

    response = request_api(
        "GET",
        f"/student/schedule-exam/{question_paper_id}?session_id=1",
        headers=custom_headers,
    )

    return response.json()


def create_exam_status(token, user_id, schedule_exam_id):
    payload = {
        "schedule_exam_id": schedule_exam_id,
        "session_id": 1,
    }

    response = request_api(
        "POST",
        "/student/exam-status",
        headers=headers(token, user_id),
        json=payload,
    )

    return response.json()


def student(token, user_id):
    response = request_api(
        "GET",
        "/student/student",
        headers=headers(token, user_id),
    )

    return response.json()


def self_data(token, user_id):
    response = request_api(
        "GET",
        "/student/self?all=true",
        headers=headers(token, user_id),
    )

    return response.json()


def question_paper(token, user_id, question_paper_id):
    response = request_api(
        "GET",
        f"/student/question-paper/{question_paper_id}?page=-1",
        headers=headers(token, user_id),
    )

    return response.json()


def submit_subjective_answer(
    token,
    user_id,
    pdf_url,
    schedule_exam_id,
    question_id,
):
    payload = {
        "subjective_answer": pdf_url,
        "schedule_exam_id": schedule_exam_id,
        "question_id": question_id,
    }

    response = request_api(
        "POST",
        "/student/exam-answer-subjective",
        headers=headers(token, user_id),
        json=payload,
    )

    return response.json()


def finish_exam(
    token,
    user_id,
    schedule_exam_id,
    session_id=1,
):
    payload = {
        "session_id": session_id,
    }

    response = request_api(
        "PUT",
        f"/student/exam-status/{schedule_exam_id}",
        headers=headers(token, user_id),
        json=payload,
    )

    return response.json()