import os
import shutil
from glob import glob
from tempfile import mkdtemp, NamedTemporaryFile

from .latex import Latex, merge_files
from .source import make_solution_from_file_path, DiffChecker, CustomChecker


class TaskResult:
    def __init__(self, msg, status=True):
        self.msg = msg
        self.status = status

    def __bool__(self):
        return self.status


class OcimaticException(Exception):
    def __init__(self, msg):
        self._msg = msg

    def __str__(self):
        return self._msg


def create_layout_for_contest(contest_path):
    ocimatic_dir = os.path.dirname(__file__)
    shutil.copytree(os.path.join(ocimatic_dir, "resources/contest-skel"),
                    contest_path)


class Contest:
    def __init__(self, dir_path):
        if not os.path.isdir(dir_path) or \
           not os.path.isfile(os.path.join(dir_path, '.ocimatic')):
            raise OcimaticException('No contest in `%s`.' % dir_path)
        self._dir_path = dir_path
        self._problems = get_problems_from_dir(dir_path)
        self._titlepage = Latex(os.path.join(self._dir_path,
                                             'titlepage.tex'))

    def get_problems(self):
        return self._problems

    def gen_problemset_pdf(self):
        try:
            # Temp working directory
            tmpdir_path = mkdtemp()

            # Merge files
            latex_files = [p.statement() for p in self._problems]
            latex_files.insert(0, self._titlepage)
            problemset_tex = os.path.join(tmpdir_path, 'problemset.tex')
            merge_files(latex_files, problemset_tex)

            # Generate pdf
            latex_file = Latex(problemset_tex)
            status = latex_file.gen_pdf()
            if status:
                shutil.copy2(os.path.join(tmpdir_path, 'problemset.pdf'),
                             os.path.join(self._dir_path, 'problemset.pdf'))
                msg = 'OK'
            else:
                msg = 'Failed'
        except Exception as e:
            raise e
            # raise e
            # msg = 'Un'
            # status = False
        finally:
            shutil.rmtree(tmpdir_path)
        return TaskResult(msg, status)


def create_layout_for_problem(problem_path):
    ocimatic_dir = os.path.dirname(__file__)
    shutil.copytree(os.path.join(ocimatic_dir, "resources/problem-skel"),
                    problem_path)


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


def get_solutions_from_dir(dir_path):
    solutions = []
    for file_path in glob(os.path.join(dir_path, '*')):
        sol = make_solution_from_file_path(file_path)
        if sol:
            solutions.append(sol)
    return solutions


class Problem:
    def __init__(self, path):
        if not os.path.isdir(path):
            raise OcimaticException('No problem in `%s`.' % path)
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

        self._checker = DiffChecker()
        if os.path.isfile(os.path.join(self._path, 'managers/checker')):
            self._checker = CustomChecker(os.path.join(self._path,
                                                       'managers/checker'))

    def statement(self):
        return self._statement

    def name(self):
        return self._name

    def __str__(self):
        return self.name()

    def gen_pdf(self, start_callback, end_callback):
        start_callback(str(self._statement))
        if self._statement.gen_pdf():
            end_callback(TaskResult('OK'))
        else:
            end_callback(TaskResult('Failed', True))

    def __testdata_iter(self, sample=False):
        for test in self._dataset:
            yield test
        if sample:
            for test in self._samples:
                yield test

    def run(self, solution_callback, start_callback, end_callback,
            partial, sample=False,
            formatter=lambda outcome, time: '%.3f [%.3f]' % (outcome, time),
            status_fun=lambda outcome, time: True):
        solutions = self._correct_solutions
        if partial:
            solutions += self._partial_solutions
        for solution in self._correct_solutions:
            solution_callback(str(solution))
            for test in self.__testdata_iter(sample):
                start_callback(str(test))
                try:
                    with NamedTemporaryFile() as tmp_file:
                        out_path = tmp_file.name
                        if not test.has_expected():
                            status = False
                            msg = 'No expected file'
                        else:
                            status, time = solution.run(test.input_path(),
                                                        out_path)

                            if not status:
                                status = False
                                msg = 'Runtime Error'
                            else:
                                outcome = self._checker(test.input_path(),
                                                        test.expected_path(),
                                                        out_path)
                                msg = formatter(outcome, time)
                                status = status_fun(outcome, time)
                except Exception as e:
                    # raise e
                    status = False
                    msg = str(e)

                end_callback(TaskResult(msg, status))

    def check(self, solution_callback, start_callback, end_callback):
        self.run(solution_callback, start_callback, end_callback,
                 False, True,
                 lambda outcome, _: ('OK' if outcome >= 1.0 else 'Failed'),
                 lambda outcome, _: outcome >= 1.0)

    def gen_solutions_for_dataset(self, start_callback, end_callback):
        if len(self._correct_solutions) == 0:
            return
        # We use any correct solution
        solution = self._correct_solutions[0]
        for test in self._dataset:
            start_callback(str(test))
            if solution.run(test.input_path(), test.expected_path()):
                end_callback(TaskResult('OK'))
            else:
                end_callback(TaskResult('Failed', False))

    def build_all(self, start_callback, end_callback):
        for solution in self._correct_solutions + self._partial_solutions:
            start_callback(str(solution))
            if solution.build():
                end_callback(TaskResult('OK'))
            else:
                end_callback(TaskResult('Failed', False))


class Dataset:
    def __init__(self, dir_path):
        if not os.path.isdir(dir_path):
            raise OcimaticException('No testdata directory `%s`.' % dir_path)
        self.dir_path = dir_path

        self._dataset = []
        for file_path in sorted(glob(os.path.join(dir_path,
                                                  '*' + TestData.input_ext))):
            basename, _ = os.path.splitext(file_path)
            self._dataset.append(TestData(basename))

    def __iter__(self):
        for test in self._dataset:
            yield test


class TestData:
    input_ext = 'in'
    expected_ext = 'sol'

    def __init__(self, basename_path):
        self._basename_path = basename_path
        self._input_path = '%s.%s' % (basename_path, TestData.input_ext)
        self._expected_path = '%s.%s' % (basename_path, TestData.expected_ext)
        assert os.path.isfile(self._input_path)

    def __str__(self):
        return self._input_path

    def input_path(self):
        return self._input_path

    def expected_path(self):
        return self._expected_path

    def has_expected(self):
        return os.path.isfile(self._expected_path)
