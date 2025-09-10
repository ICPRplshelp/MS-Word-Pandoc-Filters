#!/usr/bin/env python

"""Pandoc filter that permits source code blocks
in Microsoft Word to be treated as Markdown code blocks.

So you can define their languages on top.
Languages are not case-sensitive, so feel free
to ignore casing in your MS Word document.

The first line: If it's not a language, nothing will happen.
If it is a language, then remove the first line from the code block,
strip it, lowercase it, and set it as the language of the code block.

Also ensures that smart quotes are converted to regular
quotes for both inline code and source code. Note that you cannot
define languages for inline code blocks.
"""


import panflute as pf

CODE_LANG = {'80',
             'abap',
             'acsl',
             'ada',
             'algol',
             'ant',
             'assembler',
             'awk',
             'bash',
             'basic',
             'c',
             'c++',
             'caml',
             'cil',
             'clean',
             'cobol',
             'comal',
             'command.com',
             'comsol',
             'csh',
             'delphi',
             'eiffel',
             'elan',
             'erlang',
             'euphoria',
             'fortran',
             'gcl',
             'gnuplot',
             'haskell',
             'html',
             'idl',
             'inform',
             'java',
             'jvmis',
             'ksh',
             'lingo',
             'lisp',
             'logo',
             'make',
             'mathematica',
             'matlab',
             'mercury',
             'metapost',
             'miranda',
             'mizar',
             'ml',
             'modula-2',
             'mupad',
             'nastran',
             'oberon-2',
             'ocl',
             'octave',
             'oz',
             'pascal',
             'perl',
             'php',
             'pl/i',
             'plasm',
             'postscript',
             'pov',
             'prolog',
             'promela',
             'pstricks',
             'python',
             'r',
             'reduce',
             'rexx',
             'rsl',
             'ruby',
             's',
             'sas',
             'scilab',
             'sh',
             'shelxl',
             'simula',
             'sparql',
             'sql',
             'tcl',
             'tex',
             'ts',
             'vbscript',
             'verilog',
             'vhdl',
             'vrml',
             'xml',
             'xslt'}
ALIASES = {
    'py': 'python',
}


def set_code_block_language(code_block, doc):
    """Also ensures all tabs are four spaces"""
    if type(code_block) == pf.Code:
        code_block.text = code_block.text.replace('\t', '    ').replace("‘", "'")\
            .replace("’", "'").replace('“', '"').replace('”', '"')\
            .replace('ÔÇ£', '"').replace('ÔÇØ', '"').replace('–', '-').replace("â", "-").replace("ÔÇô", "-")
    if type(code_block) == pf.CodeBlock:
        # Get the first line of the code block
        # pf.debug(dir(code_block))
        # pf.debug(f'{code_block.classes} / {code_block.tag}')
        first_line = code_block.text.strip().split('\n')[0]
        # Is the first line a programming language
        if first_line.lower() in ALIASES:
            first_line = ALIASES[first_line.lower()]
        if first_line.lower() in CODE_LANG:
            # Apparently the classes is the language
            code_block.classes = [first_line.lower()]
            code_block.text = '\n'.join(code_block.text.strip().split('\n')[1:])
        code_block.text = code_block.text.replace('\t', '    ').replace("‘", "'")\
            .replace("’", "'").replace('“', '"').replace('”', '"')\
            .replace('ÔÇ£', '"').replace('ÔÇØ', '"')


def main(doc=None):
    # Iterate over all the code blocks in the document
    return pf.run_filter(set_code_block_language, doc)


if __name__ == '__main__':
    main()
