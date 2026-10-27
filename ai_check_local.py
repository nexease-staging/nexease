import os, json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from apps.saas.ai import SCHEMA, parse_response

key = os.getenv("OPENAI_API_KEY", "").strip()
print("API key configured:", bool(key))
print("Model:", os.getenv("OPENAI_MODEL", "gpt-5.4-mini"))

body = {
    "model": os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
    "store": False,
    "max_output_tokens": 5000,
    "reasoning": {"effort": "none"},
    "input": "Prepare an expense: paid INR 500 for petrol by UPI. Leave unknown fields empty.",
    "text": {"format": {
        "type": "json_schema", "name": "nexease_entry",
        "strict": True, "schema": SCHEMA
    }}
}

if key:
    req = Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + key}
    )
    try:
        with urlopen(req, timeout=75) as response:
            result = json.load(response)
        print("Provider status:", result.get("status"))
        parsed = parse_response(result)
        print("Extraction successful:", parsed.get("kind"))
    except HTTPError as e:
        print("HTTP status:", e.code)
        try:
            error = json.loads(e.read()).get("error", {})
            print("Error code:", error.get("code"))
            print("Error parameter:", error.get("param"))
        except Exception:
            print("Provider returned a non-JSON error.")
    except URLError:
        print("Network/TLS connection failed.")
    except Exception as e:
        print("Error type:", type(e).__name__)
        print("Detail:", str(e).replace(key, "[REDACTED]"))
