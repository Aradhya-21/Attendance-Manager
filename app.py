from flask import Flask, render_template, request, flash, redirect, url_for, send_file
import os, csv
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = "secret123"

# ================= Helpers =================

def parse_ddmmyyyy(s: str) -> date:
    return datetime.strptime(s, "%d-%m-%Y").date()

def format_ddmmyyyy(d: date) -> str:
    return d.strftime("%d-%m-%Y")

def from_html_date(s: str) -> str:
    """Convert HTML date input (yyyy-mm-dd) -> dd-mm-yyyy"""
    return datetime.strptime(s, "%Y-%m-%d").strftime("%d-%m-%Y")

def to_html_date(s: str) -> str:
    """Convert dd-mm-yyyy -> yyyy-mm-dd for HTML input"""
    return datetime.strptime(s, "%d-%m-%Y").strftime("%Y-%m-%d")

def filename_for_date_str(date_ddmmyyyy: str) -> str:
    d = parse_ddmmyyyy(date_ddmmyyyy)
    return f"{d.strftime('%Y-%m-%d')}_Attendance.csv"

# ================= CSV Utilities =================

def load_attendance_for_date(date_ddmmyyyy: str):
    filename = filename_for_date_str(date_ddmmyyyy)
    records = []
    if os.path.exists(filename):
        with open(filename, newline="") as f:
            reader = csv.DictReader(f)
            records = list(reader)
    return records

def save_attendance(date_ddmmyyyy: str, roll_no: str, name: str, status: str):
    filename = filename_for_date_str(date_ddmmyyyy)
    file_exists = os.path.exists(filename)
    with open(filename, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Roll No.", "Name", "Status"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "Date": date_ddmmyyyy,
            "Roll No.": roll_no,
            "Name": name,
            "Status": status
        })

def update_status(date_ddmmyyyy: str, roll_no: str, new_status: str):
    filename = filename_for_date_str(date_ddmmyyyy)
    if not os.path.exists(filename):
        return
    rows = []
    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Roll No."] == roll_no:
                row["Status"] = new_status
            rows.append(row)
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Roll No.", "Name", "Status"])
        writer.writeheader()
        writer.writerows(rows)

def delete_record(date_ddmmyyyy: str, roll_no: str):
    filename = filename_for_date_str(date_ddmmyyyy)
    if not os.path.exists(filename):
        return
    rows = []
    with open(filename, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not (row["Roll No."] == roll_no and row["Date"] == date_ddmmyyyy):
                rows.append(row)
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Date", "Roll No.", "Name", "Status"])
        writer.writeheader()
        writer.writerows(rows)

def is_duplicate(date_ddmmyyyy: str, roll_no: str):
    for row in load_attendance_for_date(date_ddmmyyyy):
        if row["Roll No."] == roll_no:
            return True
    return False

# ================= Routes =================

@app.route("/", methods=["GET", "POST"])
def index():
    today_ddmmyyyy = format_ddmmyyyy(date.today())
    today_html = to_html_date(today_ddmmyyyy)
    selected_date = today_ddmmyyyy

    # Handle marking attendance
    if request.method == "POST" and "mark" in request.form:
        roll_no = request.form.get("roll_no", "").strip()
        name = request.form.get("name", "").strip()
        html_date = request.form.get("date", today_html)
        status = request.form.get("status", "Present")

        try:
            date_str = from_html_date(html_date)
            d = parse_ddmmyyyy(date_str)
        except ValueError:
            flash("Invalid date format.", "error")
            date_str = today_ddmmyyyy
            d = date.today()

        # ✅ Prevent future dates
        if d > date.today():
            flash("You cannot mark attendance for future dates.", "error")
            date_str = today_ddmmyyyy

        if not roll_no or not name:
            flash("Roll No. and Name are required!", "error")
        elif is_duplicate(date_str, roll_no):
            flash(f"Roll No. {roll_no} already exists for {date_str}.", "error")
        else:
            save_attendance(date_str, roll_no, name, status)
            flash("Attendance marked successfully!", "success")
            selected_date = date_str

    # Handle searching attendance
    if request.method == "POST" and "search" in request.form:
        html_date = request.form.get("search_date", today_html)
        try:
            selected_date = from_html_date(html_date)
            d = parse_ddmmyyyy(selected_date)
        except ValueError:
            flash("Invalid search date.", "error")
            selected_date = today_ddmmyyyy
            d = date.today()

        # ✅ Prevent future dates
        if d > date.today():
            flash("You cannot search attendance for future dates.", "error")
            selected_date = today_ddmmyyyy

    records = load_attendance_for_date(selected_date)
    return render_template(
        "index.html",
        records=records,
        selected_date=selected_date,
        selected_date_html=to_html_date(selected_date),
        today_html=today_html
    )

@app.route("/update", methods=["POST"])
def update():
    roll_no = request.form.get("roll_no")
    new_status = request.form.get("status")
    date_str = request.form.get("date")

    if roll_no and new_status and date_str:
        update_status(date_str, roll_no, new_status)
        flash(f"Status updated for Roll No. {roll_no} → {new_status}", "success")

    return redirect(url_for("index"))

@app.route("/delete", methods=["POST"])
def delete():
    roll_no = request.form.get("roll_no")
    date_str = request.form.get("date")

    if roll_no and date_str:
        delete_record(date_str, roll_no)
        flash(f"Deleted record for Roll No. {roll_no} on {date_str}", "success")

    return redirect(url_for("index"))

@app.route("/download/<date_str>")
def download(date_str):
    """Download attendance CSV for a specific date"""
    filename = filename_for_date_str(date_str)
    if not os.path.exists(filename):
        flash(f"No attendance file found for {date_str}", "error")
        return redirect(url_for("index"))
    return send_file(filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
