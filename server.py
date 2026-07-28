"""
🚀 FASTAPI BACKEND SERVER WITH SSE STREAMING (Server-Sent Events)
Cung cấp API Streaming ReAct Agent thời gian thực cho Single Page App (Web Frontend).
"""

import os
import sys
import json
import re
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

app = FastAPI(title="Coursera AI Agent SSE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static web files
WEB_DIR = os.path.join(BASE_DIR, "web")
if os.path.exists(WEB_DIR):
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(WEB_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Coursera AI Agent SSE Backend is Running."}

@app.get("/api/test-cases")
def get_test_cases():
    config_path = os.path.join(BASE_DIR, "config", "test_cases.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

@app.get("/api/stream")
async def stream_agent_events(question: str, provider_name: str = "mock"):
    """
    SSE Endpoint streaming từng bước ReAct Agent (Thought, Action, Observation, Final Answer)
    """
    provider = get_llm_provider(provider_name)

    async def event_generator():
        step = 0
        history = f"Câu hỏi của sinh viên: {question}\n"

        while step < MAX_ITERATIONS:
            step += 1
            prompt = REACT_SYSTEM_PROMPT + "\n" + history
            
            # Mô phỏng thời gian suy luận nhỏ cho hiệu ứng UI mượt
            await asyncio.sleep(0.3)
            response = provider.generate(prompt)

            if "Final Answer:" in response:
                final_ans = response.split("Final Answer:")[-1].strip()
                event_data = {
                    "type": "final_answer",
                    "step": step,
                    "content": final_ans
                }
                yield f"data: {json.dumps(event_data, ensure_ascii=False)}\n\n"
                break

            action_match = re.search(r"Action:\s*(\w+)\[(.*?)\]", response)
            if action_match:
                tool_name = action_match.group(1).strip()
                tool_arg = action_match.group(2).strip().strip("'\"")

                step_data = {
                    "type": "react_step",
                    "step": step,
                    "thought": response.split("Action:")[0].replace("Thought:", "").strip(),
                    "action": f"{tool_name}[{tool_arg}]",
                    "tool_name": tool_name,
                    "tool_arg": tool_arg
                }
                yield f"data: {json.dumps(step_data, ensure_ascii=False)}\n\n"

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
                    obs = f"LỖI: Tool '{tool_name}' không tồn tại."

                await asyncio.sleep(0.2)
                obs_data = {
                    "type": "observation",
                    "step": step,
                    "tool_name": tool_name,
                    "observation": obs
                }
                yield f"data: {json.dumps(obs_data, ensure_ascii=False)}\n\n"

                history += f"\n{response}\nObservation:\n{obs}\n"
            else:
                history += f"\n{response}\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
