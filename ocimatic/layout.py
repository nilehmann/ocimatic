import os

solutions_correct_path = "solutions/correct/"
solutions_partial_path = "solutions/partial/"
statement_path = "statement"
testdata_path = "testdata/"
ocimatic_file = ".ocimatic"


problem_layout = {
    'attic': None,
    'statement': None,
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
    try:
        os.makedirs(contest_path)
        ocimatic_file = '%s/.ocimatic' % contest_path
        with open(ocimatic_file, 'a'):
            os.utime(ocimatic_file, None)
    except:
        return False
    return True


def create_layout_for_problem(problem_path):
    try:
        make_dirs_from_dict(problem_layout, problem_path)
    except:
        return False
    return True
