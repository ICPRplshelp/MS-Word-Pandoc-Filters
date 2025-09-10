#!/usr/bin/env python

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
    
    def left_right_depth(s: str, index: int) -> int:
        """Returns how deep I am, left to right
        Assume the start token is the backslash, and
        we count everything BEFORE index
        """
        depth = 0
        left = "\\left"
        right = "\\right"
        longer = max(len(left), len(right))
        for i, _ in enumerate(s):
            if i == index:
                return depth
            if s[i:longer].startswith(left):
                depth += 1
            elif s[i:longer].startswith(right):
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


        eqn_al = eqn_al.strip()
        max_len = 9999999999

        if len(eqn_al) == 0 or eqn_al[0] != "{":
            tm = None
            return eqn_al

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
                    if previous_char == '}' and (char == '_' or char == '^'): 
                        return [s_sub]
                    result.append(s_sub[i_ex_substr:])
                    return result
                previous_char = char
            return result

        sub_strs = extract_ms_equation_substrings(eqn_al)
        return generate_align_from_equations(sub_strs)

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
                ['<', '>', '\\leq', '\\geq', '\\approx'],
                ['\\subset', '\\subseteq', '\\not\\subset'],
                ['\\neq']
            ]
            target_index = 0  # start replacing BEFORE that index
            target_precedence = len(hierarchy) - 1
            for j, _ in enumerate(text):
                if brace_depth(text, j) == 0 and left_right_depth(text, j):
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
