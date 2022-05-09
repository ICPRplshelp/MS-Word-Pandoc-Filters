"""Most of the helper functions to converter.py and any other modules.

I/O functions are NOT allowed.
"""
# import json
import logging
import math
from dataclasses import dataclass, fields
from typing import Optional, Iterable, Callable, Union, Any

# ch = logging.StreamHandler()
# ch.setLevel(logging.DEBUG)
PREAMBLE_PATH = ('preamble.txt', 'preamble_LTable.txt', 'preamble_light.txt')

APA_MODE = True
ALPHABET = 'abcdefghijklmnopqrstuvwxyz'
ALPHABET_ALL = ALPHABET + ALPHABET.upper() + '1234567890-+.,*/?!='
MAX_PAGE_LENGTH = 35
ALLOW_SPACES_IN_LANGUAGES = True
ENV_FORBIDDEN = ['table', 'tabular', 'longtable', 'minipage', 'texttt', 'enumerate', 'itemize',
                 'align*', 'gather', 'matrix', 'bmatrix', 'pmatrix', 'vmatrix', 'Bmatrix',
                 'Vmatrix']
MINTED_LANGUAGES = {'cucumber', 'abap', 'ada', 'ahk', 'antlr', 'apacheconf', 'applescript', 'as', 'aspectj', 'autoit',
                    'asy', 'awk', 'basemake', 'bash', 'bat', 'bbcode', 'befunge', 'bmax', 'boo', 'bro',
                    'bugs', 'c', 'ceylon', 'cfm', 'cfs', 'cheetah', 'clj', 'cmake', 'cobol', 'cl', 'console', 'control',
                    'coq', 'cpp', 'croc', 'csharp', 'css', 'cuda', 'cyx', 'd', 'dg', 'diff', 'django', 'dpatch', 'duel',
                    'dylan', 'ec', 'erb', 'evoque', 'fan', 'fancy', 'fortran', 'gas', 'genshi', 'glsl', 'gnuplot', 'go',
                    'gosu', 'groovy', 'gst', 'haml', 'haskell', 'hxml', 'html', 'http', 'hx', 'idl', 'irc', 'ini',
                    'java', 'jade', 'js', 'json', 'jsp', 'kconfig', 'koka', 'lasso', 'livescrit', 'llvm', 'logos',
                    'lua', 'mako', 'mason', 'matlab', 'minid', 'monkey', 'moon', 'mxml', 'myghty', 'mysql', 'nasm',
                    'newlisp', 'newspeak', 'numpy', 'ocaml', 'octave', 'ooc', 'perl', 'php', 'plpgsql', 'postgresql',
                    'postscript', 'pot', 'prolog', 'psql', 'puppet', 'python', 'qml', 'ragel', 'raw', 'ruby', 'rhtml',
                    'sass', 'scheme', 'smalltalk', 'sql', 'ssp', 'tcl', 'tea', 'tex', 'text', 'vala', 'vgl', 'vim',
                    'xml', 'xquery', 'yaml', 'ts'}

LISTING_LANGUAGES = {'ABAP', 'ACSL', 'Ada', 'Algol', 'Ant', 'Assembler', 'Awk', 'bash', 'Basic', 'C', 'C++', 'Caml',
                     'CIL', 'Clean', 'Cobol', 'Comal', '80', 'command.com', 'Comsol', 'csh', 'Delphi', 'Eiffel', 'Elan',
                     'erlang', 'Euphoria', 'Fortran', 'GCL', 'Gnuplot', 'Haskell', 'HTML', 'IDL', 'inform', 'Java',
                     'JVMIS', 'ksh', 'Lingo', 'Lisp', 'Logo', 'make', 'Mathematica', 'Matlab', 'Mercury', 'MetaPost',
                     'Miranda', 'Mizar', 'ML', 'Modula-2', 'MuPAD', 'NASTRAN', 'Oberon-2', 'OCL', 'Octave', 'Oz',
                     'Pascal', 'Perl', 'PHP', 'PL/I', 'Plasm', 'PostScript', 'POV', 'Prolog', 'Promela', 'PSTricks',
                     'Python', 'R', 'Reduce', 'Rexx', 'RSL', 'Ruby', 'S', 'SAS', 'Scilab', 'sh', 'SHELXL', 'Simula',
                     'SPARQL', 'SQL', 'tcl', 'TeX', 'VBScript', 'Verilog', 'VHDL', 'VRML', 'XML', 'XSLT', 'ts'}


class MinipageInLongtableError(Exception):
    def __str__(self) -> str:
        """Return a string representation of this
        exception.
        """
        return 'Minipages in longtables detected. Check if your tables have lists, ' \
               'or choose a different config mode - perhaps one with ' \
               'eliminate longtables set to off.'


def deduce_preamble_mode(tex_file: str) -> int:
    """Longtable?
    """
    if '\\begin{longtable}' in tex_file:
        # print('Has a longtable')
        return 0
    else:
        # print('Does not have a longtable')
        return 2


def insert_in_preamble(tex_file: str, file_text: str) -> str:
    """Insert in preamble
    """
    # have it insert right before the document starts
    title_index = find_nth(tex_file, '\\begin{document}', 1)
    newest_text = tex_file[:title_index] + '\n' + file_text + '\n' + tex_file[title_index:]
    return newest_text


def many_instances(old_tex: str, tex_file: str, todo_str: str) -> str:
    """Many instances
    """
    while True:
        try:
            old_tex, tex_file = one_instance(old_tex, tex_file, todo_str)
        except AssertionError:
            break
    return tex_file


def longtable_split_detector(text: str) -> str:
    """Split the longtable.

    Preconditions:
        - text is an entire longtable environment.
    """
    header = find_not_in_any_env_tolerance(text, '\\endhead', depth_overlimit=2)
    footer = find_not_in_any_env_tolerance(text, '\\bottomrule()', depth_overlimit=2)
    during, before, after = three_way_isolation(text, header + len('\\endhead'), footer)
    during = longtable_splitter(during)
    return '\n\n'.join([before, during, after])


def longtable_eliminator(text: str, label: str = '', caption: str = '', float_type: str = 'h',
                         max_page_len: int = MAX_PAGE_LENGTH) -> str:
    """Instance - Here, everything is in a longtable.
    j is the number of times this has run starting from 0.
    text is a longtable instance.
    """
    caption_on_top_of_table = False

    band = 'GfªsBDÜG'

    tab_start = '\\endhead'
    tab_end = '\\bottomrule()'
    tab_s_index = find_not_in_any_env_tolerance(text, tab_start, 0, 2, 1) + len(tab_start)
    tab_e_index = find_not_in_any_env_tolerance(text, tab_end, 0, 2, 1)

    headers_so_far = []
    left_border = '\\begin{minipage}[b]{\\linewidth}\\raggedright\n'
    # right_border = '\\end{minipage}'  # leading \n only
    i = 1
    # highest_index = 0
    env_dict = {'longtable': 2}

    while True:
        left_index = find_not_in_environment_tolerance(text, left_border, env_dict, 0, i) + len(left_border)
        right_index = find_env_end(text, left_index - len(left_border), 'minipage')
        if right_index == -1:
            # we need to change how base cases are detected.
            break
        # highest_index = right_index
        cur_header = text[left_index:right_index].strip()
        headers_so_far.append(cur_header)
        i += 1

    if tab_s_index != tab_e_index:
        tab_data = text[tab_s_index:tab_e_index].strip()
        # tab_data = table_minipage_cleaner(tab_data)
    else:
        tab_data = ''

    header_count = len(headers_so_far)
    em_length = max_page_len // header_count
    # a table can have up to 3 headers until we start splitting up the tables.

    headers_so_far = [process_equations_in_table_header(x, em_length) for x in headers_so_far]

    first_row = '& '.join(headers_so_far)
    if '\\begin{minipage}' in first_row:
        pass  # raise MinipageInLongtableError

    max_header_count = 1
    seperator = 'c'

    if header_count > max_header_count:
        seperator = 'm{' + str(em_length) + 'em}'
    vertical_line = '|'
    table_width = ((vertical_line + seperator) * header_count) + vertical_line
    if tab_data != '':
        fbd_env = ENV_FORBIDDEN
        tab_data = tab_data.replace('\\&', band)
        split_data = str_split_not_in_env(tab_data, R'\\', fbd_env)
        columns = []  # [[a, b, c, d], [e, f, g, h]]
        for roow in split_data:
            cols = str_split_not_in_env(roow, '&', fbd_env)
            # things that are done for all columns
            cols = [process_equations_in_tables(minipage_remover(x.strip()), em_length) for x in cols]
            # cols = [force_not_inline(x) for x in cols]
            columns.append(cols)
        # what we do here to columns is the reconstruction of the table
        rows_stage_2 = [' & '.join(x) for x in columns]
        tab_data = ' \\\\ \\hline\n'.join(rows_stage_2)
        tab_data = '\n\\hline\n' + first_row + '\\\\ \\hline\n' + tab_data + '\n\\\\\\hline\n'
    else:
        tab_data = '\n\\hline\n' + first_row + '\n\\hline'
    if caption != '':
        caption_info = '\\caption{' + caption + '}\n'
    else:
        caption_info = ''
    if caption_on_top_of_table:
        table_start = '\\begin{table}[' + float_type + ']\n\\centering\n' + caption_info + '\n' + label + \
                      '\n\\begin{tabular}{' + table_width \
                      + '}\n'
        table_end = '\\end{tabular}\n' + '\n' + '\\end{table}\n'
    else:
        table_start = '\\begin{table}[' + float_type + ']\n\\centering\n' + '\n' + label + \
                      '\n\\begin{tabular}{' + table_width \
                      + '}\n'
        table_end = '\\end{tabular}\n' + caption_info + '\n' + '\\end{table}\n'
    if '\\begin{minipage}' in tab_data:
        pass  # raise MinipageInLongtableError
    new_table = table_start + tab_data + table_end
    # new_table = new_table.replace(R'\[', R'\(')  # all math in tables are inline math
    # new_table = new_table.replace(R'\]', R'\)')
    return new_table


def table_minipage_cleaner(text: str) -> str:
    """Clear all minipages from a table.
    """
    list_table = table_to_lists(text)
    remove_minipages_from_tables(list_table)
    return lists_to_table(list_table, True)


def table_to_lists(text: str) -> list[list[str]]:
    """Return a tabular list of the LaTeX table data passed into
    text.

    Preconditions:
        - text is a LaTeX table generated by pandoc
        - text is not an empty table, meaning text != ''
    """
    text = text.strip()
    forbidden_envs = ['table', 'tabular', 'longtable', 'minipage', 'texttt', 'enumerate', 'itemize',
                      'align*', 'gather', 'matrix', 'bmatrix', 'pmatrix', 'vmatrix', 'Bmatrix',
                      'Vmatrix']
    and_symbol = '&'
    line_break = R'\\'
    rows = str_split_not_in_env(text, line_break, forbidden_envs)
    if rows[-1] == '':
        rows.pop()  # remove the last row, if applicable. Often caused by \\ ending
    table = []
    for row in rows:
        horizontal_cells = str_split_not_in_env(row, and_symbol, forbidden_envs)
        table.append(horizontal_cells)
    return table


def remove_minipages_from_tables(table_data: list[list[str]]) -> None:
    """Mutate table_data by removing all minipages from it.
    """
    for row in table_data:
        for i, _ in enumerate(row):
            row[i] = minipage_remover(row[i].strip())


def lists_to_table(table_data: list[list[str]], ending_double_backslash: bool = True) -> str:
    """Inverse of table_to_lists.
    No mutations are to be done.
    """
    new_tab_data = []
    for i, row in enumerate(table_data):
        row_data = []
        for j, cell in enumerate(row):
            if j < len(row) - 1:  # if j is not the last one
                temp = cell.strip() + ' & '
            else:  # if j is the last one
                temp = cell.strip() + R' \\'
            row_data.append(temp)
        new_tab_data.append(row_data)
    # choose whether to remove the ending double backslash
    if not ending_double_backslash:
        new_tab_data[-1][-1] = new_tab_data[-1][-1][:-2]
    # combine the data. Each row is split with a newline
    row_strings = [''.join(x) for x in new_tab_data]
    return '\n'.join(row_strings)


def detect_end_of_bracket_env(text: str, env_start: int) -> int:
    """Whatever it returns is the position AT the environment.
    Preconditions:
        - no weird brackets in texttt regions.
    """
    # print('new bracket region')
    brackets_to_ignore = 1
    while True:
        ind = find_nth(text, '}', brackets_to_ignore, env_start)
        # print(ind)
        if text[ind - 1] == '\\':  # last
            brackets_to_ignore += 1
            # char can't be \\ and \} has to be out
            continue
        # elif bracket_layers(text, ind, starting_index=env_start) != -1:
        #     # cur_text = text[ind - 1]
        #     brackets_to_ignore += 1
        #     continue
        else:
            break
    return ind


def fix_all_textt(text: str) -> str:
    """This method aims to do all the following:
        - if two texttt commands are shown in a row, combine them.
    """
    # combine all texttt commands.
    texttt_command = '\\texttt{'
    len_texttt = len(texttt_command)
    skip = 1
    while True:
        texttt_index = find_nth(text, texttt_command, skip)
        if texttt_index == -1:
            break
        texttt_end = local_env_end(text, texttt_index)  # the index where texttt ends
        if text[texttt_end + 1:texttt_end + 1 + len_texttt] == texttt_command:
            text = text[:texttt_end] + text[texttt_end + 1 + len_texttt:]  # the index after the } in texttt
        else:
            skip += 1
    return text


def fix_all_textt_old(text: str) -> str:
    """Do it
    """
    text = text.replace('{[}', '[')
    text = text.replace('{]}', ']')
    dealt_with = 1
    while True:
        t_index = find_nth(text, R'\texttt{', dealt_with)
        if t_index == -1:
            break
        t_index += len(R'\texttt{')
        end = detect_end_of_bracket_env(text, t_index)
        texttt_bounds = text[t_index:end]
        tb = fix_texttt(texttt_bounds)
        text = text[:t_index] + tb + text[end:]

        dealt_with += 1
    text = combine_all_textt(text)
    return text


def combine_all_textt(text: str) -> str:
    """
    Do it
    Precondition: The document does not end with a texttt.
    This is supposed to run after everything of that is run.
    """
    dealt_with = 1
    min_index = 0
    while True:
        t_index = find_nth(text, R'\texttt{', dealt_with, min_index)
        if t_index == -1:
            break
        end = detect_end_of_bracket_env(text, t_index)
        end += 1
        new_index = find_nth(text, R'\texttt{', 1, end)
        if new_index == end:
            text = text[:end - 1] + text[end + len(R'\texttt{'):]
        else:
            dealt_with += 1
    return text


def fix_texttt(text: str) -> str:
    """Everything has to be in a texttt env

    """
    # slashed_indices = []
    # prev_char = ''
    text = text.replace('–', '-')
    text = text.replace(R'\_', '🬀')
    text = text.replace(R'\&', '🬐')
    text = text.replace(R'\$', '🬠')
    text = text.replace(R'\{', '🬰')
    text = text.replace(R'\}', '🭀')
    text = text.replace(R'{]}', '}')
    text = text.replace('r{[}', '[')
    text = text.replace('\\', '')
    text = text.replace('🬀', R'\_')
    text = text.replace('🬐', R'\&')
    text = text.replace('🬠', R'\$')
    text = text.replace('🬰', R'\{')
    text = text.replace('🭀', R'\}')
    # w_quote_remove = lambda s: s.replace('‘', "'").replace('’', "'")
    # text = w_quote_remove(text)
    text = text.replace('‘', "'").replace('’', "'").replace('“', '"').replace('”', '"')

    # for i, char in enumerate(text):
    #     if prev_char in ALPHABET_ALL and char == '\\':
    #        slashed_indices.append(i)
    #    prev_char = char
    # for index in slashed_indices:
    #     str_text = [x for x in text]
    #     str_text[index] = ''  # different
    #    text = ''.join(str_text)
    return text


def three_way_isolation(text: str, left_index: int, right_index: int) -> tuple[str, str, str]:
    """Three way isolation
    0: inside, 1: before, 2: after
    """
    return text[left_index:right_index], text[:left_index], text[right_index:]


def eliminate_all_longtables(text: str, disallow_figures: bool = True,
                             replace_longtable: bool = True, split_longtables: bool = False,
                             float_type: str = 'h', max_page_len: int = 35) -> str:
    """Eliminate all longtables.
    Upper function for the other

    If disallow_figures is true, figuring tables will not count anything.
    """
    # i = 1
    lt_start = '\\begin{longtable}'
    lt_end = '\\end{longtable}'
    table_text_cap = 'Table'
    tables_so_far = []
    skip = 1
    # j = 1
    while True:
        # find_not_in_environment(text, lt_start, )
        lt_start_index = find_nth(text, lt_start, skip)  # backslash of begin
        lt_end_index = find_env_end(text, lt_start_index, 'longtable') + len(lt_end) + 2
        # lt_end_index = find_nth(text, lt_end, skip) + len(lt_end) + 2
        if lt_start_index == -1 or lt_end_index == -1:
            break
        during, before, after = three_way_isolation(text, lt_start_index, lt_end_index)
        if not disallow_figures and after[:len(table_text_cap)] == table_text_cap:

            end_figure_index = find_nth(after, '\n\n', 1)

            temp_figure_text = after[:end_figure_index]
            temp_figure_text_2 = temp_figure_text[len(table_text_cap) + 1:]
            end_of_numbering_1 = find_nth(temp_figure_text_2, ':', 1)
            end_of_numbering_2 = find_nth(temp_figure_text_2, '\n', 1)
            # we can assert that end of both numbers aren't the same
            if end_of_numbering_1 == end_of_numbering_2 == -1:
                end_of_numbering = len(temp_figure_text_2)
            else:
                if end_of_numbering_1 < 0:
                    end_of_numbering_1 = end_of_numbering_2
                if end_of_numbering_2 < 0:
                    end_of_numbering_2 = end_of_numbering_1
                end_of_numbering = min(end_of_numbering_2, end_of_numbering_1)
            figure_num = temp_figure_text_2[:end_of_numbering]  # this is actually a string
            figure_caption = temp_figure_text_2[end_of_numbering + 2:end_figure_index]
            after = after[end_figure_index:]
            if figure_num == '' or not check_valid_label(figure_num):  # if the label is invalid, don't add it.
                fig_label = ''
            else:
                fig_label = '\\label{table:p' + figure_num + '}\n'
                tables_so_far.append(figure_num)
            if split_longtables:
                during = longtable_split_detector(during)
            if replace_longtable:
                new_table_info = longtable_eliminator(during, fig_label, figure_caption, float_type, max_page_len)
            else:
                during = add_label_to_longtable(during, figure_caption, fig_label)
                new_table_info = during
                skip += 1
        else:
            if split_longtables:
                during = longtable_split_detector(during)
            if replace_longtable:
                new_table_info = longtable_eliminator(during, '', '', float_type, max_page_len=max_page_len)
            else:
                new_table_info = during
                skip += 1
        text = before + new_table_info + after
    new_figures_so_far = ['\\ref{table:p' + x + '}' for x in tables_so_far]
    old_figures_so_far = ['Table ' + y for y in tables_so_far]
    old_figures_so_far_1 = ['table ' + z for z in tables_so_far]
    for i in range(0, len(old_figures_so_far)):
        text = text.replace(old_figures_so_far[i], 'Table ' + new_figures_so_far[i])
    for i in range(0, len(old_figures_so_far_1)):
        text = text.replace(old_figures_so_far_1[i], 'table ' + new_figures_so_far[i])
        # j += 1
    return text


def replace_not_in_environment(text: str, depth: int, env: str, sub: str, sub2: str) -> str:
    """Replace environment depth
    """
    skip_mode = False
    if sub2 in sub or sub in sub2:
        skip_mode = True
    skip = 1
    while True:
        ind = find_not_in_environment_tolerance(text, sub, {env: depth}, 0, skip)
        if ind == -1:
            break
        text = text[:ind] + sub2 + text[ind + len(sub):]
        if skip_mode:
            skip += 1
    return text


def bulk_labeling(text: str, label_tags: list[str], type_labeled: str,
                  ref_cmd: str = 'ref', ref_kw: Optional[str] = None) -> str:
    """Used for all your labelling needs.
        - label_tags: [4A, 1, 2B, 3C]
        - type_labeled: table -> Table, table - the first letter upper first lower
        - ref_cmd: ref - the ref command used in text
        - ref_kw: table -> \\labs{table:___} - inserted at the start of the ref

    Preconditions:
        - type_labeled != ''
    """
    type_upper = type_labeled[0].upper() + type_labeled[1:] + ' '
    type_lower = type_labeled[0].lower() + type_labeled[1:] + ' '
    if ref_kw is None:
        ref_kw = type_labeled.lower().replace(' ', '')
    ref_cmd = '\\' + ref_cmd + '{' + ref_kw + ':'
    new_figures_so_far = [ref_cmd + x + '}' for x in label_tags]
    old_figures_so_far = [type_upper + y for y in label_tags]
    old_figures_so_far_1 = [type_lower + z for z in label_tags]
    for i in range(0, len(old_figures_so_far)):
        text = text.replace(old_figures_so_far[i], type_upper + new_figures_so_far[i])
    for i in range(0, len(old_figures_so_far_1)):
        text = text.replace(old_figures_so_far_1[i], type_lower + new_figures_so_far[i])
        # j += 1
    return text


def add_label_to_longtable(text: str, caption: str, label: str) -> str:
    """Add caption and label to the longtable.

    caption is string; label has the latex command

    Preconditions:
        - text contains a longtable that is produced by pandoc
        - text.startswith('\\begin{longtable}')
    """
    assert text.startswith('\\begin{longtable}')
    caption_str = '\\caption{' + caption + '}' + label + '\\\\'
    return insert_before(text, '\\toprule()', caption_str)


def insert_before(text: str, key: str, sub: str) -> str:
    """Insert sub before key in text. We're looking for the first occurrence.
    Return text if key not in text.
    """
    key_index = text.find(key)
    if key_index == -1:
        return text
    else:
        return text[:key_index] + sub + text[key_index:]


def qed(text: str, special: bool = False) -> str:
    """Allow QED support.
    Nesting QED statements are not allowed.
    """
    sp = '{}{}' if special else ''
    proof_str = '\n\n\\emph{Proof.}'
    proof_start = '\n\n\\ѮѱѮѱѮ{proof}' + sp
    proof_start_serious = '\n\n\\begin{proof}' + sp
    assert len(proof_start) == len(proof_start_serious)
    # qed_length_difference = len(proof_start) - len(proof_str)
    # skip = 1
    cur_index = 0
    while True:
        qed_start_index = find_not_in_environment(text, proof_str, 'longtable', cur_index)
        if qed_start_index == -1:
            break
        text = text[:qed_start_index] + proof_start + text[qed_start_index + len(proof_str):]
        text, cur_index = blacksquare_detector_single(text, qed_start_index)  # qed_start_index is \n\n\\...
        text = text.replace(proof_start, proof_start_serious)
    # text = text.replace('\n\n\\emph{Proof.}', '\n\n\\begin{proof}' + sp)
    # text = text.replace('\\[\\blacksquare\\]', '\\end{proof}')
    # text = text.replace('\\blacksquare\\]', '\\] \\end{proof}')
    # text = text.replace('\\(\\blacksquare\\)', '\\end{proof}')
    # text = text.replace('\\blacksquare\\)', '\\) \\end{proof}')
    # text = text.replace(R'~◻', '\\end{proof}')
    # text = text.replace(R'□', '\\end{proof}')
    # text = text.replace(R'◻', '\\end{proof}')
    # text = text.replace(R'∎', '\\end{proof}')
    # text = '\\renewcommand\\qedsymbol{$\\blacksquare$}\n' + text
    # text = blacksquare_detector(text)
    return text


def one_instance(old_tex: str, tex_file: str, todo_str: str) -> tuple[str, str]:
    """Just one run
    """
    reduced_old_tex, extract = gather_section(old_tex)
    new_text_file = insert_at_todo(extract, tex_file, todo_str)
    return reduced_old_tex, new_text_file


def file_name_only_forward(path: str) -> str:
    """File path only! / not \\
    """
    l_index = path.rfind('/')
    return path[l_index + 1:]


def truncate_path(text: str, disallow_pdf: bool = False) -> tuple[str, bool]:
    """Truncate path!

    """
    icg = '\\includegraphics{'
    i = 1
    while True:
        location = find_nth(text, icg, i)
        if location == -1:
            break
        ending_index = text.find('}', location + len(icg))
        include_string = text[location + len(icg):ending_index]
        include_string = 'media/' + file_name_only_forward(include_string)
        text = text[:location] + icg + include_string + text[ending_index:]
        i += 1
    bool_state = i >= 2 if disallow_pdf else False
    return text, bool_state


def remove_images(text: str) -> str:
    """Remove all images.

    Preconditions:
        - include graphics is all on one line
        - verbatims are concealed
    """
    # figures_so_far = []
    all_lines = text.split('\n')
    all_lines_2 = [x for x in all_lines if not x.strip().startswith('\\includegraphics')]
    return '\n'.join(all_lines_2)


def find_stripped(text: str, sub: str) -> int:
    """Behaves very similar to str.find(), but strips the string first.
    Start and end are not supported.
    Parameters
    ----------
    text
        the text the search will be occurring in.
    sub
        the item to look for.

    Returns
    -------
        the index of the first occurrence of item
    """
    stripped = text.lstrip()
    len_diff = len(text) - len(stripped)
    return text.find(sub, len_diff)


def detect_include_graphics(text: str, disallow_figures: bool = False, float_type: str = 'H') -> str:
    """Center all images.
    """
    # if True:  # WHEN YOU CAN'T COMMENT OUT LINES
    figures_so_far = []
    i = 1

    figure_text_cap = '\n\nFigure'
    while True:
        bl = '\n\\begin{figure}[' + float_type + ']\n\\centering\n'
        el = '\\end{figure}\n'
        include_index = find_nth(text, '\\includegraphics', i)
        in_table = check_in_environment(text, 'longtable', include_index) or \
            check_in_environment(text, 'tabular', include_index)
        if include_index == -1:
            break
        before = text[:include_index]
        temp_after = text[include_index:]
        try:
            temp_after_index = local_env_end(temp_after, 0)  # temp_after.index('\n')
        except ValueError:
            break

        during = temp_after[:temp_after_index + 1]
        # paste_after = temp_after[temp_after_index + 2:]
        after = temp_after[temp_after_index + 1:]  # starts with \n
        if not disallow_figures and after[:len(figure_text_cap)] == figure_text_cap and not in_table:
            # end_figure_index = find_stripped(after, '\n\n')
            # assert after.startswith('\n\n')
            end_figure_index = find_nth(after, '\n\n', 1, starter=2)  # start at that
            # I need a find stripped
            temp_figure_text = after[:end_figure_index]
            temp_figure_text_2 = temp_figure_text[len(figure_text_cap) + 1:]
            end_of_numbering_1 = find_nth(temp_figure_text_2, ':', 1)
            end_of_numbering_2 = find_nth(temp_figure_text_2, '\n', 1)
            # we can assert that end of both numbers aren't the same
            if end_of_numbering_1 < 0:
                end_of_numbering_1 = end_of_numbering_2
            if end_of_numbering_2 < 0:
                end_of_numbering_2 = end_of_numbering_1
            end_of_numbering = min(end_of_numbering_2, end_of_numbering_1)
            figure_num = temp_figure_text_2[:end_of_numbering]
            valid_figure = check_valid_label(figure_num)
            figure_caption = temp_figure_text_2[end_of_numbering + 2:end_figure_index]
            after = after[end_figure_index:]
            fig_label = '\\label{fig:p' + figure_num + '}\n' if valid_figure else ''
            el = '\n\\caption{' + figure_caption + '}\n' + fig_label + el
            if valid_figure:
                figures_so_far.append(figure_num)
        else:
            bl = '\n\\begin{figure}[' + float_type + ']\n\\centering\n'
            el = '\n\\end{figure}'

        text = before + bl + during + el + '\n' + after
        i += 1
    new_figures_so_far = ['\\ref{fig:p' + x + '}' for x in figures_so_far]
    old_figures_so_far = ['Figure ' + y for y in figures_so_far]
    old_figures_so_far_1 = ['figure ' + z for z in figures_so_far]
    for i in range(0, len(old_figures_so_far)):
        text = text.replace(old_figures_so_far[i], 'Figure ' + new_figures_so_far[i])
    for i in range(0, len(old_figures_so_far_1)):
        text = text.replace(old_figures_so_far_1[i], 'figure ' + new_figures_so_far[i])

    return text


def insert_at_todo(extract: str, tex_file: str, todo_str: str) -> str:
    """Insert extract at the first "to do:" in the tex file.
    tex_file must not include the preamble.

    Preconditions: sections don't have newline characters in them.
    """
    first_todo_index = find_nth(tex_file, todo_str, 1)
    if first_todo_index == -1:
        print('Ran out of TODOs in the appending TeX file')
        assert False
    # and then split the thing:
    left_tex = tex_file[:first_todo_index]
    right_text = tex_file[first_todo_index:]
    first_newline_afterwards = right_text.index('\n')
    if first_newline_afterwards == -1:
        right_text = ''
    # elif first_newline_afterwards - first_todo_index > 7:
    #     while True:
    #         if right_text[first_newline_afterwards - 1] == '}':
    #             break
    #         if right_text[first_newline_afterwards - 1] != '}':
    #             first_newline_afterwards = right_text.index('\n', first_newline_afterwards + 1)
    #         if first_newline_afterwards == -1:
    #             right_text = ''
    #             break
    #             # loop again to check

    right_text = right_text[first_newline_afterwards:]
    final_text = left_tex + ' ' + extract + right_text
    return final_text


def gather_section(latex_str: str) -> tuple[str, str]:
    """First index of tuple is the text with the old subsection text removed.
    Second index is the extracted text.
    """
    section_alias = '\\section'
    start_section = find_nth(latex_str, section_alias, 1)
    end_section = find_nth(latex_str, section_alias, 2)

    # if start section isn't -1
    if start_section != -1:
        sliced_section = latex_str[start_section:end_section]
        n = 1
        while True:
            newline_index = find_nth(sliced_section, '}', n)
            if newline_index == -1:
                raise ValueError('Did you put latex code in verbatim environments?')
            if sliced_section[newline_index - 1] == '\\':
                n += 1
                continue
            else:
                break
                # sliced_section.index('\n')
        no_section_text = sliced_section[newline_index + 1:]

        popped_section = latex_str[:start_section] + '\n' + latex_str[end_section:]
        return popped_section, no_section_text
    else:
        print('Ran out of sections in converted word document')
        assert False


def find_nth(haystack: str, needle: str, n: int, starter: Optional[int] = None, end: Optional[int] = None) -> int:
    """Needle in a haystack but awesome
    Return -1 on failure
    n = 1 is the lowest value of n; any value below 1 is treated as 1
    starter means from what index?
    """
    if starter is None:
        start = haystack.find(needle)
    else:
        start = haystack.find(needle, starter)
    if end is None:
        end = len(haystack)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start + len(needle), end)
        n -= 1
    return start


def rfind_nth(haystack: str, needle: str, n: int, starter: int = 0,
              ender: Optional[int] = None) -> int:
    """Same as find_nth, but looking at the opposite direction.
    starter and ender are to be interpreted as slice notation.

    Return -1 on failure.

    >>> test_text_here = '0123456789012345678901234567890'
    >>> rfind_nth(test_text_here, '6', 2, 9, 20)
    -1
    """
    if ender is None:
        ender = len(haystack)
    end = haystack.rfind(needle, starter, ender)
    while end >= 0 and n > 1:
        end = haystack.rfind(needle, starter, end)
        n -= 1
    return end


def do_citations(text: str, bib_contents: str, mode: str = 'apa', brackets: bool = False,
                 cite_properities: Optional[dict[str, Any]] = None) -> str:
    """Return text with converted citations.
    """
    if cite_properities is None:
        cite_properities = {}
    authors = extract_authors_from_bib(bib_contents)
    text = citation_handler(text, authors, brackets, cite_properities)
    text = bulk_citation_page_handler(text, mode, False, authors, brackets, cite_properities)
    text = multi_cite_handler_bulk(text, authors, cite_properities)
    return text


def citation_handler(text: str, citation_list: list[str], brackets: bool = False,
                     cite_properities: Optional[dict[str, Any]] = None) -> str:
    """Handle all non-page citations.
    """
    # citation_list = bib_path
    if cite_properities is None:
        cite_properities = {}
    for src in citation_list:
        bracket_src = '(' + src + ')'
        cite_src = '\\' + cite_properities['citation_kw'] + '{' + src + '}'
        if brackets:
            cite_src = ' (' + cite_src + ')'
        text = text.replace(bracket_src, cite_src)
    return text


def bulk_citation_page_handler(text: str, mode: str,
                               p: bool, citation_list: list[str], brackets: bool = False,
                               cite_properities: Optional[dict[str, Any]] = None) -> str:
    """Page numbers
    mode: apa1, apa2, or mla (default mla)
    if p is true latex page numbers will start with p. otherwise nothing
    """
    # citation_list = extract_authors_from_bib(bib_path)
    if cite_properities is None:
        cite_properities = {}
    for src in citation_list:
        text = citation_page_handler(text, src, mode, p, brackets, cite_properities)
    return text


# def create_citations_list(directory: str) -> list[str]:
#     """Create a citations list.
#     This function shouldn't run at all.
#     """
#     with open(directory) as f:
#         citations = f.read()
#     citation_list = citations.split('\n')
#     return citation_list


def citation_page_handler(text: str, src: str, mode: str = 'apa2', p: bool = False, brackets: bool = False,
                          cite_properities: Optional[dict[str, Any]] = None) -> str:
    """Handle all page citations.
    The text should never make a fake-out citation ( please)

    >>> original_text = 'the reason why \\cite[32]{John} you are (John, p. 39) not.'
    >>> source = 'John'
    >>> expect = 'the reason why \\cite[32]{John} you are\\cite[39]{John} not.'
    >>> citation_page_handler(original_text, source, 'apa2', False) == expect
    True
    >>> original_text = 'the reason why \\cite[32]{John} you are (John 39) not.'
    >>> citation_page_handler(original_text, source, 'mla', False) == expect
    True
    """
    if cite_properities is None:
        cite_properities = {}
    mode = mode.lower()
    if mode == 'apa1':
        str_text = '(' + src + ','
    elif mode == 'apa2':
        str_text = '(' + src + ', p. '
    else:  # MLA
        str_text = '(' + src + ' '
    while True:
        starter = text.find(str_text)
        # temp_text = text[starter:]
        if starter == -1:
            break
        start_offset = len(str_text)
        end = starter + start_offset  # the index after 'p. '
        closing_bracket = text.find(')', end)
        if closing_bracket == -1:
            break
        page_number = text[end:closing_bracket]
        citation_bound_end = closing_bracket + 1
        if p:
            page_number = 'p. ' + page_number
        cite_src = '\\' + cite_properities['citation_kw'] + '[' + page_number + ']{' + src + '}'
        if brackets:
            cite_src = ' (' + cite_src + ')'
        text = text[:starter - 1] + cite_src + text[citation_bound_end:]
    return text


def multi_cite_handler_bulk(text: str, srcs: list[str], cite_properities: Optional[dict[str, Any]] = None) -> str:
    """Handle all the multi-inline citations in bulk.
    Must be called after all the other citation modules.
    """
    if cite_properities is None:
        cite_properities = {}
    for src in srcs:
        text = multi_cite_handler(text, src, srcs, cite_properities)
    return text


MCRAW = r"""
This is (a1, a2, a3, a4). Also, (a1, a2, a3, a4).
"""
T_ALIST = ['a1', 'a2', 'a3', 'a4']


def multi_cite_handler(text: str, cur_src: str, srcs: list[str],
                       cite_properities: Optional[dict[str, Any]] = None) -> str:
    """Handle multiple authors cited in the same inline
    citation.
    If there is anything wrong with the citation syntax, stop the process.
    Author names may not contain parentheses for any reason.

    This will not result in any conflicts because latex's syntax
    is way different.

    Preconditions:
        - All other citation handlers have run
        - Raw text is in the format (Author1, Author2, Author3) or related
    """
    if cite_properities is None:
        cite_properities = {}
    look_for = f'({cur_src}, '
    n = 1
    while True:  # per initial occurrence
        author_list = [cur_src]
        cite_ind = find_nth(text, look_for, n)  # index of the para in in-text cite
        if cite_ind == -1:
            break
        post_cite_ind = cite_ind + len(look_for)  # the index after the whitespace
        next_parentheses = text.find(')', cite_ind)
        if next_parentheses == -1:
            break
        for author in srcs:
            new_author_str = f'{author}, '
            cur_author_ind = text.find(new_author_str, post_cite_ind, next_parentheses)
            if cur_author_ind != -1:
                author_list.append(author)
            else:
                para_author_str = f'{author})'
                ending_author_ind = text.find(para_author_str, post_cite_ind, next_parentheses + 1)
                if ending_author_ind != -1:
                    author_list.append(author)
        # updated text
        text = text[:cite_ind] + '\\' + cite_properities['citation_kw'] + \
            '{' + ','.join(author_list) + '}' + text[next_parentheses + 1:]
    return text


class LatexEnvironment:
    """A class representing an environment.
    Instance Attributes:
        - env_name: name of the LaTeX environment.
        - start: start text of the LaTeX environment.
        - end: end text of the LaTeX environment.
        - encapsulation: Formats required
    """
    env_name: str  # env name, doesn't matter if caps or not
    start: str
    end: str
    encapsulation: str
    initial_newline: bool
    priority: int
    has_extra_args: bool
    extra_args_type: str
    env_prefix: str
    env_suffix: str
    env_middlefix: str

    def __init__(self, env_name: str, start: str, end: str,
                 encapsulation: Optional[str] = None, initial_newline: bool = False, priority: int = 0,
                 has_extra_args: bool = False, extra_args_type: str = 'bracket',
                 env_prefix: str = '', env_suffix: str = '', start_alt: str = '',
                 env_middlefix: str = '') -> None:
        """start and end here are not formatted - formats are done in encapsulation. This is in
        terms of the inputs. In the class itself, start and end are what you would see in
        LaTeX.
        """
        self.initial_newline = initial_newline
        if encapsulation is None or encapsulation == '':
            self.start = start
            self.end = end
        else:
            self.start = '\\' + encapsulation + '{' + start + '}'
            self.end = '\\' + encapsulation + '{' + end + '}'
        self.env_name = env_name
        if start_alt == '':
            self.start_alt = self.env_name
        else:
            self.start_alt = start_alt
        self.priority = priority
        self.has_extra_args = has_extra_args
        self.extra_args_type = extra_args_type
        self.env_prefix = env_prefix
        self.env_suffix = env_suffix
        self.env_middlefix = env_middlefix


@dataclass
class _RawLatexEnvironment:
    """Before
    """
    env_name: str  # the literal name of the environment. First letter should be
    # in caps. This is the starter keyword for automatic breaks.
    start: str = 'ȚHE#$$$$$$@%@$#VER!!!ASTA#!!!ȚTT'  # Environment starter keyword. Not supported for automatic breaks.
    end: str = 'TH!!!ERȚ!!WAȚ@#ȚSNE*(VEȚAN*@##END'  # Environment end keyword. Not supported for automatic breaks.
    encapsulation: str = ''  # any modifiers to the environment call.
    initial_newline: bool = False  # if the environment must start on a newline.
    priority: int = 3  # the priority of the env
    has_extra_args: bool = False  # whether you want extra arguments in the envs.
    # for example: \begin{definition}[the definition]. Set to false
    # if you want to have a plain environment.
    extra_args_type: str = 'brace'  # bracket or brace which determines what the extra
    # args should be surrounded by. Must be ON if you want automatic breaks.
    env_prefix: str = ''  # text to append before environment declaration: \begin{env}
    env_suffix: str = ''  # text to append after environment declaration: \begin{env}
    name_alt: str = ''  # Replaces the env name for automatic breaks

    # def create_latex_env(self) -> LatexEnvironment:
    #     pass
    #


def work_with_environments(text, envs: Union[dict, list], disable_legacy: bool = False) -> str:
    """The master function for working with environments.
    """
    if isinstance(envs, dict):
        envs = unpack_environments(envs)
    else:
        envs = unpack_environment_list(envs)
        disable_legacy = True
    return bulk_environment_wrapper(text, envs, disable_legacy)


# def check_environments(json_dir: str) -> list[LatexEnvironment]:
#     """The old version.
#     """
#     with open(json_dir) as json_file:
#         json_data = json.load(json_file)
#     env_dict = json_data["environments"]
#     envs_so_far = []
#
#     for env_name, env_info in env_dict.items():
#         field_names = set(f.name for f in fields(_RawLatexEnvironment))
#         raw_latex_env = _RawLatexEnvironment(**{k: v for k, v in env_info.items() if k in field_names})
#         latex_env = LatexEnvironment(raw_latex_env.env_name, raw_latex_env.start, raw_latex_env.end,
#                                      raw_latex_env.encapsulation, raw_latex_env.initial_newline,
#                                      raw_latex_env.priority, raw_latex_env.has_extra_args,
#                                      raw_latex_env.extra_args_type,
#                                      raw_latex_env.env_prefix, raw_latex_env.env_suffix,
#                                      raw_latex_env.name_alt)
#         # latex_env = LatexEnvironment(env_name, env_info['start'],
#         #                             env_info['end'], env_info['encapsulation'],
#         #                             env_info['initial_newline'], env_info['priority'],
#         #                             env_info['has_extra_args'], env_info['extra_args_type'])
#         envs_so_far.append(latex_env)
#     envs_so_far.sort(key=lambda x: x.priority, reverse=True)
#     return envs_so_far


def unpack_environment_list(envs: list[str]) -> list[LatexEnvironment]:
    """Unpack the environments list in the most lazy way possible.
    Syntax: if theorem is the name of our environment
        - "theorem" for default: extra args is bracket. no start/end
        - "theorem[]" is the same as "theorem"
        - "theorem{}": extra args is brace. start/end
        - "theorem{}{}": extra args is brace; suffix is '{}'
        - "theo!theorem{}{}": the env alias (start_alt) is theo, but the env name is theorem
        - "the!theorem[shut up]{}{shut up}": the env alias is the, env name is theorem

    """
    envs_so_far = []
    for env in envs:
        # I am skeptical and don't want to mutate envs
        # So I will reassign it
        env_name = env
        # this is meant for optional parameters.
        # the last two chars in the env str may state whether
        # it has optional parameters.
        nearest_bracket = find_fallback(env_name, '[]')
        nearest_brace = find_fallback(env_name, '{}')
        extra_args = 'bracket' if nearest_bracket <= nearest_brace else 'brace'
        nearest_delimiter = min(nearest_brace, nearest_bracket)
        true_env_name = env_name[:nearest_delimiter]
        env_suffix = env_name[nearest_delimiter + 2:]
        if true_env_name[-1] == ']':
            nearest_square = true_env_name.find('[')
            env_middlefix = true_env_name[nearest_square:]
            true_env_name = true_env_name[:nearest_square]
            # if extra_args == 'bracket':
            #    raise ValueError('Forced [optional] parameter paired with [insertable] optional parameter')
        else:
            env_middlefix = ''

        splitted_env_name = true_env_name.split('!')
        if len(splitted_env_name) == 2:
            start_alt = splitted_env_name[0].strip()
            env_name_to_use = splitted_env_name[1].strip()
        else:
            if len(splitted_env_name) != 1:
                raise ValueError('Invalid syntax for list environment declaration - more than one ! used')
            start_alt = ''
            env_name_to_use = splitted_env_name[0].strip()
        env_name_to_use = env_name_to_use.lower()
        new_environment = LatexEnvironment(env_name_to_use, 'r»aò»doò un»icoò»e', 'r»aòd»om un»i»òod»e',
                                           env_suffix=env_suffix, extra_args_type=extra_args,
                                           start_alt=start_alt,
                                           has_extra_args=True, env_middlefix=env_middlefix)
        envs_so_far.append(new_environment)
    return envs_so_far


def unpack_environments(envs: dict) -> list[LatexEnvironment]:
    """Unpack the environments dictionary and return a list
    of latex environments.
    """
    # with open(json_dir) as json_file:
    #     json_data = json.load(json_file)
    env_dict = envs  # json_data["environments"]
    envs_so_far = []

    for env_name, env_info in env_dict.items():
        field_names = set(f.name for f in fields(_RawLatexEnvironment))
        raw_latex_env = _RawLatexEnvironment(**{k: v for k, v in env_info.items() if k in field_names})
        latex_env = LatexEnvironment(raw_latex_env.env_name, raw_latex_env.start, raw_latex_env.end,
                                     raw_latex_env.encapsulation, raw_latex_env.initial_newline,
                                     raw_latex_env.priority, raw_latex_env.has_extra_args,
                                     raw_latex_env.extra_args_type,
                                     raw_latex_env.env_prefix, raw_latex_env.env_suffix,
                                     raw_latex_env.name_alt)
        # latex_env = LatexEnvironment(env_name, env_info['start'],
        #                             env_info['end'], env_info['encapsulation'],
        #                             env_info['initial_newline'], env_info['priority'],
        #                             env_info['has_extra_args'], env_info['extra_args_type'])
        envs_so_far.append(latex_env)
    envs_so_far.sort(key=lambda x: x.priority, reverse=True)
    return envs_so_far


def bulk_environment_wrapper(text: str, envs: list[LatexEnvironment], disable_legacy: bool = False) -> str:
    """Return environment_wrapper(text...) run on all environments.
    """

    # env_stack = environment_stack(text, envs)
    # text = env_wrapper_many(text, env_stack)

    # env_basic = [en for en in envs if not en.has_extra_args]
    env_complex = [en for en in envs if en.has_extra_args]

    for env in envs:
        text = longtable_environment(text, env.env_name, env)
    for env in env_complex:
        text = environment_wrapper_2(text, env)
    if not disable_legacy:
        for env in envs:
            text = quote_to_environment(text, env, env.has_extra_args)
        for env in envs:
            text = environment_wrapper(text=text, env=env.env_name, start=env.start,
                                       end=env.end, initial_newline=env.initial_newline,
                                       has_extra_args=env.has_extra_args, extra_args_type=env.extra_args_type,
                                       env_info=env)
    return text


@dataclass
class EnvironmentInstance:
    """This would have been a dict
    Because we only support end breaking characters,
    we only have one end position."""
    tag: str
    start_pos_1: int
    start_pos_2: int
    end_pos: Optional[int] = None


def environment_stack(text: str, envs: list[LatexEnvironment]) -> list[EnvironmentInstance]:
    """Generate and return an environment stack, or a list of environment instances.
    """
    # assume extra args type is turned on by default
    # this is terribly broken
    # env nestings work, but we have to add a ghost environment at the bottom.
    text = text + r"""\emph{Info.} Why do I do this.

    ◺"""
    last_tracking_index = 0
    # former_tracking_index = -1
    finished_env_instances = []
    working_env_instances = []
    while True:
        former_tracking_index = last_tracking_index
        tracking_index_so_far = []
        # current objectives: scanning all the env names, figure out which one starts the earliest.
        for env in envs:
            env_start_text = env.start
            temp_start = find_nth(text, env_start_text, 1, last_tracking_index)
            temp_end = temp_start + len(env.start)  # the index AFTER the end of the starting keyword
            env_tag = env.env_name
            temp_dict = {'start': temp_start, 'start_end': temp_end, 'tag': env_tag}
            tracking_index_so_far.append(temp_dict)
        stopper = find_closest_unicode_char_index(text, last_tracking_index)
        if stopper == -1:
            stopper = math.inf
        tracking_index_so_far.sort(key=lambda x: x['start'] if x['start'] != -1 else math.inf, reverse=False)
        target_env_instance = tracking_index_so_far[0]
        tiev_start = target_env_instance['start']
        if tiev_start < 0:
            tiev_start = math.inf
        last_tracking_index = min(tiev_start + 1, stopper + 1)  # the loc AFTER stopper
        # if last_tracking_index == math.inf:
        #     break
        if stopper < target_env_instance['start']:
            working_env_instances[-1].end_pos = stopper
            finished_env_instances.append(working_env_instances.pop())
        elif (target_env_instance['start'] == -1 or target_env_instance == math.inf) and stopper == math.inf:
            # working_env_instances[-1].end_pos = stopper
            # finished_env_instances.append(working_env_instances.pop())
            break
        elif last_tracking_index < former_tracking_index:
            # working_env_instances[-1].end_pos = stopper
            # finished_env_instances.append(working_env_instances.pop())
            break
        else:
            temp_env_instance = EnvironmentInstance(target_env_instance['tag'],
                                                    target_env_instance['start'],
                                                    target_env_instance['start_end'])
            working_env_instances.append(temp_env_instance)
    if len(working_env_instances) != 0:
        logging.warning('You didn\'t close all environments. That may cause problems.'
                        'I will ignore unclosed environments.')
    return finished_env_instances


def find_closest_unicode_char_index(text: str, min_index: int) -> int:
    unicode = ['◾', '▨', '◺']
    indices_so_far = []
    # return min(find_nth(text, uni, 1, min_index) for uni in unicode)
    for uni in unicode:
        ind = find_nth(text, uni, 1, min_index)
        indices_so_far.append(ind)
    if all(u == -1 for u in indices_so_far):
        return -1
    else:
        return min(v for v in indices_so_far if v != -1)


def env_wrapper_many(text: str, env_instances: list[EnvironmentInstance]) -> str:
    """That but multiple times"""
    for env_instance in env_instances:
        text = environment_wrapper_new(text, env_instance)
    return text


def environment_wrapper_new(text: str, env_instance: EnvironmentInstance) -> str:
    """If text is between start and end, place it in an environment.
    This replaces ALL environments.
    text: our text
    env: environment name defined in latex.
    start: substring that indicates the start of an environment.
    end: substring that indicates the end of it.
    initial_newline: if True, '\n' must precede start.
    """
    # weird_unicode_chars = ['◾', '▨', '◺']
    # if initial_newline and start[0] != '\n':
    #     start = '\n' + start
    start_pos_1 = env_instance.start_pos_1
    start_pos_2 = env_instance.start_pos_2
    # indices_so_far = []
    end_pos_7 = env_instance.end_pos
    end_pos_8 = end_pos_7 + 1  # 1 is the length of emojis
    end_pos_1, end_pos_2 = end_pos_7, end_pos_8
    # can't find any; occurs when environments are exhausted
    if -1 in {start_pos_1, start_pos_2, end_pos_1, end_pos_2}:
        return text
    # misplaced environments
    if start_pos_1 >= end_pos_1:
        return text
    begin_env = '\n\\begin{' + env_instance.tag + '}'
    end_env = '\n\\end{' + env_instance.tag + '}\n'

    # if has_extra_args:  # only generate extra args when permitted AND does not cut off on line 1
    start_pos_3 = find_nth(text, '\n\n', 1, start_pos_2)
    if start_pos_3 != -1 and end_pos_1 > start_pos_3 and end_pos_1 - start_pos_3 <= 100:
        # match extra_args_type:
        #    case 'bracket':
        #        brc = ('[', ']')
        #    case 'brace':
        #        brc = ('{', '}')
        #    case _:
        #        brc = ('[', ']')
        extra_env_args = (text[start_pos_2:start_pos_3].strip()).replace('\n', '')
        if all(k in extra_env_args for k in {'{[}', '{]}'}) or all(k in extra_env_args for k in {'\\{', '\\}'}):
            begin_env = begin_env + extra_env_args.replace(R'\{', '{').replace(R'\}', '}'). \
                replace('{[}', '[').replace('{]}', ']')
            spbr = find_nth(text, '\\}', 1, start_pos_2) + 2
            spbc = find_nth(text, '{]}', 1, start_pos_2) + 3
            spbr, spbc = min(spbr, start_pos_3), min(spbc, start_pos_3)
            decrease_value = max(spbr, spbc) if not all(start_pos_3 == x for x in [spbr, spbc]) else start_pos_2
            start_pos_2 += decrease_value

    # prior_text = text[:start_pos_1]
    # post_text = text[:end_pos_2]
    text = text[:start_pos_1] + begin_env + '\n' + text[start_pos_2:end_pos_1].strip() + end_env + text[end_pos_2:]
    # call the function again
    return text  # recursive


# SAMPLE_LATEX_ENV = unpack_environments('config.json')

SAMPLE_ENV_TEXT = r"""
This is some text.

\textbf{Definition - environments:} This is something
that needs to be said

\[some math region\]

we're out not yet.

\begin{itemize}
    \item not anymore?
    \item I don't think so.

\[some math region\]

Now we're out.

\textbf{Corollary.} This does not work. ◺
"""


def environment_wrapper_2(text: str, env_info: LatexEnvironment) -> str:
    """An updated version of the environment wrapper which uses a newer word syntax.
    Compatible with the old environment wrapper, though this is always run first.
    """
    braces = env_info.extra_args_type != 'bracket'
    if (not braces) and env_info.env_middlefix != '':
        return text

    # mid_fix = env_info.env_middlefix  # if braces else ''
    # assert braces or mid_fix == ''
    dashes = {'- ', '– ', '— ', '--', }
    k_begin = R'\begin{' + env_info.env_name.lower() + '}'
    k_end = R'\end{' + env_info.env_name.lower() + '}'
    keyword = env_info.start_alt[0].upper() + env_info.start_alt[1:]
    wrapper = 'textbf'
    br = '{}' if braces else '[]'
    allowed_terms = [R'\begin{enumerate}', R'\begin{itemize}']

    keyword_wrapper = '\\' + wrapper + '{' + keyword

    # find nth: haystack, needle, n, starter = None
    n = 1  # skip
    while True:
        start = find_nth(text, keyword_wrapper, n)
        if start == -1:  # BASE CASE: we couldn't find an environment starter
            break
        start_after = start + len(keyword_wrapper) + 1  # index of the dash
        if (text[start_after:start_after + 2] not in dashes and text[start_after] != '(') or \
                text[start - 2:start] != '\n\n':
            # THIS WILL RUN INCASE OF FAILURE
            def_after = start + len(keyword_wrapper)
            if text[def_after:def_after + 2] == '.}' and text[start - 2:start] == '\n\n':
                end_declare = def_after + 2  # the index after \textbf{Definition}
                # extra_args_name = ''
                end = end_declare
                # term = extra_args_name
                term = ''
            elif text[def_after:].startswith('} ('):
                # assume that no brackets are nested.
                end_open = text.find(')', def_after + 3)
                extra_args_name = text[def_after + 3:end_open]
                # end_open + 1 is the period at \textbf{Definition} (Salt).
                # However, the period is optional.
                tbf_dot = '\\textbf{.}'
                tbf_dot2 = '\\textbf{. }'

                # End_declare is the index after the period.
                if text[end_open + 1] == '.':
                    end_declare = end_open + 2
                elif text[end_open + 1:].startswith(tbf_dot):
                    end_declare = end_open + 1 + len(tbf_dot)
                elif text[end_open + 1:].startswith(tbf_dot2):
                    end_declare = end_open + 1 + len(tbf_dot2)
                else:
                    end_declare = end_open + 1
                end = end_declare
                term = extra_args_name.strip()
                # A strip would occur anyway.
            else:
                # IF THE FALLBACK FAILS
                n += 1
                continue
                # otherwise
        else:
            end = local_env_end(text, start)  # find_nth(text, '}', 1, start_after)
            # find_endbrace(text, start_after)
            temp_num = 1 if text[start_after] == '(' else 2
            term = text[start_after + temp_num:end]
            if term[-1] == ':':
                term = term[:-1]
            elif term.endswith(').'):
                term = term[:-2]
            term = term.strip()
        next_nl_skip = 1
        while True:  # intent: math regions don't break. Actual: Max of one math region.
            next_newline = find_nth(text, '\n\n', next_nl_skip, end + 1)
            if next_newline == -1:  # base case: there is now next newline. Then give up
                # next_newline = len(text) - 1
                return text
                # break

            elif text[next_newline + 2:next_newline + 4] == R'\[' \
                    or text[next_newline + 2:next_newline + 3] in ALPHABET or any(
                    text[next_newline + 2:].startswith(tx) for tx in allowed_terms):
                next_nl_skip += 1
                continue
            else:
                break

        extra_args = br[0] + term + br[1] if term != '' else ''

        text = text[:start] + k_begin + extra_args + \
            env_info.env_suffix + '\n' + text[end + 1:next_newline].strip() + '\n' + \
            k_end + text[
                                                                                                                                 next_newline:]
    return text


def environment_wrapper(text: str, env: str, start: str, end: str, env_info: LatexEnvironment,
                        initial_newline: bool = False, has_extra_args: bool = False,
                        extra_args_type: str = 'bracket') -> str:
    """If text is between start and end, place it in an environment.
    This replaces ALL environments.
    text: our text
    env: environment name defined in latex.
    start: substring that indicates the start of an environment.
    end: substring that indicates the end of it.
    initial_newline: if True, '\n' must precede start.
    """
    weird_unicode_chars = ['◾', '▨', '◺']
    if initial_newline and start[0] != '\n':
        start = '\n' + start
    start_pos_1 = find_nth(text, start, 1)  # the index of the first char of start.
    start_pos_2 = start_pos_1 + len(start)  # the index of the char after start.
    indices_so_far = []
    for weird_char in weird_unicode_chars:
        end_pos_special = find_nth(text, weird_char, 1, start_pos_2)
        if end_pos_special != -1:
            indices_so_far.append(end_pos_special)
    end_pos_7 = min(indices_so_far) if indices_so_far != [] else math.inf
    end_pos_8 = end_pos_7 + 1  # 1 is the length of emojis
    end_pos_1 = find_nth(text, end, 1, start_pos_2)  # the first index of the ending
    end_pos_2 = end_pos_1 + len(end)  # the character right after the ending
    if end_pos_7 < end_pos_1 or end_pos_1 == -1:
        end_pos_1, end_pos_2 = end_pos_7, end_pos_8
    # can't find any; occurs when environments are exhausted
    if -1 in {start_pos_1, start_pos_2, end_pos_1, end_pos_2}:
        return text
    # misplaced environments
    if start_pos_1 >= end_pos_1:
        return text
    begin_env = '\n\\begin{' + env.lower() + '}'
    end_env = '\n\\end{' + env.lower() + '}\n'

    if has_extra_args:  # only generate extra args when permitted AND does not cut off on line 1
        start_pos_3 = find_nth(text, '\n\n', 1, start_pos_2)
        if start_pos_3 != -1 and end_pos_1 > start_pos_3 and abs(end_pos_1 - start_pos_3) >= 10:
            extra_args_choices = {'bracket': ('[', ']'), 'brace': ('{', '}')}
            brc = extra_args_choices.get(extra_args_type, ('[', ']'))
            extra_text = text[start_pos_2:start_pos_3]
            begin_env = begin_env + env_info.env_prefix + brc[0] + extra_text.strip() + brc[1] + env_info.env_suffix
            start_pos_2 = start_pos_3
        elif len(env_info.env_suffix) > 0:
            extra_args_choices = {'bracket': ('[', ']'), 'brace': ('{', '}')}
            brc = extra_args_choices.get(extra_args_type, ('[', ']'))
            # extra_text = brc[0] + brc[1]
            begin_env = begin_env + env_info.env_prefix + brc[0] + brc[1] + env_info.env_suffix
            # extra_env_args = (text[start_pos_2:start_pos_3].strip()).replace('\n', '')
            # if all(k in extra_env_args for k in {'{[}', '{]}'}) or all(k in extra_env_args for k in {'\\{', '\\}'}):
            # begin_env = begin_env + extra_env_args.replace(R'\{', '{').replace(R'\}', '}'). \
            #     replace('{[}', '[').replace('{]}', ']')
            # spbr = find_nth(text, '\\}', 1, start_pos_2) + 2
            # spbc = find_nth(text, '{]}', 1, start_pos_2) + 3
            # spbr, spbc = min(spbr, start_pos_3), min(spbc, start_pos_3)
            # decrease_value = max(spbr, spbc) if not all(start_pos_3 == x for x in [spbr, spbc]) else start_pos_2
            # start_pos_2 += decrease_value

    # prior_text = text[:start_pos_1]
    # post_text = text[:end_pos_2]
    text = text[:start_pos_1] + begin_env + '\n' + text[start_pos_2:end_pos_1].strip() + end_env + text[end_pos_2:]
    # call the function again
    return environment_wrapper(text, env, start, end, env_info, initial_newline, has_extra_args,
                               extra_args_type)  # recursive


def dy_fixer(text: str) -> str:
    """Fix how pandoc deals with dy and dx.
    """
    low_letters = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
                   'p', 'q', 'R', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'}
    cap_letters = {letter.upper() for letter in low_letters}
    extra_letters = {'θ'}
    # I wonder how theta will work with this?
    all_letters = (low_letters.union(cap_letters)).union(extra_letters)
    for letter_instance in all_letters:
        d_text = '\\text{d' + letter_instance + '}'
        if letter_instance == 'θ':
            letter_instance = '\\theta'
        d_text_fixed = '\\text{d}' + letter_instance
        text = text.replace(d_text, d_text_fixed)
    return text


# αβγδεϵζηθϑικλμνξοπϖρϱσςτυφϕχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ
REPLAC = {'α': R'\alpha', 'β': R'\beta', 'γ': R'\gamma', 'δ': R'\delta',
          'θ': R'\theta', 'π': R'\pi', 'Ω': R'\Omega'}


def text_bound_fixer(text: str, replacement: dict[str, str], n: int = 1) -> str:
    """Detect and fix text environments with
    unicode characters. Also fix text environments that are two characters
    or shorter.
    """
    # logging.warning('text is ' + text)

    # replacement = {'π': R'\pi'}
    unicode_list = list(replacement.keys())
    # n = 1  # ignored count starting from 1
    btext = R'\text{'
    text_index = find_nth(text, btext, n)
    if text_index == -1:
        # logging.warning('could not find another text env')
        return text
    starting_index = text_index + len(btext)
    layers_in = 0
    min_index = starting_index
    while True:
        inner_brace = text.find(R'{', min_index)
        outer_brace = text.find(R'}', min_index)
        if outer_brace == -1:
            # logging.warning('No outer brace')
            return text
        if inner_brace == -1:
            inner_brace = math.inf
        if inner_brace < outer_brace:
            layers_in += 1
            min_index = inner_brace + 1
            continue
        else:
            if layers_in > 0:
                layers_in -= 1
                min_index = outer_brace - 1
            else:  # if layers_in == 0
                break
    inner_text = text[starting_index:outer_brace]
    fix_region = check_inner_text(inner_text) or check_char_bulk(inner_text, unicode_list)
    # print(text)
    if fix_region:

        # logging.warning('fix region detected')
        for u1, u2 in replacement.items():
            inner_text = inner_text.replace(u1, u2 + ' ')
        text = text[:text_index] + inner_text + text[outer_brace + 1:]
        return text_bound_fixer(text, replacement, n)
    else:
        n += 1
        # logging.warning(n)
        return text_bound_fixer(text, replacement, n)


def check_inner_text(inner_text: str) -> bool:
    """Check if the region of an inner text should be processed.
    We already know no weird unicode characters will be within them.

    TRUE if the region should be fixed
    FALSE if the region should NOT be fixed.
    """
    # DON'T fix if the text is over 2 leters long
    if len(inner_text) >= 3:
        return False
    # AUTO FALSE:
    whitelisted_words = {
        'is', 'be', 'do', 'go', 'hi', 'of', 'so', 'or', 'oh'
    }
    # two letter case
    if inner_text in whitelisted_words:
        return False
    # if it is d by itself and only by itself
    elif inner_text == 'd':
        return False
    else:
        return True


def check_char_bulk(text: str, uni: list[str]) -> bool:
    """Return True if at least one str in uni is in text.
    """
    for u in uni:
        if u in text:
            return True
    return False


def bracket_layers(text: str, index: int,
                   opening_brace: str = '{', closing_brace: str = '}', escape_char: bool = True,
                   starting_index: int = 0) -> int:
    """Return the depth of the index in text based on opening_brace and closing_brace
    When escape_char is true, only if opening_brace / closing_brace are both length 1, then it
    will ignore instances where the escape character is used.

    If the index you are looking at is an opening brace or a closing brace,
    it will check the next position (even if it is blank).

        If the above case is true and the next position is also an opening or closing brace,
        it will treat that the opening or closing brace is not a brace.

    The starting index is the minimum index where brackets will be tracked.

    >>> temp_text = '{123\\{56}89}12'
    >>> bracket_layers(temp_text, 6)
    1
    """
    if not (len(opening_brace) == 1 and len(closing_brace) == 1):
        escape_char = False
    layer = 0
    prev_char = ''
    esc = '\\' + opening_brace
    esc2 = '\\' + closing_brace
    if escape_char:
        text = text.replace(esc, '🬍🬘').replace(esc2, '🬮🭕')
        # replaces escape chars with something of same length

    for i, char in enumerate(text):
        if i < starting_index:
            continue
        # if escape_char and prev_char == '\\':
        #     prev_char = ''
        #     continue
        if char == opening_brace:
            layer += 1
        if char == closing_brace:
            layer -= 1
        if i == index:
            # if escape_char:
            # text = text.replace('🬍🬘', esc).replace('🬮🭕', esc2)
            return layer

        prev_char = char
    if index == -1:
        return layer
    else:
        raise IndexError('Your index was out of bounds.')


# NUMBERED_EQUATIONS = True


def split_all_equations(text: str, max_len: int, skip: int = 0,
                        numbered_equations: bool = True, label_equations: bool = False,
                        tag_equations: bool = True) -> tuple[str, list[str]]:
    """Split equation done for all equations.
    Also, label equations if needed.
    Must be done before dollar sign equations, but after alignment regions
    are processed for the first time. If fix alignment regions are off,
    this may not run.

    Initially, skip must always be set to 0.

    Long equations may not be numbered. Shorter equations can. If so,
    nothing that would result in backslashes or braces appearing
    in the comment may be present,
    otherwise the comment will be thrown out.
    """
    equation_labels = []  # this is an equation label. Feel free to
    # screenshot.
    while True:
        equation_is_numbered = False
        starting_index = find_nth(text, R'\[', skip + 1)
        finishing_index = find_nth(text, R'\]', skip + 1)
        if -1 in (starting_index, finishing_index):
            break
        assert starting_index < finishing_index
        eqn_text = text[starting_index + 2:finishing_index]
        eqn_comment = None
        if numbered_equations and valid_matrix(eqn_text):
            eqn_text, eqn_comment = matrix_equation_extractor(eqn_text)
            equation_is_numbered = True
        new_eqn_text = split_equation(eqn_text, max_len)
        if new_eqn_text is None:  # everything is fine - no updates done.
            if equation_is_numbered:
                # wrap the entire equation using the equation environment.
                # equations can be tagged, but labelling isn't supported.
                # I don't even want to support labelling, but I will.
                begin_equation = '\n\\begin{equation}\n'
                end_equation = '\n\\end{equation}\n'

                # begin_equation_st = '\n\\begin{equation}\n'
                # end_equation_st = '\n\\end{equation}\n'

                eqn_label = get_equation_label(eqn_comment)
                if eqn_label is not None:
                    labeling = R' \tag{' + eqn_label + '} ' if tag_equations else ''
                    if label_equations:
                        labeling += ' \\label{eq:' + eqn_label + '}'
                        equation_labels.append(eqn_label)
                    eqn_env_text = begin_equation + eqn_text + labeling + end_equation
                else:  # no time for wrapping
                    logging.warning(f'equation {eqn_text} has an invalid comment; removing comment.'
                                    f' Invalid comments are not plain text or numbers.')
                    eqn_env_text = '\\[' + eqn_text + '  \\]'  # add a backslash before
                    skip += 1
                text = text[:starting_index] + eqn_env_text + text[finishing_index + 2:]
            else:  # skip only if we didn't wrap this around an eqn environment
                skip += 1
        else:  # otherwise, updates are done, and then we continue.
            if equation_is_numbered:
                logging.warning(f'Extra long numbered equation: {eqn_comment}. Comment deleted.')
            text = text[:starting_index] + R'\[' + new_eqn_text + R'\]' + text[finishing_index + 2:]
            skip += 1
    # if equation_labels:  # if equation_labels isn't empty
    #     text = bulk_labeling(text, equation_labels, )
    # we will not be including refs because of how equations are typed out.

    return text, equation_labels


def remove_local_environment(text: str, env: Union[str, list[str]]) -> str:
    """Remove all local environments in env from text.
    """
    if isinstance(env, str):
        env = [env]
    for env_instance in env:
        env_start = '\\' + env_instance + '{'
        while True:
            starting_index = text.find(env_start)
            if starting_index == -1:
                break
            ending_index = local_env_end(text, starting_index)
            # the local environment is always destroyed everytime this is run.
            text = text[:starting_index] + text[starting_index + len(env_start):ending_index] + \
                text[ending_index + 1:]
    return text


def get_equation_label(numbering: str) -> Optional[str]:
    """Return the equation label from the comment.
    In other words:
        - if numbering is wrapped by parentheses, remove the brackets.
        - otherwise, return numbering without making changes.
        - if the label results in errors, then return None.
    """
    if len(numbering) == 0:
        return None
    if numbering[0] == '(' and numbering[-1] == ')':
        numbering = numbering[1:len(numbering) - 1]
    elif numbering.startswith(R'\left(') and numbering.endswith(R'\right)'):
        numbering = numbering[len(R'\left('):len(numbering) - len(R'\right)')]
    # afterwards, check if the label is valid
    # remove all text from local environments
    numbering = remove_local_environment(numbering, ['text', 'mathbf'])
    numbering = formatted_text_encryptor(numbering, ['textbf', 'emph'])
    if check_valid_label(numbering):
        numbering = formatted_text_decryptor(numbering, ['textbf', 'emph'])
        return numbering.strip()
    else:
        return None


def check_valid_label(label: str) -> bool:
    """Return True if the label is valid.
    A label is valid when the following conditions
    of this function is met.

    - no backslashes
    - no braces
    """
    # first condition: no backslashes at all
    if '\\' in label:
        return False
    elif '{' in label:
        return False
    elif '}' in label:
        return False
    else:
        return True


def matrix_equation_extractor(text: str) -> tuple[str, str]:
    """Extract the one value in the matrix.

    Preconditions:
        - valid_matrix(text)
    """
    # logging.warning(text)
    text = text.strip()  # strip the text first
    bm = R'\begin{matrix}'
    em = R'\end{matrix}'
    starting_matrix_location = text.find(bm)
    # conditions: above is 0
    if starting_matrix_location != 0:
        assert False
    ending_matrix_location = text.rfind(em)
    required_ending_location = len(text) - len(em)
    # conditions: ending matrix ends where it is supposed to end
    if ending_matrix_location != required_ending_location:
        assert False
    # Matrix conditions should be met by this point.
    hashtag = R'\#'
    if R'\#' not in text:
        assert False
    # intl passing location. For now, let's assume that this is only where # appears.
    ti_temp = text.rfind(hashtag)  # the index of the last hashtag, starting at the backslash
    if any_layer(text, ti_temp, R'\left', R'\right') != 0:
        assert False
    if any_layer(text, ti_temp, R'\begin', R'\end') != 1:
        assert False
    # if dbl.any_layer(text, ti_temp, bm, em) != 1:
    #     return None, None
    start = ti_temp + len(hashtag)
    end = text.find(R'\\', start)
    # we assume we didn't define any matrices in our comment
    comment = text[start:end].strip()
    b_start = len(bm)
    # ti_temp is also where the hashtag point starts, so everything before it is the contents
    equation_contents = text[b_start:ti_temp].strip()
    return equation_contents, comment


DIAG = R"""
LHS = AP = A\begin{bmatrix}
 \mid & \mid & \mid & \mid & \mid \\
{\overset{⃑}{v}}_{1} & {\overset{⃑}{v}}_{2} & {\overset{⃑}{v}}_{3} & \cdots & {\overset{⃑}{v}}_{n} \\
 \mid & \mid & \mid & \mid & \mid \\
\end{bmatrix} = \left\lbrack A\begin{matrix}
 \mid & \mid & \mid & \mid & \mid \\
{\overset{⃑}{v}}_{1} & A{\overset{⃑}{v}}_{2} & A{\overset{⃑}{v}}_{3} & \cdots & A{\overset{⃑}{v}}_{n} \\
 \mid & \mid & \mid & \mid & \mid \\
\end{matrix} \right\rbrack
"""


def split_equation(text: str, max_len: int, list_mode: bool = False) -> Union[None, str, list[str]]:
    """Return a split version of an equation.
    text is the raw equation text, and is not wrapped by display style brackets.
    max_len is the max length of an equation line before a newline
    has to be added.
    Return none if the equation does not need to be split.
    If list_mode is set to True, then return as a list of strings.
    """
    text = text.strip()
    eqn_len = calculate_eqn_length(text)  # split equal signs.
    breaker_chars = ('<', '>', '\\leq', '\\geq', '=', '\\land', '\\lor',
                     '\\subset', '\\subseteq', '\\not\\subset', '\\neq', '\\Rightarrow',
                     '\\approx')
    other_chars = ('+', '-', '\\times', '\\pm', '\\mp', '\\in')
    # breaker_chars_highest = max(len(x) for x in breaker_chars)
    if eqn_len > max_len and any(x in text for x in breaker_chars + other_chars):
        # everything goes down here
        equal_indexes = [0]  # the index where equal signs start.
        for i, char in enumerate(text):
            # if any(text[i:].startswith(x) for x in breaker_chars)
            any_condition = any([
                text.startswith(breaker_chars, i),
                text.startswith(other_chars, i) and i - equal_indexes[-1] >= math.floor(max_len * 0.7)
            ])
            all_condition = all([
                bracket_layers(text, i) == 0,
                any_layer(text, i, '\\left', '\\right') == 0,
                environment_layer(text, i) == 0
            ])

            if any_condition and all_condition:
                # or if the difference of the last equal indices is greater than
                # 0.7 times the line length limit
                equal_indexes.append(i)
        lines_of_eqn = []
        if len(equal_indexes) == 1:
            return None  # we wouldn't be able to split the equation anyway.
        # temp_start = 0
        temp_end = 0
        for i, eq_index in enumerate(equal_indexes):
            if i == 0:
                continue
            temp_start = equal_indexes[i - 1]
            temp_end = eq_index
            lines_of_eqn.append(text[temp_start:temp_end])
        # add the last line
        lines_of_eqn.append(text[temp_end:len(text)])
        # now we have the lines of equation
        # now we want to distribute them
        master = []
        cur_line = []
        for eqn_line in lines_of_eqn:
            cur_line.append(eqn_line)
            cur_line_len = calculate_eqn_length(''.join(cur_line))
            # stack it up
            if cur_line_len > math.floor(max_len * 0.50) and len(cur_line) >= 2:
                # stack it down
                cur_line.pop(-1)
                master.append(cur_line)
                cur_line = [eqn_line]
        if cur_line:
            master.append(cur_line)
        # combine everything.
        new_master = [''.join(cl) for cl in master]
        final_str = ''
        if not list_mode:
            for line in new_master:
                final_str = final_str + '{ ' + line + ' }'
            return final_str
        else:
            return new_master
    return None


def calculate_eqn_length(text: str, disable: Optional[Iterable] = None) -> int:
    """Return the relative length of an equation line.
    """
    # list of defined functions:
    if disable is None:
        disable = []

    replacement_dict = {'+': 'plu', '-': 'miu', '\\times': 'tie'}
    text = replace_many(text, replacement_dict)

    text = text.lower()
    predetermined_functions = {'sin', 'cos', 'tan', 'csc', 'sec', 'cot', 'arcsin', 'arccos', 'arctan',
                               'log', 'ln', 'sqrt', 'sinh', 'cosh', 'tanh', 'coth'}
    # text = text.replace('\\left', '')
    # text = text.replace('\\right', '')

    # fraction blocks (this will recursively run itself)
    if 'frac' not in disable:
        while True:
            frac_index = find_nth(text, R'\frac', 1)
            if frac_index == -1:
                break
            ending_frac_index = index_fourth_closing_bracket(text, frac_index) + 1  # AT the char AFTER }
            if ending_frac_index == 0:
                break
            text = text[:frac_index] + seperate_fraction_block(text[frac_index:ending_frac_index]) + \
                text[ending_frac_index:]

    if 'matrix' not in disable:
        text = remove_matrices(text, 'matrix')
        text = remove_matrices(text, 'bmatrix')

    for fun in predetermined_functions:
        text = text.replace('\\' + fun, fun)

    text = remove_envs(text)
    text = text.replace(' ', '')
    text = text.replace(',', ', ')
    if disable is None:
        pass
    # logging.warning(text)
    return len(text)


def remove_envs(text: str) -> str:
    """Remove everything between \\ up until it's not a letter

    >>> temp_text = '\\lim(2+4)+\\sum(3+6)'
    >>> remove_envs(temp_text)
    '(2+4)+(3+6)'
    """
    backslash_location = -1
    index_diff = 0
    first_backslash = False
    ending_location = -1
    for i, char in enumerate(text):
        if not first_backslash and char == '\\':
            backslash_location = i
            first_backslash = True
            continue
        if first_backslash:
            if char in ALPHABET:
                index_diff += 1
            else:
                if index_diff == 0:
                    first_backslash = False
                else:
                    ending_location = i
                    break
    if backslash_location == -1 or ending_location == -1:
        return text
    else:
        text = text[:backslash_location] + 'j' + text[ending_location:]
        return remove_envs(text)


def index_fourth_closing_bracket(text: str, index: int) -> int:
    """Return the index of the fourth closing bracket starting at index.
    """
    bracket_positions = []
    bracket_layers_sep = 0
    prev_char = None
    for i, char in enumerate(text):
        if i <= index:
            prev_char = char
            continue
        else:
            if prev_char != '\\':
                if char == '{':
                    if bracket_layers_sep == 0:
                        bracket_positions.append(i)
                    bracket_layers_sep += 1
                if char == '}':
                    if bracket_layers_sep == 1:
                        bracket_positions.append(i)
                        if len(bracket_positions) == 4:
                            return i
                    bracket_layers_sep -= 1
            prev_char = char
    return -1


def seperate_fraction_block(frac_text: str) -> str:
    """Return the side of the fraction that is longer.
    Preconditions:
        - frac_text looks like \\frac{}{}

    >>> temp_text = R'\frac{2+4+6}{7}'
    >>> seperate_fraction_block(temp_text)
    '2+4+6'
    """
    bracket_positions = []
    bracket_layers_sep = 0
    prev_char = None
    for i, char in enumerate(frac_text):
        if prev_char != '\\':
            if char == '{':
                if bracket_layers_sep == 0:
                    bracket_positions.append(i)
                bracket_layers_sep += 1
            if char == '}':
                if bracket_layers_sep == 1:
                    bracket_positions.append(i)
                bracket_layers_sep -= 1
        prev_char = char
    assert bracket_positions[-1] == len(frac_text) - 1  # the last closing brace
    numerator = frac_text[bracket_positions[0] + 1:bracket_positions[1]]
    denominator = frac_text[bracket_positions[2] + 1:bracket_positions[3]]
    num_len = calculate_eqn_length(numerator, ['frac', 'matrix'])
    den_len = calculate_eqn_length(denominator, ['frac', 'matrix'])
    return numerator if num_len >= den_len else denominator


def remove_matrices(text: str, matrix_type: str) -> str:
    """Approximate the length of all matrices.
    """
    start = R'\begin{' + matrix_type + '}'
    end = R'\end{' + matrix_type + '}'
    start_pos_1 = find_nth(text, start, 1)  # the index of the first char of start.
    start_pos_2 = start_pos_1 + len(start)  # the index of the char after start.
    end_pos_1 = find_nth(text, end, 1)
    end_pos_2 = end_pos_1 + len(end)
    # can't find any; occurs when environments are exhausted
    if -1 in {start_pos_1, start_pos_2, end_pos_1, end_pos_2}:
        return text
    else:
        matrix_text = text[start_pos_2:end_pos_1].replace('\n', '')
        matrix_rows = matrix_text.split(R'\\')
        row_len = []  # a list of ints
        for row in matrix_rows:
            row_len.append(calculate_eqn_length(row, ['frac', 'matrix']))
        max_row_len = max(row_len)
    text = text[:start_pos_1] + 'a' * max_row_len + text[end_pos_2:]
    return remove_matrices(text, matrix_type)


def combine_environments(text: str, env: str) -> str:
    """Combine broken-up environments.
    Example: env = 'align*'"""
    skip = 1
    end_str = '\\end{' + env + '}'
    begin_str = '\\begin{' + env + '}'
    while True:
        end_pos = find_nth(text, end_str, skip)
        if end_pos == -1:
            break
        next_start_pos = find_nth(text, begin_str, 1, end_pos + len(end_str))
        if next_start_pos == -1:
            break
        # this is the position of the backslash of the next environment
        text_between = text[end_pos + len(end_str):next_start_pos]
        if check_region_empty(text_between):
            text = text[:end_pos] + R' \\' + text[next_start_pos + len(begin_str):]
        else:
            skip += 1
    return text


def check_region_empty(text_between: str) -> bool:
    """Check if text_between only contains newline characters and spaces
    """
    for char in text_between:
        if char not in {' ', '\n'}:
            return False
    return True


TEMP_OLD_TEXT = r"""
\title{This is the title for now}
\author{PLEASE DO THIS I CANNOT}
\date{YESTERDAY I DID}
"""


# def test_author() -> None:
#     """Why
#     """
#     aa = swap_author(TEMP_OLD_TEXT, 'John', 'author')
#     # print(aa)


def swap_day_with_today(text: str) -> str:
    """Swap the date of the document with today.
    If there is no date specified, then add a date with today.
    """
    raise NotImplementedError


def find_author(text: str, props: str = 'author') -> Optional[str]:
    """Find the current author of the text.
    text is the entire text.
    Return None otherwise.
    """
    auth = '\\' + props + '{'
    author_pos_raw = rfind_nth(text, auth, 1)  # the position of the \ in \author{}
    if author_pos_raw == -1:
        return None
    else:
        # the position of the character after the { in author declaration
        author_pos = author_pos_raw + len(auth)
        end_author_pos = local_env_end(text, author_pos_raw)  # focused on the closing bracket
        author_name = text[author_pos:end_author_pos]
        return author_name


def swap_author(text: str, new_author: str, props: str = 'author') -> str:
    """Change the author. text is the entire text.
    If no existing author field, return what is written in text.
    """
    auth = '\\' + props + '{'
    author_pos = find_nth(text, auth, 1)
    if author_pos == -1:
        return text
    end_author_pos = local_env_end(text, author_pos)
    return text[:author_pos] + auth + new_author + '}' + text[end_author_pos:]


def strip_string(text: str) -> str:
    """Strip the string.
    """
    text = text.replace('\n', '')
    return text.strip()


# OBJECTIVES: For each section, remove any newline characters in between them.


def modify_text_in_environment(text: str, env: str, modification: Callable[[str], str]) -> str:
    """Modify text in all instances of the environment env.
    Preconditions:
        - No LaTeX code in verbatim environments
        - Target environment doesn't nest any additional environments
    this will not work for things that are not defined as environments
    """
    envs_traversed = 1
    begin = R'\begin{' + env + '}'
    # end = R'\end{' + env + '}'
    while True:
        # print(envs_traversed)
        start_pos_1 = find_nth(text, begin, envs_traversed)  # the index at the backslash of begin
        start_pos_2 = start_pos_1 + len(begin)  # the index on the char after begin env
        end_pos_1 = find_env_end(text, start_pos_1, env)
        # end_pos_1 = find_nth(text, end, envs_traversed)
        # end_pos_2 = end_pos_1 + len(end)

        if -1 in {start_pos_1, end_pos_1}:
            break

        before = text[:start_pos_2]
        during = text[start_pos_2:end_pos_1]
        after = text[end_pos_1:]

        during = modification(during)

        text = before + during + after
        envs_traversed += 1
    return text


def longtable_backslash_add_line(text: str) -> str:
    """Add hline after all \\s, except the first one and the last one.

    Preconditions: no align regions or anything containing backslashes are allowed
    """
    text = text.replace(R'\\', '🯰', 1)
    backslash_occur = text.count(R'\\')
    text = text.replace(R'\\', R'\\ \hline', backslash_occur - 1)
    text = text.replace('🯰', R'\\')
    return text


def longtable_backslash_add_full(text: str) -> str:
    return modify_text_in_environment(text, 'longtable', longtable_backslash_add_line)


# bracket_layers is a useful function


TEST_BIB = r"""
@conference{Xconference,
    author    = "",
    title     = "",
    booktitle = "",
    ?_editor   = "",
    ?_volume   = "",
    ?_number   = "",
    ?_series   = "",
    ?_pages    = "",
    ?_address  = "",
    year      = "XXXX",
    ?_month    = "@youuuu",
    ?_publisher= "",
    ?_note     = "",
}

@customone{thenotthe,
    author    = "",
    title     = "",
    booktitle = "",
    ?_editor   = "",
    ?_volume   = "",
    ?_number   = "",
    ?_series   = "",
    ?_pages    = "",
    ?_address  = "",
    year      = "XXXX",
    ?_month    = "",
    ?_publisher= "",
    ?_note     = "",
}
"""


def extract_authors_from_bib(bib_text: str) -> list[str]:
    """Return a list of author tags from a .bib file.

    Preconditions:
        - bib_text is the text contents of the .bib file and must be formatted as such.
        - author tags don't have commas
        - none of the file types referenced are in a format that requires an opening brace
    """
    skip = 1
    authors = []
    while True:
        at_ind = find_nth(bib_text, '@', skip)
        if at_ind == -1:
            break
        # who would ever put an @ symbol inside any field that isn't an author declaration
        bracket_layer = bracket_layers(bib_text, at_ind)
        if bracket_layer > 0:
            logging.info('someone put an @ symbol inside the citation thing')
            skip += 1
            continue
        bracket_afterwards = find_nth(bib_text, '{', 1, at_ind)
        comma_afterwards = find_nth(bib_text, ',', 1, bracket_afterwards)
        author_name = bib_text[bracket_afterwards + 1:comma_afterwards]
        authors.append(author_name)
        skip += 1
    return authors


EX_AT = r"""
\title{Title}
\subtitle{Subtitle}
\author{Author}
\date{What day is it}
"""


def retain_author_info(text: str) -> str:
    """Return author-related metadata
    """
    # add subtitle to mdl to force a subtitle
    mdl = ['title', 'author', 'date']
    metadata = {}
    for md in mdl:
        auth = find_author(text, md)
        if auth is not None:
            metadata[md] = auth
    author_text = ''
    for mdd, txt in metadata.items():
        # if 'ons for packages loaded elsewher' in txt:
        #     txt = ''
        author_text += '\\' + mdd + '{' + txt + '}\n'
    return author_text


def verbatim_to_listing(text: str, lang: str, plugin: str = '', minted_params: str = '') -> tuple[str, bool]:
    """Converts all verbatim environments to the language in question.
    No language detection is done.
    Language must be in this list:
    https://www.overleaf.com/learn/latex/Code_listing

    This may only run once.
    """
    if plugin not in ('minted', 'lstlisting'):
        return text, False
    language_dir = {'minted': MINTED_LANGUAGES, 'lstlisting': LISTING_LANGUAGES}[plugin]
    # MINTED_LANGUAGES if lang.strip().lower() == 'minted' else LISTING_LANGUAGES

    skip = 1
    bv = R'\begin{verbatim}'
    ev = R'\end{verbatim}'

    converted_once = False
    while True:
        closest_verb = find_nth(text, bv, skip)
        if closest_verb == -1:
            break
        # look for the end
        ending_verb = find_env_end(text, closest_verb, 'verbatim')
        before = text[:closest_verb]
        during = '\n' + text[closest_verb + len(bv):ending_verb].strip() + '\n'
        after = text[ending_verb + len(ev):]

        language = ''
        for lan in language_dir:
            if lan.lower() in during.lower():
                language = lan
                break

        assert language in language_dir or lang == ''
        if language == '':
            language = lang  # lang is the default language
        # if it is still empty, then:
        if language == '':
            skip += 1
            continue

        # BY THIS POINT, A LANGUAGE HAS BEEN DETECTED.
        # print('FOUND A LANGUAGE!!!')
        converted_once = True
        # otherwise, it must have a language.
        if plugin == 'minted':
            params = minted_params if minted_params.startswith('[') and minted_params.endswith(']') else \
                '[' + minted_params + ']'
            command_start = '\\begin{minted}' + params + '{' + language + '}'
            command_end = '\\end{minted}'
        else:
            params = minted_params[1:-1] if minted_params.startswith('[') and minted_params.endswith(']') else \
                minted_params
            command_start = '\\begin{lstlisting}[language=' + language + ', ' + params + ']'
            command_end = '\\end{lstlisting}'

        text = before + command_start + during + command_end + after
    return text, converted_once


def first_upper(text: str) -> str:
    """Capitalize the first letter.
    """
    if len(text) > 0:
        return text[0].upper() + text[1:]
    else:
        return text


def any_layer(text: str, index: int, start: str, end: str) -> int:
    """Return the depth of the index in text, depending on start and end.

    If the index is in the middle of start and end, the first letter
    of the starting and ending keywords will act as the marker.

    If the index is on the first character of the start and end
    keyword, it will act as the index is one more, then do calculations
    normally.

    Preconditions:
        - '\\' + start not in text
        - '\\' + end not in text

    >>> start_t = 'start'
    >>> end_t = 'end'
    >>> text_t = 'start01end234start0123end789end'
    >>> any_layer(text_t, 19, start_t, end_t)
    1
    """
    bsq = start.startswith('\\') or end.startswith('\\')
    n1 = 1
    starting_ind = []
    while True:
        temp_ind = find_nth(text, start, n1)
        if temp_ind == -1:
            break
        else:
            if bsq:
                if not text[temp_ind + len(start)].isalpha():
                    # prevents mistaking \rightarrow
                    starting_ind.append(temp_ind)
            else:
                starting_ind.append(temp_ind)

            n1 += 1
    n2 = 1
    ending_ind = []
    while True:
        temp_ind2 = find_nth(text, end, n2)
        if temp_ind2 == -1:
            break
        else:
            if bsq:
                if not text[temp_ind2 + len(end)].isalpha():
                    ending_ind.append(temp_ind2)
            else:
                ending_ind.append(temp_ind2)
            n2 += 1
    start_depth = lst_smaller_index(index, starting_ind)
    ending_depth = lst_smaller_index(index, ending_ind)
    final_depth = start_depth - ending_depth
    return final_depth


def lst_smaller_index(item: int, lst: list[int]) -> int:
    """Return the index AFTER where item occurs in list.
    Otherwise, return the index where item is greater than
    the item of the current index, but less than the item of the
    next index.

    Preconditions:
        - lst is sorted
        - lst has no repeating elements

    >>> tl = [2, 4, 6, 8, 10]
    >>> lst_smaller_index(10, tl)
    5
    >>> lst_smaller_index(7, tl)
    3
    >>> lst_smaller_index(6, tl)
    3
    >>> lst_smaller_index(5, tl)
    2
    >>> lst_smaller_index(4, tl)
    2
    >>> lst_smaller_index(3, tl)
    1
    >>> lst_smaller_index(2, tl)
    1
    >>> lst_smaller_index(1, tl)
    0

    """
    for i, li in enumerate(lst):
        if item < li:  # 1
            return i
    return len(lst)


def local_env_layer(text: str, index: int, local_env: str) -> bool:
    """Return whether index is in a local environment.
    Like black slash texttt or so on.

    Preconditions:
        - index isn't located anywhere where the env substring appears
        - text[index] != '}'
        - '}' not in local_env

    >>> te = 'abc\\wh{force}the'
    >>> local_env_layer(te, 10, 'wh')
    True
    """
    env_kw = '\\' + local_env + '{'
    closest_starter = text.rfind(env_kw, 0, index)  # type: int
    if closest_starter == -1:
        return False
    n = 1
    # cur_ind = None
    while True:
        closest_bracket = find_nth(text, '}', n, closest_starter)
        if closest_bracket == -1:
            raise ValueError
        b_layer = bracket_layers(text, closest_bracket, starting_index=closest_starter)
        if b_layer == 0:
            # cur_ind = closest_bracket
            break
        else:
            n += 1
    return closest_starter < index < closest_bracket


def local_env_end(text: str, index: int) -> int:
    """Return the position of the closing brace where the local environment ends.

    It is strongly recommended that text[index] == '\\' and
    is the start of a local environment declaration. Though the farthest
    index can be is at the position of the opening brace.

    Raise ValueError if an end cannot be found.

    >>> te = 'abc\\wh{fo3rce}the'
    >>> local_env_end(te, 6)
    13
    """
    n = 1
    while True:
        closest_bracket = find_nth(text, '}', n, index)
        if closest_bracket == -1:
            raise ValueError("Opening bracket without a closing bracket detected")
        b_layer = bracket_layers(text, closest_bracket, starting_index=index)
        if b_layer == 0:
            # cur_ind = closest_bracket
            break
        else:
            n += 1
    return closest_bracket


TEST_STR_AGAIN = r"""
CCCCCC
\begin{verbatim}
ccccccccccccccccccccc
\end{verbatim}
CCCCCC
"""


def find_not_in_environment(text: str, sub: str, env: Union[str, list[str]],
                            start: int = 0, skip: int = 1) -> int:
    """Similar to find, but prevent finding things in the specified environment.

    Return -1 on failure.
    """
    # skip = 1
    if isinstance(env, str):
        env = [env]
    while True:
        ind = find_nth(text, sub, skip, start)
        if ind == -1:  # always return -1 on failure.
            return -1
        failed = False
        for env_instance in env:
            if check_in_environment(text, env_instance, ind):
                failed = True
                break
        if failed:
            skip += 1
            continue
        else:
            return ind


def find_not_in_environment_tolerance(text: str, sub: str, env: dict[str, int],
                                      start: int = 0, skip: int = 1) -> int:
    """Similar to find, but prevent finding things in the specified environment.
    env - key is env name, item is the depth where envs will be skipped (any less and
    it will be a pass)

    For example, a depth overlimit of 1 means at least one layer deep will cause it
    to be skipped. A depth overlimit of 2 means 2 layers will cause it to be skipped.
    0 means invisible.

    Return -1 on failure.
    """
    # skip = 1
    if isinstance(env, str):
        env = [env]
    while True:
        ind = find_nth(text, sub, skip, start)
        if ind == -1:  # always return -1 on failure.
            return -1
        failed = False
        for env_instance, depth_overlimit in env.items():
            if environment_depth(text, ind, env_instance) >= depth_overlimit:
                failed = True
                break
        if failed:
            skip += 1
            continue
        else:
            return ind


def find_not_in_any_env_tolerance(text: str, sub: str,
                                  start: int = 1,
                                  depth_overlimit: int = 1, skip: int = 1) -> int:
    """Similar to find, but prevent finding things in the specified environment.
    env - key is env name, item is the depth where envs will be skipped (any less and
    it will be a pass)

    For example, a depth overlimit of 1 means at least one layer deep will cause it
    to be skipped. A depth overlimit of 2 means 2 layers will cause it to be skipped.
    0 means invisible.

    Return -1 on failure.
    """
    # skip = 1
    while True:
        ind = find_nth(text, sub, skip, start)
        if ind == -1:  # always return -1 on failure.
            return -1
        failed = False
        if environment_depth(text, ind) >= depth_overlimit:
            failed = True
        if failed:
            skip += 1
            continue
        else:
            return ind


def check_in_environment(text: str, env: str, index: int) -> bool:
    """Return if current index in environment.

    If index is part of an environment declaration, treat as if the
    declaration never existed.

    >>> check_in_environment(TEST_STR_AGAIN, 'verbatim', 29)
    True
    """
    if index < 0:
        index = len(text) - index
    env_str = '\\begin{' + env + '}'
    env_end = '\\end{' + env + '}'
    v1_cie = text.find(env_str, index)  # this is allowed to be -1. Fallback to len(text)
    if v1_cie == -1:
        v1_cie = len(text)
    v2_cie = text.find(env_end, index)
    if v2_cie == -1:
        return False
    v3_cie = text.rfind(env_str, 0, index)
    if v3_cie == -1:
        return False
    v4_cie = text.rfind(env_end, 0, index)  # this is allowed to be -1.
    return not (v1_cie < v2_cie or v4_cie > v3_cie)


def do_something_to_local_env(text: str, env: str, func: Callable[[str], str]) -> str:
    """Do something to everything in a local environment.
    Such as texttt{modify stuff here}.

    Preconditions:
        - No LaTeX-like code in verbatim environments
    """
    env_str = '\\' + env + '{'
    skip = 1
    while True:
        # locate where the next environment is
        ind = find_nth(text, env_str, skip)
        if ind == -1:
            break
        # locate where the local environment ends
        local_skip = 1
        while True:
            ind_2 = find_nth(text, '}', local_skip, ind)
            if text[ind_2 - 1] == '\\':
                local_skip += 1
                continue
            assert ind_2 != -1
            bracket_layer = bracket_layers(text, ind_2)
            if bracket_layer == 0:
                break
            else:
                local_skip += 1
                # continue
        # Do stuff in the text. TODO: Enable ignore nested envs; enable ignore commands
        env_text = text[ind + len(env_str):ind_2]
        new_env_text = func(env_text)
        text = text[:ind + len(env_str)] + new_env_text + text[ind_2:]
        skip += 1
    return text


RRR = r"""
\[\begin{matrix}
\int_{}^{}{4 + 2dx} + \sqrt{4 + 2}\ \# 40 \\
\end{matrix}\]

\[\begin{matrix}
\int_{}^{}{4 + 2dx} + \sqrt{4 + 2}\ \# 40 \\
\end{matrix}\]

\[\begin{matrix}
\int_{}^{}{4 + 2dx} + \sqrt{4 + 2}\ \# 40 \\
\end{matrix}\]

\[\begin{matrix}
\int_{}^{}{4 + 2dx} + \sqrt{4 + 2}\ \# 40 \\
\end{matrix}\]
"""


def bad_backslash_replacer(text: str, eqs: str = '\\[', eqe: str = '\\]') -> str:
    """Replaces all bad backslash instances with just spaces.
    """
    rpl = R'\ '
    # eqs = R'\['
    # eqe = R'\]'
    fake_unicode = '🮿'
    ind = 0
    while True:
        try:
            extracted, st_in, en_in = find_between(text, eqs, eqe, ind)
        except ValueError:
            break
        extracted = extracted.replace(R'\ \text{', fake_unicode)
        extracted = extracted.replace(rpl, ' ')
        extracted = extracted.replace(fake_unicode, R'\ \text{')
        text = text[:st_in] + extracted + text[en_in:]
        ind = st_in + len(eqs) + len(extracted) + len(eqe)
    # Add spaces after all text envs
    skip_text = 0

    # comment this entire thing out for no post adding
    while True:
        closest_text = find_closest_local_env(text, 'text', skip_text)
        if closest_text == -1:
            break
        if text[closest_text - 2:closest_text] != R'\ ':
            skip_text += 1
            continue
        end_of_text = local_env_end(text, closest_text)
        if end_of_text == -1:
            break  # never supposed to run.
        if text[end_of_text + 1:end_of_text + 3] != R'\ ':
            text = text[:end_of_text + 1] + R'\ ' + text[end_of_text + 1:]
        skip_text += 1
    return text


def find_between(s: str, first: str, last: str, stt: int) -> tuple[str, int, int]:
    """Return extracted string between two substrings, start index, and end index
    start index is based on extracted.
    """
    start = s.index(first, stt) + len(first)
    end = s.index(last, start)
    return s[start:end], start, end


TEST_TEXT_AGAIN = r"""
\end{proof}
\begin{proof}
proof text here
\begin{proof}
\begin{proof}
\begin{proof}
\end{proof}
\end{proof}
\end{proof}
\end{proof}
\begin{proof}
\begin{proof}

\begin{proof}
\begin{proof}


"""

TEST_DOC_2 = r"""

\section{aaaaa}
THIS IS THIS IS
THIS IS THIS IS
\subsection{THIS IS THIS IS}
THIS IS THIS IS THIS IS THIS
THIS IS THIS IS THIS IS THIS IS
THIS IS THIS IS THIS
\subsubsection{THIS IS THIS IS THIS IS}
COMPLETELY BLANK TEXT
"""


def extract_all_sections(text: str) -> list[str]:
    """Extract all sections from this document."""
    sections = []
    prev_ind_so_far = -1
    while True:
        # print('in while loop')
        cur_ind_so_far = find_next_section(text, prev_ind_so_far + 1)
        # print(cur_ind_so_far)
        section_text = text[prev_ind_so_far:cur_ind_so_far]
        sections.append(section_text)
        prev_ind_so_far = cur_ind_so_far
        if cur_ind_so_far >= len(text):
            break
    return sections


def environment_fallback(text: str, target_env: str) -> str:
    """Prevents environments from not being closed.
    An environment is not closed if it is open within a section
    and closed after the section ends.

    Also, if an environment is not open in a section but closed in
    a later section, then we have a problem.

    A proof environment is well-formed if it is well formed.
    """
    env_str = '\\begin{' + target_env + '}'
    env_end = '\\end{' + target_env + '}'
    # n = 1
    # m = 1
    # begin environments without proper endings
    new_section_list = []
    section_list = extract_all_sections(text)
    for t_section in section_list:
        n = 1
        m = 1
        while True:
            closest_start = find_nth(text, env_str, n, 0)
            closest_end = find_nth(text, env_end, m, 0)
            if closest_start != -1 and closest_end != -1 and closest_start > closest_end:
                # remove closest end and retry
                t_section = t_section[:closest_end] + t_section[closest_end + len(env_end):]
            elif closest_end == -1 and closest_start != -1:
                # only start exists? remove it
                t_section = t_section[:closest_start] + t_section[closest_start + len(env_str):]
            elif closest_start == -1 and closest_end != -1:
                # remove closest end and retry
                t_section = t_section[:closest_end] + t_section[closest_end + len(env_end):]
            elif closest_start == -1 and closest_end == -1:
                break
            else:
                n += 1
                m += 1
        new_section_list.append(t_section)
    return ''.join(new_section_list)

    # preconditions: both above is not -1. Otherwise, we have to handle them seperately
    #     section_from_start = find_next_section(text, closest_start)
    #     if closest_start != -1 and closest_end != -1:
    #         if closest_start < closest_end and not (closest_start <= section_from_start <= closest_end):
    #             # passable
    #             n += 1
    #             m += 1
    #             continue
    #         elif closest_start < closest_end and closest_start <= section_from_start <= closest_end:
    #             # remove the proof starters and proof stoppers
    #             text = text[:closest_start] + text[closest_start + len(env_str):] + text[:closest_end] + \
    #             text[closest_end + len(env_end):]
    #         else:
    #             # closest end is before closest start so remove the proof closure
    #             text = text[:closest_end] + text[closest_end + len(env_end):]
    #     elif closest_start == -1 and closest_end != -1:
    #         # remove it
    #         text = text[:closest_end] + text[closest_end + len(env_end):]
    #     elif closest_end == -1 and closest_start != -1:
    #         # conclude at end of section
    #         text = text[:section_from_start] + env_end + text[:section_from_start]
    #     elif closest_end == -1 and closest_end == -1:
    #         # stop checking
    #         break
    # return text
    #

    #     env_s_ind = find_nth(text, env_str, n)
    #     if env_s_ind == -1:
    #         break
    #     env_next_s_ind = find_nth(text, env_str, n + 1)
    #     if env_next_s_ind == -1:
    #         env_next_s_ind = len(text)
    #     ending_env_ind = text.find(env_end, env_s_ind)
    #     if ending_env_ind == -1:
    #         ending_env_ind = env_next_s_ind
    #     next_section_ind = find_next_section(text, env_s_ind)
    #     if next_section_ind < ending_env_ind < env_next_s_ind:
    #         # if the next section starts before the proof ends
    #         logging.warning('Found a runaway environment definition')
    #         text = text[:next_section_ind] + '\n' + env_end + '\n\n' + text[next_section_ind:]
    #     elif env_next_s_ind < ending_env_ind < next_section_ind:
    #         # if the next proof starts before the current proof ends
    #         logging.warning('Found a new environment declaration whilst the previous one'
    #                         ' never closed')
    #         text = text[:env_next_s_ind] + '\n' + env_end + '\n\n' + text[env_next_s_ind:]
    #         print(text)
    #     elif env_next_s_ind == ending_env_ind == next_section_ind:
    #         # if the proof doesn't close and the end of the document hits without
    #         # any of the other cases occurring
    #         logging.warning('end of document reached')
    #         text = text[:env_s_ind] + text[env_s_ind + len(env_str):]
    #     n += 1
    # # end environments without proper beginnings
    # n = 1  # reset n again
    # while True:
    #     env_e_ind = find_nth(text, env_end, n)
    #     if env_e_ind == -1:
    #         break
    #     prev_env_end = text.rfind(env_end, 0, env_e_ind)
    #     # -1 fallback default
    #     if prev_env_end == -1:
    #         prev_env_end = -5
    #     prev_section = find_previous_section(text, env_e_ind)
    #     # -1 fallback default
    #     prev_env_start = text.rfind(env_str, 0, env_e_ind)
    #     # -1 fallback default
    #     if prev_env_start == -1:
    #         prev_env_start = -7
    #     # this is required:
    #     # the declaration for the environment must be before the environment ending
    #     # and the declaration for the previous section must be placed before
    #
    #     condition = prev_env_start > prev_env_end and prev_env_start > prev_section
    #     if condition:
    #         n += 1
    #     else:
    #         text = text[:env_e_ind] + text[env_e_ind + len(env_end):]
    # return text


def find_previous_section(text: str, max_index: int, max_depth: int = 6) -> int:
    """Find when the previous section / subsection / subsubsection occurs.
    The number returned should be the index of the backslash of whehere
    the new section occurs.

    Return -1 on failure.
    """
    highest_start = 0
    if max_depth < 0:
        max_depth = 0
    for i in range(max_depth, -1, -1):
        section_keyword = '\\' + 'sub' * i + 'section' + '{'
        s_start = text.rfind(section_keyword, 0, max_index)
        # -1 already does the job here
        if highest_start < s_start:
            highest_start = s_start
    return highest_start


def find_next_section(text: str, min_index: int, max_depth: int = 6) -> int:
    """Find when the next section / subsection / subsubsection occurs.
    The number returned should be the index of the backslash of where
    the new section occurs.
    section is depth 0. subsection is depth 1.
    If it can't find the next section then return the position of the end of the document.
    """
    lowest_start = len(text)
    if max_depth < 0:
        max_depth = 0
    for i in range(max_depth, -2, -1):
        if i != -2:
            section_keyword = '\\' + 'sub' * i + 'section' + '{'
        else:
            section_keyword = '\\chapter{'
        # print(f'looking for {section_keyword}')
        s_start = text.find(section_keyword, min_index)
        if s_start == -1:
            s_start = len(text)
        if lowest_start > s_start:
            lowest_start = s_start
    return lowest_start


def quote_to_environment(text: str, env: LatexEnvironment, has_extra_args: bool = True) -> str:
    """Turns quotes to environments. env is the name of the env to convert to.
    env_kw is the keyword for this region to be formatted like this (syntax in MD):
    **Definition: Extra args.** Definition text.
    Text boldface must be used here.

    has_extra_args: you know what this is.

    Syntax: Env call: <Env tag>. <Text afterwards>
    We assume Env call is bolded before being passed to this function.

    Preconditions:
        - No LaTeX code in verbatim environments
        - Target environment doesn't nest any additional environments
    this will not work for things that are not defined as environments
    """
    envs_traversed = 1
    begin = R'\begin{quote}' + '\n'
    end = '\n' + R'\end{quote}'
    while True:
        # print(envs_traversed)
        start_pos_1 = find_nth(text, begin, envs_traversed)  # the index at the backslash of begin
        start_pos_2 = start_pos_1 + len(begin)  # the index on the char after begin env

        end_pos_1 = find_nth(text, end, envs_traversed)
        # end_pos_2 = end_pos_1 + len(end)

        if -1 in {start_pos_1, end_pos_1}:
            break

        # before = text[:start_pos_2]
        during = text[start_pos_2:end_pos_1]

        tbf = R'\textbf{'

        if not during.startswith(tbf):
            envs_traversed += 1
            continue
        declare_end = local_env_end(during, 0)
        bold_str = during[len(tbf):declare_end]
        if not bold_str.startswith(env.env_name):  # is something like "Definition" or an alias to that
            envs_traversed += 1
            continue
        k_begin = R'\begin{' + env.env_name.lower() + '}'
        k_end = R'\end{' + env.env_name.lower() + '}'
        env_starter_contents = bold_str.split(':')
        if has_extra_args:
            if len(env_starter_contents) == 2:
                env_title = env_starter_contents[1].strip().replace('\n', ' ').replace('.', '')
            elif len(env_starter_contents) == 1:
                env_title = ''
            else:
                assert False  # who decided to put more than one colon?
            br = ('{', '}') if env.extra_args_type == 'brace' else ('[', ']')
            text = text[:start_pos_1] + env.env_prefix + k_begin + br[0] + \
                env_title + br[1] + \
                env.env_suffix + '\n' + \
                during[declare_end + 1:end_pos_1] + k_end + text[end_pos_1 + len(end):]
        else:
            text = text[:start_pos_1] + env.env_prefix + k_begin + \
                   env.env_suffix + '\n' + \
                   during[declare_end + 1:end_pos_1].strip() + k_end + text[end_pos_1 + len(end):]
    return text


def detect_if_bib_exists(text: str, bib_keyword: str) -> tuple[bool, str, int]:
    """Return True if there is an upper section named this:

    Bibliography

    This is case-sensitive, but no trailing whitespaces or newlines.

    If True is returned, it will also return text with the bib section removed.
    It will also return the index where the original bibliography was.
    Otherwise, it will return text with no modifications.
    It will also return the bib data if it was stated in the MS Word document.

    No works cited or references - we want Chicago style only.
    """
    bib_section: str = '\\section{' + bib_keyword + '}'
    r_location = text.rfind(bib_section)
    if r_location == -1:
        return False, text, -1
    # else
    next_section = find_next_section(text, r_location + len(bib_section), max_depth=0)
    # inside = text[r_location + len(bib_section):next_section]  # all the text within that

    # vb = inside.find('\\begin{verbatim}')
    # if vb != -1:
    #     vb2 = inside.find('\\end{verbatim}')
    #     bib_text = inside[vb + len('\\begin{verbatim}'):vb2]
    # else:
    #     bib_text = ''
    text = text[:r_location] + '\n\n\n' + text[next_section:]
    return True, text, r_location + 1


def verb_encryptor(count: int, lang: str = '') -> str:
    """This was a list of verb encryptors, but
    we wouldn't list everything

    Preconditions:
        - count >= 0
    """
    return f'ｗｗBLｗ{count}⚋⚌⚍⚎⚏ｗ{lang}ｗ' if lang != '' else f'ｗBTｗ{count}⚋⚌⚍⚎⚏ｗｗｗ'


# def check_verbatims() -> str:
#     """I just want to see if this works
#
#     """
#     txt = r"""
#     no longer encrypted
#     \begin{verbatim}
#         encrypted
#     \end{verbatim}
#     not encrypted yet
#     \begin{verbatim}
#         encrypted
#     \end{verbatim}
#     not encrypted yet
#     """
#     txt, d_info = hide_verbatims(txt)
#     pass
#     tx = show_verbatims(txt, d_info)
#     print(tx)
#     return tx


def what_section_is_this(text: str, index: int) -> Optional[str]:
    """Return the name of the section text at index is in.
    It will only look for top-level indices.

    Preconditions:
        - index is not inside a section declaration
    """
    prev_section_location = text.rfind('\\section{', 0, index)
    if prev_section_location == -1:
        return None
    else:
        ps_end = local_env_end(text, prev_section_location)
        section_name = text[prev_section_location + len('\\section{'):ps_end]
        return section_name


def hide_verbatims(text: str, track: str = 'Bibliography', verb_plugin: str = '') -> tuple[str, dict[str, str]]:
    """Hide all verbatim stuff.
    Put them in a dictionary.

    Note: the begin and end verbatim calls will still be present in the document. It is merely
    the text contents that are being concealed.
    """
    # if bibliography_keyword != '':
    #     bib_section = '\\section{' + bibliography_keyword + '}'
    #     bib_index = text.rfind(bib_section)
    #     if bib_index != -1:
    #         next_section = find_next_section(text, bib_index + len(bib_section), max_depth=0)
    #         bib_indices = (bib_index + len(bib_section), next_section)

    # else:
    #     bib_section = 'INVALID'
    env = 'verbatim'
    envs_traversed = 1
    begin = R'\begin{' + env + '}'
    end = R'\end{' + env + '}'
    dict_so_far = {}
    i = 0
    while True:
        # print(envs_traversed)
        start_pos_1 = find_nth(text, begin, envs_traversed)  # the index at the backslash of begin
        start_pos_2 = start_pos_1 + len(begin)  # the index on the char after begin env

        end_pos_1 = find_nth(text, end, envs_traversed)
        # end_pos_2 = end_pos_1 + len(end)

        if -1 in {start_pos_1, end_pos_1}:
            break

        before = text[:start_pos_2]
        during = text[start_pos_2:end_pos_1].replace('“', '"').replace('”', '"').replace("’", "'").replace("‘", "'")
        after = text[end_pos_1:]

        code_lang, during = identify_language(during, verb_plugin)

        curr_section = what_section_is_this(text, start_pos_1)
        if curr_section is None:
            curr_section = 'NO<T A<P<<<<P>>>LICAB<LE AT THIS T<<IME'

        ve_value = verb_encryptor(i, code_lang)
        dict_so_far[ve_value] = during
        during = ve_value

        if curr_section.strip() == track:
            dict_so_far['BIBLO'] = dict_so_far[ve_value]

        text = before + '\n' + during + '\n' + after
        envs_traversed += 1
        i += 1
    return text, dict_so_far


def show_verbatims(text: str, verb_info: dict[str, str]) -> str:
    """Unhide all verbatim environments.
    """
    for key, value in verb_info.items():
        text = text.replace(key, value)
    return text


def identify_language(text: str, verb_plugin: str = '') -> tuple[str, str]:
    """Return the language of the
    text. Return the text with the language removed.

    Strip text
    Ignore the first instances of //, #, or -- (one of the three)
    Strip text
    Next word has to declare the language
    If so, then return the language and delete what
    declared the language
    Strip text

    EXAMPLES:
    >>> test_temp_text = 'python def foo(bar): # function body'
    >>> identify_language(test_temp_text)
    ('python', 'def foo(bar): # function body')

    >>> test_temp_text = '# python def foo(bar): # function body'
    >>> identify_language(test_temp_text)
    ('python', 'def foo(bar): # function body')

    >>> test_temp_text = 'def foo(bar): # function body'
    >>> identify_language(test_temp_text)
    ('', 'def foo(bar): # function body')


    Preconditions:
        - text was in a verbatim environment
    """
    if verb_plugin not in ('minted', 'lstlisting'):
        return '', text

    lang_list = {'minted': MINTED_LANGUAGES, 'lstlisting': LISTING_LANGUAGES}[verb_plugin]

    text = text.strip()
    hold = text
    comment_chars = ('//', '--')
    if text.startswith(comment_chars):
        text = text[2:].strip()
    elif text.startswith('#'):
        text = text[1:].strip()
    next_nl = text.find('\n')
    if ALLOW_SPACES_IN_LANGUAGES:
        next_space = text.find(' ')
    else:
        next_space = -1
    if next_nl == -1 and next_space == -1:
        return '', hold
    elif next_nl != 1 and next_space == -1:
        breaker = next_nl
    elif next_nl == -1 and next_space != -1:
        breaker = next_space
    else:
        breaker = min(next_nl, next_space)
    text, language = text[breaker + 1:].strip('\n'), text[:breaker].strip().lower()
    if language in [x.lower() for x in lang_list]:
        if language == 'ts':
            language = 'js'  # swap the language
        return language, text
    else:
        return '', hold


def count_outer(text: str, key: str, avoid_escape_char: bool = True) -> int:
    """Like in, but only checks outside matrices and text.
    Meant for equations.
    """
    all_matrices = ['matrix', 'bmatrix', 'pmatrix']
    for m_mode in all_matrices:
        text = modify_text_in_environment(text, m_mode, lambda s: '')
    # text = do_something_to_local_env(text, 'text', lambda s: '')
    if len(key) == 1 and avoid_escape_char:
        text = text.replace(f'\\{key}', '')
    return text.count(key)


def count_matrix_size(matrix: str) -> tuple[int, int]:
    """Count the size of the matrix. Do not count the size
    of any matrices inside.

    Return in the format of n - 1, m - 1.
    """
    a_cms = count_outer(matrix, '&')
    b_cms = count_outer(matrix, '\\\\')
    return b_cms, a_cms


TEST_STR_2 = r"""
\begin{matrix}
ccc
\begin{matrix}
&&&&&&&\\\\\\\&&|&|&|
\end{matrix}
\#(no. 1)
\end{matrix}
""".strip()

TEST_STR_3 = """
\\begin{matrix}
42 + 534r\\#(67) \\\\
\\end{matrix}
""".strip()


def valid_matrix(matrix: str) -> bool:
    """Check if the matrix happens to be one used for
    the hashtag. Input to matrix is always stripped before
    checking.

    The matrix must have its begin and end keywords.

    A matrix is valid if:
        - not a bracket or para matrix
        - it's 1x1
        - has only one visible # inside it, that isn't nested

    >>> valid_matrix(TEST_STR_2)
    True
    """
    matrix = matrix.strip()
    all_matrices = ['\\begin{matrix}']  # I know, only one loop iteration
    started_with = ''
    for am in all_matrices:
        if matrix.startswith(am):
            started_with = am
    if started_with == '':
        return False
    matrix = matrix[len(started_with):len(matrix) - len(started_with) + 2]
    cms = count_matrix_size(matrix)
    if cms != (1, 0):  # not all(ti == 0 for ti in cms):
        return False
    hashtag = '\\#'
    cms2 = count_outer(matrix, hashtag, False)
    return cms2 == 1


FI = R'\text{because }x+4=9 \text{, this is true.} 9 + 10 = 21'
FI2 = R'(4.3)'


def equation_to_regular_text_unused(text: str) -> str:
    """Input: text seen in an equation.
    Output: text seen NOT in an equation.

    # >>> equation_to_regular_text(FI)
    'because \\(x+4=9\\) , this is true.'
    """
    # special case: string only has (, ), ., whitespaces, and any number
    set_string = {st for st in text}
    temp_allowed_chars = {st for st in '[]().0123456789'}
    if set_string.issubset(temp_allowed_chars):
        # print('fast time')
        return text
    # approach: like an AST, but using lists
    # [text, True], where True means equation and False means regular text
    # we will use bracket layering here:
    # \text regions can only be marked if for all characters
    # in \text, the bracket layer of the declaration is zero
    tx_env = '\\text{'
    list_so_far = []
    while True:
        clv = find_closest_local_env(text, 'text')
        if clv != -1:
            before = text[:clv]
            end = local_env_end(text, clv)
            after = text[clv + len(tx_env):end]
            text = text[end + 1:]
            if len(before) == 0 or all(bf == ' ' for bf in before):
                list_so_far.append([after, False])
            else:
                list_so_far.extend([[before, True], [after, False]])
        else:
            if not (len(text) == 0 or all(bf == ' ' for bf in text)):
                list_so_far.append([text, True])
            break
    # assuming this works:
    new_str = ''
    for i, item in enumerate(list_so_far):
        if item[1]:  # equation
            new_str += f'\\({item[0].strip()}\\)'
        else:  # regular text
            stripped = item[0].strip()
            if stripped[0] not in {',', '.', '?', ')'} and i != 0:
                stripped = ' ' + stripped
            if stripped[-1] != '(':
                stripped = stripped + ' '
            new_str += stripped
    return new_str.strip()


def find_closest_local_env(text: str, env: str, skip: int = 0) -> int:
    """Return the index of the closest local environment,
    that isn't nested with any other local environment.

    Skip should be 0 if we're looking for the closest local env.

    Preconditions:
        - skip >= 0

    Return -1 on failure.
    """
    env_str = '\\' + env + '{'
    n = 1
    while True:
        ind = find_nth(text, env_str, n)
        if ind == -1:
            return -1
        if environment_layer(text, ind):
            n += 1
            continue
        else:
            if skip > 0:
                skip -= 1
                n += 1
                continue
            else:
                return ind


def environment_layer(text: str, index: int) -> bool:
    """Return whether text at index is inside an environment.

    Using find and rfind at index.
    """
    bg = R'\begin{'
    en = R'\end{'
    next_end = text.find(en, index)  # -1 if fail
    next_begin = text.find(bg, index)  # big if fail
    # previous_begin = text.rfind(bg, index)  # big if fail
    # previous_end = text.rfind(en, index)  # -1 if fail

    if next_end == -1:
        return False
    elif next_end > next_begin:
        return False
    else:  # only the case where the next end is before the next begin
        return True


def environment_depth(text: str, index: int, env: Optional[str] = None) -> int:
    """Return how deep text is in an environment at index.
    If index is in the middle of an environment declaration, assume
    that declaration does not exist.

    If env is not stated, then this applies for all environments.
    """

    if env is not None:
        be = R'\begin{' + env + '}'
        en = R'\end{' + env + '}'
    else:
        be = R'\begin{'
        en = R'\end{'
    ti = text[:index]
    begins = ti.count(be)
    ends = ti.count(en)
    return begins - ends


def find_env_name_begin(text: str, index: int) -> str:
    """Find the name of the environment, based on
    the index of the backslash of backslash begin.
    """
    begin = '\\begin{'
    assert text.startswith(begin, index)
    index_env_start = index + len(begin)
    index_env_end = local_env_end(text, index)
    return text[index_env_start:index_env_end]


def check_same_environment(text: str, index_1: int, index_2: int) -> bool:
    """Return true if index_1 is in the same environment as index_2.

    Preconditions:
        - index_1 and index_2 are both not part of any environment declarations
    """
    starting_index = min(index_1, index_2)
    begin = '\\begin{'
    closest_begin = text.rfind(begin, 0, starting_index)
    if closest_begin == -1:
        # index 1 and index 2 must have an environment depth of 0
        return environment_depth(text, index_1) == 0 and environment_depth(text, index_2) == 0
    else:
        env_name = find_env_name_begin(text, closest_begin)
        proposed_env_end = find_env_end(text, closest_begin, env_name)

        condition_1 = closest_begin < index_1 < proposed_env_end and closest_begin < index_2 < proposed_env_end
        condition_2 = environment_depth(text, index_1) == environment_depth(text, index_2) == 0
        return condition_1 and condition_2


def verbatim_regular_quotes(text: str) -> str:
    """Remove weird quotes from verbatim environments.
    """
    text = modify_text_in_environment(text, 'verbatim', lambda s: s.replace('‘', "'").replace('’', "'"))
    return text


def framed(text: str) -> str:
    """Frame all 1x1 tables.
    Ran before long table environment and proofs.
    """
    skip = 1
    while True:
        lt_index = find_nth(text, R'\begin{longtable}', skip)
        env_d = environment_depth(text, lt_index, 'longtable')
        # forbid_env_tolerance = {'longtable': 2 + env_d}
        if lt_index == -1:
            break  # break if we can't find a starting longtable
        # lt_end_index = find_nth(text, R'\end{longtable}', 1, lt_index)
        lt_end_index = find_env_end(text, lt_index, 'longtable')
        if lt_end_index == -1:
            break
        # we now have the contents of the longtable, represented by
        # text[lt_index:lt_end_index + len(R'\end{longtable}')]

        left_border = '\\begin{minipage}[b]{\\linewidth}\\raggedright\n'
        # right_border = '\\end{minipage}'
        left_index_border = find_nth(text, left_border, 1, lt_index) + len(left_border)
        # right_index_border = find_nth(text, right_border, 1, lt_index)
        right_index_border = find_env_end(text, left_index_border, 'minipage')
        if right_index_border == -1:
            skip += 1
            continue
            # pass
            # assert False  # never supposed to happen here
        cur_header = text[left_index_border:right_index_border].strip()
        # This must be in the name of the environment
        # if cur_header.lower() != env.lower():
        #     skip += 1  # skip if the header isn't the environment we look for
        #     continue
        # check if this table is only one wide:
        if not text[right_index_border:].startswith('\\end{minipage} \\\\\n\\midrule()\n\\endhead\n\\bottomrule()'
                                                    '\n\\end{longtable}'):
            skip += 1
            continue  # if it is not one wide, then this is the wrong table
        # from this point, assume our table is one wide and only has 3 rows
        # table_content_start = text.find(R'\endhead', right_index_border) + len(R'\endhead')
        else:
            text = text[:lt_index] + '\\begin{framed}\n\n' + cur_header + '\n\n\\end{framed}\n\n' + \
                   text[lt_end_index + len('\\end{longtable}'):]
    return text


def longtable_environment(text: str, env: str, env_info: LatexEnvironment) -> str:
    """Looks for all 3x1 long tables for an environment and converts them.
    All format on these tables must be clear. The first row is the
    name of the environment, which is not case-sensitive.
    The second row is the name of the term, which is case-sensitive.
    The third row is the contents of the environment, which
    one may do anything they want. Even lists are allowed there.
    """
    # assert env == env_info.env_name
    env_alias = env_info.start_alt
    forbid_envs = ['matrix', 'bmatrix', 'pmatrix', 'minipage', 'align*', 'longtable']
    # forbid_env_tolerance = {'longtable': 2}
    skip = 1
    while True:
        lt_index = find_nth(text, R'\begin{longtable}', skip)
        env_d = environment_depth(text, lt_index, 'longtable')
        forbid_env_tolerance = {'longtable': 2 + env_d}
        if lt_index == -1:
            break  # break if we can't find a starting longtable
        # lt_end_index = find_nth(text, R'\end{longtable}', 1, lt_index)
        lt_end_index = find_env_end(text, lt_index, 'longtable')
        if lt_end_index == -1:
            break
        # we now have the contents of the longtable, represented by
        # text[lt_index:lt_end_index + len(R'\end{longtable}')]

        left_border = '\\begin{minipage}[b]{\\linewidth}\\raggedright\n'
        # right_border = '\\end{minipage}'
        left_index_border = find_nth(text, left_border, 1, lt_index) + len(left_border)
        # right_index_border = find_nth(text, right_border, 1, lt_index)
        right_index_border = find_env_end(text, left_index_border, 'minipage')
        if right_index_border == -1:
            skip += 1
            continue
            # pass
            # assert False  # never supposed to happen here
        cur_header = text[left_index_border:right_index_border].strip()
        # This must be in the name of the environment
        if cur_header.lower().strip().strip('.') not in [env_alias.lower(), '\\textbf{' + env_alias.lower() + '}',
                                                         '\\emph{' + env_alias.lower() + '}']:
            skip += 1  # skip if the header isn't the environment we look for
            continue
        # check if this table is only one wide:
        if not text[right_index_border:].startswith(R'\end{minipage} \\'):
            skip += 1
            continue  # if it is not one wide, then this is the wrong table
        # from this point, assume our table is one wide and only has 3 rows
        # table_content_start = text.find(R'\endhead', right_index_border) + len(R'\endhead')

        table_content_start = find_not_in_environment_tolerance(text, R'\endhead', forbid_env_tolerance,
                                                                right_index_border) + len(R'\endhead')
        table_content_end = find_not_in_environment_tolerance(text, R'\bottomrule()', forbid_env_tolerance,
                                                              right_index_border)
        # table_content_end = text.find(R'\bottomrule', right_index_border)
        if table_content_start == -1 or table_content_end == -1:
            assert False  # never supposed to happen
        table_contents = text[table_content_start:table_content_end]
        table_rows = str_split_not_in_env(table_contents, R'\\', forbid_envs)
        table_rows = [minipage_remover(trrr) for trrr in table_rows]
        if len(table_rows) == 2:
            brack = '{}' if env_info.extra_args_type == 'brace' else '[]'
            if env_info.extra_args_type == 'brace' or env_info.env_middlefix == '':
                extra_args = brack[0] + table_rows[0] + brack[1]
            else:
                extra_args = ''
            middle_fix = env_info.env_middlefix if env_info.env_middlefix != '[EMPTY]' else ''
            env_starter = R'\begin{' + env.lower() + '}' + middle_fix + extra_args + env_info.env_suffix + '\n\n'
            total_env_contents = env_starter + force_not_inline(table_rows[1]) + '\n' + R'\end{' + env.lower() + '}'
            text = text[:lt_index] + total_env_contents + text[lt_end_index + len(R'\end{longtable}'):]
        # if len(table_rows) == 2
        elif len(table_rows) == 1:
            forced_brace = '{}' if env_info.extra_args_type == 'brace' else ''
            middle_fix = env_info.env_middlefix if env_info.env_middlefix != '[EMPTY]' else ''
            env_starter = R'\begin{' + env.lower() + '}' + middle_fix + forced_brace + '\n\n'
            total_env_contents = env_starter + force_not_inline(table_rows[0]) + '\n' + R'\end{' + env.lower() + '}'
            text = text[:lt_index] + total_env_contents + text[lt_end_index + len(R'\end{longtable}'):]
        else:
            skip += 1
            continue
    return text


TEST_ENV_STR = r"""
This is \\
not again \\
please \\
\begin{matrix}
4 \\
2 \\
3 \end{matrix}
please
"""

TEST_ENV_STR_2 = r"""
\begin{minipage}[b]{\linewidth}\raggedright
Theorem
\end{minipage}
"""


def minipage_remover(text: str) -> str:
    """If the text is wrapped with minipages, remove them.

    >>> minipage_remover(TEST_ENV_STR_2)
    'Theorem'
    """
    mp_1 = R'\begin{minipage}[t]{\linewidth}\raggedright'
    mp_11 = R'\begin{minipage}[b]{\linewidth}\raggedright'
    mp_2 = R'\end{minipage}'
    text = text.strip()
    if (text.startswith(mp_1) or text.startswith(mp_11)) and text.endswith(mp_2):
        return text[len(mp_1):len(text) - len(mp_2)].strip()
    else:
        return text  # just the generic text otherwise.


def str_split_not_in_env(text: str, sep: str, env: Union[str, list[str]]) -> list[str]:
    """Similar to str.split(), but prevent splitting things inside
    the specified environment.
    """
    lst_so_far = []
    curr_index = -len(sep)  # index of the last sep.
    while True:
        prev_index = curr_index + len(sep)  # the char after sep
        curr_index = find_not_in_environment(text, sep, env, curr_index + len(sep))  # char at sep
        if curr_index == -1:
            if not lst_so_far:
                prev_index = 0
            last_part = text[prev_index:curr_index]
            if len(last_part) != 0:
                lst_so_far.append(text[prev_index:curr_index])
            break
        lst_so_far.append(text[prev_index:curr_index])
    return lst_so_far


LINELESS_TEST = r"""

Content of theorem

\({9 + 10 = 21
}{4 + 2 = 48
}{7 + 33 = 68
}{8 + 293 = 49
}\begin{matrix}
43 & 32 \\
34 & 54 \\
\end{matrix}\)

Unfortunat

"""


def force_not_inline(text: str) -> str:
    """Forces inline but not inline equations to no longer be inline.
    This is often caused by putting equations in tables.
    """
    i_start = '\\('
    i_end = '\\)'
    p_start = '\\['
    p_end = '\\]'
    skip = 1
    while True:
        st = find_nth(text, i_start, skip)
        en = find_nth(text, i_end, skip)
        if st == -1 or en == -1:
            break
        assert st < en
        if (text[st - 2:st] == '\n\n' or len(text[st - 2:st]) != 2) and (text[en + 2:en + 4] == '\n\n' or len(
                text[en + 2: en + 4]) != 2):  # if both detected () are newline-wrapped
            text = text[:st] + p_start + text[st + 2:en] + p_end + text[en + 2:]
        else:
            skip += 1
    return text


def aug_matrix_spacing(text: str) -> str:
    """Spaces all augmented matrices.
    """
    old = R'\end{matrix}\mid\begin{matrix}'
    new = R'\end{matrix}\;\middle|\;\begin{matrix}'
    return text.replace(old, new)


T_STR_07 = r"""\begin{matrix}
\begin{matrix}
\end{matrix}
aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
\end{matrix}
NO MORE
"""


def find_env_start(text: str, index: int, env: Optional[str] = None) -> int:
    """Find where the environment starts.
    Index should be located somewhere inside the environment.

    Return -1 on failure, that is, if index happens to not be in an environment.
    """
    # skip = 1
    skip_st = 1
    skip_en = 1
    if env is not None:
        env_st = R'\begin{' + env + '}'
        env_en = R'\end{' + env + '}'
    else:
        env_st = R'\begin{'
        env_en = R'\end{'
    while True:
        t_st = rfind_nth(text, env_st, skip_st, 0, index)  # -1 if -1
        t_en = rfind_nth(text, env_en, skip_en, 0, index)  # big if -1
        if t_en == -1 and t_st == -1:
            # could not find any environment beforehand
            return -1
        elif t_en == -1:
            t_en = len(text)
        if t_st < t_en <= index:
            skip_st += 1
            skip_en += 1
            continue
        else:
            # if t_en < t_st, or t_st is later
            return t_st


def find_env_end(text: str, index: int, env: Optional[str] = None) -> int:
    """Find where the environment ends. Helps
    bypass nesting.

    Index should be located somewhere inside the environment.
    It should be positioned at the backslash of where the environment is declared.

    Return where the backslash occurs on the environment end.
    Return -1 on failure.
    """
    skip = 1
    index += 1
    skip_st = 1
    skip_en = 1
    if env is not None:
        env_st = R'\begin{' + env + '}'
        env_en = R'\end{' + env + '}'
    else:
        env_st = R'\begin{'
        env_en = R'\end{'
    while True:
        t_st = find_nth(text, env_st, skip_st, index)  # big if -1
        t_en = find_nth(text, env_en, skip_en, index)  # -1 if -1
        if t_st == -1:
            t_st = len(text) + 100
        if t_en == -1:
            return -1
        if t_st < t_en:
            skip_st += 1
            skip_en += 1
            continue
        else:
            if skip > 1:
                skip_st += 1
                skip_en += 1
                skip -= 1
                continue
            else:
                return t_en


def modify_equations(text: str, func: Callable[[str], str], inline: bool = False) -> str:
    """Modifies all equations, but only inline or not inline, depending on what
    argument was passed into that parameter.

    This should be placed before alignment regions are processed.

    Preconditions:
        - Backslash square brackets are only used to define equations.
        - All verbatim environments are concealed.
    """
    eqs = '\\[' if not inline else '\\('
    eqen = '\\]' if not inline else '\\)'
    skip = 1
    while True:
        st = find_nth(text, eqs, skip)  # the backslash of equation start
        stt = st + len(eqs)  # the character after \[_ (the underscore)
        en = find_nth(text, eqen, skip)  # the backslash of equation end
        if st == -1 or en == -1:
            break
        eq_contents = text[stt:en]
        new_eq_contents = func(eq_contents)
        text = text[:stt] + new_eq_contents + text[en:]
        skip += 1
    return text


def blacksquare_detector(text: str) -> str:
    """Looks through all inline and non-inline equations and kicks out any
    black squares, changing them to proof finishers.
    """
    eq_array = (('\\[', '\\]'), ('\\(', '\\)'))
    for wrapper_brackets in eq_array:
        eqs = wrapper_brackets[0]  # '\\[' if not inline else '\\('
        eqen = wrapper_brackets[1]  # '\\]' if not inline else '\\)'
        skip = 1
        while True:
            dontskip = False
            st = find_nth(text, eqs, skip)  # the backslash of equation start
            stt = st + len(eqs)  # the character after \[_ (the underscore)
            en = find_nth(text, eqen, skip)  # the backslash of equation end
            if st == -1 or en == -1:
                break
            eq_contents = text[stt:en]
            if '\\blacksquare' in eq_contents:
                eq_contents = eq_contents.replace('\\blacksquare', '')
                # if the leftovers of the equation is empty, apart from whitespaces or newlines,
                # then get rid of the equation entirely
                if eq_contents.replace(' ', '').replace('\n', '') == '':
                    text = text[:st] + '\\end{proof}' + text[en + len(eqen):]
                    dontskip = True
                else:
                    text = text[:stt] + eq_contents + eqen + '\n\\end{proof}' + text[en + len(eqen):]
            # new_eq_contents = func(eq_contents)
            # text = text[:stt] + new_eq_contents + text[en:]
            # otherwise, do nothing
            if not dontskip:
                skip += 1
    return text


def blacksquare_detector_single(text: str, index: int) -> tuple[str, int]:
    """Same as blacksquare_detector(), but only searches once,
    from the index. It will never search past the next section.

    Return: new text AND the index after end proof

    If no blacksquare is found, then insert a blacksquare at the index end.

    is located in, then take it out.
    This must be run before any equation processing is done.
    """
    # the only way a blacksquare can POSSIBLY APPEAR is because it's in an
    # equation. Not even verbatim environments can mess this up.
    nearest_blacksquare = find_in_same_environment(text, '\\blacksquare', index)
    if nearest_blacksquare == -1:
        nearest_blacksquare = len(text) + 100
    end_of_environment = find_env_end(text, index)
    next_section = find_next_section(text, index)

    end_proof_temp_2 = '\n\\end{proof}\n'
    end_proof_temp = '\n\\end{proof}'

    # the next section is earlier than the next blacksquare, and blacksquare not in environment
    if (nearest_blacksquare > end_of_environment != -1) or nearest_blacksquare > next_section:
        if next_section < nearest_blacksquare and (end_of_environment == -1 or next_section < end_of_environment):
            # if next section is
            # earlier than blacksquare
            # and earlier than the end of the closest environment
            text = text[:next_section] + end_proof_temp_2 + text[next_section:]
            return text, next_section + len(end_proof_temp_2)  # index after end proof
        else:
            text = text[:end_of_environment] + end_proof_temp_2 + text[end_of_environment:]
            return text, end_of_environment + len(end_proof_temp_2)
    para_end = find_fallback(text, '\\)', nearest_blacksquare)
    bracket_end = find_fallback(text, '\\]', nearest_blacksquare)
    if para_end < bracket_end:
        starter_bracket = '\\('
        bracket_finisher = para_end
    else:
        starter_bracket = '\\['
        bracket_finisher = bracket_end
    assert para_end != bracket_end
    starter_location = text.rfind(starter_bracket, 0, nearest_blacksquare)
    assert starter_location != -1
    equation_contents = text[starter_location + 2:bracket_finisher]
    equation_contents = equation_contents.replace('\\blacksquare', '')
    if equation_contents.replace(' ', '') == '':
        text = text[:starter_location] + end_proof_temp + text[bracket_finisher + 2:]
        proof_ends = starter_location + len(end_proof_temp)
    else:
        text = text[:starter_location + 2] + equation_contents + \
               text[bracket_finisher:bracket_finisher + 2] + end_proof_temp + text[bracket_finisher + 2:]
        proof_ends = starter_location + 2 + len(equation_contents) + 2 + len(end_proof_temp)
    return text, proof_ends


SUB_TEXT = r"""
one two three four
\begin{env}
five six
\end{env}
seven eight
five six
"""


def find_in_same_environment(text: str, sub: str, start: int, skip: int = 1) -> int:
    """Find sub in the same environment as start.

    Return -1 on failure.
    """
    env_start = find_env_start(text, start)
    env_end = find_env_end(text, start)
    # both are -1, or both are not -1
    assert (env_start == -1) == (env_end == -1)
    if (env_start == -1) and (env_end == -1):
        # if the environment depth happens to be 0
        return find_not_in_any_env_tolerance(text, sub, start, 1, skip)
    else:
        env_true_start = local_env_end(text, env_start) + 1
        # candidate_index = find_nth(text, sub, skip, env_start, env_end)
        text_in_environment = text[env_true_start:env_end]
        # candidate_index_text_in_environment = candidate_index - env_true_start
        temp_index = find_not_in_any_env_tolerance(text_in_environment, sub, start - env_true_start, 1, skip)
        if temp_index != -1:
            temp_index += env_true_start
        return temp_index


def fix_accents(text: str) -> str:
    """Fix accents causing problems.
    """
    # Underbrace
    skip = 1
    while True:
        # pattern:
        # \overset{above}{︸}
        overset_ind = find_nth(text, '\\overset', skip)
        if overset_ind == -1:
            break
        overset_end = local_env_end(text, overset_ind)
        contents = text[overset_ind + len('\\overset') + 1:overset_end]
        if text[overset_end:overset_end + 5] == '}{︸}}':
            text = text[:overset_ind] + '\\underbrace{' + contents + '}}' + text[overset_end + 5:]
        else:
            skip += 1

    # weird left arrow
    text = text.replace(R'\overset{⃐}', R'\mathbf')
    # print(x)

    # overleftrightarrow
    skip = 1
    while True:
        over_lra = '\\overleftrightarrow{}}{'
        os_ind = find_nth(text, '\\overset{', skip)
        if os_ind == -1:
            break
        os_ind_after = os_ind + len('\\overset{')
        if text[os_ind_after:os_ind_after + len(over_lra)] == '\\overleftrightarrow{}}{':
            ending = find_next_closing_bracket(text, os_ind_after + len(over_lra))
            assert ending != -1
            contents = text[os_ind_after + len(over_lra):ending]
            text = text[:os_ind] + '\\overleftrightarrow{' + contents + text[ending:]
        else:
            skip += 1
    return text


def find_next_closing_bracket(text: str, index: int) -> int:
    """Find the next closing bracket.
    Preconditions:
        - text[index] != '{' or text[index] != '}'

    Return -1 on failure.

    >>> test_text = 'this{}{}{}{}{}{}}'
    >>> find_next_closing_bracket(test_text, 0) == len(test_text) - 1
    True

    """
    skip = 1
    while True:
        ind = find_nth(text, '}', skip, index)
        if ind == -1:
            return -1
        if text[ind - 1] == '\\':
            skip += 1
            continue
        if bracket_layers(text, ind, starting_index=index) != -1:
            skip += 1
            continue
        else:
            return ind


SAMPL = r"""
blblbllblblblblb\env{blblblbl}blblbl\begin{blbl}blblblb\end{blblbl}blblbl\(blblb\)blblbl
"""


# modify_text_not_in_environments(SAMPL, lambda x: x.upper())


def modify_text_not_in_environments(text: str, key: Callable[[str], str]) -> str:
    """Apply a key to modify a string. Will not attempt to modify anything
    inside any environments.

    This is done by breaking up each segment into lists. This means the following
    will not be affected:
        - begin/end environments
        - local environments
        - equations

    Preconditions:
        - verbatim is concealed
        - environments are set up in a way such that latex won't cry
    """
    forbidden_regions: list[tuple] = []
    # layers = 0
    cur_pos = 0
    # mode = ''
    # assert mode in {'', 'local', 'begin', 'inline', 'equation'}

    # the pattern for local is:
    # \___{
    # patterns
    begin_st, begin_en = '\\begin{', '\\end{'
    inline_st, inline_en = '\\(', '\\)'
    equation_st, equation_en = '\\[', '\\]'
    while True:
        begin_ind = find_fallback(text, begin_st, cur_pos)
        inline_ind = find_fallback(text, inline_st, cur_pos)
        equation_ind = find_fallback(text, equation_st, cur_pos)
        local_ind = nearest_local_env(text, cur_pos)
        if local_ind == -1:
            local_ind = len(text)
        elif local_ind == begin_ind:
            local_ind = begin_ind + 1  # prevents conflicts, as \begin{} is caught
        assert local_ind <= len(text)
        # detect which one is the lowest
        starters = [begin_ind, inline_ind, equation_ind, local_ind]
        starter_index = min(starters)
        # check if lowest is unique
        num_starters = starters.count(starter_index)
        if num_starters > 1:
            break
        # by this point, we know that the starter is unique
        # and no error would occur here
        starter_map = ['begin', 'inline', 'equation', 'local']
        type_of_starter = starter_map[starters.index(starter_index)]
        if type_of_starter == 'begin':
            finish = text.find(begin_en, starter_index)
            end_of_env = local_env_end(text, finish) + 1
            # [starter_index:end_of_env] would capture the environment
            # otherwise, it won't be captured
        elif type_of_starter == 'inline':
            end_of_env = text.find(inline_en, starter_index) + len(inline_en)
        elif type_of_starter == 'equation':
            end_of_env = text.find(equation_en, starter_index) + len(inline_en)
        elif type_of_starter == 'local':
            end_of_env = local_env_end(text, starter_index) + 1
            if end_of_env == 0:
                logging.warning('runaway argument on command')
                assert False  # something wrong happened
        else:
            assert False  # impossible to reach this branch
        # prior = text[:starter_index]
        # within = text[starter_index:end_of_env]
        # after = text[end_of_env:]
        assert starter_index < end_of_env
        forbidden_bounds = (starter_index, end_of_env)
        forbidden_regions.append(forbidden_bounds)
        cur_pos = end_of_env  # cur pos is updated to the end of the environment,
        # the character after the end of the environment we checked

    # checking forbidden_regions:
    split_text: list[str] = []  # always alternating between change and stay, starting from change
    prev_region_end = 0
    if len(forbidden_regions) == 0:
        return key(text)
    else:
        for region in forbidden_regions:
            split_text.append(text[prev_region_end:region[0]])
            split_text.append(text[region[0]:region[1]])
            prev_region_end = region[1]
        new_str_list = []
        for i, txt in enumerate(split_text):
            if i % 2 == 0:  # is even, meaning change
                new_str_list.append(key(txt))
            else:
                new_str_list.append(txt)
        new_str_list.append(key(text[prev_region_end:]))
        return ''.join(new_str_list)


def find_fallback(text: str, sub: str, start: Optional[int] = None, end: Optional[int] = None) -> int:
    """Similar to text.find(), but return len(text) on failure.
    """
    if start is not None and end is not None:
        location = text.find(sub, start, end)
    elif start is None and end is not None:
        location = text.find(sub, __end=end)
    elif start is not None and end is None:
        location = text.find(sub, start)
    else:
        location = text.find(sub)

    if location == -1:
        return len(text)
    else:
        return location


LC_ENV_STR = r"""C\tb{abcd}efgh\tb{ijklmn}"""


def nearest_local_env(text: str, start: int = 0) -> int:
    """Find the nearest location of the next local environment,
    A.K.A. LaTeX command.

    Return -1 on failure.
    """
    skip = 1
    while True:
        nearest_backslash = find_nth(text, '\\', skip, start)
        if nearest_backslash == -1:
            return -1
        if not nearest_backslash == 0 and text[nearest_backslash - 1] == '\\':
            # skip case 1: the character behind is also a backslash
            skip += 1
            continue
        # now, check if opening brace comes before the next space
        next_brace = find_fallback(text, '{', nearest_backslash)
        next_space = find_fallback(text, ' ', nearest_backslash)
        if next_brace > next_space:
            skip += 1
            continue
        elif next_brace < next_space:
            ending = local_env_end(text, next_brace)
            if ending == -1:
                raise IndexError  # The command never ended
            else:
                return nearest_backslash
        else:
            # this can only occur if the program cannot find the next { or space.
            skip += 1
            continue


def modify_text_not_in_environments_encrypted(text: str, key: Callable[[str], str]) -> str:
    """Encrypts texts similar to how it is done in verb environments.

    Apply a key to modify a string. Will not attempt to modify anything
    inside any environments.

    This is done by breaking up each segment into lists. This means the following
    will not be affected:
        - begin/end environments
        - local environments
        - equations

    Preconditions:
        - verbatim is concealed
        - environments are set up in a way such that latex won't cry
    """
    forbidden_regions: list[tuple] = []
    # layers = 0
    cur_pos = 0
    # mode = ''
    # assert mode in {'', 'local', 'begin', 'inline', 'equation'}

    # the pattern for local is:
    # \___{
    # patterns
    begin_st, begin_en = '\\begin{', '\\end{'
    inline_st, inline_en = '\\(', '\\)'
    equation_st, equation_en = '\\[', '\\]'
    while True:
        begin_ind = find_fallback(text, begin_st, cur_pos)
        inline_ind = find_fallback(text, inline_st, cur_pos)
        equation_ind = find_fallback(text, equation_st, cur_pos)
        local_ind = nearest_local_env(text, cur_pos)
        if local_ind == -1:
            local_ind = len(text)
        elif local_ind == begin_ind:
            local_ind = begin_ind + 1  # prevents conflicts, as \begin{} is caught
        assert local_ind <= len(text)
        # detect which one is the lowest
        starters = [begin_ind, inline_ind, equation_ind, local_ind]
        starter_index = min(starters)
        # check if lowest is unique
        num_starters = starters.count(starter_index)
        if num_starters > 1:
            break
        # by this point, we know that the starter is unique
        # and no error would occur here
        starter_map = ['begin', 'inline', 'equation', 'local']
        type_of_starter = starter_map[starters.index(starter_index)]
        if type_of_starter == 'begin':
            finish = text.find(begin_en, starter_index)
            end_of_env = local_env_end(text, finish) + 1
            # [starter_index:end_of_env] would capture the environment
            # otherwise, it won't be captured
        elif type_of_starter == 'inline':
            end_of_env = text.find(inline_en, starter_index) + len(inline_en)
        elif type_of_starter == 'equation':
            end_of_env = text.find(equation_en, starter_index) + len(inline_en)
        elif type_of_starter == 'local':
            end_of_env = local_env_end(text, starter_index) + 1
            if end_of_env == 0:
                logging.warning('runaway argument on command')
                assert False  # something wrong happened
        else:
            assert False  # impossible to reach this branch
        # prior = text[:starter_index]
        # within = text[starter_index:end_of_env]
        # after = text[end_of_env:]
        assert starter_index < end_of_env
        forbidden_bounds = (starter_index, end_of_env)
        forbidden_regions.append(forbidden_bounds)
        cur_pos = end_of_env  # cur pos is updated to the end of the environment,
        # the character after the end of the environment we checked

    # checking forbidden_regions:
    split_text: list[str] = []  # always alternating between change and stay, starting from change
    prev_region_end = 0
    if len(forbidden_regions) == 0:
        return key(text)
    else:
        encrypted = {}
        for region in forbidden_regions:
            split_text.append(text[prev_region_end:region[0]])
            split_text.append(text[region[0]:region[1]])
            prev_region_end = region[1]
        new_str_list = []
        for i, txt in enumerate(split_text):
            if i % 2 == 0:  # is even, meaning change
                new_str_list.append(txt)
            else:
                encrypt_key = text_environment_encryptor(i)
                encrypted[encrypt_key] = txt
                new_str_list.append(encrypt_key)
        nst = ''.join(new_str_list)
        nst = key(nst)
        for k, v in encrypted.items():
            nst = nst.replace(k, v)
        # new_str_list.append(key(text[prev_region_end:]))
        return nst


def text_environment_encryptor(count: int) -> str:
    """This was a list of t-env encryptors, but
    we wouldn't list everything

    Preconditions:
        - count >= 0
    """
    return f'🬟{count}⚍⚋🬯⚎☆⚌⚏'


def formatted_text_encryptor(text: str, envs_to_encrypt: list[str]) -> str:
    """Hide local environment declarations. There will be a decrypt function.
    """
    env_st = ['🮥sT1🮥' + z + '🮥sT2🮥' for z in envs_to_encrypt]
    env_en = '🮥eN1🮥'
    for env, env_st_kw in zip(envs_to_encrypt, env_st):
        env_bg = '\\' + env + '{'
        while True:
            st_ind = text.find(env_bg)
            if st_ind == -1:
                break
            en_ind = local_env_end(text, st_ind)
            text = text[:st_ind] + env_st_kw + text[st_ind + len(env_bg):en_ind] + env_en + text[en_ind + 1:]
    return text


def formatted_text_decryptor(text: str, envs_to_decrypt: list[str]) -> str:
    """Ran after formatted_text_encryptor.
    """
    env_st = ['🮥sT1🮥' + z + '🮥sT2🮥' for z in envs_to_decrypt]
    env_en = '🮥eN1🮥'
    text = text.replace(env_en, '}')
    for env, env_st_kw in zip(envs_to_decrypt, env_st):
        env_bg = '\\' + env + '{'
        text = text.replace(env_st_kw, env_bg)
    return text


def check_bibtex(preamble: str, replace_bibtex: str) -> str:
    """Overwrite the preamble's bibtex thing. Firstly, check
    if bibtex is defined. If so, then remove it.
    """
    btex = 'biblatex'
    skip = 1
    while True:
        closest_package = find_closest_local_env(preamble, 'usepackage', skip)
        if closest_package == -1:  # base case
            return preamble + replace_bibtex
        # start_of_brace = find_no_escape_char(preamble, '{', 1, closest_package)  # preamble.find('{', closest_package)
        package_end = local_env_end(preamble, closest_package)
        preamble_contents = preamble[closest_package:package_end]  # I don't care otherwise
        if btex in preamble_contents:  # oop, try again
            return preamble[:closest_package] + replace_bibtex + preamble[package_end + 1:]


def find_no_escape_char(text: str, sub: str, skip: int = 1, start: int = 0) -> int:
    """Same as find_nth, but prevents looking at escape characters.
    """
    private_skip = 1
    while True:
        candidate_location = find_nth(text, sub, skip, start)
        if candidate_location == -1:
            return -1
        temp_state = text[candidate_location - 1] == '\\' if len(text) != 0 else False
        if temp_state:
            private_skip += 1
            continue
        else:
            skip -= 1
            if skip == 0:
                return candidate_location
            else:
                private_skip += 1
    # return candidate_location


def find_no_escape_char_first(text: str, sub: str, start: int = 0) -> int:
    """Very similar to str.find. Return -1 on failure.
    Parameters
    ----------
    text
        the text to search.
    sub
        the substring to find.
    start
        the index to start searching.

    Returns
    -------
        the index at the first occurrence of the substring, ignoring
        instances where a backslash is put before the substring.
    """
    skip = 1
    while True:
        candidate_index = find_nth(text, sub, skip, start)
        # assert 0 <= candidate_index < len(text)
        if candidate_index == -1:
            return candidate_index
        elif candidate_index != 0 and text[candidate_index - 1] == '\\':
            skip += 1
            continue
        else:
            return candidate_index


def date_today(text: str) -> str:
    """If the date in the preamble contains the word Today, then actually make it today.
    This is case-sensitive.
    """
    # text = text.replace('\\date{Today}', '\\date{\\today}', 1)
    return text


def change_document_class(text: str, document_class: str) -> str:
    """Change the document class of the entire document.
        - text is the entire latex document.

        Do nothing if document_class == ''.
    """
    if document_class == '':
        return text
    document_class_ind = text.find('\\documentclass')
    end_of_doc_class_declaration = local_env_end(text, document_class_ind)
    if '\\' not in document_class:
        doc_class_text = '\\documentclass{' + document_class + '}'
    else:
        doc_class_text = document_class
    text = text[:document_class_ind] + doc_class_text + text[end_of_doc_class_declaration + 1:]
    return text


def remove_comments_from_document(text: str) -> str:
    """I want every single comment in this document gone

    Preconditions:
        - verbatim concealed
    """
    as_list = text.split('\n')
    return '\n'.join([t.split('%')[0] for t in as_list])


def subsection_limit(text: str, section_limit: int, deepest_section: int = 6) -> str:
    """Subsection fallback time.
    Section limit is based on how they are numbered in MS Word.
    Anything greater would be reduced to section limit

    Preconditions:
        - section_limit >= 1
    """
    if section_limit < 1:
        raise ValueError
    default_section = '\\' + (section_limit - 1) * 'sub' + 'section{'
    for i in range(deepest_section, section_limit, -1):
        section_kw = '\\' + (i - 1) * 'sub' + 'section{'
        text = text.replace(section_kw, default_section)
    return text


LTS_TEST = R"""
A & B & C \\
D & E & F \\
G & H & I \\
"""


def longtable_splitter(text: str) -> str:
    """Massively split the longtable.
    I mean, actually split it. This means
    to split up every & and \\.

    Text must be the contents of the longtable
    and may not include any headings.
    """
    escape_and = '⅘ↈ↋ↇ'
    text = text.replace('\\&', escape_and)

    target_characters = ('&', R'\\')

    # spaced_and = 'Ⅻⅽ⅛Ⅿ'
    for t_char in target_characters:
        skip = 1

        t_ind_so_far = []
        # loop invariant: t_ind_so_far has no duplicate values
        while True:
            closest_and = find_not_in_any_env_tolerance(text, t_char, 0, 1, skip)
            if closest_and == -1:
                break
            t_ind_so_far.append(closest_and)
            skip += 1
        for ind in reversed(t_ind_so_far):
            text = text[:ind] + f'\n\n\n{t_char}\n\n\n' + text[ind + len(t_char):]
    text = text.replace('\n ', '\n')
    text = text.replace(escape_and, '\\&')
    return '\n\n' + text + '\n\n'


def replace_many(text: str, replace: dict[str, str]) -> str:
    """Same as str.replace(...), but allows multiple
    replacements to be made. Key is find, value is replace
    """
    for k, v in replace.items():
        text = text.replace(k, v)
    return text


def abstract_wrapper(text: str) -> str:
    """If there's an abstract, wrap it.
    """
    mt = '\\maketitle'
    checker_text = text.strip()
    if checker_text.startswith(mt):
        checker_text = checker_text[len(mt):].strip()
    abstract_text = 'Abstract'
    abstract_location = checker_text.find('Abstract')
    abstract_location_bold = checker_text.find('\\textbf{Abstract}')
    if abstract_location_bold != -1 and abstract_location_bold < abstract_location:
        abstract_location = abstract_location_bold
        abstract_text = '\\textbf{Abstract}'
    if abstract_location == -1:  # if the word abstract DNE
        return text
    else:
        nearest_section_location = find_next_section(checker_text, 0)
        # look for the next the nearest section. if the abstract starts
        # before the nearest next section, then declare it.
        if abstract_location < nearest_section_location:
            text = text.replace(abstract_text, '\\begin{abstract}\n\n', 1)
            next_section = find_next_section(text, 0, 6)
            text = text[:next_section] + '\n\n\\end{abstract}\n\n' + text[next_section:]
            # by convention, the abstract will always go
            # before the table of contents. if there is a table of contents,
            # swap them.
            abstract_location = text.find('\\begin{abstract}')
            abstract_ending = text.find('\\end{abstract}')
            title_location = text.find('\\maketitle')
            assert abstract_ending != -1 and abstract_location != -1
            if title_location == -1:  # can't find the title? place the abstract at the v. start
                text = text[abstract_location:abstract_ending + len('\\end{abstract')] + \
                    text[:abstract_location] + text[abstract_ending + len('\\end{abstract}'):]
            else:
                text = text[:title_location + len('\\maketitle')] + \
                    text[abstract_location:abstract_ending + len('\\end{abstract}')] + \
                    text[title_location + len('\\maketitle'):abstract_location] + \
                    text[abstract_ending + len('\\end{abstract}'):]  # past the abstract end
                # start to \maketitle
                # add the abstract content
                # after title to where the abstract starts
                # after the abstract ends

        return text
    # else:
    #     return text


def local_env_layer_bulk(text: str, index: int, envs: list[str]) -> int:
    """local_env_layer, but accepts multiple local environment layers.
    Always return the HIGHEST of what was returned.
    """
    highest_env_so_far = 0
    for le in envs:
        lsf = local_env_layer(text, index, le)
        if lsf > highest_env_so_far:
            highest_env_so_far = lsf
    return highest_env_so_far


def latexing(text: str) -> str:
    """Latex all LaTeX.

    We need to update local env layer to allow the detection of params.
    """
    all_bad_envs = ['texttt', 'includegraphics', 'label', 'ref']
    ltx = '◚LT◞X◩◩'
    location = len(text)
    while True:
        latex = 'LaTeX'

        location = text.rfind(latex, 0, location)
        if location == -1:
            break
        in_env = local_env_layer_bulk(text, location, all_bad_envs) > 0
        in_eqn = check_in_equation(text, location)
        if not (in_env or in_eqn):
            text = text[:location] + ltx + text[location + len(latex):]
    return text.replace(ltx, '\\LaTeX')


def check_in_equation(text: str, index: int) -> bool:
    """Return whether text[index] is inside any equation.

    Must be ran before alignment regions are processed.
    """
    l1 = any_layer(text, index, '\\[', '\\]')
    if l1 == 1:
        return True
    l2 = any_layer(text, index, '\\(', '\\)')
    return l2 == 1


def conditional_preamble(text: str, keys: dict[str, Union[bool, int, str]]) -> str:
    """This is the CONDITIONAL PREAMBLE module. SYNTAX:
    % CONDITION: var1==True
    When a line in the preamble is conditional,
    only show if it is true. If false, then discard.

    text is a preamble.
    """
    as_list = text.split('\n')
    added_back = []

    force_hide = False

    for line in as_list:
        components = line.split('%')
        if not force_hide:
            if len(components) >= 2:
                comment = components[1]
                if not comment.strip().startswith('IF'):
                    # Default
                    if condition_checker(comment, keys):
                        added_back.append(components[0])
                    else:
                        pass
                else:
                    # IF statement detected at the start
                    # If an expression is invalid, the default is TRUE
                    comment = comment.strip()[2:].strip()
                    if not condition_checker(comment, keys):
                        force_hide = True
            else:  # If there isn't a comment, the default is TRUE
                added_back.append(components[0])
        else:
            if len(components) >= 2 and components[1].strip().startswith('ENDIF'):
                force_hide = False
    added_back = remove_consecutive_empty_entries(added_back)
    return '\n'.join(added_back)


def condition_checker(comment: str, keys: dict[str, Union[bool, int, str]],
                      default: bool = True) -> bool:
    """Input comment and keys. Check if True should be returned.
    """
    valid_comment_expression = check_valid_comment_expression(comment)
    if valid_comment_expression is not None:
        key, value = valid_comment_expression
        left_side = keys.get(key, None)
        # SUCCESSFUL BRANCH
        if left_side is not None and (isinstance(left_side, str) or isinstance(left_side, bool)
                                      or isinstance(left_side, int)):
            state = weak_equality(left_side, value)
            return state
    return default


def check_valid_comment_expression(text: str) -> Optional[tuple[str, str]]:
    """Check if a comment is valid. If so, return the expression.
    """
    text = text.strip()
    spl2 = text.split('==', 1)
    if len(spl2) == 2:
        spl3 = (spl2[0].strip(), spl2[1].strip())
        return spl3
    else:
        return None


def weak_equality(left: Union[str, int, bool], right: Union[str, int, bool]) -> bool:
    """A weak equality.
    """
    return str(left) == str(right)


CH_TEST = R"""
Please

\section{h}

\subsection{h}

\subsubsection{h}

\subsubsubsection{h}

\subsubsubsubsection{h}

"""


def make_chapter(text: str, depth: int = 8, shift: int = -1) -> str:
    """Shift everything to the left by the number stated in shift.
    Must be done before anything that messes with the sections.

    Preconditions:
        - -2 <= parts <= 0
    """
    secs = ['part', 'chapter'] + [k * 'sub' + 'section' for k in range(depth + 2)]
    # add 2 to secs for fairness
    decrease = shift
    for i in range(0, depth):
        # print(secs[i+2])
        # print(secs[i+2+decrease])
        st = '\\' + secs[i + 2] + '{'  # '\\' + 'sub' * i + 'section{'
        st2 = '\\' + secs[i + 2 + decrease] + '{'
        text = text.replace(st, st2)
    return text


def remove_consecutive_empty_entries(lst: list[str]) -> list[str]:
    """If more than one empty entry occurs in a row, remove them.
    """
    new_list = []
    last_empty = False
    for item in lst:
        if item != '':
            new_list.append(item)
            last_empty = False
        elif not last_empty:
            new_list.append(item)
            last_empty = True
        else:
            pass  # do nothing
    return new_list


def has_longtable(text: str) -> bool:
    """Return whether text has a longtable.
    """
    return '\\begin{longtable}' in text


EQN_TABLE = R"""
\(1+2=3\)
\({4+2+66+5=4}{43+5+345+43=5}\)
\(1+2=3\)
\({4+2+66+5=4}{43+5+345+43=5}\)
"""


def process_equations_in_tables(text: str, p_box_size: int = 11) -> str:
    """Inputs: text is an entire cell
    in a regular LaTeX table.

    p_box_size is always measured in em.
    """
    p_box = '\\parbox{' + str(p_box_size) + 'em}{'
    skip = 1
    while True:
        eq_opener = find_not_in_any_env_tolerance(text, '\\(', start=0, skip=skip)
        eq_closer = find_not_in_any_env_tolerance(text, '\\)', start=0, skip=skip)
        if eq_opener == -1:
            break  # also, eq_closer should be -1 as well
        equation_contents = text[eq_opener:eq_closer + 2]
        if equation_in_table_checker(equation_contents):
            text = text[:eq_opener] + p_box + '\n\\[' + equation_contents[2:-2] + '\\]' + '\n}\n\n' + text[
                                                                                                      eq_closer + 2:]
        else:
            skip += 1
    return text


def process_equations_in_table_header(text: str, p_box_size: int = 11) -> str:
    """Inputs: text is an entire cell
     in a regular LaTeX table.

     p_box_size is always measured in em.
     """
    p_box = '\\parbox{' + str(p_box_size) + 'em}{'
    skip = 1
    while True:
        eq_opener = find_not_in_any_env_tolerance(text, '\\[', start=0, skip=skip)
        eq_closer = find_not_in_any_env_tolerance(text, '\\]', start=0, skip=skip)
        if eq_opener == -1:
            break  # also, eq_closer should be -1 as well
        equation_contents = text[eq_opener:eq_closer + 2]
        if equation_in_table_checker(equation_contents):
            text = text[:eq_opener] + p_box + '\n\\[' + equation_contents[2:-2] + '\\]' + '\n}\n\n' + text[
                                                                                                      eq_closer + 2:]
        skip += 1  # skip always goes up by 1
    return text


def equation_in_table_checker(text: str) -> bool:
    """Inputs: text is the contents of an equation, which
    MUST start with \\( and end with \\)

    Returns: True if it's an alignment equation, False otherwise.
    """
    # assert text.startswith('\\(') and text.endswith('\\)')
    text = text[2:-2]  # strip the left and right \( and \)
    text = '\\[' + text + '\\]'
    valid_alignment_state = check_valid_alignment(text)
    return valid_alignment_state is not None


def check_valid_alignment(text: str) -> Optional[tuple[str, int, int]]:
    """Return isolate string, start index, end index + 1 for the first align region found in text.
    Return nothing if no align region found.

    What should be passed in must start with \\[ and \\].

    Detect an alignment region. An alignment region starts with \\[ and ends with \\],
    but only if { follows \\[. It will only detect if that happens for the first time.
    Return None if we can't do that.

    >>> string = 'you are not \\[{9 + 10 = 21}{420 + 69 = 222}\\] real'
    >>> output = '\\[{9 + 10 = 21}{420 + 69 = 222}\\]'
    >>> check_valid_alignment(string) == output
    True


    """
    # text = 'aaaa(bb()()ccc)dd'
    # istart = []  # stack of indices of opening parentheses
    # d = {}

    inside = False  # True if \[ has passed and not closed
    brace_layer = 0
    last_opening_region = 0
    prev_is_backslash = False
    prev_is_opening_bracket = False  # if the prev is \[ - the [
    finished_region = [-1, -1]
    found = False
    special_region_info = None
    for i, c in enumerate(text):  # the massive for loop
        assert not (prev_is_opening_bracket and prev_is_backslash), '[ and \\ at the same time'

        if prev_is_opening_bracket and c != '{':
            inside = False
            prev_is_opening_bracket = False
        else:
            prev_is_opening_bracket = False  # if \[{
        # It's not an alignment region if all of the conditions are met:
        # Inside is True
        # brace_layer is 0
        # the char we are focusing at is not {, }, or \n, and
        # \{ and \} do not count as braces
        if inside:
            if c == '\\':
                pass
            elif prev_is_backslash and (c == '[' or c == ']'):
                pass
            elif not prev_is_backslash and (c == '{' or c == '}'):  # bare { or }
                if c == '{':
                    brace_layer += 1
                elif c == '}':
                    brace_layer -= 1
                else:
                    assert False  # we will NEVER reach there
            elif prev_is_backslash and (c in {'[', ']'}):  # bare \[ or \]
                pass  # prevents the branch below from happening. We would've ended stuff here.
            elif c == '\n':
                pass
            else:
                if brace_layer <= 0:  # this is a very special case.
                    # if that is the case, skip to the next \\]
                    # then check everything between c and before \\], stripped
                    ti_c = text.find('\\]', i)
                    assert ti_c != -1
                    last_part = text[i - 1:ti_c].strip()
                    state = valid_matrix(last_part)
                    if not state:  # this happens the most often
                        inside = False  # this is rarer.
                    else:
                        finished_region[0] = last_opening_region
                        finished_region[1] = ti_c + 2
                        found = True
                        special_region_info = [i - 1, ti_c]  # positions to add { and }, similar to list.insert()
                        break

        if prev_is_backslash:
            if c == '[':
                inside = True
                last_opening_region = i - 1
                prev_is_opening_bracket = True
            if c == ']' and inside:
                # print('captured a region')
                finished_region[0] = last_opening_region
                finished_region[1] = i + 1
                assert finished_region[0] <= finished_region[1], 'future sight'
                found = True
                break
        prev_is_backslash = (c == '\\')  # if c is \\
        # if prev_is_backslash:
        #    print(prev_is_backslash)
    # if we ever find one
    if found:
        if special_region_info is None:
            captured_region = text[finished_region[0]:finished_region[1]]
            # print(captured_region)
        else:
            captured_region = text[finished_region[0]:special_region_info[0]] + '{' + \
                              text[special_region_info[0]:special_region_info[1]] + '}' + \
                              text[special_region_info[1]:finished_region[1]]
            # print(captured_region)

        return captured_region, finished_region[0], finished_region[1]
    else:
        # print('ran out of alignment regions to check')
        return None


def include_graphics_failsafe(text: str) -> str:
    """Prevents include graphics instances from
    breaking the LaTeX file.

    Parameters
    ----------
    text
        the text contents of the LaTeX file.

    Returns
    -------
        a modified version of the text contents of the
        LaTeX file.
    """
    return text.replace('\\includegraphics', '        \\includegraphics')


def toc_detector(text: str, depth: int) -> str:
    """Detect if there's a table of contents in the document.
    If so, return text with the table of contents.
    Note that in MS Word, the table contents begins with a section.
    It is treated to end at the next section, so you should
    start a new section after the
    table of contents finish.

    Preconditions:
        - hypertargets eliminated
        - depth >= 0

    Parameters
    ----------
    text
        the text to input.
    depth
        if this value is greater than 0, it means that the entire
        document has its headers shifted.

    Returns
    -------
        text with the toc appended, or not at all.
    """
    sb = 'sub' * depth
    toc = '\n{\n\\setcounter{tocdepth}{3}\n\\tableofcontents\n}\n'
    toc_location = text.find('\\' + sb + 'section{Contents}')
    if toc_location == -1:
        return text
    # elif find_previous_section(text, toc_location) != -1:  # there may not be a
    #     # previous section
    #     return text
    else:
        next_section = find_next_section(text, toc_location + 2)
        original_toc_contents = text[toc_location:next_section]
        if '\\protect\\hyperlink' in original_toc_contents:
            return text[:toc_location] + toc + text[next_section:]
        else:
            return text
