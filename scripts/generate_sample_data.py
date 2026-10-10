"""Regenerate data/sample_data/students_sample.json deterministically.

    python scripts/generate_sample_data.py

The output is committed to the repository; this script only exists so the
demonstration data can be reproduced or adjusted.
"""
import json
import random
from datetime import date
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "data" / "sample_data" / "students_sample.json"

NAMES = [
    ("Aarav", "Sharma"), ("Ananya", "Verma"), ("Rohan", "Patel"), ("Priya", "Nair"),
    ("Karan", "Mehta"), ("Sneha", "Iyer"), ("Vikram", "Rao"), ("Neha", "Gupta"),
    ("Arjun", "Reddy"), ("Isha", "Kapoor"), ("Rahul", "Joshi"), ("Pooja", "Bhat"),
    ("Aditya", "Singh"), ("Divya", "Menon"), ("Manish", "Tiwari"), ("Kavya", "Pillai"),
    ("Siddharth", "Chauhan"), ("Meera", "Desai"), ("Nikhil", "Agarwal"), ("Riya", "Banerjee"),
    ("Harsh", "Yadav"), ("Tanvi", "Kulkarni"), ("Yash", "Malhotra"), ("Shruti", "Saxena"),
    ("Deepak", "Mishra"), ("Anjali", "Dubey"), ("Rajat", "Thakur"), ("Swati", "Jain"),
    ("Amit", "Pandey"), ("Lakshmi", "Subramanian"),
]

# (course, department, id prefix, number of semesters)
PROGRAMS = [
    ("MCA", "Computer Applications", "MCA", 4),
    ("BCA", "Computer Applications", "BCA", 6),
    ("B.Tech Information Technology", "Information Technology", "BIT", 8),
    ("M.Sc. Computer Science", "Computer Science", "MSC", 4),
    ("MBA", "Management Studies", "MBA", 4),
]
WEIGHTS = [9, 6, 6, 4, 5]

PLACES = [
    ("Pune", "Maharashtra"), ("Bhopal", "Madhya Pradesh"), ("Jaipur", "Rajasthan"),
    ("Hyderabad", "Telangana"), ("Lucknow", "Uttar Pradesh"), ("Kochi", "Kerala"),
    ("Indore", "Madhya Pradesh"), ("Ahmedabad", "Gujarat"), ("Nagpur", "Maharashtra"),
]
STREETS = ["Station Road", "Gandhi Nagar", "Civil Lines", "MG Road", "Lake View Colony", "Nehru Park Road"]


def build():
    rng = random.Random(2026)
    counters = {}
    records = []
    for index, (first, last) in enumerate(NAMES):
        course, department, prefix, max_sem = rng.choices(PROGRAMS, weights=WEIGHTS)[0]
        semester = rng.randint(1, max_sem)
        admission = date(2026 - (semester - 1) // 2, 7, rng.randint(1, 28))
        key = (prefix, admission.year)
        counters[key] = counters.get(key, 0) + 1
        student_id = f"{prefix}{admission.year % 100:02d}{counters[key]:03d}"

        dob = date(rng.randint(1996, 2005), rng.randint(1, 12), rng.randint(1, 28))
        city, state = rng.choice(PLACES)
        marks = round(rng.uniform(42, 96), 1)
        if semester == 1 and index % 3 == 0:
            marks = None  # first-semester students without results yet

        records.append({
            "student_id": student_id,
            "full_name": f"{first} {last}",
            "email": f"{first.lower()}.{last.lower()}@students.example.edu",
            "phone": f"+91 {rng.choice(['98', '97', '96', '88', '70'])}{rng.randint(100, 999)} {rng.randint(10000, 99999)}",
            "course": course,
            "department": department,
            "semester": semester,
            "admission_date": admission.isoformat(),
            "date_of_birth": dob.isoformat(),
            "marks": marks,
            "address": f"{rng.randint(10, 199)}, {rng.choice(STREETS)}, {city}, {state}",
            "created_at": f"{admission.isoformat()}T09:30:00+00:00",
            "updated_at": f"{admission.isoformat()}T09:30:00+00:00",
        })
    return records


if __name__ == "__main__":
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "students": build()}
    OUTPUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(payload['students'])} records to {OUTPUT}")
