function Para (para)
    if para.content[1] and para.content[1].text then
        local start = para.content[1].text
        if start:sub(1, 1) == "[" and start:sub(-1) == "]" then
            local class = start:sub(2, -2):lower()
            table.remove(para.content, 1)
            return pandoc.Div(para, pandoc.Attr("", {class}))
        end
    end
    return para
end