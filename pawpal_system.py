"""PawPal+ system skeleton.

Class stubs generated from the UML class diagram (diagrams/diagrams/uml_draft.mmd).
Data-holding entities use dataclasses; Scheduler holds behavior over tasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta


def priority_label(level: int) -> str:
    """Map a numeric priority level to a human-readable label."""
    if level >= 3:
        return "high"
    if level == 2:
        return "medium"
    return "low"


@dataclass
class Task:
    id: str
    category: str
    length: int
    priority_level: int
    completion: bool = False
    # Back-reference to the pet this task is required for (UML: Pet "1" --> "*" Task).
    pet_id: str | None = None

    def assign_length(self, minutes: int) -> None:
        """Set the task's length in minutes, rejecting negative values."""
        if minutes < 0:
            raise ValueError("length must be non-negative")
        self.length = minutes

    def assign_priority_level(self, level: int) -> None:
        """Set the task's numeric priority level."""
        self.priority_level = level

    def assign_category(self, category: str) -> None:
        """Set the task's category."""
        self.category = category

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completion = True

    def mark_uncomplete(self) -> None:
        """Mark the task as not completed."""
        self.completion = False


@dataclass
class Pet:
    id: str
    name: str
    breed: str
    special_needs: list[str] = field(default_factory=list)
    # Tasks this pet requires (UML: Pet "1" --> "*" Task : requires).
    tasks: list[Task] = field(default_factory=list)

    def add_special_needs(self, need: str) -> None:
        """Add a special need to the pet, skipping duplicates."""
        if need not in self.special_needs:
            self.special_needs.append(need)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and sync its back-reference."""
        # Keep the back-reference in sync so the Scheduler can trace a task to its pet.
        task.pet_id = self.id
        if task not in self.tasks:
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Detach a task from this pet and clear its back-reference."""
        if task in self.tasks:
            self.tasks.remove(task)
            task.pet_id = None


@dataclass
class Owner:
    id: str
    name: str
    # Every owner has exactly one scheduler (UML: Owner "1" --> "1" Scheduler).
    scheduler: "Scheduler" = field(default_factory=lambda: Scheduler())
    pets: list[Pet] = field(default_factory=list)
    # Hours the owner has available for pet care; used by Scheduler.prioritize_tasks.
    available_hours: int = 0
    # Clock time (HH:MM) the owner is free to start pet care. Tasks are laid out
    # back-to-back from here by Scheduler.build_daily_plan.
    available_from: str = "08:00"

    def __post_init__(self) -> None:
        """Wire the scheduler's back-reference to this owner after init."""
        # Wire the back-reference so the Scheduler can reach this owner's pets and hours.
        self.scheduler.owner = self

    def modify_name(self, name: str) -> None:
        """Change the owner's name."""
        self.name = name

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner, skipping duplicates."""
        if pet not in self.pets:
            self.pets.append(pet)

    def remove_pet(self, pet: Pet) -> None:
        """Remove a pet from the owner if present."""
        if pet in self.pets:
            self.pets.remove(pet)

    def set_availability(self, hours: int) -> None:
        """Set the owner's available care hours, rejecting negative values."""
        if hours < 0:
            raise ValueError("available hours must be non-negative")
        self.available_hours = hours

    def set_available_from(self, time_str: str) -> None:
        """Set the owner's start time, validating the HH:MM format."""
        # Validate the HH:MM format up front so bad input fails loudly here
        # rather than deep inside the scheduler.
        datetime.strptime(time_str, "%H:%M")
        self.available_from = time_str


@dataclass
class Scheduler:
    tasks: list[Task] = field(default_factory=list)
    # Back-reference to the owning Owner; lets prioritize_tasks read available_hours
    # and reach each Pet's required tasks. Set when the scheduler is attached.
    owner: "Owner | None" = None

    def _collect_owner_tasks(self) -> list[Task]:
        """Flatten every task required by each of the owner's pets.

        This is the single source of truth: pets own their tasks, so the
        Scheduler reads through the owner back-reference rather than keeping a
        divergent copy.
        """
        if self.owner is None:
            return []
        return [task for pet in self.owner.pets for task in pet.tasks]

    def view_schedule(self) -> list[Task]:
        """Return a copy of the currently scheduled tasks."""
        return list(self.tasks)

    def delete_schedule(self) -> None:
        """Clear all scheduled tasks."""
        self.tasks = []

    def create_new_schedule(self) -> None:
        """Rebuild the schedule from the owner's pets' current tasks."""
        # Rebuild the schedule from the current state of the owner's pets.
        self.tasks = self._collect_owner_tasks()

    def add_task(self, task: Task) -> None:
        """Add a task to the schedule, skipping duplicates."""
        if task not in self.tasks:
            self.tasks.append(task)

    def prioritize_tasks(self) -> list[Task]:
        """Order incomplete tasks by priority, fitting them into available hours.

        Higher priority_level first, then shorter tasks. Tasks are included only
        while the running total stays within the owner's available_hours (in
        minutes); tasks that don't fit are dropped from the prioritized list.
        """
        self.create_new_schedule()

        pending = [task for task in self.tasks if not task.completion]
        pending.sort(key=lambda task: (-task.priority_level, task.length))

        available_minutes = (self.owner.available_hours * 60) if self.owner else None
        if available_minutes is None:
            return pending

        scheduled: list[Task] = []
        remaining = available_minutes
        for task in pending:
            if task.length <= remaining:
                scheduled.append(task)
                remaining -= task.length
        return scheduled

    def build_daily_plan(self) -> list[tuple[str, Task]]:
        """Lay prioritized tasks out back-to-back from the owner's free time.

        Returns (clock_time, task) pairs where each task starts when the
        previous one ends, beginning at the owner's ``available_from`` time.
        """
        prioritized = self.prioritize_tasks()

        start_str = self.owner.available_from if self.owner else "08:00"
        current = datetime.strptime(start_str, "%H:%M")

        plan: list[tuple[str, Task]] = []
        for task in prioritized:
            plan.append((current.strftime("%H:%M"), task))
            current += timedelta(minutes=task.length)
        return plan
