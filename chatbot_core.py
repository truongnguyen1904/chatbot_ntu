"""
Logic chung: gọi Rasa + PhoBERT fallback; hỗ trợ nhiều câu hỏi trong một tin nhắn;
ghi log SQLite (db.py) cho báo cáo đồ án.
"""
from __future__ import annotations

import os
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

import requests

from db import ensure_db, log_message
from phobert_utils import ensure_faq_loaded, find_best_intent

RASA_URL = os.environ.get(
    "RASA_URL", "http://localhost:5005/webhooks/rest/webhook"
)
RASA_PARSE_URL = os.environ.get(
    "RASA_PARSE_URL", "http://localhost:5005/model/parse"
)
REQUEST_TIMEOUT = int(os.environ.get("RASA_TIMEOUT", "30"))
MULTI_QUESTION_ENABLED = os.environ.get("CHATBOT_MULTI_QUESTION", "1") not in (
    "0",
    "false",
    "False",
)
# Ngưỡng cosine PhoBERT (câu ngắn / khẩu ngữ thường thấp hơn 0.7)
PHOBERT_INTENT_THRESHOLD = float(os.environ.get("PHOBERT_INTENT_THRESHOLD", "0.62"))
PRELOAD_PHOBERT_ON_START = os.environ.get("CHATBOT_PRELOAD_PHOBERT", "1") not in (
    "0",
    "false",
    "False",
)
_WL_MARK = "\x01WL\x01"

_ABBREV_MAP: list[tuple[str, str]] = [
    (r"\bko\b", "không"),
    (r"\bk\b", "không"),
    (r"\bkh\b", "không"),
    (r"\bkg\b", "không"),
    (r"\bhok\b", "không"),
    (r"\bkho\b", "không"),
    (r"\bk0\b", "không"),
    (r"\bkooo\b", "không"),

    (r"\bdc\b", "được"),
    (r"\bđc\b", "được"),
    (r"\bduoc\b", "được"),

    (r"\br\b", "rồi"),
    (r"\broi\b", "rồi"),
    (r"\brui\b", "rồi"),

    (r"\bvs\b", "với"),
    (r"\bvsao\b", "vì sao"),
    (r"\bvsn\b", "vì sao"),

    (r"\bntn\b", "như thế nào"),

    (r"\bmk\b", "mật khẩu"),
    (r"\bpass\b", "mật khẩu"),
    (r"\bpw\b", "mật khẩu"),
    (r"\bpassword\b", "mật khẩu"),

    (r"\btk\b", "tài khoản"),
    (r"\bid\b", "tài khoản"),
    (r"\bacc\b", "tài khoản"),
    (r"\baccount\b", "tài khoản"),

    (r"\bdk\b", "đăng ký"),
    (r"\bđk\b", "đăng ký"),
    (r"\bdki\b", "đăng ký"),
    (r"\bđki\b", "đăng ký"),
    (r"\breg\b", "đăng ký"),

    # Common Vietnamese abbreviations (with and without spaces)
    (r"\bdk(?=[a-z0-9])", "đăng ký "),
    (r"\bđk(?=[a-z0-9])", "đăng ký "),

    (r"\bkt\b", "kiểm tra"),
    (r"\bkt(?=[a-z0-9])", "kiểm tra "),

    (r"\bhp\b", "học phần"),
    (r"\bhp(?=[a-z0-9])", "học phần "),

    (r"\bmh\b", "môn học"),
    (r"\bmh(?=[a-z0-9])", "môn học "),

    # No-diacritics fused words (common typing without spaces)
    (r"\bdangkyhocphan\b", "đăng ký học phần"),
    (r"\bdangkymonhoc\b", "đăng ký môn học"),
    (r"\bdangky\b", "đăng ký"),
    (r"\bkiemtra\b", "kiểm tra"),
    (r"\bhocphan\b", "học phần"),
    (r"\bmonhoc\b", "môn học"),
    (r"\bel\b", "elearning"),
    

    (r"\blogin\b", "đăng nhập"),
    (r"\bsignin\b", "đăng nhập"),
    (r"\bsign in\b", "đăng nhập"),
    (r"\blog in\b", "đăng nhập"),

    (r"\blogout\b", "đăng xuất"),
    (r"\bsignout\b", "đăng xuất"),

   
    (r"\bsv\b", "sinh viên"),
    (r"\bgv\b", "giảng viên"),
    (r"\bthk\b", "thời khóa biểu"),
    (r"\btkb\b", "thời khóa biểu"),
    (r"\bql\b", "quản lý"),
    (r"\bht\b", "hệ thống"),

   
    (r"\bsubmit\b", "nộp bài"),
    (r"\bsubmission\b", "nộp bài"),
    (r"\bassign\b", "bài tập"),
    (r"\bassignment\b", "bài tập"),
    (r"\bhw\b", "bài tập"),
    (r"\bhomework\b", "bài tập"),

    (r"\bquiz\b", "bài kiểm tra"),
    (r"\btest\b", "bài kiểm tra"),
    (r"\bexam\b", "thi"),

    (r"\bgrade\b", "điểm"),
    (r"\bgrades\b", "điểm"),
    (r"\bscore\b", "điểm"),
    (r"\bgpa\b", "điểm"),

    (r"\bdeadline\b", "hạn nộp"),
    (r"\bdue\b", "hạn nộp"),

    (r"\bcourse\b", "môn học"),
    (r"\bclass\b", "môn học"),

    (r"\bmaterial\b", "tài liệu"),
    (r"\bfile\b", "tài liệu"),
    (r"\bdoc\b", "tài liệu"),

    (r"\bforum\b", "thảo luận"),
    (r"\bdiscussion\b", "thảo luận"),

 
    (r"\bokela\b", "ok"),
    (r"\bokie\b", "ok"),
    (r"\bokkk\b", "ok"),
    (r"\bokkkk\b", "ok"),
    (r"\bokayy\b", "ok"),

    (r"\bthx\b", "cảm ơn"),
    (r"\bthanks\b", "cảm ơn"),
    (r"\bty\b", "cảm ơn"),

    (r"\bplz\b", "please"),
    (r"\bpls\b", "please"),

    (r"\bomg\b", "ôi trời"),
    (r"\bwth\b", "cái gì"),
    (r"\bwtf\b", "cái gì"),

  
    (r"\bwifi\b", "mạng"),
    (r"\bnet\b", "mạng"),
    (r"\binternet\b", "mạng"),
    (r"\b4g\b", "mạng"),

    (r"\blag\b", "chậm"),
    (r"\blagging\b", "chậm"),
    (r"\bfreeze\b", "treo"),
    (r"\bcrash\b", "lỗi"),
    (r"\berror\b", "lỗi"),
    (r"\bbug\b", "lỗi"),

    (r"\bslow\b", "chậm"),
    (r"\bdown\b", "sập"),

   
    (r"\bdnag nhap\b", "đăng nhập"),
    (r"\bdang nhap\b", "đăng nhập"),
    (r"\bdnag ky\b", "đăng ký"),
    (r"\bno bai\b", "nộp bài"),
    (r"\bxem diem\b", "xem điểm"),
    (r"\bthoi khoa bieu\b", "thời khóa biểu"),

   
    (r"\b1\b", "một"),
    (r"\b2\b", "hai"),
    (r"\b3\b", "ba"),
    (r"\b4\b", "bốn"),
    (r"\b5\b", "năm"),

    (r"\bms\b", "mình sẽ"),
    (r"\bmjh\b", "mình"),
    (r"\bbn\b", "bạn"),
    (r"\brl\b", "rồi"),
]

_COMPACT_HINTS: list[tuple[str, str]] = [
    ("xinchao", "chao_hoi"),
    ("chao", "chao_hoi"),
    ("hello", "chao_hoi"),
    ("hi", "chao_hoi"),
    ("alo", "chao_hoi"),
    ("hey", "chao_hoi"),

    ("tambiet", "tam_biet"),
    ("bye", "tam_biet"),
    ("goodbye", "tam_biet"),
    ("exit", "tam_biet"),
    ("thoat", "tam_biet"),

    ("ok", "dong_y"),
    ("oke", "dong_y"),
    ("okela", "dong_y"),
    ("yes", "dong_y"),
    ("yep", "dong_y"),
    ("vay", "dong_y"),
    ("dung", "dong_y"),

    ("no", "tu_choi"),
    ("khong", "tu_choi"),
    ("ko", "tu_choi"),
    ("k", "tu_choi"),
    ("sai", "tu_choi"),
    ("khongphai", "tu_choi"),

    ("botlaai", "hoi_bot"),
    ("banlaai", "hoi_bot"),
    ("ai", "hoi_bot"),
    ("botlaai", "hoi_bot"),

    ("dangnhap", "dang_nhap_khong_duoc"),
    ("login", "dang_nhap_khong_duoc"),
    ("signin", "dang_nhap_khong_duoc"),
    ("loginkhongduoc", "dang_nhap_khong_duoc"),
    ("khongdangnhapduoc", "dang_nhap_khong_duoc"),

    ("saimatkhau", "dang_nhap_sai_mat_khau"),
    ("wrongpassword", "dang_nhap_sai_mat_khau"),
    ("wrongpass", "dang_nhap_sai_mat_khau"),
    ("matkhau", "dang_nhap_sai_mat_khau"),
    ("pass", "dang_nhap_sai_mat_khau"),

    ("hetphien", "dang_nhap_het_phien"),
    ("sessionexpired", "dang_nhap_het_phien"),
    ("timeout", "dang_nhap_het_phien"),
    ("logout", "dang_nhap_het_phien"),

    ("nhieuthietbi", "dang_nhap_nhieu_thiet_bi"),
    ("multidevice", "dang_nhap_nhieu_thiet_bi"),

    ("nopbai", "huong_dan_nop_bai"),
    ("submit", "huong_dan_nop_bai"),
    ("upload", "huong_dan_nop_bai"),
    ("assignment", "huong_dan_nop_bai"),

    ("loinopbai", "loi_nop_bai"),
    ("uploaderror", "loi_nop_bai"),
    ("submiterror", "loi_nop_bai"),

    ("nhieufile", "nop_nhieu_file"),
    ("multiplefile", "nop_nhieu_file"),

    ("filelon", "nop_file_dung_luong_lon"),
    ("largefile", "nop_file_dung_luong_lon"),

    ("draft", "ban_nhap_nop_bai"),
    ("savedraft", "ban_nhap_nop_bai"),

    ("checknop", "kiem_tra_nop_bai"),
    ("checksubmission", "kiem_tra_nop_bai"),
    ("submitted", "kiem_tra_nop_bai"),

    ("nopbosung", "nop_bo_sung_bai"),
    ("resubmit", "nop_bo_sung_bai"),
    ("replace", "nop_bo_sung_bai"),

    ("xemdiem", "xem_diem"),
    ("diem", "xem_diem"),
    ("grade", "xem_diem"),
    ("grades", "xem_diem"),
    ("gpa", "xem_diem"),
    ("score", "xem_diem"),

    ("chuacodiem", "diem_chua_hien"),
    ("missinggrade", "diem_chua_hien"),
    ("noresult", "diem_chua_hien"),

    ("diemchinhthuc", "diem_co_chinh_thuc_khong"),
    ("officialgrade", "diem_co_chinh_thuc_khong"),

    ("tinhdiem", "cach_tinh_diem"),
    ("howgrade", "cach_tinh_diem"),

    ("forum", "thao_luan"),
    ("discussion", "thao_luan"),
    ("thaoluan", "thao_luan"),
    ("reply", "thao_luan"),

    ("tailieu", "tai_tai_lieu"),
    ("download", "tai_tai_lieu"),
    ("material", "tai_tai_lieu"),
    ("file", "tai_tai_lieu"),

    ("loifile", "loi_tai_lieu"),
    ("fileerror", "loi_tai_lieu"),
    ("cannotopen", "loi_tai_lieu"),

    ("lichhoc", "lich_hoc"),
    ("schedule", "lich_hoc"),
    ("timetable", "lich_hoc"),

    ("lichthi", "lich_thi"),
    ("exam", "lich_thi"),
    ("test", "lich_thi"),

    ("deadline", "kiem_tra_deadline"),
    ("due", "kiem_tra_deadline"),
    ("duedate", "kiem_tra_deadline"),

    ("noptre", "chinh_sach_nop_tre"),
    ("late", "chinh_sach_nop_tre"),

    ("nhamgio", "nham_lan_thoi_gian_deadline"),
    ("am", "nham_lan_thoi_gian_deadline"),
    ("pm", "nham_lan_thoi_gian_deadline"),

    ("giangvien", "thong_tin_giang_vien"),
    ("lecturer", "thong_tin_giang_vien"),
    ("teacher", "thong_tin_giang_vien"),

    ("khongthongbao", "khong_nhan_thong_bao"),
    ("missingnotify", "khong_nhan_thong_bao"),

    ("notification", "cai_dat_thong_bao"),
    ("notify", "cai_dat_thong_bao"),

    ("monhoc", "khong_tim_thay_mon_hoc"),
    ("course", "khong_tim_thay_mon_hoc"),

    ("timmon", "tim_kiem_loc_mon_hoc"),
    ("filter", "tim_kiem_loc_mon_hoc"),

    ("timnhanh", "tim_kiem_nhanh_mon_hoc"),
    ("search", "tim_kiem_nhanh_mon_hoc"),

    ("cham", "he_thong_tai_cham"),
    ("lag", "he_thong_tai_cham"),
    ("slow", "he_thong_tai_cham"),

    ("sapp", "website_bi_sap"),
    ("down", "website_bi_sap"),
    ("error500", "website_bi_sap"),

    ("loimang", "loi_duong_truyen"),
    ("network", "loi_duong_truyen"),

    ("whitescreen", "loi_hien_thi"),
    ("blank", "loi_hien_thi"),

    ("quizerror", "loi_quiz_kiem_tra"),
    ("examerror", "loi_quiz_kiem_tra"),

    ("quyche", "quy_che_dao_tao"),
    ("regulation", "quy_che_dao_tao"),

    ("ctdt", "chuong_trinh_dao_tao"),
    ("curriculum", "chuong_trinh_dao_tao"),

    ("doimatkhau", "doi_mat_khau"),
    ("reset", "doi_mat_khau"),
    ("forgot", "doi_mat_khau"),

    ("dangky", "dang_ky_hoc_phan"),
    ("register", "dang_ky_hoc_phan"),

    ("cuocthi", "tim_cuoc_thi"),
    ("contest", "tim_cuoc_thi"),

    ("hotro", "lien_he_ho_tro"),
    ("support", "lien_he_ho_tro"),

    ("gopy", "gop_y_he_thong"),
    ("feedback", "gop_y_he_thong"),

    ("khongthacmac", "khong_co_thac_mac"),
    ("okfine", "khong_co_thac_mac"),

    ("ngoaiphamvi", "ngoai_pham_vi"),
]
# English intent hints (lightweight; no external translate API)
EN_KEYWORDS: list[tuple[str, str]] = [

    # CHÀO HỎI
    ("hello", "chao_hoi"),
    ("hi", "chao_hoi"),
    ("hey", "chao_hoi"),
    ("good morning", "chao_hoi"),
    ("good afternoon", "chao_hoi"),
    ("good evening", "chao_hoi"),

    ("bye", "tam_biet"),
    ("goodbye", "tam_biet"),
    ("see you", "tam_biet"),
    ("see ya", "tam_biet"),
    ("talk to you later", "tam_biet"),

    ("ok", "dong_y"),
    ("okay", "dong_y"),
    ("yes", "dong_y"),
    ("yeah", "dong_y"),
    ("agree", "dong_y"),
    ("sure", "dong_y"),

    ("no", "tu_choi"),
    ("nope", "tu_choi"),
    ("not really", "tu_choi"),

    ("who are you", "hoi_bot"),
    ("what are you", "hoi_bot"),
    ("what can you do", "hoi_bot"),

    # LOGIN
    ("login", "dang_nhap_khong_duoc"),
    ("log in", "dang_nhap_khong_duoc"),
    ("sign in", "dang_nhap_khong_duoc"),
    ("cannot login", "dang_nhap_khong_duoc"),
    ("can't login", "dang_nhap_khong_duoc"),
    ("unable to login", "dang_nhap_khong_duoc"),

    ("wrong password", "dang_nhap_sai_mat_khau"),
    ("incorrect password", "dang_nhap_sai_mat_khau"),

    ("session expired", "dang_nhap_het_phien"),
    ("logged out", "dang_nhap_het_phien"),

    ("multiple device", "dang_nhap_nhieu_thiet_bi"),
    ("login on many devices", "dang_nhap_nhieu_thiet_bi"),

    # SUBMISSION
    ("submit", "huong_dan_nop_bai"),
    ("assignment submit", "huong_dan_nop_bai"),

    ("submission error", "loi_nop_bai"),
    ("upload error", "loi_nop_bai"),
    ("cannot submit", "loi_nop_bai"),

    ("multiple files", "nop_nhieu_file"),
    ("several files", "nop_nhieu_file"),

    ("large file", "nop_file_dung_luong_lon"),
    ("file too big", "nop_file_dung_luong_lon"),
    ("file too large", "nop_file_dung_luong_lon"),

    ("draft", "ban_nhap_nop_bai"),
    ("save draft", "ban_nhap_nop_bai"),

    ("check submission", "kiem_tra_nop_bai"),
    ("submission status", "kiem_tra_nop_bai"),
    ("submitted for grading", "kiem_tra_nop_bai"),

    ("resubmit", "nop_bo_sung_bai"),
    ("submit again", "nop_bo_sung_bai"),
    ("replace submission", "nop_bo_sung_bai"),

    # GRADES
    ("grade", "xem_diem"),
    ("grades", "xem_diem"),
    ("score", "xem_diem"),
    ("mark", "xem_diem"),
    ("gpa", "xem_diem"),

    ("no grade", "diem_chua_hien"),
    ("grades not showing", "diem_chua_hien"),
    ("grade missing", "diem_chua_hien"),

    ("official grade", "diem_co_chinh_thuc_khong"),
    ("final grade", "diem_co_chinh_thuc_khong"),

    ("how grade calculated", "cach_tinh_diem"),
    ("grade breakdown", "cach_tinh_diem"),

    # DISCUSSION
    ("forum", "thao_luan"),
    ("discussion", "thao_luan"),
    ("reply", "thao_luan"),
    ("post", "thao_luan"),

    # MATERIAL
    ("download", "tai_tai_lieu"),
    ("material", "tai_tai_lieu"),
    ("lecture notes", "tai_tai_lieu"),

    ("file error", "loi_tai_lieu"),
    ("cannot open file", "loi_tai_lieu"),

    # SCHEDULE
    ("schedule", "lich_hoc"),
    ("timetable", "lich_hoc"),

    ("exam", "lich_thi"),
    ("test schedule", "lich_thi"),

    ("deadline", "kiem_tra_deadline"),
    ("due date", "kiem_tra_deadline"),

    ("late submission", "chinh_sach_nop_tre"),

    ("am pm", "nham_lan_thoi_gian_deadline"),
    ("midnight", "nham_lan_thoi_gian_deadline"),

    # INFO
    ("lecturer", "thong_tin_giang_vien"),
    ("teacher", "thong_tin_giang_vien"),
    ("professor", "thong_tin_giang_vien"),

    ("no notification", "khong_nhan_thong_bao"),
    ("not receiving notification", "khong_nhan_thong_bao"),

    ("notification settings", "cai_dat_thong_bao"),

    # COURSE
    ("course not found", "khong_tim_thay_mon_hoc"),
    ("missing course", "khong_tim_thay_mon_hoc"),

    ("filter course", "tim_kiem_loc_mon_hoc"),

    ("search course", "tim_kiem_nhanh_mon_hoc"),

    # SYSTEM
    ("slow system", "he_thong_tai_cham"),
    ("system lag", "he_thong_tai_cham"),
    ("lag", "he_thong_tai_cham"),

    ("website down", "website_bi_sap"),
    ("server down", "website_bi_sap"),

    ("network error", "loi_duong_truyen"),

    ("display error", "loi_hien_thi"),
    ("white screen", "loi_hien_thi"),

    ("quiz error", "loi_quiz_kiem_tra"),
    ("exam error", "loi_quiz_kiem_tra"),

    # POLICY
    ("regulation", "quy_che_dao_tao"),
    ("academic rules", "quy_che_dao_tao"),

    ("curriculum", "chuong_trinh_dao_tao"),

    # ACTION
    ("change password", "doi_mat_khau"),
    ("reset password", "doi_mat_khau"),
    ("forgot password", "doi_mat_khau"),

    ("register course", "dang_ky_hoc_phan"),
    ("enroll course", "dang_ky_hoc_phan"),

    ("competition", "tim_cuoc_thi"),
    ("contest", "tim_cuoc_thi"),

    # SUPPORT
    ("help", "lien_he_ho_tro"),
    ("support", "lien_he_ho_tro"),
    ("contact", "lien_he_ho_tro"),

    ("feedback", "gop_y_he_thong"),
    ("complaint", "gop_y_he_thong"),

    # STATUS
    ("no question", "khong_co_thac_mac"),
    ("everything fine", "khong_co_thac_mac"),

    ("out of scope", "ngoai_pham_vi"),
]

# EN_RESPONSES: Dict[str, str] = {
#     # HỆ THỐNG & CHÀO HỎI
#     "chao_hoi": "Hello! I'm the NTU E-learning support chatbot. How can I help you today?",
#     "tam_biet": "Goodbye! Wishing you a productive day of studying!",
    
#     # ĐIỂM
#     "xem_diem": "📊 To view your grades: Log in to E-learning → Open the course → Click **Grades** (or **Điểm**) on the course menu.",
#     "diem_chua_hien": "⏳ Grades appear when the lecturer publishes them. Some activities may not show grades on E-learning. Check the student portal (sinhvien.ntu) for official results.",
#     "diem_co_chinh_thuc_khong": "⚠️ Grades on E-learning are usually component scores, not the official final grade. The official transcript is on the student portal.",
#     "cach_tinh_diem": "📐 Grading formulas vary by course. Check the course syllabus or ask your lecturer for the specific weightings (e.g., attendance 10%, mid-term 30%, final 60%).",
    
#     # NỘP BÀI
#     "huong_dan_nop_bai": "📝 To submit an assignment:\n1️⃣ Open the course\n2️⃣ Open the assignment\n3️⃣ Click **Add submission**\n4️⃣ Upload your file(s) ➕\n5️⃣ Click **Save changes** (and **Submit** if required)",
#     "loi_nop_bai": "⚠️ If submission fails:\n• Check your network connection\n• Check file type & size limits\n• Try another browser\n• Try again later\nIf it keeps failing, contact your lecturer or IT support.",
#     "nop_nhieu_file": "📁 Yes, you can submit multiple files. Click the ➕ icon to add each file, then **Save changes**. Alternatively, zip all files and upload the zip.",
#     "nop_file_dung_luong_lon": "🗄️ For large files: compress to .zip/.rar, split into smaller parts, or reduce image/video quality. If still too large, contact your lecturer.",
#     "ban_nhap_nop_bai": "📑 **Draft** means the assignment is saved but NOT officially submitted. Look for **Submitted for grading** status. If unsure, check with your lecturer.",
#     "kiem_tra_nop_bai": "✅ After submitting, you'll see **Submission status: Submitted for grading** in green. No email confirmation is sent.",
#     "nop_bo_sung_bai": "🔄 Some assignments allow resubmission. The new submission may replace the old one and could be marked as late. Contact your lecturer before resubmitting if you submitted on time.",
    
#     # ĐĂNG NHẬP
#     "dang_nhap_khong_duoc": "🔐 Can't log in? Try:\n• Check account/password (case-sensitive)\n• Clear browser cache\n• Try another browser\n• Wait a few minutes (peak hours may be overloaded)\nIf still stuck, contact IT support.",
#     "dang_nhap_sai_mat_khau": "🔑 Password incorrect? Try:\n• Use the 👁️ icon to check your password\n• Make sure Caps Lock is off\n• No extra spaces\n• Use 'Forgot password' if needed",
#     "dang_nhap_het_phien": "⏰ Your session expired due to inactivity. Just log in again to continue.",
#     "dang_nhap_nhieu_thiet_bi": "📱💻 You can log in on multiple devices, but using them simultaneously may cause session conflicts. For important activities (exams/quizzes), use only one device.",
    
#     # THẢO LUẬN
#     "thao_luan": "💬 Discussion may be required and graded depending on your lecturer. To participate: open the course → find Discussion/Forum in General → create a post or reply.",
    
#     # TÀI LIỆU
#     "tai_tai_lieu": "📂 To download materials: Open the course → Find the file/resource → Click to download. Bulk download is not supported unless the lecturer provides a zip file.",
#     "loi_tai_lieu": "⚠️ If a file won't open: Try downloading again, check your network, use a different app/program, or report the issue to your lecturer.",
    
#     # LỊCH
#     "lich_hoc": "📅 The official class schedule is on the student portal (sinhvien.ntu). E-learning may show some dates, but always check the portal for accuracy.",
#     "lich_thi": "📅 Exam schedules are on the student portal (sinhvien.ntu). E-learning is not always updated for exams. Check the portal and your lecturer's announcements.",
#     "kiem_tra_deadline": "⏰ Deadlines are shown inside each assignment/quiz as **Due date**. After the deadline passes, submission may be closed or marked late (depends on lecturer settings).",
#     "chinh_sach_nop_tre": "📜 Late submission policy varies by lecturer. Some accept late work with penalties, some don't. Check your course syllabus or ask your lecturer.",
#     "nham_lan_thoi_gian_deadline": "⏰ Moodle uses AM/PM format. **12:00 AM** = midnight (start of day), **12:00 PM** = noon. Submit a few hours early to avoid confusion!",
    
#     # THÔNG TIN GIẢNG VIÊN & THÔNG BÁO
#     "thong_tin_giang_vien": "👩‍🏫 Lecturer information (name, email, office hours) is usually in the course syllabus. Check the 'General information' section of your course.",
#     "khong_nhan_thong_bao": "🔔 Not receiving notifications? Lecturers may not always enable email notifications. Check your course page regularly for updates.",
#     "cai_dat_thong_bao": "⚙️ To configure notifications: Click your avatar → **Preferences** → **Notification preferences** → Turn on email/app notifications for the types you want.",
    
#     # MÔN HỌC
#     "khong_tim_thay_mon_hoc": "🔍 Can't find a course? Go to **My courses** → **Course overview** → Select **All**. If still missing, check if you're enrolled on the student portal, then contact the academic office.",
#     "tim_kiem_loc_mon_hoc": "🔎 To filter courses: Go to **My courses** → Use the search bar or filter by **In progress** / **Past** / **All**.",
    
#     # LỖI HỆ THỐNG
#     "he_thong_tai_cham": "🐢 The system may be slow during peak hours. Please wait, reload after a few minutes, or try again later.",
#     "website_bi_sap": "⚠️ The system may be under maintenance or overloaded. Wait a while and try again. If down for a long time, check university announcements.",
#     "loi_duong_truyen": "🌐 This may be a network issue. Check your WiFi/mobile data, reload the page, or try a different network.",
#     "loi_hien_thi": "🖥️ Display issues? Try: hard refresh (Ctrl+F5), clear cache, switch browsers, or enable desktop mode on mobile.",
#     "loi_quiz_kiem_tra": "📝 Quiz disconnected? Use a stable network, don't close the tab, try another browser. Take screenshots and report to your lecturer immediately.",
    
#     # CHÍNH SÁCH & ĐÀO TẠO
#     "quy_che_dao_tao": "📜 Academic regulations are NOT on E-learning. Visit: https://pdtdaihoc.ntu.edu.vn/ for official policies.",
#     "chuong_trinh_dao_tao": "📚 The curriculum is NOT on E-learning. Visit: http://ctdt.ntu.edu.vn/ for your program's requirements.",
#     "doi_mat_khau": "🔑 Password changes must be done on the student portal (sinhvien.ntu), not on E-learning. Change it there, then use the new password for E-learning.",
#     "dang_ky_hoc_phan": "📝 Course registration is done on the student portal (sinhvien.ntu), not on E-learning. After successful registration, courses will appear on E-learning.",
#     "tim_cuoc_thi": "🏆 To find competitions: Go to **Courses** → Select the correct semester/year → Search by competition name. Note: many competitions are annual, so check the year carefully.",
    
#     # HỖ TRỢ & GÓP Ý
#     "lien_he_ho_tro": "📧 For official support: Contact your lecturer (email/class group) or the Academic Affairs Office. Technical issues should be reported to the IT/E-learning department.",
#     "gop_y_he_thong": "💬 Thank you for your feedback! Please send suggestions to the E-learning admin or Academic Affairs Office through official channels for proper handling.",
    
#     # TRẠNG THÁI
#     "khong_co_thac_mac": "😊 Glad to hear that! If you have questions about assignments, grades, deadlines, or E-learning later, just ask.",
#     "dong_y": "👍 Okay! Let me know if you need anything else.",
#     "tu_choi": "😄 I understand. Could you tell me more so I can help you better?",
#     "hoi_bot": "🤖 I'm an AI chatbot designed to help NTU students with E-learning issues (login, assignments, grades, deadlines, etc.).",
#     "ngoai_pham_vi": "👉 Sorry, I only understand questions related to NTU E-learning. Please ask about login, assignments, grades, deadlines, or course materials.",
# }

FAQ_MAP: Dict[str, List[str]] = {
    # HỆ THỐNG & CHÀO HỎI
    "chao_hoi": [
        "xin chào", "chào bạn", "hello", "hi", "bot ơi", "alo bot",
    ],
    "tam_biet": [
        "tạm biệt", "bye", "hẹn gặp lại", "thoát", "kết thúc",
    ],
    "dong_y": [
        "ok", "đúng", "được", "vâng", "có", "đồng ý",
    ],
    "tu_choi": [
        "không", "không phải", "sai rồi", "chưa đúng",
    ],
    "hoi_bot": [
        "bạn là ai", "bạn là bot à", "ai trả lời mình", "chatbot phải không",
    ],

    # LOGIN
    "dang_nhap_khong_duoc": [
        "không đăng nhập được", "login không được", "không vào được elearning",
        "lỗi đăng nhập", "không login được", "đăng nhập thất bại",
    ],

    "dang_nhap_sai_mat_khau": [
        "sai mật khẩu", "password sai", "login sai pass",
        "nhập sai mật khẩu", "không đúng mật khẩu",
    ],

    "dang_nhap_het_phien": [
        "bị đăng xuất", "hết phiên đăng nhập", "session expired",
        "tự logout", "bị văng ra",
    ],

    "he_thong_tai_cham": [
        "hệ thống chậm khi đăng nhập", "login chậm", "đăng nhập chậm",
        "web đăng nhập lâu", "load login lâu",
    ],

    "dang_nhap_nhieu_thiet_bi": [
        "đăng nhập nhiều thiết bị", "login nhiều máy",
        "đăng nhập nhiều nơi", "dùng nhiều thiết bị",
    ],

    # NỘP BÀI
    "huong_dan_nop_bai": [
        "nộp bài", "cách nộp bài", "submit bài", "submit assignment",
        "hướng dẫn nộp bài",
    ],

    "loi_nop_bai": [
        "lỗi nộp bài", "không nộp được bài", "upload lỗi",
        "submit bị lỗi",
    ],

    "nop_nhieu_file": [
        "nộp nhiều file", "upload nhiều file", "multi file",
    ],

    "nop_file_dung_luong_lon": [
        "file lớn", "file quá nặng", "dung lượng file lớn",
        "upload file 100mb",
    ],

    "ban_nhap_nop_bai": [
        "bản nháp", "save draft", "lưu nháp",
        "draft bài",
    ],

    "kiem_tra_nop_bai": [
        "kiểm tra nộp bài", "đã nộp chưa", "submitted for grading",
    ],

    "nop_bo_sung_bai": [
        "nộp bổ sung", "nộp lại bài", "thêm file sau khi nộp",
    ],

    # ĐIỂM
    "xem_diem": [
        "xem điểm", "bảng điểm", "grade", "grades",
    ],

    "diem_chua_hien": [
        "chưa thấy điểm", "chưa có điểm", "điểm chưa hiện",
    ],

    "diem_co_chinh_thuc_khong": [
        "điểm có chính thức không", "điểm elearning đúng không",
    ],

    "cach_tinh_diem": [
        "cách tính điểm", "trọng số điểm", "tính điểm môn",
    ],

    # THẢO LUẬN
    "thao_luan": [
        "thảo luận", "forum", "discussion", "cách tham gia thảo luận",
    ],

    # TÀI LIỆU
    "tai_tai_lieu": [
        "tải tài liệu", "download file", "tải slide",
    ],

    "loi_tai_lieu": [
        "file không mở được", "lỗi tài liệu", "pdf lỗi",
    ],

    # LỊCH
    "lich_hoc": [
        "lịch học", "thời khóa biểu", "timetable",
    ],

    "lich_thi": [
        "lịch thi", "exam", "ngày thi",
    ],

    "kiem_tra_deadline": [
        "deadline", "hạn nộp", "due date",
    ],

    "chinh_sach_nop_tre": [
        "nộp trễ", "late submission", "quá hạn nộp",
    ],

    "nham_lan_thoi_gian_deadline": [
        "nhầm giờ deadline", "12 am 12 pm", "sai giờ nộp",
    ],

    # GIẢNG VIÊN
    "thong_tin_giang_vien": [
        "giảng viên", "email giảng viên", "thông tin giảng viên",
    ],

    "khong_nhan_thong_bao": [
        "không nhận thông báo", "không thấy thông báo",
    ],

    "cai_dat_thong_bao": [
        "bật thông báo", "notification", "cài email thông báo",
    ],

    # MÔN HỌC
    "khong_tim_thay_mon_hoc": [
        "không thấy môn học", "môn học bị mất", "không có môn",
    ],

    "tim_kiem_loc_mon_hoc": [
        "lọc môn học", "tìm môn", "course filter",
    ],

    "tim_kiem_nhanh_mon_hoc": [
        "tìm nhanh môn học", "search môn", "tìm khóa học",
    ],

    # HỆ THỐNG
    "he_thong_tai_cham": [
        "hệ thống chậm", "web lag", "load lâu", "login chậm",
    ],

    "website_bi_sap": [
        "sập web", "không vào được", "500 error",
    ],

    "loi_duong_truyen": [
        "mạng yếu", "lỗi mạng", "connection error",
    ],

    "loi_hien_thi": [
        "lỗi hiển thị", "màn hình trắng", "giao diện lỗi",
    ],

    "loi_quiz_kiem_tra": [
        "lỗi quiz", "bị văng khi thi", "mất bài kiểm tra",
    ],

    # KHÁC
    "quy_che_dao_tao": [
        "quy chế đào tạo", "nội quy", "regulation",
    ],

    "chuong_trinh_dao_tao": [
        "chương trình đào tạo", "ctdt", "curriculum",
    ],

    "doi_mat_khau": [
        "đổi mật khẩu", "reset password", "forgot password",
    ],

    "dang_ky_hoc_phan": [
        "đăng ký học phần", "đăng ký môn", "register course",
    ],

    "tim_cuoc_thi": [
        "cuộc thi", "contest", "competition",
    ],

    "lien_he_ho_tro": [
        "liên hệ hỗ trợ", "help desk", "báo lỗi",
    ],

    "gop_y_he_thong": [
        "góp ý", "feedback", "đề xuất cải tiến",
    ],

    "khong_co_thac_mac": [
        "không có thắc mắc", "ok rồi", "xong rồi",
    ],

    "ngoai_pham_vi": [
        # fallback
    ],
}
def ask_rasa(message: str, sender: str) -> List[Dict[str, Any]]:
    try:
        res = requests.post(
            RASA_URL,
            json={"sender": sender, "message": message},
            timeout=REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()
        return data if isinstance(data, list) else []
    except requests.RequestException:
        return []


def ask_rasa_intent(message: str) -> Dict[str, Any]:
    try:
        res = requests.post(
            RASA_PARSE_URL,
            json={"text": message},
            timeout=REQUEST_TIMEOUT,
        )
        res.raise_for_status()
        data = res.json()
        return data if isinstance(data, dict) else {}
    except requests.RequestException:
        return {}


def _payload_to_text(payload: List[Dict[str, Any]]) -> str:
    texts = [item.get("text") for item in payload if item.get("text")]
    if not texts:
        return ""
    return "\n".join(texts)


def _normalize_bot_text(text: str) -> str:
    """
    Reduce excessive blank lines in chatbot responses.
    Keep at most one empty line between paragraphs.
    """
    t = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    # Trim trailing whitespace per line
    t = re.sub(r"[ \t]+$", "", t, flags=re.M)
    # Collapse 3+ newlines -> 2 newlines (one blank line max)
    t = re.sub(r"\n{3,}", "\n\n", t)
    # Collapse spaced blank lines too
    t = re.sub(r"\n\s+\n", "\n\n", t)
    return t.strip()


def _strip_accents(text: str) -> str:
    norm = unicodedata.normalize("NFD", text or "")
    return "".join(ch for ch in norm if unicodedata.category(ch) != "Mn")


def _normalize_user_text(text: str) -> str:
    t = (text or "").strip().lower()
    if not t:
        return ""
    t = re.sub(r"[_\-./]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    for pattern, repl in _ABBREV_MAP:
        t = re.sub(pattern, repl, t, flags=re.IGNORECASE)
    # compact = re.sub(r"[^a-z0-9]", "", _strip_accents(t).lower())
    # hints: list[str] = []
    # for key, phrase in _COMPACT_HINTS:
    #     if key in compact:
    #         hints.append(phrase)
    # if hints:
    #     t = f"{t} {' '.join(hints)}"
    return re.sub(r"\s+", " ", t).strip()


def split_multipart_question(text: str) -> List[str]:
    """
    Tách tin nhắn thành nhiều ý (dấu hỏi, ;, xuống dòng, **với**, **và**, với lại, còn…).
    Bảo vệ cụm "với lại" để không tách nhầm.
    """
    t = (text or "").strip()
    if len(t) < 6:
        return [t]

    def unmark(s: str) -> str:
        return s.replace(_WL_MARK, " với lại ")

    raw = (
        t.replace(" với lại ", _WL_MARK)
        .replace("Với lại ", _WL_MARK)
        .replace("với lại ", _WL_MARK)
    )

    parts: List[str] = []
    chunks = re.split(r"\s*\?\s*", raw)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        for sub in chunk.split(";"):
            sub = sub.strip()
            if len(sub) >= 4:
                parts.append(unmark(sub))

    if len(parts) <= 1:
        for sep in (
            "\n",
            " với ",
            " voi ",
            " và ",
            " ; ",
            " va ",
            " and ",
            " also ",
            " đồng thời ",
            " ngoài ra ",
            " / ",
            " | ",
            "\t",
        ):
            if sep in raw:
                parts = [
                    unmark(p.strip())
                    for p in raw.split(sep)
                    if len(p.strip()) >= 4
                ]
                break

    if not parts:
        return [t]
    if len(parts) <= 1:
        return [t]
    return parts


def _resolve_with_phobert(user_input: str) -> Tuple[Optional[str], float]:
    ensure_faq_loaded(FAQ_MAP)
    return find_best_intent(user_input)


def _looks_english(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    letters = sum(1 for c in t if c.isalpha())
    ascii_letters = sum(1 for c in t if ("A" <= c <= "Z") or ("a" <= c <= "z"))
    if letters == 0:
        return False
    # mostly ASCII letters + contains some common English keywords
    ratio = ascii_letters / max(letters, 1)
    if ratio < 0.75:
        return False
    low = t.lower()
    return any(k in low for k, _ in EN_KEYWORDS)


def _guess_intent_en(text: str) -> Optional[str]:
    low = (text or "").lower()
    for k, intent in EN_KEYWORDS:
        if k in low:
            return intent
    return None


import re
from typing import Optional

def _hard_intent_guard(user_input: str) -> Optional[str]:
    t = (user_input or "").lower().strip()
    if not t:
        return None

    t_noacc = _strip_accents(t)
    t_join = re.sub(r"[\s_\-./]+", "", t_noacc)

    # =========================
    # 1. DICTIONARY KEYWORDS (CLEAN & SAFE)
    # =========================

    INTENT_KEYWORDS = {
        "lich_thi": {
            "lichthi", "ngaythi", "examschedule", "lichthian"
        },
        "lich_hoc": {
            "lichhoc", "tkb", "thoikhoabieu", "schedule"
        },
        "kiem_tra_deadline": {
            "ktdeadline", "hanop", "hannop", "hanchot", "deadline"
        },

        # ===== ĐIỂM =====
        "cach_tinh_diem": {
            "cachtinhdiem", "tinhdiem", "trongso", "weightdiem"
        },
        "xem_diem": {
            "xemdiem", "ketquahoctap", "bangdiem", "diemso", "grades"
        },

        # ===== NỘP BÀI =====
        "huong_dan_nop_bai": {
            "nopbai", "submit", "guibai", "upload"
        },
        "loi_nop_bai": {
            "nopbai", "submit", "upload", "loi", "khongduoc"
        },
        "tai_tai_lieu": {
            "tailieu", "slide", "giaotrinh", "download"
        },

        # ===== LOGIN =====
        "doi_mat_khau": {
            "quenmatkhau", "doimatkhau", "resetpass", "forgotpassword"
        },
        "dang_nhap_khong_duoc": {
            "dangnhap", "login", "loginkhongduoc", "khongdangnhapduoc", "loi"
        },

        # ===== KHÁC =====
        "dang_ky_hoc_phan": {
            "dkhp", "dangkyhocphan", "dkmonhoc", "register"
        },
        "thong_tin_giang_vien": {
            "giangvien", "emailgv", "sdtgv", "ttgv"
        },
    }

    # =========================
    # 2. PRIORITY ORDER (QUAN TRỌNG)
    # =========================
    PRIORITY = [
        "cach_tinh_diem",      # cụ thể hơn
        "xem_diem",

        "dang_nhap_khong_duoc",
        "doi_mat_khau",

        "huong_dan_nop_bai",
        "loi_nop_bai",

        "lich_thi",
        "lich_hoc",
        "kiem_tra_deadline",

        "dang_ky_hoc_phan",
        "thong_tin_giang_vien",
        "tai_tai_lieu",
    ]

    # =========================
    # 3. MATCH SCORE (TRÁNH FALSE POSITIVE)
    # =========================
    def score(intent_keywords: set) -> int:
        return sum(1 for kw in intent_keywords if kw in t_join or kw in t_noacc)

    best_intent = None
    best_score = 0

    for intent in PRIORITY:
        keywords = INTENT_KEYWORDS.get(intent, set())
        s = score(keywords)

        if s > best_score:
            best_score = s
            best_intent = intent

    # =========================
    # 4. THRESHOLD CHỐNG NHẦM
    # =========================
    if best_score == 0:
        return None

    return best_intent

def _process_single_turn(user_input: str, sender: str) -> Dict[str, Any]:
    """Một lượt: parse intent → Rasa hoặc PhoBERT fallback → text."""
    debug: Dict[str, Any] = {}
    user_input = (user_input or "").strip()
    if not user_input:
        return {
            "text": "",
            "rasa_messages": [],
            "error": "empty_message",
            "debug": debug,
        }

    normalized_input = _normalize_user_text(user_input)
    if normalized_input and normalized_input != user_input:
        debug["normalized_input"] = normalized_input
    effective_input = normalized_input or user_input

    forced_intent = _hard_intent_guard(f"{user_input} {effective_input}")
    if forced_intent:
        payload = ask_rasa(f"/{forced_intent}", sender)
        text = _normalize_bot_text(_payload_to_text(payload)) or "Xin lỗi, tôi chưa hiểu."
        debug["intent"] = forced_intent
        debug["confidence"] = 1.0
        debug["via"] = "hard_guard"
        return {
            "text": text,
            "rasa_messages": payload,
            "error": None,
            "debug": debug,
        }

    # If user asks in English, map keywords -> intent and call Rasa directly.
    if _looks_english(effective_input):
        en_intent = _guess_intent_en(effective_input)
        if en_intent:
            payload = ask_rasa(f"/{en_intent}", sender)
            text = _normalize_bot_text(_payload_to_text(payload)) or "Sorry, I couldn't understand."
            debug["intent"] = en_intent
            debug["confidence"] = 1.0
            debug["via"] = "en_keyword"
            return {
                "text": text,
                "rasa_messages": payload,
                "error": None,
                "debug": debug,
            }

    rasa_result = ask_rasa_intent(effective_input)
    intent_info = (rasa_result or {}).get("intent") or {}
    intent: Optional[str] = intent_info.get("name")
    confidence = float(intent_info.get("confidence") or 0.0)
    debug["intent"] = intent
    debug["confidence"] = confidence

    if intent is None:
        return {
            "text": "Không kết nối được máy chủ Rasa (kiểm tra `rasa run`).",
            "rasa_messages": [],
            "error": "parse_failed",
            "debug": debug,
        }

    low_conf = confidence < 0.5
    is_nlu_fallback = intent == "nlu_fallback"

    if low_conf or is_nlu_fallback:
        try:
            # PhoBERT fallback: try original + accent-stripped variants.
            # This helps when user types "không dấu" or minor typos.
            candidates: List[str] = [effective_input]
            stripped = _strip_accents(effective_input or "")
            if stripped and stripped != effective_input:
                candidates.append(stripped)

            # If it looks like "no diacritics", lower threshold slightly.
            no_diacritics = (
                _strip_accents(effective_input or "").strip().lower()
                == (effective_input or "").strip().lower()
            )
            threshold = max(0.45, PHOBERT_INTENT_THRESHOLD - (0.08 if no_diacritics else 0.0))

            best_intent: Optional[str] = None
            best_score = 0.0
            for c in candidates:
                it, sc = _resolve_with_phobert(c)
                if it and sc > best_score:
                    best_intent, best_score = it, sc
        except Exception as e:
            print("PhoBERT ERROR:", e)
            best_intent, best_score, threshold = None, 0.0, PHOBERT_INTENT_THRESHOLD
        debug["phobert_intent"] = best_intent
        debug["phobert_score"] = best_score
        debug["phobert_threshold_used"] = threshold

        if best_intent and best_score >= threshold:
            payload = ask_rasa(f"/{best_intent}", sender)
            text = _normalize_bot_text(_payload_to_text(payload))
            debug["via"] = "phobert"
            debug["phobert_threshold"] = threshold
            if not text:
                text = "Xin lỗi, tôi chưa hiểu."
            return {
                "text": text,
                "rasa_messages": payload,
                "error": None,
                "debug": debug,
            }

        if is_nlu_fallback and not low_conf:
            payload = ask_rasa(effective_input, sender)
            text = _normalize_bot_text(_payload_to_text(payload))
            debug["via"] = "rasa_fallback"
            if not text:
                text = "Xin lỗi, tôi chưa hiểu."
            return {
                "text": text,
                "rasa_messages": payload,
                "error": None,
                "debug": debug,
            }

        debug["via"] = "clarify"
        return {
            "text": "👉 Xin lỗi, mình chưa hiểu rõ câu hỏi của bạn hoặc câu hỏi này nằm ngoài vùng hiểu biết của mình. Bạn vui lòng nói cụ thể vấn đề liên quan E-learning NTU. Nếu cần, bạn có thể liên hệ bộ phận hỗ trợ để được giải quyết.",
            "rasa_messages": [],
            "error": None,
            "debug": debug,
        }

    # Use the already predicted intent to avoid re-classification drift.
    payload = ask_rasa(f"/{intent}", sender)
    text = _normalize_bot_text(_payload_to_text(payload))
    debug["via"] = "rasa"
    if not text:
        text = "Xin lỗi, tôi chưa hiểu."
    return {
        "text": text,
        "rasa_messages": payload,
        "error": None,
        "debug": debug,
    }


def _warmup_runtime() -> None:
    if not PRELOAD_PHOBERT_ON_START:
        return
    try:
        ensure_faq_loaded(FAQ_MAP)
        print("PhoBERT preloaded at startup.")
    except Exception as e:
        print("PhoBERT preload skipped:", e)


_warmup_runtime()


def process_user_message(user_input: str, sender: str) -> Dict[str, Any]:
    """
    Trả về:
      text: nội dung hiển thị cho người dùng
      rasa_messages: gộp từ các lượt (multi) hoặc một lượt
      error: lỗi nếu có
      debug: intent, multi_parts, v.v.
    """
    ensure_db()
    user_input = (user_input or "").strip()
    base_debug: Dict[str, Any] = {}

    if not user_input:
        return {
            "text": "",
            "rasa_messages": [],
            "error": "empty_message",
            "debug": base_debug,
        }

    parts = split_multipart_question(user_input)
    if not MULTI_QUESTION_ENABLED or len(parts) <= 1:
        out = _process_single_turn(user_input, sender)
        intent = (out.get("debug") or {}).get("intent")
        conf = (out.get("debug") or {}).get("confidence")
        log_message(
            sender,
            user_input,
            intent,
            float(conf) if conf is not None else None,
            out.get("text") or "",
            False,
            None,
            out.get("debug"),
        )
        return out

    blocks: List[str] = []
    all_payload: List[Dict[str, Any]] = []
    sub_intents: List[Dict[str, Any]] = []
    primary_intent: Optional[str] = None
    primary_conf: Optional[float] = None

    header = "Bạn hỏi nhiều ý trong một tin nhắn nên mình sẽ trả lời lần lượt các vấn đề nhé:\n"

    for idx, part in enumerate(parts, start=1):
        one = _process_single_turn(part, sender)
        d = one.get("debug") or {}
        intent_name = d.get("intent")
        conf = d.get("confidence")
        if primary_intent is None and intent_name:
            primary_intent = intent_name
            primary_conf = float(conf) if conf is not None else None

        sub_intents.append(
            {
                "index": idx,
                "snippet": part[:120],
                "intent": intent_name,
                "confidence": conf,
                "via": d.get("via"),
            }
        )

        preview = part if len(part) <= 100 else part[:97] + "..."
        label = (
            f"━━━━━━━━━━━━━━\n"
            f"📌 Câu {idx}: {preview}\n"
            f"💬 {one.get('text') or ''}"
        )
        blocks.append(label)
        rp = one.get("rasa_messages") or []
        if isinstance(rp, list):
            all_payload.extend(rp)

    combined = header + "\n".join(blocks)
    base_debug["multi_question"] = True
    base_debug["parts"] = len(parts)
    base_debug["sub_intents"] = sub_intents

    log_message(
        sender,
        user_input,
        primary_intent,
        primary_conf,
        combined,
        True,
        sub_intents,
        base_debug,
    )

    return {
        "text": _normalize_bot_text(combined),
        "rasa_messages": all_payload,
        "error": None,
        "debug": base_debug,
    }
