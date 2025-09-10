-- Set of supported languages (lowercase)
local CODE_LANG = {
  ["80"] = true, ["abap"] = true, ["acsl"] = true, ["ada"] = true, ["algol"] = true,
  ["ant"] = true, ["assembler"] = true, ["awk"] = true, ["bash"] = true, ["basic"] = true,
  ["c"] = true, ["c++"] = true, ["caml"] = true, ["cil"] = true, ["clean"] = true,
  ["cobol"] = true, ["comal"] = true, ["command.com"] = true, ["comsol"] = true, ["csh"] = true,
  ["delphi"] = true, ["eiffel"] = true, ["elan"] = true, ["erlang"] = true, ["euphoria"] = true,
  ["fortran"] = true, ["gcl"] = true, ["gnuplot"] = true, ["haskell"] = true, ["html"] = true,
  ["idl"] = true, ["inform"] = true, ["java"] = true, ["jvmis"] = true, ["ksh"] = true,
  ["lingo"] = true, ["lisp"] = true, ["logo"] = true, ["make"] = true, ["mathematica"] = true,
  ["matlab"] = true, ["mercury"] = true, ["metapost"] = true, ["miranda"] = true, ["mizar"] = true,
  ["ml"] = true, ["modula-2"] = true, ["mupad"] = true, ["nastran"] = true, ["oberon-2"] = true,
  ["ocl"] = true, ["octave"] = true, ["oz"] = true, ["pascal"] = true, ["perl"] = true,
  ["php"] = true, ["pl/i"] = true, ["plasm"] = true, ["postscript"] = true, ["pov"] = true,
  ["prolog"] = true, ["promela"] = true, ["pstricks"] = true, ["python"] = true, ["r"] = true,
  ["reduce"] = true, ["rexx"] = true, ["rsl"] = true, ["ruby"] = true, ["s"] = true,
  ["sas"] = true, ["scilab"] = true, ["sh"] = true, ["shelxl"] = true, ["simula"] = true,
  ["sparql"] = true, ["sql"] = true, ["tcl"] = true, ["tex"] = true, ["ts"] = true,
  ["vbscript"] = true, ["verilog"] = true, ["vhdl"] = true, ["vrml"] = true, ["xml"] = true,
  ["xslt"] = true
}

-- Aliases for languages
local ALIASES = {
  ["py"] = "python",
  ["ts"] = "java",
  ["js"] = "java"
}

-- Replace smart quotes and tabs
local function clean_text(text)
  return text
    :gsub("\t", "    ")
    :gsub("‘", "'")
    :gsub("’", "'")
    :gsub("“", '"')
    :gsub("”", '"')
    :gsub("ÔÇ£", '"')
    :gsub("ÔÇØ", '"')
    :gsub("–", "-")
    :gsub("â", "-")
    :gsub("ÔÇô", "-")
end

function CodeBlock(block)
  local lines = {}
  for line in block.text:gmatch("([^\n]*)\n?") do
    table.insert(lines, line)
  end
  local first_line = lines[1]:lower():match("^%s*(.-)%s*$")
  if ALIASES[first_line] then
    first_line = ALIASES[first_line]
  end
  if CODE_LANG[first_line] then
    block.classes = { first_line }
    table.remove(lines, 1)
    block.text = table.concat(lines, "\n")
  end
  block.text = clean_text(block.text)
  return block
end

function Code(inline)
  inline.text = clean_text(inline.text)
  return inline
end