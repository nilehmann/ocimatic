import os
from glob import glob
from tempfile import NamedTemporaryFile
import subprocess


def make_solution_from_file_path(file_path):
    basename_path, ext = os.path.splitext(file_path)
    if ext == CppSolution.src_ext:
        return CppSolution(basename_path)
    if ext == CSolution.src_ext:
        return CSolution(basename_path)
    else:
        return None


class Solution:
    def __init__(self, basename_path, src_ext, bin_ext):
        assert os.path.isfile(basename_path + src_ext)
        self._basename_path = basename_path
        self._src_path = basename_path + src_ext
        self._bin_path = basename_path + bin_ext

    def run(self, in_path, out_path):
        if not self.isbuilt():
            self.build()
        return Binary(self._bin_path).run(in_path, out_path)

    def __str__(self):
        return os.path.basename(self._src_path)

    def isbuilt(self):
        return os.path.isfile(self._bin_path)

    def build(self):
        raise NotImplementedError("Method not implemented in child class")


class CppSolution(Solution):
    src_ext = ".cpp"
    bin_ext = ".bin"

    def __init__(self, basename_path):
        super().__init__(basename_path,
                         CppSolution.src_ext,
                         CppSolution.bin_ext)

    def build(self):
        cmd_line = 'g++ -O2 -o %s %s' % (self._bin_path, self._src_path)
        return subprocess.call(cmd_line, shell=True) == 0


class CSolution(Solution):
    src_ext = ".c"
    bin_ext = ".bin"

    def __init__(self, basename_path):
        super().__init__(basename_path, CSolution.src_ext, CSolution.bin_ext)

    def build(self):
        cmd_line = 'gcc -O2 -lm -std=c99 -o %s %s' % (self._bin_path,
                                                      self._src_path)
        return subprocess.call(cmd_line, shell=True) == 0


class Binary:
    def __init__(self, file_path):
        assert os.path.isfile(file_path)
        self._file_path = file_path

    def run(self, in_path, out_path):
        pid = os.fork()
        if pid == 0:
            with open(in_path, 'r') as in_file:
                os.dup2(in_file.fileno(), 0)
            with open(out_path, 'a') as out_file:
                os.dup2(out_file.fileno(), 1)
            with open('/dev/null', 'w') as err_file:
                os.dup2(err_file.fileno(), 2)
            os.execl(self._file_path, self._file_path)
        (pid, status, rusage) = os.wait4(pid, 0)
        status = os.WEXITSTATUS(status) == 0
        wtime = rusage.ru_utime + rusage.ru_stime
        return status, wtime


class DiffChecker:
    def __call__(self, in_path, expected_path, out_path):
        with open('/dev/null', 'a') as null:
            status = subprocess.call(['diff',
                                        expected_path,
                                        out_path],
                                        stdout=null,
                                        stderr=null)
            return 1.0 if status == 0 else 0.0


class CustomChecker:
    def __init__(self, file_path):
        self._binary = Binary(file_path)

    def __call__(self, in_path, expected_path, out_path):
        with NamedTemporaryFile() as tmp_file:
            tmp_path = tmp_file.name
            status, _ = self._binary.run(in_path, tmp_path)
            return float(tmp_file.read())
