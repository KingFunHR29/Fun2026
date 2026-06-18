# app.py

import requests
import os
import pandas as pd
import concurrent.futures
import time


from fastapi import FastAPI
from fastapi import Request
from fastapi import UploadFile
from fastapi import File
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from services2.api import *

from sqlalchemy.orm import Session
import json

from database import SessionLocal
from database import engine

from models import Base
from models import StudentExam

from services import login_student
from services import fetch_exam_schedule
from services import parse_exam


# ==================================================
# CREATE TABLES
# ==================================================

Base.metadata.create_all(bind=engine)


# ==================================================
# FASTAPI APP
# ==================================================

app = FastAPI(
    title="Student Exam Dashboard"
)


# ==================================================
# TEMPLATE FOLDER
# ==================================================

templates = Jinja2Templates(
    directory="templates"
)


# ==================================================
# UPLOAD FOLDER
# ==================================================

UPLOAD_FOLDER = "uploads"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ==================================================
# DATABASE SESSION
# ==================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# ==================================================
# HOME PAGE
# ==================================================

@app.get("/debug")
def debug():
    return {
        "cwd": os.getcwd(),
        "files": os.listdir(".")
    }


@app.get(
    "/",
    response_class=HTMLResponse
)
async def home(
    request: Request
):

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )


# ==================================================
# UPLOAD EXCEL
# ==================================================

@app.post("/upload")
async def upload_excel(
    file: UploadFile = File(...)
):

    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )

    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(
            await file.read()
        )

    df = pd.read_excel(
        file_path
    )

    db = SessionLocal()

    try:

        total_rows = len(df)

        processed = 0

        for _, row in df.iterrows():

            username = row.get(
                "username"
            )

            password = row.get(
                "password"
            )

            if pd.isna(username):
                continue

            if pd.isna(password):
                continue

            username = str(
                username
            ).strip()

            password = str(
                password
            ).strip()

            print(
                f"Processing -> {username}"
            )

            login_result, login_api = (
                login_student(
                    username,
                    password
                )
            )

            if (
                login_result.get(
                    "status"
                )
                != "success"
            ):

                print(
                    f"Login Failed -> {username}"
                )

                continue

            student = login_result[
                "data"
            ]

            token = student.get(
                "token"
            )

            student_id = student.get(
                "id"
            )

            exams, exam_api = (
                fetch_exam_schedule(
                    token,
                    student_id
                )
            )

            if not exams:

                record = StudentExam(

                    name=student.get(
                        "name"
                    ),

                    username=username,

                    contact=student.get(
                        "contact"
                    ),

                    bearer_token=token,

                    student_id=str(
                        student_id
                    ),

                    exam_id="",

                    question_id="",

                    subject="NO EXAM DATA",

                    exam_date="",

                    start_time="",

                    end_time="",

                    exam_type="",

                    exam_api=exam_api
                )

                db.add(record)

                db.commit()

                processed += 1

                continue

            # ===================================
            # SAVE ALL EXAMS
            # ===================================

            for exam in exams:

                exam_data = (
                    parse_exam(
                        exam
                    )
                )

                # avoid duplicate

                exists = (
                    db.query(
                        StudentExam
                    )
                    .filter(
                        StudentExam.username
                        == username,

                        StudentExam.exam_id
                        == str(
                            exam_data[
                                "exam_id"
                            ]
                        )
                    )
                    .first()
                )

                if exists:
                    continue

                record = StudentExam(

                    name=student.get(
                        "name"
                    ),

                    username=username,

                    contact=student.get(
                        "contact"
                    ),

                    bearer_token=token,

                    student_id=str(
                        student_id
                    ),

                    exam_id=str(
                        exam_data[
                            "exam_id"
                        ]
                    ),

                    question_id=str(
                        exam_data[
                            "question_id"
                        ]
                    ),

                    subject=exam_data[
                        "subject"
                    ],

                    exam_date=exam_data[
                        "exam_date"
                    ],

                    start_time=exam_data[
                        "start_time"
                    ],

                    end_time=exam_data[
                        "end_time"
                    ],

                    exam_type=exam_data[
                        "exam_type"
                    ],

                    exam_api=exam_api
                )

                db.add(record)

            db.commit()

            processed += 1

            print(
                f"Done {processed}/{total_rows}"
            )

    finally:

        db.close()

    return RedirectResponse(
        "/dashboard",
        status_code=302
    )
from fastapi.responses import FileResponse
from sqlalchemy import func


# ==================================================
# DASHBOARD
# ==================================================

@app.get(
    "/dashboard",
    response_class=HTMLResponse
)
async def dashboard(
    request: Request,
    name: str = "",
    username: str = "",
    exam_date: str = "",
    subject: str = ""
):

    db = SessionLocal()

    try:

        query = db.query(
            StudentExam
        )

        # --------------------------
        # FILTER NAME
        # --------------------------

        if name:

            query = query.filter(
                StudentExam.name.ilike(
                    f"%{name}%"
                )
            )

        # --------------------------
        # FILTER ENROLLMENT
        # --------------------------

        if username:

            query = query.filter(
                StudentExam.username.ilike(
                    f"%{username}%"
                )
            )

        # --------------------------
        # FILTER DATE
        # --------------------------

        if exam_date:

            query = query.filter(
                StudentExam.exam_date
                == exam_date
            )

        # --------------------------
        # FILTER SUBJECT
        # --------------------------

        if subject:

            query = query.filter(
                StudentExam.subject
                == subject
            )

        rows = (
            query.order_by(
                StudentExam.exam_date.desc()
            )
            .all()
        )

        subjects = (

            db.query(
                StudentExam.subject
            )

            .distinct()

            .all()
        )

        total_students = (

            db.query(
                func.count(
                    StudentExam.id
                )
            )

            .scalar()
        )

        total_subjects = len(
            subjects
        )

        return templates.TemplateResponse(

            "dashboard.html",

            {
                "request": request,

                "rows": rows,

                "subjects": subjects,

                "total_students":
                    total_students,

                "total_subjects":
                    total_subjects,

                "selected_subject":
                    subject,

                "selected_name":
                    name,

                "selected_username":
                    username,

                "selected_date":
                    exam_date
            }
        )

    finally:

        db.close()


# ==================================================
# API ALL STUDENTS
# ==================================================

@app.get("/api/students")
def api_students():

    db = SessionLocal()

    try:

        rows = db.query(
            StudentExam
        ).all()

        result = []

        for row in rows:

            result.append({

                "name":
                    row.name,

                "username":
                    row.username,

                "subject":
                    row.subject,

                "exam_date":
                    row.exam_date,

                "student_id":
                    row.student_id,

                "exam_id":
                    row.exam_id,

                "question_id":
                    row.question_id,

                "token":
                    row.bearer_token
            })

        return result

    finally:

        db.close()


# ==================================================
# API SINGLE EXAM
# ==================================================

@app.get(
    "/api/exam/{exam_id}"
)
def exam_details(
    exam_id: str
):

    db = SessionLocal()

    try:

        rows = (

            db.query(
                StudentExam
            )

            .filter(
                StudentExam.exam_id
                == exam_id
            )

            .all()
        )

        result = []

        for row in rows:

            result.append({

                "name":
                    row.name,

                "username":
                    row.username,

                "subject":
                    row.subject,

                "exam_date":
                    row.exam_date,

                "student_id":
                    row.student_id,

                "exam_id":
                    row.exam_id,

                "question_id":
                    row.question_id,

                "token":
                    row.bearer_token
            })

        return result

    finally:

        db.close()


# ==================================================
# EXPORT EXCEL
# ==================================================

@app.get("/export")
def export_excel():

    db = SessionLocal()

    try:

        rows = db.query(
            StudentExam
        ).all()

        export_data = []

        for row in rows:

            export_data.append({

                "Name":
                    row.name,

                "Enrollment":
                    row.username,

                "Contact":
                    row.contact,

                "Subject":
                    row.subject,

                "Exam Date":
                    row.exam_date,

                "Start Time":
                    row.start_time,

                "End Time":
                    row.end_time,

                "Student ID":
                    row.student_id,

                "Exam ID":
                    row.exam_id,

                "Question ID":
                    row.question_id,

                "Bearer Token":
                    row.bearer_token
            })

        df = pd.DataFrame(
            export_data
        )

        export_file = (
            "student_export.xlsx"
        )

        df.to_excel(
            export_file,
            index=False
        )

        return FileResponse(

            export_file,

            media_type=(
                "application/"
                "vnd.openxmlformats-"
                "officedocument."
                "spreadsheetml.sheet"
            ),

            filename=export_file
        )

    finally:

        db.close()


# ==================================================
# DELETE ALL DATA
# ==================================================

@app.get("/delete-all")
def delete_all():

    db = SessionLocal()

    try:

        db.query(
            StudentExam
        ).delete()

        db.commit()

        return {
            "status":
                "success",

            "message":
                "All records deleted"
        }

    finally:

        db.close()


# ==================================================
# STATS API
# ==================================================

@app.get("/stats")
def stats():

    db = SessionLocal()

    try:

        total_records = (

            db.query(
                func.count(
                    StudentExam.id
                )
            )

            .scalar()
        )

        total_subjects = (

            db.query(
                StudentExam.subject
            )

            .distinct()

            .count()
        )

        return {

            "total_records":
                total_records,

            "total_subjects":
                total_subjects
        }

    finally:

        db.close()


@app.get("/exam-helper/{record_id}")
async def exam_helper(
    request: Request,
    record_id: int
):

    db = SessionLocal()

    try:

        student = (
            db.query(StudentExam)
            .filter(
                StudentExam.id == record_id
            )
            .first()
        )

        if not student:

            return {
                "error": "Record not found"
            }
        print(student.question_id)
        questions_text, _ = get_questions(student.bearer_token, student.student_id, student.question_id)
        return templates.TemplateResponse(

            "exam_helper.html",

            {
                "request": request,
                "data":{
                    "student_name":
                        student.name,

                    "enrollment":
                        student.username,

                    "token":
                        student.bearer_token,

                    "user_id":
                        student.student_id,

                    "exam_id":
                        student.exam_id,

                    "question_id":
                        student.question_id,

                    "subject":
                        student.subject,

                    "exam_date":
                        student.exam_date,

                    "start_time":
                        student.start_time,

                    "end_time":
                        student.end_time,

                    "questions":
                        questions_text
                }
            }
        )
    finally:
        db.close()

def get_questions(token, user_id, question_paper_id):
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "device": "WEB",
        "origin": "https://student.subhartidistance.com",
        "referer": "https://student.subhartidistance.com/",
        "user-agent": "Mozilla/5.0",
        "userid": user_id
    }

    urls = [
        f"https://backendnew.subhartidistance.com/student/question-paper/{question_paper_id}?page=-1",
        f"https://backend.subhartidde.com/student/question-paper/{question_paper_id}?page=-1",
        f"https://backend.subhartidistance.com/student/question-paper/{question_paper_id}?page=-1",
        f"https://backendnew.subhartidde.com/student/question-paper/{question_paper_id}?page=-1"
    ]
    last_exception = None
    for idx, question_url in enumerate(urls):
        print(f"[get_questions] Trying URL {idx+1}: {question_url}")
        try:
            r = requests.get(question_url, headers=headers, timeout=15)
            r.raise_for_status()
            data = r.json()
            all_questions = data.get("data", {}).get("data", [])
            objective_questions = [q for q in all_questions if q.get("type") == "OBJECTIVE"]

            questions_text = []
            for idx, q in enumerate(all_questions):
                qid = q.get("id", "---")
                question_text = q.get("question", "---")
                o1 = q.get("option_1", "N/A")
                o2 = q.get("option_2", "N/A")
                o3 = q.get("option_3", "N/A")
                o4 = q.get("option_4", "N/A")
                entry = f"Q{idx + 1} (QID: {qid})\n{question_text}\n  1. {o1}\n  2. {o2}\n  3. {o3}\n  4. {o4}\n---"
                questions_text.append(entry)
            print(f"[get_questions] Successfully fetched questions from URL {idx+1}")
            return "\n\n".join(questions_text), objective_questions
        except Exception as e:
            print(f"[get_questions] Failed on URL {idx+1}: {e}")
            last_exception = e
            continue
    print("[get_questions] All URLs failed.")
    raise last_exception

def submit_answers_stream(token, user_id, exam_id, answers):
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "device": "WEB",
        "origin": "https://student.subhartidistance.com",
        "priority": "u=1, i",
        "referer": "https://student.subhartidistance.com/",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "userid": user_id
    }
    

    answer_urls = [
        "https://backendnew.subhartidistance.com/student/exam-answer-objective",
        "https://backend.subhartidde.com/student/exam-answer-objective",
        "https://backend.subhartidistance.com/student/exam-answer-objective",
        "https://backendnew.subhartidde.com/student/exam-answer-objective"
    ]

    def submit_one(qid_str, opt_str):
        try:
            qid = int(qid_str)
            opt = int(opt_str)
        except Exception:
            print(f"[submit_answers_stream] Skipping invalid QID or Option: {qid_str} => {opt_str}")
            return f"Skipping invalid QID or Option: {qid_str} => {opt_str}\n"
        payload = {
            "objective_answer": opt,
            "schedule_exam_id": exam_id,
            "question_id": qid
        }
        last_error = None
        for idx, answer_url in enumerate(answer_urls):
            print(f"[submit_answers_stream] Trying URL {idx+1} for QID {qid}: {answer_url}")
            try:
                r = requests.post(answer_url, json=payload, headers=headers, timeout=10)
                if r.status_code == 200:
                    json_resp = r.json()
                    status = json_resp.get("status", "error")
                    msg = json_resp.get("message", "")
                    if status == "success":
                        print(f"[submit_answers_stream] QID {qid}: Submitted Option {opt} - SUCCESS on URL {idx+1}")
                        return f"QID {qid}: Submitted Option {opt} - SUCCESS\n"
                    else:
                        print(f"[submit_answers_stream] QID {qid}: ERROR: {msg} on URL {idx+1}")
                        return f"QID {qid}: Submitted Option {opt} - ERROR: {msg}\n"
                else:
                    last_error = f"QID {qid}: HTTP {r.status_code} error during submission to {answer_url}\n"
                    print(f"[submit_answers_stream] {last_error.strip()}")
            except Exception as e:
                last_error = f"QID {qid}: Exception during submission to {answer_url}: {str(e)}\n"
                print(f"[submit_answers_stream] {last_error.strip()}")
        print(f"[submit_answers_stream] QID {qid}: Submission failed for all endpoints.")
        return last_error or f"QID {qid}: Submission failed for all endpoints.\n"

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_qid = {}
        for qid_str, opt_str in answers.items():
            future = executor.submit(submit_one, qid_str, opt_str)
            future_to_qid[future] = qid_str
            time.sleep(0.3)  # Stagger each submission by 0.5 seconds
        for future in concurrent.futures.as_completed(future_to_qid):
            result = future.result()
            yield result
            yield "\n"  # Encourage flush to frontend

def submit_subjective_answers_stream(token, user_id, exam_id, answers):
  
    headers = {
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
        "device": "WEB",
        "origin": "https://student.subhartidistance.com",
        "referer": "https://student.subhartidistance.com/",
        "user-agent": "Mozilla/5.0",
        "userid": str(user_id)
    }

    subjective_urls = [
        "https://backendnew.subhartidistance.com/student/exam-answer-subjective",
        "https://backend.subhartidistance.com/student/exam-answer-subjective",
        "https://backendnew.subhartidde.com/student/exam-answer-subjective",
        "https://backend.subhartidde.com/student/exam-answer-subjective"
    ]

    def submit_one(qid_str, pdf_url=""):
        try:
            qid = int(qid_str)
        except Exception:
            return f"Skipping invalid QID: {qid_str}\n"

        payload = {
            "subjective_answer": "https://static.subhartidistance.com/subjective-answers-prod-jan-2025/696630/8f5jTlp1GKtn5he13b4ULE4ooKxPUlNl3tTt54A3.pdf",
            "schedule_exam_id": exam_id,
            "question_id": qid
        }

        last_error = None

        for idx, url in enumerate(subjective_urls):
            try:
                r = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=10
                )

                if r.status_code == 200:
                    try:
                        data = r.json()
                    except Exception:
                        return f"QID {qid}: SUCCESS (non-json response)\n"

                    if data.get("status") == "success":
                        return f"QID {qid}: PDF submitted successfully\n"

                    return (
                        f"QID {qid}: ERROR - "
                        f"{data.get('message', 'Unknown error')}\n"
                    )

                last_error = (
                    f"QID {qid}: HTTP {r.status_code} "
                    f"on endpoint {idx + 1}\n"
                )

            except Exception as e:
                last_error = (
                    f"QID {qid}: Exception on endpoint "
                    f"{idx + 1}: {e}\n"
                )

        return last_error or f"QID {qid}: Failed\n"

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}

        for qid, pdf_url in answers.items():
            future = executor.submit(submit_one, qid, pdf_url)
            futures[future] = qid
            time.sleep(0.3)

        for future in concurrent.futures.as_completed(futures):
            yield future.result()
            yield "\n"


from fastapi import Request
from fastapi.responses import StreamingResponse
import json

@app.post("/submit")
async def submit(request: Request):

    data = await request.json()

    token = data.get("token")
    user_id = data.get("user_id")
    exam_id = data.get("exam_id")
    answer_json_str = data.get("answer_json")

    print("token =", token)
    print("user_id =", user_id)
    print("exam_id =", exam_id)
    print("answer_json =", answer_json_str)

    answers = json.loads(answer_json_str)
    # Fix nested answer_json payload
    if "answer_json" in answers:
        answers = json.loads(answers["answer_json"])

    print("FINAL ANSWERS:", answers)

    def generate():
        yield "Submitting answers...\n"

        yield from submit_answers_stream(
            token,
            user_id,
            exam_id,
            answers
        )

        yield "All submissions complete.\n"

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )# ==================================================

@app.post("/start-flow")
async def start_flow(data: dict):

    token = data["token"].strip()
    user_id = data["user_id"].strip()
    exam_id = data["exam_id"].strip()
    question_paper_id = data["question_paper_id"].strip()

    logs = []
    print("token:",token)
    print("user_id:",user_id)
    print("exam_id:",exam_id)
    print("question_id:",question_paper_id)
    logs.append("Checking Exam Status")

    status = exam_status(
        token,
        user_id,
        exam_id
    )
    print(status)
    logs.append("Scheduling Exam")

    schedule = schedule_exam(
        token,
        user_id,
        question_paper_id
    )
    print(schedule)
    schedule_exam_id = schedule["data"]["id"]

    logs.append(
        f"Schedule ID: {schedule_exam_id}"
    )

    logs.append(
        "Creating Exam Session"
    )

    exam = create_exam_status(
        token,
        user_id,
        schedule_exam_id
    )

    logs.append(
        "Loading Student"
    )

    student_data = student(
        token,
        user_id
    )

    logs.append(
        "Loading Self Data"
    )

    self_info = self_data(
        token,
        user_id
    )

    logs.append(
        "Loading Question Paper"
    )

    paper = question_paper(
        token,
        user_id,
        question_paper_id
    )

    logs.append(
        "Question Paper Loaded"
    )
    
    questions = []

    try:
        paper_data = paper.get("data", {})
        question_list = paper_data.get("data", [])

        for q in question_list:

            if str(q.get("type", "")).upper() == "SUBJECTIVE":

                questions.append({
                    "id": q.get("id"),
                    "question": q.get("question"),
                    "type": q.get("type")
                })
                print(submit_subjective_answer(token,user_id,"https://static.subhartidistance.com/subjective-answers-prod-jan-2025/696630/uDBlKulmXHM8BM25pL0w2DQ2AvJnTmoHK0X13rZu.pdf",exam_id,q.get("id")))

        logs.append(
            f"Found {len(questions)} subjective questions"
        )

    except Exception as e:

        logs.append(
            f"Question Parse Error: {e}"
        )
    print(finish_exam(token,user_id,exam_id,1))

    logs.append("Completed")

    return JSONResponse({
        "logs": logs,
        "exam_status": status,
        "exam": exam,
        "questions": questions,
        "Exam":"submit successfuly"
    })

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8002,
        reload=True
    )

