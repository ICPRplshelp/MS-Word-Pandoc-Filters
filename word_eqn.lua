-- Returns true if 'str' starts with 'prefix'
local function startswith(str, prefix)
    return str:sub(1, #prefix) == prefix
end

-- Returns the index (1-based) of the nth occurrence of 'needle' in 'haystack'
-- Returns -1 if not found
-- n = 1 is the lowest value of n; any value below 1 is treated as 1
-- starter means from what index? (1-based, optional)
local function find_nth(haystack, needle, n, starter, end_idx)
    n = math.max(n, 1)
    local start
    if starter == nil then
        start = string.find(haystack, needle, 1, true)
    else
        start = string.find(haystack, needle, starter, true)
    end
    if end_idx == nil then
        end_idx = #haystack
    end
    while start ~= nil and n > 1 do
        local next_start = string.find(haystack, needle, start + #needle, true)
        if next_start == nil or next_start > end_idx then
            start = nil
            break
        end
        start = next_start
        n = n - 1
    end
    if start == nil or start > end_idx then
        return -1
    end
    return start
end


local function bracket_layers(text_bl, index, opening_brace, closing_brace, escape_char, starting_index)
    opening_brace = opening_brace or "{"
    closing_brace = closing_brace or "}"
    escape_char = escape_char == nil and true or escape_char
    starting_index = starting_index or 1

    if #opening_brace ~= 1 or #closing_brace ~= 1 then
        escape_char = false
    end

    local layer = 0
    local esc = "\\" .. opening_brace
    local esc2 = "\\" .. closing_brace

    if escape_char then
        text_bl = text_bl:gsub(esc, "🬍🬘"):gsub(esc2, "🬮🭕")
    end

    local len = #text_bl


    for i = 1, len do

        if i < starting_index then
            -- continue
        else
            local char = text_bl:sub(i, i)
            if char == opening_brace then
                layer = layer + 1
            end
            if char == closing_brace then
                layer = layer - 1
            end
            if i == index then
                return layer
            end
        end
    end

    if index == -1 then
        return layer
    else
        error("Your index was out of bounds.")
    end
end

-- fix equations. takes a string, returns a string.
local function fix_equations(eqn)

    local function multi_replace(s, replacements)
        for _, pair in ipairs(replacements) do
            local old, new = pair[1], pair[2]
            s = s:gsub(old, new)
        end
        return s
    end

    local function brace_depth(s, index)
        local depth = 0
        for i = 1, #s do
            if (i - 1) == index then -- Python's 0-indexing to Lua's 1-indexing
                break
            end
            local char = s:sub(i, i)
            if char == "{" then
                depth = depth + 1
            elseif char == "}" then
                depth = depth - 1
            end
        end
        return depth
    end

    ---Returns how deep we are, left to right.
    ---Assumes the start token is the backslash, and counts everything BEFORE index.
    ---@param s string
    ---@param index integer -- 1-based index (Lua)
    ---@return integer
    local function left_right_depth(s, index)
        local depth = 0
        local left = "\\left"
        local right = "\\right"
        local longer = math.max(#left, #right)
        local i = 1
        while i <= #s do
            if i == index then
                return depth
            end
            local substr = s:sub(i, i + longer - 1)
            if substr:sub(1, #left) == left then
                depth = depth + 1
            elseif substr:sub(1, #right) == right then
                depth = depth - 1
            end
            i = i + 1
        end
        return depth
    end

    local function fix_vectors_again(txt)
        local arg1 = "overset{⃑}"
        local replace1 = "mathbf"
        -- Escape the backslash for Lua patterns
        local pattern = "\\" .. arg1
        local replacement = "\\" .. replace1
        -- Use gsub for global substitution
        local x = txt:gsub(pattern, replacement)
        return x
    end

    local function fix_accents(text)
    -- Find the next closing bracket
        local function find_next_closing_bracket(text_fncb, index)
            local skip_fncb = 1
            while true do
                local ind = find_nth(text_fncb, "}", skip_fncb, index)
                if ind == -1 then
                    return -1
                end
                if text_fncb:sub(ind - 1, ind - 1) == "\\" then
                    skip_fncb = skip_fncb + 1
                    -- goto continue
                elseif bracket_layers(text_fncb, ind, nil, nil, nil, index) ~= -1 then
                    skip_fncb = skip_fncb + 1
                    -- goto continue
                else
                    return ind
                end
                -- ::continue::
            end
        end

        -- Return the position of the closing brace where the local environment ends
        ---@param text_local_env_end string
        ---@param index number
        ---@return number
        local function local_env_end(text_local_env_end, index)
            local n = 1
            while true do
                local closest_bracket = find_nth(text_local_env_end, "}", n, index)
                if closest_bracket == -1 then
                    error("Opening bracket without a closing bracket detected")
                end
                local b_layer = bracket_layers(text_local_env_end, closest_bracket, nil, nil, nil, index)
                if b_layer == 0 then
                    return closest_bracket
                else
                    n = n + 1
                end
            end
            return -1
        end

        -- Underbrace replacement
        local skip = 1
        while true do
            local overset_ind = find_nth(text, "\\overset", skip)
            if overset_ind == -1 then
                break
            end
            local overset_end = local_env_end(text, overset_ind)
            local contents = text:sub(overset_ind + #("\\overset") + 1, overset_end - 1)
            
            local pattern_1 = "}{︸}}"
            local pattern_2 = "}{´©©}}"
            if startswith(text:sub(overset_end), pattern_1) then
                text = text:sub(1, overset_ind - 1) .. "\\underbrace{" .. contents .. "}}" .. text:sub(overset_end + #pattern_1)
            elseif startswith(text:sub(overset_end), pattern_2) then
                text = text:sub(1, overset_ind - 1) .. "\\underbrace{" .. contents .. "}}" .. text:sub(overset_end + #pattern_2)
            else
                skip = skip + 1
            end
        end

        -- weird left arrow
        text = text:gsub("\\overset{⃐}", "\\mathbf")

        -- overleftrightarrow replacement
        skip = 1
        while true do
            local over_lra = "\\overleftrightarrow{}}{"
            local os_ind = find_nth(text, "\\overset{", skip)
            if os_ind == -1 then
                break
            end
            local os_ind_after = os_ind + #("\\overset{")
            if text:sub(os_ind_after, os_ind_after + #over_lra - 1) == over_lra then
                local ending = find_next_closing_bracket(text, os_ind_after + #over_lra)
                assert(ending ~= -1)
                local contents = text:sub(os_ind_after + #over_lra, ending - 1)
                text = text:sub(1, os_ind - 1) .. "\\overleftrightarrow{" .. contents .. text:sub(ending)
            else
                skip = skip + 1
            end
        end

        return text
    end

    local function aug_matrix_spacing(__text)
        local __old = "\\end{matrix}\\mid\\begin{matrix}"
        local __new = "\\end{matrix}\\;\\middle|\\;\\begin{matrix}"
        return __text:gsub(__old, __new)
    end

    local function extract_ms_equation_substrings(s_sub)
        -- Convert an equation in MS Word form with no conflicting braces into a list of equations.
        -- ASSUMPTIONS: No spaces, well-formed
        -- If the equation isn't well-formed, immediately give up.
        local stack = {}
        local result = {}
        local depth = 0
        local previous_char = nil
        local i = 1
        local len = #s_sub
        while i <= len do
            local char = s_sub:sub(i, i)
            if char == '{' then
                if depth == 0 then
                    if previous_char ~= '}' and previous_char ~= nil then
                        return {}
                    end
                    table.insert(stack, "")
                else
                    stack[#stack] = stack[#stack] .. char
                end
                depth = depth + 1
            elseif char == '}' then
                depth = depth - 1
                if depth == 0 and #stack > 0 then
                    table.insert(result, table.remove(stack))
                elseif #stack > 0 then
                    stack[#stack] = stack[#stack] .. char
                end
            elseif #stack > 0 then
                stack[#stack] = stack[#stack] .. char
            else
                if previous_char == '}' and (char == '_' or char == '^') then
                    return {s_sub}
                end
                table.insert(result, s_sub:sub(i))
                return result
            end
            previous_char = char
            i = i + 1
        end
        return result
    end
    
    local function generate_align_from_equations(sub_strs)
        if #sub_strs <= 1 then
            if #sub_strs == 1 then
                return sub_strs[1]
            else
                return ""
            end
        end

        local str_builder = {}

        local hierarchy = {
            {"\\iff", "\\Leftrightarrow", "\\Rightarrow", "\\implies", "\\Leftarrow"},
            {"<", ">", "\\leq", "\\geq", "\\approx"},
            {"\\subset", "\\subseteq", "\\not\\subset"},
            {"\\neq"}
        }

        local function add_and_to_symbol(text)
            local target_index = 1
            local target_precedence = #hierarchy
            for j = 1, #text do
                if brace_depth(text, j) == 0 and left_right_depth(text, j) == 0 then
                    for k, row in ipairs(hierarchy) do
                        if k > target_precedence then
                            -- goto continue_row
                        else
                            for _, symbol in ipairs(row) do
                                if text:sub(j, j + #symbol - 1) == symbol then
                                    target_index = j
                                    target_precedence = k
                                end
                            end
                        end
                    end
                end
            end
            return text:sub(1, target_index - 1) .. " &" .. text:sub(target_index)
        end

        for i, line in ipairs(sub_strs) do
            local last = i == #sub_strs
            local trailing = last and "" or " \\\\"
            local string_so_far = add_and_to_symbol(line)
            table.insert(str_builder, string_so_far .. trailing)
        end

        return "\\begin{aligned}\n" .. table.concat(str_builder, "\n") .. "\n\\end{aligned}"
    end


    local function fix_equation_align_case(eqn_al)
        eqn_al = eqn_al:match("^%s*(.-)%s*$") -- trim
        local max_len = math.huge

        if #eqn_al == 0 or eqn_al:sub(1, 1) ~= "{" then
            local tm = nil
            return eqn_al
        end

        local sub_strs = extract_ms_equation_substrings(eqn_al)
        return generate_align_from_equations(sub_strs)
    end


    eqn = multi_replace(eqn, {
        {"\n", " "},
        {"\\{", "\\lbrace"},
        {"\\}", "\\rbrace"},
        {"≢", "\\not\\equiv "},
        {"\\overrightarrow", "\\vec"}
    })

    eqn = fix_vectors_again(eqn)
    eqn = fix_accents(eqn)
    eqn = aug_matrix_spacing(eqn)
    -- eqn = eqn:gsub("^{'}", " '")
    eqn = string.gsub(eqn, "–", "-")
    eqn = string.gsub(eqn, "%^{'}", " '")
    eqn = fix_equation_align_case(eqn)

    return eqn .. " "
end

-- local ab = [[
-- \overset{Ôâæ}{a} + \overset{Ôâæ}{b} = \overset{Ôâæ}{c}
-- ]]
-- print(fix_equations(ab))

function Math(elem)
    if elem.text ~= nil then
        elem.text = fix_equations(elem.text)
    end
    return elem
end