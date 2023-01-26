# Event
#
# (c) 2022 Orlando Chamberlain
#
# Show event window, run events.

from input_manager import im, help_event
import compositor as comp
import window as win
import storage
import combat
import entities
from collections import defaultdict
from copy import deepcopy
import pygame

window_size = (600,900)
title_font = 36
title_size = (window_size[0], title_font + 10)
desc_size = (window_size[0], window_size[1] - title_size[1])

events = storage.load_events()
event_layer = comp.Composite(comp.resolution, alpha=True)

class Event:
	def __init__(self, name, tile=None):
		self.name = name
		self.event = deepcopy(events[name])
		self.title = self.event["title"]
		self.desc = self.event["desc"]

		if "entity" in self.event.keys():
			assert tile
			self.entity_group = entities.NPC(tile, self)

		self.has_tile = False
		self.has_comp = False

		if tile:
			self.tile = tile
			self.has_tile = True
			visual = self.event.get("visual")
			if visual:
				self.has_comp = True
				self.comp = comp.Image((30,30))
				self.pos = self.tile.rand_pos()
				self.tile_show()

				colour = visual.get("colour")
				if colour:
					self.comp.set_colour(colour)
			self.tile_activate()
	
	def tile_show(self):
		"""Show event's visual on it's tile"""
		assert self.has_tile and self.has_comp, \
				"Tried to show an event on a tile when it doesn't have a tile"
		self.link = comp.Link(self.tile.comp, self.comp, self.pos,10)
	
	def tile_hide(self):
		"""Hide event's visual on it's tile"""
		assert self.has_tile and self.has_comp, \
				"Tried to hide an event on a tile when it doesn't have a tile"
		if self.link:
			self.link.remove()
			self.link = None

	def tile_activate(self):
		"""Activate an event's tile enter trigger"""
		assert self.has_tile, \
				"Tried to activate a tile trigger for event without tile."
		self.tile.events.append(self)
	
	def tile_deactivate(self):
		"""Deactivate an event's tile enter trigger"""
		assert self.has_tile, \
				"Tried to deactivate a tile trigger for event without tile."
		self.tile.events.remove(self)
	
	def remove(self):
		"""Remove an event from a tile completely"""
		self.tile_deactivate()
		if self.has_comp:
			self.tile_hide()

	def run(self, player):
		"""Put a player through an event"""
		self.player = player
		if self.player:
			player.current_event = self


		self.options = self.__filter_options(self.event["options"])

		self.window = self.__mk_window()
		y = event_layer.rect.center[1] - self.window.rect.center[1]
		comp.Link(event_layer, self.window, (y,y), 5)

		self.__register_actions()

	def __filter_options(self, all_options):
		options = all_options.copy()
		for option in all_options:
			reqs = option["reqs"]
			types = reqs.keys()
			remove = False
			if "items" in types:
				for item in reqs["items"]:
					if item not in self.player.inventory:
						remove = True
						break

			if "player_attr" in types:
				for attr in reqs["player_attr"]:
					if not self.player.__dict__[attr]:
						remove = True
						break

			if "eq" in types:
				for eq in reqs["eq"]:
					if not eval(eq):
						remove = True
						break
			if remove:
				options.remove(option)

		return options

	def __mk_window(self):
		text = [self.desc.format(e=self)]

		options = []

		for i in self.options:
			repeat = i.get("repeat")
			if repeat:
				match repeat:
					case "per_personnel":
						for person in self.player.entities:
							option = deepcopy(i)
							option["text"] = option["text"].format(person=person)
							for outcome in option["outcomes"]:
								outcome.append(person)

							options.append(option)
			else:
				options.append(i)

		for i in range(len(options)):
				text.extend(("\n",f"\t{str(i+1)}. {options[i]['text']}"))
		layout = [
					[win.Text(title_size,self.title, font_size=title_font)],
					[win.Text(desc_size, "\n".join(text), font_size=24)],
				]

		self.filtered_options = options

		return win.Window(window_size, layout)

	def __register_actions(self):
		im.push_set()
		for i in range(len(self.filtered_options)):
			key = getattr(pygame, "K_"+str(i+1))
			im.add_action(key, (self.ret, i))

	def __format_summary(self, summary):

		"""
		[Items]
			+1 Rock
			-1 Bean
		[Resources]
			-1 Medicine
		[Personnel]
			Name joined the party.
			Name died.
		[Combat]
			Greg takes 3 damage
			Wolf group takes 4 damage
			1 Wolf died
			3 Worms died
		"""
		lines = []

		# TODO: remove False entries in summary's dicts

		items = summary["items"]
		resources = summary["resources"]

		for _dict, name in ((items, "Items"), (resources, "Resources")):
			if _dict:
				lines.append(f"[{name}]")
				for item in _dict.keys():
					if _dict[item] > 0:
						lines.append(f"\t+{_dict[item]} {item}")
					elif _dict[item] < 0:
						lines.append(f"\t{_dict[item]} {item}")

		personnel = summary["personnel"]

		if personnel:
			lines.append("[Personnel]")
			for person in personnel.keys():
				assert personnel[person] == 1, "Obituaries are not implemented or used yet"
				lines.append(f"\t{person} joined the party")

		deaths = summary["deaths"]
		hp = summary["hp"]
		if hp or deaths:
			lines.append("[Combat]")
			for creature in hp.keys():
				if hp[creature] > 0:
					lines.append(f"\t{creature} loses {hp[creature]} HP")
				elif hp[creature] < 0:
					lines.append(f"\t{creature} gains {-hp[creature]} HP")

			for creature in deaths.keys():
				lines.append(f"\t{creature} dies.")

		return "\n".join(lines)

	def ret(self, n):
		a = self.window.parents[0].parent
		self.window.unlink()
		im.pop_set()
		zero_dict = defaultdict(int)

		summary = {
				"items": zero_dict.copy(),
				"resources": zero_dict.copy(),
				"personnel": zero_dict.copy(),
				"deaths": zero_dict.copy(),
				"hp": zero_dict.copy(),
				}
		if self.player:
			self.player.completed_events.append(self.name)
			if not self.player.data.get("summary"):
				self.player.data["summary"] = ""

		outcomes = self.filtered_options[n]["outcomes"]

		for outcome in outcomes:
			match outcome[0]:
				case "item_gain":
					self.player.inventory.extend(outcome[1])
					for item in outcome[1]:
						summary["items"][item] += 1

				case "item_lose":
					for item in outcome[1]:
						self.player.inventory.remove(item)
						summary["items"][item] -= 1

				case "chain":
					self.player.data["summary"] = self.__format_summary(summary)
					Event(outcome[1]).run(self.player)

				case "remove":
					self.player.tile_event.remove()

				case "set_data":
					self.player.data[outcome[1]] = outcome[2]

				case "inc_data":
					if self.player.data.get(outcome[1]) == None:
						self.player.data[outcome[1]] = 0
					self.player.data[outcome[1]] += outcome[2]

				case "resource":
					self.player.resources[outcome[1]] += outcome[2]
					summary["resources"][outcome[1]] += outcome[2]

				case "add_person":
					self.player.add_person(outcome[1])
					summary["personnel"][outcome[1]] += 1

				case "fight":
					assert self.entity_group, "Event triggered a fight but there was no linked opponent"
					combat.group_fight(self.player, self.entity_group, summary=summary)
					self.player.data["summary"] = self.__format_summary(summary)
					self.player.data["enemy"] = self.entity_group
					if not self.player.entities:
						Event("Battle2").run(self.player)
					elif self.player.data["enemy"].entities:
						Event("Battle0").run(self.player)
					else:
						Event("Battle1").run(self.player)

				case "clear_summary":
					for i in summary.values():
						i.clear()

				case "__fight":
					assert self.player.data["enemy"], "Event triggered a fight but there was no linked opponent"
					combat.group_fight(self.player, self.player.data["enemy"], summary=summary)
					self.player.data["summary"] = self.__format_summary(summary)
					if not self.player.entities:
						Event("Battle2").run(self.player)
					elif self.player.data["enemy"].entities:
						self.run(self.player)
					else:
						Event("Battle1").run(self.player)

				case "repeat":
					self.player.data["summary"] = self.__format_summary(summary)
					self.run(player=self.player)

				case "heal":
					if self.player.resources["medication"] and outcome[1].hp < outcome[1].max_hp:
						outcome[1].hp += 1
						self.player.resources["medication"] -= 1
						summary["hp"]["test"] += 1

				case "move_back":
					self.player.move_back()

				case "inventory":
					self.player.inventory_win.show()

				case _:
					return outcome[0]

		if self.player and self.player.current_event == self:
			self.player.current_event = None

# Avoid circular import
help_event.append(Event("Intro0"))

