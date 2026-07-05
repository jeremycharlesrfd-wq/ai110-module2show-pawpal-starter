"""Demo script for the PawPal+ system.

Creates an owner with two pets, adds tasks *out of order* with explicit clock
times, then exercises the Scheduler's sort_by_time() and filter_tasks() methods
so you can confirm the ordering and filtering behave correctly in the terminal.
"""

from pawpal_system import Owner, Pet, Task, priority_label


def format_task(task: Task, pets_by_id: dict[str, Pet]) -> str:
    """Render one task as a single schedule line."""
    pet = pets_by_id.get(task.pet_id)
    pet_name = pet.name if pet else "Unknown"
    status = "done" if task.completion else "todo"
    time = task.time or "--:--"
    return (
        f"  {time} — {task.category} ({task.length} min) "
        f"for {pet_name} [priority: {priority_label(task.priority_level)}, {status}]"
    )


def print_section(title: str, tasks: list[Task], pets_by_id: dict[str, Pet]) -> None:
    """Print a titled block of task lines."""
    print("=" * 60)
    print(title)
    print("=" * 60)
    if not tasks:
        print("  (no matching tasks)")
    for task in tasks:
        print(format_task(task, pets_by_id))
    print()


def main() -> None:
    """Run the terminal demo: build a jumbled schedule, then sort/filter it.

    Sets up an owner with two pets and deliberately out-of-order, double-booked
    tasks, then walks through the Scheduler's algorithmic methods —
    ``sort_by_time`` (chronological ordering), ``filter_tasks`` (by completion
    status and pet name), and ``detect_conflicts`` (same-slot warnings) — printing
    each result so the ordering, filtering, and conflict detection are visible.
    """
    # Create an owner with two pets.
    owner = Owner(id="o1", name="Jeremy")
    rex = Pet(id="p1", name="Rex", breed="Labrador")
    rex.add_special_needs("daily medication")
    milo = Pet(id="p2", name="Milo", breed="Tabby Cat")
    owner.add_pet(rex)
    owner.add_pet(milo)

    # Add tasks OUT OF ORDER (times are deliberately jumbled) so the sort has
    # something real to do. Feeding is a must-do meal.
    groom = Task(id="t3", category="Grooming", length=30, priority_level=1, time="11:15")
    walk = Task(id="t1", category="Morning walk", length=45, priority_level=2, time="08:00")
    feed = Task(
        id="t2", category="Feeding", length=10, priority_level=3,
        mandatory=True, time="09:30",
    )
    play = Task(id="t4", category="Playtime", length=20, priority_level=1, time="10:00")
    # Deliberately double-booked at 08:00 (same slot as Rex's walk) to exercise
    # the Scheduler's conflict detection — Milo's vet call clashes with the walk.
    vet_call = Task(id="t5", category="Vet call", length=15, priority_level=2, time="08:00")

    rex.add_task(groom)   # 11:15
    rex.add_task(walk)    # 08:00
    milo.add_task(feed)   # 09:30
    milo.add_task(play)   # 10:00
    milo.add_task(vet_call)  # 08:00 — collides with Rex's walk

    # Feeding already happened this morning — mark it done to show the filter.
    feed.mark_complete()

    # Pull the pets' tasks into the scheduler in their (unsorted) insertion order.
    scheduler = owner.scheduler
    scheduler.create_new_schedule()
    pets_by_id = {pet.id: pet for pet in owner.pets}

    # 1. Raw insertion order — deliberately not chronological.
    print_section("As added (insertion order)", scheduler.view_schedule(), pets_by_id)

    # 2. Sorted by clock time using the new sort_by_time().
    print_section("Sorted by time", scheduler.sort_by_time(), pets_by_id)

    # 3. Filter by completion status.
    print_section(
        "Filter: completed tasks",
        scheduler.filter_tasks(completed=True),
        pets_by_id,
    )
    print_section(
        "Filter: remaining (incomplete) tasks",
        scheduler.filter_tasks(completed=False),
        pets_by_id,
    )

    # 4. Filter by pet name (case-insensitive).
    print_section(
        "Filter: Rex's tasks",
        scheduler.filter_tasks(pet_name="rex"),
        pets_by_id,
    )

    # 5. Lightweight conflict detection — warns on same-time tasks without crashing.
    print("=" * 60)
    print("Schedule conflicts")
    print("=" * 60)
    conflicts = scheduler.detect_conflicts()
    if not conflicts:
        print("  (no conflicts — every task has its own slot)")
    for warning in conflicts:
        print(f"  {warning}")
    print()


if __name__ == "__main__":
    main()
