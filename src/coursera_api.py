import os
import base64
import time
import json
import datetime
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

COURSERA_OAUTH_URL = "https://api.coursera.com/oauth2/client_credentials/token"
COURSERA_BASE_URL = os.getenv("COURSERA_BASE_URL", "https://api.coursera.org/api")

# Key & Secret từ .env
COURSERA_KEY = os.getenv("COURSERA_KEY") or os.getenv("COURSERA_APP_KEY")
COURSERA_SECRET = os.getenv("COURSERA_SECRET") or os.getenv("COURSERA_APP_SECRET")
TIMEOUT = int(os.getenv("COURSERA_TIMEOUT", 10))
TOKEN_FILE = os.path.join("config", "coursera_token.json")

class CourseraAPIClient:
    """Class quản lý kết nối Coursera API, tự động xin, lưu vết và gia hạn OAuth2 Token."""

    _access_token: Optional[str] = None
    _expires_at: float = 0.0

    @classmethod
    def load_cached_token(cls) -> Optional[str]:
        """Đọc token đã lưu từ file config/coursera_token.json nếu chưa hết hạn."""
        if os.path.exists(TOKEN_FILE):
            try:
                with open(TOKEN_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    expires_at = data.get("expires_at_timestamp", 0)
                    # Nếu token còn hạn ít nhất 60 giây
                    if time.time() < (expires_at - 60):
                        cls._access_token = data.get("access_token")
                        cls._expires_at = expires_at
                        return cls._access_token
            except Exception as e:
                print(f"⚠️ Lỗi đọc cache token: {e}")
        return None

    @classmethod
    def fetch_and_save_access_token(cls) -> Optional[Dict[str, Any]]:
        """
        Gửi cURL HTTP POST tới Coursera OAuth2 endpoint để lấy Access Token mới
        và ghi file config/coursera_token.json kèm thời gian hết hạn.
        """
        if not COURSERA_KEY or not COURSERA_SECRET:
            print("⚠️ Chưa cấu hình COURSERA_KEY và COURSERA_SECRET trong .env. Dùng Public APIs.")
            return None

        credentials = f"{COURSERA_KEY}:{COURSERA_SECRET}"
        encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}"
        }
        data = {"grant_type": "client_credentials"}

        try:
            response = requests.post(COURSERA_OAUTH_URL, headers=headers, data=data, timeout=TIMEOUT)
            response.raise_for_status()
            token_info = response.json()

            cls._access_token = token_info.get("access_token")
            issued_at = token_info.get("issued_at", int(time.time()))
            expires_in = token_info.get("expires_in", 1800)
            cls._expires_at = issued_at + expires_in

            # Định dạng ngày giờ đọc được
            issued_at_iso = datetime.datetime.fromtimestamp(issued_at).strftime("%Y-%m-%d %H:%M:%S")
            expires_at_iso = datetime.datetime.fromtimestamp(cls._expires_at).strftime("%Y-%m-%d %H:%M:%S")

            token_data = {
                "token_type": token_info.get("token_type", "Bearer"),
                "access_token": cls._access_token,
                "grant_type": token_info.get("grant_type"),
                "issued_at_timestamp": issued_at,
                "issued_at_time": issued_at_iso,
                "expires_in_seconds": expires_in,
                "expires_at_timestamp": cls._expires_at,
                "expires_at_time": expires_at_iso
            }

            os.makedirs("config", exist_ok=True)
            with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=2, ensure_ascii=False)

            print(f"🔑 Lấy và lưu Coursera Access Token thành công!")
            print(f"   - Token: {cls._access_token}")
            print(f"   - Thời gian cấp: {issued_at_iso}")
            print(f"   - Thời gian hết hạn: {expires_at_iso} (Thời lượng: {expires_in} giây)")
            return token_data

        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi lấy Access Token từ Coursera: {e}")
            return None

    @classmethod
    def get_access_token(cls) -> Optional[str]:
        """Lấy token (ưu tiên đọc từ cache nếu còn hạn, nếu hết hạn sẽ tự xin token mới)."""
        cached = cls.load_cached_token()
        if cached:
            return cached
        token_data = cls.fetch_and_save_access_token()
        return token_data.get("access_token") if token_data else None

    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """Tạo HTTP Headers chứa Authorization Bearer Token."""
        headers = {}
        token = cls.get_access_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @classmethod
    def search_courses(cls, query: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """Tra cứu danh sách khóa học trên Coursera Catalog API."""
        endpoint = f"{COURSERA_BASE_URL}/courses.v1"
        params = {"limit": 50, "fields": "description,photoUrl,certificates,workload"}
        try:
            response = requests.get(endpoint, headers=cls.get_headers(), params=params, timeout=TIMEOUT)
            response.raise_for_status()
            elements = response.json().get("elements", [])
            
            if query:
                q_lower = query.lower()
                matched = [c for c in elements if q_lower in c.get("name", "").lower() or q_lower in c.get("slug", "").lower()]
                return matched[:limit] if matched else elements[:limit]
            return elements[:limit]
        except requests.exceptions.RequestException as e:
            print(f"❌ Lỗi gọi Coursera Courses API: {e}")
            return []

if __name__ == "__main__":
    print("🔄 Đang thực hiện lấy và lưu Access Token...")
    token_info = CourseraAPIClient.fetch_and_save_access_token()
    if token_info:
        print("\n🔍 Đang test gọi Coursera Courses API với Bearer Token...")
        courses = CourseraAPIClient.search_courses(limit=3)
        print(f"✅ Đã gọi thành công ({len(courses)} khóa học):")
        for c in courses:
            print(f"   - {c.get('name')} (Slug: {c.get('slug')})")
