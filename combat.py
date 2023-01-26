# Combat
#
# (c) Orlando Chamberlain 2022
#
# Evaluate combat outcomes

# Combat procedure:
#	inputs per combatant: def, atk, hp
#	dmg to c1 from c2 = randint(1, c2.atk) * (1 - c1.def)

from random import randint, choice
from collections import defaultdict
import entities

def group_fight(plr, foe, summary=None):
	for g_atk, g_def in ((plr,foe),(foe,plr)):
		for creature in g_atk.entities:
			if g_def.entities:
				if type(g_atk) == entities.Player:
					if g_atk.resources["ammunition"]:
						g_atk.resources["ammunition"] -= 1
						if summary:
							summary["resources"]["ammuintion"] -= 1
					else:
						pass
				defender, dmg, died = creature_attack(creature, choice(g_def.entities))
				if summary:
					summary["hp"][defender.name] += dmg
					if died:
						summary["deaths"][defender.name] = 1
						for loot in defender.loot:
							summary["items"][loot] += 1
						plr.inventory.extend(defender.loot)
			else:
				break

def creature_attack(a, t):
	"""make 2 Creatures fight
	
	a: attacker
	t: target"""

	damage = int(randint(1, a.attack) * (1 - t.defence))
	died = t.damage(damage)

	return (t, damage, died)

