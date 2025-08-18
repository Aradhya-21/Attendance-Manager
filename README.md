# 📊 Attendance Manager (Flask Web App)

### 🧠 Technology
- **Domain:** Web Application / Attendance Tracking  
- **Level:** Beginner – Intermediate  
- **Tech Stack:** Python, Flask, HTML, CSV  

---

### 📌 Project Description

**Attendance Manager** is a **Flask web application** that allows administrators to **record, search, update, delete, and download attendance** efficiently.  
It uses **CSV files** to store daily attendance in a lightweight, portable format.  

The system includes **input validation, duplicate prevention, and color-coded records**, ensuring accurate and user-friendly attendance management.

---

### 🔧 Features

- ✅ **Mark Attendance** → Add Roll No., Name, Date, and Status (Present/Absent)  
- 🛡 **Duplicate Prevention** → Prevents the same Roll No. being added twice for the same date  
- 🔎 **Search Attendance** → View saved records by selecting a date  
- ✏️ **Update Status** → Change Present/Absent dynamically  
- 🗑 **Delete Records** → Remove student entries for a date  
- 📥 **Download CSV** → Export daily attendance as `.csv` file  
- 📅 **Validation** → Blocks future dates & ensures required fields  

---

### 📦 Requirements

- Python 3.7+  
- Flask  

Install dependencies with: pip install -r requirements.txt


### 💾 Data Storage

Attendance is saved in .csv files named by date:

YYYY-MM-DD_Attendance.csv


CSV Columns:

Date, Roll No., Name, Status

### 🤝 Contributing

Contributions, suggestions, and feature requests are welcome!

### 📄 License

This project is intended for educational and personal use.
Feel free to modify and improve it.
