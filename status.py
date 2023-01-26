# Status
#
# (c) 2022 Orlando Chamberlain
#
# Status Bar

import compositor as comp
import window as win

side_gap_px = 40
height = 40
window_size = comp.resolution[0] - 2 * side_gap_px, height
half_size = window_size[0] // 2, window_size[1]
font_size = 36

status_layer = comp.Composite(comp.resolution, alpha=True)

class Status_Bar:
	def __init__(self, player):
		"""The player's status bar"""
		self.player = player

		x = side_gap_px
		y = side_gap_px
		self.pos = (x,y)
		self.link = None
		
		self.window = self.__create_window()

	def __create_window(self):
		left = win.Text(half_size, self.__gen_left_text(), font_size=font_size)
		right = win.Text(half_size, self.__gen_right_text(), font_size=font_size)
		self.left_half = left[1]
		self.right_half = right[1]

		layout = [[left, right]]
		
		return win.Window(window_size, layout)

	def __gen_left_text(self):
		turn = self.player.turn_number
		food = self.player.resources["food"]
		meds = self.player.resources["medication"]
		ammo = self.player.resources["ammunition"]

		return "Turn:%3.2d | Food:%3.2d Meds:%3.2d Ammo:%3.2d |" \
				% (turn, food, meds, ammo)

	def __gen_right_text(self):
		states = [""]
		
		for person in self.player.entities:
			name = person.name
			hp = person.hp
			state = "%6s: %2d HP" % (name, hp)
			states.append(state)

		return "|".join(states)

	def update(self):
		"""Call me to update my window with the current player data"""
		self.left_half.set_text(self.__gen_left_text())
		self.right_half.set_text(self.__gen_right_text())

	def show(self):
		"""Call me to show the status bar"""
		if self.link:
			self.close()

		self.link = comp.Link(status_layer, self.window, self.pos, 3)
	
	def close(self):
		"""Close status bar"""
		if self.link:
			self.link.remove()
			self.link = None

