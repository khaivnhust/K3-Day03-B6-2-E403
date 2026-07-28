"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import (
    AVAILABLE_TOOLS,
    get_weather,
    search_flights,
    get_student_profile,
    get_student_academic_status,
    recommend_coursera_skills,
    get_coursera_courses,
)
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")




def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    step = 0

    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        tool_call = route_query_to_tool(user_query)
        print(f"🧠 Thought: {tool_call['thought']}")
        print(f"🛠️ Action: {tool_call['action']}")

        if tool_call["tool_name"] is None:
            obs = "Không có tool phù hợp để gọi."
        else:
            tool_fn = AVAILABLE_TOOLS[tool_call["tool_name"]]
            obs = tool_fn(*tool_call["args"])

        print(f"👁️ Observation: {obs}")

        if "khóa học" in user_query.lower() or "course" in user_query.lower():
            print("🧠 Thought: Tôi đã có danh sách khóa học, tiếp tục đề xuất khóa học phù hợp cho học viên.")
            rec_obs = AVAILABLE_TOOLS["recommend_coursera_skills"]("SV001")
            print(f"🛠️ Action: recommend_coursera_skills['SV001']")
            print(f"👁️ Observation: {rec_obs}")

        break

    if step >= MAX_ITERATIONS:
        print(f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


def run_test_suite(provider):
    """Chạy toàn bộ test cases từ file config/test_cases.json."""
    tests = load_test_cases()
    for case in tests:
        if "question" not in case:
            continue

        print(f"\n===== Test {case.get('id', '?')} - {case.get('category', 'Unknown')} =====")
        print(f"❓ Câu hỏi: {case['question']}")
        run_baseline_chatbot(case["question"], provider)
        run_react_agent(case["question"], provider)


if __name__ == "__main__":
    print("==================================================")
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("==================================================")
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")

    run_test_suite(provider)
