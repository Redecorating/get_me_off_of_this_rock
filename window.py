# Window
#
# (c) 2022 Orlando Chamberlain
#
# Create windows

import compositor

# These macros create elements to put on a window.
def Text(size, text, font_size=None):
	img = compositor.Image(size, alpha=True)
	img.set_text(text, font_size)
	return (img.size, img)

def Gap(size):
	return (size, None)

def Window(size, layout):
	comp = compositor.Composite(size, alpha=True)
	bg = compositor.Image(size)
	bg.set_colour((255,255,255))
	compositor.Link(comp, bg, (0,0),0)

	y = 0
	for line in layout:
		x = 0
		max_y_increment = 0
		for size, element in line:
			if element:
				compositor.Link(comp, element, (x,y), 8)
			x += size[0]
			max_y_increment = max(max_y_increment, size[1])
		y += max_y_increment

	return comp

