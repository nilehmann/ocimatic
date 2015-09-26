import os
from glob import glob


class Dataset:
    def __init__(self, dir_path):
        assert os.path.isdir(dir_path)
        self.dir_path = dir_path

        self._dataset = []
        for file_path in glob('%s/*.%s' % (dir_path, TestData.input_ext)):
            basename, _ = os.path.splitext(file_path)
            self._dataset.append(TestData(basename))

    def __iter__(self):
        for test in self._dataset:
            yield test


class TestData:
    input_ext = 'in'
    solution_ext = 'sol'

    def __init__(self, basename_path):
        self._basename_path = basename_path
        self._input_path = '%s.%s' % (basename_path, TestData.input_ext)
        self._solution_path = '%s.%s' % (basename_path, TestData.solution_ext)
        assert os.path.isfile(self._input_path)

    def __str__(self):
        return self._input_path

    def get_input_path(self):
        return self._input_path

    def get_solution_path(self):
        return self._solution_path

    def has_solution(self):
        return os.path.isfile(self._solution_path)

