import copy

def isTaken(square, players):
	for player in players:
		for num, piece in player.pieces.iteritems():
			if piece.loc == square:
				return True
	return False
def push(distance, user, target, players):
	for i in range(abs(distance)):
		d = 1 if distance > 0 else -1
		if user.loc[0] > target.loc[0] and not isTaken((target.loc[0]-d, target.loc[1]), players):
			new_x = target.loc[0] - d
			target.loc = (new_x, target.loc[1])
		elif user.loc[0] < target.loc[0] and not isTaken((target.loc[0]+d, target.loc[1]), players):
			new_x = target.loc[0] + d
			target.loc = (new_x, target.loc[1])

		if user.loc[1] > target.loc[1] and not isTaken((target.loc[0], target.loc[1]-d), players):
			new_y = target.loc[1] - d
			target.loc = (target.loc[0], new_y)
		elif user.loc[1] < target.loc[1] and not isTaken((target.loc[0], target.loc[1]+d), players):
			new_y = target.loc[1] + d
			target.loc = (target.loc[0], new_y)

def speed(value, user, target, duration):
	target.speed += value
	target.effects['speed'] = duration

def move(target, user, value):
	if value == 'ignore':
		user.loc = target

def targetable(value, user, target, duration):
	target.targetable = value
	target.effects['targetable'] = duration

def damageDealt(value, user, target, duration):
	target.effects['damage dealt:'+str(value)] = duration

def rangeChange(value, user, target, duration):
	target.range_bonus = value
	target.effects['range'] = duration

def damage(value, user, target):
	if target.shield > 0:
		d_dealt = target.shield
		target.shield -= value
		if target.shield <= 0 and value-d_dealth > 0:
			target.health -= (value - d_dealt)
	else:
		target.health -= value
	for effect in user.effects:
		if 'damage dealt:' in effect:
			if target.shield > 0:
				d_dealt = target.shield
				target.shield -= int(effect.split(':')[1])
				if target.shield <= 0 and (int(effect.split(':')[1]) - d_dealt) > 0:
					target.health -= (int(effect.split(':')[1]) - d_dealt)
			else:
				target.health -= int(effect.split(':')[1])
	for effect in target.effects:
		if 'damage taken:' in effect:
			if target.shield > 0:
				d_dealt = target.shield
				target.shield -= int(effect.split(':')[1])
				if target.shield <= 0 and (int(effect.split(':')[1]) - d_dealt) > 0:
					target.health -= (int(effect.split(':')[1]) - d_dealt)
			else:
				target.health -= int(effect.split(':')[1])
	if target.health <= 0:
		target.dead = True
	if target.health > target.max_health:
		target.health = target.max_health

def dot(value, target, duration):
	target.effects['dot:'+str(value)] = duration

def hot(value, target, duration):
	target.effects['hot:'+str(value)] = duration

def shield(value, target):
	target.shield = value

def durations(value, user, target):
	if value == 'damage':
		for index, effect in enumerate(target.effects):
			if 'skill_' not in effect:
				if target.shield > 0:
					d_dealt = target.shield
					target.shield -= 1
					if target.shield <= 0 and 1-d_dealth > 0:
						target.health -= (1 - d_dealt)
				else:
					target.health -= 1
		for effect in user.effects:
			if 'damage dealt:' in effect:
				if target.shield > 0:
					d_dealt = target.shield
					target.shield -= int(effect.split(':')[1])
					if target.shield <= 0 and (int(effect.split(':')[1]) - d_dealt):
						target.health -= (int(effect.split(':')[1]) - d_dealt)
				else:
					target.health -= int(effect.split(':')[1])	
		for effect in target.effects:
			if 'damage taken:' in effect:
				if target.shield > 0:
					d_dealt = target.shield
					target.shield -= int(effect.split(':')[1])
					if target.shield <= 0 and (int(effect.split(':')[1]) - d_dealt):
						target.health -= (int(effect.split(':')[1]) - d_dealt)
				else:
					target.health -= int(effect.split(':')[1])	
		if target.health <= 0:
			target.dead = True
	
	if value == 'dispel':
		temp = copy.deepcopy(target.effects)
		for effect, value in target.effects.iteritems():
			if not 'skill_' in effect:
				temp.pop(effect)
		target.effects = temp

def damageTaken(value, user, target, duration):
	target.effects['damage taken:'+str(value)] = duration

def canMove(value, target, duration):
	target.can_move = value
	target.effects['can_move'] = duration

def canAttack(value, target, duration):
	target.can_attack = value
	target.effects['can_attack'] = duration

def canMinor(value, target, duration):
	target.can_minor = value
	target.effects['can_minor'] = duration

def swap(active_piece, target):
	temp_loc = active_piece.loc
	active_piece.loc = target.loc
	target.loc = temp_loc