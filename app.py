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

if st.button("Add task"):
    task = Task(
        id=task_title,
        category=task_title,
        length=int(duration),
        priority_level=PRIORITY_LEVELS[priority],
        mandatory=mandatory,
    )
    # Mutates the Pet living in the vault → persists across re-runs.
    pet.add_task(task)

if pet.tasks:
    st.write("Current tasks:")
    st.table(
        [
            {
                "title": t.category,
                "duration_minutes": t.length,
                "priority": priority_label(t.priority_level),
                "must_do": t.mandatory,
                "done": t.completion,
            }
            for t in pet.tasks
        ]
    )
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

    # Resolve each task's pet_id back to a readable pet name for the table.
    pet_names = {p.id: p.name for p in owner.pets}

    if plan:
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
