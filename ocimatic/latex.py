import shutil
import re
import uuid
import subprocess
import os
from os import path
from tempfile import mkdtemp


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = path.join(src, item)
        d = path.join(dst, item)
        if path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def compile_latex(dir_path, filename):
    cmd_line = 'cd %s && pdflatex %s %s' % (dir_path,
                                            '-interaction=batchmode',
                                            # '',
                                            filename)

    # We run latex multiple times just to be sure all is in place
    f = open('/dev/null', 'a')
    # f = open('/dev/stdout', 'w')
    st = subprocess.call(cmd_line, stdout=f, shell=True) == 0
    st = st and subprocess.call(cmd_line, stdout=f, shell=True) == 0
    st = st and subprocess.call(cmd_line, stdout=f, shell=True) == 0
    return st


def merge_packages(files):
    packages = {}
    for latex_file in files:
        for pkg, opts in latex_file.packages().items():
            if pkg not in packages:
                packages[pkg] = set()
                packages[pkg] = packages[pkg] | opts
    return packages


def merge_files(files, dst_path):
    dst, filename = os.path.split(dst_path)
    os.makedirs(dst, exist_ok=True)
    output_file = open(path.join(dst, filename), 'w')
    packages = merge_packages(files)

    # Preamble
    output_file.write('\\documentclass{oci}\n')
    for pkg, opts in packages.items():
        output_file.write('\\usepackage[%s]{%s}\n' % (','.join(opts), pkg))

    for latex in files:
        output_file.write(latex.preamble())

    # Begin document
    output_file.write('\\begin{document}\n')

    # Append files
    for latex in files:
        tmpdir = str(uuid.uuid4())

        # Copy referenced files
        refs = latex.referenced_files()
        for ref in refs:
            dst_file = path.join(dst, tmpdir, ref)
            src_file = path.join(latex._dir_path, ref)
            dst_dir, _ = path.split(dst_file)
            os.makedirs(dst_dir, exist_ok=True)
            shutil.copy2(src_file, dst_file)

        # output_file.write('\\clearpage\n')
        output_file.write('\\title{%s}\n' % latex.title())
        output_file.write(latex.document(tmpdir))
        output_file.write('\n')

    # End document
    output_file.write('\\end{document}\n')


class Latex:
    def __init__(self, file_path):
        assert path.isfile(file_path)
        dir_path, filename = path.split(path.normpath(file_path))
        self._dir_path = dir_path
        self._file_path = file_path
        self._filename = filename

    def __str__(self):
        return self._file_path

    def preamble(self):
        statement_file = open(self._file_path, 'r')
        preamble = ''
        for line in statement_file:
            if re.search(r'\\begin{document}', line):
                break
            m1 = re.match(r'\\usepackage(\[([^\]]*)\])?{([^}]*)}', line)
            m2 = re.match(r'\\documentclass(\[([^\]]*)\])?{([^}]*)}', line)
            if not m1 and not m2:
                preamble += line

        statement_file.close()
        return preamble

    def referenced_files(self):
        """Return relative path to files referenced inside the document"""
        statement_file = open(self._file_path, 'r')
        files = set()
        for line in statement_file:
            m = re.search(r'\\sampleIO{([^}]*)}', line)
            m and files.add(m.group(1) + '.in')
            m and files.add(m.group(1) + '.sol')

            m = re.search(r'\\includegraphics{([^}]*)}', line)
            m and files.add(m.group(1))

            m = re.search(r'\\input{([^}]*)}', line)
            m and files.add(m.group(1) + '.tex')

            m = re.search(r'\\include{([^}]*)}', line)
            m and files.add(m.group(1) + '.tex')
        return list(files)

    def document(self, path=''):
        statement_file = open(self._file_path, 'r')
        document = ''
        p = False
        for line in statement_file:
            line = re.sub(r'\\sampleIO{([^}]*)}',
                          r'\sampleIO{%s/\g<1>}' % path,
                          line)
            line = re.sub(r'\\includegraphics{([^}]*)}',
                          r'\includegraphics{%s/\g<1>}' % path,
                          line)
            if re.search(r'\\end{document}', line):
                p = False
            if p:
                document += line
            if re.search(r'\\begin{document}', line):
                p = True
        statement_file.close()
        return document

    def title(self):
        statement_file = open(self._file_path, 'r')
        for line in statement_file:
            m = re.match(r'\\title{([^}]*)}', line)
            if m:
                statement_file.close()
                return m.group(1)

        statement_file.close()
        return ''

    def io_samples(self):
        statement_file = open(self._file_path, 'r')
        samples = set()
        for line in statement_file:
            m = re.match(r'\\sampleIO{([^}]*)}', line)
            m and samples.add(m.group(1))
        statement_file.close()
        return list(samples)

    def packages(self):
        statement_file = open(self._file_path, 'r')
        packages = {}
        for line in statement_file:
            m = re.match(r'\\usepackage(\[([^\]]*)\])?{([^}]*)}', line)
            if m:
                # multiple packages
                for pkg in m.group(3).split(','):
                    if pkg not in packages:
                        packages[pkg] = set()
                    if m.group(2):
                        packages[pkg].add(m.group(2))
        statement_file.close()
        return packages

    def gen_pdf(self):
        tmpdir_path = mkdtemp()

        try:
            copytree(self._dir_path, tmpdir_path)

            # Copy oci.cls and logo.eps
            script_dir = path.dirname(__file__)
            shutil.copy2(path.join(script_dir, 'resources/oci.cls'),
                         path.join(tmpdir_path, 'oci.cls'))
            shutil.copy2(path.join(script_dir, 'resources/logo.eps'),
                         path.join(tmpdir_path, 'logo.eps'))

            # Compile
            status = compile_latex(tmpdir_path, self._filename)

            # Copy generated pdf
            basename, _ = path.splitext(self._filename)
            pdf = basename + ".pdf"
            shutil.copy2(path.join(tmpdir_path, pdf),
                         path.join(self._dir_path, pdf))
        except Exception:
            # raise e
            return False
        finally:
            shutil.rmtree(tmpdir_path)

        return status
