local List = require 'pandoc.List'
local theorem_environments

function to_str(el)
    return el[1].text
end

local title_header 
function Meta(meta)
    if meta["theorem-environments"] then
        theorem_environments = meta["theorem-environments"]:map(to_str)
    end
    if title_header ~= nil and title_header ~= "" then
        meta.title = title_header
    end
    print('meta')
    theorem_environments = {'theorem'}
    return meta
end


function header_string(header)
    local r = {}

    for _, inline in ipairs(header.content) do
        if inline.t == "Str" then
            table.insert(r, inline.text)
        else
            table.insert(r, " ")
        end
    end
    return table.concat(r)
end

-- This function is called on each block in the document.
--
local in_theorem = false
local env_name = ""
local counter = 0
local header_label = ""
local label, environment
function transform(block)
    print('transform')
    if block.tag == 'Header' then
        if title_header == nil and block.level == 1 then
            title_header = header_string(block)
            return {}
        elseif title_header == nil then
            title_header = ""
        end


        local str = header_string(block)



        for i, env in ipairs(theorem_environments) do 
            local env = env:sub(1, 1):upper() .. env:sub(2):lower()
            ev, label = str:match("^(" .. env .. ")%s?%(?(.-)%)?$")
            if ev ~= "" then
                environment = env
                break
            end
        end
    end
    

    if not in_theorem then
        if block.tag == "Header" and block.level == 3 and environment ~= nil then
            in_theorem = true
            environment = block.content[1].text:lower()
            counter = counter + 1
            
            if block.identifier == environment then
                header_label = "" .. environment .. ":" .. tostring(counter)
            else
                header_label = "" .. environment .. ":" .. block.identifier
            end
            return {}       
        end
    else
        if label ~= nil and label ~= "" then
            block_start = pandoc.RawInline('latex', "\\begin{" .. environment .. "}[" .. label .. "] \\label{" .. header_label .. "}\n")
        else
            block_start = pandoc.RawInline('latex', "\\begin{" .. environment .. "} \\label{" .. header_label .. "}\n")
        end
        local block_end = pandoc.RawInline('latex', "\n\\end{" .. environment .. "}")

        environment = nil
        label = nil

    
        table.insert(block.content, 1, block_start)
        table.insert(block.content, block_end)


        
        in_theorem = false


        return block
    end

    return block
end

function Pandoc(doc)
    doc.blocks = doc.blocks:walk({Block = transform})
    return doc
end

function Emph(el)
    if el.content[1].text == "Proof." then
        return pandoc.RawInline('latex', '\\begin{proof}\n')
    elseif el.content[1].text == "Q.E.D" then  
        return pandoc.RawInline('latex', '\n\\end{proof}')
    end
end

function Para(para)
    --- handle equation labels

    local labels = {}
    local previous_was_tex = false
    for i, v in ipairs(para.content) do
        if previous_was_tex and v.tag == "Str" and string.sub(v.text, 1, 1) == "^" then
            labels[i - 1] = string.sub(v.text, 2, -1)
        end
        
        if v.tag == 'RawInline' and v.format == 'latex' then
            previous_was_tex = true
        else
            previous_was_tex = false
        end
    end
    for i, label in pairs(labels) do
        para.content[i].text = string.gsub(para.content[i].text, "\\begin{equation%*}", "\\begin{equation} \\label{" .. label .. "}" )
        para.content[i].text = string.gsub(para.content[i].text, "\\end{equation%*}", "\\end{equation}")
    end
    local new_content = {}
    for i, v in ipairs(para.content) do 
        if labels[i - 1] == nil then
            table.insert(new_content, v)
        end
    end
    return pandoc.Para(new_content)
end

function Math(math)
    if math.mathtype == "DisplayMath" then
        return pandoc.RawInline("latex", "\n\\begin{equation*}" .. math.text .. "\\end{equation*}\n")
    end
end


return {
    {Math = Math},
    {Para = Para},
    {Meta = Meta},
    {Pandoc = Pandoc},
}