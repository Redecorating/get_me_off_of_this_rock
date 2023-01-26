# Entities
#
# (c) 2022 Orlando Chamberlain
#
# 

import compositor
import inventory
import status
import event
import map
from collections import namedtuple, OrderedDict
from random import randint, choice
import pygame

person_max_hp = 10

resource_names = ("food", "medication", "ammunition")
resource_start_value = 50

class __Entity:
	def __super_init(self, tile):
		self.tile = tile

		self.map = tile.map
		self.data = {}

		self.comp = compositor.Image((30,50))
		self.comp.set_colour((205, 205, 205))
		self.__enter_tile(tile)
	
	def __enter_tile(self, tile):
		self.tile = tile
		self.tile.entities.append(self)
		pos = self.tile.rand_pos()

		self.tile_link = compositor.Link(self.tile.comp, self.comp, pos, 11)

	def __exit_tile(self):
		assert self.tile_link, "Can't exit tile when not in a tile."
		self.tile.entities.remove(self)
		self.tile_link.remove()
		self.tile = None

	def __move(self, ops):
		tile = self.tile
		while ops:
			op = ops.pop(0)
			coords = map.adj(tile, op)

	def move(self, tile):
		"""Move the entity towards direction distance squares"""
		self.__exit_tile()
		self.__enter_tile(tile)

class Creature(__Entity):
	"""an entity on the map

	tile: tile the entity is on
	name: string name of entity
	hp: int
	defence: int
	attack: int
	parent: __Entity_Group subclass instance"""
	def __init__(self, tile, name, hp, defence, attack, parent, loot=[]):
		self._Entity__super_init(tile)

		self.name = name
		self.hp = hp
		self.max_hp = hp
		self.defence = defence
		self.attack = attack
		self.loot = loot

		self.parent = parent
		self.parent.entities.append(self)

	def damage(self, damage):
		"""make creature sustain damage"""
		self.hp -= damage
		if self.hp <=0:
			self.die()
			return 1
		return 0

	def die(self):
		"""make the creature die"""
		self._Entity__exit_tile()
		self.parent.child_died_callback(self)

	def __str__(self):
		return self.name + " " + str(self.tile)

class __Entity_Group:
	def __super_init(self, tile):
		self.tile = tile
		self.last_move = None
		self.entities = []

	def __move(self, bearing):
		"""Move entities towards bearing

		bearing: string (e.g. "NE")"""

		self.last_move = bearing
		self.tile = self.tile.map.get_tile(map.adj(self.tile, bearing))
		for e in self.entities:
			e.move(self.tile)

class NPC(__Entity_Group):
	"""Non Player Character

	tile: tile
	colour: (int,int,int)
	count: int"""
	def __init__(self, tile, event):
		self._Entity_Group__super_init(tile)

		self.event = event

		entity_data = event.event["entity"]
		stats = entity_data["stats"]

		self.movement_tendency = entity_data["movement"]

		self.name = entity_data["name_plural"]

		for i in range(entity_data["number"]):
			Creature(self.tile, entity_data["name_single"]+" "+str(i+1),
					stats["hp"], stats["def"], stats["atk"], self,
					entity_data["loot"])
			self.entities[-1].comp.set_colour(entity_data["colour"])

		self.tile.map.entities.append(self)
	
	def rm_entity(self, entity):
		self.entities.remove(entity)

		if not self.entities:
			#we are die
			self.tile.map.entities.remove(self)
			self.event.tile_deactivate()

	def move(self, bearing):
		"""move a square to bearing"""
		self.event.tile_deactivate()
		self._Entity_Group__move(bearing)
		self.event.tile = self.tile
		self.event.tile_activate()

	def do_turn(self):
		"""NPC takes a turn"""
		if not randint(0,self.movement_tendency):
			bearing = choice(tuple(map.directions.keys()))
			self.move(bearing)

	def child_died_callback(self, child):
		self.rm_entity(child)

class Player(__Entity_Group):
	"""Player object

	_map: map"""
	def __init__(self, _map):
		self.completed_events = []
		self.actions = {}
		self.data = {}

		self.current_event = None

		self.turn_number = 0

		tile = _map.get_tile((0,0))
		self._Entity_Group__super_init(tile)

		self.add_person("Greeg")
		self.add_person("Grank")

		self.has_had_low_food = False
		self.has_no_food = False

		self.inventory = []

		self.resources = OrderedDict()
		for resource in resource_names:
			self.resources[resource] = resource_start_value

		self.status_win = status.Status_Bar(self)
		self.status_win.show()

		self.inventory_win = inventory.Inventory(self)

		self.actions["MOVE"] = [(k, (self.move, d,)) for k, d in
				((pygame.K_q, "NW"), (pygame.K_w, "N"),
				 (pygame.K_e, "NE"), (pygame.K_a, "SW"),
				 (pygame.K_s, "S"),  (pygame.K_d, "SE"))]

		self.actions["INV"] = [(pygame.K_i, (self.inventory_win.show,))]

		for tile in self.tile.adj.values():
			tile.set_vision(map.VISION_LOTS)
		self.tile.set_vision(map.VISION_LOTS)

	def add_person(self, name):
		"""add a person to the party"""
		person = Creature(self.tile, name, person_max_hp, 0,2, parent=self)
		person.comp.set_colour((255, 255, 255))

	def move_back(self):
		if self.last_move:
			bearing = map.opposite[self.last_move]
			self.move(bearing)

	def move(self, bearing):
		"""Move player towards bearing

		bearing: string (e.g. "NE")"""
		self._Entity_Group__move(bearing)
		self.turn_attrition()
		self.tile.map.do_npc_turns()
		self.tile.map.centre(self.tile)

		for tile in self.tile.adj.values():
			tile.set_vision(map.VISION_LOTS)
		self.tile.set_vision(map.VISION_LOTS)

		for event in self.tile.events:
			self.tile_event = event
			event.run(self)

	def turn_attrition(self):
		"""Hunger tick"""
		self.turn_number += 1
		if not self.has_had_low_food:
			if self.resources["food"] <= len(self.entities)*11:
				event.Event("Hunger0").run(self)
				self.has_had_low_food = True

		# TODO: put this in some order?
		for person in self.entities.copy():
			if self.resources["food"]:
				self.resources["food"] -= 1
			else:
				person.damage(1)
				# run event?

		if self.resources["food"]:
			if self.has_no_food:
				self.has_no_food = False
		else:
			if not self.has_no_food:
				self.has_no_food = True
				event.Event("Hunger1").run(self)
	
	def child_died_callback(self, child):
		self.entities.remove(child)
		if not self.entities:
			event.Event("Death0").run(self)

