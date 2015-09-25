import os
from glob import glob


class TestData:
    def __init__(self, dir_path):
        assert os.path.isdir(dir_path)
        self.dir_path = dir_path

        self.in_data = []
        for file_path in glob('%s/*.in' % dir_path):
            self.in_data.append(TestDataFile(file_path))

        self.sol_data = []
        for file_path in glob('%s/*.sol' % dir_path):
            self.sol_data.append(TestDataFile(file_path))


class TestDataFile:
    def __init__(self, file_path):
        assert os.path.isfile(file_path)
        self.file_path = file_path
