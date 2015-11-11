#!/usr/bin/env python3
# -*- coding: utf-8; -*-
import os
import sys
import getopt
import textwrap
import re
from .core import Contest, create_layout_for_contest
from .core import Problem, create_layout_for_problem
from .core import OcimaticException

OPTS = {
    'partial': False,
    'problem': None,
    'sample': False,
}

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


def usage():
    return ('Usage: ' + bold('ocimatic ') + underline('[OPTIONS]') +
            ' ' + underline('[contest|problem]') +
            ' ' + underline('ACTION') + ' ...')


def error_message(message):
    writeln('ocimatic: ' + message)
    writeln()
    writeln(usage())
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
    length -= 6
    # Ensure the message has an even length.
    if len(fn) % 2 == 0:
        fn = '%s  ' % fn
    else:
        fn = '%s ' % fn

    if len(fn) <= length:
        fn = ' * ' + fn + '. ' * ((length - len(fn)) // 2 + 3)
    elif len(fn) > length:
        # clip message
        fn = ' * ...' + fn[len(fn)-length+3:] + '. . . '

    sys.stdout.write(fn)
    sys.stdout.flush()


def end_task(res):
    if res:
        color = OK
    else:
        color = ERROR
    sys.stdout.write(colorize(str(res.msg), color))
    print()


TAB_WIDTH = 6


def indent(level, text):
    writeln(' '*level*TAB_WIDTH + text)
    # writeln('\t'*level + text)


def description(level, text, width=90):
    # line = ''
    # tab_width = 6
    lines = textwrap.wrap(text,
                          width,
                          initial_indent=' '*TAB_WIDTH*level,
                          subsequent_indent=' '*TAB_WIDTH*level)
    writeln('\n'.join(lines))


def header(text):
    writeln(bold(text))


def ocimatic_help():
    writeln(usage())
    writeln()

    header('DESCRIPTION')
    description(1, 'Ocimatic is a tool for automating the work related to the'
                ' creation of problems for the Chilean Olympiad in Informatics'
                ' (OCI).')
    writeln()
    description(1, 'Ocimatic use GNU style scanning mode, so option and'
                ' non-option arguments may be intermixed. To specify the'
                ' action to perform you should provide one of the following'
                ' modes. If no mode is provided ' + bold('problem') +
                ' is assumed.')
    writeln()
    indent(1, bold('contest'))
    description(2, 'Performs contest related tasks.')
    writeln()
    indent(1, bold('problem'))
    description(2, 'Perform actions related to problems. If ocimatic is called'
                ' inside a problem directory or subdirectory the action is'
                ' performed for the specific problem. Otherwise the action is'
                ' performed for all problems in the contest. For example, '
                ' calling ' + bold('ocimatic problem check') + ' in the'
                ' contest root will check all problems input/output'
                ' correctness. This behavior can be overriden with the ' +
                bold('-p') + ' option.')
    writeln('')

    header('CONTEST ACTIONS')
    indent(1, bold('new') + ' ' + underline('NAME'))
    description(2, 'Create a new contest in the current directory with the'
                ' given name.')
    indent(1, bold('pdf'))
    description(2, 'Merge the statements of all problems generating a'
                ' problemset pdf.')
    writeln()

    header('PROBLEM ACTIONS')
    indent(1, bold('new') + ' ' + underline('NAME'))
    description(2, 'Create a new problem with the given name.')
    indent(1, bold('expected'))
    description(2, 'Generate expected output files (*.sol) for all input'
                ' testdata (*.in) using any correct solution.')
    indent(1, bold('pdf'))
    description(2, 'Generates pdf file for the problem statement.')
    indent(1, bold('check'))
    description(2, 'Checks input/output running all correct solutions with all'
                ' testdata and sample inputs.')
    indent(1, bold('run'))
    description(2, 'Run solutions with all test data and display the output'
                ' of the checker.')
    indent(1, bold('build'))
    description(2, 'Build all correct and partial solutions.')
    writeln()

    header('OPTIONS')
    indent(1, bold('-h, --help'))
    description(2, 'Display this help.')
    writeln()
    indent(1, bold('-p, --problem') + '=' + underline('NAME'))
    description(2, 'If specified, problem tasks are performed only on' +
                ' problem ' + underline('NAME') + ' regardless of where'
                ' ocimatic was called.')
    writeln()
    indent(1, bold('--partial'))
    description(2, 'By default the actions ' + bold('run') + ' doesn\'t'
                ' execute partial solutions. Use this option to run partial'
                ' solution as well.')
    writeln()
    indent(1, bold('--sample'))
    description(2, 'By default the action ' + bold('expected') + ' does not'
                ' generate sample outputs. Use this option to consider samples.')
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


def new_contest(args):
    if len(args) < 1:
        error_message('You have to specify a name for the contest.')
    name = args[0]

    try:
        create_layout_for_contest(os.path.join(os.getcwd(), name))
        show_message('Info', 'Contest [%s] created' % name)
    except Exception as exc:
        error_message('Couldn\'t create contest: %s.' % exc)


def contest_pdf(contest, _):
    start_task('Generating problemset')
    end_task(contest.gen_problemset_pdf())


def contest_mode(args):
    if not args:
        ocimatic_help()

    actions = {
        'pdf': contest_pdf,
    }

    if args[0] == "new":
        new_contest(args[1:])
    elif args[0] in actions:
        change_directory()
        contest = Contest(os.getcwd())
        actions[args[0]](contest, args[1:])
    else:
        error_message('Unknown action for contest.')


def new_problem(args):
    if len(args) < 1:
        error_message('You have to specify a name for the problem.')
    name = args[0]
    try:
        create_layout_for_problem(os.path.join(os.getcwd(), name))
        show_message('Info', 'Problem [%s] created' % name)
    except Exception as exc:
        error_message('Couldn\'t create problem: %s' % exc)


def problems_build(problems, _):
    for problem in problems:
        task_header(problem, "Building solutions")
        problem.build_all(start_task, end_task)


def gen_sol_files(problems, _):
    for problem in problems:
        task_header(problem, "Generating expected solutions for testdata")
        problem.gen_solutions_for_dataset(start_task, end_task, OPTS['sample'])


def problems_check(problems, _):
    for problem in problems:
        problem.check(
            (lambda problem:
             lambda solution: task_header(problem, "Checking %s" % solution))(problem),
            start_task, end_task)


def problems_run(problems, _):
    for problem in problems:
        problem.run(
            (lambda problem:
             lambda solution:
             task_header(problem, "Checking %s" % solution))(problem),
            start_task,
            end_task,
            OPTS['partial'],
        )


def problems_pdf(problems, _):
    for problem in problems:
        task_header(problem, "Generating pdf file")
        problem.gen_pdf(start_task, end_task)


def problems_compress(problems, _):
    for problem in problems:
        task_header(problem, "Compressing test data")
        problem.compress()


def problems_normalize(problems, _):
    for problem in problems:
        task_header(problem, "Normalizing test data")
        problem.normalize()

def problem_mode(args):
    if not args:
        ocimatic_help()

    actions = {
        'build': problems_build,
        'check': problems_check,
        'expected': gen_sol_files,
        'pdf': problems_pdf,
        'run': problems_run,
        'compress' : problems_compress,
        'normalize' : problems_normalize,
    }

    problem_call = change_directory()
    contest = Contest(os.getcwd())

    if args[0] == 'new':
        new_problem(args[1:])
    elif args[0] in actions:
        if OPTS['problem']:
            problems = [Problem(os.path.join(os.getcwd(), OPTS['problem']))]
        elif problem_call:
            problems = [Problem(problem_call)]
        else:
            problems = contest.get_problems()

        if not problems:
            show_message("Warning", "no problems", WARNING)

        actions[args[0]](problems, args[1:])

    else:
        error_message('Unknown action for problem.')


def main():
    try:
        optlist, args = getopt.gnu_getopt(sys.argv[1:], 'hp:',
                                          ['help', 'partial', 'problem=',
                                           '--phase=', 'sample'])
    except getopt.GetoptError as err:
        error_message(str(err))

    if len(args) == 0:
        ocimatic_help()

    modes = {
        'contest': contest_mode,
        'problem': problem_mode,
    }

    # If no mode is provided we assume problem
    if args[0] in modes:
        mode = args.pop(0)
    else:
        mode = 'problem'

    # Process options
    for (key, val) in optlist:
        if key == '-h' or key == '--help':
            ocimatic_help()
        elif key == '--partial':
            OPTS['partial'] = True
        elif key == '--problem' or key == '-p':
            OPTS['problem'] = val
        elif key == '--sample':
            OPTS['sample'] = True
        elif key == '--phase':
            os.environ["OCIMATIC_PHASE"] = val

    # Select mode
    try:
        if mode in modes:
            modes[mode](args)
        else:
            error_message('Unknown mode.')
    except OcimaticException as exc:
        error_message(str(exc))
