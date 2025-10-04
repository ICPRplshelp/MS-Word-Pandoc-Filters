# Microsoft Word Equation Filter (Pandoc Filter)

YOU SHOULD USE THE WORD TEMPLATE PROVIDED IN THIS VIDEO: <https://www.youtube.com/watch?v=jlX_pThh7z8>

These set of filters bridges the gap between Microsoft Word and Markdown when running conversions from them. Of course, Markdown **is** better for more complicated papers, so weigh pros and cons of using MS Word and Markdown accordingly. Moreover, use MS Word for informal documents that you won't be submitting as a thesis or publishing in a prestigious journal.

I know that `docx+styles` exists as an option (for those who know it), but there are some downsides that exist with it -- mainly, it messes up how code blocks work -- which I plan to fix (not at the moment).

We have some filters:


- `code_block.lua`
  - Makes source code blocks behave like Markdown code blocks, exactly.
      Define their language on the top of the code block. Languages are case-insensitive
- `div_inserter.lua`
  - If this starts a paragraph: `[TEXTINSQUAREBRACKETS]` This entire paragraph gets put in a LaTeX environment `textinsquarebrackets` (all lowercase) **given you use the `pandoc-latex-enviornment` filter** (otherwise don't use it)
- `word_eqn.lua`
  - Fixes every issue pandoc has with Microsoft word equations. See [below](#how-the-equation-filter-works)
- `no_longtable.lua`
  - Does not need to be with Microsoft Word, specifically. For conversions to LaTeX, prevents the `longtable` environment from being used entirely, instead using the `tabular` environment. One limitation: automatic line breaks don't occur anymore, so make sure your lines are short. **The only reason to use this, is if the pandoc template you're using can't support `longtable` such as anything that has multiple columns.**
  - **IMPORTANT:** When using this with `word_eqn.lua`, use this **AFTER**, meaning `--lua-filter=no_longtable.lua` must be placed after `--lua-filter=word_eqn.lua`.
  - `\usepackage{makecell} \usepackage{graphicx}` may need to be put in the header: `-V header-includes="\usepackage{makecell} \usepackage{graphicx}"`.

*Note: caption images by using the "caption" feature in Microsoft Word, which is now supported in Pandoc for quite a while.*

## How to use filters

Use your standard pandoc command, and specify the filters there.
The flag is specifically `--lua-filter=<FILTER>`.

Since the filter is a **path to a file**, it must either be:

- In the current working directory
- An absolute path
- If the filter is in `C:\Users\%USERNAME%\AppData\Roaming\pandoc\filters`, you can treat it as if it is in your current working directory.

A document can have multiple filters.

SAMPLE COMMAND:

```sh
pandoc -s word_file.docx -o output.pdf --lua-filter=code_block.lua --lua-filter=word_eqn.lua
```

# How the equation filter works

I'll be assuming you're familiar with typesetting equations in Microsoft Word. If you aren't, take a look at [this guide that I've written.](docs/msw_eqn_syntax.md)

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
