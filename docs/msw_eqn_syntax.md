# MS Word Equation syntax

Create an equation by using `ALT+=`.

The syntax is **very** similar to LaTeX, including all backslash commands. There are some differences:

- Bracket sizing: done automatically.
- Common functions like sin, cos, tan, min, max, and keywords like lim should not be typed with the backslash. MS Word will recognize these functions, and will not *slant* them. You can also add additional recognized functions that MS Word won't slant. You can alternatively use `\funcapply` after typing the function to unslant them. For example: `samplefunction\funcapply (...)`
- Accents, like vectors, are done like this: `a\vec`, and press space twice after entering these keystrokes.
- Matrices: do the following keystrokes - `[\matrix(@@&&)] ` (INCLUDING all spaces in the code block), and you'll get a 3x3 blank matrix where you can add stuff in.
- Augmented matrices: They are two matrices together joined with `\mid`, as the line.
- System of equations: Matrices with only a visible brace on the left. Here's an example of the keystrokes you would input to create a 2x2 system of equations: `{\matrix(x+2@x+4)\close `. Note that MS Word's `\close` is like LaTeX's `\right.` with the period.
- MathBB: `\doubleZ` is MS Word's version of `\mathbb{Z}`. Also, `\scriptO` is MS Word's version of `\mathcal{O}`.
- Fractions: Have you used Desmos before? Fractions type very similarly to Desmos. Use brackets if you want more control over them.
- Typing text in the equation box and have them be treated like actual text: wrap them in quotation marks `"`. `"sample"` is LaTeX's `\text{sample}` or `\mathrm{sample}`.
- Macros and custom commands: Use the equation autocorrect to set them up. Here:

![image](https://user-images.githubusercontent.com/93059453/164126495-8041469c-b86f-41c6-988b-fade20319496.png)

- Integrals: press space TWICE after typing `\int` to create an indefinite integral that is treated like an integral rather than some other character that MS Word will bug out with. Definite integrals don't need this.
- Equation numbering: See the equation numbering page in this Wiki.

Here are some macros I've set up, which aren't set up by default:

| What I type | Will be replaced with this |
| ----------- | -------------------------- |
| `\22m` | `■(@&)` |
| `\33m` | `■(@@&&)` |
| `\2m` | `■(@)` |
| `\augmat` | `[■(&&@&&@&&)  ∣ ■(@@)]` |
| `\Omdef` | `∃c,n_0∈ℝ^+,∀n∈ℕ,n≥n_0⇒g(n)≥c⋅f(n)` |
| `\rn` | `ℝ^(≥0)` |
| `\real` | `ℝ` (must copy paste from here) |
| `\v` | `⃑` (the vector half-arrow, similar and called like `\vec`) |
| `\qed` | `∎` |

## Additional articles you should look at:

- https://unicode.org/notes/tn28/UTN28-PlainTextMath-v3.pdf
- https://en.wikibooks.org/wiki/Typing_Mathematics_in_Microsoft_Word
- https://support.microsoft.com/en-us/office/linear-format-equations-using-unicodemath-and-latex-in-word-2e00618d-b1fd-49d8-8cb4-8d17f25754f8
