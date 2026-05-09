#!/usr/bin/env python3
"""Server som serverar webbsidan och genererar PDF via /api/pdf."""

import io
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from generate_pdf import generate_pdf, fetch_holidays


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/pdf":
            params = urllib.parse.parse_qs(parsed.query)
            country = (params.get("country") or ["SE"])[0]
            year_str = (params.get("year") or ["2026"])[0]
            try:
                year = int(year_str)
            except ValueError:
                self.send_error(400, "Invalid year")
                return

            try:
                pdf_bytes = generate_pdf(country, year)
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header(
                    "Content-Disposition",
                    f'attachment; filename="helgdagar_{country}_{year}.pdf"',
                )
                self.send_header("Content-Length", str(len(pdf_bytes)))
                self.end_headers()
                self.wfile.write(pdf_bytes)
            except Exception as e:
                self.send_error(500, str(e))
            return

        return super().do_GET()


if __name__ == "__main__":
    port = 8080
    server = HTTPServer(("", port), Handler)
    print(f"Server: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print("Server stopped.")
