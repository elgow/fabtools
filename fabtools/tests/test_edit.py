from __future__ import absolute_import, print_function
import unittest
import re
from pathlib2 import Path
from fabric.api import *
from tempfile import NamedTemporaryFile

# our test text
_TEST_TEXT = '''\
one
two
three
four
five
six
seven'''

class Mixin(object):
    """
    Mixin base class that calls unit test __init__ to make it all work
    """
    def __init__(self, *args):
        unittest.TestCase.__init__(self, *args)


class TopLimitMixin(Mixin):
    """
    Mixin that limits non-multi-line operations to the first three lines
    """
    def _set_limits(self):
        self.start = None
        self.stop = 3

class BottomLimitMixin(Mixin):
    """
    Mixin that limits non-multi-line operations to skip the first three lines using a pattern, which can get weird
    """
    def _set_limits(self):
        self.start = re.compile('f[ou]+r')
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
    Tests for sed invocations. These get run three times, no limits, top limit, bottom limit
    """

    def _set_limits(self):
        """
        default to no limits
        :return:
        """
        self.start = None
        self.stop = None

    def setUp(self):
        self._set_limits()
        with NamedTemporaryFile(delete=False) as dat:
            self.textfile = Path(dat.name)
            dat.write(_TEST_TEXT)

    def tearDown(self):
        self.textfile.unlink()

    def test_find(self):
        from fabtools.edit import find
        import re

        self.assertEquals(find('one', self.textfile, start=self.start, stop=self.stop, use_sudo=local),
                          [1] if not self.start else [])
        self.assertEquals(find('three', self.textfile, start=self.start, stop=self.stop, use_sudo=local),
                          [3] if not self.start else [])
        self.assertEquals(find('five', self.textfile, start=self.start, stop=self.stop, use_sudo=local),
                          [5] if not self.stop else [])

        self.assertEqual(find('not one', self.textfile, start=self.start, stop=self.stop, use_sudo=local), [])
        self.assertEqual(find(re.compile('t[whre]+[eo]'), self.textfile, start=self.start, stop=self.stop,
                              do_all=True, use_sudo=local), [2, 3] if not self.start else [])
        self.assertEqual(find(re.compile('o..e'), self.textfile, start=self.start, stop=self.stop, use_sudo=local), [])
        self.assertEqual(find(re.compile('^two$'), self.textfile, start=self.start, stop=self.stop, use_sudo=local),
                         [2] if not self.start else [])
        self.assertEqual(find('one\ntwo\nthree', self.textfile, start=self.start, stop=self.stop, use_sudo=local), [])
        self.assertEqual(find('one\ntwo\nthree', self.textfile, multi_line=True, use_sudo=local), [7])
        self.assertEqual(find('one\ntwo\nthree', self.textfile, multi_line=True, do_all=True, use_sudo=local), [7])
        # multi-file case
        self.assertEqual(find('three', [self.textfile, self.textfile], start=self.start, stop=self.stop,
                              do_all=True, use_sudo=local),
                         ([3] if not self.start else []) + ([10] if not self.stop else []))

    def test_prepend(self):
        from fabtools.edit import prepend, find
        text = 'hi there'
        # test prepend twice, sometimes limited to once by range limit
        prepend(text, self.textfile, pat='two', start=self.start, stop=self.stop, use_sudo=local)
        prepend(text, self.textfile, pat='five', start=self.start, stop=self.stop, use_sudo=local)
        self.assertEqual(find(text, self.textfile, start=self.start, stop=self.stop, do_all=True, use_sudo=local),
                         [2] if self.stop else [5] if self.start else [2, 6])

    def test_append(self):
        from fabtools.edit import append, find
        text = 'howdy'
        # test basic append after match
        append(text, self.textfile, pat='three', use_sudo=local)
        self.assertEqual(find(text, self.textfile, do_all=True, use_sudo=local), [4])


    def test_delete(self):
        from fabtools.edit import delete, find
        # test basic single line delete
        delete('two', self.textfile, start=self.start, stop=self.stop, use_sudo=local)
        self.assertEqual(find('two', self.textfile, multi_line=True, use_sudo=local),
                         [] if not self.start else [7])

    def test_replace(self):
        from fabtools.edit import replace, find
        # test first line replace with regex pattern that matches more than one line
        replace(re.compile('^s.*'), 'blah', self.textfile, start=self.start, stop=self.stop, use_sudo=local)
        self.assertEqual(find('blah', self.textfile, use_sudo=local),
                         [6] if not self.stop else [])
        self.assertEqual(find('seven', self.textfile, use_sudo=local), [7])
        self.assertEqual(find('six', self.textfile, multi_line=True, use_sudo=local),
                         [7] if self.stop else [])
        # test regex pattern w/ backref replace in multi-line block
        replace(re.compile('(thr)e+'), '\\1 \\1\n\\1 \\1\n\\1 \\1', self.textfile,
                start=self.start, stop=self.stop, use_sudo=local)
        self.assertEqual(find('thr thr', self.textfile, do_all=True, use_sudo=local),
                         [3, 4, 5] if not self.start else [])
        print("three at %s "  % find('three', self.textfile, multi_line=True, use_sudo=local))
        self.assertEqual(find('three', self.textfile, multi_line=True, use_sudo=local),
                         [7] if self.start else [])
        # test do_all replace of multiple instances of a string in multiple lines
        replace('thr', 'well', self.textfile, do_all=True,
                start=self.start, stop=self.stop, use_sudo=local)
        self.assertEqual(find('well well', self.textfile, do_all=True, use_sudo=local),
                         [3, 4, 5] if not (self.stop or self.start) else [3] if self.stop else [])
        self.assertEqual(find('thr', self.textfile, multi_line=True, use_sudo=local),
                         [7] if self.start else [9] if self.stop else [])


    def test_capture(self):
        from fabtools.edit import capture
        # test regex grep capture of all lines
        self.assertEqual(capture(re.compile('^t'), self.textfile, do_all=True,
                                 start=self.start, stop=self.stop, use_sudo=local).split(),
                         ['two', 'three'] if not self.start else [])
        # test w/o do_all get only first line
        self.assertEqual(capture(re.compile('^t'), self.textfile,
                                 start=self.start, stop=self.stop, use_sudo=local).split(),
                         ['two'] if not self.start else [])
        # multi-line positive
        self.assertEqual(capture('two', self.textfile, multi_line=True,
                                 start=self.start, stop=self.stop, use_sudo=local).split(),
                         _TEST_TEXT.split())
        # multi-line negative
        self.assertEqual(capture('NOT IN FILE', self.textfile, multi_line=True,
                                 start=self.start, stop=self.stop, use_sudo=local).split(),
                         [])




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
