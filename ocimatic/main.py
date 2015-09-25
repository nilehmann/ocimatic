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
            ui.show_message('ERROR',
                            'ocimatic was not called inside a contest',
                            ERROR)
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
    status = layout.create_layout_for_contest('%s/%s' % (os.getcwd(),
                                                         contest_name))
    if status:
        ui.show_message('Info', 'Contest [%s] created' % contest_name)
    else:
        ui.show_message('Error',
                        'Couldn\'t create contest',
                        ERROR)


def contest(args):
    if not args:
        ui.usage()

    if args[0] == "new":
        new_contest(args[1:])
    elif args[0] == "pdf":
        change_directory()
        contest = Contest(os.getcwd())
        ui.start_task('Generating problemset')
        ui.end_task(contest.gen_problemset_pdf())
    else:
        new_contest(args)


def new_problem(args):
    if len(args) != 1:
        ui.usage()
    problem_name = args[0]
    status = layout.create_layout_for_problem('%s/%s' % (os.getcwd(),
                                                         problem_name))

    if status:
        ui.show_message('Info', 'Problem [%s] created' % problem_name)
    else:
        ui.show_message('Error',
                        'Couldn\'t create problem',
                        ERROR)


def build_problems(problems):
    for problem in problems:
        ui.task_header(problem, "Building solutions...")
        problem.build_all(
            lambda solution: ui.start_task(solution),
            lambda status: ui.end_task(status))

def gen_sol_files(problems):
    for problem in problems:
        ui.task_header(problem, "Generating solutions for testdata...")
        problem.gen_solutions_for_dataset(
            lambda testdata: ui.start_task(testdata),
            lambda status: ui.end_task(status))

def check_problem(problems):
    for problem in problems:
        problem.check(
            lambda solution: ui.task_header(problem,
                                            "Checking %s... " % solution),
            lambda testdata: ui.start_task(testdata),
            lambda status: ui.end_task(status))

def gen_pdf_problem(problems):
    for problem in problems:
        ui.task_header(problem, "Generating pdf file...")
        problem.gen_pdf(lambda statement: ui.start_task(statement),
                        lambda status: ui.end_task(status))

def problem(args):
    if not args:
        ui.usage()

    cmds = ['new', 'build', 'check', 'gen-sol', 'pdf']

    problem_call = change_directory()
    contest = Contest(os.getcwd())

    if args[0] == "new":
        new_problem(args[1:])
    elif args[0] in cmds:
        problems = []
        if problem_call:
            problems.append(Problem(problem_call))
        else:
            problems += contest.get_problems()

        if not problems:
            ui.show_message("Warning", "no problems", WARNING)

        if args[0] == 'build':
            build_problems(problems)
        elif args[0] == 'gen-sol':
            gen_sol_files(problems)
        elif args[0] == 'check':
            check_problem(problems)
        elif args[0] == 'pdf':
            gen_pdf_problem(problems)
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
