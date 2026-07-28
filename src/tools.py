"""
🛠️ TOOL REGISTRY & SCHEMAS (Dành cho Role 2: Tool & Spec Engineer)
Nơi khai báo tất cả các "món đồ nghề" mà ReAct Agent có thể gọi.
"""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

# Dữ liệu học viên được giữ ở dạng mẫu local, chỉ phục vụ demo cho app cá nhân.
CURRENT_STUDENT = {
    "student_id": "SV001",
    "name": "Nguyễn An",
    "major": "Công nghệ thông tin",
    "year": 2,
    "gpa": 3.4,
    "credits": 78,
    "courses": ["CS101", "CS201", "MATH101"],
    "advisor": "TS. Minh"
}

def get_weather(location: str) -> str:
    """
    Tra cứu thời tiết hiện tại của một thành phố.

    Args:
        location (str): Tên thành phố (Ví dụ: 'Hà Nội', 'TP.HCM', 'Đà Nẵng')

    Returns:
        str: Thông tin thời tiết chi tiết
    """
    loc_lower = location.lower()
    if "hà nội" in loc_lower or "ha noi" in loc_lower:
        return "Thời tiết Hà Nội: 28°C, Nắng nhẹ, Độ ẩm 65%."
    elif "hồ chí minh" in loc_lower or "tp.hcm" in loc_lower or "hcm" in loc_lower:
        return "Thời tiết TP.HCM: 33°C, Nắng nóng, Có mây."
    elif "đà nẵng" in loc_lower or "da nang" in loc_lower:
        return "Thời tiết Đà Nẵng: 30°C, Gió nhẹ, Mát mẻ."
    else:
        return f"LỖI: Không tìm thấy dữ liệu thời tiết cho địa điểm '{location}'."


def search_flights(origin: str, destination: str) -> str:
    """
    Tra cứu chuyến bay giữa hai địa điểm.

    Args:
        origin (str): Nơi đi (Ví dụ: 'TP.HCM')
        destination (str): Nơi đến (Ví dụ: 'Hà Nội')

    Returns:
        str: Danh sách chuyến bay khả dụng và giá vé
    """
    return (
        f"Chuyến bay từ {origin} -> {destination} ngày mai:\n"
        f"1. VN123 (08:00) - Giá: 1,500,000 VNĐ (Còn vé)\n"
        f"2. VJ456 (14:30) - Giá: 1,200,000 VNĐ (Còn vé)"
    )

def get_student_profile(student_id: str) -> str:
    """
    Lấy thông tin cơ bản của học viên hiện tại trong app.

    Args:
        student_id (str): Mã số sinh viên cần truy vấn (Ví dụ: 'SV001')

    Returns:
        str: Thông tin hồ sơ học viên như tên, ngành, năm học và cố vấn học tập
    """
    if student_id.upper() != CURRENT_STUDENT["student_id"]:
        return f"LỖI: Chỉ hỗ trợ xem thông tin cho học viên hiện tại '{CURRENT_STUDENT['student_id']}'."

    student = CURRENT_STUDENT
    return (
        f"Học viên {student['student_id']}: {student['name']}, ngành {student['major']}, "
        f"năm học {student['year']}, cố vấn {student['advisor']}."
    )


def get_student_academic_status(student_id: str) -> str:
    """
    Lấy trạng thái học tập của học viên hiện tại trong app.

    Args:
        student_id (str): Mã số sinh viên cần truy vấn (Ví dụ: 'SV001')

    Returns:
        str: Điểm trung bình, số tín chỉ và các môn đang học
    """
    if student_id.upper() != CURRENT_STUDENT["student_id"]:
        return f"LỖI: Chỉ hỗ trợ xem thông tin cho học viên hiện tại '{CURRENT_STUDENT['student_id']}'."

    student = CURRENT_STUDENT
    return (
        f"Học viên {student['student_id']}: GPA {student['gpa']}, {student['credits']} tín chỉ, "
        f"đang học các môn {', '.join(student['courses'])}."
    )


def recommend_coursera_skills(student_id: str) -> str:
    """
    Đề xuất các khóa học kỹ năng trên Coursera phù hợp với học viên hiện tại.

    Args:
        student_id (str): Mã số sinh viên cần đề xuất khóa học (Ví dụ: 'SV001')

    Returns:
        str: Danh sách các khóa học Coursera phù hợp với ngành, năm học và mức độ học tập hiện tại
    """
    if student_id.upper() != CURRENT_STUDENT["student_id"]:
        return f"LỖI: Chỉ hỗ trợ đề xuất cho học viên hiện tại '{CURRENT_STUDENT['student_id']}'."

    student = CURRENT_STUDENT
    major = student["major"].lower()
    year = student["year"]
    gpa = student["gpa"]

    if "công nghệ thông tin" in major or "it" in major:
        recommendations = [
            "Google - Python for Everybody",
            "Meta - Introduction to Front-End Development",
            "DeepLearning.AI - Generative AI with Large Language Models"
        ]
    elif "kinh tế" in major:
        recommendations = [
            "University of Michigan - Data Analysis with Python",
            "University of Illinois - Financial Analysis for Decision Making"
        ]
    else:
        recommendations = [
            "Coursera - Communication Skills for University Success",
            "University of California - Learning How to Learn"
        ]

    if year >= 3:
        recommendations.append("Google - Agile Project Management")
    if gpa >= 3.0:
        recommendations.append("IBM - Data Science Fundamentals")

    return (
        f"Gợi ý khóa học Coursera cho {student['name']} ({student['major']}):\n"
        + "\n".join(f"- {course}" for course in recommendations)
    )


def get_coursera_courses(topic: str) -> str:
    """
    Lấy các khóa học Coursera theo một chủ đề hoặc lĩnh vực cụ thể.

    Args:
        topic (str): Chủ đề hoặc lĩnh vực cần tìm khóa học (Ví dụ: 'python', 'AI', 'quản lý')

    Returns:
        str: Danh sách các khóa học Coursera liên quan đến chủ đề đã cho
    """
    topic_lower = topic.lower()

    if "python" in topic_lower:
        courses = [
            "Python for Everybody - University of Michigan",
            "Crash Course on Python - Google"
        ]
    elif "ai" in topic_lower or "trí tuệ nhân tạo" in topic_lower:
        courses = [
            "Generative AI with Large Language Models - DeepLearning.AI",
            "AI For Everyone - DeepLearning.AI"
        ]
    elif "quản lý" in topic_lower or "management" in topic_lower:
        courses = [
            "Agile Project Management - Google",
            "Project Management Principles - University of California"
        ]
    elif "dữ liệu" in topic_lower or "data" in topic_lower:
        courses = [
            "Data Science Fundamentals - IBM",
            "Data Analysis with Python - University of Michigan"
        ]
    else:
        courses = [
            "Learning How to Learn - University of California",
            "Communication Skills for University Success - Coursera"
        ]

    return (
        f"Các khóa học Coursera về '{topic}':\n"
        + "\n".join(f"- {course}" for course in courses)
    )


# Danh sách các tool được đăng ký để Agent sử dụng
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "search_flights": search_flights,
    "get_student_profile": get_student_profile,
    "get_student_academic_status": get_student_academic_status,
    "recommend_coursera_skills": recommend_coursera_skills,
    "get_coursera_courses": get_coursera_courses,
}


