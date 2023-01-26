# Map
#
# (c) 2022 Orlando Chamberlain
#
# Data structures for the map and its tiles.
# The tiles know which tiles they are next to.
#

import compositor
import event
import entities
from collections import namedtuple
from random import choice, randint, random
from math import pi, cos, sin
import pygame

Coord = namedtuple("Coord", ["x","y"])

VISION_NONE = 0
VISION_SOME = 1
VISION_LOTS = 2

# For regular Hexagon:
# height = sqrt(3)/2 * width

tile_rect_dims = Coord(400,320)

directions = {
	"N": Coord(1,0),
	"NE": Coord(0,1),
	"NW": Coord(0,-1),
	"SE": Coord(-1,1),
	"SW": Coord(-1,-1),
	"S": Coord(-1,0),
	}

opposite = {
	"N": "S",
	"NE": "SW",
	"SE": "NW",
	"S": "N",
	"SW": "NE",
	"NW": "SE"
	}

# tiles x y
# +'ve x is North, -'ve x is South
# -'ve y is West, +'ve y is East
#
# ["SW", "NW", ...  ],
# ["S",  self, "N"  ],
# ["SE", "NE", ...  ]
#
# Due to hexagons not being squares, for even y values the West and East tiles
# are one further to positive x compared to the example above.

def adj(tile, direction):
	"""Return coords of adjacent tile in that direction

	tile: tile
	direction: string"""
	dir_ = directions[direction]

	x = tile.coords.x+dir_.x
	y = tile.coords.y+dir_.y

	# Hexagons aren't squares.
	if tile.coords.y%2 == 0 and len(direction) == 2:
		x += 1

	x %= tile.map.size.x
	y %= tile.map.size.y

	return Coord(x,y)

class Tile:
	"""a map tile

	full_map: parent map
	coords: (x,y) on parent map"""
	def __init__(self, full_map, coords):
		self.map = full_map
		self.coords = Coord(*coords)

		self.last_known_entities = []
		self.entities = []
		self.events = []
		self.adj = {}
		self.vision = VISION_NONE
		self.link_to_map = None

		self.map.tiles[coords.x][coords.y] = self

		self.comp = compositor.Composite(tile_rect_dims, alpha=True)

		colour = [randint(50,150)]*3
		self.bg = compositor.Image(tile_rect_dims, alpha=True)
		self.bg.set_colour(colour)
		self.bg.set_mask(compositor.hex_mask)

		compositor.Link(self.comp, self.bg, (0,0), 10)
		self.__relink()

	def __show_on_map(self):
		if self.link_to_map == None:
			self.link_to_map = compositor.Link(self.map.comp,
					self.comp, self.__get_pixel_coords(),
					self.coords.x + self.coords.y * self.map.size.x)

	def __hide_on_map(self):
		if self.link_to_map:
			self.link_to_map.remove()
			self.link_to_map = None

	def set_vision(self,level):
		"""Show or hide this til:"""
		# TODO: why can't I use VISION_SOME etc??
		match level:
			case 2:
				self.__show_on_map()
			case 1:
				# TODO
				pass
			case 0:
				self.__hide_on_map()


	def __get_pixel_coords(self):
		py = tile_rect_dims.y * (self.map.size.x - self.coords.x - 0.5)
		px = (tile_rect_dims.x * self.coords.y * 3) // 4
		# even y coord -> shift north
		if self.coords.y % 2 == 0:
			py -= tile_rect_dims.y // 2

		return Coord(px, py)

	def __relink(self):
		for bearing in directions.keys():
			coords = adj(self,bearing)

			tile = self.map.tiles[coords.x][coords.y]

			if tile:
				self.__link(tile, bearing)
				tile.__link(self, opposite[bearing])

	def __link(self, tile, dir_):
		self.adj[dir_] = tile

	def __str__(self):
		if self.entities:
			return "<##>"
		else:
			return "<  >"
	
	def rand_pos(self):
		angle = random() * pi * 2
		dist = random() * tile_rect_dims.y * 0.5 * 0.8
		x = dist * cos(angle) + tile_rect_dims.x / 2
		y = dist * sin(angle) + tile_rect_dims.y / 2
		return Coord(x,y)

class Map:
	"""Map, consisting of tiles

	size: (x,y), x is odd, y is even"""
	def __init__(self, size):
		self.size = Coord(*size)

		x = int((self.size.y * 0.75 + 0.25) * tile_rect_dims.x)
		y = int((self.size.x + 0.5) * tile_rect_dims.y)
		self.size_px = Coord(x,y)
		self.comp = compositor.Composite(self.size_px)

		self.entities = []

		assert type(self.size.x) == int and \
				self.size.x > 0 and \
				self.size.x % 2 == 1, \
				"Map must be an positive odd integer of tiles high."
		assert type(self.size.y) == int and \
				self.size.y > 0 and \
				self.size.y % 2 == 0, \
				"Map must be an positive even integer of tiles wide."

		map_tile_count = self.size.x*self.size.y

		self.tiles = [
					[None]*self.size.y
					for _ in range(self.size.x)
				]

		self.centred_tile_coords = (0,0)
		# coords of ungenerated tiles
		self.ungenerated = [Coord(i%self.size.x,i//self.size.x)
			for i in range(map_tile_count)]

		self.__fill()

		self.__arrange_tiled_map()

	def get_tile(self, coord):
		"""return tile at coord

		coord: (x,y)"""
		coord = Coord(*coord)
		return self.tiles[coord.x][coord.y]

	def centre(self, tile):
		"""Centre the map on tile."""
		display_link = self.tiled_map.parents[0]
		orig_pos_px = display_link.pos

		# Handle map looping
		shifts = [tile_rect_dims.x // 4 - self.size_px.x,
				  self.size_px.y - tile_rect_dims.y // 2]

		x_orig, y_orig = self.centred_tile_coords
		y, x = tile.coords
		self.centred_tile_coords = (x,y)

		dx = x - x_orig
		dy = y - y_orig

		# Why doesn't python have pointers to ints!
		for d, shift_index in ((dx, 0), (dy, 1)):
			if d not in (-1, 0, 1):
				if d > 1:
					shifts[shift_index] *= -1
				# Else, it stays positive
			else:
				shifts[shift_index] = 0

		# Hexagons aren't squares.
		if x%2 == 0:
			y += 0.5
		y += 0.5
		x -= 0.5

		tile_pos = Coord(x, y)

		pos_px = Coord((- 0.5 - tile_pos.x) * (tile_rect_dims.x * 0.75),
				-(self.size.x - tile_pos.y) * tile_rect_dims.y)

		display_link.move((pos_px.x + shifts[0],
						   pos_px.y + shifts[1]),
						  steps=10, duration=0.1)
		display_link.move(pos_px)

	def __arrange_tiled_map(self):
		# We will show a section of the tiled map to the user. This will be
		# tiled so that if the map is centred on any tile, there will be
		# copied sections of the map creating the illusion of a edgeless map.

		size_x = self.size_px.x - tile_rect_dims.x + compositor.resolution[0]
		size_y = self.size_px.y - tile_rect_dims.y + compositor.resolution[1]
		self.tiled_map = compositor.Composite((size_x, size_y), alpha=True)

		base_pos = Coord(compositor.resolution[0]//2 - self.size_px.x,
				compositor.resolution[1]//2 - self.size_px.y)

		offsets = ((0,0),(0,1),(0,2),
				(1,0),(1,1),(1,2),
				(2,0),(2,1),(2,2))

		for i, offset in enumerate(offsets):
			pos = Coord(base_pos.x + (self.size_px.x - tile_rect_dims.x // 4) * offset[0],
					base_pos.y + (self.size_px.y - tile_rect_dims.y // 2) * offset[1])
			compositor.Link(self.tiled_map, self.comp, pos, i)

	def __gen_tile(self, coords=None):
		if self.ungenerated:
			if coords == None:
				coords = choice(self.ungenerated)

			if self.tiles[coords.x][coords.y]:
				print("Requested an already generated tile.")
				return coords

			tile = Tile(self, coords)
			self.ungenerated.remove(coords)
			return coords
		else:
			print("All tiles have already been generated.")

	def __distribute_events(self):
		# TODO: don't hardcode this
		events = ["Rock0", "Rock0", "Hole0", "Tree0", "Tree0",
				  "Greg0", "Ship0", "Goop0", "Wolf0", "Slime0",
				  "Cave0", "Hole0"]
		event.Event("Wreck0", self.tiles[0][0])

		while events:
			tile = choice(choice(self.tiles))
			if not tile.events:
				event.Event(events.pop(0), tile=tile)

	def do_npc_turns(self):
		for npc in self.entities:
			npc.do_turn()

	def print_map(self):
		"""print a representation of map to terminal"""
		print()
		for y in range(self.size.y):
			if not y%2:
				print(end=" "*2)
			for x in range(self.size.x):
				g = self.tiles[x][y]
				print(g, end=' ')
			print()

	def __fill(self):
		while self.ungenerated:
			self.__gen_tile()
		self.__distribute_events()

