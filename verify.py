import os
import json
import requests
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Parse parameters (?email=user@domain.com)
        parsed_url = urlparse(self.path)
        params = parse_qs(parsed_url.query)
        email = params.get('email', [None])[0]

        # 2. Configure HTTP response headers
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        if not email:
            self.wfile.write(json.dumps({"error": "Missing email parameter"}).encode())
            return

        # 3. Read API Key from Vercel environment variables
        api_key = os.environ.get("ABSTRACT_API_KEY")
        if not api_key:
            self.wfile.write(json.dumps({"error": "API Key is missing on server"}).encode())
            return

        # 4. Request validation from Abstract API
        try:
            url = f"https://emailvalidation.abstractapi.com/v1/?api_key={api_key}&email={email}"
            api_res = requests.get(url, timeout=10)
            data = api_res.json()

            # Parse fields from API response payload
            deliverability = data.get("email_deliverability", {})
            quality = data.get("email_quality", {})

            status = deliverability.get("status", "undeliverable")
            is_format_valid = deliverability.get("is_format_valid", False)
            is_mx_valid = deliverability.get("is_mx_valid", False)
            is_disposable = quality.get("is_disposable", False)
            quality_score = quality.get("score", 0.0)

            overall_status = "Invalid"
            if status == "deliverable" and not is_disposable:
                overall_status = "Valid"
            elif is_mx_valid and is_format_valid:
                overall_status = "Risky"

            result = {
                "email": email,
                "valid_syntax": is_format_valid,
                "is_disposable": is_disposable,
                "has_mx_records": is_mx_valid,
                "quality_score": float(quality_score),
                "deliverability": status,
                "overall_status": overall_status
            }
            self.wfile.write(json.dumps(result).encode())

        except Exception as e:
            self.wfile.write(json.dumps({"error": f"Verification failed: {str(e)}"}).encode())