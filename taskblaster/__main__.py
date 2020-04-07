import argparse
from datetime import datetime
import logging
import sys

logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser(
    prog="taskblaster")

args = parser.parse_args(sys.argv[1:])

print("Hello, world!")
print(args)
