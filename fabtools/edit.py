'''
Edit tools
==========

Tools for performing batch edits of files on the target system. Implemended using sed.
'''

from pipes import quote
import re
from pathlib2 import Path

_IN_MEMORY = '1h;2,$H;$!d;g'  # sed magic to do in-memory processing for multiline patterns

def _mk_sed_cmd(op, files, args=None, start=None, end=None, opts=None, delim='+',  **kwargs):
    '''
    Create the command string for running sed on the target system
    :param op: sed operation
    :param file: target file path as Path object
    :param start: first address pattern (int, string, or regex. String will be regex escaped)
    :param end: second address pattern (int, string, or regex. String will be regex escaped)
    :param opts: extra sed opts
    :param args: sed operator args
    :param kwargs:
    :return: fully prepared shell command for sed operation
    '''

    assert op in list('aiscd')
    assert isinstance(files,Path) or type(files) is list

    files = files if type(files) is list else [files]
    return 'sed {opts} -e {cmd} {args}'.format(
        opts=quote('-' + opts) if opts else '',
        cmd=quote("{start}{end}{op}".format (
            start=_mk_selector(start, delim=delim),
            end=',' + _mk_selector(end, delim=delim) if end else '',
            op=op)),
        args=' '.join([quote(x) for x in args]) if args else '',
        files=' '.join([quote(str(x)) for x in list(files)])
    )


def contains_line(pat, all=False):
    '''
    Checks for the presence of line(s) that match the pattern
    :param pat: literal string or compiled regex
    :return: line number(s) if found, None if not
    '''
    pass


def contains(pat, end_pat):
    '''
    Search for text matching the pattern, which may span multiple lines by using '\\n'
    :param pat: literal string or compiled regex
    :return: 1 if found, None if not
    '''
    pass


def prepend(text, pat=1, do_all=False):
    '''
    Prepend text ahead of line matching pattern [defaults to first line]. If do_all is true then every line matching
    the pattern will be processed.
    :param text: text to insert
    :param pat: pattern to match
    :param do_all:
    :return:
    '''
    pass


def append(text, pat='$', all=False):
    '''
    Prepend text ahead of line matching pattern [defaults to first line]. If do_all is true then every line matching
    the pattern will be processed.
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





_REGEX_TYPE = type(re.compile('foo'))

def _mk_selector(sel, delim='+'):
    if sel is None:
        return ''
    elif type(sel) is int:
        return str(sel)
    elif type(sel) is str:
        return '{0}{1}{0}'.format(delim, re.escape(sel))
    elif type(sel) is _REGEX_TYPE:
        return '{0}{1}{0}'.format(delim, sel.pattern)
    else:
        raise TypeError('Illegal type for pattern %s' % str(type(sel)))


