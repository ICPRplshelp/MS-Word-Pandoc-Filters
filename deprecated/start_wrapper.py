#!/usr/bin/env python

"""
::: definition the word I want to define

I am defining

/// definition

Your start and end flags must be on their own paragraphs. Anything past
the word "definition" is the title of the environment, to be placed
in [square brackets]. If that isn't there, then I won't place anything.

-->

\\begin{definition}[the word I want to define]

I am defining

\\end{definition}

Note that for Python's docstrings, I must use double backslashes.
"""


import io
import sys
import json


class ASTProcessor:
    c_ast: dict
    type_of: str
    start_key: str
    end_key: str
    start_block: list[dict]
    end_block: list[dict]
    delimiter: str

    # other environment variables may be placed here

    def __init__(self, c_ast: dict, type_of: str,
                 start_key: str, end_key: str,
                 delimiter: str, ending_flag: str) -> None:
        self.c_ast = c_ast
        self.type_of = type_of

        self.start_key = start_key
        self.end_key = end_key
        self.delimiter = delimiter
        self.ending_flag = ending_flag

        self.start_block = [{
            "t": "Para",
            "c": [
                {
                    "t": "Str",
                    "c": delimiter
                },
                {
                    "t": "Space"
                },
                {
                    "t": "Str",
                    "c": self.start_key
                }
            ]
        }]
        self.end_block = [{
            "t": "Para",
            "c": [
                {
                    "t": "Str",
                    "c": ending_flag
                },
                {
                    "t": "Space"
                },
                {
                    "t": "Str",
                    "c": self.end_key
                }
            ]
        }]

    def process_ast_first_time(self) -> None:
        """Note that c_ast is the raw pandoc
        ast, and it starts from there.

        This method fails if a blocks key doesn't
        exist in the root AST.
        """
        temp_blocks = self.c_ast.get("blocks")
        if temp_blocks is None:
            return

        # true when we're inside a block, as detected
        inside_key = False
        block_pairs: list[tuple[int, int, str]] = []
        start_block_index = 0
        # end_block_index = 0
        title_so_far = ''
        for i, block in enumerate(temp_blocks):
            if not inside_key:
                if self.block_content_matches(block, self.start_block):
                    start_block_index = i
                    inside_key = True
                    # otherwise do nothing
                    title_so_far = pandoc_list_to_string(block['c'], self.start_block[0].__len__() + 1)


            else:
                if self.block_content_matches(block, self.end_block):
                    end_block_index = i
                    inside_key = False
                    block_pairs.append((start_block_index, end_block_index, title_so_far))
        # SO FAR: block_pairs contains all pairs of blocks, which we will
        # need to put in its own type. start is the index where the block
        # started (has the start flag) and end is the index where the block
        # finished (has the finish flag)
        for st, en, title_of in reversed(block_pairs):
            # case 1: st < en
            inner_blocks = temp_blocks[st + 1:en]
            replacement_block = self.generate_wrapping_block(inner_blocks, title_of)
            temp_blocks[st:en + 1] = [replacement_block]
        # end of function. all blocks should be replaced.

    def generate_wrapping_block(self, inner_blocks: list[dict], title_of: str) -> dict:
        """Generates the wrapping block. How the block is made will
        depend on what class it is. It's best to extend and override
        this method in a superclass if you want to modify it"""
        if title_of != '':
            temp = {
                't': "Div",
                'c': [
                    # id, class, data-XXXX [[data, XXXX], ...]
                    ['', [self.type_of], [['title', title_of]]],
                    inner_blocks
                ]
            }
        else:
            temp = {
                't': "Div",
                'c': [
                    # id, class, data-XXXX [[data, XXXX], ...]
                    ['', [self.type_of], []],
                    inner_blocks
                ]
            }

        return temp
        #
        # temp = {
        #     't': self.type_of,
        #     'c': inner_blocks
        # }
        # return temp

    @staticmethod
    def block_content_matches(target_block: dict, check_block: list[dict]) -> bool:
        """Return True if and only if
        - target_block is a paragraph
        - target_block's content matches check_block
        """
        # skips anything that isn't [a para and doesn't have content]
        if not (target_block.get("t") == 'Para' and 'c' in target_block):
            return False

        return list_startswith_same([target_block][0]['c'], check_block[0]['c'])


def list_startswith_same(c1: list, c2: list) -> bool:
    for item1, item2 in zip(c1, c2):
        if item1 != item2:
            return False
    return True


def pandoc_list_to_string(li: list[dict[str, str]], skip: int) -> str:
    """Converts a pandoc list to a string."""
    li2 = li[skip:]
    words = []
    for item in li2:
        if item.get('t') == 'Str':
            words.append(item['c'])
    return' '.join(words)


if __name__ == '__main__':
    # Read the AST from stdin
    # input_stream = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')
    ast = json.loads(sys.stdin.read())
    # astp = ASTProcessor(ast, "proof", "proof", "QED", ':::')
    # astp.process_ast_first_time()
    starter_flag = ':::'
    ending_flag_f = '///'

    asts = [  # ast, div name, start flag, end flag
        ASTProcessor(ast, "note", "note", "note", starter_flag, ending_flag_f),
        ASTProcessor(ast, "tip", "tip", "tip", starter_flag, ending_flag_f),
        ASTProcessor(ast, "warning", "warning", "warning", starter_flag, ending_flag_f),
        ASTProcessor(ast, "caution", "caution", "caution", starter_flag, ending_flag_f),
        ASTProcessor(ast, "important", "important", "important", starter_flag, ending_flag_f),
        ASTProcessor(ast, "proof", "proof", "QED", starter_flag, ending_flag_f),
        ASTProcessor(ast, "definition", "definition", "definition", starter_flag, ending_flag_f),
        ASTProcessor(ast, "solution", "solution", "solution", starter_flag, ending_flag_f),
        ASTProcessor(ast, "box", "box", "box", starter_flag, ending_flag_f)
    ]
    for ast_p in asts:
        ast_p.process_ast_first_time()
    sys.stdout.write(json.dumps(ast))
