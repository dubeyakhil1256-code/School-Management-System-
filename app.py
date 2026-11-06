import json
import os
from abc import ABC, abstractmethod

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------- config
st.set_page_config(page_title="School Manager", page_icon="🎓", layout="wide")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "school_data.json")


# ---------------------------------------------------------------- data layer
def load_data():
    data = {"students": [], "teachers": []}
    if os.path.exists(DATABASE):
        with open(DATABASE, "r") as f:
            content = f.read().strip()
            if content:
                data = json.loads(content)
    return data


def save(data):
    with open(DATABASE, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------------- OOP layer (same design as your original code)
class Persons(ABC):
    def __init__(self, data):
        self.data = data

    @abstractmethod
    def get_roles(self):
        pass

    @abstractmethod
    def register(self, **kwargs):
        pass

    @staticmethod
    def validate_email(email):
        return "@" in email and "." in email


class Student(Persons):
    def get_roles(self):
        return "Student"

    def register(self, name, age, email, roll_no):
        if not name.strip() or not roll_no.strip():
            return False, "Name and roll number are required."
        if not Persons.validate_email(email):
            return False, "Invalid email address."
        if any(s["roll_no"] == roll_no for s in self.data["students"]):
            return False, "A student with this roll number already exists."
        self.data["students"].append(
            {"name": name.strip(), "age": age, "email": email.strip(),
             "roll_no": roll_no.strip(), "grades": {}}
        )
        save(self.data)
        return True, f"Student {name} registered successfully!"

    def find(self, roll_no):
        return next((s for s in self.data["students"] if s["roll_no"] == roll_no), None)

    def add_grade(self, roll_no, subject, marks):
        s = self.find(roll_no)
        if not s:
            return False, "Student not found."
        s["grades"][subject.strip()] = marks
        save(self.data)
        return True, f"Added {subject}: {marks} for {s['name']}."

    def delete(self, roll_no):
        self.data["students"] = [s for s in self.data["students"] if s["roll_no"] != roll_no]
        save(self.data)

    @staticmethod
    def average(student):
        g = student["grades"]
        return sum(g.values()) / len(g) if g else 0.0


class Teacher(Persons):
    def get_roles(self):
        return "Teacher"

    def register(self, name, age, email, subject, emp_id):
        if not name.strip() or not emp_id.strip():
            return False, "Name and employee ID are required."
        if not Persons.validate_email(email):
            return False, "Invalid email address."
        if any(t["emp_id"] == emp_id for t in self.data["teachers"]):
            return False, "A teacher with this employee ID already exists."
        self.data["teachers"].append(
            {"name": name.strip(), "age": age, "subject": subject.strip(),
             "email": email.strip(), "emp_id": emp_id.strip()}
        )
        save(self.data)
        return True, f"Teacher {name} registered successfully!"

    def delete(self, emp_id):
        self.data["teachers"] = [t for t in self.data["teachers"] if t["emp_id"] != emp_id]
        save(self.data)


# ---------------------------------------------------------------- styling
st.markdown(
    """
    <style>
    .block-container {padding-top: 2rem;}
    .hero {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #db2777 100%);
        padding: 1.8rem 2rem; border-radius: 18px; color: white; margin-bottom: 1.5rem;
    }
    .hero h1 {margin: 0; font-size: 2rem; color: white;}
    .hero p {margin: .3rem 0 0; opacity: .9;}
    div[data-testid="stMetric"] {
        background: rgba(124, 58, 237, 0.08);
        border: 1px solid rgba(124, 58, 237, 0.25);
        padding: 1rem 1.2rem; border-radius: 14px;
    }
    .card {
        border: 1px solid rgba(128,128,128,.25); border-radius: 16px;
        padding: 1.2rem 1.4rem; margin-bottom: 1rem;
        background: rgba(128,128,128,.05);
    }
    .badge {
        display: inline-block; padding: .15rem .7rem; border-radius: 999px;
        background: #7c3aed; color: white; font-size: .8rem; margin-right: .4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def hero(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- app state
data = load_data()
stud = Student(data)
teacher = Teacher(data)

with st.sidebar:
    st.markdown("## 🎓 School Manager")
    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "🧑‍🎓 Register Student", "👩‍🏫 Register Teacher",
         "📝 Add Grades", "🔍 Student Details", "📋 Teacher Directory"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(f"👥 {len(data['students'])} students · {len(data['teachers'])} teachers")


# ---------------------------------------------------------------- pages
if page == "📊 Dashboard":
    hero("Dashboard", "A quick overview of your school")
    c1, c2, c3 = st.columns(3)
    c1.metric("Students", len(data["students"]))
    c2.metric("Teachers", len(data["teachers"]))
    all_avgs = [Student.average(s) for s in data["students"] if s["grades"]]
    c3.metric("Overall Avg Marks", f"{sum(all_avgs) / len(all_avgs):.1f}" if all_avgs else "—")

    st.markdown("### 🏆 Student Averages")
    if all_avgs:
        df = pd.DataFrame(
            [{"Student": s["name"], "Average": round(Student.average(s), 2)}
             for s in data["students"] if s["grades"]]
        ).sort_values("Average", ascending=False)
        left, right = st.columns([2, 1])
        left.bar_chart(df.set_index("Student"), color="#7c3aed")
        right.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("No grades yet. Add some from the **Add Grades** page.")

elif page == "🧑‍🎓 Register Student":
    hero("Register Student", "Add a new student to the system")
    with st.form("student_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name")
        roll_no = c2.text_input("Roll number")
        email = c1.text_input("Email")
        age = c2.number_input("Age", min_value=3, max_value=100, value=18, step=1)
        submitted = st.form_submit_button("Register Student", type="primary", use_container_width=True)
    if submitted:
        ok, msg = stud.register(name, int(age), email, roll_no)
        (st.success if ok else st.error)(msg)
        if ok:
            st.balloons()

elif page == "👩‍🏫 Register Teacher":
    hero("Register Teacher", "Add a new teacher to the system")
    with st.form("teacher_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Full name")
        emp_id = c2.text_input("Employee ID")
        email = c1.text_input("Email")
        subject = c2.text_input("Subject")
        age = st.number_input("Age", min_value=18, max_value=100, value=30, step=1)
        submitted = st.form_submit_button("Register Teacher", type="primary", use_container_width=True)
    if submitted:
        ok, msg = teacher.register(name, int(age), email, subject, emp_id)
        (st.success if ok else st.error)(msg)

elif page == "📝 Add Grades":
    hero("Add Grades", "Record marks for a student's subject")
    if not data["students"]:
        st.warning("Register a student first.")
    else:
        options = {f"{s['name']} ({s['roll_no']})": s["roll_no"] for s in data["students"]}
        with st.form("grade_form", clear_on_submit=True):
            choice = st.selectbox("Student", list(options.keys()))
            c1, c2 = st.columns(2)
            subject = c1.text_input("Subject")
            marks = c2.number_input("Marks", min_value=0.0, max_value=100.0, value=0.0, step=0.5)
            submitted = st.form_submit_button("Save Grade", type="primary", use_container_width=True)
        if submitted:
            if not subject.strip():
                st.error("Please enter a subject.")
            else:
                ok, msg = stud.add_grade(options[choice], subject, marks)
                (st.success if ok else st.error)(msg)

elif page == "🔍 Student Details":
    hero("Student Details", "Look up a student's profile and grades")
    if not data["students"]:
        st.warning("No students registered yet.")
    else:
        options = {f"{s['name']} ({s['roll_no']})": s["roll_no"] for s in data["students"]}
        choice = st.selectbox("Select student", list(options.keys()))
        s = stud.find(options[choice])
        if s:
            avg = Student.average(s)
            st.markdown(
                f"""<div class="card">
                <h3 style="margin-top:0">{s['name']}</h3>
                <span class="badge">Roll: {s['roll_no']}</span>
                <span class="badge">Age: {s['age']}</span>
                <span class="badge">{s['email']}</span>
                </div>""",
                unsafe_allow_html=True,
            )
            c1, c2 = st.columns(2)
            c1.metric("Subjects", len(s["grades"]))
            c2.metric("Average", f"{avg:.2f}")
            if s["grades"]:
                gdf = pd.DataFrame(list(s["grades"].items()), columns=["Subject", "Marks"])
                a, b = st.columns([1, 2])
                a.dataframe(gdf, hide_index=True, use_container_width=True)
                b.bar_chart(gdf.set_index("Subject"), color="#db2777")
            else:
                st.info("No grades recorded yet.")
            with st.expander("⚠️ Danger zone"):
                if st.button("Delete this student", type="secondary"):
                    stud.delete(s["roll_no"])
                    st.rerun()

elif page == "📋 Teacher Directory":
    hero("Teacher Directory", "All registered teachers")
    if not data["teachers"]:
        st.warning("No teachers registered yet.")
    else:
        search = st.text_input("🔎 Search by name or subject")
        rows = [t for t in data["teachers"]
                if search.lower() in t["name"].lower() or search.lower() in t["subject"].lower()]
        df = pd.DataFrame(rows).rename(columns={
            "name": "Name", "age": "Age", "subject": "Subject", "email": "Email", "emp_id": "Emp ID"})
        st.dataframe(df, hide_index=True, use_container_width=True)
        with st.expander("⚠️ Danger zone"):
            emp = st.selectbox("Remove teacher", [t["emp_id"] for t in data["teachers"]])
            if st.button("Delete teacher"):
                teacher.delete(emp)
                st.rerun()