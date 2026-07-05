"""Tests for the PawPal+ system."""

from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


# ---------------------------------------------------------------------------
# Existing behavior: task completion and attachment
# ---------------------------------------------------------------------------
def test_mark_complete_changes_status():
    """Task Completion: mark_complete() flips the task's status to complete."""
    task = Task(id="t1", category="walk", length=30, priority_level=2)
    assert task.completion is False

    task.mark_complete()

    assert task.completion is True


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet increases that pet's task count."""
    pet = Pet(id="p1", name="Rex", breed="Labrador")
    assert len(pet.tasks) == 0

    task = Task(id="t1", category="feed", length=10, priority_level=1)
    pet.add_task(task)

    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Helper: wire an owner + pet + scheduler together
# ---------------------------------------------------------------------------
def _owner_with_pet(available_hours=24, available_from="08:00"):
    """Build an Owner with one pet, ready for scheduling assertions."""
    owner = Owner(id="o1", name="Sam", available_hours=available_hours)
    owner.set_available_from(available_from)
    pet = Pet(id="p1", name="Rex", breed="Labrador")
    owner.add_pet(pet)
    return owner, pet


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------
def test_sort_by_time_returns_chronological_order():
    """Sorting: tasks come back earliest-first regardless of insertion order."""
    scheduler = Scheduler()
    scheduler.add_task(Task(id="a", category="walk", length=30, priority_level=1, time="11:15"))
    scheduler.add_task(Task(id="b", category="feed", length=10, priority_level=1, time="08:00"))
    scheduler.add_task(Task(id="c", category="med", length=5, priority_level=1, time="09:30"))

    ordered = scheduler.sort_by_time()

    assert [t.time for t in ordered] == ["08:00", "09:30", "11:15"]


def test_sort_by_time_puts_unscheduled_tasks_last():
    """Sorting: tasks with no time (None) sort after every real clock time."""
    scheduler = Scheduler()
    scheduler.add_task(Task(id="a", category="walk", length=30, priority_level=1, time=None))
    scheduler.add_task(Task(id="b", category="feed", length=10, priority_level=1, time="08:00"))

    ordered = scheduler.sort_by_time()

    assert [t.id for t in ordered] == ["b", "a"]


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------
def test_daily_task_complete_creates_task_for_next_day():
    """Recurrence: completing a daily task spawns a fresh task due tomorrow."""
    today = date.today()
    task = Task(
        id="walk",
        category="walk",
        length=30,
        priority_level=2,
        recurrence="daily",
        due_date=today,
    )

    successor = task.mark_complete()

    assert task.completion is True
    assert successor is not None
    assert successor.completion is False
    assert successor.due_date == today + timedelta(days=1)
    assert successor.category == "walk"


def test_weekly_task_complete_creates_task_for_next_week():
    """Recurrence: a weekly task advances the due date by 7 days."""
    today = date.today()
    task = Task(id="bath", category="bath", length=45, priority_level=1, recurrence="weekly")

    successor = task.mark_complete()

    assert successor is not None
    assert successor.due_date == today + timedelta(weeks=1)


def test_one_off_task_complete_returns_none():
    """Recurrence: a non-recurring task has no successor."""
    task = Task(id="vet", category="vet", length=60, priority_level=3)

    assert task.mark_complete() is None


def test_successor_id_does_not_compound_across_completions():
    """Recurrence: repeated completions keep the id as base@date, not base@d1@d2."""
    task = Task(id="walk", category="walk", length=30, priority_level=2, recurrence="daily")

    gen2 = task.mark_complete()
    gen3 = gen2.mark_complete()

    assert gen2.id.count("@") == 1
    assert gen3.id.count("@") == 1
    assert gen3.id.split("@", 1)[0] == "walk"


def test_complete_task_reenrolls_successor_and_survives_rebuild():
    """Recurrence: complete_task attaches the successor to the pet so it
    survives a create_new_schedule rebuild."""
    owner, pet = _owner_with_pet()
    task = Task(id="walk", category="walk", length=30, priority_level=2, recurrence="daily")
    pet.add_task(task)
    owner.scheduler.create_new_schedule()

    successor = owner.scheduler.complete_task(task)

    assert successor in pet.tasks  # re-enrolled on the pet, not just the list
    owner.scheduler.create_new_schedule()
    assert successor in owner.scheduler.tasks


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------
def test_detect_conflicts_flags_two_tasks_at_same_time():
    """Conflict: two tasks sharing a clock slot produce exactly one warning."""
    owner, pet = _owner_with_pet()
    pet.add_task(Task(id="a", category="walk", length=30, priority_level=1, time="08:00"))
    pet.add_task(Task(id="b", category="feed", length=10, priority_level=1, time="08:00"))
    owner.scheduler.create_new_schedule()

    warnings = owner.scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_detect_conflicts_counts_three_overlapping_tasks():
    """Conflict: three tasks at one slot still give one warning, count = 3."""
    owner, pet = _owner_with_pet()
    for i in range(3):
        pet.add_task(Task(id=f"t{i}", category="c", length=5, priority_level=1, time="09:00"))
    owner.scheduler.create_new_schedule()

    warnings = owner.scheduler.detect_conflicts()

    assert len(warnings) == 1
    assert "3 tasks" in warnings[0]


def test_detect_conflicts_ignores_unscheduled_and_distinct_times():
    """Conflict: distinct times and None-time tasks never clash."""
    owner, pet = _owner_with_pet()
    pet.add_task(Task(id="a", category="walk", length=30, priority_level=1, time="08:00"))
    pet.add_task(Task(id="b", category="feed", length=10, priority_level=1, time="09:00"))
    pet.add_task(Task(id="c", category="play", length=15, priority_level=1, time=None))
    owner.scheduler.create_new_schedule()

    assert owner.scheduler.detect_conflicts() == []


# ---------------------------------------------------------------------------
# Prioritization / budget edge cases
# ---------------------------------------------------------------------------
def test_mandatory_tasks_scheduled_even_when_over_budget():
    """Budget: mandatory tasks are kept even if they alone exceed the hours;
    no optional task fits once time is overrun."""
    owner, pet = _owner_with_pet(available_hours=1)  # 60 minutes
    must = Task(id="med", category="med", length=90, priority_level=3, mandatory=True)
    optional = Task(id="walk", category="walk", length=10, priority_level=2)
    pet.add_task(must)
    pet.add_task(optional)

    scheduled = owner.scheduler.prioritize_tasks()

    assert must in scheduled
    assert optional not in scheduled


def test_optional_tasks_fill_remaining_budget():
    """Budget: optional tasks are added by priority until the budget is spent."""
    owner, pet = _owner_with_pet(available_hours=1)  # 60 minutes
    pet.add_task(Task(id="a", category="a", length=40, priority_level=3))
    pet.add_task(Task(id="b", category="b", length=15, priority_level=2))
    pet.add_task(Task(id="c", category="c", length=30, priority_level=1))
    scheduled = owner.scheduler.prioritize_tasks()

    ids = {t.id for t in scheduled}
    assert ids == {"a", "b"}  # 40 + 15 = 55 <= 60; c (30) no longer fits


def test_completed_tasks_excluded_from_prioritization():
    """Budget: already-completed tasks are dropped from the plan."""
    owner, pet = _owner_with_pet(available_hours=24)
    done = Task(id="done", category="walk", length=30, priority_level=2, completion=True)
    pending = Task(id="todo", category="feed", length=10, priority_level=2)
    pet.add_task(done)
    pet.add_task(pending)

    scheduled = owner.scheduler.prioritize_tasks()

    assert done not in scheduled
    assert pending in scheduled


# ---------------------------------------------------------------------------
# Daily plan layout
# ---------------------------------------------------------------------------
def test_build_daily_plan_lays_tasks_back_to_back():
    """Plan: each task starts when the previous ends, from available_from."""
    owner, pet = _owner_with_pet(available_hours=24, available_from="08:00")
    pet.add_task(Task(id="a", category="a", length=30, priority_level=3))
    pet.add_task(Task(id="b", category="b", length=45, priority_level=2))
    pet.add_task(Task(id="c", category="c", length=15, priority_level=1))

    plan = owner.scheduler.build_daily_plan()

    times = [slot for slot, _ in plan]
    assert times == ["08:00", "08:30", "09:15"]


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------
def test_filter_tasks_combines_completed_and_pet_name():
    """Filter: completed + pet_name combine with AND, case-insensitively."""
    owner, pet = _owner_with_pet()
    done = Task(id="done", category="walk", length=30, priority_level=2, completion=True)
    pending = Task(id="todo", category="feed", length=10, priority_level=2)
    pet.add_task(done)
    pet.add_task(pending)
    owner.scheduler.create_new_schedule()

    result = owner.scheduler.filter_tasks(completed=True, pet_name="rex")

    assert result == [done]


def test_filter_tasks_unknown_pet_returns_empty():
    """Filter: an unknown pet name yields no tasks (not all tasks)."""
    owner, pet = _owner_with_pet()
    pet.add_task(Task(id="t", category="feed", length=10, priority_level=1))
    owner.scheduler.create_new_schedule()

    assert owner.scheduler.filter_tasks(pet_name="Ghost") == []


# ---------------------------------------------------------------------------
# Empty / no-task edge cases
# ---------------------------------------------------------------------------
def test_pet_with_no_tasks_produces_empty_plan():
    """Edge: a pet with no tasks schedules nothing and never crashes."""
    owner, _pet = _owner_with_pet()

    assert owner.scheduler.prioritize_tasks() == []
    assert owner.scheduler.build_daily_plan() == []
    assert owner.scheduler.detect_conflicts() == []
