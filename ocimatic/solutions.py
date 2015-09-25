import os
from glob import glob
import subprocess


def get_solutions_from_dir(dir_path):
    solutions = []
    for file_path in glob('%s/*' % dir_path):
        sol = make_solution_from_file_path(file_path)
        if sol:
            solutions.append(sol)
    return solutions


def make_solution_from_file_path(file_path):
    basename_path, ext = os.path.splitext(file_path)
    ext = ext[1:]
    if ext in CppSolution.src_exts:
        return CppSolution(basename_path, ext)
    if ext in CSolution.src_exts:
        return CSolution(basename_path, ext)
    else:
        return None


class Solution:
    def __init__(self, basename_path, src_ext, bin_ext):
        assert os.path.isfile('%s.%s' % (basename_path, src_ext))
        self._basename_path = basename_path
        self._src_path = '%s.%s' % (basename_path, src_ext)
        self._bin_path = '%s.%s' % (basename_path, bin_ext)

    def run(self, in_path, out_path):
        if not self.isbuilt():
            self.build()
        assert os.path.isfile(self._bin_path)

        pid = os.fork()
        if pid == 0:
            with open(in_path, 'r') as in_file:
                os.dup2(in_file.fileno(), 0)
            with open(out_path, 'w') as out_file:
                os.dup2(out_file.fileno(), 1)
            with open('/dev/null', 'w') as err_file:
                os.dup2(err_file.fileno(), 2)
            os.execl(self._bin_path, self._bin_path)
        (pid, status, rusage) = os.wait4(pid, 0)
        return os.WEXITSTATUS(status) == 0

    def __str__(self):
        return os.path.basename(self._src_path)

    def isbuilt(self):
        return os.path.isfile(self._bin_path)

    def build(self):
        raise NotImplementedError("Method not implemented in child class")


class CppSolution(Solution):
    src_exts = ["cpp", "cc"]
    bin_ext = "bin"

    def __init__(self, basename_path, src_ext="cpp"):
        super().__init__(basename_path, src_ext, CppSolution.bin_ext)

    def build(self):
        cmd_line = 'g++ -O2 -o %s %s' % (self._bin_path, self._src_path)
        return subprocess.call(cmd_line, shell=True) == 0


class CSolution(Solution):
    src_exts = ["c"]
    bin_ext = "bin"

    def __init__(self, basename_path, src_ext="cpp"):
        super().__init__(basename_path, src_ext, CSolution.bin_ext)

    def build(self):
        cmd_line = 'gcc -O2 -lm -std=c99 -o %s %s' % (self._bin_path,
                                                      self._src_path)
        return subprocess.call(cmd_line, shell=True) == 0
