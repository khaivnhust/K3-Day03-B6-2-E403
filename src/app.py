"""
🚀 CORE AGENT APP (Coursera AI Recommendation Agent)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
import re
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ tools, prompts & providers
from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) thực thi dynamic Coursera Tools.
    """
    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    step = 0
    history = f"Câu hỏi của sinh viên: {user_query}\n"
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        prompt = REACT_SYSTEM_PROMPT + "\n" + history
        response = provider.generate(prompt)
        print(f"{response}")
        
        # Bắt Final Answer
        if "Final Answer:" in response:
            break
            
        # Parse Action: tool_name[param]
        action_match = re.search(r"Action:\s*(\w+)\[(.*?)\]", response)
        if action_match:
            tool_name = action_match.group(1).strip()
            tool_arg = action_match.group(2).strip().strip("'\"")
            
            if tool_name in AVAILABLE_TOOLS:
                print(f"🛠️ [EXECUTE TOOL] Calling {tool_name} with arg: '{tool_arg}'")
                try:
                    # Đưa vào đa tham số nếu phân cách bằng dấu phẩy
                    if "," in tool_arg and tool_name == "match_coursera_skill_gap":
                        args = [a.strip() for a in tool_arg.split(",", 1)]
                        obs = AVAILABLE_TOOLS[tool_name](args[0], args[1])
                    elif "," in tool_arg and tool_name == "register_coursera_enrollment":
                        args = [a.strip() for a in tool_arg.split(",", 1)]
                        obs = AVAILABLE_TOOLS[tool_name](args[0], args[1])
                    else:
                        obs = AVAILABLE_TOOLS[tool_name](tool_arg)
                except Exception as e:
                    obs = f"LỖI THỰC THI TOOL {tool_name}: {str(e)}"
                    
                print(f"👁️ Observation:\n{obs}")
                history += f"\n{response}\nObservation:\n{obs}\n"
            else:
                obs = f"LỖI: Tool '{tool_name}' không tồn tại trong hệ thống."
                print(f"👁️ Observation:\n{obs}")
                history += f"\n{response}\nObservation:\n{obs}\n"
        else:
            history += f"\n{response}\n"
            
    if step >= MAX_ITERATIONS:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")


if __name__ == "__main__":
    print("==================================================")
    print("🎓 COURSERA AI RECOMMENDATION AGENT (LAB 3)")
    print("==================================================")
    
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # Chạy thử câu test case số 5 (Multi-step)
    sample_query = tests[4]["question"]
    
    print("--- DEMO 1: CHẠY TRÊN CHATBOT BASELINE ---")
    run_baseline_chatbot(sample_query, provider)
    
    print("\n--- DEMO 2: CHẠY TRÊN REACT AGENT ---")
    run_react_agent(sample_query, provider)
