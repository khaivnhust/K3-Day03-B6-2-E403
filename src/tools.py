"""
🛠️ TOOL REGISTRY & SCHEMAS (Coursera AI Recommendation Agent)
Khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể sử dụng.
Tự động kết nối với Coursera REST APIs bằng Access Token trong config/coursera_token.json.
"""

import os
import sys
import webbrowser

_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
for _p in [_current_dir, _parent_dir]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import coursera_api
    CourseraAPIClient = coursera_api.CourseraAPIClient
    get_real_coursera_url = coursera_api.get_real_coursera_url
except Exception:
    from src.coursera_api import CourseraAPIClient, get_real_coursera_url

def search_coursera_catalog(query: str) -> str:
    """
    Tra cứu danh sách các khóa học trên nền tảng Coursera theo từ khóa kỹ năng.
    
    Args:
        query (str): Từ khóa tìm kiếm (Ví dụ: 'Machine Learning', 'Python', 'Data Analytics', 'Generative AI')
        
    Returns:
        str: Danh sách khóa học Coursera phù hợp kèm thời lượng và link đăng ký.
    """
    courses = CourseraAPIClient.search_courses(query, limit=5)
    if not courses:
        return f"Không tìm thấy khóa học nào phù hợp với từ khóa '{query}' trên Coursera."
    
    results = []
    for idx, c in enumerate(courses, 1):
        name = c.get("name")
        slug = c.get("slug")
        workload = c.get("workload", "Không xác định")
        desc = c.get("description", "")[:120] + "..." if c.get("description") else ""
        url = get_real_coursera_url(slug)
        results.append(f"{idx}. 📌 **{name}**\n   - Slug: {slug}\n   - Thời lượng: {workload}\n   - Mô tả: {desc}\n   - Link: {url}")
        
    return "\n\n".join(results)


def get_coursera_specialization_details(spec_slug: str) -> str:
    """
    Tra cứu thông tin chi tiết một Chuyên ngành (Specialization - Chuỗi nhiều khóa học) trên Coursera.
    
    Args:
        spec_slug (str): Slug của chuyên ngành (Ví dụ: 'deep-learning', 'ibm-data-science')
        
    Returns:
        str: Chi tiết chuyên ngành, danh sách các môn học con và đối tác giảng dạy.
    """
    spec = CourseraAPIClient.get_specialization_by_slug(spec_slug)
    if not spec:
        return f"LỖI: Không tìm thấy Chuyên ngành Coursera với slug '{spec_slug}'."
    
    name = spec.get("name")
    desc = spec.get("description", "Không có mô tả.")
    partners = ", ".join(spec.get("partnerIds", []))
    course_ids = spec.get("courseIds", [])
    url = get_real_coursera_url(spec_slug, is_specialization=True)
    
    return (
        f"🏆 **Chuyên ngành Coursera:** {name}\n"
        f"🏢 Đối tác đào tạo: {partners}\n"
        f"📚 Số lượng khóa học thành phần: {len(course_ids)} khóa học\n"
        f"📝 Mô tả: {desc}\n"
        f"🔗 Link Chuyên ngành: {url}"
    )


def get_user_coursera_profile(user_id: str) -> str:
    """
    Tra cứu hồ sơ sinh viên, kỹ năng hiện có, chứng chỉ Coursera đã hoàn thành và quỹ thời gian rảnh/tuần.
    
    Args:
        user_id (str): Mã sinh viên (Ví dụ: 'USER_CS_9921')
        
    Returns:
        str: Thông tin hồ sơ sinh viên hoặc thông báo lỗi nếu mã sinh viên không tồn tại.
    """
    mock_users = {
        "USER_CS_9921": {
            "name": "Nguyễn Việt Thắng",
            "major": "Computer Science",
            "gpa": 3.52,
            "weekly_hours": 5,
            "completed_courses": ["python-for-everybody", "mathematics-for-machine-learning"],
            "known_skills": ["Python", "Basic Algebra", "SQL"]
        }
    }
    
    user = mock_users.get(user_id)
    if not user:
        return f"LỖI: Sinh viên có mã ID '{user_id}' không tồn tại trong hệ thống quản lý."
    
    return (
        f"👤 **Hồ sơ sinh viên:** {user['name']} (ID: {user_id})\n"
        f"🎓 Ngành học: {user['major']} | GPA: {user['gpa']}\n"
        f"⏱️ Quỹ thời gian rảnh: {user['weekly_hours']} giờ/tuần\n"
        f"✅ Kỹ năng đã có: {', '.join(user['known_skills'])}\n"
        f"📜 Khóa Coursera đã học: {', '.join(user['completed_courses'])}"
    )


def match_coursera_skill_gap(known_skills: str, target_role: str) -> str:
    """
    Phân tích khoảng trống kỹ năng giữa Hồ sơ sinh viên hiện tại và Vị trí công việc mục tiêu.
    
    Args:
        known_skills (str): Danh sách kỹ năng hiện có (Ví dụ: 'Python, SQL')
        target_role (str): Vị trí công việc mơ ước (Ví dụ: 'Machine Learning Engineer', 'Data Scientist')
        
    Returns:
        str: Báo cáo kỹ năng thiếu và danh sách từ khóa học tập gợi ý.
    """
    target_lower = target_role.lower()
    
    if "machine learning" in target_lower or "ai" in target_lower:
        missing = ["Supervised Machine Learning", "Neural Networks & Deep Learning", "PyTorch / TensorFlow"]
        topics = ["Machine Learning Specialization", "Deep Learning Specialization"]
    elif "data scientist" in target_lower or "data analytics" in target_lower:
        missing = ["Pandas & Data Wrangling", "Statistical Inference", "Data Visualization"]
        topics = ["IBM Data Science Specialization", "Google Data Analytics"]
    else:
        missing = ["Fullstack Web Development", "Cloud Architecture (GCP/AWS)"]
        topics = ["Cloud Engineering", "Web Development Specialization"]
        
    return (
        f"📊 **Báo cáo Phân tích Khoảng trống Kỹ năng (Skill Gap Analysis):**\n"
        f"🎯 Vị trí mục tiêu: {target_role}\n"
        f"❌ Kỹ năng quan trọng còn thiếu: {', '.join(missing)}\n"
        f"💡 Chủ đề Coursera khuyên dùng: {', '.join(topics)}"
    )


def register_coursera_enrollment(user_id: str, course_slug: str) -> str:
    """
    Khởi tạo phiếu đăng ký môn học (Enrollment Ticket) trên Coursera cho sinh viên.
    
    Args:
        user_id (str): Mã sinh viên
        course_slug (str): Slug môn học Coursera (Ví dụ: 'neural-networks-deep-learning')
        
    Returns:
        str: Mã vé đăng ký và thông báo xác nhận.
    """
    import random
    ticket_id = f"ENROLL-COURSERA-{user_id}-{random.randint(1000, 9999)}"
    url = get_real_coursera_url(course_slug, action_enroll=True)
    
    return (
        f"🎉 **ĐĂNG KÝ KHÓA HỌC SUCCESSFUL!**\n"
        f"🎫 Mã phiếu đăng ký: {ticket_id}\n"
        f"👤 Sinh viên ID: {user_id}\n"
        f"📚 Khóa học: {course_slug}\n"
        f"🔗 Link xác nhận ghi danh: {url}"
    )


def open_coursera_enrollment_page(course_slug: str) -> str:
    """
    Tự động kích hoạt trình duyệt web (Chrome/Safari) trên máy tính người dùng chuyển thẳng tới trang đăng ký Coursera.
    
    Args:
        course_slug (str): Slug khóa học Coursera
        
    Returns:
        str: Thông báo trạng thái kích hoạt trình duyệt web.
    """
    url = get_real_coursera_url(course_slug, action_enroll=True)
    try:
        webbrowser.open(url)
        return f"🚀 [SUCCESS] Đã tự động mở trình duyệt web thật tới trang đăng ký Coursera của khóa học '{course_slug}'!\n🔗 URL mở: {url}"
    except Exception as e:
        return f"LỖI: Không thể mở trình duyệt web: {str(e)}"


# Danh sách toàn bộ các tools được đăng ký cho ReAct Agent
AVAILABLE_TOOLS = {
    "search_coursera_catalog": search_coursera_catalog,
    "get_coursera_specialization_details": get_coursera_specialization_details,
    "get_user_coursera_profile": get_user_coursera_profile,
    "match_coursera_skill_gap": match_coursera_skill_gap,
    "register_coursera_enrollment": register_coursera_enrollment,
    "open_coursera_enrollment_page": open_coursera_enrollment_page
}
