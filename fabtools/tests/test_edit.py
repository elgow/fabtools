from __future__ import absolute_import
import unittest
import re
from pathlib2 import Path
from fabric.api import run, sudo, local
from tempfile import NamedTemporaryFile

class EditTestCase(unittest.TestCase):
    def setUp(self):
        with NamedTemporaryFile(delete=False) as dat:
            self.textfile = Path(dat.name)
            dat.write('one\ntwo\nthree\nfour\nfive\nsix\n')


    def tearDown(self):
        self.textfile.unlink()


    def test__mk_selector(self):
        from fabtools.edit import _mk_selector
        _TEST_REGEX = 'a .ell of [aA] re.*x'

        # int
        self.assertEqual(_mk_selector(1234), '1234')
        # literal string
        self.assertEqual(_mk_selector(_TEST_REGEX), "\\#" + re.escape(_TEST_REGEX) + "#")
        # regex and delimiter
        self.assertEqual(_mk_selector(re.compile(_TEST_REGEX)),  '\\#' + _TEST_REGEX + '#')


    def test__mk_sed_cmd(self):
        from fabtools.edit import _mk_sed_cmd
        print str(Path)

        self.assertEqual(_mk_sed_cmd('a', self.textfile, 'FFFF'), '')

        # op, file, start=None, end=None, opts=None, delim='+', *args, **kwargs):


    def test_contains_line(self):
        from fabtools.edit import contains_line
        import re

        self.assertTrue(contains_line('one', self.textfile, use_sudo=local))
        self.assertFalse(contains_line('not one', self.textfile, use_sudo=local))
        self.assertTrue(contains_line(re.compile('o[na]e'), self.textfile, use_sudo=local))
        self.assertFalse(contains_line(re.compile('o..e'), self.textfile, use_sudo=local))
        self.assertTrue(contains_line(re.compile('^two$'), self.textfile, use_sudo=local))


    def test_contains(self):
        from fabtools.edit import contains
        import re

        self.assertTrue(contains('one', self.textfile, use_sudo=local))
        self.assertFalse(contains('not one', self.textfile, use_sudo=local))
        self.assertTrue(contains('one\ntwo\nthree', self.textfile, use_sudo=local))
        self.assertTrue(contains(re.compile('t[whre\\n]+e'), self.textfile, use_sudo=local))
        self.assertFalse(contains(re.compile('o..e'), self.textfile, use_sudo=local))


    def test__choose_delim(self):
        from fabtools.edit import _choose_delim

        self.assertEqual(_choose_delim('hi'), '#')
        self.assertEqual(_choose_delim('hi#'), '/')
        self.assertEqual(_choose_delim('hi#/'), '@')
        with self.assertRaises(RuntimeError):
            _choose_delim('#/_@')


