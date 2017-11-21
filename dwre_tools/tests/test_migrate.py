from unittest import TestCase
import shutil, tempfile
import os
from os.path import join as J

import responses

import dwre_tools
from dwre_tools.migrate import get_migrations

TEST_DATA = os.path.join(dwre_tools.__path__[0], '..', 'testdata')

class TestMigrationIntegration(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = os.path.join(self.temp_dir, 'test1')
        shutil.copytree(J(TEST_DATA, 'test1'), self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @responses.activate
    def test_testing_directory_exists(self):
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'migrations')))


