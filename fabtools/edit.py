"""
Edit tools
==========

Tools for performing batch edits of files on the target system. Implemended using sed.
"""

from pipes import quote
import re
from pathlib2 import Path
from fabric.api import *


_IN_MEMORY = '1h;2,$H;$!d;g'  # sed magic to do in-memory processing for multi-line pattern search
_END = re.compile('$')
_DELIM_CHARS = {'@', '#', '/', '_', '~', '`'}  # chars for address pattern delimiter auto-selection


def find(pat, files,  start=None, stop=None, multi_line=False, do_all=False, use_sudo=False):
    """
    Locates line(s) that match the pattern. In multi-line mode the pattern may span lines with \n, but the
    value returned will always be the total number of lines in the file.
    :param pat: search pattern (line number, literal string or compiled regex)
    :param files: files to search. Multiple files will be concatenated.
    :param start: Limit processing to start at this pattern (line number, literal string or compiled regex)
    :param stop: Limit processing to stop at this pattern (line number, literal string or compiled regex)
    :param multi_line: treat entire file as one line so pattern may contain '\n'
    :param do_all: find all lines w/ pattern. No effect in multi_line mode.
    :param use_sudo: True/False for use of sudo or specify run, sudo, or local from Fabric
    :return: list of line number(s) where pattern was found, empty list if not found
    """
    op = '=' if do_all else '{=;q}'
    cmd = '{sel}{op}'.format(
        sel=_mk_selector(pat),
        op=op)
    lim_cmd = cmd if multi_line else _mk_limit_sed_cmd(cmd, start=start, stop=stop)
    res = _run_func(use_sudo)(_mk_sed_call(lim_cmd, files, inmem=multi_line,  opts=['-n']))
    return [int(n) for n in res.split('\n')] if res else []


def append(text, files, pat=_END, start=None, stop=None, do_all=False, backup=None, use_sudo=False):
    """
    Append text after the pattern, or at end of file by default
    :param text: text to insert.  May contain \n to insert multi-line block
    :param files: files to process. Mulitple files will be processed separately
    :param pat: search pattern (line number, literal string or compiled regex) [default = eof]
    :param start: Limit processing to start at this pattern (line number, literal string or compiled regex)
    :param stop: Limit processing to stop at this pattern (line number, literal string or compiled regex)
    :param do_all: process all lines w/ pattern.
    :param backup: if specified then a backup file will be created with this suffix appended to the name
    :param use_sudo: True/False for use of sudo or specify run, sudo, or local from Fabric
    """
    _add_line('a', text, files, pat=pat, start=start, stop=stop, do_all=do_all, backup=backup, use_sudo=use_sudo)



def prepend(text, files, pat=1, start=None, stop=None, do_all=False, backup=None, use_sudo=False):
    """
    Prepend text before the pattern, or at beginning of file by default
    :param text: text to insert.  May contain \n to insert multi-line block
    :param files: files to process. Mulitple files will be processed separately.
    :param pat: search pattern (line number, literal string or compiled regex) [default = eof]
    :param files: files to search
    :param start: Limit processing to start at this pattern (line number, literal string or compiled regex)
    :param stop: Limit processing to stop at this pattern (line number, literal string or compiled regex)
    :param do_all: process all lines w/ pattern.
    :param backup: if specified then a backup file will be created with this suffix appended to the name
    :param use_sudo: True/False for use of sudo or specify run, sudo, or local from Fabric
    """
    _add_line('i', text, files, pat=pat, start=start, stop=stop, do_all=do_all, backup=backup, use_sudo=use_sudo)


def replace_line(pat, text, files, start=None, stop=None, do_all=False, backup=None, use_sudo=False):
    """
    Replace line(s) that match the pattern with specified text
    :param pat: search pattern (line number, literal string or compiled regex) [required]
    :param text: text to replace with.  May contain \n to insert multi-line block
    :param files: files to search. Mulitple files will be processed separately.
    :param start: Limit processing to start at this pattern (line number, literal string or compiled regex)
    :param stop: Limit processing to stop at this pattern (line number, literal string or compiled regex)
    :param do_all: process all lines w/ pattern.
    :param backup: if specified then a backup file will be created with this suffix appended to the name
    :param use_sudo: True/False for use of sudo or specify run, sudo, or local from Fabric
    """
    _add_line('c', text, files, pat=pat, start=start, stop=stop, do_all=do_all, backup=backup, use_sudo=use_sudo)


def delete(pat, files, start=None, stop=None, do_all=False, backup=None, use_sudo=False):
    """
    Delete lines that match the pattern
    :param pat: search pattern (line number, literal string or compiled regex) [required]
    :param files: files to process. Mulitple files will be processed separately.
    :param start: Limit processing to start at this pattern (line number, literal string or compiled regex)
    :param stop: Limit processing to stop at this pattern (line number, literal string or compiled regex)
    :param do_all: process all lines w/ pattern.
    :param backup: if specified then a backup file will be created with this suffix appended to the name
    :param use_sudo: True/False for use of sudo or specify run, sudo, or local from Fabric
    """
    suffix = quote(backup) if backup else ''
    cmd = "%sd" % (_mk_selector(pat),) if do_all else \
           "%s{d; b L}; b; :L  {n; b L}" % (_mk_selector(pat),)
    lim_cmd = _mk_limit_sed_cmd(cmd, start=start, stop=stop)
    _run_func(use_sudo)(_mk_sed_call(lim_cmd, files, opts=['-i%s' % (suffix,), '-s'], do_all=do_all, use_sudo=use_sudo))


def replace(pat, text, files, start=None, stop=None, do_all=False, backup=None, use_sudo=False):
    """
    Search for text matching the pattern, which may (span multiple lines by using \\n in multi-line mode)
    and replace it with the given text, which may contain sed backreferences (\\1, etc.)
    This differs from replace_line in that it only replaces the match text, not the whole line.
    :param pat: line_number, literal string or compiled regex
    :param text: text to replace
    :param files: files to process. Multiple files will be processed separately
    :param start: Limit processing to start at this pattern (line number, literal string or compiled regex)
    :param stop: Limit processing to stop at this pattern (line number, literal string or compiled regex)
    :param do_all: replace every occurrance of the pattern
    :param backup: if specified then a backup file will be created with this suffix appended to the name
    :param use_sudo: True/False for use of sudo or specify run, sudo, or local from Fabric
    :return:
    """
    escaped_text = text.replace('\n', '\\n')
    suffix = quote(backup) if backup else ''

    if type(pat) is str:
        sel = re.escape(pat)
    elif type(pat) is type(_END):
        sel = pat.pattern
    else:
        raise RuntimeError("Replace pattern must be string or regex, not %s" % str(pat))

    cmd = "{addr}s{delim}{sel}{delim}{text}{delim}g".format(
            addr=_mk_selector(pat), delim=_choose_delim(sel+text), sel=sel, text=escaped_text) if do_all \
         else "{addr}{{s{delim}{sel}{delim}{text}{delim}; b L}}; b; :L  {{n; b L}}".format(
            addr=_mk_selector(pat), delim=_choose_delim(sel + text), sel=sel, text=escaped_text)
    lim_cmd = _mk_limit_sed_cmd(cmd, start=start, stop=stop)
    _run_func(use_sudo)(_mk_sed_call(lim_cmd, files, opts=['-i%s' % (suffix,), '-s'],
                                     do_all=do_all, use_sudo=use_sudo))


def capture(pat, files, start=None, stop=None, multi_line=False, do_all=False, use_sudo=False):
    """
    Find and return the text selected by the pattern within start/stop limits
    :param pat: line number, literal string or compiled regex
    :param files: files to process. Multiple files will be concatenated
    :param start: Limit processing to start at this pattern (line number, literal string or compiled regex)
    :param stop: Limit processing to stop at this pattern (line number, literal string or compiled regex)
    :param multi_line: treat entire file as one line so pattern may contain '\n'
    :param do_all: find all lines w/ pattern. No effect in multi_line mode. [defaults to False, so only gets first]
    :param use_sudo: True/False for use of sudo or specify run, sudo, or local from Fabric
    :return: selected text
    """
    op = 'p' if do_all else '{p;q}'
    cmd = '%s%s' % (_mk_selector(pat), op)
    lim_cmd = cmd if multi_line else _mk_limit_sed_cmd(cmd, start=start, stop=stop)
    res = _run_func(use_sudo)(_mk_sed_call(lim_cmd, files, inmem=multi_line,  opts=['-n']))
    return res



####### Internal functions ###########

def _captured_local(*args, **kwargs):
    """
    Wrapper on fabric local() to capture the output to match the behavior of run() and sudo()
    :param args:
    :param kwargs:
    :return:
    """
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
    elif type(sel) is type(_END):
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


def _mk_limit_sed_cmd(op, args=None, start=None, stop=None):
    """
    Create a sed command that wraps any other sed command in start,stop limits
    :param op: sed command to be wrapped
    :param args: optional more of sed command
    :param start: start limit (line number, literal string, or regex). Defaults to 1.
    :param stop: start limit (line number, literal string, or regex). Defaults to end of file.
    :return: wrapped sed command
    """
    cmd = '{start}{stop}{{{op}{args}}}'.format(
        start=_mk_selector(start) if start else '1',
        stop=',%s' % (_mk_selector(stop) if stop else '$',),
        op=op,
        args=args if args else '')
    return cmd


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


def _add_line(op, text, files, pat=_END, start=None, stop=None, do_all=False, backup=None, use_sudo=False):
    """
    Append text after line matching pattern [defaults to last line]. If do_all is true then every line matching
    the pattern will be processed. This function acts on each specified file independently and in-place.
    :param text: text to insert. May contain \n, so block of lines is OK. Sed will process '\' escaped chars.
    :param files: files to process, separately and in-place
    :param pat: pattern to match
    :param bak: if not empty then a backup file will be created with this extension.
    :param do_all: prepend text before every occurrance of the pattern
    :param use_sudo: True/False for use of sudo or specify run, sudo, or local from Fabric
    :return:
    """
    assert op in list('aic')
    escaped_text = text.replace('\n', '\\n')
    suffix = quote(backup) if backup else ''
    cmd = "%s%s \\\n%s\n" % (_mk_selector(pat), op, escaped_text) if do_all else \
           "%s{%s \\\n%s\n; b L}; b; :L  {n; b L}" % (_mk_selector(pat), op, escaped_text)
    lim_cmd = _mk_limit_sed_cmd(cmd, start=start, stop=stop)
    _run_func(use_sudo)(_mk_sed_call(lim_cmd, files, opts=['-i%s' % suffix, '-s'],  do_all=do_all, use_sudo=use_sudo))


