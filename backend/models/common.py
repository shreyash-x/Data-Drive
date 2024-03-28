from enum import Enum


class Permission(Enum):
    NONE = 0
    READ = 1
    WRITE = 2

    def __lt__(self, other):
        return self.value < other.value

class Role(Enum):
    USER = 0 
    ADMIN = 1
    SUPERADMIN = 2

    def __lt__(self, other):
        return self.value < other.value