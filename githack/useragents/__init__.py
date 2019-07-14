from random import choice

from .data import user_agents


def get_random_ua() -> str:
    return choice(user_agents)
