"""
Web demo E-learning NTU + chatbot Rasa.
Chạy từ thư mục gốc project:
  pip install flask
  python web_demo/app.py
Đồng thời cần: rasa run --enable-api (mặc định cổng 5005)
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

import requests
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chatbot_core import process_user_message  # noqa: E402

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)
app.secret_key = __import__("os").environ.get(
    "FLASK_SECRET_KEY", "ntu-elearning-demo-dev-key"
)

STUDENT_DEMO_USER = "64139004"
STUDENT_DEMO_PASS = "123456"
GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"
STUDENT_COURSES = [
    {
        "id": "nec326",
        "title": "An toàn và bảo mật thông tin - NEC326_64.CNTT-1",
        "teacher": "GV. Trần Minh Văn",
        "term": "Năm học 2024-2025 HK2",
        "category": "Support",
        "cover_class": "cover-nec326",
        "links": [
            ("Link đề cương học phần", "https://ctdt.ntu.edu.vn/decuonghp/NEC326_64CNTT-1o"),
            ("Google Meet của giảng viên", "https://meet.google.com/xea-bsyr-itv"),
            ("Link Zalo lớp", "https://zalo.me/g/remlto566"),
        ],
    },
    {
        "id": "se301",
        "title": "Công nghệ phần mềm - SE301_64.CNTT-2",
        "teacher": "GV. Nguyễn Đình Hưng ",
        "term": "Năm học 2024-2025 HK2",
        "category": "Năm học 2024-2025 HK2",
        "cover_class": "cover-se301",
        "links": [
            ("Lịch học và đề cương", "https://elearning.ntu.edu.vn/"),
            ("Nhóm trao đổi lớp", "https://zalo.me/"),
            ("Kho tài liệu môn học", "https://drive.google.com/"),
        ],
    },
    {
        "id": "it201",
        "title": "Kỹ thuật lập trình - IT201_64.CNTT",
        "teacher": "GV. Nguyễn Đình Hưng",
        "term": "Năm học 2023-2024 HK1",
        "category": "Năm học 2023-2024 HK1",
        "cover_class": "cover-it201",
        "links": [
            ("Thông tin môn học", "https://elearning.ntu.edu.vn/"),
            ("Tài liệu học tập", "https://drive.google.com/"),
            ("Diễn đàn thảo luận", "https://elearning.ntu.edu.vn/"),
        ],
    },
]


def _is_logged_in() -> bool:
    return bool(session.get("user_role") == "student")


def _get_course_by_id(course_id: str) -> dict | None:
    for course in STUDENT_COURSES:
        if course["id"] == course_id:
            return course
    return None


@app.route("/")
def index():
    if "sender" not in session:
        session["sender"] = f"web_{uuid.uuid4().hex[:12]}"
    return render_template("demo.html")


@app.route("/courses")
def courses():
    return render_template("courses.html")


@app.route("/my-courses")
def my_courses():
    if not _is_logged_in():
        return redirect(url_for("login", next="/my-courses"))
    return render_template("my_courses.html", courses=STUDENT_COURSES)


@app.route("/my-courses/<course_id>")
def my_course_detail(course_id: str):
    if not _is_logged_in():
        return redirect(url_for("login", next=f"/my-courses/{course_id}"))
    course = _get_course_by_id(course_id)
    if course is None:
        return redirect(url_for("my_courses"))
    return render_template("course_detail.html", course=course)


@app.route("/guides")
def guides():
    if not _is_logged_in():
        return redirect(url_for("login", next="/guides"))
    return render_template("guides.html")

@app.route("/guild")
def guild():
    # Keep a short alias because some users type "/guild".
    return redirect(url_for("guides"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    next_url = request.args.get("next") or "/"
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        next_url = (request.form.get("next") or "").strip() or "/"
        if username == STUDENT_DEMO_USER and password == STUDENT_DEMO_PASS:
            session["user_role"] = "student"
            session["username"] = username
            if "sender" not in session:
                session["sender"] = f"web_{uuid.uuid4().hex[:12]}"
            return redirect(next_url)
        error = "Sai tài khoản hoặc mật khẩu demo."
    return render_template(
        "login.html",
        error=error,
        next_url=next_url,
        demo_user=STUDENT_DEMO_USER,
        demo_pass=STUDENT_DEMO_PASS,
    )


@app.route("/logout")
def logout():
    session.pop("user_role", None)
    session.pop("username", None)
    return redirect(url_for("index"))


@app.route("/student")
def student_dashboard():
    if not _is_logged_in():
        return redirect(url_for("login", next="/student"))
    return render_template("student.html", courses=STUDENT_COURSES)

@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    sender = (data.get("sender") or session.get("sender") or "").strip()
    if not sender:
        sender = f"web_{uuid.uuid4().hex[:12]}"
        session["sender"] = sender

    if not message:
        return jsonify({"ok": False, "error": "empty_message", "text": ""}), 400

    try:
        result = process_user_message(message, sender)
        return jsonify(
            {
                "ok": result.get("error") is None
                or result.get("error") == "empty_message",
                "text": result.get("text") or "",
                "text_en": result.get("text_en"),
                "debug": result.get("debug"),
                "error": result.get("error"),
            }
        )
    except Exception:
        # Always return JSON so frontend doesn't mis-report as "network error".
        return (
            jsonify(
                {
                    "ok": False,
                    "error": "server_error",
                    "text": "Hệ thống demo đang lỗi. Bạn thử tải lại trang và gửi lại giúp mình nhé.",
                }
            ),
            500,
        )


@app.post("/api/translate")
def api_translate():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    source = (data.get("source") or "vi").strip() or "vi"
    target = (data.get("target") or "en").strip() or "en"
    if not text:
        return jsonify({"ok": False, "error": "empty_text"}), 400

    try:
        resp = requests.get(
            GOOGLE_TRANSLATE_URL,
            params={
                "client": "gtx",
                "sl": source,
                "tl": target,
                "dt": "t",
                "q": text,
            },
            timeout=10,
        )
        resp.raise_for_status()
        payload = resp.json()
        chunks = payload[0] if isinstance(payload, list) and payload else []
        translated = "".join(
            str(item[0]) for item in chunks if isinstance(item, list) and item
        ).strip()
        if not translated:
            return jsonify({"ok": False, "error": "translate_failed"}), 502
        return jsonify({"ok": True, "translated_text": translated})
    except Exception:
        return jsonify({"ok": False, "error": "translate_failed"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)