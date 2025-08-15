import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import os
import csv
from datetime import datetime, date

# ===================== Helpers =====================

def parse_ddmmyyyy(s: str) -> date:
    return datetime.strptime(s, "%d-%m-%Y").date()

def format_ddmmyyyy(d: date) -> str:
    return d.strftime("%d-%m-%Y")

def filename_for_date_str(date_ddmmyyyy: str) -> str:
    # Store files by ISO date for easy sorting on disk
    d = parse_ddmmyyyy(date_ddmmyyyy)
    return f"{d.strftime('%Y-%m-%d')}_Attendance.csv"

# ===================== CSV Utilities =====================

def load_attendance_for_date(date_ddmmyyyy: str):
    """Load a specific date into the table."""
    attendance_tree.delete(*attendance_tree.get_children())
    filename = filename_for_date_str(date_ddmmyyyy)
    if os.path.exists(filename):
        with open(filename, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                insert_with_color(row["Date"], row["Roll No."], row["Name"], row["Status"])

def save_attendance(date_ddmmyyyy: str, roll_no: str, name: str, status: str):
    """Append a record to that date's file (create header if needed)."""
    filename = filename_for_date_str(date_ddmmyyyy)
    file_exists = os.path.exists(filename)
    with open(filename, mode="a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Date", "Roll No.", "Name", "Status"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({"Date": date_ddmmyyyy, "Roll No.": roll_no, "Name": name, "Status": status})

def status_update(date_ddmmyyyy: str, roll_no: str, new_status: str):
    """Update status for a roll number for the given date."""
    filename = filename_for_date_str(date_ddmmyyyy)
    if not os.path.exists(filename):
        return
    rows = []
    with open(filename, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Roll No."] == roll_no:
                row["Status"] = new_status
            rows.append(row)
    with open(filename, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["Date", "Roll No.", "Name", "Status"])
        writer.writeheader()
        writer.writerows(rows)

def is_duplicate(date_ddmmyyyy: str, roll_no: str) -> bool:
    """Check if roll_no already exists for that date."""
    filename = filename_for_date_str(date_ddmmyyyy)
    if not os.path.exists(filename):
        return False
    with open(filename, mode="r", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row.get("Roll No.") == roll_no:
                return True
    return False

# ===================== Treeview Helpers =====================

def insert_with_color(date_str, roll_no, name, status):
    tag = "present" if status.lower() == "present" else "absent"
    attendance_tree.insert("", tk.END, values=(date_str, roll_no, name, status), tags=(tag,))

def update_status_dropdown(event):
    selected = attendance_tree.selection()
    if not selected:
        return
    item_id = selected[0]
    vals = attendance_tree.item(item_id, "values")
    date_str, roll_no, name, cur_status = vals

    # Place a combobox over the Status cell
    x, y, w, h = attendance_tree.bbox(item_id, column=3)
    if x is None:
        return

    var = tk.StringVar(value=cur_status)
    dd = ttk.Combobox(attendance_tree, textvariable=var, values=["Present", "Absent"],
                      state="readonly", width=10, justify="center")
    dd.place(x=x, y=y, width=w, height=h)

    def on_sel(_e=None):
        new_status = var.get()
        attendance_tree.item(item_id, values=(date_str, roll_no, name, new_status), tags=(new_status.lower(),))
        status_update(date_str, roll_no, new_status)
        dd.destroy()
        messagebox.showinfo("Updated", f"Status for Roll No. {roll_no} updated to {new_status}")

    def on_blur(_e=None):
        dd.destroy()

    dd.bind("<<ComboboxSelected>>", on_sel)
    dd.bind("<FocusOut>", on_blur)
    attendance_tree.bind("<Button-1>", lambda e: dd.destroy(), add="+")
    dd.focus_set()

# ===================== Calendar Popup =====================

calendar_popup = None
calendar_close_binds = []

def close_calendar_popup():
    global calendar_popup, calendar_close_binds
    if calendar_popup and calendar_popup.winfo_exists():
        # Unbind outside-click handlers
        for args in calendar_close_binds:
            widget, sequence, funcid = args
            widget.unbind(sequence, funcid)
        calendar_close_binds.clear()
        calendar_popup.destroy()
    calendar_popup = None

def bind_outside_close(widget, sequence, func):
    """Bind and keep the bind id for later unbinding."""
    bind_id = widget.bind(sequence, func, add="+")
    calendar_close_binds.append((widget, sequence, bind_id))

def pick_date(entry_var: tk.StringVar):
    """Open calendar popup above main window, allow only today & past, close on outside click."""
    global calendar_popup
    close_calendar_popup()  # ensure only one

    def on_select():
        sel = cal.selection_get()
        if sel <= date.today():
            entry_var.set(sel.strftime("%d-%m-%Y"))
            close_calendar_popup()
        else:
            messagebox.showerror("Invalid Date", "You can only select today or previous dates.")

    calendar_popup = tk.Toplevel(root)
    calendar_popup.transient(root)
    calendar_popup.overrideredirect(False)  # Keep native frame
    calendar_popup.attributes("-topmost", True)

    # Position: centered horizontally, just above root window
    root.update_idletasks()
    rx = root.winfo_rootx()
    ry = root.winfo_rooty()
    rwidth = root.winfo_width()
    popup_width = 280
    x = rx + (rwidth - popup_width) // 2
    y = max(ry - 10, 0)
    calendar_popup.geometry(f"+{x}+{y}")

    # Calendar widget
    today = date.today()
    cal = Calendar(calendar_popup, selectmode="day", date_pattern="dd-mm-yyyy", maxdate=today)
    cal.pack(padx=10, pady=10)
    ttk.Button(calendar_popup, text="Select", command=on_select).pack(pady=(0, 10))

    # Close when clicking outside or losing focus
    def outside_click(_e=None):
        # If click is outside the popup window bounds, close it
        if not calendar_popup.winfo_exists():
            return
        # Delay a tick so click targets can resolve
        calendar_popup.after(1, close_calendar_popup)

    bind_outside_close(root, "<Button-1>", lambda e: outside_click())
    bind_outside_close(calendar_popup, "<FocusOut>", lambda e: outside_click())

# ===================== Attendance Actions =====================

def mark_attendance():
    roll_no = roll_var.get().strip()
    name = name_var.get().strip()
    status = status_var.get()
    date_str = mark_date_var.get().strip()

    if not roll_no or not name or not date_str:
        messagebox.showwarning("Input Error", "Roll No., Name and Date are required.")
        return

    try:
        d = parse_ddmmyyyy(date_str)
    except ValueError:
        messagebox.showerror("Date Error", "Please pick a valid date (dd-mm-yyyy).")
        return

    if d > date.today():
        messagebox.showwarning("Date Error", "Cannot mark attendance for future dates.")
        return

    if is_duplicate(date_str, roll_no):
        messagebox.showerror("Duplicate", f"Roll No. {roll_no} already exists for {date_str}.")
        return

    save_attendance(date_str, roll_no, name, status)
    insert_with_color(date_str, roll_no, name, status)
    roll_var.set("")
    name_var.set("")
    status_var.set("Present")

def search_attendance():
    date_str = search_date_var.get().strip()
    if not date_str:
        messagebox.showwarning("Input Error", "Please select a date to search.")
        return
    try:
        d = parse_ddmmyyyy(date_str)
    except ValueError:
        messagebox.showerror("Date Error", "Please pick a valid date (dd-mm-yyyy).")
        return
    if d > date.today():
        messagebox.showwarning("Date Error", "Cannot search future dates.")
        return
    load_attendance_for_date(date_str)

# ===================== GUI =====================

root = tk.Tk()
root.title("Attendance Manager")
root.geometry("820x620")
root.configure(bg="white")

# Title banner (light gray, centered, full width)
title_label = tk.Label(
    root, text="Attendance Tracker", font=("Helvetica", 20, "bold"),
    bg="#d3d3d3", fg="black", pady=10
)
title_label.pack(fill="x")

# ---------- Mark Attendance Section ----------
mark_frame = tk.LabelFrame(root, text="Mark Attendance", padx=12, pady=12, bg="white")
mark_frame.pack(fill="x", padx=20, pady=12)

# Variables
roll_var = tk.StringVar()
name_var = tk.StringVar()
status_var = tk.StringVar(value="Present")
mark_date_var = tk.StringVar(value=format_ddmmyyyy(date.today()))

# Layout grid (4 columns; button centered by spanning)
for c in range(6):
    mark_frame.columnconfigure(c, weight=1)

tk.Label(mark_frame, text="Roll No.:", bg="white").grid(row=0, column=0, padx=5, pady=5, sticky="e")
tk.Entry(mark_frame, textvariable=roll_var, justify="center").grid(row=0, column=1, padx=5, pady=5, sticky="w")

tk.Label(mark_frame, text="Name:", bg="white").grid(row=0, column=2, padx=5, pady=5, sticky="e")
tk.Entry(mark_frame, textvariable=name_var, justify="center").grid(row=0, column=3, padx=5, pady=5, sticky="w")

tk.Label(mark_frame, text="Status:", bg="white").grid(row=0, column=4, padx=5, pady=5, sticky="e")
ttk.Combobox(mark_frame, textvariable=status_var, values=["Present", "Absent"],
             state="readonly", width=10, justify="center").grid(row=0, column=5, padx=5, pady=5, sticky="w")

tk.Label(mark_frame, text="Date:", bg="white").grid(row=1, column=0, padx=5, pady=5, sticky="e")
mark_date_entry = tk.Entry(mark_frame, textvariable=mark_date_var, justify="center", width=14)
mark_date_entry.grid(row=1, column=1, padx=(5, 0), pady=5, sticky="w")
ttk.Button(mark_frame, text="📅", width=3, command=lambda: pick_date(mark_date_var)).grid(row=1, column=1, padx=(140, 0), pady=5, sticky="w")

# Centered "Mark Attendance" button (span full row, center via columnspan)
mark_btn = ttk.Button(mark_frame, text="Mark Attendance", command=mark_attendance)
mark_btn.grid(row=2, column=0, columnspan=6, pady=(10, 0))

# ---------- Search Section ----------
search_frame = tk.LabelFrame(root, text="Search Attendance", padx=12, pady=12, bg="white")
search_frame.pack(fill="x", padx=20, pady=12)

search_date_var = tk.StringVar(value=format_ddmmyyyy(date.today()))
for c in range(4):
    search_frame.columnconfigure(c, weight=1)

tk.Label(search_frame, text="Select Date:", bg="white").grid(row=0, column=0, padx=5, pady=5, sticky="e")
search_date_entry = tk.Entry(search_frame, textvariable=search_date_var, justify="center", width=14)
search_date_entry.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="w")
ttk.Button(search_frame, text="📅", width=3, command=lambda: pick_date(search_date_var)).grid(row=0, column=1, padx=(140, 0), pady=5, sticky="w")
ttk.Button(search_frame, text="Search", command=search_attendance).grid(row=0, column=2, padx=5, pady=5, sticky="w")

# ---------- Attendance Table ----------
tree_frame = tk.Frame(root, bg="white")
tree_frame.pack(fill="both", expand=True, padx=20, pady=10)

attendance_tree = ttk.Treeview(
    tree_frame,
    columns=("Date", "Roll No.", "Name", "Status"),
    show="headings",
    height=15,
)
attendance_tree.heading("Date", text="Date")
attendance_tree.heading("Roll No.", text="Roll No.")
attendance_tree.heading("Name", text="Name")
attendance_tree.heading("Status", text="Status")

attendance_tree.column("Date", width=120, anchor="center")
attendance_tree.column("Roll No.", width=120, anchor="center")
attendance_tree.column("Name", width=220, anchor="center")
attendance_tree.column("Status", width=120, anchor="center")

attendance_tree.pack(fill="both", expand=True, side="left")

scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=attendance_tree.yview)
attendance_tree.configure(yscroll=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Dark colors with white text
attendance_tree.tag_configure("present", background="#006400", foreground="#ffffff")  # dark green
attendance_tree.tag_configure("absent", background="#8B0000", foreground="#ffffff")   # dark red

attendance_tree.bind("<Double-1>", update_status_dropdown)

# ---------- Initial Load ----------
today_ddmmyyyy = format_ddmmyyyy(date.today())
load_attendance_for_date(today_ddmmyyyy)

# Ensure popup closes if main window is closed
root.protocol("WM_DELETE_WINDOW", lambda: (close_calendar_popup(), root.destroy()))

root.mainloop()
