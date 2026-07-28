"""
🎓 STREAMLIT DEMO — Trợ lý Tư vấn Khóa học Coursera (Lab 3: Chatbot vs ReAct Agent)
Thể hiện đầy đủ 4 CẤP ĐỘ AI HỘI THOẠI trên cùng một bối cảnh tư vấn khóa học.

Chạy:  streamlit run streamlit_app.py
"""

import json
import os
import sys
import time

import streamlit as st
from dotenv import load_dotenv

# --- Đưa src/ và src/ai_levels/ vào path để import module dự án ---
_ROOT = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_ROOT, "src")
for p in (_SRC, os.path.join(_SRC, "ai_levels")):
    if p not in sys.path:
        sys.path.append(p)

load_dotenv()

from providers import get_llm_provider  # noqa: E402
from prompts import (  # noqa: E402
    MAX_ITERATIONS,
    MAX_IDENTICAL_ACTIONS,
    MAX_RECOMMENDED_COURSES,
)
from tools import AVAILABLE_TOOLS  # noqa: E402
from coursera_levels import (  # noqa: E402
    level1_rule_based,
    level2_llm_chatbot,
    level3_react_agent,
    level4_autonomous_agent,
)

TOKEN_FILE = os.path.join(_ROOT, "config", "coursera_token.json")

st.set_page_config(page_title="CourseMate — Coursera Advisor (4 AI Levels)",
                   page_icon="🎓", layout="wide")


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_test_cases():
    path = os.path.join(_ROOT, "config", "test_cases.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def coursera_token_status():
    if not os.path.exists(TOKEN_FILE):
        return "🟡 Public API (không token)"
    try:
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        if time.time() < d.get("expires_at_timestamp", 0) - 60:
            return "🟢 Authenticated (token còn hạn)"
        return "🟠 Token hết hạn → fallback Public API"
    except Exception:
        return "🟡 Public API (không đọc được token)"


def build_provider(name, model, api_key):
    """Ghi cấu hình vào biến môi trường rồi tạo provider."""
    os.environ["LLM_PROVIDER"] = name
    if model:
        os.environ["LLM_MODEL"] = model
    key_env = {
        "gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY", "openrouter": "OPENROUTER_API_KEY",
    }.get(name)
    if key_env and api_key:
        os.environ[key_env] = api_key
    return get_llm_provider(name)


def render_step(s):
    """Hiển thị 1 bước ReAct."""
    if s["thought"]:
        st.markdown(f"🧠 **Thought:** {s['thought']}")
    if s["action"]:
        st.markdown(f"🛠️ **Action:** `{s['action']}`")
    if s["observation"] is not None:
        st.info(f"👁️ **Observation:** {s['observation']}")
    if s["final_answer"] is not None:
        st.success(f"🏁 **Final Answer:** {s['final_answer']}")
    if s["guardrail"] is not None:
        st.warning(f"🛡️ **GUARDRAIL:** {s['guardrail']}")


# ----------------------------------------------------------------------------
# Sidebar — cấu hình
# ----------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Cấu hình")
    provider_name = st.selectbox(
        "LLM Provider",
        ["mock", "gemini", "openai", "anthropic", "openrouter"],
        help="Chọn 'mock' để demo offline không cần API key.",
    )
    model_name = st.text_input("Model (tùy chọn)", value="",
                               placeholder="để trống = model mặc định")
    api_key = ""
    if provider_name != "mock":
        api_key = st.text_input(f"{provider_name.upper()} API Key", type="password")

    st.divider()
    st.subheader("🎓 Coursera API")
    st.write(coursera_token_status())

    st.divider()
    st.subheader("🛡️ Guardrails")
    st.write(f"- MAX_ITERATIONS = `{MAX_ITERATIONS}`")
    st.write(f"- MAX_IDENTICAL_ACTIONS = `{MAX_IDENTICAL_ACTIONS}`")
    st.write(f"- MAX_RECOMMENDED_COURSES = `{MAX_RECOMMENDED_COURSES}`")

    st.divider()
    st.subheader("🛠️ Tools đã đăng ký")
    for name in AVAILABLE_TOOLS:
        st.write(f"- `{name}`")

provider = build_provider(provider_name, model_name, api_key)

# ----------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------
st.title("🎓 CourseMate — Trợ lý Tư vấn Khóa học Coursera")
st.caption(
    f"Lab 3: Chatbot vs ReAct Agent · Provider: **{provider.__class__.__name__}** "
    f"(model: {getattr(provider, 'model_name', 'mock')})"
)

LEVELS = {
    "Cấp 1 · Rule-Based": "🤖",
    "Cấp 2 · LLM Chatbot": "💬",
    "Cấp 3 · ReAct Agent": "🧠",
    "Cấp 4 · Autonomous": "🚀",
    "So sánh 4 cấp": "📊",
}
tabs = st.tabs([f"{v} {k}" for k, v in LEVELS.items()])
tests = load_test_cases()
examples = [t["question"] for t in tests if "question" in t]

# ============================================================================
# TAB 1 — RULE-BASED
# ============================================================================
with tabs[0]:
    st.subheader("🤖 Cấp 1 — Rule-Based Bot (if/else, không LLM)")
    st.caption("Khớp từ khóa cố định. Ngoài tập luật → không trả lời được.")
    q1 = st.text_input("Câu hỏi", value="Coursera là gì?", key="q1")
    if st.button("Chạy Cấp 1", key="b1"):
        st.markdown(f"**Bot:** {level1_rule_based(q1)}")
    with st.expander("Gợi ý câu hợp/ngoài luật"):
        st.write("Trong luật: *Coursera là gì?*, *học phí*, *chứng chỉ*, *liên hệ*")
        st.write("Ngoài luật: *Tìm khóa ML cho người mới* → Cấp 1 bó tay, cần Cấp 3.")

# ============================================================================
# TAB 2 — LLM CHATBOT
# ============================================================================
with tabs[1]:
    st.subheader("💬 Cấp 2 — LLM Chatbot (baseline, KHÔNG có tool)")
    st.caption("Sinh text tự nhiên nhưng không tra cứu được dữ liệu thật → dễ bịa số liệu.")
    q2 = st.text_area("Câu hỏi", value="Sự khác biệt giữa Course và Specialization trên Coursera?", key="q2")
    if st.button("Chạy Cấp 2", key="b2"):
        with st.spinner("Đang gọi LLM..."):
            st.markdown(f"**Chatbot:** {level2_llm_chatbot(q2, provider)}")

# ============================================================================
# TAB 3 — REACT AGENT
# ============================================================================
with tabs[2]:
    st.subheader("🧠 Cấp 3 — ReAct Agent (Thought → Action → Observation)")
    st.caption("Suy luận + gọi tool + Coursera API thật + Guardrails.")

    ex = st.selectbox("Chọn test case mẫu (hoặc tự nhập bên dưới)",
                      ["— tự nhập —"] + examples, key="ex3")
    default_q3 = ex if ex != "— tự nhập —" else \
        "Tôi muốn thành Machine Learning Engineer (user_id: 'USER_CS_9921'), phân tích kỹ năng thiếu và tìm khóa Coursera phù hợp."
    q3 = st.text_area("Câu hỏi", value=default_q3, key="q3")

    if st.button("Chạy ReAct Agent", key="b3", type="primary"):
        with st.spinner("Agent đang suy luận..."):
            steps = level3_react_agent(q3, provider)
        for s in steps:
            with st.container(border=True):
                st.markdown(f"**🔄 Step {s['step']}/{MAX_ITERATIONS}**")
                render_step(s)

# ============================================================================
# TAB 4 — AUTONOMOUS
# ============================================================================
with tabs[3]:
    st.subheader("🚀 Cấp 4 — Autonomous Agent (Planning + Memory)")
    st.caption("Tự rã mục tiêu phức tạp thành nhiều bước con, lưu Memory, dùng tool thật.")
    goal = st.text_area(
        "Mục tiêu phức tạp",
        value="Tôi là USER_CS_9921, muốn trở thành Machine Learning Engineer. Hãy lập lộ trình học Coursera cho tôi.",
        key="q4",
    )
    enroll = st.checkbox("Tự động đăng ký khóa đầu tiên", value=True, key="enr4")
    if st.button("Chạy Autonomous Agent", key="b4", type="primary"):
        with st.spinner("Agent đang lập kế hoạch & thực thi..."):
            res = level4_autonomous_agent(goal, enroll=enroll)

        c1, c2 = st.columns(2)
        c1.metric("Học viên", res["user_id"])
        c2.metric("Mục tiêu", res["target_role"])

        st.markdown("#### 📋 Planning — kế hoạch tự sinh")
        for p in res["plan"]:
            st.markdown(f"- {p}")

        st.markdown("#### 💾 Memory — lưu vết thực thi tool thật")
        st.dataframe(
            [{"Step": m["step"], "Action": m["action"],
              "Result": (m["result"][:120] + "…") if len(m["result"]) > 120 else m["result"]}
             for m in res["memory"]],
            width="stretch",
        )

        st.markdown("#### 🏁 Kết quả tổng hợp")
        st.success(res["final_answer"])

# ============================================================================
# TAB 5 — SO SÁNH
# ============================================================================
with tabs[4]:
    st.subheader("📊 So sánh 4 cấp độ trên cùng một câu hỏi")
    st.caption("Thấy rõ vì sao bài toán tư vấn khóa học CẦN tới ReAct Agent (Cấp 3+).")
    st.table([
        {"Cấp": "1 · Rule-Based", "LLM": "❌", "Tool": "❌", "Dữ liệu thật": "❌",
         "Điểm mạnh": "Nhanh, rẻ", "Điểm yếu": "Cứng nhắc, ngoài luật là bó tay"},
        {"Cấp": "2 · LLM Chatbot", "LLM": "✅", "Tool": "❌", "Dữ liệu thật": "❌",
         "Điểm mạnh": "Nói tự nhiên", "Điểm yếu": "Không tra cứu được → dễ bịa"},
        {"Cấp": "3 · ReAct Agent", "LLM": "✅", "Tool": "✅", "Dữ liệu thật": "✅",
         "Điểm mạnh": "Suy luận + tool + Coursera API", "Điểm yếu": "Chi phí gọi LLM cao hơn"},
        {"Cấp": "4 · Autonomous", "LLM": "✅", "Tool": "✅", "Dữ liệu thật": "✅",
         "Điểm mạnh": "Tự lập kế hoạch + Memory", "Điểm yếu": "Phức tạp, cần kiểm soát chặt"},
    ])
    st.info("Câu hỏi kiến thức chung → đi Chatbot path (Cấp 1–2). "
            "Câu cần tra cứu/đăng ký khóa học → đi ReAct/Autonomous path (Cấp 3–4). "
            "Xem `docs/hybrid_flowchart.mermaid`.")
