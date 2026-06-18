# models.py

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from database import Base


class StudentExam(Base):
    __tablename__ = "student_exams"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(String(255))

    username = Column(
        String(100),
        index=True
    )

    contact = Column(String(50))

    bearer_token = Column(String(3000))

    student_id = Column(String(100))

    exam_id = Column(String(100))

    question_id = Column(String(255))

    subject = Column(String(255))

    exam_date = Column(String(50))

    start_time = Column(String(50))

    end_time = Column(String(50))

    exam_type = Column(String(100))

    exam_api = Column(String(100))