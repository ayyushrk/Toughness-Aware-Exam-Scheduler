# 🎓 Toughness-Aware Exam Scheduler

A dynamic, interactive exam scheduling web application built with **Streamlit** and advanced graph coloring heuristics. Unlike static timetable generators, this application takes student conflict constraints (graph edges) *and* subject difficulty (toughness weights) into account to minimize student academic stress and optimize exam spacing.

---

## ✨ Features

- **Dynamic Course Management:** Add, edit, and delete courses from a blank canvas on the fly.
- **Explicit Semester Assignment:** Assign specific semesters (1 to 8) to each course, even for custom-named courses without numbers.
- **Toughness Ratings:** Scale course difficulty from 1 (Easy) to 5 (Extremely Tough) to control stress heuristics.
- **Conflict Graph Builder:** Define which courses share overlapping students to automatically prevent simultaneous or closely-spaced exam clashes.
- **Flexible Scheduling Controls:** 
  - Adjustable exam days and slots per day (Forenoon, Afternoon, Evening).
  - Minimum slot gap constraint between conflicting exams.
  - Crowding penalty weight to balance daily student workloads.
- **Multiple Visualization Views:**
  - Day-by-Day Slot Matrix Calendar
  - Semester-wise breakdown expanders
  - Detailed chronological exam schedule table
  - Real-time graph adjacency and state inspector

---

## 🚀 Getting Started

### Prerequisites

Make sure you have Python 3.8 or higher installed on your machine. You will also need `streamlit`, `pandas`, and standard data structures (`collections`, `heapq`).

### Installation

1. Clone or download this repository.
2. Install the required dependencies:
   ```bash
   pip install streamlit pandas
   ```

3. Save your scheduler code into a file named `app.py`.

4. Run the Streamlit application:
   ```bash
   streamlit run app.py
   ```

5. Open the local URL provided in your terminal (usually `http://localhost:8501`) in your browser.

---

## 💡 How to Use

1. **Configure Parameters:** Use the sidebar to set your total available **Exam Days**, **Slots per Day**, and **Minimum Slot Gap**.
2. **Add Courses:** 
   - Enter a **Course Code** (e.g., `CS301` or `MACHINE_LEARNING`).
   - Select its **Semester**.
   - Choose its **Toughness Level** (1–5).
   - Select any already-added **Conflicting Courses** that share students.
   - Click **Add Course**.
3. **Edit Details:** Need to change a course's semester or toughness later? Use the **Edit Existing Course** section in the sidebar.
4. **View Timetable:** Instantly inspect the generated valid timetable, matrix calendar, and stress metrics in the main view tabs!

## 👥 Contributors
- [@ARJYUN](https://github.com/ARJYUN)
- [@abhinav-v-r](https://github.com/abhinav-v-r)
- [@adarsh-k-10](https://github.com/adarsh-k-10)
- [@ardraar06](https://github.com/ardrar06)
