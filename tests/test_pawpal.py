"""Tests for the PawPal+ system."""

from pawpal_system import Pet, Task


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
