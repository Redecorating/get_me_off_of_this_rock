# Compositor
#
# (c) 2022 Orlando Chamberlain
#
# Put images together
# Handle their ordering
# Put a final image on the display

import pygame.gfxdraw
import pygame
import time

resolution = (1920,1080)
caption = "Get Me Off of this Rock!"

def get_font(size):
	return pygame.font.Font(pygame.font.get_default_font(), size)

def __find_composites(composite, found):
	for layer in composite.layers:
		if layer._child not in found:
			found.append(layer._child)
			__find_composites(layer._child, found)

def force_outdate(composite):
	"""Force a composite to mark all of its layers as needing updates"""
	for layer in composite.layers:
		composite.outdated.append(layer)
		if composite.damage:
			composite.damage.union_ip(layer.rect)
		else:
			composite.damage = layer.rect.copy()

def force_deep_outdate(composite):
	"""Force a composite to mark all of its layers as needing updates, recursively"""
	found = [composite]
	__find_composites(composite, found)
	for comp in found:
		force_outdate(comp)

def hex_mask(comp):
	"""Cut corners of rectangle out to make hexagon

	surf: surface"""
	w, h = comp.surf.get_size()
	for x1,y1,x2,y2,x3,y3 in (
			(0,0,	w//4,0,		0,h//2), # Top left
			(0,h,	w//4,h,		0,h//2), # Bottom left
			(w,0,	3*(w//4),0,	w,h//2), # Top right
			(w,h,	3*(w//4),h,	w,h//2)):# Bottom right
		pygame.gfxdraw.filled_trigon(comp.surf, x1,y1,x2,y2,x3,y3, (0,0,0,0))

class Link:
	"""defines where a composite is put on another composite

	parent: composite the child is put on
	child: composite that is put on the parent
	pos: (x,y) position of the child on the parent
	order: float of order to render the parents children"""
	def __init__(self, parent, _child, pos, order):
		self.parent = parent
		self._child = _child
		self.pos = pos
		self.order = order

		self.rect = _child.surf.get_rect()

		parent.layers.append(self)
		parent.layers.sort(key=lambda x: x.order)
		_child.parents.append(self)
		self.outdate(self.rect)

	def move(self, pos, steps=1, duration=0):
		assert steps >= 1
		assert duration >= 0
		orig_pos = self.pos
		offset_x = pos[0] - orig_pos[0]
		offset_y = pos[1] - orig_pos[1]

		for i in range(1,steps+1):
			inc_pos_x = orig_pos[0] + offset_x * (i/steps)
			inc_pos_y = orig_pos[1] + offset_y * (i/steps)
			self.__move((inc_pos_x, inc_pos_y))
			compositor_instance.update()
			time.sleep(duration/steps)
		self.pos = pos


	def __move(self,pos):
		self.pos = pos
		damage = self.rect.move(self.pos)
		self.parent.outdate(None, damage=self.rect.move(self.pos))

	def remove(self):
		"""remove and unlink the link from parent and child.

		informs parent that it needs to rerender that bit"""
		damage = self.rect.move(self.pos)

		self._child.parents.remove(self)
		self.parent.layers.remove(self)
		self.parent.outdate(None, damage=damage)

	def update(self):
		"""Updates the child"""
		self._child.update()

	def outdate(self, damage):
		"""Our child has been modified, inform parents

		damage: rect of child modified"""
		self.parent.outdate(self, damage=damage.move(self.pos))

class __Composite:
	def __super_init(self, size, surf=None, alpha=True):
		self.flags = pygame.SRCALPHA * alpha
		self.size = size
		self.no_pickle = False
		self.custom_surf = bool(surf)

		self.parents = [] # Links

		self.__init_surf(surf=surf)

		self.rect = self.surf.get_rect()

	def __getstate__(self):
		parents = self.parents.copy()
		for parent in self.parents:
			if parent.parent.no_pickle:
				parents.remove(parent)
		data = self.__dict__.copy()
		data.pop("surf")
		data["parents"] = parents
		return data

	def __super_setstate(self, data):
		for key in data.keys():
			self.__setattr__(key,data[key])
		if not self.custom_surf:
			self.__init_surf()

	def __init_surf(self, surf=False):
		if surf:
			self.surf = surf
		else:
			self.surf = pygame.surface.Surface(self.size, flags=self.flags)

	def unlink(self):
		"""Remove all links to ourself"""
		for link in self.parents + self.layers:
			link.remove()

class Composite(__Composite):
	def __init__(self, size, surf=None, alpha=True):
		"""A composite of images

		size: (x,y)
		surf: (optional) use this surface instead of generating our own. This won't be restored on save load
		alpha: bool, enables alpha channel"""
		self.layers = [] # Links
		self.outdated = [] # Link
		self.damage = False
		self._Composite__super_init(size, surf=surf, alpha=alpha)

	def __setstate__(self, data):
		self._Composite__super_setstate(data)

	def update(self):
		"""Pull changes from self.outdated"""
		if self.damage:
				to_blit = []

				# TODO: Only do this for damaged area
				self.surf.fill((0,0,0,0))
				for layer in self.outdated:
					layer.update()

				for layer in self.layers:
					#damage = self.damage.move(-layer.pos[0], -layer.pos[1])
					#damage.clip(layer._child.surf.get_rect())
					to_blit.append((layer._child.surf, layer.pos))#, damage)) #FIXME

				if to_blit:
					self.surf.blits(to_blit)

				self.outdated.clear()
				self.damage = False

	def outdate(self, trigger, damage):
		"""flag composite as needing update

		If no trigger, yes damage, link was removed.
		Informs parent links of the damaged area.
		Add links+areas this composite needs updated to self.outdated

		trigger: Link or None
		damage: rect of parent surf that's outdated"""
		if self.damage:
			self.damage.union_ip(damage)
		else:
			self.damage = damage

		if trigger:
			self.outdated.append(trigger)

		# Inform parents
		# TODO: only do this if len(self.outdated) < 2 or damaged area changed
		for parent in self.parents:
			parent.outdate(self.damage.move(parent.pos))

class Image(__Composite):
	def __init__(self, size, alpha=True):
		"""Image created with colour, text and a mask.

		Each one of those are optional and can be changed at runtime."""
		self.layers = ()
		self.__colour = (0,0,0,0)
		self.__text = "", (0,0), 10
		self.__mask = None
		self._Composite__super_init(size, alpha=alpha)

	def __setstate__(self, data):
		self._Composite__super_setstate(data)
		self.update()

	def set_colour(self, colour):
		"""Set image's bacground to colour"""
		self.__colour = colour
		self.outdate()

	def __apply_colour(self):
		self.surf.fill(self.__colour)

	def set_text(self, text, size=None, offset=None):
		"""Set text to be put on the image"""
		if not size:
			size = self.__text[2]
		if not offset:
			offset = self.__text[1]
		self.__text = (text, offset, size)
		self.outdate()

	def __wrap_text(self, text, font):
		input_lines = text.split("\n")
		max_width, max_height = self.surf.get_size()
		# TODO: %@ are taller, does this matter?
		# TODO: If not enough space, put "..." at end and return extra text.
		lines = []
		for input_line in input_lines:
			words = input_line.split(" ")
			line = []
			width = 0
			while words:
				word = words[0].replace("\t", "  ")
				word_width = font.size(word+" ")[0]
				if width == 0 or (width + word_width) <= max_width:
					line.append(word)
					words.pop(0)
					width += word_width
				else:
					lines.append(" ".join(line))
					line.clear()
					width = 0
			lines.append(" ".join(line))
		return lines

	def __apply_text(self):
		text, offset, size = self.__text
		offset = list(offset)
		if text:
			font = get_font(size)
			lines = self.__wrap_text(text, font)
			line_height = font.get_height()
			for line in lines:
				text_surf = font.render(line, True, (0,0,0))
				self.surf.blit(text_surf, offset)
				offset[1] += line_height

	def set_mask(self, func=None, args=(), kwargs={}):
		"""Set the function to be used as the mask"""
		if func:
			self.__mask = (func, args, kwargs)
		else:
			self.__mask = None
		self.outdate()

	def __apply_mask(self):
		if self.__mask:
			func, args, kwargs = self.__mask
			func(self, *args, **kwargs)

	def update(self):
		"""Regenerate image contents"""
		self.__apply_colour()
		self.__apply_text()
		self.__apply_mask()

	def clear(self):
		"""Reset to black/transparent"""
		self.__colour = (0,0,0,0)
		self.__text = ""
		self.__mask = None
		self.outdate()

	def outdate(self):
		"""Tell parents we are modified"""
		# TODO: only do this if len(self.outdated) < 2 or damaged area changed
		for parent in self.parents:
			parent.outdate(self.surf.get_rect().move(parent.pos))

class Compositor:
	"""Manages display"""
	def __init__(self):
		pygame.display.set_caption(caption)
		self.display_surf = pygame.display.set_mode(resolution)

		self.display = Composite(resolution, surf=self.display_surf)
		self.display.no_pickle = True

	def update(self):
		"""Pull updates from composites, then put them on the screen"""
		self.display.update()
		pygame.display.update()

