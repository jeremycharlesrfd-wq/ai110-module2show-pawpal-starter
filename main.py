"""Demo script for the PawPal+ system.

Creates an owner with two pets, assigns tasks with different durations, then
prints "Today's Schedule" with real clock times starting from when the owner
is free.
"""

from pawpal_system import Owner, Pet, Task, priority_label


def main() -> None:
    # Create an owner, set how long they have, and when they are free to start.
    owner = Owner(id="o1", name="Jeremy")
    owner.set_availability(2)  # 2 hours == 120 minutes

    # Ask the user when they are free to start. Keep prompting until we get a
    # valid HH:MM, and fall back to 08:00 if they just press Enter.
    while True:
        when = input("What time are you free to start? (HH:MM) [08:00] ").strip()
        if not when:
            when = "08:00"
        try:
            owner.set_available_from(when)
            break
        except ValueError:
            print("  Please enter a time as HH:MM, e.g. 09:30.")

    # Create at least two pets.
    rex = Pet(id="p1", name="Rex", breed="Labrador")
    rex.add_special_needs("daily medication")

    milo = Pet(id="p2", name="Milo", breed="Tabby Cat")

    owner.add_pet(rex)
    owner.add_pet(milo)

    # Add at least three tasks with different durations (minutes).
    walk = Task(id="t1", category="Morning walk", length=45, priority_level=2)
    feed = Task(id="t2", category="Feeding", length=10, priority_level=3)
    groom = Task(id="t3", category="Grooming", length=30, priority_level=1)

    rex.add_task(walk)
    rex.add_task(feed)
    milo.add_task(groom)

    # Lay tasks out back-to-back from the owner's free time.
    plan = owner.scheduler.build_daily_plan()
    pets_by_id = {pet.id: pet for pet in owner.pets}

    # Print "Today's Schedule", each task at its assigned clock time.
    print("=" * 44)
    print(f"Today's Schedule for {owner.name} (free from {owner.available_from})")
    print("=" * 44)
    for time, task in plan:
        pet = pets_by_id.get(task.pet_id)
        pet_name = pet.name if pet else "Unknown"
        print(
            f"  {time} — {task.category} ({task.length} min) "
            f"for {pet_name} [priority: {priority_label(task.priority_level)}]"
        )
    print("=" * 44)


if __name__ == "__main__":
    main()
