import math
import re
from typing import Optional, Union, Iterable, Any

from panflute import Math, run_filter


def fix_equations(eqn: str) -> str:
    """Repair all equations.
    This method is a bit long, so you might want to use folding.
    This should work with most equations.
    """

    def multi_replace(s: str, replacements: list[tuple[str, str]]) -> str:
        for old, new in replacements:
            s = s.replace(old, new)
        return s

    def brace_depth(s: str, index: int) -> int:
        depth = 0
        for i, char in enumerate(s):
            if i == index:
                break
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
        return depth

    def fix_vectors_again(txt: str) -> str:
        arg1 = "overset{⃑}"
        replace1 = "mathbf"
        x = re.sub("\\\\" + arg1, "\\\\" + replace1, txt)
        return x

    def fix_accents(text: str) -> str:
        """Fix accents causing problems.
        """

        def find_next_closing_bracket(text_fncb: str, index: int) -> int:
            """Find the next closing bracket.
            Preconditions:
                - text[index] != '{' or text[index] != '}'

            Return -1 on failure.
            """
            skip_fncb = 1
            while True:
                ind = find_nth(text_fncb, '}', skip_fncb, index)
                if ind == -1:
                    return -1
                if text_fncb[ind - 1] == '\\':
                    skip_fncb += 1
                    continue
                if bracket_layers(text_fncb, ind, starting_index=index) != -1:
                    skip_fncb += 1
                    continue
                else:
                    return ind

        def local_env_end(text_local_env_end: str, index: int) -> int:
            """Return the position of the closing brace where the local environment ends.

            It is strongly recommended that text[index] == '\\' and
            is the start of a local environment declaration. Though the farthest
            index can be is at the position of the opening brace.

            Raise ValueError if an end cannot be found.
            """
            n = 1
            while True:
                closest_bracket = find_nth(text_local_env_end, '}', n, index)
                if closest_bracket == -1:
                    raise ValueError("Opening bracket without a closing bracket detected")
                b_layer = bracket_layers(text_local_env_end, closest_bracket, starting_index=index)
                if b_layer == 0:
                    # cur_ind = closest_bracket
                    break
                else:
                    n += 1
            return closest_bracket

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

    def aug_matrix_spacing(__text: str) -> str:
        """Spaces all augmented matrices.
        """
        __old = R'\end{matrix}\mid\begin{matrix}'
        __new = R'\end{matrix}\;\middle|\;\begin{matrix}'
        return __text.replace(__old, __new)

    def fix_equation_align_case(eqn_al: str) -> str:
        """Repair the equation, if applicable"""

        def split_equation(text: str, max_len: int) -> Union[None, list[str]]:
            """Return a split version of an equation.
            text is the raw equation text, and is not wrapped by display style brackets.
            max_len is the max length of an equation line before a newline
            has to be added.
            Return none if the equation does not need to be split.
            If list_mode is set to True, then return as a list of strings.
            """

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

            def replace_many(text: str, replace: dict[str, str]) -> str:
                """Same as str.replace(...), but allows multiple
                replacements to be made. Key is find, value is replace
                """
                for k, v in replace.items():
                    text = text.replace(k, v)
                return text

            ALPHABET = 'abcdefghijklmnopqrstuvwxyz'

            def remove_envs(text: str) -> str:
                """Remove everything between \\ up until it's not a letter
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

            def seperate_fraction_block(frac_text: str) -> str:
                """Return the side of the fraction that is longer.
                Preconditions:
                    - frac_text looks like \\frac{}{}

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
                        ending_frac_index = index_fourth_closing_bracket(text, frac_index) + 1  # AT the char AFTER
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
                """
                for i, li in enumerate(lst):
                    if item < li:  # 1
                        return i
                return len(lst)

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
                return new_master
            return None

        eqn_al = eqn_al.strip()
        max_len = 80
        if len(eqn_al) == 0 or eqn_al[0] != "{":
            tm = split_equation(eqn_al, max_len)
            if tm is None or len(tm) <= 1:
                return eqn_al
            else:
                return generate_align_from_equations(tm)

        def extract_ms_equation_substrings(s_sub: str) -> list[str]:
            """Convert an equation in MS Word form with no conflicting braces
            into a list of equations.
            ASSUMPTIONS: No spaces, well-formed
            If the equation isn't well-formed, immediately give up.
            """
            stack = []
            result = []
            depth = 0
            previous_char = None
            for i_ex_substr, char in enumerate(s_sub):
                if char == '{':
                    if depth == 0:
                        if previous_char != "}" and previous_char is not None:
                            return []
                        stack.append('')
                    else:
                        stack[-1] += char
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0 and stack:
                        result.append(stack.pop())
                    elif stack:
                        stack[-1] += char
                elif stack:
                    stack[-1] += char
                else:
                    if previous_char == '}' and (char == '_' or char == '^'):  # this case proves it impossible to be an
                        return [s_sub]
                    result.append(s_sub[i_ex_substr:])
                    return result
                previous_char = char
            return result

        sub_strs = extract_ms_equation_substrings(eqn_al)
        new_ss = []
        for ss in sub_strs:
            tm = split_equation(ss, max_len)
            if tm is None:
                new_ss.append(ss)
            else:
                new_ss.extend(tm)
        return generate_align_from_equations(new_ss)

    def generate_align_from_equations(sub_strs: list[str]) -> str:

        if len(sub_strs) <= 1:
            if len(sub_strs) == 1:
                return sub_strs[0]
            else:
                return ""

        str_builder = []

        def add_and_to_symbol(text: str) -> str:
            hierarchy = [
                ["\\iff", "\\Leftrightarrow", "\\Rightarrow", "\\implies", "\\Leftarrow"],
                ['='],
                ['<', '>', '\\leq', '\\geq', '\\approx'],
                ['\\subset', '\\subseteq', '\\not\\subset'],
                ['\\neq']
            ]
            target_index = 0  # start replacing BEFORE that index
            target_precedence = len(hierarchy) - 1
            for j, char in enumerate(text):
                if brace_depth(text, j) == 0:
                    for k, row in enumerate(hierarchy):
                        if k > target_precedence:
                            continue
                        for symbol in row:
                            if text[j:].startswith(symbol):
                                target_index = j
                                target_precedence = k
            return text[:target_index] + f" &" + text[target_index:]

        for i, line in enumerate(sub_strs):
            last = i == len(sub_strs) - 1
            trailing = R" \\" if not last else ""
            string_so_far = add_and_to_symbol(line)
            str_builder.append(string_so_far + trailing)
        return "\\begin{aligned}\n" + "\n".join(str_builder) + "\n\\end{aligned}"

    eqn = multi_replace(eqn, [
        ("\n", " "),
        (R"\{", R"\lbrace"), (R"\}", R"\rbrace"),
        ('≢', '\\not\\equiv '),
        ("\\overrightarrow", "\\vec")
    ])

    eqn = fix_vectors_again(eqn)
    eqn = fix_accents(eqn)
    eqn = aug_matrix_spacing(eqn)
    eqn = fix_equation_align_case(eqn)
    return eqn + "  "


def find_nth(haystack: str, needle: str, __n: int, starter: Optional[int] = None, end: Optional[int] = None) -> int:
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
    while start >= 0 and __n > 1:
        start = haystack.find(needle, start + len(needle), end)
        __n -= 1
    return start


def bracket_layers(text_bl: str, index: int,
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
    """
    if not (len(opening_brace) == 1 and len(closing_brace) == 1):
        escape_char = False
    layer = 0
    esc = '\\' + opening_brace
    esc2 = '\\' + closing_brace
    if escape_char:
        text_bl = text_bl.replace(esc, '🬍🬘').replace(esc2, '🬮🭕')
    for i, char in enumerate(text_bl):
        if i < starting_index:
            continue
        if char == opening_brace:
            layer += 1
        if char == closing_brace:
            layer -= 1
        if i == index:
            return layer

    if index == -1:
        return layer
    else:
        raise IndexError('Your index was out of bounds.')


def fix_equations_pf(elem: Any, doc: Any):
    if type(elem) == Math:
        txt = elem.text
        elem.text = fix_equations(txt)
    return elem


def main(doc: Any = None) -> Any:
    return run_filter(fix_equations_pf, doc=doc)


if __name__ == "__main__":
    main()
