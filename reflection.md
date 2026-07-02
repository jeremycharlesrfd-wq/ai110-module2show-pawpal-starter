# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

The user should be able to set their time avalaibility, they should also have the possibility to change or delete the tasks suggested by the app. They should also be able to add a new pet.

- What classes did you include, and what responsibilities did you assign to each?

I included four classes, splitting the data-holding entities (Task, Pet, Owner) from the class that holds the scheduling behavior (Scheduler).

**Task** — represents a single care activity. Its responsibility is to describe the work and track its own state.
- Attributes: `id`, `category`, `length` (minutes), `priority_level`, `completion`
- Methods: `assign_length()`, `assign_priority_level()`, `assign_category()`, `add()`, `edit()`, `mark_complete()`, `mark_uncomplete()`

**Pet** — represents a pet the owner cares for. Its responsibility is to hold the pet's identity and any special needs that generate care tasks.
- Attributes: `id`, `name`, `breed`, `special_needs`
- Methods: `add()`, `remove()`, `add_special_needs()`

**Owner** — represents the user of the app. Its responsibility is to manage the owner's profile, their pets, their availability, and to own a Scheduler.
- Attributes: `id`, `name`, `schedule` (a Scheduler), `pets` (a list of Pet)
- Methods: `add_owner()`, `change_owner()`, `modify_name()`, `add_pet()`, `remove_pet()`, `set_availability()`

**Scheduler** — the behavior-focused class. Its responsibility is to hold and organize the owner's tasks and build a prioritized schedule.
- Attributes: `tasks` (a list of Task)
- Methods: `view_schedule()`, `delete_schedule()`, `create_new_schedule()`, `add_task()`, `prioritize_tasks()`

Relationships: an Owner has one Scheduler and owns many Pets; the Scheduler manages many Tasks; a Pet can require many Tasks.


**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes, it changed.

**Change 1 — Connected Pets to their Tasks.**
In my first design, a Pet had no link to the tasks it needed. That meant there was no way to know which pet a task belonged to. I added a `tasks` list to Pet (and a `pet_id` on Task) so every task points back to the pet that requires it. Without this, the scheduler could not answer a basic question like "what does this pet need today?"

**Change 2 — Moved "add/edit/delete" methods onto the classes that own the data.**
Originally Task had its own `add()`/`edit()` methods and Pet had its own `add()`/`remove()`. But an object cannot really add itself to a list — it does not know where that list is. So I removed those methods and let the container classes handle it instead: the Scheduler adds tasks (`add_task()`) and the Owner adds/removes pets (`add_pet()`/`remove_pet()`). This gives one clear place to create or delete things, instead of two competing ways that could get out of sync.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
