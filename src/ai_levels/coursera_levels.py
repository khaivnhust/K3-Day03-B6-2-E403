"""
🎓 4 CẤP ĐỘ AI HỘI THOẠI — theo chủ đề Trợ lý Tư vấn Khóa học Coursera.

Cùng một bối cảnh (tư vấn khóa học) thể hiện sự tiến hóa qua 4 cấp:
- Cấp 1: Rule-Based Bot   — if/else khớp từ khóa, không LLM.
- Cấp 2: LLM Chatbot      — sinh text tự nhiên, KHÔNG gọi tool (dễ bịa số liệu).
- Cấp 3: ReAct Agent      — Thought→Action→Observation, gọi tool + Coursera API thật.
- Cấp 4: Autonomous Agent — tự lập kế hoạch (Planning) + bộ nhớ (Memory) qua nhiều bước.

Cấp 3 & 4 dùng chung tool/prompt/API thật của dự án.
"""

import os
import re
import sys

# Cho phép import các module trong src/ khi chạy từ Streamlit hoặc CLI
_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC not in sys.path:
    sys.path.append(_SRC)

from tools import (  # noqa: E402
    get_user_coursera_profile,
    match_coursera_skill_gap,
    search_coursera_catalog,
    register_coursera_enrollment,
)
from prompts import CHATBOT_BASELINE_PROMPT  # noqa: E402
from agent_core import react_agent_steps  # noqa: E402


# =============================================================================
# CẤP ĐỘ 1 — RULE-BASED BOT (if/else, không LLM)
# =============================================================================
def level1_rule_based(user_input: str) -> str:
    text = (user_input or "").lower()
    if any(k in text for k in ["chào", "hi ", "hello", "xin chào"]):
        return "Xin chào! Tôi là Rule-Based Bot (Cấp 1) của cổng khóa học. Bạn cần hỏi gì?"
    if "coursera là gì" in text or ("coursera" in text and "là gì" in text):
        return "Coursera là nền tảng học trực tuyến (MOOC) cung cấp Course, Specialization và Professional Certificate."
    if "học phí" in text or "giá" in text or "chi phí" in text:
        return "Học phí tuỳ khóa: nhiều khóa có thể học miễn phí (audit); lấy chứng chỉ thường ~$49/tháng."
    if "chứng chỉ" in text or "certificate" in text:
        return "Hoàn thành khóa học đạt yêu cầu, bạn nhận Certificate có thể chia sẻ lên LinkedIn."
    if "liên hệ" in text or "hotline" in text or "hỗ trợ" in text:
        return "Hỗ trợ học vụ: 1900-1234 · Email: support@coursemate.edu.vn"
    return "Xin lỗi, câu hỏi nằm ngoài tập luật (keywords) cài sẵn của Cấp 1. Hãy thử Cấp 2–4!"


# =============================================================================
# CẤP ĐỘ 2 — LLM CHATBOT (baseline, không tool)
# =============================================================================
def level2_llm_chatbot(user_input: str, provider) -> str:
    """Dùng LLM sinh câu trả lời tự nhiên nhưng KHÔNG có công cụ tra cứu."""
    return provider.generate(user_input, system_prompt=CHATBOT_BASELINE_PROMPT)


# =============================================================================
# CẤP ĐỘ 3 — REACT AGENT (Thought → Action → Observation, có tool)
# =============================================================================
def level3_react_agent(user_input: str, provider):
    """Trả về danh sách các bước ReAct có cấu trúc (xem agent_core.react_agent_steps)."""
    return react_agent_steps(user_input, provider)


# =============================================================================
# CẤP ĐỘ 4 — AUTONOMOUS AGENT (Planning + Memory qua nhiều bước, dùng tool thật)
# =============================================================================
_ROLE_KEYWORDS = {
    "machine learning": "machine learning",
    "ml engineer": "machine learning",
    "data scientist": "data",
    "data analyst": "data",
    "ai": "ai",
    "python": "python",
}


def _extract_user_id(text: str) -> str:
    m = re.search(r"user_[a-z]+_\d+", (text or "").lower())
    return m.group(0).upper() if m else "USER_CS_9921"


def _extract_role(text: str) -> str:
    t = (text or "").lower()
    for k in ["machine learning engineer", "ml engineer", "data scientist", "data analyst"]:
        if k in t:
            return k
    return "Machine Learning Engineer"


def _search_keyword(role: str) -> str:
    r = role.lower()
    for k, v in _ROLE_KEYWORDS.items():
        if k in r:
            return v
    return "data"


def level4_autonomous_agent(goal: str, enroll: bool = False):
    """
    Agent tự chủ: tự chia mục tiêu phức tạp thành nhiều bước con (Planning),
    thực thi tool thật cho từng bước và lưu vết vào Memory, cuối cùng tổng hợp.

    Trả về dict: {goal, user_id, target_role, plan, memory, final_answer}
    """
    user_id = _extract_user_id(goal)
    role = _extract_role(goal)
    keyword = _search_keyword(role)

    # 1) PLANNING — tự rã mục tiêu thành các bước con
    plan = [
        f"Bước 1: Xác thực hồ sơ học viên {user_id}",
        f"Bước 2: Phân tích kỹ năng còn thiếu để trở thành {role}",
        f"Bước 3: Tra cứu khóa học Coursera phù hợp (chủ đề: {keyword})",
        "Bước 4: Tổng hợp lộ trình" + (" và đăng ký khóa đầu tiên" if enroll else ""),
    ]

    # 2) EXECUTION + MEMORY — thực thi tool thật, lưu vết từng bước
    memory = []

    prof = get_user_coursera_profile(user_id)
    memory.append({"step": 1, "plan": plan[0],
                   "action": f"get_user_coursera_profile[{user_id}]", "result": prof})

    # Tự đánh giá: hồ sơ lỗi -> dừng sớm (autonomous self-evaluation)
    if prof.startswith("LỖI"):
        return {
            "goal": goal, "user_id": user_id, "target_role": role,
            "plan": plan, "memory": memory,
            "final_answer": f"⛔ Không thể tiếp tục: {prof} Vui lòng cung cấp mã học viên hợp lệ.",
        }

    gap = match_coursera_skill_gap(user_id, role)
    memory.append({"step": 2, "plan": plan[1],
                   "action": f"match_coursera_skill_gap[{user_id}, {role}]", "result": gap})

    catalog = search_coursera_catalog(keyword)
    memory.append({"step": 3, "plan": plan[2],
                   "action": f"search_coursera_catalog[{keyword}]", "result": catalog})

    # 4) Tổng hợp (+ đăng ký nếu yêu cầu)
    first_course = "Machine Learning Specialization"
    for line in catalog.splitlines():
        if line.strip().startswith("-"):
            first_course = line.strip().lstrip("- ").split(" (slug")[0]
            break

    enroll_note = ""
    if enroll:
        enr = register_coursera_enrollment(user_id, first_course)
        memory.append({"step": 4, "plan": plan[3],
                       "action": f"register_coursera_enrollment[{user_id}, {first_course}]",
                       "result": enr})
        enroll_note = f"\n\n📝 {enr}"

    final = (
        f"✅ Lộ trình cho {user_id} → mục tiêu **{role}**:\n"
        f"- {gap}\n"
        f"- Khóa gợi ý bắt đầu: **{first_course}**\n"
        f"- (Đã tra cứu Coursera theo chủ đề '{keyword}')."
        f"{enroll_note}"
    )

    return {
        "goal": goal, "user_id": user_id, "target_role": role,
        "plan": plan, "memory": memory, "final_answer": final,
    }


if __name__ == "__main__":
    from providers import get_llm_provider
    p = get_llm_provider()
    print("L1:", level1_rule_based("Coursera là gì?"))
    print("L2:", level2_llm_chatbot("Học Data Science cần gì?", p))
    print("L4:", level4_autonomous_agent(
        "Tôi là USER_CS_9921 muốn thành Machine Learning Engineer, lập lộ trình học", enroll=True
    )["final_answer"])
