# Storage
#
# (c) 2022 Orlando Chamberlain
#
# Load and save data to a game save

import pickle
import json
import os
import sys

platform = sys.platform

if platform == "linux":
	try:
		data_dir = os.path.join(os.environ["XDG_DATA_HOME"], "GetMeOffOfThisRock")
	except KeyError:
		data_dir = os.path.join(os.environ["HOME"],".local", "share", "GetMeOffOfThisRock")
else:
	print(platform, "not supported currently, saving might not work.")
	data_dir = "."
try:
	os.mkdir(data_dir)
except FileExistsError:
	pass

code_dir = os.path.split(__file__)[0]

class Store:
	"""Datastore on disk in pickle format

	filename: string of file within game data folder"""
	def __init__(self, filename):
		self.path = os.path.join(data_dir, filename)
		self.filename = filename
		self.data = None

		self.__load()

	def __load(self):
		try:
			fd = open(self.path, "rb")
		except FileNotFoundError:
			try:
				os.rename(self.path+".old", self.path)
				fd = open(self.path, "rb")
				print(f"Recovering old save.")
			except FileNotFoundError:
				fd = None

		if fd:
			try:
				self.data = pickle.load(fd)
			except pickle.UnpicklingError:
				pass
			fd.close()
	
	def save(self):
		"""Save self.data to disk as pickle"""
		try:
			os.rename(self.path, self.path+".old")
		except FileNotFoundError:
			pass
		fd = open(self.path, "wb")
		pickle.dump(self.data, fd)

def load_events():
	name = os.path.join(code_dir, "events.json")
	fd = open(name, "r")
	return json.load(fd)

