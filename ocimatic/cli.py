#!/usr/bin/env python3
# -*- coding: utf-8; -*-
import os
import sys
# import getopt
import textwrap
import re
from .contest import Contest, create_layout_for_contest
from .problems import Problem, create_layout_for_problem

RESET = '\x1b[0m'
BOLD = '\x1b[1m'
UNDERLINE = '\x1b[4m'
RED = '\x1b[31m'
GREEN = '\x1b[32m'
YELLOW = '\x1b[33m'
BLUE = '\x1b[34m'


def colorize(text, color):
    u"Add ANSI coloring to `text`."
    return color + text + RESET


def decolorize(text):
    u"Strip ANSI coloring from `text`."
    return re.sub(r'\033\[[0-9]+m', '', text)

INFO = BOLD
OK = BOLD + GREEN
WARNING = BOLD + YELLOW
ERROR = BOLD + RED


def show_message(label, message, color=INFO):
    indent_size = len(label) + 3
    lines = textwrap.wrap(message,
                          width=80,
                          initial_indent=' %s: ' % label,
                          subsequent_indent=' ' * indent_size)
    lines[0] = lines[0][indent_size:]
    sys.stdout.write(' %s ' % colorize(label + ':', color + UNDERLINE))
    sys.stdout.write('\n'.join(lines))
    print()
    print()


def task_header(name, message):
    print()
    sys.stdout.write(colorize('[%s] %s' % (name, message), INFO))
    print()


def start_task(fn, length=80):
    # Ensure the message has an even length.
    if len(fn) % 2 == 0:
        fn = ' * %s   ' % fn
    else:
        fn = ' * %s  ' % fn

    if len(fn) < length:
        fn += '. ' * ((length - len(fn)) // 2)
    elif len(fn) > length:
        # clip message
        fn = fn[:(length-4)] + '... '

    sys.stdout.write(fn)
    sys.stdout.flush()


def end_task(status=None):
    if status is True:
        status = 'OK'
        color = OK
    elif status is False:
        status = 'failed'
        color = ERROR
    else:
        status = ''
        color = INFO
    sys.stdout.write(colorize(status, color))
    print()


def usage():
    print()
    print("usage:")
    sys.exit(1)


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
    while not os.path.exists('.ocimatic'):
        last_dir = os.getcwd()
        head, tail = last_dir, None
        while not tail:
            head, tail = os.path.split(head)
        os.chdir('..')
        if os.getcwd() == '/':
            show_message('ERROR',
                         'ocimatic was not called inside a contest',
                         ERROR)
            usage()
    return last_dir


def parse_arguments():
    """Parse options returning the command and the rest of the arguments."""
    # optlist, args = getopt.gnu_getopt(sys.argv[1:], 'l:s')
    args = sys.argv[1:]
    try:
        cmd = args.pop(0)
    except IndexError:
        usage()
    return cmd, args


def new_contest(args):
    if len(args) != 1:
        usage()
    contest_name = args[0]
    status = create_layout_for_contest('%s/%s' % (os.getcwd(),
                                                  contest_name))
    if status:
        show_message('Info', 'Contest [%s] created' % contest_name)
    else:
        show_message('Error',
                     'Couldn\'t create contest',
                     ERROR)


def contest(args):
    if not args:
        usage()

    if args[0] == "new":
        new_contest(args[1:])
    elif args[0] == "pdf":
        change_directory()
        contest = Contest(os.getcwd())
        start_task('Generating problemset')
        end_task(contest.gen_problemset_pdf())
    else:
        new_contest(args)


def new_problem(args):
    if len(args) != 1:
        usage()
    problem_name = args[0]
    status = create_layout_for_problem('%s/%s' % (os.getcwd(),
                                                  problem_name))

    if status:
        show_message('Info', 'Problem [%s] created' % problem_name)
    else:
        show_message('Error',
                     'Couldn\'t create problem',
                     ERROR)


def build_problems(problems):
    for problem in problems:
        task_header(problem, "Building solutions...")
        problem.build_all(
            lambda solution: start_task(solution),
            lambda status: end_task(status))


def gen_sol_files(problems):
    for problem in problems:
        task_header(problem, "Generating solutions for testdata...")
        problem.gen_solutions_for_dataset(
            lambda testdata: start_task(testdata),
            lambda status: end_task(status))


def check_problem(problems):
    for problem in problems:
        problem.check(
            lambda solution: task_header(problem,
                                         "Checking %s... " % solution),
            lambda testdata: start_task(testdata),
            lambda status: end_task(status))


def gen_pdf_problem(problems):
    for problem in problems:
        task_header(problem, "Generating pdf file...")
        problem.gen_pdf(lambda statement: start_task(statement),
                        lambda status: end_task(status))


def problem(args):
    if not args:
        usage()

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
            show_message("Warning", "no problems", WARNING)

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


def main():
    cmd, args = parse_arguments()

    if cmd == "contest":
        contest(args)
    elif cmd == "problem":
        problem(args)
    else:
        usage()
