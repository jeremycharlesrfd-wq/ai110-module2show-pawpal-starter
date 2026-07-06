from datetime import datetime

import streamlit as st

from pawpal_system import Task, Pet, Owner, Scheduler, priority_label

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs")
owner_name = st.text_input("Owner name", value="Jordan")

# --- Session vault: build the Owner exactly ONCE ---
# The script re-runs on every interaction, so we guard creation with an
# `in` check. On later re-runs this block is skipped and the existing
# object — with all its pets and tasks — is preserved.
if "owner" not in st.session_state:
    owner = Owner(id="owner-1", name=owner_name)
    owner.add_pet(Pet(id="pet-1", name="Mochi", breed="dog"))
    st.session_state.owner = owner
    # Monotonic counter so every added pet gets a unique id.
    st.session_state.pet_count = 1

# Fetch the SAME persisted object to read/mutate on this run.
owner = st.session_state.owner
owner.modify_name(owner_name)  # keep the owner's name synced each re-run

# Map the UI's priority labels to the numeric levels Task expects.
PRIORITY_LEVELS = {"low": 1, "medium": 2, "high": 3}

st.markdown("### Pets")

# "Add a Pet" component → owner.add_pet(...). A form batches the inputs so we
# only mutate the vault when the button is pressed.
with st.form("add_pet", clear_on_submit=True):
    new_pet_name = st.text_input("Pet name", value="")
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet") and new_pet_name.strip():
        st.session_state.pet_count += 1
        owner.add_pet(
            Pet(
                id=f"pet-{st.session_state.pet_count}",
                name=new_pet_name.strip(),
                breed=new_pet_species,
            )
        )

# Pick the active pet; the task controls below operate on this one.
pet = st.selectbox(
    "Active pet",
    options=owner.pets,
    format_func=lambda p: f"{p.name} ({p.breed})",
)

st.markdown("### Tasks")
st.caption(f"Tasks you add here attach to **{pet.name}** and feed the scheduler.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

mandatory = st.checkbox(
    "Must-do (schedule even if time runs short)",
    help="Medication, feeding, and other tasks that should never be dropped to fit the time budget.",
)

preferred_time = st.text_input(
    "Preferred start time (HH:MM, optional)",
    value="",
    help="Pin this task to a clock time. If two tasks want the same slot, "
    "PawPal+ will flag the conflict when you build the schedule.",
)

if st.button("Add task"):
    # Validate the optional time up front so a typo surfaces here, not deep in
    # the scheduler. Empty means "no preference" — leave time as None.
    pinned_time = None
    if preferred_time.strip():
        try:
            datetime.strptime(preferred_time.strip(), "%H:%M")
            pinned_time = preferred_time.strip()
        except ValueError:
            st.error("Preferred start time must be in HH:MM format (e.g. 09:30).")

    if not preferred_time.strip() or pinned_time is not None:
        task = Task(
            id=task_title,
            category=task_title,
            length=int(duration),
            priority_level=PRIORITY_LEVELS[priority],
            mandatory=mandatory,
            time=pinned_time,
        )
        # Mutates the Pet living in the vault → persists across re-runs.
        pet.add_task(task)

st.markdown("### Current tasks")

# Sync the scheduler's task list with every pet's current tasks so the
# filter/sort methods below read live data (they operate on scheduler.tasks).
scheduler = owner.scheduler
scheduler.create_new_schedule()

if scheduler.tasks:
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        pet_filter = st.selectbox(
            "Filter by pet", options=["All pets"] + [p.name for p in owner.pets]
        )
    with fcol2:
        status_filter = st.selectbox("Filter by status", ["All", "To do", "Done"])

    # Translate the UI choices into the keyword args Scheduler.filter_tasks expects.
    completed = {"All": None, "To do": False, "Done": True}[status_filter]
    pet_name = None if pet_filter == "All pets" else pet_filter

    # Filter and sort using the Scheduler's own methods: sort_by_time() gives the
    # canonical chronological order, and we keep only the tasks that pass the
    # filter (matched by identity so duplicate titles don't collide).
    matching = {id(t) for t in scheduler.filter_tasks(completed=completed, pet_name=pet_name)}
    visible = [t for t in scheduler.sort_by_time() if id(t) in matching]

    pet_names = {p.id: p.name for p in owner.pets}
    if visible:
        st.table(
            [
                {
                    "time": t.time or "—",
                    "pet": pet_names.get(t.pet_id, "—"),
                    "task": t.category,
                    "duration_minutes": t.length,
                    "priority": priority_label(t.priority_level),
                    "must_do": t.mandatory,
                    "done": t.completion,
                }
                for t in visible
            ]
        )
    else:
        st.info("No tasks match this filter.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Set the owner's availability, then generate a prioritized daily plan.")

avail_hours = st.number_input("Available hours today", min_value=0, max_value=24, value=2)
avail_from = st.text_input("Available from (HH:MM)", value="08:00")

if st.button("Generate schedule"):
    # Push the availability constraints onto the persisted Owner...
    owner.set_availability(int(avail_hours))
    owner.set_available_from(avail_from)

    # ...then let the Scheduler prioritize and lay tasks out back-to-back.
    # The plan spans ALL of the owner's pets (Scheduler._collect_owner_tasks).
    plan = owner.scheduler.build_daily_plan()

    # Ask the Scheduler to flag any double-booked slots among the pinned
    # preferred times. build_daily_plan() already refreshed scheduler.tasks.
    conflicts = owner.scheduler.detect_conflicts()

    # Conflicts come FIRST: a double-booking is the one thing a pet owner must
    # act on, so we surface it before the plan rather than burying it below.
    # It's a warning, not an error — the plan is still shown so the day isn't
    # blocked, and we point to a concrete fix instead of just naming the clash.
    if conflicts:
        st.warning(f"⚠️ {len(conflicts)} time conflict(s) need your attention:")
        for warning in conflicts:
            st.markdown(f"- {warning}")
        st.caption(
            "Fix a conflict by staggering the tasks' preferred start times, or by "
            "marking the essential one as must-do so it's placed first."
        )

    # Resolve each task's pet_id back to a readable pet name for the table.
    pet_names = {p.id: p.name for p in owner.pets}

    if plan:
        if not conflicts:
            st.success(
                f"✅ Planned {len(plan)} task(s) starting at {owner.available_from} — "
                "no conflicts."
            )
        st.table(
            [
                {
                    "time": time_str,
                    "pet": pet_names.get(task.pet_id, "—"),
                    "task": task.category,
                    "minutes": task.length,
                    "priority": priority_label(task.priority_level),
                }
                for time_str, task in plan
            ]
        )
    else:
        st.info(
            "No tasks fit the available time. Add tasks or increase available hours."
        )
