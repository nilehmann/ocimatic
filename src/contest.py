import os
from glob import glob
from problems import Problem


def get_problems_from_dir(dir_path):
    """Returns a list of problems in dir_path
    Returns:
      (list of Problem)
    """
    problems = []
    for path in glob('%s/*' % dir_path):
        if os.path.isdir(path):
            problems.append(Problem(path))
    return problems


class Contest:
    def __init__(self, dir_path):
        assert os.path.isdir(dir_path)
        self._dir_path = dir_path
        self._problems = get_problems_from_dir(dir_path)

    def get_problems(self):
        return self._problems
