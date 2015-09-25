import sys
import textwrap
import re

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
    # Remove the leading directory (it's already mentioned in the header)
    # fn = fn.split('/', 1)[1]
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
    # if color is None:
    #     if status == 'OK':
    #         color = OK
    #     elif status == 'failed':
    #         color = ERROR
    #     else:
    #         color = INFO
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
