#!/usr/bin/env python3
# -*- coding: utf-8; -*-
import os
import sys
# import getopt
import ui
import layout
from contest import Contest
from problems import Problem
from ui import OK, WARNING, ERROR


def change_directory():
    """Change directory to the contest root and returns the absolute path of the
    last directory before reaching the root, this correspond to the directory
    of the problem in which ocimatic was called. If the function reach system
    root the program exists.
    Returns:
        (string) If ocimatic was called inside a subdirectory belonging to a
    problem this function returns the absolute path of the problem directory.
    Otherwise it returns None.
    """
    last_dir = None
    while not os.path.exists(layout.ocimatic_file):
        last_dir = os.getcwd()
        head, tail = last_dir, None
        while not tail:
            head, tail = os.path.split(head)
        os.chdir('..')
        if os.getcwd() == '/':
            ui.show_message('Warning',
                            'ocimatic was not called inside a contest',
                            WARNING)
            ui.usage()
    return last_dir


def parse_arguments():
    """Parse options returning the command and the rest of the arguments."""
    # optlist, args = getopt.gnu_getopt(sys.argv[1:], 'l:s')
    args = sys.argv[1:]
    try:
        cmd = args.pop(0)
    except IndexError:
        ui.usage()
    return cmd, args


def new_contest(args):
    if len(args) != 1:
        ui.usage()
    contest_name = args[0]
    layout.create_layout_for_contest('%s/%s' % (os.getcwd(), contest_name))


def contest(args):
    if not args:
        ui.usage()

    if args[0] == "new":
        new_contest(args[1:])
    else:
        new_contest(args)


def new_problem(args):
    if len(args) != 1:
        ui.usage()
    problem_name = args[0]
    layout.create_layout_for_problem('%s/%s' % (os.getcwd(), problem_name))


def build_problems(problems):
    if not problems:
        ui.show_message("Warning", "no problems", WARNING)
        return
    for problem in problems:
        ui.task_header(str(problem), "Building solutions...")
        problem.build_all(
            lambda solution: ui.start_task(str(solution)),
            lambda status: ui.end_task(status))


def problem(args):
    if not args:
        ui.usage()

    problem_call = change_directory()
    contest = Contest(os.getcwd())

    if args[0] == "new":
        new_problem(args[1:])
    elif args[0] == "build":
        if problem_call:
            build_problems([Problem(problem_call)])
        else:
            build_problems(contest.get_problems())
    else:
        new_problem(args)


if __name__ == '__main__':
    cmd, args = parse_arguments()

    if cmd == "contest":
        contest(args)
    elif cmd == "problem":
        problem(args)
    else:
        ui.usage()
