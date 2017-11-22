from unittest import TestCase
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch
import shutil
import tempfile
import os
from os.path import join as J

import dwre_tools
from dwre_tools.validations import validate_file, validate_directory, validate_command

TEST_DATA = os.path.join(dwre_tools.__path__[0], '..', 'testdata')


class TestValidations(TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = os.path.join(self.temp_dir, 'test1')
        self.invalid_test_dir = os.path.join(self.temp_dir, 'test2')
        shutil.copytree(J(TEST_DATA, 'test1'), self.test_dir)
        shutil.copytree(J(TEST_DATA, 'test2'), self.invalid_test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_validates_single_file(self):
        filename = J(self.test_dir, 'migrations/20171115T1210_jira_collector_meta/' +
                     'meta/system-objecttype-extensions.xml')
        self.assertTrue(validate_file(filename))

    def test_validates_directory_recursively(self):
        directory = J(self.test_dir, 'migrations/20171115T1210_jira_collector_meta')
        self.assertTrue(validate_directory(directory))

    def test_validates_invalid_file(self):
        filename = J(self.invalid_test_dir, 'migrations/20171115T1210_jira_collector_meta/' +
                     'meta/system-objecttype-extensions.xml')
        self.assertFalse(validate_file(filename))

    @patch('dwre_tools.validations.validate_directory')
    def test_validates_based_on_target_type_directory(self, mock_validate_directory):
        filename = J(self.test_dir, 'migrations/20171115T1210_jira_collector_meta')
        validate_command(filename)
        mock_validate_directory.assert_called_with(filename)
        filename = J(self.test_dir, 'migrations/20171115T1210_jira_collector_meta/' +
                     'meta/system-objecttype-extensions.xml')

    @patch('dwre_tools.validations.validate_file')
    def test_validates_based_on_target_type_file(self, mock_validate_file):
        filename = J(self.test_dir, 'migrations/20171115T1210_jira_collector_meta/' +
                     'meta/system-objecttype-extensions.xml')
        validate_command(filename)
        mock_validate_file.assert_called_with(filename)
