"""
🧩 AGENT CORE — Lõi ReAct dùng chung cho CLI (app.py) và Streamlit demo.

Tách phần parse + dispatch + guardrails ra đây để mọi giao diện dùng chung
một nguồn logic duy nhất, trả về các bước (steps) có cấu trúc để render.
"""

import re

from tools import AVAILABLE_TOOLS
from prompts import REACT_SYSTEM_PROMPT, MAX_ITERATIONS, MAX_IDENTICAL_ACTIONS

ACTION_RE = re.compile(r"Action:\s*([A-Za-z_]\w*)\s*\[(.*?)\]", re.DOTALL)
FINAL_RE = re.compile(r"Final Answer:\s*(.+)", re.DOTALL)
THOUGHT_RE = re.compile(r"Thought:\s*(.+)")


def parse_args(raw_args: str):
    """Tách 'a, b' -> ['a', 'b'], loại bỏ dấu nháy/khoảng trắng."""
    if not raw_args.strip():
        return []
    parts = [p.strip().strip("'\"") for p in raw_args.split(",")]
    return [p for p in parts if p != ""]


def execute_tool(tool_name: str, args) -> str:
    """Gọi tool an toàn — mọi lỗi thành chuỗi Observation, không làm sập Agent."""
    tool_fn = AVAILABLE_TOOLS.get(tool_name)
    if tool_fn is None:
        return f"LỖI: Không tồn tại công cụ '{tool_name}'."
    try:
        return tool_fn(*args)
    except TypeError as e:
        return f"LỖI: Sai số lượng/kiểu tham số cho '{tool_name}' ({e})."
    except Exception as e:  # noqa: BLE001 - tool không được phép làm sập Agent
        return f"LỖI: Công cụ '{tool_name}' gặp sự cố ({e})."


def react_agent_steps(
    user_query: str,
    provider,
    max_iterations: int = MAX_ITERATIONS,
    max_identical: int = MAX_IDENTICAL_ACTIONS,
):
    """
    Chạy vòng lặp ReAct và TRẢ VỀ danh sách các bước có cấu trúc.

    Mỗi step là dict:
      {step, thought, action, observation, final_answer, guardrail}
    (các khóa không dùng sẽ là None). Bước cuối chứa final_answer hoặc guardrail.
    """
    steps = []
    scratchpad = f"Câu hỏi của người dùng: {user_query}\n"
    action_counts: dict[str, int] = {}

    for step in range(1, max_iterations + 1):
        llm_out = provider.generate(scratchpad, system_prompt=REACT_SYSTEM_PROMPT)

        thought_m = THOUGHT_RE.search(llm_out)
        thought = thought_m.group(1).strip().splitlines()[0] if thought_m else ""

        final = FINAL_RE.search(llm_out)
        action = ACTION_RE.search(llm_out)

        # Ưu tiên Final Answer nếu xuất hiện trước Action
        if final and (not action or final.start() < action.start()):
            steps.append({"step": step, "thought": thought, "action": None,
                          "observation": None, "final_answer": final.group(1).strip(),
                          "guardrail": None})
            return steps

        if not action:
            steps.append({"step": step, "thought": thought, "action": None,
                          "observation": None, "final_answer": llm_out.strip(),
                          "guardrail": None})
            return steps

        tool_name = action.group(1)
        args = parse_args(action.group(2))
        action_key = f"{tool_name}[{action.group(2).strip()}]"

        # GUARDRAIL: chặn lặp lại y hệt một Action
        if action_counts.get(action_key, 0) >= max_identical:
            steps.append({"step": step, "thought": thought, "action": action_key,
                          "observation": None, "final_answer": None,
                          "guardrail": f"Action '{action_key}' bị lặp quá {max_identical} lần → ngắt."})
            return steps
        action_counts[action_key] = action_counts.get(action_key, 0) + 1

        obs = execute_tool(tool_name, args)
        steps.append({"step": step, "thought": thought, "action": action_key,
                      "observation": obs, "final_answer": None, "guardrail": None})

        scratchpad += f"Thought: {thought}\nAction: {action_key}\nObservation: {obs}\n"

    steps.append({"step": max_iterations, "thought": "", "action": None,
                  "observation": None, "final_answer": None,
                  "guardrail": f"Đã đạt giới hạn {max_iterations} bước → ngắt lặp an toàn."})
    return steps
