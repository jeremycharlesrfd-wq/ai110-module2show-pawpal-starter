# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
What time are you free to start? (HH:MM) [08:00] 10:00            
============================================
Today's Schedule for Jeremy (free from 10:00)
============================================
  10:00 — Feeding (10 min) for Rex [priority: high]
  10:10 — Morning walk (45 min) for Rex [priority: medium]
  10:55 — Grooming (30 min) for Milo [priority: low]
============================================
```

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## ✨ Features

The scheduling algorithms below live on the `Scheduler` and `Task` classes in [pawpal_system.py](pawpal_system.py):

- **Sorting by time** — [`Scheduler.sort_by_time()`](pawpal_system.py#L288) orders the day's tasks chronologically by their `HH:MM` start time. Zero-padded time strings sort correctly as plain text, and unscheduled tasks (no time yet) fall to the end via a `"99:99"` sentinel.
- **Priority-based scheduling within a time budget** — [`Scheduler.prioritize_tasks()`](pawpal_system.py#L307) selects and orders tasks by priority (high → low), groups same-pet tasks together, and breaks ties shortest-first, all while fitting them into the owner's `available_hours`. Optional tasks that don't fit are dropped.
- **Must-do (mandatory) task protection** — Tasks flagged `mandatory` (e.g. medication, feeding) are scheduled unconditionally *before* the time budget is applied, so essential care is never dropped to make room for optional work.
- **Daily plan builder** — [`Scheduler.build_daily_plan()`](pawpal_system.py#L379) lays prioritized tasks back-to-back starting from the owner's `available_from` time, returning `(clock_time, task)` pairs where each task begins when the previous one ends.
- **Conflict warnings** — [`Scheduler.detect_conflicts()`](pawpal_system.py#L346) groups tasks by exact start time and flags any slot with two or more tasks. It returns human-readable warnings rather than raising, so a double-booking never crashes the app.
- **Filtering** — [`Scheduler.filter_tasks()`](pawpal_system.py#L255) narrows the schedule by completion status and/or pet name (case-insensitive), combining both with AND logic.
- **Daily & weekly recurrence** — [`Task.next_due_date()`](pawpal_system.py#L67) and [`Task.spawn_next()`](pawpal_system.py#L83) roll a completed recurring task forward by one day or one week using `timedelta` (handling month/year boundaries automatically). [`Scheduler.complete_task()`](pawpal_system.py#L232) auto-enrolls the next occurrence on the pet so it survives a schedule rebuild.
- **Priority labeling** — [`priority_label()`](pawpal_system.py#L21) maps numeric levels to `high` / `medium` / `low` for readable output across the CLI and Streamlit UI.

## 📐 Smarter Scheduling

All scheduling logic lives on the `Scheduler` and `Task` classes in [pawpal_system.py](pawpal_system.py). Below is each feature we implemented and the method that powers it.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Chronological sorting | [`Scheduler.sort_by_time()`](pawpal_system.py#L288) | Orders scheduled tasks by their `HH:MM` time, earliest first; unscheduled tasks sink to the end |
| Priority sorting | [`Scheduler.prioritize_tasks()`](pawpal_system.py#L307), [`Scheduler._order_key()`](pawpal_system.py#L298) | Sorts by priority (high → low), groups same-pet tasks, then shortest first |
| Filtering | [`Scheduler.filter_tasks()`](pawpal_system.py#L255) | Filter by completion status and/or pet name; both are optional and combine with AND |
| Time-budget filtering | [`Scheduler.prioritize_tasks()`](pawpal_system.py#L307) | Optional tasks that don't fit the owner's `available_hours` are dropped; mandatory tasks are always kept |
| Conflict detection | [`Scheduler.detect_conflicts()`](pawpal_system.py#L346) | Groups tasks by exact start time and returns warning strings for overlaps (never raises) |
| Recurring tasks | [`Task.mark_complete()`](pawpal_system.py#L107), [`Task.spawn_next()`](pawpal_system.py#L83), [`Task.next_due_date()`](pawpal_system.py#L67), [`Scheduler.complete_task()`](pawpal_system.py#L232) | Completing a `daily`/`weekly` task spawns a fresh copy for the next occurrence and re-enrolls it on the pet |

## 📸 Demo Walkthrough

PawPal+ runs as a Streamlit web app (`app.py`) with a matching terminal demo (`main.py`). This section walks through what the app can do without needing to watch a video.

### Main UI features

The Streamlit app is organized top-to-bottom into a few sections:

- **Owner** — enter the owner's name. The `Owner` is created once and persisted in Streamlit's session state, so it (and its pets/tasks) survive every re-run.
- **Pets** — add pets with a name and species (dog / cat / other), then pick the *active pet* that new tasks attach to.
- **Tasks** — give a task a title, duration (minutes), and priority (low / medium / high). You can also mark a task **Must-do** (never dropped to fit the time budget) and pin an optional **preferred start time** (`HH:MM`, validated on entry).
- **Current tasks** — a live table of every task across all pets, with dropdowns to **filter by pet** and **filter by status** (To do / Done). The table is always shown in chronological order.
- **Build Schedule** — set the owner's *available hours* and *available from* time, then click **Generate schedule** to produce a prioritized, back-to-back daily plan with conflict warnings surfaced at the top.

### Example workflow

1. Enter the owner name (e.g. `Jordan`). A starter pet, *Mochi (dog)*, is created automatically.
2. In **Pets**, add another pet — say *Rex (dog)* — and select the pet you want to schedule for.
3. In **Tasks**, add a few tasks: a `Feeding` (10 min, high, must-do), a `Morning walk` (45 min, medium), and a `Grooming` (30 min, low). Optionally pin a preferred start time on any of them.
4. Scroll to **Current tasks** to confirm they appear, then use the filters to view just one pet's tasks or only the tasks still to do.
5. In **Build Schedule**, set *available hours* (e.g. `2`) and *available from* (e.g. `10:00`), then click **Generate schedule** to see today's plan.

### Key Scheduler behaviors shown

- **Chronological sorting** — the Current tasks table and the terminal demo both order tasks by their `HH:MM` start time (unscheduled tasks sink to the end).
- **Priority within a time budget** — the daily plan selects and orders tasks high → low priority, groups same-pet tasks, breaks ties shortest-first, and drops *optional* tasks that don't fit the owner's available hours.
- **Must-do protection** — tasks flagged must-do (medication, feeding) are always scheduled first, even if the time budget is exceeded.
- **Conflict warnings** — when two tasks share the same start time, PawPal+ shows a non-blocking `⚠️` warning above the plan (and prints one in the CLI) instead of crashing, with a suggested fix.
- **Filtering** — filter by completion status and/or pet name (case-insensitive), combined with AND logic.

### Sample CLI output

Running the terminal demo exercises sorting, filtering, and conflict detection on a deliberately jumbled, double-booked schedule:

```text
$ python3 main.py
============================================================
As added (insertion order)
============================================================
  11:15 — Grooming (30 min) for Rex [priority: low, todo]
  08:00 — Morning walk (45 min) for Rex [priority: medium, todo]
  09:30 — Feeding (10 min) for Milo [priority: high, done]
  10:00 — Playtime (20 min) for Milo [priority: low, todo]
  08:00 — Vet call (15 min) for Milo [priority: medium, todo]

============================================================
Sorted by time
============================================================
  08:00 — Morning walk (45 min) for Rex [priority: medium, todo]
  08:00 — Vet call (15 min) for Milo [priority: medium, todo]
  09:30 — Feeding (10 min) for Milo [priority: high, done]
  10:00 — Playtime (20 min) for Milo [priority: low, todo]
  11:15 — Grooming (30 min) for Rex [priority: low, todo]

============================================================
Filter: completed tasks
============================================================
  09:30 — Feeding (10 min) for Milo [priority: high, done]

============================================================
Filter: remaining (incomplete) tasks
============================================================
  11:15 — Grooming (30 min) for Rex [priority: low, todo]
  08:00 — Morning walk (45 min) for Rex [priority: medium, todo]
  10:00 — Playtime (20 min) for Milo [priority: low, todo]
  08:00 — Vet call (15 min) for Milo [priority: medium, todo]

============================================================
Filter: Rex's tasks
============================================================
  11:15 — Grooming (30 min) for Rex [priority: low, todo]
  08:00 — Morning walk (45 min) for Rex [priority: medium, todo]

============================================================
Schedule conflicts
============================================================
  ⚠️  Conflict at 08:00: 2 tasks overlap — Morning walk (Rex), Vet call (Milo)
```

## Testing PawPal+

Command to run tests: python3 -m pytest

====================================== test session starts =======================================
platform darwin -- Python 3.13.7, pytest-9.0.3, pluggy-1.6.0
rootdir: /Users/jeremycharlesrafidimanana/Documents/summer 26/codepath/Projects/ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collected 19 items                                                                               

tests/test_pawpal.py ...................                                                   [100%]

======================================= 19 passed in 0.01s =======================================

Description of what the tests cover: task completion/attachment, chronological sorting (incl. None times last), recurrence (daily/weekly spawn, one-off returns None, id doesn't compound, survives rebuild), conflict detection (duplicate times flagged), budget prioritization (mandatory kept over budget, completed excluded), back-to-back daily plan layout, filtering (AND, case-insensitive, unknown pet → []), and empty-pet edge cases.

Confidence level: ⭐️⭐️⭐️⭐️⭐️