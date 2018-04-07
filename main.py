import pygame
import math
import json
import effects
import copy

pygame.init()
pygame.font.init()

size = width, height = 1000,800
board_size = board_width, board_height = 800, 800
screen = pygame.display.set_mode((size))
font40 = pygame.font.SysFont('Calibri', 40)
font30 = pygame.font.SysFont('Calibri', 30)
font20 = pygame.font.SysFont('Calibri', 20)

piece_imgs = {'Brute': pygame.image.load('img/Mesmer.jpg'), 'Archer': pygame.image.load('img/Archer.jpg')}

piece_types = json.load(open('templates/piece_types.json'))
abilities = {}
abilities['attack'] = json.load(open('templates/attacks.json'))
abilities['skill'] = json.load(open('templates/skills.json'))
active_ability = None
ability_type = ''
ability_buttons = []
cooldown_covers = {}
use_covers = []

end_button = pygame.Rect(board_width+10, height-100, width-board_width-20, 100)
end_text = font30.render("End Turn", False, (0, 0, 0))
end_text_rect = end_text.get_rect()
end_text_rect.center = end_button.center

square_size = board_width/10

side = 0
active_piece = None
active_player = None

class Player:
	def __init__(self):
		self.pieces = {}
		self.num_pieces = 0
		self.piece = 0

	def addPieces(self, pieces):
		global cooldown_covers
		for piece in pieces:
			self.pieces[str(self.num_pieces)] = piece
			self.num_pieces += 1

	def getPieces(self):
		return self.pieces

class Piece:
	def __init__(self, loc, template):
		self.loc = loc
		self.health = piece_types[template]['health']
		self.max_health = piece_types[template]['health']
		self.speed = piece_types[template]['speed']
		self.attacks = piece_types[template]['attacks']
		self.skills = piece_types[template]['skills']
		self.img = piece_imgs[template]
		self.effects = {}
		self.targetable = True
		self.range_bonus = 0
		self.shield = 0
		self.has_moved = False
		self.has_attacked = False
		self.has_minored = False
		self.can_move = True
		self.can_attack = True
		self.can_minor = True
		self.dead = False
		self.template = template

def handleEffect(effect, value, target, duration):
	if effect == 'push':
		effects.push(value, active_piece, target, players)
	if effect == 'speed':
		effects.speed(value, active_piece, target, duration)
	if effect == 'move':
		if type(target) is tuple:
			effects.move(target, active_piece, value)
	if effect == 'targetable':
		effects.targetable(value, active_piece, target, duration)
	if effect == 'damage dealt':
		effects.damageDealt(value, active_piece, target, duration)
	if effect == 'range':
		effects.rangeChange(value, active_piece, target, duration)
	if effect == 'damage':
		effects.damage(value, active_piece, target)
	if effect == 'dot':
		effects.dot(value, target, duration)
	if effect == 'hot':
		effects.hot(value, target, duration)
	if effect == 'shield':
		effects.shield(value, target)
	if effect == 'durations':
		effects.durations(value, active_piece, target)
	if effect == 'damage taken':
		effects.damageTaken(value, active_piece, target, duration)
	if effect == 'can move':
		effects.canMove(value, target, duration)
	if effect == 'can attack':
		effects.canAttack(value, target, duration)
	if effect == 'can minor':
		effects.canMinor(value, target, duration)
	if effect == 'swap':
		effects.swap(active_piece, target)

def handleSkill(skill_name, click_loc):
	used = True
	skill = abilities['skill'][skill_name]
	if 'ground' in skill['targets']:
		if ':' in skill['targets']:
			size = int(skill['targets'].split(':')[1])
			x = click_loc[0]-size
			locs = []
			while x <= click_loc[0]+size:
				y = click_loc[1]-size
				while y <= click_loc[1]+size:
					locs.append((x,y))
					y += 1
				x += 1
			for player in players:
				for num, piece in player.pieces.iteritems():
					for loc in locs:
						if piece.loc == loc:
							for effect, value in skill['effects'].iteritems():
								handleEffect(effect, value, piece, skill['duration'])
		else:
			for effect, value in skill['effects'].iteritems():
				handleEffect(effect, value, click_loc, skill['duration'])
	if skill['targets'] == 'self':
		if skill['range'] > 0:
			for player in players:
				for num, piece in player.pieces.iteritems():
					if piece != active_piece:
						if active_piece.range_bonus is not 0:
							rt = skill['range'] + active_piece.range_bonus
							r = rt if rt > 0 else 1
						else:
							r = skill['range']
						if getDist(active_piece.loc, piece.loc) <= r:
							for effect, value in skill['effects'].iteritems():	
								handleEffect(effect, value, piece, skill['duration'])
		else:	
			for effect, value in skill['effects'].iteritems():
				handleEffect(effect, value, active_piece, skill['duration'])
	if skill['targets'] == 'enemies':
		hit = False
		player = players[(side+1)%len(players)]
		for num, piece in player.pieces.iteritems():
			if active_piece.range_bonus is not 0:
				rt = skill['range'] + active_piece.range_bonus
				r = rt if rt > 0 else 1
			else:
				r = skill['range']
			if getDist(click_loc, piece.loc) <= 0 and getDist(active_piece.loc, piece.loc) <= r:
				hit = True
				for effect, value in skill['effects'].iteritems():
					handleEffect(effect, value, piece, skill['duration'])
		if not hit:
			used = False
	if skill['targets'] == 'allies':
		hit = False
		player = players[side]
		for num, piece in player.pieces.iteritems():
			if active_piece.range_bonus is not 0:
				rt = skill['range'] + active_piece.range_bonus
				r = rt if rt > 0 else 1
			else:
				r = skill['range']
			if getDist(click_loc, piece.loc) <= 0 and getDist(active_piece.loc, piece.loc) <= r:
				hit = True
				for effect, value in skill['effects'].iteritems():
					handleEffect(effect, value, piece, skill['duration'])
		if not hit:
			used = False
	if skill['targets'] == 'others':
		hit = False
		for player in players:
			for num, piece in player.pieces.iteritems():
				if piece is not active_piece:
					if active_piece.range_bonus is not 0:
						rt = skill['range'] + active_piece.range_bonus
						r = rt if rt > 0 else 1
					else:
						r = skill['range']
					if getDist(click_loc, piece.loc) <= 0 and getDist(active_piece.loc, piece.loc) <= r:
						hit = True
						for effect, value in skill['effects'].iteritems():
							handleEffect(effect, value, piece, skill['duration'])
		if not hit:
			used = False

	if skill['targets'] == 'any':
		hit = False
		for player in players:
			for num, piece in player.pieces.iteritems():
				if active_piece.range_bonus is not 0:
					rt = skill['range'] + active_piece.range_bonus
					r = rt if rt > 0 else 1
				else:
					r = skill['range']
				if getDist(click_loc, piece.loc) <= 0 and getDist(active_piece.loc, piece.loc) <= r:
					hit = True
					for effect, value in skill['effects'].iteritems():
						handleEffect(effect, value, piece, skill['duration'])
		if not hit:
			used = False

	if used:
		if skill['attack']:
			active_piece.has_attacked = True
		else:
			active_piece.has_minored = True
		active_piece.effects['skill_'+skill_name] = skill['cooldown']

		global active_ability, ability_type, ability_buttons
		cover = None
		text_rect = None
		text = None
		for button in ability_buttons:
			if button[1] == skill_name:
				cover = button[2]
				text = font40.render(str(active_piece.effects['skill_'+skill_name]), False, (0, 0, 0))
				text_rect = text.get_rect()
				text_rect.center = cover.center
		if str(side)+str(active_player.piece) not in cooldown_covers:
			cooldown_covers[str(side)+str(active_player.piece)] = []
		cooldown_covers[str(side)+str(active_player.piece)].append(['skill_'+skill_name, cover, text_rect, text])

		active_ability = None
		ability_type = ''

def getDist(loc1, loc2):
	return int(math.sqrt(math.pow((loc1[0]-loc2[0]),2)+math.pow((loc1[1]-loc2[1]),2)))

def getPieceButtons(piece):
	for i in range(len(piece.attacks)):
		attack_text = font30.render(piece.attacks[i], False, (255, 255, 255))
		button = pygame.Rect(board_width+10, 210*i, width-board_width-20, 100)
		text_rect = attack_text.get_rect()
		text_rect.center = button.center
		ability_buttons.append((attack_text, piece.attacks[i], button, text_rect, 'attack'))

		button = pygame.Rect(board_width+10, 210*i, width-board_width-20, 100)
		use_covers.append((button, 'attack'))
	offset = len(ability_buttons)
	for i in range(len(piece.skills)):
		skill_text = font30.render(piece.skills[i], False, (255, 255, 255))
		button = pygame.Rect(board_width+10, 210*(i+offset), width-board_width-20, 100)
		text_rect = skill_text.get_rect()
		text_rect.center = button.center
		ability_buttons.append((skill_text, piece.skills[i], button, text_rect, 'skill'))

		if abilities['skill'][piece.skills[i]]['attack']:
			button = pygame.Rect(board_width+10, 210*(i+offset), width-board_width-20, 100)
			use_covers.append((button, 'attack'))
		else:
			button = pygame.Rect(board_width+10, 210*(i+offset), width-board_width-20, 100)
			use_covers.append((button, 'minor'))
		
	return ability_buttons, use_covers

def endTurn():
	global side, active_player, active_piece, active_ability, ability_type, ability_buttons
	active_ability = None
	ability_type = ''
	ability_buttons = []
	active_piece.has_attacked = False
	active_piece.has_moved = False
	active_piece.has_minored = False
	temp = copy.deepcopy(active_piece.effects)
	for effect, duration in active_piece.effects.iteritems():
		temp[effect] -= 1
		if 'skill_' in effect:
			covers = cooldown_covers[str(side)+str(active_player.piece)]
			for index, cover in enumerate(covers):
				if cover[0] == effect:
					text = font40.render(str(temp[effect]), False, (0, 0, 0))
					text_rect = text.get_rect()
					text_rect.center = cover[1].center
					cooldown_covers[str(side)+str(active_player.piece)][index] = [cover[0], cover[1], text_rect, text]
		elif 'dot:' in effect:
			active_piece.health -= int(effect.split(":")[1])
			if active_piece.health <= 0:
				active_piece.dead = True

		elif 'hot:' in effect:
			active_piece.health += int(effect.split(":")[1])
			if active_piece.health > active_piece.max_health:
				active_piece.health = active_piece.max_health

		if 'skill_' in effect and temp[effect] <= 0:
			temp.pop(effect)
			covers = cooldown_covers[str(side)+str(active_player.piece)]
			for index, cover in enumerate(covers):
				if cover[0] == effect:
					covers.pop(index)
		elif 'skill_' not in effect and temp[effect] <= 0:
			if effect == 'targetable':
				setattr(active_piece, effect, True)
				temp.pop(effect)
			elif effect == 'can_move' or effect == 'can_minor' or effect == 'can_attack':
				setattr(active_piece, effect, True)
			elif effect == 'range':
				setattr(active_piece, 'range_bonus', 0)
				temp.pop(effect)
			elif 'damage dealt:' in effect or 'damage taken:' in effect or 'dot:' in effect or 'hot' in effect:
				temp.pop(effect)
			else:
				setattr(active_piece, effect, piece_types[active_piece.template][effect])
				temp.pop(effect)

	active_piece.effects = temp
	side = (side+1)%len(players)

	active_player = players[side]
	active_player.piece += 1
	if str(active_player.piece) not in active_player.pieces:
			active_player.piece = 0
	while active_player.pieces[str(active_player.piece)].dead:
		active_player.piece += 1
		if str(active_player.piece) not in active_player.pieces:
			active_player.piece = 0

	print 'Player ' + str(side) + '\'s Turn, using piece ' + str(active_player.piece)
	active_piece = active_player.pieces[str(active_player.piece)]
	active_piece.shield = 0
	ability_buttons, use_covers = getPieceButtons(active_piece)

def checkWin():
	for player in players:
		allDead = True
		for num, piece in player.pieces.iteritems():
			if not piece.dead:
				allDead = False
		if allDead:
			print 'Player ' + str((side+1)%len(players)) + ' has won!' 

def init():
	global players, active_player, active_piece, ability_buttons
	players = [Player(), Player()]
	players[0].addPieces([Piece((1,1), 'Brute')])
	players[0].addPieces([Piece((1,3), 'Archer')])
	players[1].addPieces([Piece((1,2), 'Archer')])
	players[1].addPieces([Piece((3,1), 'Archer')])
	active_player = players[0]
	active_piece = active_player.pieces["0"]
	ability_buttons, use_covers = getPieceButtons(active_piece)
	print 'Player 0\'s Turn, using piece 0'	


init()

done = False
while not done:
	checkWin()

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done = True
		elif event.type == pygame.MOUSEBUTTONDOWN:
			move = True
			mouse_loc = mouse_x, mouse_y = pygame.mouse.get_pos()
			button_clicked = False
			
			if end_button.collidepoint(mouse_loc): 
				endTurn()
				button_clicked = True
			for button in ability_buttons:
				if button[2].collidepoint(mouse_loc):
					if active_ability == button[1]:
						active_ability = None
						ability_type = ''
					else:
						if button[4] == 'attack' and active_piece.can_attack:
							active_ability = button[1]
							ability_type = 'attack'
						elif button[4] == 'skill' and "skill_"+button[1] not in active_piece.effects and ((abilities['skill'][button[1]]['attack'] and active_piece.can_attack) or (not abilities['skill'][button[1]]['attack'] and active_piece.can_minor)):
							active_ability = button[1]
							ability_type = 'skill'
					button_clicked = True
			if not button_clicked:
				click_loc = click_x, click_y = mouse_x % board_width/square_size, mouse_y % board_height/square_size

				if active_ability is not None and getDist(active_piece.loc, click_loc) <= abilities[ability_type][active_ability]['range']:
					if ability_type == 'attack' and not active_piece.has_attacked and active_piece.can_attack:
						player = players[(side+1)%len(players)]
						for num, piece in player.getPieces().iteritems():
							if piece.loc == click_loc and piece.targetable:
								if piece.shield > 0:
									d_dealt = piece.shield
									piece.shield -= abilities['attack'][active_ability]['damage']
									if piece.shield <= 0 and (abilities['attack'][active_ability]['damage'] - d_dealt) > 0:
										piece.health -= (abilities['attack'][active_ability]['damage'] - d_dealt)
								else:
									piece.health -= abilities['attack'][active_ability]['damage']
								for effect in active_piece.effects:
									if 'damage dealt:' in effect:
										if piece.shield > 0:
											d_dealt = piece.shield
											piece.shield -= int(effect.split(':')[1])
											if piece.shield <= 0 and (int(effect.split(':')[1]) - d_dealt):
												piece.health -= (int(effect.split(':')[1]) - d_dealt)
										else:
											piece.health -= int(effect.split(':')[1])
								for effect in piece.effects:
									if 'damage taken:' in effect:
										if piece.shield > 0:
											d_dealt = piece.shield
											piece.shield -= int(effect.split(':')[1])
											if piece.shield <= 0 and (int(effect.split(':')[1]) - d_dealt):
												piece.health -= (int(effect.split(':')[1]) - d_dealt)
										else:
											piece.health -= int(effect.split(':')[1])
								if piece.health <= 0:
									piece.dead = True
								active_piece.has_attacked = True
								active_ability = None
								ability_type = ''
					elif ability_type == 'skill':
						if (not active_piece.has_attacked and active_piece.can_attack) or (not abilities['skill'][active_ability]['attack'] and active_piece.can_minor):
							if 'ground' not in abilities['skill'][active_ability]['targets']:
								for player in players:
									for num, piece in player.pieces.iteritems():
										if piece.loc == click_loc:	
											if piece.targetable:
												handleSkill(active_ability, click_loc)
							else:
								handleSkill(active_ability, click_loc)
				elif not active_piece.has_moved and active_piece.can_move and getDist(active_piece.loc, click_loc) <= active_piece.speed:
					is_open = True
					for player in players:
						for num, piece in player.getPieces().iteritems():
							if click_loc == piece.loc:
								is_open = False
					if is_open:
						active_piece.loc = click_loc
						active_piece.has_moved = True

	screen.fill((0,0,0))

	for x in range(11):
		pygame.draw.line(screen, (255,255,255), (square_size*x,0), (square_size*x,board_height))
		pygame.draw.line(screen, (255,255,255), (0,square_size*x), (board_width, square_size*x))

	for x in range(10):
		for y in range(10):
			if active_ability is not None:
				if ability_type == 'attack':
					color = (255, 0, 255)
				elif ability_type == 'skill':
					color = (150, 255, 0)
				if active_piece.range_bonus is not 0:
					rt = abilities[ability_type][active_ability]['range'] + active_piece.range_bonus
					r = rt if rt > 0 else 1
				else:
					r = abilities[ability_type][active_ability]['range']
				if getDist(active_piece.loc, (x, y)) <= r:
					pygame.draw.circle(screen, color, (x*square_size+(square_size/2), y*square_size+(square_size/2)), square_size/2-5)
			elif not active_piece.has_moved and active_piece.can_move and getDist(active_piece.loc, (x, y)) <= active_piece.speed and not (x is active_piece.loc[0] and y is active_piece.loc[1]):
				pygame.draw.circle(screen, (0,0,255), (x*square_size+(square_size/2), y*square_size+(square_size/2)), square_size/2-5)

	for index, player in enumerate(players):
		for num, piece in player.pieces.iteritems():
			if not piece.dead:
				outline = pygame.Rect(piece.loc[0]*square_size+13, piece.loc[1]*square_size+13, 55, 55)
				if index == 0:
					pygame.draw.rect(screen, (0,0,255), outline)
				elif index == 1:
					pygame.draw.rect(screen, (0,255,0), outline)
				screen.blit(piece.img, (piece.loc[0]*square_size+18, piece.loc[1]*square_size+18))
				piece_health = font20.render(str(piece.health)+'/'+str(piece.max_health), False, (255, 255, 255))
				screen.blit(piece_health, ((piece.loc[0]*square_size+10, piece.loc[1]*square_size+70)))
				if piece.shield > 0:
					piece_shield = font20.render(str(piece.shield), False, (255, 255, 255))
					screen.blit(piece_shield, ((piece.loc[0]*square_size+60, piece.loc[1]*square_size+70)))

	

	for button in ability_buttons:
		if button[4] == 'attack':
			pygame.draw.rect(screen, (255, 0, 255), button[2])
		elif button[4] == 'skill':
			pygame.draw.rect(screen, (150, 255, 0), button[2])
		screen.blit(button[0], button[3])

	for cover in use_covers:
		if (cover[1] == 'attack' and (not active_piece.can_attack or active_piece.has_attacked) or (cover[1] == 'minor' and (not active_piece.can_minor or active_piece.has_minored))):
			cover_surface = pygame.Surface(cover[0].size)
			cover_surface.fill((0,0,0))
			cover_surface.set_alpha(50)
			screen.blit(cover_surface, (cover[0].topleft))

	for piece_string, covers in cooldown_covers.iteritems():
		s = str(side)+str(active_player.piece)
		if piece_string == s:
			if len(covers) > 0:
				for cover in covers:
					cover_surface = pygame.Surface(cover[1].size)
					cover_surface.fill((0,0,0))
					cover_surface.set_alpha(50)
					screen.blit(cover_surface, (cover[1].topleft))
					screen.blit(cover[3], cover[2])
				

	pygame.draw.rect(screen, (255,255,255), end_button)
	screen.blit(end_text, end_text_rect)

	pygame.display.flip()