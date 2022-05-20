from app import app

from dotenv import load_dotenv
load_dotenv()

import os

os.system('ls -a')

@app.route("/")
def index():

    # Use os.getenv("key") to get environment variables
    app_name = os.getenv("test")

    if app_name:
        return f"Hello from flask with working env: {app_name}"

    return "Hello from Flask"