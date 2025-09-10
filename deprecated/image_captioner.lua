--[[
Makes all images with ALT text figures. The ALT text will act as the figure number.
Images with NO ALT text will not be affected.
]]

function Image(img)
  -- If the image has alt text (content), set its title to 'fig:'
  if img.caption and #img.caption > 0 then
    img.title = 'fig:'
  end
  return img
end