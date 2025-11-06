import requests
from django.conf import settings

class BytescaleClient:
    BASE_URL = f"https://api.bytescale.com/v2/accounts/{settings.BYTESCALE_ACCOUNT_ID}/uploads/form_data"
    HEADERS = {"Authorization": f"Bearer {settings.BYTESCALE_API_KEY}"}
    FALLBACK_URL = "https://images.unsplash.com/photo-1527847263472-aa5338d178b8?w=500&auto=format&fit=crop&q=60&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8M3x8ZmFybWVyfGVufDB8fDB8fHww"

    @classmethod
    def upload_file(cls, file_name: str, file_content: bytes, content_type: str) -> str:
        """
        Uploads a file to Bytescale. If the upload fails for any reason,
        returns a default fallback image URL.
        """
        try:
            files = {'file': (file_name, file_content, content_type)}
            resp = requests.post(cls.BASE_URL, headers=cls.HEADERS, files=files, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            if not data or "files" not in data or not data["files"]:
                raise RuntimeError("Bytescale response missing 'files'")
            url = data["files"][0].get("fileUrl")
            if not url:
                raise RuntimeError("Bytescale missing fileUrl")
            return url
        except Exception as e:
            print(f"[Bytescale Upload Failed] {str(e)} — using fallback URL")
            return cls.FALLBACK_URL
