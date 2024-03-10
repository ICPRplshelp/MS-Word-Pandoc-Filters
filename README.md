# Microsoft Word Equation Filter (Pandoc Filter)

YOU SHOULD USE THE WORD TEMPLATE PROVIDED IN THIS VIDEO: <https://www.youtube.com/watch?v=jlX_pThh7z8>

This filter is based on the same modules I've
created in [Quick Word To LaTeX](https://github.com/ICPRplshelp/Quick-word-to-LaTeX-4).

These set of filters bridges the gap between Microsoft Word and Markdown when running conversions from them. Of course, Markdown **is** better for more complicated papers, so weigh pros and cons of using MS Word and Markdown accordingly. Moreover, use MS Word for informal documents that you won't be submitting as a thesis or publishing in a prestigious journal.

I know that `docx+styles` exists as an option (for those who know it), but there are some downsides that exist with it -- mainly, it messes up how code blocks work -- which I plan to fix (not at the moment).

We have some filters:

- `image_captioner.py`
  - Makes all Alt text captions. All images with Alt text will count as figures. Images without Alt text will not count as figures.
  - As of right now, you cannot tamper with figure numbering or make references to figures.
- `code_block.py`
  - Makes source code blocks behave like Markdown code blocks, exactly.
      Define their language on the top of the code block. Languages are case-insensitive
- `div_inserter.lua`
  - If this starts a paragraph: `[TEXTINSQUAREBRACKETS]` This entire paragraph gets put in a LaTeX environment `textinsquarebrackets` (all lowercase) **given you use the `pandoc-latex-enviornment` filter**
- `start_wrapper.py`
  - DEPRECATED - DO NOT USE



In the future, I might allow wildcards.

- `ms_word_eqn_filter.py`
  - Read below

**IMPORTANT:** One of the filters may break if you don't enter `set PYTHONIOENCODING=utf-8`
in command prompt before running the filter. You must do this every time you open command prompt.


## How to use filters


You must have these python packages installed first:

```
panflute
pandocfilters
```

Anywhere in your pandoc command, if `--filter <filtername>` is typed, then the filter `<filtername>` will be applied. `<filtername>` is the filter; an example being `code_block.py`. If you want to use multiple filters, just have multiple `--filter`s in your command.

If the filter is a **Lua** filter, you must use `--lua-filter=<FILTER>` instead.

Since the filter is a **path to a file**, it must either be:

- In the current working directory
- An absolute path
- If the filter is in `C:\Users\%USERNAME%\AppData\Roaming\pandoc\filters`, you can treat it as if it is in your current working directory.

A document can have multiple filters.

SAMPLE COMMAND:

```sh
pandoc -s word_file.docx -o output.pdf --filter code_block.py --filter ms_word_eqn_filter.py
```

# How the equation filter works

I'll be assuming you're familiar with typesetting equations in Microsoft Word. If you aren't, take a look at [this guide that I've written.](https://github.com/ICPRplshelp/Quick-word-to-LaTeX-4/wiki/Microsoft-Word-Equation-Syntax)

The equation filter works by ensuring that Pandoc's handling of Microsoft
Word equations does not mess anything up. In other words, it makes
the equations you type in Microsoft Word appear as how you actually
typed it in MS Word, when Pandoc is used with that filter.

Normally, equations may break without the filter. If you use this
filter, there are some conventions you **must** follow:

- To simulate a series of stacked display equations (typically done with `\begin{align} ... \end{align}`), use `SHIFT+ENTER` to create new rows (the filter will use `\begin{aligned} ... \end{aligned}`). Do not use any other method. If you don't use `SHIFT+ENTER`, then the two equations will be treated as separate display equations.

- Try to minimize the use of `CTRL+B`, `CTRL+I`, or any other formatting when writing equations.

- Avoid numbering your equations. Even though this filter supports it, this feature is very unstable. If you want to add comments to equations, you'll have to do it in some other way (equivalent to `\emsp \text{comment here}`)

- `\funcapply` may not work. Use quotes (`""`, has the same effect as `\text{...}`) instead.
