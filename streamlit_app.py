"""
🎓 COURSERA AI RECOMMENDATION AGENT - STREAMLIT WEB APP
Giao diện Web tương tác trực quan thời gian thực (Real-time ReAct Streaming)
Tùy chỉnh CSS High-Contrast tương phản cao, chữ sáng rõ ràng 100%.
Tự động đánh chặn và sửa lỗi URL bị ảo giác từ tất cả các LLM (GPT-4o, Gemini, Claude).
"""

import os
import sys
import time
import json
import re
import webbrowser
import streamlit as st

# Thêm thư mục root dự án vào sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
for _path in [BASE_DIR, SRC_DIR]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from tools import AVAILABLE_TOOLS
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

try:
    from coursera_api import CourseraAPIClient, TOKEN_FILE, fix_response_urls
except ImportError:
    from src.coursera_api import CourseraAPIClient, TOKEN_FILE, fix_response_urls

# Cấu hình trang Streamlit
st.set_page_config(
    page_title="Coursera AI Agent - Consultation & Enrollment",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS High-Contrast tương phản cao (Ép toàn bộ chữ màu sáng rõ nét 100%)
st.markdown("""
<style>
    /* 1. Theme màu nền chính của App */
    .stApp {
        background: linear-gradient(135deg, #0b0f19 0%, #111827 50%, #0b0f19 100%) !important;
        color: #ffffff !important;
    }
    
    /* 2. Ép tất cả các văn bản, nhãn, thẻ tiêu đề luôn có màu sáng nổi bật */
    p, span, label, h1, h2, h3, h4, h5, h6, div, li, small {
        color: #f8fafc !important;
    }

    /* 3. Header Container */
    .header-box {
        background: rgba(30, 41, 59, 0.95) !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
    }
    
    .header-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #38bdf8 !important;
        margin: 0 0 10px 0;
    }

    .header-subtitle {
        color: #cbd5e1 !important;
        font-size: 1.05rem;
        margin: 0;
    }

    /* 4. Khung Chat Message Bubbles */
    [data-testid="stChatMessage"] {
        background-color: #1e293b !important;
        border: 1px solid #475569 !important;
        border-radius: 14px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
    }

    [data-testid="stChatMessageContent"] * {
        color: #ffffff !important;
    }

    /* 5. Style Tabs (Phase 1 vs Phase 2) */
    button[data-baseweb="tab"] {
        color: #94a3b8 !important;
        font-weight: 600 !important;
        font-size: 1.05rem !important;
        background-color: transparent !important;
    }
    button[aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom: 3px solid #38bdf8 !important;
    }

    /* 6. Status Widget & Expanders (Vòng lặp ReAct Step) */
    [data-testid="stStatusWidget"] {
        background-color: #0f172a !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 10px !important;
    }
    [data-testid="stStatusWidget"] * {
        color: #f8fafc !important;
    }

    /* Info Box Callout */
    .stAlert {
        background-color: #1e293b !important;
        border: 1px solid #0284c7 !important;
        border-radius: 10px !important;
    }
    .stAlert * {
        color: #e0f2fe !important;
    }

    /* 7. Khối hiển thị Code Observation */
    code, pre, .stCodeBlock {
        background-color: #020617 !important;
        color: #4ade80 !important;
        font-weight: 500 !important;
        border-radius: 8px !important;
    }

    /* 8. Nút bấm Sidebar */
    .stButton > button {
        background-color: #1e293b !important;
        color: #f8fafc !important;
        border: 1px solid #475569 !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #0284c7 !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)


def load_test_cases():
    config_path = os.path.join(BASE_DIR, "config", "test_cases.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# HEADER HỆ THỐNG
st.markdown("""
<div class="header-box">
    <h1 class="header-title">🎓 Coursera AI Recommendation Agent</h1>
    <p class="header-subtitle">
        Hệ thống AI ReAct Agent thông minh tư vấn lộ trình học tập, phân tích khoảng trống kỹ năng và tự động hóa ghi danh khóa học trên Coursera.
    </p>
</div>
""", unsafe_allow_html=True)


# SIDEBAR ĐIỀU KHIỂN
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/9/97/Coursera-Logo_600x600.svg", width=130)
    st.markdown("<h2 style='color:#38bdf8!important;'>⚙️ Control Panel</h2>", unsafe_allow_html=True)
    
    st.markdown("<h4 style='color:#f8fafc!important;'>🔌 Multi-Provider LLM</h4>", unsafe_allow_html=True)
    provider_option = st.selectbox(
        "Chọn Nhà cung cấp AI:",
        ["Auto-Detect / Offline Mock", "Google Gemini API", "OpenAI GPT-4o"],
        index=0
    )
    
    provider_key = "mock"
    if "Gemini" in provider_option:
        provider_key = "gemini"
    elif "OpenAI" in provider_option:
        provider_key = "openai"
        
    provider = get_llm_provider(provider_key)
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    
    if "Mock" in provider.__class__.__name__:
        st.info("💡 **Chế độ:** Offline Mock Mode (Miễn phí, 0.01s response)")
    else:
        st.success(f"🟢 **Chế độ:** {provider.__class__.__name__}\nModel: `{model_name}`")
        
    st.markdown("---")
    
    st.markdown("<h4 style='color:#f8fafc!important;'>🔑 Coursera OAuth Token</h4>", unsafe_allow_html=True)
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                t_data = json.load(f)
                exp_time = t_data.get("expires_at_time", "N/A")
                st.markdown(f"<span style='color:#4ade80!important;'>✅ Token Active (Hết hạn: {exp_time})</span>", unsafe_allow_html=True)
        except Exception:
            st.caption("⚠️ Chưa có Token file.")
    else:
        st.caption("⚠️ Sử dụng Public API Access.")
        
    st.markdown("---")
    
    st.markdown("<h4 style='color:#f8fafc!important;'>🧪 1-Click Test Cases</h4>", unsafe_allow_html=True)
    test_cases = load_test_cases()
    
    selected_tc_question = None
    for tc in test_cases:
        t_id = tc["id"]
        q_short = tc["question"][:32] + "..."
        
        btn_label = f"#{t_id}: {q_short}"
        if st.button(btn_label, key=f"tc_btn_{t_id}", use_container_width=True):
            selected_tc_question = tc["question"]


# SESSION STATE CHO LỊCH SỬ CHAT
if "messages" not in st.session_state:
    st.session_state.messages = []

if selected_tc_question:
    st.session_state.messages.append({"role": "user", "content": selected_tc_question})

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "tools_called" in msg and msg["tools_called"]:
            st.markdown(f"<span style='color:#94a3b8!important; font-size:0.85rem;'>🛠️ Tools đã gọi: <code>{', '.join(msg['tools_called'])}</code></span>", unsafe_allow_html=True)


# NHẬP CÂU HỎI TỪ NGƯỜI DÙNG
user_input = st.chat_input("Nhập câu hỏi tư vấn hoặc đăng ký khóa học Coursera...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

# XỬ LÝ VÀ CHẠY REACT AGENT STREAMING
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
    latest_query = st.session_state.messages[-1]["content"]
    
    with st.chat_message("assistant"):
        st.markdown("<h3 style='color:#38bdf8!important;'>🤖 Coursera AI Agent Processing...</h3>", unsafe_allow_html=True)
        
        tab_react, tab_baseline = st.tabs(["🤖 Phase 2: ReAct Agent (Có Tools)", "💬 Phase 1: Baseline Chatbot (Không Tools)"])
        
        # TAB 1: REACT AGENT VỚI SUY LUẬN TỪNG BƯỚC
        with tab_react:
            step = 0
            history = f"Câu hỏi của sinh viên: {latest_query}\n"
            tools_called = []
            final_ans = ""
            
            status_box = st.status("🧠 Agent đang phân tích yêu cầu...", expanded=True)
            
            while step < MAX_ITERATIONS:
                step += 1
                prompt = REACT_SYSTEM_PROMPT + "\n" + history
                
                with status_box:
                    st.markdown(f"<h5 style='color:#fde047!important;'>🔄 Vòng lặp ReAct Step {step}/{MAX_ITERATIONS}...</h5>", unsafe_allow_html=True)
                    response = provider.generate(prompt)
                    
                    if "Final Answer:" in response:
                        final_ans = response.split("Final Answer:")[-1].strip()
                        # Tự động đánh chặn và sửa lỗi URL bị ảo giác bởi LLM
                        final_ans = fix_response_urls(final_ans)
                        st.markdown("<span style='color:#4ade80!important; font-weight:bold;'>✅ Đã hoàn thành suy luận!</span>", unsafe_allow_html=True)
                        break
                        
                    action_match = re.search(r"Action:\s*(\w+)\[(.*?)\]", response)
                    if action_match:
                        tool_name = action_match.group(1).strip()
                        tool_arg = action_match.group(2).strip().strip("'\"")
                        tools_called.append(tool_name)
                        
                        st.info(f"🛠️ **Gọi Tool:** `{tool_name}` | **Tham số:** `{tool_arg}`")
                        
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
                            
                        with st.expander(f"👁️ Observation từ Tool `{tool_name}`"):
                            st.code(obs, language="markdown")
                            
                        history += f"\n{response}\nObservation:\n{obs}\n"
                    else:
                        history += f"\n{response}\n"
                        
            status_box.update(label="🎉 Xử lý hoàn tất!", state="complete", expanded=False)
            
            st.markdown("<h4 style='color:#38bdf8!important;'>🏁 Trả lời người dùng:</h4>", unsafe_allow_html=True)
            st.markdown(final_ans if final_ans else "Không tìm thấy câu trả lời phù hợp.")
            
            # Nếu câu trả lời có chứa link Coursera, tạo nút Web Automation 1-click
            urls = re.findall(r'https?://[^\s]+', final_ans)
            if urls:
                target_url = urls[0].rstrip(').')
                st.markdown(f"<br><a href='{target_url}' target='_blank' style='background:linear-gradient(135deg, #0284c7, #4f46e5); color:#ffffff!important; padding:12px 24px; border-radius:10px; text-decoration:none; font-weight:bold; display:inline-block;'>🚀 Mở trang đăng ký Coursera thật trong Tab mới ➔</a>", unsafe_allow_html=True)

        # TAB 2: BASELINE CHATBOT KHÔNG TOOLS
        with tab_baseline:
            st.caption("Mô hình Chatbot truyền thống chỉ trả lời bằng tri thức nền (không tra cứu API Coursera hay Profile).")
            baseline_resp = provider.generate(latest_query, system_prompt=CHATBOT_BASELINE_PROMPT)
            # Tự động đánh chặn và sửa lỗi URL cho baseline chatbot
            baseline_resp = fix_response_urls(baseline_resp)
            st.write(baseline_resp)

    # Lưu phản hồi vào Session State
    st.session_state.messages.append({
        "role": "assistant",
        "content": final_ans,
        "tools_called": tools_called
    })
