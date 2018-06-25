from unittest import TestCase
import shutil, tempfile
import os
from os.path import join as J

import responses

from dwre_tools.watch import watch_command


class TestWatch(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        with open(J(self.temp_dir, "file1.txt"), "w") as f:
            f.write("TESTING1")
        with open(J(self.temp_dir, "file2.txt"), "w") as f:
            f.write("TESTING1")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    @responses.activate
    def test_testing_directory_exists(self):
        self.assertTrue(os.path.exists(self.temp_dir))
