"""
Simple Flask web interface for the outreach pipeline.
This allows the CLI tool to run as a web service on Render.
"""
from flask import Flask, request, jsonify, render_template_string
import logging
import sys
import io

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Outreach Pipeline</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        .status { padding: 20px; background: #e8f5e9; border-radius: 8px; margin: 20px 0; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #4CAF50; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #45a049; }
        pre { background: #f5f5f5; padding: 15px; border-radius: 4px; overflow-x: auto; }
        .checkbox-group { margin: 10px 0; }
    </style>
</head>
<body>
    <h1>🚀 Outreach Pipeline</h1>
    <div class="status">
        <strong>Status:</strong> ✅ Running<br>
        <strong>Version:</strong> 1.0.0
    </div>
    
    <h2>Run Pipeline</h2>
    <form action="/run" method="POST">
        <div class="form-group">
            <label>Seed Domain (e.g., stripe.com):</label>
            <input type="text" name="domain" placeholder="example.com" required>
        </div>
        <div class="checkbox-group">
            <label><input type="checkbox" name="mock" checked> Mock Mode (use sample data)</label>
        </div>
        <div class="checkbox-group">
            <label><input type="checkbox" name="dry_run" checked> Dry Run (no emails sent)</label>
        </div>
        <button type="submit">Run Pipeline</button>
    </form>
    
    <h2>API Usage</h2>
    <pre>
POST /run
Content-Type: application/json

{
  "domain": "stripe.com",
  "mock": true,
  "dry_run": true
}
    </pre>
    
    <h2>CLI Usage</h2>
    <pre>
outreach stripe.com --mock --dry-run   # Test run
outreach stripe.com --dry-run          # Real APIs, no send
outreach stripe.com                     # Full run
    </pre>
</body>
</html>
"""

RESULT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pipeline Result</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        pre { background: #f5f5f5; padding: 15px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; }
        a { color: #4CAF50; }
    </style>
</head>
<body>
    <h1>Pipeline Result</h1>
    <pre>{{ output }}</pre>
    <p><a href="/">← Back to Home</a></p>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HTML_TEMPLATE)


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "version": "1.0.0"})


@app.route("/run", methods=["POST"])
def run_pipeline():
    # Get parameters
    if request.is_json:
        data = request.json
        domain = data.get("domain", "example.com")
        mock = data.get("mock", True)
        dry_run = data.get("dry_run", True)
    else:
        domain = request.form.get("domain", "example.com")
        mock = request.form.get("mock") == "on"
        dry_run = request.form.get("dry_run") == "on"
    
    # Capture output
    old_stdout = sys.stdout
    sys.stdout = captured = io.StringIO()
    
    # Set up logging to capture
    handler = logging.StreamHandler(captured)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s", "%H:%M:%S")
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    try:
        from outreach_pipeline.pipeline import run
        sent = run(
            domain,
            mock=mock,
            dry_run=dry_run,
            auto_yes=True  # Auto-confirm for web interface
        )
        output = captured.getvalue()
        output += f"\n\n✅ Pipeline complete. Emails sent: {sent}"
    except Exception as e:
        output = captured.getvalue()
        output += f"\n\n❌ Error: {str(e)}"
    finally:
        sys.stdout = old_stdout
        root_logger.removeHandler(handler)
    
    if request.is_json:
        return jsonify({"output": output, "domain": domain})
    else:
        return render_template_string(RESULT_TEMPLATE, output=output)


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
