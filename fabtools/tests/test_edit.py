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

    def test__choose_delim(self):
        from fabtools.edit import _choose_delim

        self.assertEqual(_choose_delim('hi'), '#')
        self.assertEqual(_choose_delim('hi#'), '/')
        self.assertEqual(_choose_delim('hi#/'), '@')
        with self.assertRaises(RuntimeError):
            _choose_delim('#/_@')

    def test__mk_selector(self):
        from fabtools.edit import _mk_selector
        _TEST_REGEX = 'a .ell of [aA] re.*x'

        # int
        self.assertEqual(_mk_selector(1234), '1234')
        # literal string
        self.assertEqual(_mk_selector(_TEST_REGEX), "\\#" + re.escape(_TEST_REGEX) + "#")
        # regex and delimiter
        self.assertEqual(_mk_selector(re.compile(_TEST_REGEX)),  '\\#' + _TEST_REGEX + '#')


    # def test__mk_sed_call(self):
    #     from fabtools.edit import _mk_sed_call
    #     print str(Path)
    #
    #     self.assertEqual(_mk_sed_call('a', self.textfile, 'FFFF'), '')
    #
    #     # op, file, start=None, end=None, opts=None, delim='+', *args, **kwargs):


    def test_find(self):
        from fabtools.edit import find
        import re

        self.assertEquals(find('one', self.textfile, use_sudo=local), [1])
        self.assertEqual(find('not one', self.textfile, use_sudo=local), [])
        self.assertEqual(find(re.compile('t[whre]+[eo]'), self.textfile, do_all=True, use_sudo=local), [2,3])
        self.assertEqual(find(re.compile('o..e'), self.textfile, use_sudo=local), [])
        self.assertEqual(find(re.compile('^two$'), self.textfile, use_sudo=local), [2])
        self.assertEqual(find('one\ntwo\nthree', self.textfile,use_sudo=local), [])
        self.assertEqual(find('one\ntwo\nthree', self.textfile, multi_line=True, use_sudo=local), [6])
        self.assertEqual(find('one\ntwo\nthree', self.textfile, multi_line=True, do_all=True, use_sudo=local), [6])

    def test_prepend(self):
        from fabtools.edit import prepend, find
        text = 'hi there'
        prepend(text, self.textfile, pat='three', use_sudo=local)
        prepend(text, self.textfile, pat='five', use_sudo=local)
        self.assertEqual(find(text, self.textfile, do_all=True, use_sudo=local), [3, 6])

    def test_append(self):
        from fabtools.edit import append, find
        text = 'howdy'
        append(text, self.textfile, pat='three', use_sudo=local)
        self.assertEqual(find(text, self.textfile, use_sudo=local), [4])



