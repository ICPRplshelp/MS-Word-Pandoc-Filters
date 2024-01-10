# Microsoft Word Equation Filter (Pandoc Filter)

YOU SHOULD WATCH THIS FIRST: https://www.youtube.com/watch?v=jlX_pThh7z8

This filter is based on the same modules I've
created in [Quick Word To LaTeX](https://github.com/ICPRplshelp/Quick-word-to-LaTeX-4).

These set of filters bridges the gap between Microsoft Word and Markdown when running conversions from them. Of course, Markdown **is** better for more complicated papers, so weigh pros and cons of using MS Word and Markdown accordingly. Moreover, use MS Word for informal documents that you won't be submitting as a thesis or publishing in a prestigious journal.

I know that `docx+styles` exists as an option (for those who know it), but there are some downsides that exist with it -- mainly, it messes up how code blocks work -- which I plan to fix (not at the moment).

We have some filters:

- `image_captioner.py`
    - Makes all Alt text captions. Precisely:
    - ![this](https://media.discordapp.net/attachments/1036007721343926342/1060011166853771274/image.png)
    - As of right now, you cannot tamper with figure numbering or make references to figures.
- `code_block.py`
    - Makes source code blocks behave like Markdown code blocks, exactly.
      Define their language on the top of the code block.
     ![example](https://media.discordapp.net/attachments/1036007721343926342/1060011485713137804/image.png)

- `start_wrapper.py`
    - Bring Pandoc's Div syntax to MS Word. Read the header
      of this Python file for more reference, and scroll down to see
      the divs/environments that are supported.
    - I used this using Python by itself and no packages, so **this filter will only work in the outer most div** (hence, it won't work if you nest anything in a list or a table)
    - > ::: definition term
      >
      > Definition text goes here
      >
      > /// definition

    - All the text inside will be put in a `div` with the **class** set to the first word\*, and the **title** set to all words after that. For instance, the quote above would be morphed into
    - ```html
      <div class="definition" title="term"> 
      Definition text goes here 
      </div>
      ```
    - There will **not** be a title if it is blank.
    - If you use this with the [Pandoc LaTeX environment](https://github.com/chdemko/pandoc-latex-environment) filter, you will end up with
    - ```tex
      \begin{definition}[text goes here]
      Definition text goes here
      \end{definition}
      ```
    - **The classes are hardcoded!!!** For now. This means there is a limited number of classes that work with this. You can always change the source code if you want to. Just be aware of this:


```python
starter_flag = ':::'
    ending_flag_f = '///'

    asts = [  # ast (ignore), div name, start flag (text after ::: to signal env start), end flag (text after /// to signal end of env)
        ASTProcessor(ast, "note", "note", "note", starter_flag, ending_flag_f),
        ASTProcessor(ast, "tip", "tip", "tip", starter_flag, ending_flag_f),
        ASTProcessor(ast, "warning", "warning", "warning", starter_flag, ending_flag_f),
        ASTProcessor(ast, "caution", "caution", "caution", starter_flag, ending_flag_f),
        ASTProcessor(ast, "important", "important", "important", starter_flag, ending_flag_f),
        # ::: proof \n\n [proof text] \n\n /// QED. This one is special
        ASTProcessor(ast, "proof", "proof", "QED", starter_flag, ending_flag_f),
        ASTProcessor(ast, "definition", "definition", "definition", starter_flag, ending_flag_f),
        ASTProcessor(ast, "solution", "solution", "solution", starter_flag, ending_flag_f),
        ASTProcessor(ast, "box", "box", "box", starter_flag, ending_flag_f)
    ]
```

In the future, I might allow wildcards.

- `ms_word_eqn_filter.py`
    - Read below

**IMPORTANT:** One of the filters may break if you don't enter `set PYTHONIOENCODING=utf-8`
in command prompt before running the filter. You must do this every time you open command prompt.


## How to use filters

Anywhere in your pandoc command, if `--filter <filtername>` is typed, then the filter `<filtername>` will be applied. `<filtername>` is the filter; an example being `code_block.py`.

Since the filter is a **path to a file**, it must be in the same working directory as where you are executing the command, or it must be a full path right from the root (`C:` in windows). I believe in Pandoc's installation files there
is a folder where if any filter is there, you can just type
the filter's name without any verboseness regardless of which working directory you are in.

A document can have multiple filters.

You must have these python packages installed first:

```
panflute
pandocfilters
```


## I'm getting this error: `pandoc: Could not find executable python` in Mac OS! How do I fix it?

If you're getting this error, it probably means that running `python` in terminal does nothing. Hence, you'll
need to mess with some environment variables. The steps are a bit complicated, but what you are trying to do is
to make `python` an alias to `python3.11`.

Follow these steps carefully.

1. Open terminal. Run `nano ~/.bashrc`
2. If you don't see this in the file, add the following, as **verbatim** into the file in its own line: `export PATH="/usr/local/bin:$PATH"`
3. Save the file (press `CTRL+O` then hit `RETURN`)
4. Close and re-open terminal (and maybe all other apps that involve using the terminal)
5. Run `sudo ln -s /usr/local/bin/python3.11 /usr/local/bin/python` in the terminal. NOTE: you may need to replace `/usr/local/bin/python3.11` with whatever
   you see here: 
   ![this image](https://media.discordapp.net/attachments/889357303034314782/1059019405721354291/image.png) (Open PyCharm, go to settings > python interpreter, and look for the specific interpreter you want to target)
6. Verify what you did worked by typing `python` in terminal. If you are successful, the python console should appear. Type `exit()` to exit the console, but
   now the filters here should work regardless.


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
