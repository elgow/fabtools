from __future__ import absolute_import, print_function
import unittest
import re
from pathlib2 import Path
from fabric.api import *
from tempfile import NamedTemporaryFile



class Mixin(object):
    def __init__(self, *args):
        unittest.TestCase.__init__(self, *args)


class TopLimitMixin(Mixin):
    def _set_limits(self):
        self.start = None
        self.stop = 3

class BottomLimitMixin(Mixin):

    def _set_limits(self):
        self.start = re.compile('thr(e)+')
        self.stop = None



class UtilTestCase(unittest.TestCase):
    """
    Tests for internal utility functions that don't run sed
    """
    def test_choose_delim(self):
        from fabtools.edit import _choose_delim

        self.assertEqual(_choose_delim('hi'), '#')
        self.assertEqual(_choose_delim('hi#'), '/')
        self.assertEqual(_choose_delim('hi#/'), '@')
        with self.assertRaises(RuntimeError):
            _choose_delim('#/_@')

    def test_mk_selector(self):
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



class EditTestCase(unittest.TestCase):
    """
    Tests for sed invocations
    """

    def _set_limits(self):
        self.start = None
        self.stop = None

    def setUp(self):
        self._set_limits()
        with NamedTemporaryFile(delete=False) as dat:
            self.textfile = Path(dat.name)
            dat.write('one\ntwo\nthree\nfour\nfive\nsix\nseven\n')

    def tearDown(self):
        self.textfile.unlink()


    def test_find(self):
        from fabtools.edit import find
        import re

        self.assertEquals(find('one', self.textfile, start=self.start, stop=self.stop, use_sudo=local),
                          [1] if not self.start else [])
        self.assertEquals(find('three', self.textfile, start=self.start, stop=self.stop, use_sudo=local), [3])
        self.assertEquals(find('five', self.textfile, start=self.start, stop=self.stop, use_sudo=local),
                          [5] if not self.stop else [])

        self.assertEqual(find('not one', self.textfile, start=self.start, stop=self.stop, use_sudo=local), [])
        self.assertEqual(find(re.compile('t[whre]+[eo]'), self.textfile, start=self.start, stop=self.stop,
                              do_all=True, use_sudo=local), [2,3] if not self.start else [3])
        self.assertEqual(find(re.compile('o..e'), self.textfile, start=self.start, stop=self.stop, use_sudo=local), [])
        self.assertEqual(find(re.compile('^two$'), self.textfile, start=self.start, stop=self.stop, use_sudo=local),
                         [2] if not self.start else [])
        self.assertEqual(find('one\ntwo\nthree', self.textfile, start=self.start, stop=self.stop, use_sudo=local), [])
        self.assertEqual(find('one\ntwo\nthree', self.textfile, multi_line=True, use_sudo=local), [7])
        self.assertEqual(find('one\ntwo\nthree', self.textfile, multi_line=True, do_all=True, use_sudo=local), [7])

    def test_prepend(self):
        from fabtools.edit import prepend, find
        text = 'hi there'
        prepend(text, self.textfile, pat='two', start=self.start, stop=self.stop, use_sudo=local)
        prepend(text, self.textfile, pat='five', start=self.start, stop=self.stop, use_sudo=local)
        self.assertEqual(find(text, self.textfile, start=self.start, stop=self.stop, do_all=True, use_sudo=local),
                         [2] if self.stop else [5] if self.start else [2, 6])
        #"Failed on text='{text}', limit={limit}, pat={pat}".format(text, str(limit), str(pat)))

    def test_append(self):
        from fabtools.edit import append, find
        text = 'howdy'
        append(text, self.textfile, pat='three', use_sudo=local)
        self.assertEqual(find(text, self.textfile, do_all=True, use_sudo=local), [4])


class TopLimitedEditTestCase(TopLimitMixin, EditTestCase):
    pass

class BottomLimitedEditTestCase(BottomLimitMixin, EditTestCase):
    pass

def suite():
    return unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(UtilTestCase),
        unittest.TestLoader().loadTestsFromTestCase(EditTestCase),
        unittest.TestLoader().loadTestsFromTestCase(TopLimitedEditTestCase),
        unittest.TestLoader().loadTestsFromTestCase(BottomLimitedEditTestCase),
    ])

@task
def do_all_tests():
    pass
