import os
from tempfile import NamedTemporaryFile
import subprocess


def make_solution_from_file_path(file_path, managers_path):
    basename_path, ext = os.path.splitext(file_path)
    if ext == CppSolution.src_ext:
        return CppSolution(basename_path, managers_path)
    if ext == CSolution.src_ext:
        return CSolution(basename_path, managers_path)
    if ext == JavaSolution.src_ext:
        return JavaSolution(basename_path, managers_path)
    else:
        return None


def run(cmd, in_path, out_path, *args):
    pid = os.fork()
    if pid == 0:
        if in_path:
            with open(in_path, 'r') as in_file:
                os.dup2(in_file.fileno(), 0)
        with open(out_path, 'w') as out_file:
            os.dup2(out_file.fileno(), 1)
        with open('/dev/null', 'w') as err_file:
            os.dup2(err_file.fileno(), 2)
        os.execl(cmd, cmd, *args)
    (pid, status, rusage) = os.wait4(pid, 0)
    status = os.WEXITSTATUS(status) == 0
    wtime = rusage.ru_utime + rusage.ru_stime
    return status, wtime

class Solution:
    def run(self, in_path, out_path):
        raise NotImplementedError("Method not implemented in child class.")

    def __str__(self):
        raise NotImplementedError("Method not implemented in child class.")

    def isbuilt(self):
        raise NotImplementedError("Method not implemented in child class.")

    def build(self):
        raise NotImplementedError("Method not implemented in child class.")


class CppSolution(Solution):
    src_ext = ".cpp"
    grader_name = "grader.cpp"

    def __init__(self, basename_path, managers_path=''):
        self._basename_path = basename_path
        self._src_path = basename_path + self.src_ext
        self._bin_path = basename_path + ".bin"

        self._managers_path = managers_path
        self._use_grader = False
        if os.path.exists(os.path.join(managers_path, self.grader_name)):
            self._use_grader = True
            self._grader_path = os.path.join(managers_path, self.grader_name)

    def __str__(self):
        return self._basename_path

    def run(self, in_path, out_path):
        if self.need_rebuilt():
            print("Rebuilt")
            self.build()
        return Binary(self._bin_path).run(in_path, out_path)

    def isbuilt(self):
        return os.path.isfile(self._bin_path)

    def need_rebuilt(self):
        if self.isbuilt():
            bin_time = os.path.getmtime(self._bin_path)
            src_time = os.path.getmtime(self._src_path)
            return src_time > bin_time
        return True

    def build(self):
        grader = ''
        if self._use_grader:
            grader = '"'+self._grader_path+'"'
        cmd_line = 'g++ -std=c++11 -O2 -I"%s" -o "%s" %s "%s"' % (
            self._managers_path,
            self._bin_path,
            grader,
            self._src_path)
        return subprocess.call(cmd_line, shell=True) == 0


class CSolution(Solution):
    src_ext = ".c"
    grader_name = "grader.c"

    def __init__(self, basename_path, managers_path):
        self._basename_path = basename_path
        self._src_path = basename_path + self.src_ext
        self._bin_path = basename_path + ".bin"

        self._managers_path = managers_path

    def __str__(self):
        return self._basename_path

    def run(self, in_path, out_path):
        if not self.isbuilt():
            self.build()
        return Binary(self._bin_path).run(in_path, out_path)

    def isbuilt(self):
        return os.path.isfile(self._bin_path)

    def build(self):
        bin_time = os.path.getmtime(self._bin_path)
        src_time = os.path.getmtime(self._src_path)
        if src_time <= bin_time:
            return True
        cmd_line = 'gcc -O2 -lm -std=c99 -I"%s" -o "%s" "%s"' % (
                self._managers_path,
                self._bin_path,
                self._src_path)
        return subprocess.call(cmd_line, shell=True) == 0

class JavaSolution(Solution):
    src_ext = ".java"
    grader_name = "Grader.java"

    def __init__(self, basename_path, managers_path):
        (self._class_path, self._class_name) = os.path.split(basename_path)
        self._src_path = basename_path + self.src_ext
        self._bytecode_path = basename_path + ".class"

        # self._managers_path = managers_path
        # self._grader_path = ''
        # if os.path.exists(os.path.join(managers_path, JavaSolution.grader_name)):
        #     self._grader_path = os.path.join(grader_path, JavaSolution.grader_name)

    def __str__(self):
        return os.path.join(self._class_path, self._class_name)

    def run(self, in_path, out_path):
        if self.need_rebuilt():
            self.build()
        return run("/usr/bin/java", in_path, out_path,
                   "-cp", self._class_path,
                   self._class_name)

    def isbuilt(self):
        return os.path.isfile(self._bytecode_path)

    def need_rebuilt(self):
        if self.isbuilt():
            bytecode_time = os.path.getmtime(self._bytecode_path)
            src_time = os.path.getmtime(self._src_path)
            return src_time > bytecode_time
        return True

    def build(self):
        cmd_line = 'javac "%s"' % (self._src_path)
        return subprocess.call(cmd_line, shell=True) == 0

class Binary:
    def __init__(self, file_path):
        assert os.path.isfile(file_path)
        self._file_path = file_path

    def run(self, in_path, out_path, *args):
        return run(self._file_path, in_path, out_path, *args)


class DiffChecker:
    def __call__(self, in_path, expected_path, out_path):
        with open('/dev/null', 'w') as null:
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
            self._binary.run(None, tmp_path, in_path, expected_path, out_path)
            return float(tmp_file.read())
