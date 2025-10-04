local utils = require("pandoc.utils")

function Meta(meta)
  if FORMAT:match("latex") then
    
    local includes = meta["header-includes"] or {}
    table.insert(includes, pandoc.RawBlock("latex", "\\usepackage{makecell}"))
    table.insert(includes, pandoc.RawBlock("latex", "\\usepackage{graphicx}"))
    meta["header-includes"] = includes
  end
  return meta
end


function Table(tbl)
  if not FORMAT:match("latex") then
    return tbl
  end

  
  local alignment = {}
  for _, spec in ipairs(tbl.colspecs) do
    local align = spec[1]
    if align == 'AlignLeft' then
      table.insert(alignment, 'l')
    elseif align == 'AlignRight' then
      table.insert(alignment, 'r')
    else
      table.insert(alignment, 'c')
    end
  end
  local align_str = "|" .. table.concat(alignment, "|") .. "|"

  local lines = {}
  table.insert(lines, "\\begin{tabular}{" .. align_str .. "}")

  
  local function render_cell(cell)
    
    local content = cell.content or cell.contents or {}
  
    if type(content) ~= "table" or next(content) == nil then
      return ""
    end
  
    
    local inlines = pandoc.utils.blocks_to_inlines(content)
    local latex = pandoc.write(pandoc.Pandoc({pandoc.Para(inlines)}), "latex")
    latex = latex:gsub("\n$", "")
    latex = latex:gsub("\\%[", "\\(")
    latex = latex:gsub("\\%]", "\\)")
    
    latex = "\\makecell{" .. latex .. "}"
    
    return latex
  end

  
  table.insert(lines, "\\hline")
  for _, row in ipairs(tbl.head.rows) do
    local cells = {}
    for _, cell in ipairs(row.cells) do
      table.insert(cells, render_cell(cell))
    end
    table.insert(lines, table.concat(cells, " & ") .. " \\\\")
  end
  table.insert(lines, "\\hline")

  
  for _, body in ipairs(tbl.bodies) do
    for _, row in ipairs(body.body) do
      local cells = {}
      for _, cell in ipairs(row.cells) do
        table.insert(cells, render_cell(cell))
      end
      table.insert(lines, table.concat(cells, " & ") .. " \\\\")
      table.insert(lines, "\\hline")
    end
  end

  table.insert(lines, "\\end{tabular}")

  
  local caption = utils.stringify(tbl.caption)
  if caption ~= "" then
    lines = {
      "\\begin{table}[h]",
      "\\centering",
      table.concat(lines, "\n"),
      "\\caption{" .. caption .. "}",
      "\\end{table}"
    }
  end

  return pandoc.RawBlock("latex", table.concat(lines, "\n"))
end
