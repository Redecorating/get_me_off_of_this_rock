import pygame
pygame.init()

from input_manager import im
import storage
import compositor as comp
import entities
import inventory
import status
import event
import window
import map

def new_game(save):
	world_map = map.Map((7,8))
	im.pop_set()
	player = entities.Player(world_map)
	save.data = player
	
	return run_game(player)

def continue_game(save):
	player = save.data
	world_map = player.tile.map
	player.status_win.show()
	comp.force_deep_outdate(world_map.tiled_map)

	return run_game(player)

def run_game(player):
	compositor = comp.compositor_instance
	world_map = player.tile.map

	compositor.display.unlink()

	comp.Link(compositor.display, event.event_layer, (0,0), 7)
	comp.Link(compositor.display, world_map.tiled_map, (-50000,0), 5)
	# 50000 starts it off screen
	comp.Link(compositor.display, status.status_layer, (0,0), 7)
	comp.Link(compositor.display, inventory.inventory_layer, (0,0), 6)

	world_map.centre(player.tile)

	for k, d in player.actions["MOVE"] + player.actions["INV"]:
		im.add_action(k, d)

	if player.current_event:
		player.current_event.run(player)
	elif player.turn_number == 0:
		event.Event("Intro1").run(player)

	compositor.update()

	return player


def main():
	compositor = comp.Compositor()
	comp.compositor_instance = compositor

	comp.Link(compositor.display, event.event_layer, (0,0), 7)

	player = None

	save = storage.Store("save")
	if save.data:
		event.Event("Menu1").run(None)
	else:
		event.Event("Menu0").run(None)

	compositor.update()

	while True:
		save.save()
		out = im.wait()
		if out == None:
			if player:
				player.status_win.close()
			break
		else:
			ret = out[0](*out[1:])
			if player:
				player.status_win.update()
			compositor.update()
			match ret:
				case "exit_game":
					exit(0)
				case "continue_game":
					player = continue_game(save)
				case "new_game":
					player = new_game(save)

if __name__ == '__main__':
	main()
