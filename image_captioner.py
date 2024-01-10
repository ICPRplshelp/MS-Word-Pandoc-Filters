"""Makes all images with ALT text figures. The ALT text will act as the figure number.
This filter should only be used when converting from any format other than markdown
because pandoc already does this for you.

Images with NO ALT text will not be affected. In MS Word, mark those images as decorative.
"""


import panflute as pf


def set_code_block_language(elem, doc):
    if type(elem) == pf.Image:
        if len(elem.content) > 0:
            elem.title = 'fig:'


def main(doc=None):
    # Iterate over all the code blocks in the document
    return pf.run_filter(set_code_block_language, doc)


if __name__ == '__main__':
    main()
