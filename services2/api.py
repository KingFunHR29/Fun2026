import requests


BASE_URL = "https://backendnew.subhartidistance.com"


def headers(token, user_id):
    return {
        "accept": "application/json",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "device": "WEB",
        "userid": str(user_id),
    }


def exam_status(token, user_id, exam_id):
    url = f"{BASE_URL}/student/exam-status/{exam_id}?session_id=1"

    r = requests.get(
        url,
        headers=headers(token, user_id)
    )

    return r.json()


import requests
import json

def schedule_exam(token, user_id, question_paper_id):

    url = (
        f"https://backendnew.subhartidistance.com/"
        f"student/schedule-exam/{question_paper_id}"
        f"?session_id=1"
    )

    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.6",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "device": "WEB",
        "origin": "https://student.subhartidistance.com",
        "referer": "https://student.subhartidistance.com/",
        "userid": str(user_id)
    }

    r = requests.get(url, headers=headers)

    return r.json()
    


def create_exam_status(
    token,
    user_id,
    schedule_exam_id
):
    url = f"{BASE_URL}/student/exam-status"

    payload = {
        "schedule_exam_id": schedule_exam_id,
        "session_id": 1
    }

    r = requests.post(
        url,
        headers=headers(token, user_id),
        json=payload
    )

    return r.json()


def student(token, user_id):
    url = f"{BASE_URL}/student/student"

    r = requests.get(
        url,
        headers=headers(token, user_id)
    )

    return r.json()


def self_data(token, user_id):
    url = f"{BASE_URL}/student/self?all=true"

    r = requests.get(
        url,
        headers=headers(token, user_id)
    )

    return r.json()

def question_paper(
    token,
    user_id,
    question_paper_id
):
    url = (
        f"{BASE_URL}/student/question-paper/"
        f"{question_paper_id}?page=-1"
    )

    r = requests.get(
        url,
        headers=headers(token, user_id)
    )

    return r.json()

def submit_subjective_answer(
    token,
    user_id,
    pdf_url,
    schedule_exam_id,
    question_id
):
    url = (
        "https://backendnew.subhartidistance.com/"
        "student/exam-answer-subjective"
    )

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "device": "WEB",
        "userid": str(user_id)
    }

    payload = {
        "subjective_answer": pdf_url,
        "schedule_exam_id": schedule_exam_id,
        "question_id": question_id
    }

    r = requests.post(
        url,
        headers=headers,
        json=payload
    )

    return r.json()

def finish_exam(
    token,
    user_id,
    schedule_exam_id,
    session_id=1
):
    url = (
        f"https://backendnew.subhartidistance.com/"
        f"student/exam-status/{schedule_exam_id}"
    )

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "device": "WEB",
        "userid": str(user_id)
    }

    payload = {
        "session_id": session_id
    }

    r = requests.put(
        url,
        headers=headers,
        json=payload
    )

    return r.json()