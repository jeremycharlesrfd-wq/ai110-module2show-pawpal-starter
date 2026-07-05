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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

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