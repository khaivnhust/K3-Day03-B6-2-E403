"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer / Integrator)
Ghép nối Tools + Prompts + Test Cases + Multi-Provider và chạy vòng lặp ReAct thật.
Lõi ReAct nằm ở src/agent_core.py (dùng chung với Streamlit demo).
"""

import json
import os
import sys

from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS  # noqa: E402
from providers import get_llm_provider  # noqa: E402
from agent_core import react_agent_steps  # noqa: E402

load_dotenv()


def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """Chatbot gốc (Baseline) — chỉ dùng LLM, không có công cụ."""
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """Vòng lặp ReAct thật — in các bước Thought -> Action -> Observation ra CLI."""
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    steps = react_agent_steps(user_query, provider)
    for s in steps:
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {s['step']}/{MAX_ITERATIONS}) ---")
        if s["thought"]:
            print(f"🧠 Thought: {s['thought']}")
        if s["action"]:
            print(f"🛠️ Action: {s['action']}")
        if s["observation"] is not None:
            print(f"👁️ Observation: {s['observation']}")
        if s["final_answer"] is not None:
            print(f"🏁 Final Answer: {s['final_answer']}")
        if s["guardrail"] is not None:
            print(f"🛡️ GUARDRAIL TRIGGERED: {s['guardrail']}")


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
    print("🎓 Đề tài: Trợ lý Tư vấn Khóa học Coursera (Hybrid)")
    print("==================================================")

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider: {provider.__class__.__name__} (Model: {model_name})")

    tests = load_test_cases()
    print(f"✅ Đã tải {len(tests)} Test Cases từ config/test_cases.json\n")

    run_test_suite(provider)
