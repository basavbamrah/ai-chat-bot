import traceback
import datetime
from flask import Flask, request
import os
from flask_cors import CORS
from datetime import datetime
from main import GetCatalyzedAgent

app = Flask(__name__)
app.secret_key = os.urandom(24)


@app.route("/", methods=["POST", "GET"])
def index():
    return {
        "status": "success",
        "version": "0.0.1",
    }


@app.route("/ask", methods=["POST", "GET"])
def ask():
    try:
        if request.method == "GET":
            return {
                "status": "success",
                "message": "start with a post request",
            }, 200
        data = request.get_json()
        print(data)

        obj = GetCatalyzedAgent()
        response = obj.ask_question(data["query"])
        return {
            "status": "success",
            "input": response["input"],
            "output": response["output"],
            "token": response["token"],
        }
    except Exception as e:
        traceback.print_exc()
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc(),
        }, 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
