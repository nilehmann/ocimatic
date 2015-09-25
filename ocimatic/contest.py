import os
import shutil
import subprocess
from tempfile import mkdtemp
from glob import glob
from problems import Problem


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


class Contest:
    def __init__(self, dir_path):
        assert os.path.isdir(dir_path)
        self._dir_path = dir_path
        self._problems = get_problems_from_dir(dir_path)

    def get_problems(self):
        return self._problems

    def gen_problemset_pdf(self):
        tmpdir_path = mkdtemp()
        front = open('%s/front.tex' % (self._dir_path))
        problemset = open('%s/problemset.tex' % (tmpdir_path), 'w')

        # Get packages of problems
        packages = {}
        for problem in self._problems:
            statement = problem.get_statement();
            for pkg, opts in statement.get_packages().items():
                if pkg not in packages:
                    packages[pkg] = set()
                packages[pkg] = packages[pkg] | opts

        # Append frontpage
        for line in front:
            # intert packages before \begin{document}
            if line == '\\begin{document}\n':
                for pkg, opts in packages.items():
                    problemset.write('\\usepackage[%s]{%s}\n' % (','.join(opts),
                                                                 pkg))
            if not line == '\\end{document}':
                problemset.write(line)
        front.close()

        # Append problems
        for problem in self._problems:
            statement = problem.get_statement();
            statement.copy_to('%s/%s' % (tmpdir_path, problem.name()))
            problemset.write('\\clearpage\n')
            problemset.write('\\title{%s}\n' % statement.get_title())
            problemset.write(statement.get_document(problem.name()))
            problemset.write('\n')

        problemset.write('\\end{document}\n')
        problemset.close()

        # Copy oci.cls and logo.eps
        script_dir = os.path.dirname(__file__)
        shutil.copy2('%s/extra/oci.cls' % script_dir,
                     '%s/extra/oci.cls' % tmpdir_path)
        shutil.copy2('%s/extra/logo.eps' % script_dir,
                     '%s/extra/logo.eps' % tmpdir_path)


        cmd_line = 'cd %s && pdflatex %s %s' % (tmpdir_path,
                                                '-interaction=nonstopmode',
                                                # '',
                                                'problemset.tex')

        # We run latex multiple times just to be sure all is in place
        f = open('/dev/null', 'a')
        # f = open('/dev/stdout', 'w')
        status = subprocess.call(cmd_line, stdout=f, shell=True) == 0
        status = status and subprocess.call(cmd_line, stdout=f, shell=True) == 0
        status = status and subprocess.call(cmd_line, stdout=f, shell=True) == 0

        if status:
            try:
                shutil.copy2('%s/%s' % (tmpdir_path, 'problemset.pdf'),
                             '%s/%s' % (self._dir_path, 'problemset.pdf'))
            except:
                return False
        return status


