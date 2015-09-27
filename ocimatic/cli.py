#!/usr/bin/env python3
# -*- coding: utf-8; -*-
import os
import sys
import getopt
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


def bold(text):
    return colorize(text, BOLD)


def underline(text):
    return colorize(text, UNDERLINE)


def decolorize(text):
    u"Strip ANSI coloring from `text`."
    return re.sub(r'\033\[[0-9]+m', '', text)


def writeln(text=''):
    sys.stdout.write(text+'\n')

INFO = BOLD
OK = BOLD + GREEN
WARNING = BOLD + YELLOW
ERROR = BOLD + RED


def error_message(message):
    writeln('ocimatic: ' + message)
    writeln('Usage: ' + bold('ocimatic ') + underline('contest|problem') +
            ' ' + underline('COMMAND') + ' ...')
    writeln('Try ' + bold('ocimatic -h') + ' for more information.')
    sys.exit(1)


def show_message(label, message, color=INFO):
    indent_size = len(label) + 3
    lines = textwrap.wrap(message,
                          width=80,
                          initial_indent=' %s: ' % label,
                          subsequent_indent=' ' * indent_size)
    lines[0] = lines[0][indent_size:]
    sys.stdout.write(' %s ' % colorize(label + ':', color + UNDERLINE))
    sys.stdout.write('\n'.join(lines))
    sys.stdout.write('\n')


def task_header(name, message):
    print()
    sys.stdout.write(colorize('[%s] %s' % (name, message), INFO))
    print()


def start_task(fn, length=80):
    # Ensure the message has an even length.
    if len(fn) % 2 == 0:
        fn = '%s . ' % fn
    else:
        fn = '%s  ' % fn

    if len(fn) < length:
        fn = ' * ' + fn + '. ' * ((length - len(fn)) // 2)
    elif len(fn) > length:
        # clip message
        fn = ' * ...' + fn[len(fn)-length+4:] 

    sys.stdout.write(fn)
    sys.stdout.flush()


def end_task(msg, status):
    if status:
        color = OK
    else:
        color = ERROR
    sys.stdout.write(colorize(msg, color))
    print()


tab_width = 6


def indent(level, text):
    writeln(' '*level*tab_width + text)
    # writeln('\t'*level + text)


def description(level, text, width=90):
    # line = ''
    # tab_width = 6
    lines = textwrap.wrap(text,
                          width,
                          initial_indent=' '*tab_width*level,
                          subsequent_indent=' '*tab_width*level)
    writeln('\n'.join(lines))


def header(text):
    writeln(bold(text))


def usage():
    writeln(bold('Usage: ocimatic ') + underline('[OPTION]') + ' ... ' +
            underline('contest|problem') +
            ' ' + underline('COMMAND') + ' ...')
    writeln()

    header('DESCRIPTION')
    description(1, 'Ocimatic is a tool for automating tasks related to the'
                ' creation of problems for the Chilean Olympiad in Informatics'
                ' (OCI).')
    writeln()
    description(1, 'To specify the task to perform you should provide one of'
                ' the following modes')
    writeln()
    indent(1, bold('contest'))
    description(2, 'Performs contest related tasks.')
    writeln()
    indent(1, bold('problem'))
    description(2, 'Performs tasks related to problems. If ocimatic is called'
                ' inside a problem directory or subdirectory the task is'
                ' performed for the specific problem. Otherwise the task is'
                ' performed for all problems in the contest. For example, '
                ' calling ' + bold('ocimatic problem check') + ' in the contest'
                'root will check all problems input/output correctness.')
    writeln('')

    header('CONTEST COMMANDS')
    indent(1, bold('new') + ' ' + underline('NAME'))
    description(2, 'Create a new contest in the current directory with the'
                ' given name.')
    indent(1, bold('pdf'))
    description(2, 'Merge the statements of all problems generating a'
                ' problemset pdf.')
    writeln()

    header('PROBLEM COMMANDS')
    indent(1, bold('new') + ' ' + underline('NAME'))
    description(2, 'Create a new problem with the given name.')
    indent(1, bold('expected'))
    description(2, 'Generates expected output files (*.sol) for all input'
                ' testdata (*.in) using any correct solution.')
    indent(1, bold('pdf'))
    description(2, 'Generates pdf file for the problem statement.')
    indent(1, bold('check'))
    description(2, 'Checks input/output running all correct solutions with all'
                ' testdata and sample inputs, and comparing the results with'
                ' the excepted output.')
    indent(1, bold('build'))
    description(2, 'Build all correct and partial solutions.')
    writeln()

    header('COMMANDS')
    indent(1, bold('-h'))
    description(2, 'Display this help.')
    writeln()
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
            error_message('ocimatic was not called inside a contest.')
    return last_dir


def parse_arguments():
    """Parse options returning the command and the rest of the arguments."""
    try:
        optlist, args = getopt.getopt(sys.argv[1:], 'h')
    except getopt.GetoptError as err:
        error_message(str(err))

    try:
        mode = args.pop(0)
    except IndexError:
        usage()

    return mode, args, optlist


def new_contest(args):
    if len(args) != 1:
        usage()
    contest_name = args[0]
    status = create_layout_for_contest(os.path.join(os.getcwd(), contest_name))
    if status:
        show_message('Info', 'Contest [%s] created' % contest_name)
    else:
        error_message('Couldn\'t create contest')


def contest(args):
    if not args:
        usage()

    if args[0] == "new":
        new_contest(args[1:])
    elif args[0] == "pdf":
        change_directory()
        contest = Contest(os.getcwd())
        start_task('Generating problemset')
        status = contest.gen_problemset_pdf()
        msg = 'OK'
        if not status:
            msg = 'Failed'
        end_task(msg, status)
    else:
        new_contest(args)


def new_problem(args):
    if len(args) != 1:
        usage()
    problem_name = args[0]
    status = create_layout_for_problem(os.path.join(os.getcwd(), problem_name))

    if status:
        show_message('Info', 'Problem [%s] created' % problem_name)
    else:
        show_message('Error',
                     'Couldn\'t create problem',
                     ERROR)


def build_problems(problems):
    for problem in problems:
        task_header(problem, "Building solutions")
        problem.build_all(
            lambda solution: start_task(solution),
            lambda msg, status: end_task(msg, status))


def gen_sol_files(problems):
    for problem in problems:
        task_header(problem, "Generating solutions for testdata")
        problem.gen_solutions_for_dataset(
            lambda testdata: start_task(testdata),
            lambda msg, status: end_task(msg, status))


def check_problem(problems):
    for problem in problems:
        problem.check(
            lambda solution: task_header(problem,
                                         "Checking %s" % solution),
            lambda testdata: start_task(testdata),
            lambda msg, status: end_task(msg, status))


def gen_pdf_problem(problems):
    for problem in problems:
        task_header(problem, "Generating pdf file")
        problem.gen_pdf(lambda statement: start_task(statement),
                        lambda msg, status: end_task(msg, status))


def problem(args):
    if not args:
        usage()

    cmds = ['new', 'build', 'check', 'expected', 'pdf']

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
        elif args[0] == 'expected':
            gen_sol_files(problems)
        elif args[0] == 'check':
            check_problem(problems)
        elif args[0] == 'pdf':
            gen_pdf_problem(problems)
    else:
        new_problem(args)


def main():
    mode, args, optlist = parse_arguments()

    if mode not in ['contest', 'problem']:
        error_message('Unknown mode.')

    for (key, val) in optlist:
        if key == '-h':
            usage()

    if mode == "contest":
        contest(args)
    elif mode == "problem":
        problem(args)
