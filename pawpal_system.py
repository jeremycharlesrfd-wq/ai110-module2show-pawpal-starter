"""PawPal+ system skeleton.

Class stubs generated from the UML class diagram (diagrams/diagrams/uml_draft.mmd).
Data-holding entities use dataclasses; Scheduler holds behavior over tasks.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    id: str
    category: str
    length: int
    priority_level: int
    completion: bool = False

    def assign_length(self, minutes: int) -> None:
        pass

    def assign_priority_level(self, level: int) -> None:
        pass

    def assign_category(self, category: str) -> None:
        pass

    def add(self) -> None:
        pass

    def edit(self) -> None:
        pass

    def mark_complete(self) -> None:
        pass

    def mark_uncomplete(self) -> None:
        pass


@dataclass
class Pet:
    id: str
    name: str
    breed: str
    special_needs: list[str] = field(default_factory=list)

    def add(self) -> None:
        pass

    def remove(self) -> None:
        pass

    def add_special_needs(self, need: str) -> None:
        pass


@dataclass
class Owner:
    id: str
    name: str
    schedule: "Scheduler" = None
    pets: list[Pet] = field(default_factory=list)

    def add_owner(self) -> None:
        pass

    def change_owner(self) -> None:
        pass

    def modify_name(self, name: str) -> None:
        pass

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet: Pet) -> None:
        pass

    def set_availability(self, hours: int) -> None:
        pass


@dataclass
class Scheduler:
    tasks: list[Task] = field(default_factory=list)

    def view_schedule(self) -> list[Task]:
        pass

    def delete_schedule(self) -> None:
        pass

    def create_new_schedule(self) -> None:
        pass

    def add_task(self, task: Task) -> None:
        pass

    def prioritize_tasks(self) -> list[Task]:
        pass
