from __future__ import absolute_import
import unittest
import re
from pathlib2 import Path

class EditTestCase(unittest.TestCase):
    def test__mk_selector(self):
        from fabtools.edit import _mk_selector
        _TEST_REGEX = 'a .ell of [aA] re.*x'
        _DELIM = '%'

        # int
        self.assertEqual(_mk_selector(1234), '1234')
        # literal string
        self.assertEqual(_mk_selector(_TEST_REGEX), "+" + re.escape(_TEST_REGEX) + "+")
        # regex and delimiter
        self.assertEqual(_mk_selector(re.compile(_TEST_REGEX), delim=_DELIM),  _DELIM + _TEST_REGEX + _DELIM)


    def test__mk_sed_cmd(self):
        from fabtools.edit import _mk_sed_cmd
        print str(Path)

        self.assertEqual(_mk_sed_cmd('a', Path('/tmp/tryit'), 'FFFF'), '')

        # op, file, start=None, end=None, opts=None, delim='+', *args, **kwargs):
