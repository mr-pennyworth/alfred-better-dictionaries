# -*- coding: utf-8 -*-
"""
When compiled into a binary using pyinstaller, we want the behavior of
this script to mirror the behavior of the actual python binary. This
way, we can distribute a "fat binary" of "python" along with the workflow
so that users of the workflow don't have to "pip install" any deps as all
the deps are already baked into the binary.
"""
import code
import runpy
import sys

# import something from BetterDict so that when pyinstaller builds
# a binary for this file, it includes all direct and transitive
# dependencies of BetterDict.py too.
from BetterDict import noop


def main():
    noop()  # use the imported func to survive "optimize imports" action
    args = sys.argv[1:]

    if len(args) == 0:
        # No arguments provided, start an interactive interpreter session
        code.interact()
        return

    if args[0] == "-m":
        if len(args) < 2:
            print("Usage: python runner.py -m <module_name> [args]")
            sys.exit(1)
        module_name = args[1]
        sys.argv = args[1:]  # Set sys.argv to the module name and its arguments
        runpy.run_module(module_name, run_name="__main__", alter_sys=True)
    else:
        script_name = args[0]
        sys.argv = args  # Set sys.argv to the script name and its arguments
        runpy.run_path(script_name, run_name="__main__")


if __name__ == "__main__":
    main()
