"""Local-only HTTP application: python app.py (http://127.0.0.1:8765)."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import storage
from experiments import evaluate
from nlp import ASPECTS, VERSION, analyze, corpus_insights, pipeline_details

ROOT = Path(__file__).parent


class Handler(BaseHTTPRequestHandler):
    def send(self, status, payload, content_type="application/json; charset=utf-8"):
        data = json.dumps(payload, ensure_ascii=False).encode() if not isinstance(payload, bytes) else payload
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self.send(200, {"status": "ok", "engine": VERSION, "aspects": list(ASPECTS)})
        if path == "/api/reviews":
            return self.send(200, {"reviews": storage.list_reviews()})
        files = {"/": ("index.html", "text/html; charset=utf-8"), "/app.js": ("app.js", "text/javascript; charset=utf-8"), "/style.css": ("style.css", "text/css; charset=utf-8")}
        if path in files:
            filename, mime = files[path]
            return self.send(200, (ROOT / "web" / filename).read_bytes(), mime)
        return self.send(404, {"error": "Not found"})

    def do_POST(self):
        # Prevent other websites from making writes against the local service.
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{self.headers.get('Host')}":
            return self.send(403, {"error": "Cross-origin requests are disabled."})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 8_000_000:
                return self.send(413, {"error": "Request must be between 1 byte and 8 MB."})
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict):
                raise ValueError("JSON body must be an object.")
            path = urlparse(self.path).path
            if path == "/api/analyze":
                return self.send(200, analyze(body.get("text")))
            if path == "/api/import":
                content = body.get("csv")
                if not isinstance(content, str):
                    raise ValueError("Provide CSV text.")
                return self.send(200, storage.import_csv(content))
            if path == "/api/demo":
                return self.send(200, storage.import_csv((ROOT / "data" / "demo_reviews.csv").read_text(encoding="utf-8"), demo=True))
            if path == "/api/corpus":
                rows = storage.list_reviews()
                results = [analyze(r["text"], r["id"], {"source": r["source"], "source_url": r["source_url"], "is_demo": bool(r["is_demo"]), "annotation": r["annotation"]}) for r in rows]
                return self.send(200, {"reviews": results, "insights": corpus_insights(results)})
            if path == "/api/annotate":
                return self.send(200, storage.annotate(body.get("id"), body.get("annotation")))
            if path == "/api/evaluate":
                return self.send(200, evaluate(storage.list_reviews()))
            if path == "/api/pipeline":
                text = body.get("text")
                analyze(text)  # Shared input validation.
                return self.send(200, pipeline_details(text, [r["text"] for r in storage.list_reviews()]))
            return self.send(404, {"error": "Not found"})
        except (ValueError, TypeError, KeyError) as exc:
            return self.send(400, {"error": str(exc)})
        except Exception:
            import traceback
            traceback.print_exc()
            return self.send(500, {"error": "Analysis failed. See the server terminal for details."})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BhashaLens local NLP lab")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"BhashaLens running at http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
