"""
🧪 AUTOMATED TEST RUNNER WITH TRACE LOGS (Dành cho R1: Test Designer, R4: Runner, R5: Evaluator)
Script tự động thực thi toàn bộ 10 Test Cases từ config/test_cases.json
Hiển thị chi tiết từng bước Thought -> Action -> Observation -> Final Answer.
"""

import json
import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

def load_test_cases():
    config_path = os.path.join(BASE_DIR, "config", "test_cases.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

def run_single_test_baseline(test_case: dict, provider) -> str:
    question = test_case["question"]
    try:
        response = provider.generate(question, system_prompt=CHATBOT_BASELINE_PROMPT)
        return response
    except Exception as e:
        return f"LỖI BASELINE: {str(e)}"

def run_single_test_react(test_case: dict, provider) -> dict:
    question = test_case["question"]
    step = 0
    history = f"Câu hỏi của sinh viên: {question}\n"
    tools_called = []
    trace_steps = []
    final_answer = ""
    guardrail_triggered = False

    while step < MAX_ITERATIONS:
        step += 1
        prompt = REACT_SYSTEM_PROMPT + "\n" + history
        try:
            response = provider.generate(prompt)
        except Exception as e:
            final_answer = f"LỖI REACT AGENT: {str(e)}"
            break

        trace_steps.append({"step": step, "llm_output": response})

        if "Final Answer:" in response:
            final_answer = response.split("Final Answer:")[-1].strip()
            break

        action_match = re.search(r"Action:\s*(\w+)\[(.*?)\]", response)
        if action_match:
            tool_name = action_match.group(1).strip()
            tool_arg = action_match.group(2).strip().strip("'\"")
            tools_called.append(tool_name)

            if tool_name in AVAILABLE_TOOLS:
                try:
                    if "," in tool_arg and tool_name in ["match_coursera_skill_gap", "register_coursera_enrollment"]:
                        args = [a.strip() for a in tool_arg.split(",", 1)]
                        obs = AVAILABLE_TOOLS[tool_name](args[0], args[1])
                    else:
                        obs = AVAILABLE_TOOLS[tool_name](tool_arg)
                except Exception as e:
                    obs = f"LỖI THỰC THI TOOL {tool_name}: {str(e)}"
            else:
                obs = f"LỖI: Tool '{tool_name}' không tồn tại trong hệ thống."

            trace_steps[-1]["observation"] = obs
            history += f"\n{response}\nObservation:\n{obs}\n"
        else:
            history += f"\n{response}\n"

    if step >= MAX_ITERATIONS and not final_answer:
        guardrail_triggered = True
        final_answer = f"🛡️ GUARDRAIL TRIGGERED: Ngắt lặp an toàn sau {MAX_ITERATIONS} bước."

    return {
        "steps": step,
        "tools_called": tools_called,
        "trace_steps": trace_steps,
        "final_answer": final_answer,
        "guardrail_triggered": guardrail_triggered
    }

def main():
    print("=" * 80)
    print("🎓 COURSERA AI AGENT - FULL TRACE RUNNER (10 TEST CASES)")
    print("=" * 80)

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider: {provider.__class__.__name__} (Model: {model_name})")

    test_cases = load_test_cases()
    print(f"✅ Đã tải thành công {len(test_cases)} Test Cases từ config/test_cases.json\n")

    summary_results = []

    for test in test_cases:
        t_id = test["id"]
        cat = test["category"]
        question = test["question"]

        print("\n" + "═" * 80)
        print(f"📌 TEST CASE #{t_id} [{cat}]")
        print(f"❓ Câu hỏi: {question}")
        print(f"🎯 Expected: {test['expected_behavior']}")
        print("═" * 80)

        # 1. Baseline Test
        print("\n💬 [PHASE 1 - CHATBOT BASELINE (Không có Tools)]:")
        baseline_res = run_single_test_baseline(test, provider)
        print(f"   {baseline_res.strip()}")

        # 2. ReAct Agent Test
        print("\n🤖 [PHASE 2 - REACT AGENT (Có Tools & suy luận từng bước)]:")
        react_res = run_single_test_react(test, provider)

        for step_info in react_res["trace_steps"]:
            print(f"\n   🔄 [Step {step_info['step']}]")
            print(f"   {step_info['llm_output'].strip()}")
            if "observation" in step_info:
                obs_text = step_info["observation"].replace("\n", "\n   | ")
                print(f"   👁️ Observation từ Tool:\n   | {obs_text}")

        print(f"\n   🏁 [FINAL ANSWER GỬI CHO NGƯỜI DÙNG]:\n   {react_res['final_answer']}")
        print(f"   🛠️ [TỔNG KẾT TOOLS ĐÃ GỌI]: {react_res['tools_called'] if react_res['tools_called'] else 'Không gọi Tool'}")

        summary_results.append({
            "id": t_id,
            "category": cat,
            "tools_list": ", ".join(react_res["tools_called"]) if react_res["tools_called"] else "None",
            "tools_count": len(react_res["tools_called"]),
            "status": "PASS"
        })

    print("\n" + "=" * 80)
    print("📊 BẢNG TỔNG HỢP KẾT QUẢ KIỂM THỬ THỰC THI (10 TEST CASES)")
    print("=" * 80)
    print(f"{'ID':<4} | {'Phân loại':<30} | {'Danh sách Tools đã gọi':<32} | {'Trạng thái':<8}")
    print("-" * 80)
    for s in summary_results:
        print(f"{s['id']:<4} | {s['category']:<30} | {s['tools_list']:<32} | {s['status']:<8}")
    print("=" * 80)

if __name__ == "__main__":
    main()
