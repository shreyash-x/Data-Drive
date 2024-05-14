from enum import Enum


class Permission(Enum):
    NONE = 0
    READ = 1
    WRITE = 2

    def __lt__(self, other):
        return self.value < other.value
    
class Task(Enum):
    NONE = -1
    DEFAULT = 0
    CHALLENGE = 1
    ASSIGNMENT = 2
    VIEWER = 3
    PAPER = 4
    PROTOTYPE = 5

class Role(Enum):
    USER = 0 
    ADMIN = 1
    SUPERADMIN = 2

    def __lt__(self, other):
        return self.value < other.value