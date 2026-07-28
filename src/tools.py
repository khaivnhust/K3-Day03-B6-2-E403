"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Trợ lý Tư vấn Khóa học Coursera — ẩn danh (KHÔNG cần user_id).
Bất kỳ ai hỏi cũng được; Agent tự tìm khóa học Coursera phù hợp.

Chiến lược dữ liệu HYBRID:
- `search_coursera_catalog` / `recommend_courses` gọi Coursera Catalog API THẬT
  (public, không cần token), tự động bổ sung danh mục mẫu khi kết quả thưa/offline.
- Các tool còn lại dùng dữ liệu mô phỏng cho kỹ năng nghề & chi tiết specialization.
"""

import os
import webbrowser

from dotenv import load_dotenv

from coursera_api import CourseraAPIClient
from prompts import MAX_RECOMMENDED_COURSES

load_dotenv()

# =============================================================================
# DỮ LIỆU MÔ PHỎNG (MOCK) — danh mục dự phòng & kỹ năng nghề
# =============================================================================
# Danh mục dự phòng/bổ sung khi Coursera API trả kết quả thưa (offline demo).
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
        "Supervised Machine Learning: Regression and Classification — DeepLearning.AI",
    ],
    "web": [
        "Meta Front-End Developer Professional Certificate — Meta",
        "HTML, CSS, and Javascript for Web Developers — Johns Hopkins",
    ],
    "marketing": [
        "Google Digital Marketing & E-commerce — Google",
        "Digital Marketing Specialization — University of Illinois",
    ],
}

# Kỹ năng cốt lõi theo một số vị trí nghề nghiệp (mô phỏng).
ROLE_SKILLS = {
    "machine learning engineer": ["Python", "Machine Learning", "Deep Learning", "MLOps"],
    "data scientist": ["Python", "Statistics", "Data Analysis", "Machine Learning"],
    "data analyst": ["SQL", "Spreadsheets", "Data Visualization", "Statistics"],
    "web developer": ["HTML/CSS", "JavaScript", "React", "Git"],
    "digital marketer": ["SEO", "Content", "Google Analytics", "Ads"],
}

# Chi tiết một số Specialization (mô phỏng khối lượng học tập).
SPECIALIZATION_DB = {
    "ibm data science specialization": {
        "name": "IBM Data Science Specialization",
        "num_courses": 12, "total_hours": 120, "level": "Beginner",
    },
    "deep learning specialization": {
        "name": "Deep Learning Specialization",
        "num_courses": 5, "total_hours": 100, "level": "Intermediate",
    },
    "machine learning specialization": {
        "name": "Machine Learning Specialization",
        "num_courses": 3, "total_hours": 90, "level": "Beginner",
    },
}


def _topic_key(text: str) -> str:
    """Đoán chủ đề chính từ câu hỏi tự do để dò danh mục mẫu."""
    t = (text or "").lower()
    for key in ["machine learning", "data", "python", "ai", "web", "marketing"]:
        if key in t:
            return key
    return ""


def _api_courses(query: str, limit: int):
    """Gọi Coursera Catalog API thật, chỉ giữ khóa có tên khớp từ khóa."""
    try:
        results = CourseraAPIClient.search_courses(query=query, limit=50)
    except Exception as e:  # noqa: BLE001 - tool không được phép crash Agent
        print(f"⚠️ Coursera API lỗi ({e}), dùng danh mục mẫu.")
        return []
    q = (query or "").lower()
    named = [c.get("name", "") for c in results if c.get("name")]
    # Chỉ giữ khóa có tên KHỚP từ khóa (tránh trả về khóa không liên quan).
    keywords = [w for w in q.split() if len(w) > 2]
    matched = [n for n in named if any(w in n.lower() for w in keywords)]
    return matched[:limit]


def search_coursera_catalog(query: str) -> str:
    """
    Tra cứu khóa học trên Coursera Catalog API (dữ liệu THẬT, có bổ sung mẫu).

    Args:
        query (str): Từ khóa/chủ đề cần tìm (Ví dụ: 'Data Analytics Google', 'Python').

    Returns:
        str: Danh sách khóa học tìm được, hoặc thông báo không tìm thấy.
    """
    query = (query or "").strip()
    if not query:
        return "LỖI: Thiếu từ khóa tìm kiếm."

    courses = _api_courses(query, MAX_RECOMMENDED_COURSES)
    if courses:
        body = "\n".join(f"- {c}" for c in courses)
        return f"[Coursera API] Kết quả cho '{query}':\n{body}"

    key = _topic_key(query)
    if key:
        body = "\n".join(f"- {c}" for c in FALLBACK_CATALOG[key])
        return f"[Danh mục mẫu] Khóa học Coursera cho '{query}':\n{body}"

    return f"LỖI: Không tìm thấy khóa học Coursera nào khớp với '{query}'."


def recommend_courses(goal: str, level: str = "") -> str:
    """
    Tự đề xuất các khóa học Coursera PHÙ HỢP cho một mục tiêu học tập tự do.

    Dùng cho người dùng ẩn danh: không cần hồ sơ/user_id. Kết hợp kết quả API
    Coursera thật với danh mục mẫu để đảm bảo gợi ý sát chủ đề.

    Args:
        goal (str): Mục tiêu/nhu cầu học (Ví dụ: 'học machine learning', 'thành data analyst').
        level (str): (Tùy chọn) trình độ mong muốn ('Beginner', 'Intermediate', 'Advanced').

    Returns:
        str: Danh sách khóa học đề xuất (tối đa MAX_RECOMMENDED_COURSES).
    """
    goal = (goal or "").strip()
    if not goal:
        return "LỖI: Vui lòng cho biết bạn muốn học gì."

    # 1) Ưu tiên khóa THẬT khớp từ khóa mục tiêu
    picked = _api_courses(goal, MAX_RECOMMENDED_COURSES)

    # 2) Bổ sung từ danh mục mẫu theo chủ đề để đủ số lượng & sát chủ đề
    key = _topic_key(goal)
    if key:
        for c in FALLBACK_CATALOG[key]:
            if len(picked) >= MAX_RECOMMENDED_COURSES:
                break
            if c not in picked:
                picked.append(c)

    if not picked:
        return f"LỖI: Chưa tìm được khóa học phù hợp cho mục tiêu '{goal}'."

    level_note = f" (trình độ: {level})" if level else ""
    body = "\n".join(f"- {c}" for c in picked[:MAX_RECOMMENDED_COURSES])
    return f"🎯 Khóa học Coursera gợi ý cho '{goal}'{level_note}:\n{body}"


def analyze_skill_gap(target_role: str) -> str:
    """
    Liệt kê các kỹ năng cốt lõi cần có cho một vị trí nghề nghiệp mục tiêu.

    Không cần hồ sơ người dùng — dùng để định hướng nên học khóa gì.

    Args:
        target_role (str): Vị trí mong muốn (Ví dụ: 'Data Scientist', 'Machine Learning Engineer').

    Returns:
        str: Danh sách kỹ năng nên trang bị cho vị trí đó.
    """
    role = (target_role or "").strip().lower()
    skills = next((v for k, v in ROLE_SKILLS.items() if k in role), None)
    if not skills:
        return (f"Chưa có dữ liệu kỹ năng riêng cho '{target_role}'. "
                f"Gợi ý chung: nền tảng lập trình, tư duy dữ liệu và một dự án thực hành.")
    return f"Để theo hướng '{target_role}', bạn nên nắm: {', '.join(skills)}."


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
    return (f"{spec['name']}: {spec['num_courses']} khóa học, tổng ~{spec['total_hours']} giờ học, "
            f"trình độ {spec['level']}.")


def open_coursera_enrollment_page(course_name: str) -> str:
    """
    Mở/đưa link trang khóa học trên Coursera để người dùng tự đăng ký (không cần đăng nhập).

    Mặc định CHỈ trả về đường dẫn để an toàn khi chạy test suite. Đặt biến môi trường
    AUTO_OPEN_BROWSER=1 nếu muốn thực sự bật tab trình duyệt.

    Args:
        course_name (str): Tên khóa học cần mở trang.

    Returns:
        str: Đường dẫn trang khóa học (và mở tab nếu AUTO_OPEN_BROWSER=1).
    """
    if not (course_name or "").strip():
        return "LỖI: Thiếu tên khóa học để mở trang."
    url = f"https://www.coursera.org/search?query={course_name.strip().replace(' ', '%20')}"
    if os.getenv("AUTO_OPEN_BROWSER") == "1":
        try:
            webbrowser.open(url)
            return f"🌐 Đã mở tab trình duyệt tới '{course_name}': {url}"
        except Exception as e:  # noqa: BLE001
            return f"⚠️ Không mở được trình duyệt ({e}). Truy cập thủ công: {url}"
    return f"🔗 Trang khóa học '{course_name}': {url} (đặt AUTO_OPEN_BROWSER=1 để tự mở tab)."


# Danh sách các tool được đăng ký để Agent sử dụng (đều ẩn danh, không cần user_id)
AVAILABLE_TOOLS = {
    "recommend_courses": recommend_courses,
    "search_coursera_catalog": search_coursera_catalog,
    "analyze_skill_gap": analyze_skill_gap,
    "get_coursera_specialization_details": get_coursera_specialization_details,
    "open_coursera_enrollment_page": open_coursera_enrollment_page,
}
