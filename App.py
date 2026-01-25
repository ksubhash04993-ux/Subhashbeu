from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import requests
import time
import io
import pandas as pd
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

BEU_URL = "https://beu-bih.ac.in/result-three"

def sem_to_roman(sem):
    return {
        "1st": "I",
        "2nd": "II",
        "3rd": "III",
        "4th": "IV",
        "5th": "V",
        "6th": "VI",
        "7th": "VII",
        "8th": "VIII"
    }.get(sem, sem)


def fetch_result(reg_no, sem, session):
    sem_roman = sem_to_roman(sem)

    params = {
        "name": f"B.Tech. {sem_roman} Semester Examination",
        "semester": sem_roman,
        "session": session,
        "regNo": reg_no,
        "exam_held": f"November/{session}"
    }

    r = requests.get(BEU_URL, params=params, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")

    table = soup.find("table")
    if not table:
        return []

    rows = table.find_all("tr")[1:]
    result = []

    for row in rows:
        cols = [c.text.strip() for c in row.find_all("td")]
        if len(cols) >= 4:
            result.append({
                "Registration No": reg_no,
                "Subject Code": cols[0],
                "Subject Name": cols[1],
                "Marks / Grade": cols[2],
                "Result": cols[3]
            })

    return result


@app.route("/bulk-result", methods=["POST"])
def bulk_result():
    data = request.json

    start_reg = int(data["start_reg"])
    end_reg   = int(data["end_reg"])
    sem       = data["sem"]
    session   = data["session"]

    all_results = []

    for reg in range(start_reg, end_reg + 1):
        print(f"Fetching {reg}")
        rows = fetch_result(reg, sem, session)
        if rows:
            all_results.extend(rows)
        time.sleep(1)  # safe delay

    if not all_results:
        return jsonify({"error": "No result found"}), 404

    df = pd.DataFrame(all_results)

    buffer = io.StringIO()
    df.to_csv(buffer, index=False)

    mem = io.BytesIO()
    mem.write(buffer.getvalue().encode("utf-8"))
    mem.seek(0)

    return send_file(
        mem,
        mimetype="text/csv",
        as_attachment=True,
        download_name="beu_results_with_marks.csv"
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
