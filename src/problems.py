import os
from testdata import TestData
from solutions import get_solutions_from_dir
import layout


class Problem:
    def __init__(self, dir_path):
        assert os.path.isdir(dir_path)
        self._dir_path = dir_path
        self._testdata = TestData('%s/%s' % (dir_path, layout.testdata_path))
        self._correct_solutions = get_solutions_from_dir(
            '%s/%s' % (dir_path, layout.solutions_correct_path))
        self._partial_solutions = get_solutions_from_dir(
            '%s/%s' % (dir_path, layout.solutions_partial_path))

    def __str__(self):
        return self._dir_path

    def build_all(self, start_callback, end_callback):
        for solution in self._correct_solutions:
            start_callback(solution)
            end_callback(solution.build())

        for solution in self._partial_solutions:
            start_callback(solution)
            end_callback(solution.build())
