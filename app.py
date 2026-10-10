from collections import defaultdict
import heapq
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Toughness-Aware Exam Scheduler", page_icon="📅", layout="wide"
)


def validate_graph(graph, toughness):
  courses = set(graph)
  for course in courses:
    if course not in toughness:
      raise ValueError(f"Missing toughness value for {course}")
  for course, neighbors in graph.items():
    for neighbor in neighbors:
      if neighbor not in courses:
        raise ValueError(
            f"Course '{neighbor}' (conflict of '{course}') is missing."
        )
      if course not in graph[neighbor]:
        raise ValueError(f"Graph is asymmetric for '{course}' and '{neighbor}'.")


def toughness_aware_schedule(
    graph, toughness, days, slots_per_day, min_gap=1, load_penalty=2.0
):
  total_slots = days * slots_per_day
  validate_graph(graph, toughness)

  vertices = list(graph.keys())
  n = len(vertices)
  if n == 0:
    return {}, {}, 0

  color = {}
  saturation = {v: set() for v in vertices}
  schedule = defaultdict(list)
  version = {v: 0 for v in vertices}
  heap = []

  def push(v):
    heapq.heappush(
        heap,
        (-len(saturation[v]), -len(graph[v]), -toughness[v], v, version[v]),
    )

  for v in vertices:
    push(v)

  def is_feasible(v, slot):
    for neighbor in graph[v]:
      if neighbor in color and abs(slot - color[neighbor]) < min_gap:
        return False
    return True

  def local_stress(v, slot):
    stress = 0.0
    for neighbor in graph[v]:
      if neighbor in color:
        distance = abs(slot - color[neighbor])
        stress += toughness[neighbor] / distance
    return stress

  total_stress = 0.0

  while len(color) < n:
    while heap:
      _, _, _, v, old_version = heapq.heappop(heap)
      if v not in color and old_version == version[v]:
        break
    else:
      raise RuntimeError("Priority queue became inconsistent.")

    candidate_slots = [
        s for s in range(1, total_slots + 1) if is_feasible(v, s)
    ]

    if not candidate_slots:
      raise RuntimeError(
          f"Could not fit '{v}' into available slots ({days} days x"
          " {slots_per_day} slots/day)."
      )

    chosen_slot = min(
        candidate_slots,
        key=lambda s: (
            local_stress(v, s) + load_penalty * len(schedule.get(s, [])),
            s,
        ),
    )

    color[v] = chosen_slot
    schedule[chosen_slot].append(v)
    total_stress += local_stress(v, chosen_slot)

    for neighbor in graph[v]:
      if neighbor not in color:
        saturation[neighbor].add(chosen_slot)
        version[neighbor] += 1
        push(neighbor)

  return color, dict(sorted(schedule.items())), total_stress


def verify_schedule(graph, color, min_gap=1):
  for u in graph:
    for v in graph[u]:
      if u < v and abs(color[u] - color[v]) < min_gap:
        return False
  return True


if "graph" not in st.session_state:
  st.session_state["graph"] = {}
if "toughness" not in st.session_state:
  st.session_state["toughness"] = {}
if "semesters" not in st.session_state:
  st.session_state["semesters"] = {}

st.title("🎓 Toughness-Aware Exam Scheduler")
st.markdown("Manage courses and generate timetables without a cramped sidebar.")

# --- MAIN SCREEN CONTROLS (EXPANDER / COLUMNS) ---
with st.expander("⚙️ Scheduler Settings & Configurations", expanded=False):
  col_s1, col_s2, col_s3, col_s4 = st.columns(4)
  with col_s1:
    days = st.slider("Total Exam Days", min_value=1, max_value=30, value=5)
  with col_s2:
    slots_per_day = st.selectbox("Slots per Day", options=[1, 2, 3], index=1)
  with col_s3:
    min_gap = st.slider("Min Slot Gap", min_value=1, max_value=3, value=1)
  with col_s4:
    load_penalty = st.slider(
        "Crowding Penalty", min_value=0.0, max_value=5.0, value=2.0, step=0.5
    )

total_slots = days * slots_per_day
slot_names = ["FN", "AN", "Eve"][:slots_per_day]

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
  st.header("➕ Add New Course")
  with st.form("add_course_form", clear_on_submit=True):
    new_code = st.text_input("Course Code (e.g., CS101)").strip().upper()
    new_semester = st.selectbox("Semester", [1, 2, 3, 4, 5, 6, 7, 8], index=2)
    new_toughness = st.slider("Toughness Level (1 - 5)", 1, 5, 3)

    existing_courses = list(st.session_state["graph"].keys())
    new_conflicts = st.multiselect("Conflicting Courses", existing_courses)

    submitted = st.form_submit_button("Add Course")
    if submitted:
      if not new_code:
        st.error("Please enter a valid course code.")
      elif new_code in st.session_state["graph"]:
        st.error(f"Course '{new_code}' already exists.")
      else:
        st.session_state["graph"][new_code] = new_conflicts
        st.session_state["toughness"][new_code] = new_toughness
        st.session_state["semesters"][new_code] = new_semester
        for neighbor in new_conflicts:
          if new_code not in st.session_state["graph"][neighbor]:
            st.session_state["graph"][neighbor].append(new_code)
        st.success(f"Added course '{new_code}' successfully!")
        st.rerun()

with col2:
  st.header("✏️ Edit Existing Course")
  if st.session_state["graph"]:
    with st.form("edit_course_form"):
      edit_code = st.selectbox(
          "Select Course to Edit", list(st.session_state["graph"].keys())
      )
      current_toughness = st.session_state["toughness"].get(edit_code, 3)
      current_sem = st.session_state["semesters"].get(edit_code, 3)

      edit_semester = st.selectbox(
          "New Semester",
          [1, 2, 3, 4, 5, 6, 7, 8],
          index=int(current_sem) - 1,
      )
      edit_toughness = st.slider(
          "New Toughness Level (1 - 5)", 1, 5, int(current_toughness)
      )

      edit_submitted = st.form_submit_button("Update Course Details")
      if edit_submitted:
        st.session_state["toughness"][edit_code] = edit_toughness
        st.session_state["semesters"][edit_code] = edit_semester
        st.success(f"Updated details for '{edit_code}'!")
        st.rerun()

    if st.button("🗑️ Clear All Courses"):
      st.session_state["graph"] = {}
      st.session_state["toughness"] = {}
      st.session_state["semesters"] = {}
      st.rerun()
  else:
    st.info("Add courses to enable editing options.")

st.markdown("---")


graph_data = st.session_state["graph"]
toughness_data = st.session_state["toughness"]
semester_data = st.session_state["semesters"]

if not graph_data:
  st.info("👆 Use the form above to start adding your courses and conflicts!")
else:
  try:
    color, schedule, total_stress = toughness_aware_schedule(
        graph_data, toughness_data, days, slots_per_day, min_gap, load_penalty
    )
    valid = verify_schedule(graph_data, color, min_gap)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Courses", len(graph_data))
    m2.metric("Total Slots", total_slots)
    m3.metric("Total Stress", f"{total_stress:.2f}")
    m4.metric("Status", "✅ VALID" if valid else "❌ INVALID")

    st.markdown("---")

    table_data = []
    for course in sorted(color.keys()):
      slot_num = color[course]
      day = (slot_num - 1) // slots_per_day + 1
      slot_in_day = (slot_num - 1) % slots_per_day
      table_data.append({
          "Course Code": course,
          "Semester": semester_data.get(course, "N/A"),
          "Day": f"Day {day}",
          "Slot": slot_names[slot_in_day],
          "Slot ID": slot_num,
          "Toughness": toughness_data[course],
          "Conflicts With": (
              ", ".join(graph_data[course]) if graph_data[course] else "None"
          ),
      })

    df = pd.DataFrame(table_data)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Timetable Matrix",
        "📚 Grouped by Semester",
        "📋 Detailed List",
        "📊 Graph Data",
    ])

    with tab1:
      matrix_rows = []
      for d in range(1, days + 1):
        row_dict = {"Day": f"Day {d}"}
        for s_idx, s_name in enumerate(slot_names):
          slot_id = (d - 1) * slots_per_day + s_idx + 1
          courses_in_slot = [c for c, s in color.items() if s == slot_id]
          row_dict[s_name] = (
              ", ".join(courses_in_slot) if courses_in_slot else "—"
          )
        matrix_rows.append(row_dict)
      st.dataframe(
          pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True
      )

    with tab2:
      for sem in sorted(df["Semester"].unique()):
        with st.expander(f"Semester {sem} Courses", expanded=True):
          st.dataframe(
              df[df["Semester"] == sem][
                  [
                      "Course Code",
                      "Day",
                      "Slot",
                      "Toughness",
                      "Conflicts With",
                  ]
              ],
              use_container_width=True,
              hide_index=True,
          )

    with tab3:
      st.dataframe(
          df.sort_values(by=["Slot ID", "Course Code"]),
          use_container_width=True,
          hide_index=True,
      )

    with tab4:
      raw_list = [
          {
              "Course": c,
              "Semester": semester_data.get(c, "N/A"),
              "Toughness": toughness_data[c],
              "Conflicts": ", ".join(graph_data[c]),
          }
          for c in graph_data
      ]
      st.dataframe(
          pd.DataFrame(raw_list), use_container_width=True, hide_index=True
      )

  except RuntimeError as e:
    st.error(f"⚠️ **Scheduling Failed:** {e}")
