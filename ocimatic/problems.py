import os
import subprocess
from tempfile import NamedTemporaryFile
from testdata import Dataset
from solutions import get_solutions_from_dir
from statement import Statement
import layout

class Problem:
    def __init__(self, dir_path):
        assert os.path.isdir(dir_path)
        self._dir_path = dir_path
        self._dataset = Dataset('%s/%s' % (dir_path, layout.testdata_path))
        self._correct_solutions = get_solutions_from_dir(
            '%s/%s' % (dir_path, layout.solutions_correct_path))
        self._partial_solutions = get_solutions_from_dir(
            '%s/%s' % (dir_path, layout.solutions_partial_path))
        self._statement = Statement('%s/%s' % (dir_path, layout.statement_path))


    def get_statement(self):
        return self._statement

    def name(self):
        return os.path.basename(os.path.normpath(self._dir_path))

    def __str__(self):
        return self.name()
        # return self._dir_path

    def gen_pdf(self, start_callback, end_callback):
        start_callback(str(self._statement))
        end_callback(self._statement.gen_pdf())

    def check(self, solution_callback, start_callback, end_callback):
        for solution in self._correct_solutions:
            solution_callback(str(solution))
            for test in self._dataset:
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
