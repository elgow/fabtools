"""
Edit tools
==========

Tools for performing batch edits of files on the target system. Implemended using sed.
"""

from pipes import quote
import re
from pathlib2 import Path
from fabric.api import *


_IN_MEMORY = '1h;2,$H;$!d;g'  # sed magic to do in-memory processing for multi-line patterns
_REGEX_TYPE = type(re.compile('foo'))
_DELIM_CHARS = {'@', '#', '/', '_'}  # chars for address pattern delimiter auto-selection


def find(pat, files, multi_line=False, do_all=True, use_sudo=False):
    """
    Locates line(s) that match the pattern, which cannot contain '\\n'. If multiple files are
    specified then they will be concatenated.
    :param pat: literal string or compiled regex
    :param files: files to search
    :param multi_line: treat entire file as one line so pattern may contain '\n'
    :param do_all: find all lines w/ pattern. No effect in multi_line mode.
    :param use_sudo: True/False for use of sudo or specify run, sudo, or local from Fabric
    :return: list of line number(s) where found, empty list if not found
    """
    op = '=' if do_all else '{=;q}'
    cmd = '{sel}{op}'.format(
        sel=_mk_selector(pat),
        op=op)

    res = _run_func(use_sudo)(_mk_sed_call(cmd, files, inmem=multi_line,  opts=['-n']))
    return [int(n) for n in res.split('\n')] if res else []


def add_line(text, files, pat='$', op='a', do_all=False, use_sudo=False):
    """
    Append text after line matching pattern [defaults to last line]. If do_all is true then every line matching
    the pattern will be processed. This function acts on each specified file independently and in-place.
    :param text: text to insert
    :param files: files to process, separately and in-place
    :param pat: pattern to match
    :param bak: if not empty then a backup file will be created with this extension.
    :param do_all: prepend text before every occurrance of the pattern
    :param use_sudo: True/False for use of sudo or specify run, sudo, or local from Fabric
    :return:
    """
    assert op in list('aic')
    cmd = "%s%s \\\n%s\n" % (_mk_selector(pat), op, text) if do_all else \
           "%s{%s \\\n%s\n; b L}; b; :L  {n; b L}" % (_mk_selector(pat), op, text)
    _run_func(use_sudo)(_mk_sed_call(cmd, files, opts=['-i'],  do_all=do_all, use_sudo=use_sudo))


def delete(pat, files, end_pat=None, do_all=False, use_sudo=False):
    pass


def replace_line(pat, files, text, do_all=False, use_sudo=False):
    pass


def replace(pat, files, text, do_all=False, use_sudo=False):
    """
    Search for text matching the pattern, which may (span multiple lines by using \\n)
    and replace it with the given text, which may contain sed backreferences (\\1, etc.)
    :param pat: literal string or compiled regex
    :param text: text to insert
    :param do_all: prepend text before every occurrance of the pattern
    :param use_sudo: True/False for use of sudo or specify run, sudo, or local from Fabric
    :return:
    """
    pass


def _captured_local(*args, **kwargs):
    return local(*args, capture=True, **kwargs)


def _run_func(sudo_arg):
    """
    Resolve the appropriate run function for fabric to use for normal(run()), sudo(), or local() execution
    :param sudo_arg:
    :return: the run function
    """
    if not sudo_arg:
        return run
    elif sudo_arg is True:
        return sudo
    elif sudo_arg is local:
        return _captured_local
    elif sudo_arg in [run, sudo]:
        return sudo_arg


def _mk_selector(sel):
    """
    Make a properly formatted sed selector for line number, literal string, or regex.
    :param sel: int, string, or compiled regex
    :return: ready to use sed selector, e.g. '\#regex#'
    """
    if sel is None:
        return ''
    elif type(sel) is int:
        return str(sel)
    elif type(sel) is str:
        pat = re.escape(sel)
        return '\\{0}{1}{0}'.format(_choose_delim(pat), pat)
    elif type(sel) is _REGEX_TYPE:
        pat = sel.pattern
        return '\\{0}{1}{0}'.format(_choose_delim(pat), pat)
    else:
        raise TypeError('Illegal type for pattern %s' % str(type(sel)))


def _choose_delim(pat):
    """
    Choose a delimiter for sed pattern addr that does not collide with chars in the pattern
    :param pat: The addr pattern
    :return: delim char
    """
    delims = _DELIM_CHARS - set(str(pat))
    if not delims:
        raise RuntimeError("No usable delimiter characters for pattern %s" % pat)
    return sorted(list(delims))[0]


def _mk_generic_sed_cmd(op, args=None, start=None, end=None):
    cmd = '{start}{end}{op}{args}'.format(
        start=_mk_selector(start),
        end=',%s' % _mk_selector(end) if end else '',
        op=op,
        args=args if args else '')

def _mk_do_once_cmd(pat, op, text):
    """
    Create a sed command to execute an a, i, or c command just once rather than for every matching line.
    :param pat: selection pattern (line number, literal string, or compiled regex)
    :param op: 'a', 'i', or 'c'
    :param text: text to be inserted by sed
    :return: sed command suitable for use in sed -e '<cmd>'
    """
    assert op in list('aic')
    return "%s{%s \\\n%s\n; b L}; b; :L  {n; b L}" % (_mk_selector(pat), op, text)


def _mk_sed_call(cmd, files, opts=None, inmem=False,  **kwargs):
    """
    Create the shell command string for running sed on the target system. If multiple files are specified
    then they will be concatenated unless the '-s' option is specified.
    :param op: sed operation
    :param files: target file(s) path as Path object or list of Paths.
    :param start: first address pattern (int, string, or regex. String will be regex escaped)
    :param end: second address pattern (int, string, or regex. String will be regex escaped)
    :param opts: extra sed opts
    :param inmem: if true then pull file into memory and apply pattern and edits accross all lines
    :param args: sed operator args
    :param kwargs:
    :return: fully prepared shell command for sed operation
    """

    files = (files,) if isinstance(files, basestring) or isinstance(files, Path) else files
    return "sed -r {opts} {inmem} -e '{cmd}' {files}".format(
        opts=' '.join(opts) if opts else '',
        inmem="-e '%s'" % _IN_MEMORY if inmem else '',
        cmd=cmd,
        files=' '.join([quote(str(x)) for x in files])
    )
