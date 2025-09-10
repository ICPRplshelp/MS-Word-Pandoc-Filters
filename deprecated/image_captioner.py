#!/usr/bin/env python

"""Makes all images with ALT text figures. The ALT text will act as the figure number.
This filter should only be used when converting from any format other than markdown
because pandoc already does this for you.

Images with NO ALT text will not be affected. In MS Word, mark those images as decorative.
"""


import panflute as pf


def make_image_caption(elem, doc):
    if type(elem) == pf.Image:
        if len(elem.content) > 0:
            elem.title = 'fig:'


def main(doc=None):
    # Iterate over all the code blocks in the document
    return pf.run_filter(make_image_caption, doc)


if __name__ == '__main__':
    main()
