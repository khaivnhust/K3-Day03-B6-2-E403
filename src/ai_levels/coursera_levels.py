"""
🎓 4 CẤP ĐỘ AI HỘI THOẠI — theo chủ đề Trợ lý Tư vấn Khóa học Coursera (ẩn danh).

Bất kỳ ai hỏi cũng được (không cần user_id). Agent tự tìm khóa học phù hợp.
Cùng một bối cảnh thể hiện sự tiến hóa qua 4 cấp:
- Cấp 1: Rule-Based Bot   — if/else khớp từ khóa, không LLM.
- Cấp 2: LLM Chatbot      — sinh text tự nhiên, KHÔNG gọi tool (dễ bịa số liệu).
- Cấp 3: ReAct Agent      — Thought→Action→Observation, gọi tool + Coursera API thật.
- Cấp 4: Autonomous Agent — tự lập kế hoạch (Planning) + bộ nhớ (Memory) qua nhiều bước.

Cấp 3 & 4 dùng chung tool/prompt/API thật của dự án.
"""

import os
import sys

# Cho phép import các module trong src/ khi chạy từ Streamlit hoặc CLI
_SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC not in sys.path:
    sys.path.append(_SRC)

from tools import (  # noqa: E402
    analyze_skill_gap,
    recommend_courses,
    open_coursera_enrollment_page,
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
def _extract_role(text: str) -> str:
    t = (text or "").lower()
    for k in ["machine learning engineer", "ml engineer", "data scientist",
              "data analyst", "web developer", "digital marketer"]:
        if k in t:
            return k
    return ""


def _extract_topic(text: str) -> str:
    t = (text or "").lower()
    for k in ["machine learning", "data", "python", "ai", "web", "marketing"]:
        if k in t:
            return k
    return "lập trình"


def level4_autonomous_agent(goal: str, level: str = "", open_page: bool = False):
    """
    Agent tự chủ (ẩn danh): tự chia mục tiêu thành nhiều bước con (Planning),
    thực thi tool thật cho từng bước và lưu vết vào Memory, cuối cùng tổng hợp.

    Trả về dict: {goal, target_role, topic, plan, memory, final_answer}
    """
    role = _extract_role(goal)
    topic = _extract_topic(goal)

    # 1) PLANNING — tự rã mục tiêu thành các bước con
    plan = []
    if role:
        plan.append(f"Bước 1: Xác định kỹ năng cần có cho vị trí '{role}'")
    plan.append(f"Bước {len(plan)+1}: Tự tìm khóa học Coursera phù hợp (chủ đề: {topic})")
    plan.append(f"Bước {len(plan)+1}: Tổng hợp gợi ý" + (" và đưa link trang khóa học" if open_page else ""))

    # 2) EXECUTION + MEMORY — thực thi tool thật, lưu vết từng bước
    memory = []
    step = 0
    gap = ""
    if role:
        step += 1
        gap = analyze_skill_gap(role)
        memory.append({"step": step, "plan": plan[step - 1],
                       "action": f"analyze_skill_gap[{role}]", "result": gap})

    step += 1
    recs = recommend_courses(goal, level)
    memory.append({"step": step, "plan": plan[step - 1],
                   "action": f"recommend_courses[{goal}, {level or '-'}]", "result": recs})

    # Lấy khóa gợi ý đầu tiên
    first_course = ""
    for line in recs.splitlines():
        if line.strip().startswith("-"):
            first_course = line.strip().lstrip("- ").split(" (slug")[0]
            break

    open_note = ""
    if open_page and first_course:
        step += 1
        link = open_coursera_enrollment_page(first_course)
        memory.append({"step": step, "plan": plan[-1],
                       "action": f"open_coursera_enrollment_page[{first_course}]", "result": link})
        open_note = f"\n\n{link}"

    final = (
        (f"🎯 Định hướng '{role}': {gap}\n\n" if gap else "")
        + f"{recs}"
        + (f"\n\n👉 Nên bắt đầu với: **{first_course}**" if first_course else "")
        + open_note
    )

    return {"goal": goal, "target_role": role or "(không chỉ định)",
            "topic": topic, "plan": plan, "memory": memory, "final_answer": final}


if __name__ == "__main__":
    from providers import get_llm_provider
    p = get_llm_provider()
    print("L1:", level1_rule_based("Coursera là gì?"))
    print("L2:", level2_llm_chatbot("Học Data Science cần gì?", p))
    print("L4:", level4_autonomous_agent("Tôi muốn học machine learning cho người mới", open_page=True)["final_answer"])
