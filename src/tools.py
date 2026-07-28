"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Trợ lý Tư vấn Khóa học Coursera — bộ công cụ cho ReAct Agent.

Chiến lược dữ liệu HYBRID:
- `search_coursera_catalog` gọi Coursera Catalog API THẬT (public, không cần token),
  tự động fallback về danh mục mẫu khi offline / lỗi mạng.
- Các tool hồ sơ học viên, đánh giá lộ trình, đăng ký... dùng dữ liệu mô phỏng
  (Coursera Partner API cần hợp đồng doanh nghiệp nên không dùng ở lab này).
"""

import os
import webbrowser

from dotenv import load_dotenv

from coursera_api import CourseraAPIClient

load_dotenv()

# =============================================================================
# DỮ LIỆU MÔ PHỎNG (MOCK) — hồ sơ học viên & danh mục dự phòng
# =============================================================================
# Học viên hợp lệ duy nhất cho demo (đồng bộ với config/test_cases.json).
LEARNER_DB = {
    "USER_CS_9921": {
        "user_id": "USER_CS_9921",
        "name": "Nguyễn An",
        "goal": "Machine Learning Engineer",
        "current_level": "Beginner",
        "current_skills": ["Python cơ bản", "Toán cao cấp"],
        "hours_per_week": 5,
        "completed_courses": ["Python for Everybody"],
    }
}

# Danh mục dự phòng khi Coursera API không truy cập được (offline demo).
FALLBACK_CATALOG = {
    "python": [
        "Python for Everybody — University of Michigan",
        "Crash Course on Python — Google",
        "Python for Data Science and AI — IBM",
    ],
    "data": [
        "Google Data Analytics Professional Certificate — Google",
        "Data Science Fundamentals — IBM",
        "Data Analysis with Python — University of Michigan",
    ],
    "ai": [
        "AI For Everyone — DeepLearning.AI",
        "Generative AI for Everyone — DeepLearning.AI",
        "Neural Networks and Deep Learning — DeepLearning.AI",
    ],
    "machine learning": [
        "Machine Learning Specialization — DeepLearning.AI",
        "Neural Networks and Deep Learning — DeepLearning.AI",
    ],
}

# Chi tiết một số Specialization (mô phỏng khối lượng học tập).
SPECIALIZATION_DB = {
    "ibm data science specialization": {
        "name": "IBM Data Science Specialization",
        "num_courses": 12,
        "total_hours": 120,
        "level": "Beginner",
    },
    "deep learning specialization": {
        "name": "Deep Learning Specialization",
        "num_courses": 5,
        "total_hours": 100,
        "level": "Intermediate",
    },
}


def search_coursera_catalog(query: str) -> str:
    """
    Tra cứu khóa học trên Coursera Catalog API (dữ liệu THẬT, có fallback mẫu).

    Args:
        query (str): Từ khóa/chủ đề cần tìm (Ví dụ: 'Data Analytics Google', 'Python').

    Returns:
        str: Danh sách khóa học tìm được, hoặc thông báo không tìm thấy.
    """
    query = (query or "").strip()
    if not query:
        return "LỖI: Thiếu từ khóa tìm kiếm."

    # 1) Ưu tiên gọi Coursera Catalog API thật
    try:
        results = CourseraAPIClient.search_courses(query=query, limit=5)
    except Exception as e:  # noqa: BLE001 - tool không được phép crash Agent
        results = []
        print(f"⚠️ search_coursera_catalog: lỗi gọi API thật ({e}), dùng fallback.")

    if results:
        lines = [f"- {c.get('name', 'N/A')} (slug: {c.get('slug', 'n/a')})" for c in results]
        return f"[Coursera API] Kết quả cho '{query}':\n" + "\n".join(lines)

    # 2) Fallback danh mục mẫu theo chủ đề
    q_lower = query.lower()
    for key, courses in FALLBACK_CATALOG.items():
        if key in q_lower:
            body = "\n".join(f"- {c}" for c in courses)
            return f"[Danh mục mẫu] Khóa học Coursera cho '{query}':\n{body}"

    return f"LỖI: Không tìm thấy khóa học Coursera nào khớp với '{query}'."


def get_user_coursera_profile(user_id: str) -> str:
    """
    Lấy hồ sơ học tập của học viên (mục tiêu, trình độ, kỹ năng, quỹ thời gian).

    Args:
        user_id (str): Mã học viên (Ví dụ: 'USER_CS_9921').

    Returns:
        str: Thông tin hồ sơ, hoặc lỗi nếu không tìm thấy học viên.
    """
    user = LEARNER_DB.get((user_id or "").strip().upper())
    if not user:
        return f"LỖI: Không tìm thấy học viên với mã '{user_id}'."
    return (
        f"Hồ sơ {user['user_id']} — {user['name']}: mục tiêu '{user['goal']}', "
        f"trình độ {user['current_level']}, kỹ năng hiện có [{', '.join(user['current_skills'])}], "
        f"quỹ thời gian {user['hours_per_week']}h/tuần, "
        f"đã hoàn thành [{', '.join(user['completed_courses'])}]."
    )


def match_coursera_skill_gap(user_id: str, target_role: str) -> str:
    """
    Phân tích kỹ năng còn thiếu giữa hồ sơ học viên và một vị trí mục tiêu.

    Args:
        user_id (str): Mã học viên (Ví dụ: 'USER_CS_9921').
        target_role (str): Vị trí nghề nghiệp mong muốn (Ví dụ: 'Machine Learning Engineer').

    Returns:
        str: Danh sách kỹ năng còn thiếu để đề xuất khóa học phù hợp.
    """
    user = LEARNER_DB.get((user_id or "").strip().upper())
    if not user:
        return f"LỖI: Không tìm thấy học viên với mã '{user_id}'."

    role = (target_role or "").lower()
    role_skills = {
        "machine learning engineer": ["Machine Learning", "Deep Learning", "MLOps"],
        "data scientist": ["Statistics", "Data Analysis", "Machine Learning"],
        "data analyst": ["SQL", "Data Visualization", "Spreadsheets"],
    }
    required = next((v for k, v in role_skills.items() if k in role), ["Kỹ năng nền tảng"])
    have = {s.lower() for s in user["current_skills"]}
    missing = [s for s in required if s.lower() not in have]
    return (
        f"Với mục tiêu '{target_role}', {user['user_id']} còn thiếu: "
        f"{', '.join(missing) if missing else 'không thiếu kỹ năng cốt lõi'}."
    )


def get_coursera_specialization_details(name: str) -> str:
    """
    Lấy chi tiết một Chương trình Chuyên sâu (Specialization) gồm khối lượng học tập.

    Args:
        name (str): Tên Specialization (Ví dụ: 'IBM Data Science Specialization').

    Returns:
        str: Số khóa học, tổng số giờ, trình độ; hoặc lỗi nếu không tìm thấy.
    """
    spec = SPECIALIZATION_DB.get((name or "").strip().lower())
    if not spec:
        return f"LỖI: Không tìm thấy Specialization '{name}'."
    return (
        f"{spec['name']}: {spec['num_courses']} khóa học, tổng ~{spec['total_hours']} giờ học, "
        f"trình độ {spec['level']}."
    )


def register_coursera_enrollment(user_id: str, course_name: str) -> str:
    """
    Tạo phiếu đăng ký khóa học (mô phỏng) sau khi đã xác thực học viên hợp lệ.

    Args:
        user_id (str): Mã học viên (Ví dụ: 'USER_CS_9921').
        course_name (str): Tên khóa học cần đăng ký.

    Returns:
        str: Xác nhận đăng ký, hoặc lỗi nếu học viên không hợp lệ.
    """
    user = LEARNER_DB.get((user_id or "").strip().upper())
    if not user:
        return f"LỖI: Không thể đăng ký — không tìm thấy học viên '{user_id}'."
    if not (course_name or "").strip():
        return "LỖI: Thiếu tên khóa học cần đăng ký."
    return (
        f"✅ Đã tạo phiếu đăng ký cho {user['user_id']} vào khóa '{course_name}'. "
        f"Mã phiếu: ENR-{abs(hash((user_id, course_name))) % 100000:05d}."
    )


def open_coursera_enrollment_page(course_name: str) -> str:
    """
    Mở trang đăng ký khóa học Coursera trên trình duyệt (Web Automation).

    Mặc định CHỈ trả về đường dẫn để an toàn khi chạy test suite. Đặt biến môi trường
    AUTO_OPEN_BROWSER=1 nếu muốn thực sự bật tab trình duyệt.

    Args:
        course_name (str): Tên khóa học cần mở trang đăng ký.

    Returns:
        str: Đường dẫn trang đăng ký (và mở tab nếu AUTO_OPEN_BROWSER=1).
    """
    if not (course_name or "").strip():
        return "LỖI: Thiếu tên khóa học để mở trang đăng ký."
    url = f"https://www.coursera.org/search?query={course_name.strip().replace(' ', '%20')}"
    if os.getenv("AUTO_OPEN_BROWSER") == "1":
        try:
            webbrowser.open(url)
            return f"🌐 Đã mở tab trình duyệt tới trang đăng ký '{course_name}': {url}"
        except Exception as e:  # noqa: BLE001
            return f"⚠️ Không mở được trình duyệt ({e}). Truy cập thủ công: {url}"
    return f"🔗 Trang đăng ký '{course_name}': {url} (đặt AUTO_OPEN_BROWSER=1 để tự mở tab)."


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "search_coursera_catalog": search_coursera_catalog,
    "get_user_coursera_profile": get_user_coursera_profile,
    "match_coursera_skill_gap": match_coursera_skill_gap,
    "get_coursera_specialization_details": get_coursera_specialization_details,
    "register_coursera_enrollment": register_coursera_enrollment,
    "open_coursera_enrollment_page": open_coursera_enrollment_page,
}
