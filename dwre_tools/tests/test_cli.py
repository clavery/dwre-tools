from unittest import TestCase


class TestCLI(TestCase):
    def test_importing_argument_parser(self):
        from dwre_tools.cli import parser  # noqa
