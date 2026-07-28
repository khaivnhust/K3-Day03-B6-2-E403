"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider mô phỏng chính xác chuỗi từng bước ReAct Agent cho bài test."""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        prompt_lower = prompt.lower()
        
        user_query = ""
        if "câu hỏi của sinh viên:" in prompt_lower:
            user_query = prompt_lower.split("câu hỏi của sinh viên:")[1].split("\n")[0]
        else:
            user_query = prompt_lower

        # TC 1: Coursera là gì
        if "coursera là gì" in user_query:
            return "Final Answer: Coursera là nền tảng học trực tuyến toàn cầu hợp tác với hơn 300+ trường đại học hàng đầu như Stanford, Yale và các tập đoàn công nghệ lớn như Google, IBM. Để đăng ký học, bạn chỉ cần tạo tài khoản và bấm nút 'Enroll'."
            
        # TC 3: Khóa học lẻ vs Specialization
        elif "khác biệt giữa một khóa học lẻ" in user_query:
            return "Final Answer: Khóa học lẻ (Single Course) tập trung vào một kỹ năng cụ thể trong 3-5 tuần. Chương trình Chuyên sâu (Specialization) gồm chuỗi 3-6 khóa học giúp làm chủ chuyên môn và nhận chứng chỉ."
            
        # TC 2: Generative AI for Everyone
        elif "generative ai for everyone" in user_query:
            if "observation:" not in prompt_lower:
                return "Thought: Cần tra cứu thông tin khóa học 'Generative AI for Everyone' trên Coursera Catalog.\nAction: search_coursera_catalog['Generative AI for Everyone']"
            else:
                return "Thought: Tôi đã nhận được thông tin chi tiết từ Coursera API.\nFinal Answer: Khóa học 'Generative AI for Everyone' của giảng viên Andrew Ng (DeepLearning.AI) giảng dạy về bản chất Generative AI, ứng dụng thực tế và cách triển khai AI trong công việc. Link: https://www.coursera.org/learn/generative-ai-for-everyone"

        # TC 4: Data Analytics Google
        elif "data analytics" in user_query and "google" in user_query:
            if "observation:" not in prompt_lower:
                return "Thought: Tra cứu danh sách khóa học Data Analytics do Google cung cấp.\nAction: search_coursera_catalog['Data Analytics Google']"
            else:
                return "Thought: Đã nhận được danh sách từ Coursera API.\nFinal Answer: Danh sách khóa học Data Analytics do Google giảng dạy trên Coursera bao gồm: Google Data Analytics Professional Certificate và các môn học về SQL, R, Data Visualization. Link: https://www.coursera.org/learn/google-data-analytics"

        # TC 5: Skill Gap Machine Learning Engineer
        elif "machine learning engineer" in user_query and "user_cs_9921" in user_query:
            obs_count = prompt_lower.count("observation:")
            if obs_count == 0:
                return "Thought: Cần tra cứu hồ sơ sinh viên USER_CS_9921 trước.\nAction: get_user_coursera_profile['USER_CS_9921']"
            elif obs_count == 1:
                return "Thought: Sinh viên có kỹ năng Python, SQL. Cần phân tích khoảng trống kỹ năng so với vị trí Machine Learning Engineer.\nAction: match_coursera_skill_gap['Python, SQL', 'Machine Learning Engineer']"
            elif obs_count == 2:
                return "Thought: Kỹ năng còn thiếu là Supervised ML và Deep Learning. Cần tìm các khóa học Coursera tương ứng.\nAction: search_coursera_catalog['Machine Learning Specialization']"
            else:
                return "Thought: Tôi đã có đủ thông tin từ tất cả 3 công cụ để đưa ra lộ trình hoàn chỉnh.\nFinal Answer: Để trở thành Machine Learning Engineer, sinh viên USER_CS_9921 cần học bổ sung Supervised Learning và Deep Learning qua khóa 'Machine Learning Specialization' bởi Andrew Ng trên Coursera. Link: https://www.coursera.org/specializations/machine-learning-specialization"

        # TC 6: Register Neural Networks and Deep Learning
        elif "neural networks and deep learning" in user_query and "user_cs_9921" in user_query:
            obs_count = prompt_lower.count("observation:")
            if obs_count == 0:
                return "Thought: Tra cứu profile sinh viên USER_CS_9921 để kiểm tra số giờ rảnh.\nAction: get_user_coursera_profile['USER_CS_9921']"
            elif obs_count == 1:
                return "Thought: Sinh viên có 5h/tuần rảnh. Tra cứu thông tin khóa học Neural Networks trên Coursera.\nAction: search_coursera_catalog['Neural Networks and Deep Learning']"
            elif obs_count == 2:
                return "Thought: Khóa học Neural Networks and Deep Learning phù hợp thời lượng. Tiến hành khởi tạo phiếu đăng ký.\nAction: register_coursera_enrollment['USER_CS_9921', 'neural-networks-deep-learning']"
            else:
                return "Thought: Đã đăng ký thành công.\nFinal Answer: Đã khởi tạo thành công phiếu đăng ký khóa học 'Neural Networks and Deep Learning' cho sinh viên USER_CS_9921. Link ghi danh chuẩn: https://www.coursera.org/learn/neural-networks-deep-learning?action=enroll"

        # TC 7: IBM Data Science
        elif "ibm data science" in user_query and "user_cs_9921" in user_query:
            obs_count = prompt_lower.count("observation:")
            if obs_count == 0:
                return "Thought: Tra cứu profile sinh viên USER_CS_9921.\nAction: get_user_coursera_profile['USER_CS_9921']"
            elif obs_count == 1:
                return "Thought: Tra cứu chi tiết Chuyên ngành IBM Data Science Specialization.\nAction: get_coursera_specialization_details['ibm-data-science']"
            else:
                return "Thought: Đã có thông tin chuyên ngành.\nFinal Answer: Chuyên ngành 'IBM Data Science Specialization' gồm 10 khóa học. Với quỹ thời gian 5h/tuần của sinh viên USER_CS_9921, bạn hoàn toàn đủ khả năng hoàn thành trong 3-4 tháng. Link: https://www.coursera.org/specializations/ibm-data-science"

        # TC 8: Web Automation Python Data Science
        elif "python for data science and ai" in user_query and "user_cs_9921" in user_query:
            obs_count = prompt_lower.count("observation:")
            if obs_count == 0:
                return "Thought: Tra cứu profile sinh viên USER_CS_9921.\nAction: get_user_coursera_profile['USER_CS_9921']"
            elif obs_count == 1:
                return "Thought: Phát hiện sinh viên chưa học khóa này. Kích hoạt trình duyệt web thật mở trang đăng ký Coursera.\nAction: open_coursera_enrollment_page['python-for-applied-data-science-ai']"
            else:
                return "Thought: Trình duyệt web đã được bật thành công.\nFinal Answer: Trình duyệt web trên máy tính của bạn đã được tự động bật và mở thẳng tới trang đăng ký Coursera thực tế của khóa học tại URL: https://www.coursera.org/learn/python-for-applied-data-science-ai?action=enroll"

        # TC 9: Klingon Quantum 500h
        elif "klingon" in user_query or "500h/tuần" in user_query:
            if "observation:" not in prompt_lower:
                return "Thought: Tìm kiếm khóa học Quantum Computing Klingon trên Coursera.\nAction: search_coursera_catalog['Quantum Computing Klingon']"
            else:
                return "Thought: Kết quả rỗng và thông số 500h/tuần là vô lý.\nFinal Answer: Không tìm thấy khóa học 'Quantum Computing ngôn ngữ Klingon' trên Coursera. Ngoài ra thời lượng 500h/tuần vượt quá số giờ tối đa của một tuần (168h), xin vui lòng chọn từ khóa hợp lệ!"

        # TC 10: USER_UNKNOWN_9999
        elif "user_unknown_9999" in user_query:
            if "observation:" not in prompt_lower:
                return "Thought: Tra cứu profile mã sinh viên USER_UNKNOWN_9999.\nAction: get_user_coursera_profile['USER_UNKNOWN_9999']"
            else:
                return "Thought: Phát hiện mã sinh viên không tồn tại trong hệ thống.\nFinal Answer: LỖI: Không thể thực hiện đăng ký do sinh viên ID 'USER_UNKNOWN_9999' không tồn tại trong hệ thống quản lý."

        return "Thought: Tôi cần hỗ trợ người dùng.\nFinal Answer: Xin chào! Tôi là Trợ lý AI Coursera, bạn cần tôi hỗ trợ tìm kiếm hay đăng ký khóa học nào?"


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()
