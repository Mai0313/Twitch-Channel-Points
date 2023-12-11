#!/usr/bin/env python

# Simple script to view contents of a cookie file stored in a pickle format

import pickle
import sys

from rich.console import Console

console = Console()

if __name__ == "__main__":
    argv = sys.argv
    if len(argv) <= 1:
        console.log("Specify a pickle file as a parameter, e.g. cookies/user.pkl")
    else:
        console.log(pickle.load(open(argv[1], "rb")))
