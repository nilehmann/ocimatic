import os

solutions_correct_path = "solutions/correct/"
solutions_partial_path = "solutions/partial/"
testdata_path = "testdata/"
ocimatic_file = ".ocimatic"


problem_layout = {
    'attic': None,
    'statement': {
        'sampleIO': None
    },
    'testdata': None,
    'solutions': {
        'correct': None,
        'partial': None,
    },
}


def make_dirs_from_dict(d, current_dir):
    if d:
        for key, val in d.items():
            make_dirs_from_dict(val, os.path.join(current_dir, key))
    else:
        os.makedirs(current_dir)


def create_layout_for_contest(contest_path):
    os.makedirs(contest_path)
    ocimatic_file = '%s/.ocimatic' % contest_path
    with open(ocimatic_file, 'a'):
        os.utime(ocimatic_file, None)


def create_layout_for_problem(problem_path):
    make_dirs_from_dict(problem_layout, problem_path)
