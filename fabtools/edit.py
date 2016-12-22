'''
Edit tools
==========

Tools for performing batch edits of files on the target system. Implemended using sed.
'''

from pipes import quote
import re
from pathlib2 import Path
from fabric.api import *

_IN_MEMORY = '1h;2,$H;$!d;g'  # sed magic to do in-memory processing for multiline patterns

def _mk_sed_cmd(op, files, args=None, start=None, end=None, opts=None, inmem=False,  **kwargs):
    '''
    Create the command string for running sed on the target system. If multiple files are specified then they will
    be concatenated unless the '-s' option is specified.
    :param op: sed operation
    :param files: target file(s) path as Path object or list of Paths.
    :param start: first address pattern (int, string, or regex. String will be regex escaped)
    :param end: second address pattern (int, string, or regex. String will be regex escaped)
    :param opts: extra sed opts
    :param inmem: if true then pull file into memory and apply pattern and edits accross all lines
    :param args: sed operator args
    :param kwargs:
    :return: fully prepared shell command for sed operation
    '''

    assert op in list('aiscd=')
    assert isinstance(files,Path) or type(files) is list


    files = files if type(files) is list else [files]
    return "sed -r {opts} {inmem} -e '{cmd}' {args} {files}".format(
        opts=' '.join(opts) if opts else '',
        inmem="-e '%s'" % _IN_MEMORY if inmem else '',
        cmd='{start}{end}{op}'.format (
            start=_mk_selector(start),
            end=',%s' % _mk_selector(end) if end else '',
            op=op),
        args=' '.join([quote(x) for x in args]) if args else '',
        files=' '.join([quote(str(x)) for x in list(files)])
    )


def contains_line(pat, files, use_sudo=False):
    '''
    Checks for the presence of line(s) that match the pattern, which cannot contain '\\n'. If multiple files are
    specified then they will be concatenated unless the '-s' option is specified.
    :param pat: literal string or compiled regex
    :param files: files to search
    :return: line number(s) if found, None if not
    '''
    try:
        res = int(_run_func(use_sudo)(_mk_sed_cmd('=', files, start=pat, opts=['-n'])))
        return res
    except ValueError as e:
        return None


def contains(pat, files, use_sudo=False):
    '''
    Search for text matching the pattern, which may span multiple lines by using '\\n'. If multiple files are
    specified then they will be concatenated unless the '-s' option is specified.
    :param pat: literal string or compiled regex
    :param files: files to search
    :return: 1 if found, None if not
    '''
    try:
        res = int(_run_func(use_sudo)(_mk_sed_cmd('=', files, start=pat, opts=['-n'], inmem=True)))
        return res
    except ValueError as e:
        return None


def prepend(text, files, pat=1, bak='', do_all=False, use_sudo=False):
    '''
    Prepend text ahead of line matching pattern [defaults to first line]. If do_all is true then every line matching
    the pattern will be processed. This function acts on each specified file independently and in-place.
    :param text: text to insert
    :param pat: pattern to match
    :param bak: if not empty then a backup file will be created with this extension.
    :param do_all: prepend text before every occurrance of the pattern
    :return:
    '''
    _run_func(use_sudo)(_mk_sed_cmd('=', files, start=pat, opts=['-n'], inmem=True))


def append(text, pat='$', all=False):
    '''
    Prepend text ahead of line matching pattern [defaults to first line]. If do_all is true then every line matching
    the pattern will be processed. This function acts on each specified file independently and in-place.
    :param text:
    :param pat:
    :param do_all:
    :return:
    '''
    pass


def delete(pat, end_pat=None, all=False):
    pass


def replace_line(pat, text, all = False):
    pass


def replace(pat, text, all=False):
    '''
    Search for text matching the pattern, which may (span multiple lines by using \\n)
    and replace it with the given text, which may contain sed backreferences (\\1, etc.)
    :param pat: literal string or compiled regex
    :return: 1 if found, None if not
    '''
    pass


def _captured_local(*args, **kwargs):
    return local(*args, capture=True, **kwargs)


def _run_func(sudo_arg):
    '''
    Resolve the appropriate run function for fabric to use for normal(run()), sudo, or local execution
    :param sudo_arg:
    :return: the run function
    '''
    if not sudo_arg:
        return run
    elif sudo_arg is True:
        return sudo
    elif sudo_arg is local:
        return _captured_local
    elif sudo_arg in [run, sudo]:
        return sudo_arg


_REGEX_TYPE = type(re.compile('foo'))

def _mk_selector(sel):
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


_DELIM_CHARS = {'@', '#', '/', '_'}
def _choose_delim(pat):
    delims = _DELIM_CHARS - set(str(pat))
    if not delims:
        raise RuntimeError("No usable delimiter characters for pattern %s" % pat)
    return sorted(list(delims))[0]
