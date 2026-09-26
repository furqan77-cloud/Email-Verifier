import json
import os
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameters
        parsed_path = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_path.query)
        email = query_params.get('email', [None])[0]

        if not email:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Email parameter is required'}).encode('utf-8'))
            return

        # Fetch API key from environment
        api_key = os.getenv('ABSTRACT_API_KEY')
        if not api_key:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'API key not configured on server'}).encode('utf-8'))
            return

        # Call Abstract API
        url = f"https://emailvalidation.abstractapi.com/v1/?api_key={api_key}&email={urllib.parse.quote(email)}"
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                api_data = json.loads(response.read().decode('utf-8'))

            # Extract fields expected by index.html
            res_payload = {
                'email': api_data.get('email', email),
                'valid_syntax': api_data.get('is_valid_format', {}).get('value', False),
                'is_disposable': api_data.get('is_disposable_email', {}).get('value', False),
                'has_mx_records': api_data.get('is_mx_found', {}).get('value', False),
                'quality_score': float(api_data.get('quality_score', 0)),
                'overall_status': api_data.get('deliverability', 'UNKNOWN')
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(res_payload).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))