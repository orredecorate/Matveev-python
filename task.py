from dataclasses import dataclass
from datetime import date
from abc import ABC
from typing import Optional
import expectations

TASK_TYPES: list[str] = ["учёба", "дела", "хобби"]


@dataclass
class Task(ABC):
    deadline: Optional[date]
    time_required: int
    type: str
    min_cont_interval: int
    is_done: bool


@dataclass
class Work(Task):
    def Complete(self):
        self.is_done = True


@dataclass
class Learning(Work):
    def MatchWith(self, other: "Learning"):
        pass


@dataclass
class Hobby(Task):
    pass