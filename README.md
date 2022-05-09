# Microsoft Word Equation Filter (Pandoc Filter)

This filter is based on the same modules I've
created in [Quick Word To LaTeX](https://github.com/ICPRplshelp/Quick-word-to-LaTeX-4).

This is a Pandoc filter to make equations typed in Microsoft Word functional when run with Pandoc.
Normally, when using Pandoc when converting Microsoft Word documents, equations
tend to look a bit off, causing them to not work well. This filter repairs it.

Features:

- Stacked equations will automatically be aligned by the first `=` signs,
      or other similar signs, or `+`, `-` if none are present for too long.
- Allows equations to be commented. In Microsoft Word, # is used to make
  flushed-right equation comments. Note that equation comments may
  not contain anything, that if translated into TeX code, would have
  a backslash, except `\text`. Please put a number or a phrase - that's
  all you need. Please use "quotation marks" instead of CTRL+I when
  adding textual comments to equations in MS Word. **Long equations can't be commented!! If you've added a comment to a long eqaution, it will
  be removed. There is no reason to do this as MS Word does not automatically line-break long equations. Single-line display and stacked (multiline)
  equations can be commented.**
- Prevents overfull H-boxes. If an equation is too long without a
  line break, it will automatically be broken in half.
- This filter aims to prevent as many LaTeX errors as possible.
  I've accounted for the errors that could rise.

TL;DR - this feature is a must-have if you plan on converting
Microsoft Word `*.docx` files using Pandoc. This properly
converts equations in a way that Pandoc is incapable of.
Without this tool, equations will look very weird and won't
run well.

This is a universal filter. This is NOT LaTeX exclusive.
This filter directly interacts with the AST Pandoc produces,
meaning it will work if you use Pandoc to convert a(n) MS Word
file to HTML, or to LaTeX.

## How to use

**There are some requirements before using this!!**

1. You must have Python installed. Please don't
install it from the Windows 10 store.
2. Install panflute. It's the easiest when
you only have one version of python installed.
Follow the instructions [here](https://github.com/sergiocorreia/panflute).
3. Download this repository. Clone it. Extract all
its contents to a folder on your computer.
4. Open CMD and `cd` it to the same directory
as `ms_word_eqn_filter.py`. Note that `helper_files` must
also be in the same directory as the `py` file I mentioned.
5. Run the pandoc command and pass in that filter.

There are better ways to do this, but this is how I'll outline
the steps.

If you understand how to pass in Pandoc filters,
you'll know what I've written below does. All
you need to do is pass in the filter to the
command-line arguments of Pandoc.

```
--filter=ms_word_eqn_filter.py
```

Did you know? You can export all images within an
MS Word file using `--extract-media=imgs`.

## Bugs?

Please report them in the issue tracker.
