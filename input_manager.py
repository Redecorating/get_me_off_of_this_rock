# Input Manager
#
# (c) 2022 Orlando Chamberlain
#
# Await input
# Check if input has an available key
# Return action for that key
#

import pygame

fps = 30

help_event = []

def show_help():
	help_event[0].run(None)
	im.rm_action(pygame.K_h)

class Input_manager:
	"""Manages Keypresses"""
	def __init__(self):
		self.actionsets = []
		self.push_set()
		self.actions = self.actionsets[-1]
		self.clock = pygame.time.Clock()
		pygame.event.set_allowed([
			pygame.QUIT,
			pygame.KEYDOWN
		])

	def push_set(self):
		"""push set of actions onto stack, the new set will be empty"""
		self.actionsets.append({})
		self.actions = self.actionsets[-1]

		self.add_action(pygame.K_h, (show_help,))

	def pop_set(self):
		"""pops the last actionset from the stack"""
		if len(self.actionsets) > 1:
			self.actionsets.pop(-1)
		else:
			self.actionsets[0] = {}
		self.actions = self.actionsets[-1]

	def add_action(self, key, func):
		"""adds and key and action to the current set

		key: pygame.K_...
		action: any, will be returned by wait()"""
		assert key not in self.actions.keys(), \
			"Tried to add an action to a key that already had one."
		self.actions[key] = func

	def rm_action(self, key):
		"""take an action off the set

		key: pygame.K_..."""
		del self.actions[key]

	def wait(self):
		"""Awaits valid keypresses, then returns the data that was with them"""
		waiting = True

		while waiting:
			events = pygame.event.get()

			for event in events:
				if event.type == pygame.QUIT:
					return None
				elif event.type == pygame.KEYDOWN:
					key = event.key
					if key in self.actions.keys():
						return self.actions[key]
			self.clock.tick(fps)

im = Input_manager()
