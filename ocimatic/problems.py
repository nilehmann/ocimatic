import os
import subprocess
import shutil
from tempfile import NamedTemporaryFile
from glob import glob

from .testdata import Dataset, TestData
from .solutions import get_solutions_from_dir
from .latex import Latex


def create_layout_for_problem(problem_path):
    ocimatic_dir = os.path.dirname(__file__)
    try:
        shutil.copytree(os.path.join(ocimatic_dir, "resources/problem-skel"),
                        problem_path)
    except:
        return False
    return True


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


class Problem:
    def __init__(self, path):
        assert os.path.isdir(path)
        dir_path, name = os.path.split(os.path.normpath(path))
        self._path = path
        self._name = name

        self._dataset = Dataset(os.path.join(self._path, 'testdata'))

        self._correct_solutions = get_solutions_from_dir(
            os.path.join(self._path, 'solutions/correct'))

        self._partial_solutions = get_solutions_from_dir(
            os.path.join(self._path, 'solutions/partial'))

        self._statement = Latex(os.path.join(self._path,
                                             'documents/statement.tex'))

        self._samples = [TestData(os.path.join(self._path, 'documents', s))
                         for s in self._statement.io_samples()]

    def statement(self):
        return self._statement

    def name(self):
        return self._name

    def __str__(self):
        return self.name()
        # return self._dir_path

    def gen_pdf(self, start_callback, end_callback):
        start_callback(str(self._statement))
        end_callback(self._statement.gen_pdf())

    def check(self, solution_callback, start_callback, end_callback):
        for solution in self._correct_solutions:
            solution_callback(str(solution))
            for test in self._dataset + self._samples:
                start_callback(str(test))
                temp_file = NamedTemporaryFile(delete=False)
                temp_path = temp_file.name

                status = solution.run(test.get_input_path(),
                                      temp_path)
                if status:
                    status = subprocess.call(['diff',
                                              test.get_solution_path(),
                                              temp_path],
                                             stdout=NamedTemporaryFile(),
                                             stderr=NamedTemporaryFile()) == 0

                end_callback(status)

    def gen_solutions_for_dataset(self, start_callback, end_callback):
        assert len(self._correct_solutions) > 0
        # We use any correct solution
        solution = self._correct_solutions[0]
        for test in self._dataset:
            start_callback(str(test))
            end_callback(solution.run(test.get_input_path(),
                                      test.get_solution_path()))

    def build_all(self, start_callback, end_callback):
        for solution in self._correct_solutions:
            start_callback(str(solution))
            end_callback(solution.build())

        for solution in self._partial_solutions:
            start_callback(str(solution))
            end_callback(solution.build())
