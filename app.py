from collections import defaultdict
import heapq
import pandas as pd
import streamlit as st

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Toughness-Aware Exam Scheduler",
    page_icon="📅",
    layout="wide",
)


# ============================================================
# SCHEDULER LOGIC CORE
# ============================================================
def get_semester(course_code):
  digits = "".join(ch for ch in course_code if ch.isdigit())
  return int(digits[0]) if digits else None


def validate_graph(graph, toughness):
  courses = set(graph)
  for course in courses:
    if course not in toughness:
      raise ValueError(f"Missing toughness value for {course}")
  for course, neighbors in graph.items():
    for neighbor in neighbors:
      if neighbor not in courses:
        raise ValueError(
            f"Course '{neighbor}' (listed as conflict of '{course}') is missing"
            " from graph vertices."
        )
      if course not in graph[neighbor]:
        raise ValueError(
            f"Graph is asymmetric: '{course}' lists '{neighbor}', but"
            f" '{neighbor}' does not list '{course}' back."
        )


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
          f"Could not fit '{v}' into any available slots "
          f"({days} days x {slots_per_day} slots/day). "
          f"Increase DAYS or SLOTS_PER_DAY."
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


# ============================================================
# INITIALIZE BLANK SESSION STATE
# ============================================================
if "graph" not in st.session_state:
  st.session_state["graph"] = {}

if "toughness" not in st.session_state:
  st.session_state["toughness"] = {}

# ============================================================
# STREAMLIT USER INTERFACE DESIGN
# ============================================================

st.title("🎓 Toughness-Aware Exam Scheduler")
st.markdown(
    "Add courses, update their toughness dynamically, manage conflicts, and"
    " generate optimal timetables."
)

with st.sidebar:
  st.header("⚙️ Scheduler Controls")
  days = st.slider("Total Exam Days", min_value=1, max_value=30, value=5)
  slots_per_day = st.selectbox("Slots per Day", options=[1, 2, 3], index=1)
  min_gap = st.slider(
      "Minimum Slot Gap Between Conflicting Exams",
      min_value=1,
      max_value=3,
      value=1,
  )
  load_penalty = st.slider(
      "Daily Crowding Penalty Weight", min_value=0.0, max_value=5.0, value=2.0, step=0.5
  )

  total_slots = days * slots_per_day
  slot_names = ["FN", "AN", "Eve"][:slots_per_day]

  st.markdown("---")
  st.header("➕ Add New Course")

  with st.form("add_course_form", clear_on_submit=True):
    new_code = st.text_input("Course Code (e.g., CS101)").strip().upper()
    new_toughness = st.slider("Toughness Level (1 - 5)", 1, 5, 3)

    existing_courses = list(st.session_state["graph"].keys())
    new_conflicts = st.multiselect(
        "Conflicting Courses (Shared Students)", existing_courses
    )

    submitted = st.form_submit_button("Add Course")

    if submitted:
      if not new_code:
        st.error("Please enter a valid course code.")
      elif new_code in st.session_state["graph"]:
        st.error(f"Course '{new_code}' already exists.")
      else:
        st.session_state["graph"][new_code] = new_conflicts
        st.session_state["toughness"][new_code] = new_toughness

        for neighbor in new_conflicts:
          if new_code not in st.session_state["graph"][neighbor]:
            st.session_state["graph"][neighbor].append(new_code)

        st.success(f"Added course '{new_code}' successfully!")
        st.rerun()

  # --- EDIT EXISTING COURSE SECTION ---
  if st.session_state["graph"]:
    st.markdown("---")
    st.header("✏️ Edit Existing Course")

    with st.form("edit_course_form"):
      edit_code = st.selectbox(
          "Select Course to Edit", list(st.session_state["graph"].keys())
      )
      current_toughness = st.session_state["toughness"].get(edit_code, 3)
      edit_toughness = st.slider(
          "New Toughness Level (1 - 5)", 1, 5, int(current_toughness)
      )

      edit_submitted = st.form_submit_button("Update Toughness")

      if edit_submitted:
        st.session_state["toughness"][edit_code] = edit_toughness
        st.success(
            f"Updated toughness for '{edit_code}' to {edit_toughness}!"
        )
        st.rerun()

    st.markdown("---")
    if st.button("🗑️ Clear All Courses"):
      st.session_state["graph"] = {}
      st.session_state["toughness"] = {}
      st.rerun()

  st.markdown("---")
  st.info(
      f"**Available Slots:** {total_slots} ({days} Days × {slots_per_day}"
      f" slots/day)\n\n**Total Added Courses:** {len(st.session_state['graph'])}"
  )

# ============================================================
# MAIN CONTENT / GENERATION
# ============================================================
graph_data = st.session_state["graph"]
toughness_data = st.session_state["toughness"]

if not graph_data:
  st.info(
      "👈 Use the sidebar to start adding courses and their conflict"
      " relationships!"
  )
else:
  try:
    color, schedule, total_stress = toughness_aware_schedule(
        graph_data, toughness_data, days, slots_per_day, min_gap, load_penalty
    )
    valid = verify_schedule(graph_data, color, min_gap)

    # Status metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Courses", len(graph_data))
    col2.metric("Total Slots Used", total_slots)
    col3.metric("Total Local Stress", f"{total_stress:.2f}")
    col4.metric("Schedule Status", "✅ VALID" if valid else "❌ INVALID")

    st.markdown("---")

    table_data = []
    for course in sorted(color.keys()):
      slot_num = color[course]
      day = (slot_num - 1) // slots_per_day + 1
      slot_in_day = (slot_num - 1) % slots_per_day
      slot_name = slot_names[slot_in_day]
      table_data.append({
          "Course Code": course,
          "Semester": get_semester(course) if get_semester(course) else "N/A",
          "Day": f"Day {day}",
          "Slot": slot_name,
          "Slot ID": slot_num,
          "Toughness (1-5)": toughness_data[course],
          "Conflicts With": (
              ", ".join(graph_data[course]) if graph_data[course] else "None"
          ),
      })

    df = pd.DataFrame(table_data)

    tab1, tab2, tab3 = st.tabs([
        "📅 Timetable Matrix",
        "📋 Detailed Course List",
        "📊 Graph Data Structure",
    ])

    with tab1:
      st.subheader("Day-by-Day Slot Matrix Calendar")
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
      matrix_df = pd.DataFrame(matrix_rows)
      st.dataframe(matrix_df, use_container_width=True, hide_index=True)

    with tab2:
      st.subheader("Assigned Exam Schedule")
      st.dataframe(
          df.sort_values(by=["Slot ID", "Course Code"]),
          use_container_width=True,
          hide_index=True,
      )

    with tab3:
      st.subheader("Current Graph Adjacency & Toughness State")
      raw_list = []
      for c in graph_data:
        raw_list.append({
            "Course": c,
            "Toughness": toughness_data[c],
            "Neighbors (Conflicts)": ", ".join(graph_data[c]),
        })
      st.dataframe(
          pd.DataFrame(raw_list), use_container_width=True, hide_index=True
      )

  except RuntimeError as e:
    st.error(f"⚠️ **Scheduling Failed:** {e}")
    st.warning(
        "Try increasing the number of **Days** or **Slots per Day** in the"
        " sidebar, or relax conflict constraints."
    )
