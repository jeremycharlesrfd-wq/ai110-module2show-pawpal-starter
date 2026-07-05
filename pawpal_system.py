"""PawPal+ system skeleton.

Class stubs generated from the UML class diagram (diagrams/diagrams/uml_draft.mmd).
Data-holding entities use dataclasses; Scheduler holds behavior over tasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

# How far ahead each recurrence rolls the due date. timedelta lets us add a
# span to a date and get back a real calendar date — it handles month and year
# boundaries for us (e.g. Dec 31 + 1 day → Jan 1), which naive arithmetic won't.
RECURRENCE_STEP = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),  # weeks=1 is exactly timedelta(days=7)
}


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
    # Clock time (HH:MM) this task is scheduled for. None until a plan assigns one.
    time: str | None = None
    # Must-do tasks (e.g. medication, feeding) are scheduled before the time
    # budget is applied so they are never silently dropped to fit optional work.
    mandatory: bool = False
    # Back-reference to the pet this task is required for (UML: Pet "1" --> "*" Task).
    pet_id: str | None = None
    # How often this task repeats: "daily", "weekly", or None for a one-off.
    recurrence: str | None = None
    # Calendar date this task is due. None means "not scheduled to a day yet".
    due_date: date | None = None

    def set_mandatory(self, value: bool = True) -> None:
        """Flag (or unflag) this task as a must-do that bypasses the time budget."""
        self.mandatory = value

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

    def next_due_date(self, *, from_date: date | None = None) -> date | None:
        """Return the due date for this task's next occurrence, or None if one-off.

        The recurrence maps to a ``timedelta`` step (1 day for "daily", 1 week
        for "weekly"), which we add to a base date. Adding a timedelta to a date
        returns a new date and rolls over month/year boundaries automatically —
        that's why it's more accurate than doing your own day arithmetic. We base
        it on ``from_date`` (defaulting to today), so a task completed "Daily"
        lands on today + 1 day.
        """
        step = RECURRENCE_STEP.get(self.recurrence or "")
        if step is None:
            return None
        base = from_date or date.today()
        return base + step

    def spawn_next(self) -> "Task | None":
        """Build a fresh, incomplete copy of this task for its next occurrence.

        Returns None for non-recurring tasks. The clone keeps the same category,
        length, priority, and pet, but resets completion and advances the due
        date. Its id embeds the new date so repeated completions stay unique.
        """
        next_due = self.next_due_date()
        if next_due is None:
            return None
        base_id = self.id.split("@", 1)[0]
        return Task(
            id=f"{base_id}@{next_due.isoformat()}",
            category=self.category,
            length=self.length,
            priority_level=self.priority_level,
            completion=False,
            time=self.time,
            mandatory=self.mandatory,
            pet_id=self.pet_id,
            recurrence=self.recurrence,
            due_date=next_due,
        )

    def mark_complete(self) -> "Task | None":
        """Mark the task as completed, returning the next occurrence if it recurs.

        For a "daily"/"weekly" task this hands back a fresh Task for the next day
        or week; for a one-off it returns None. Attaching that successor to the
        pet is the caller's job — see ``Scheduler.complete_task``.
        """
        self.completion = True
        return self.spawn_next()

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

    def complete_task(self, task: Task) -> Task | None:
        """Mark a task done and auto-enroll its next occurrence if it recurs.

        Marking complete may spawn a successor (for "daily"/"weekly" tasks). We
        attach that successor to the same pet — pets own their tasks, so the
        next occurrence flows into every future ``create_new_schedule`` — and
        also drop it into the current schedule list. Returns the new task, or
        None for a one-off.
        """
        next_task = task.mark_complete()
        if next_task is None:
            return None

        # Re-enroll on the owning pet so the recurrence survives a rebuild.
        pets = self.owner.pets if self.owner else []
        for pet in pets:
            if pet.id == next_task.pet_id:
                pet.add_task(next_task)
                break

        self.add_task(next_task)
        return next_task

    def filter_tasks(
        self, *, completed: bool | None = None, pet_name: str | None = None
    ) -> list[Task]:
        """Return scheduled tasks narrowed by completion status and/or pet name.

        Both filters are optional and combine with AND — pass neither to get every
        task, or both to get e.g. only the finished tasks for one pet:

            scheduler.filter_tasks(completed=True)          # done tasks
            scheduler.filter_tasks(pet_name="Rex")          # Rex's tasks
            scheduler.filter_tasks(completed=False, pet_name="Rex")

        Pet names are matched case-insensitively via the owner's pets, since tasks
        only carry a ``pet_id``. An unknown pet name simply yields no tasks.
        """
        # Resolve the pet name to its id up front so we compare ids, not names.
        pet_id = None
        if pet_name is not None:
            pets = self.owner.pets if self.owner else []
            match = next(
                (pet for pet in pets if pet.name.lower() == pet_name.lower()), None
            )
            if match is None:
                return []
            pet_id = match.id

        return [
            task
            for task in self.tasks
            if (completed is None or task.completion == completed)
            and (pet_id is None or task.pet_id == pet_id)
        ]

    def sort_by_time(self) -> list[Task]:
        """Return the scheduled tasks ordered by their HH:MM ``time``, earliest first.

        Zero-padded "HH:MM" strings already sort chronologically as plain text
        ("08:00" < "09:30" < "11:15"), so we sort on the raw string and skip
        parsing. Tasks with no time yet (``time is None``) get the sentinel
        "99:99" — above any real clock value — so they land at the end.
        """
        return sorted(self.tasks, key=lambda task: task.time or "99:99")

    @staticmethod
    def _order_key(task: Task) -> tuple:
        """Sort tasks by priority, then group same-pet tasks, then shortest first.

        Grouping by ``pet_id`` clusters a pet's tasks together so the owner isn't
        bouncing between animals mid-schedule.
        """
        return (-task.priority_level, task.pet_id or "", task.length)

    def prioritize_tasks(self) -> list[Task]:
        """Order incomplete tasks by priority, fitting them into available hours.

        Mandatory tasks (e.g. medication) are always included first, then optional
        tasks are added by priority — highest first, same-pet tasks grouped, then
        shortest — while the running total stays within the owner's available_hours
        (in minutes). Optional tasks that don't fit are dropped.
        """
        self.create_new_schedule()

        pending = [task for task in self.tasks if not task.completion]

        mandatory = sorted(
            (task for task in pending if task.mandatory), key=self._order_key
        )
        optional = sorted(
            (task for task in pending if not task.mandatory), key=self._order_key
        )

        available_minutes = (self.owner.available_hours * 60) if self.owner else None
        if available_minutes is None:
            return mandatory + optional

        # Must-do tasks are scheduled unconditionally, even if they overrun the
        # budget; optional tasks only fill whatever time is left.
        scheduled: list[Task] = list(mandatory)
        remaining = available_minutes - sum(task.length for task in mandatory)
        for task in optional:
            if task.length <= remaining:
                scheduled.append(task)
                remaining -= task.length
        return scheduled

    def _pet_name(self, pet_id: str | None) -> str:
        """Resolve a task's ``pet_id`` to its pet name for readable warnings."""
        pets = self.owner.pets if self.owner else []
        match = next((pet for pet in pets if pet.id == pet_id), None)
        return match.name if match else "Unknown pet"

    def detect_conflicts(self) -> list[str]:
        """Flag tasks that share the same start time, returning warnings not errors.

        This is a *lightweight* check: it groups the scheduled tasks by their
        exact ``time`` (HH:MM) and warns whenever two or more land on the same
        clock slot — whether they belong to the same pet or different pets.
        Tasks with no time assigned yet (``time is None``) are ignored, since an
        unscheduled task can't collide with anything.

        Nothing is raised or mutated: the caller gets back a list of human-readable
        warning strings (empty when the day is conflict-free) and decides what to
        do with them, so a double-booking never crashes the program.
        """
        by_time: dict[str, list[Task]] = {}
        for task in self.tasks:
            if task.time is None:
                continue
            by_time.setdefault(task.time, []).append(task)

        warnings: list[str] = []
        # Sort by clock time so warnings read top-to-bottom through the day.
        for time in sorted(by_time):
            clashing = by_time[time]
            if len(clashing) < 2:
                continue
            details = ", ".join(
                f"{task.category} ({self._pet_name(task.pet_id)})" for task in clashing
            )
            warnings.append(
                f"⚠️  Conflict at {time}: {len(clashing)} tasks overlap — {details}"
            )
        return warnings

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
