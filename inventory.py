# Inventory
#
# (c) 2022 Orlando Chamberlain
#
# Show Inventory

from input_manager import im
import compositor as comp
import window as win
import event
import pygame

window_size = (1000,800)
title_font = 36
num_columns = 3
title_size = (window_size[0]//num_columns, title_font + 10)
column_size = (window_size[0]//num_columns, window_size[1] - title_size[1])
cell_font = 30
small_cell_font = 18
cell_size = (column_size[0], 30)
cell_count = column_size[1]//cell_size[1]

inventory_layer = comp.Composite(comp.resolution, alpha=True)

# TODO scroll lists?

class Inventory:
	def __init__(self, player):
		"""The player's inventory window"""
		self.player = player

		self.heal_event = event.Event("Heal0")

		self.window = self.__create_window()

		x = inventory_layer.rect.center[0] - self.window.rect.center[0]
		y = inventory_layer.rect.center[1] - self.window.rect.center[1]
		self.pos = (x,y)

	def __create_window(self):
		col = lambda: win.Window(column_size, [
			[win.Text(cell_size, "")]
			for _ in range(cell_count)
			])
		self.column_persons = col()
		self.cells = col()
		self.column_resources = col()

		layout = [
				[win.Text(title_size, x, font_size=title_font) for x in ("Personnel", "Items", "Resources")],
				[(column_size, x) for x in (self.column_persons, self.cells, self.column_resources)]
				]
		
		self.column_persons.layers[-1]._child.set_text(
				"Press M to use medicine for healing", size=small_cell_font)

		return win.Window(window_size, layout)

	def __update_persons(self):
		person_count = len(self.player.entities)
		for i in range(len(self.column_persons.layers)-2):
			# -2 skips bg and last cell
			if i < person_count:
				person = self.player.entities[i]
				text = f"{person.name}: {person.hp} hp"
			else:
				text = " "
			# i+1 skips background layer.
			self.column_persons.layers[i+1]._child.set_text(text, size=cell_font)


	def __update_items(self):
		inv_len = len(self.player.inventory)
		for i in range(len(self.cells.layers)-1):
			if i < inv_len:
				text = self.player.inventory[i]
			else:
				text = " "
			# i+1 skips background layer.
			self.cells.layers[i+1]._child.set_text(text, size=cell_font)

	def __update_resources(self):
		names = tuple(self.player.resources.keys())
		resource_count = len(names)
		for i in range(len(self.column_resources.layers)-1):
			if i < resource_count:
				name = names[i]
				count = self.player.resources[name]
				text = f"{str(count).zfill(2)} x {name}" 
			else:
				text = " "
			# i+1 skips background layer.
			self.column_resources.layers[i+1]._child.set_text(text, size=cell_font)

	def update(self):
		"""Call me to update my window with the current player data"""
		self.__update_persons()
		self.__update_items()
		self.__update_resources()

	def __show_healing(self):
		self.close()
		self.heal_event.run(self.player)

	def show(self):
		"""Call me to show the inventory window"""
		self.update()
		im.push_set()
		im.add_action(pygame.K_m, (self.__show_healing,))
		im.add_action(pygame.K_ESCAPE, (self.close,))
		im.add_action(pygame.K_i, (self.close,))
		self.link = comp.Link(inventory_layer, self.window, self.pos, 3)
	
	def close(self):
		"""Callback for input manager to close the inventory window"""
		self.link.remove()
		im.pop_set()

