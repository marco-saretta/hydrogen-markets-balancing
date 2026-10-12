"""Logging set-up: coloured level names on the console, plain text in the run's log file."""

import logging
import sys

PLAIN = "%(asctime)s %(levelname)-8s [%(module)s] %(message)s"
COLOURS = {"DEBUG": "36", "INFO": "32", "WARNING": "33", "ERROR": "31", "CRITICAL": "1;31"}


class ColourFormatter(logging.Formatter):
    def format(self, record):
        record = logging.makeLogRecord(record.__dict__)  # copy, so the file handler stays plain
        record.levelname = f"\033[{COLOURS.get(record.levelname, '0')}m{record.levelname:<8}\033[0m"
        return super().format(record)


def setup_logging(level="INFO", log_file=None):
    """Send all loggers to the console and, if given, to a plain-text file."""
    console = logging.StreamHandler(sys.stdout)
    formatter = ColourFormatter if sys.stdout.isatty() else logging.Formatter
    console.setFormatter(formatter(PLAIN, datefmt="%H:%M:%S"))
    handlers = [console]
    if log_file is not None:
        file = logging.FileHandler(log_file)
        file.setFormatter(logging.Formatter(PLAIN))
        handlers.append(file)
    logging.basicConfig(level=level, handlers=handlers, force=True)
