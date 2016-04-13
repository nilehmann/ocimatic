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
    output_file.write('\\documentclass[twoside]{oci}\n')
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
        self._reference_macros = {
            'includegraphics': ['.eps'],
            'include' : ['.tex'],
            'input' : ['.tex'],
        }

    def get_pdf_path(self):
        (base, _)  = os.path.splitext(self._file_path)
        return base+".pdf"


    def compile(self):
        cmd_line = 'cd %s && pdflatex --shell-escape %s %s' % (self._dir_path,
                                                               '-interaction=batchmode',
                                                               # '',
                                                               self._file_path)

        # We run latex multiple times just to be sure all is in place
        f = open('/dev/null', 'a')
        # f = open('/dev/stdout', 'w')
        st = subprocess.call(cmd_line, stdout=f, shell=True) == 0
        st = st and subprocess.call(cmd_line, stdout=f, shell=True) == 0
        st = st and subprocess.call(cmd_line, stdout=f, shell=True) == 0
        return st


    def __str__(self):
        return self._file_path

    def preamble(self):
        latex_file = open(self._file_path, 'r')
        preamble = ''
        for line in latex_file:
            if re.search(r'\\begin{document}', line):
                break
            # Do not include usepackages and document class in preamble
            m1 = re.search(r'\\usepackage(\[([^\]]*)\])?{([^}]*)}', line)
            m2 = re.search(r'\\documentclass(\[([^\]]*)\])?{([^}]*)}', line)
            if not m1 and not m2:
                preamble += line

        latex_file.close()
        return preamble

    def packages(self):
        latex_file = open(self._file_path, 'r')
        packages = {}
        for line in latex_file:
            m = re.search(r'^\\usepackage(\[([^\]]*)\])?{([^}]*)}', line)
            if m:
                # multiple packages
                for pkg in m.group(3).split(','):
                    if pkg not in packages:
                        packages[pkg] = set()
                    if m.group(2):
                        packages[pkg].add(m.group(2))
        latex_file.close()
        return packages

    def referenced_files(self):
        """Return relative path to files referenced inside the document"""
        latex_file = open(self._file_path, 'r')
        files = set()
        for line in latex_file:
            for macro, exts in self._reference_macros.items():
                # with extension
                m = re.match(r'[^%%]*\\%s(\[[^\]]*\])?{([^}]*\.[^}.]*)}' % macro,
                             line)
                m and files.add(m.group(2))

                # without extension
                m = re.match(r'[^%%]*\\%s(\[[^\]]*\])?{([^}.]*)}' % macro, line)
                if m:
                    for ext in exts:
                        files.add(m.group(2) + ext)

        return list(files)

    def document(self, path=''):
        latex_file = open(self._file_path, 'r')
        document = ''
        p = False
        for line in latex_file:
            for macro in self._reference_macros:
                line = re.sub(r'\\%s(\[[^\]]*\])?{([^}]*)}' % macro,
                              r'\%s\g<1>{%s/\g<2>}' % (macro, path),
                              line)

            if re.search(r'\\end{document}', line):
                p = False
            if p:
                document += line
            if re.search(r'\\begin{document}', line):
                p = True
        latex_file.close()
        return document

    def title(self):
        latex_file = open(self._file_path, 'r')
        for line in latex_file:
            m = re.search(r'\\title{([^}]*)}', line)
            if m:
                latex_file.close()
                return m.group(1)

        latex_file.close()
        return ''


class Statement(Latex):
    def __init__(self, file_path, number=None):
        super(Statement, self).__init__(file_path)
        self._number = number
        self._reference_macros['sampleIO'] = ['.in', '.sol']

    def gen_pdf(self):
        if self._number != None:
            os.environ["OCIMATIC_PROBLEM_NUMBER"] = chr(ord('A') + self._number)

        return self.compile()


    def io_samples(self):
        latex_file = open(self._file_path, 'r')
        samples = set()
        for line in latex_file:
            m = re.match(r'[^%]*\\sampleIO{([^}]*)}', line)
            m and samples.add(m.group(1))
        latex_file.close()
        return sorted(list(samples))
