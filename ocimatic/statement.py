import os
import shutil
import re
from tempfile import mkdtemp
import inspect
import subprocess

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        print(item)
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            print(s, d)
            shutil.copy(s, d)

class Statement:
    tex_filename = 'statement.tex'
    pdf_filename = 'statement.pdf'
    def __init__(self, dir_path):
        assert os.path.isdir(dir_path)
        assert os.path.isfile('%s/%s' % (dir_path, Statement.tex_filename))
        self._dir_path = dir_path

    def __str__(self):
        return '%s/%s' % (self._dir_path, Statement.tex_filename)

    def get_document(self, path):
        statement_file = open('%s/%s' % (self._dir_path, Statement.tex_filename),
                              'r')
        document = ''
        p = False
        for line in statement_file:
            line = re.sub('\\\\sampleIO{([^}]*)}',
                          '\\sampleIO{%s/\g<1>}' % path,
                          line)
            line = re.sub('\\\\includegraphics{([^}]*)}',
                          '\\includegraphics{%s/\g<1>}' % path,
                          line)
            if re.search('\\\\end{document}', line):
                p = False
            if p:
                document += line
            if re.search('\\\\begin{document}', line):
                p = True
        statement_file.close()
        return document


    def get_title(self):
        statement_file = open('%s/%s' % (self._dir_path, Statement.tex_filename),
                              'r')
        for line in statement_file:
            m = re.match('\\\\title{([^}]*)}', line)
            if m:
                statement_file.close()
                return m.group(1)

        statement_file.close()
        return ''

    def get_io_samples(self):
        statement_file = open('%s/%s' % (self._dir_path, Statement.tex_filename),
                              'r')
        samples = []
        for line in statement_file:
            m = re.match('\\\\sampleIO{([^}]*)}', line)
            if m:
                samples.append(m.group(1))
        statement_file.close()
        return samples

    def copy_to(self, dest_path):
        if os.path.isdir(dest_path):
            copytree(self._dir_path, dest_path)
        else:
            shutil.copytree(self._dir_path, dest_path)

    def get_packages(self):
        statement_file = open('%s/%s' % (self._dir_path, Statement.tex_filename),
                              'r')
        packages = {}
        for line in statement_file:
            m = re.match('\\\\usepackage(\\[([^\\]]*)\\])?{([^}]*)}', line)
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
        copytree(self._dir_path, tmpdir_path)

        # Copy oci.cls and logo.eps
        script_dir = os.path.dirname(__file__)
        shutil.copy2('%s/extra/oci.cls' % script_dir,
                     '%s/extra/oci.cls' % tmpdir_path)
        shutil.copy2('%s/extra/logo.eps' % script_dir,
                     '%s/extra/logo.eps' % tmpdir_path)

        cmd_line = 'cd %s && pdflatex %s %s' % (tmpdir_path,
                                                '-interaction=batchmode',
                                                Statement.tex_filename)

        # We run latex multiple times just to be sure all is in place
        f = open('/dev/null', 'a')
        status = subprocess.call(cmd_line, stdout=f, shell=True) == 0
        status = status and subprocess.call(cmd_line, stdout=f, shell=True) == 0
        status = status and subprocess.call(cmd_line, stdout=f, shell=True) == 0

        if status:
            try:
                shutil.copy2('%s/%s' % (tmpdir_path, Statement.pdf_filename),
                             '%s/%s' % (self._dir_path, Statement.pdf_filename))
            except:
                return False

        return status






