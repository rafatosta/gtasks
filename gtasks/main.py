import sys

from gtasks.application import GTasksApplication


def main() -> int:
    return GTasksApplication().run(sys.argv)
