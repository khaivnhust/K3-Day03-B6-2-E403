"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer / Integrator)
Ghép nối Tools + Prompts + Test Cases + Multi-Provider và chạy vòng lặp ReAct thật.
"""

import json
import os
import re
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

from tools import AVAILABLE_TOOLS  # noqa: E402
from prompts import (  # noqa: E402
    CHATBOT_BASELINE_PROMPT,
    REACT_SYSTEM_PROMPT,
    MAX_ITERATIONS,
    MAX_IDENTICAL_ACTIONS,
)
from providers import get_llm_provider  # noqa: E402

load_dotenv()

# Regex trích xuất Action và Final Answer từ output của LLM
ACTION_RE = re.compile(r"Action:\s*([A-Za-z_]\w*)\s*\[(.*?)\]", re.DOTALL)
FINAL_RE = re.compile(r"Final Answer:\s*(.+)", re.DOTALL)
THOUGHT_RE = re.compile(r"Thought:\s*(.+)")


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


def _parse_args(raw_args: str):
    """Tách chuỗi tham số 'a, b' -> ['a', 'b'], loại bỏ dấu nháy/khoảng trắng."""
    if not raw_args.strip():
        return []
    parts = [p.strip().strip("'\"") for p in raw_args.split(",")]
    return [p for p in parts if p != ""]


def _execute_tool(tool_name: str, args) -> str:
    """Gọi tool an toàn — mọi lỗi được biến thành Observation dạng chuỗi, không crash."""
    tool_fn = AVAILABLE_TOOLS.get(tool_name)
    if tool_fn is None:
        return f"LỖI: Không tồn tại công cụ '{tool_name}'."
    try:
        return tool_fn(*args)
    except TypeError as e:
        return f"LỖI: Sai số lượng/kiểu tham số cho '{tool_name}' ({e})."
    except Exception as e:  # noqa: BLE001 - tool không được phép làm sập Agent
        return f"LỖI: Công cụ '{tool_name}' gặp sự cố ({e})."


def run_react_agent(user_query: str, provider):
    """
    Vòng lặp ReAct thật: Thought -> Action -> Observation, do LLM điều khiển,
    có Guardrails (giới hạn số vòng, chặn lặp Action trùng, chịu lỗi tool).
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    scratchpad = f"Câu hỏi của người dùng: {user_query}\n"
    action_counts: dict[str, int] = {}

    for step in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")

        llm_out = provider.generate(scratchpad, system_prompt=REACT_SYSTEM_PROMPT)

        # In Thought (nếu có) để quan sát (observability)
        thought = THOUGHT_RE.search(llm_out)
        if thought:
            print(f"🧠 Thought: {thought.group(1).strip().splitlines()[0]}")

        # 1) Nếu LLM đã đưa Final Answer -> kết thúc
        final = FINAL_RE.search(llm_out)
        action = ACTION_RE.search(llm_out)
        # Ưu tiên Action nếu nó xuất hiện TRƯỚC Final Answer trong cùng output
        if final and (not action or final.start() < action.start()):
            print(f"🏁 Final Answer: {final.group(1).strip()}")
            return

        # 2) Không parse được Action -> coi phần text là câu trả lời cuối
        if not action:
            print(f"🏁 Final Answer (không có Action): {llm_out.strip()}")
            return

        tool_name = action.group(1)
        args = _parse_args(action.group(2))
        action_key = f"{tool_name}[{action.group(2).strip()}]"
        print(f"🛠️ Action: {action_key}")

        # 3) GUARDRAIL: chặn lặp lại y hệt một Action
        if action_counts.get(action_key, 0) >= MAX_IDENTICAL_ACTIONS:
            print(
                f"🛡️ GUARDRAIL: Action '{action_key}' bị lặp quá "
                f"{MAX_IDENTICAL_ACTIONS} lần. Ngắt để tránh vòng lặp vô tận."
            )
            return
        action_counts[action_key] = action_counts.get(action_key, 0) + 1

        # 4) Thực thi tool -> Observation
        obs = _execute_tool(tool_name, args)
        print(f"👁️ Observation: {obs}")

        # 5) Nối vào scratchpad cho vòng lặp kế tiếp
        scratchpad += (
            f"Thought: {thought.group(1).strip().splitlines()[0] if thought else ''}\n"
            f"Action: {action_key}\n"
            f"Observation: {obs}\n"
        )

    print(
        f"🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. "
        f"Ngắt lặp an toàn và trả lời dựa trên thông tin đã có."
    )


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
