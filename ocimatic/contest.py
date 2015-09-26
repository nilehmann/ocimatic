import os
import shutil
from tempfile import mkdtemp

from .latex import Latex, merge_files
from .problems import get_problems_from_dir


def create_layout_for_contest(contest_path):
    ocimatic_dir = os.path.dirname(__file__)
    try:
        shutil.copytree(os.path.join(ocimatic_dir, "resources/contest-skel"),
                        contest_path)
    except:
        return False
    return True


class Contest:
    def __init__(self, dir_path):
        assert os.path.isdir(dir_path)
        self._dir_path = dir_path
        self._problems = get_problems_from_dir(dir_path)
        self._frontpage = Latex(os.path.join(self._dir_path,
                                             'titlepage.tex'))

    def get_problems(self):
        return self._problems

    def gen_problemset_pdf(self):
        tmpdir_path = mkdtemp()

        try:
            latex_files = [p.statement() for p in self._problems]
            latex_files.insert(0, self._frontpage)

            merge_files(latex_files, tmpdir_path, 'problemset.tex')

            latex_file = Latex(os.path.join(tmpdir_path, 'problemset.tex'))

            status = latex_file.gen_pdf()

            shutil.copy2(os.path.join(tmpdir_path, 'problemset.pdf'),
                         os.path.join(self._dir_path, 'problemset.pdf'))
        except:
            return False
        finally:
            shutil.rmtree(tmpdir_path)
        return status
