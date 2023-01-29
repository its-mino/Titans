import pygame
import math
import json
import effects
import copy

pygame.init()
pygame.font.init()

size = width, height = 1200,800
board_size = board_width, board_height = 800, 800
screen = pygame.display.set_mode((size))
font40 = pygame.font.SysFont('Calibri', 40)
font30 = pygame.font.SysFont('Calibri', 30)
font20 = pygame.font.SysFont('Calibri', 20)


piece_types = json.load(open('templates/piece_types.json'))
piece_names = []
for t in piece_types:
	piece_names.append(t)

piece_imgs = {}
for piece in piece_types:
	try:
		piece_imgs[piece] = pygame.image.load('img/'+piece+'.png')
	except:
		print(piece + ' picture doesn\'t exist')

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

square_size = int(board_width/10)
player_1_pieces = [None, None, None]
player_2_pieces = [None, None, None]

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
	def __init__(self, template, loc):
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
				for num, piece in player.pieces.items():
					for loc in locs:
						if piece.loc == loc:
							for effect, value in skill['effects'].items():
								handleEffect(effect, value, piece, skill['duration'])
		else:
			for effect, value in skill['effects'].items():
				handleEffect(effect, value, click_loc, skill['duration'])
	if skill['targets'] == 'self':
		if skill['range'] > 0:
			for player in players:
				for num, piece in player.pieces.items():
					if piece != active_piece:
						if active_piece.range_bonus != 0:
							rt = skill['range'] + active_piece.range_bonus
							r = rt if rt > 0 else 1
						else:
							r = skill['range']
						if getDist(active_piece.loc, piece.loc) <= r:
							for effect, value in skill['effects'].items():	
								handleEffect(effect, value, piece, skill['duration'])
		else:	
			for effect, value in skill['effects'].items():
				handleEffect(effect, value, active_piece, skill['duration'])
	if skill['targets'] == 'enemies':
		hit = False
		player = players[(side+1)%len(players)]
		for num, piece in player.pieces.items():
			if active_piece.range_bonus != 0:
				rt = skill['range'] + active_piece.range_bonus
				r = rt if rt > 0 else 1
			else:
				r = skill['range']
			if getDist(click_loc, piece.loc) <= 0 and getDist(active_piece.loc, piece.loc) <= r:
				hit = True
				for effect, value in skill['effects'].items():
					handleEffect(effect, value, piece, skill['duration'])
		if not hit:
			used = False
	if skill['targets'] == 'allies':
		hit = False
		player = players[side]
		for num, piece in player.pieces.items():
			if active_piece.range_bonus != 0:
				rt = skill['range'] + active_piece.range_bonus
				r = rt if rt > 0 else 1
			else:
				r = skill['range']
			if getDist(click_loc, piece.loc) <= 0 and getDist(active_piece.loc, piece.loc) <= r:
				hit = True
				for effect, value in skill['effects'].items():
					handleEffect(effect, value, piece, skill['duration'])
		if not hit:
			used = False
	if skill['targets'] == 'others':
		hit = False
		for player in players:
			for num, piece in player.pieces.items():
				if piece is not active_piece:
					if active_piece.range_bonus != 0:
						rt = skill['range'] + active_piece.range_bonus
						r = rt if rt > 0 else 1
					else:
						r = skill['range']
					if getDist(click_loc, piece.loc) <= 0 and getDist(active_piece.loc, piece.loc) <= r:
						hit = True
						for effect, value in skill['effects'].items():
							handleEffect(effect, value, piece, skill['duration'])
		if not hit:
			used = False

	if skill['targets'] == 'any':
		hit = False
		for player in players:
			for num, piece in player.pieces.items():
				if active_piece.range_bonus != 0:
					rt = skill['range'] + active_piece.range_bonus
					r = rt if rt > 0 else 1
				else:
					r = skill['range']
				if getDist(click_loc, piece.loc) <= 0 and getDist(active_piece.loc, piece.loc) <= r:
					hit = True
					for effect, value in skill['effects'].items():
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
		button = pygame.Rect(board_width+10, 210*i, 180, 100)
		text_rect = attack_text.get_rect()
		text_rect.center = button.center
		ability_buttons.append((attack_text, piece.attacks[i], button, text_rect, 'attack'))

		button = pygame.Rect(board_width+10, 210*i, 180, 100)
		use_covers.append((button, 'attack'))
	offset = len(ability_buttons)
	for i in range(len(piece.skills)):
		skill_text = font30.render(piece.skills[i], False, (255, 255, 255))
		button = pygame.Rect(board_width+10, 210*(i+offset), 180, 100)
		text_rect = skill_text.get_rect()
		text_rect.center = button.center
		ability_buttons.append((skill_text, piece.skills[i], button, text_rect, 'skill'))

		if abilities['skill'][piece.skills[i]]['attack']:
			button = pygame.Rect(board_width+10, 210*(i+offset), 180, 100)
			use_covers.append((button, 'attack'))
		else:
			button = pygame.Rect(board_width+10, 210*(i+offset), 180, 100)
			use_covers.append((button, 'minor'))
		
	return ability_buttons, use_covers

def endTurn():
	global side, active_player, active_piece, active_ability, ability_type, ability_buttons, turn
	active_ability = None
	ability_type = ''
	ability_buttons = []
	active_piece.has_attacked = False
	active_piece.has_moved = False
	active_piece.has_minored = False
	temp = copy.deepcopy(active_piece.effects)
	for effect, duration in active_piece.effects.items():
		temp[effect] -= 1
		if 'skill_' in effect:
			covers = cooldown_covers[str(side)+str(active_player.piece)]
			for index, cover in enumerate(covers):
				if cover[0] == effect:
					text = font40.render(str(temp[effect]), False, (0, 0, 0))
					text_rect = text.get_rect()
					text_rect.center = cover[1].center
					cooldown_covers[str(side)+str(active_player.piece)][index] = [cover[0], cover[1], text_rect, text]

		elif 'hot:' in effect:
			active_piece.health += int(effect.split(":")[1])
			if active_piece.health > active_piece.max_health:
				active_piece.health = active_piece.max_health

		elif 'dot:' in effect:
			active_piece.health -= int(effect.split(":")[1])
			if active_piece.health <= 0:
				active_piece.dead = True

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
	turn += 1
	if turn > (len(player_1_pieces) + len(player_2_pieces))-1:
		turn = 0
	active_player = players[side]
	active_player.piece += 1
	if str(active_player.piece) not in active_player.pieces:
			active_player.piece = 0
	while active_player.pieces[str(active_player.piece)].dead:
		active_player.piece += 1
		if str(active_player.piece) not in active_player.pieces:
			active_player.piece = 0

	active_piece = active_player.pieces[str(active_player.piece)]
	active_piece.shield = 0
	ability_buttons, use_covers = getPieceButtons(active_piece)

def checkWin():
	for player in players:
		allDead = True
		for num, piece in player.pieces.items():
			if not piece.dead:
				allDead = False
		if allDead:
			print('Player ' + str((side+1)%len(players)) + ' has won!')

def init():
	global players, active_player, active_piece, ability_buttons, turn
	players = [Player(), Player()]
	players[0].addPieces(player_1_pieces)
	players[1].addPieces(player_2_pieces)
	active_player = players[0]
	active_piece = active_player.pieces["0"]
	ability_buttons, use_covers = getPieceButtons(active_piece)
	players[1].piece = -1
	turn = 0

def charInfo(name, hideButton = False):
	global side, turn
	back_button = pygame.Rect(50,50,150,100)
	choose_button = pygame.Rect(250,50,150,100)
	finished = False
	while not finished:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				finished = True
				exit()
			elif event.type == pygame.MOUSEBUTTONDOWN:
				mouse_loc = mouse_x, mouse_y = pygame.mouse.get_pos()
				if back_button.collidepoint(mouse_loc):
					finished = True
				if choose_button.collidepoint(mouse_loc):
					if side == 0:
						player_1_pieces[int(turn**1/2)] = piece_names[x]
						side += 1
						turn += 1
						finished = True
					elif side == 1:
						player_2_pieces[int((turn-1)**1/2)] = piece_names[x]
						side -= 1
						turn += 1
						finished = True
		screen.fill((25,25,25))

		char_name = font40.render(name, False, (255,255,255))
		screen.blit(char_name, (100, 200))
		screen.blit(piece_imgs[name], (90, 250))
		char_health = font30.render('Health: '+str(piece_types[name]['health']), False, (255,255,255))
		screen.blit(char_health, (200, 250))
		char_health = font30.render('Speed: '+str(piece_types[name]['speed']), False, (255,255,255))
		screen.blit(char_health, (200, 300))
		attacks_label = font40.render('Attacks:', False, (255,255,255))
		screen.blit(attacks_label, (100, 400))
		skills_label = font40.render('Skills:', False, (255,255,255))
		screen.blit(skills_label, (400, 200))
		for i, attack in enumerate(piece_types[name]['attacks']):
			attack_data = abilities['attack'][attack]
			screen.blit(font30.render(attack, False, (255,255,255)), (100, 450 + i*100))
			screen.blit(font30.render('Range: ' + str(attack_data['range']), False, (255,255,255)), (100, 475 + i*100))
			screen.blit(font30.render('Damage: ' + str(attack_data['damage']), False, (255,255,255)), (100, 500 + i*100))

		for i, skill in enumerate(piece_types[name]['skills']):
			skill_data = abilities['skill'][skill]
			screen.blit(font30.render(skill, False, (255,255,255)), (400, 250 + i*175))
			if skill_data['attack']:
				screen.blit(font30.render('Action Type: Attack', False, (255,255,255)), (400, 275 + i*175))
			else:
				screen.blit(font30.render('Action Type: Minor', False, (255,255,255)), (400, 275 + i*175))
			screen.blit(font30.render('Cooldown: ' + str(skill_data['cooldown']), False, (255,255,255)), (400, 300 + i*175))
			screen.blit(font30.render('Range: ' + str(skill_data['range']), False, (255,255,255)), (400, 325 + i*175))
			screen.blit(font30.render('Description: ' + skill_data['description'][0], False, (255,255,255)), (400, 350 + i*175))
			if len(skill_data['description']) > 1:
				for z, string in enumerate(skill_data['description']):
					if z != 0:
						screen.blit(font30.render(skill_data['description'][z], False, (255,255,255)), (400, 375 + i*175))

		pygame.draw.rect(screen, (255,50,50), back_button)
		back_text = font30.render('Back', False, (255,255,255))
		back_text_rect = back_text.get_rect()
		back_text_rect.center = back_button.center
		screen.blit(back_text, back_text_rect)
		if not hideButton:
			pygame.draw.rect(screen, (50,255,50), choose_button)
			choose_text = font30.render('Choose', False, (255,255,255))
			choose_text_rect = choose_text.get_rect()
			choose_text_rect.center = choose_button.center
			screen.blit(choose_text, choose_text_rect)
		pygame.display.flip()

#team select
player_1_rects = [pygame.Rect(50, 200, 80, 80), pygame.Rect(50, 400, 80, 80), pygame.Rect(50, 600, 80, 80)]
player_2_rects = [pygame.Rect(width-130, 200, 80, 80), pygame.Rect(width-130, 400, 80, 80), pygame.Rect(width-130, 600, 80, 80)]
grid = [(325, 200), (475, 200), (625, 200), (775, 200), (325, 400), (475, 400), (625, 400), (775, 400), (475, 600), (625, 600)]
grid_rects = []
for square in grid:
	grid_rects.append(pygame.Rect(square, (80,80)))
started = False
side = 0
turn = 0
while not started:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			started = True
			exit()
		elif event.type == pygame.MOUSEBUTTONDOWN:
			mouse_loc = mouse_x, mouse_y = pygame.mouse.get_pos()
			for x, rect in enumerate(grid_rects): 
				if rect.collidepoint(mouse_loc):
					if piece_names[x] not in player_1_pieces and piece_names[x] not in player_2_pieces:
						if side == 0:
							for i, piece in enumerate(player_1_pieces):
								if piece is None:
									charInfo(piece_names[x])
									break
						elif side == 1:
							for i, piece in enumerate(player_2_pieces):
								if piece is None:
									charInfo(piece_names[x])
									break
			if turn > 5:
				started = True

	screen.fill((25,25,25))

	player_1_text = font40.render('Player 1', False, (255, 255, 255))
	player_2_text = font40.render('Player 2', False, (255, 255, 255))

	screen.blit(player_1_text, (40,100))
	screen.blit(player_2_text, (width - 150, 100))

	player_1_choose = font40.render('Player 1\'s turn to choose!', False, (255,255,255))
	player_2_choose = font40.render('Player 2\'s turn to choose!', False, (255,255,255))

	if side == 0:
		screen.blit(player_1_choose, (400, 100))
	elif side == 1:
		screen.blit(player_2_choose, (400, 100))

	pygame.draw.line(screen, (255,255,255), (170, 0), (170, height))
	pygame.draw.line(screen, (255,255,255), (width-170, 0), (width-170, height))

	for i, rect in enumerate(player_1_rects):
		if player_1_pieces[i] is None:
			pygame.draw.rect(screen, (255,255,255), rect)
		else:
			screen.blit(piece_imgs[player_1_pieces[i]], (rect.x, rect.y))
	for i, rect in enumerate(player_2_rects):
		if player_2_pieces[i] is None:
			pygame.draw.rect(screen, (255,255,255), rect)
		else:
			screen.blit(piece_imgs[player_2_pieces[i]], (rect.x, rect.y))

	for i, square in enumerate(grid):
		if piece_names[i] not in player_1_pieces and piece_names[i] not in player_2_pieces:
			screen.blit(piece_imgs[piece_names[i]], square)

	pygame.display.flip()

#prep
turn = 0
initiative_1 = []
initiative_2 = []
ready = False
player_1_wait = pygame.transform.rotate(player_1_text, 90)
player_2_wait = pygame.transform.rotate(player_2_text, 90)
player_1_go = font40.render('Player 1', False, (0, 255, 0))
player_1_go = pygame.transform.rotate(player_1_go, 90)
player_2_go = font40.render('Player 2', False, (0, 255, 0))
player_2_go = pygame.transform.rotate(player_2_go, 90)
player_1_grid = []
selected_piece = None
for i, piece in enumerate(player_1_pieces):
	player_1_grid.append(pygame.Rect(875, 200 + i * 200, 80, 80))
player_2_grid = []
for i, piece in enumerate(player_2_pieces):
	player_2_grid.append(pygame.Rect(1025, 200 + i * 200, 80, 80))
while not ready:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			ready = True
			exit()
		elif event.type == pygame.MOUSEBUTTONDOWN:
				mouse_loc = mouse_x, mouse_y = pygame.mouse.get_pos()
				picked_piece = False
				if turn % 2 == 0:
					for i ,square in enumerate(player_1_grid):
						if square.collidepoint(mouse_loc) and selected_piece is None:
							selected_piece = (1, i, player_1_pieces[i])
							player_1_pieces.pop(i)
							picked_piece = True
				else:
					for i ,square in enumerate(player_2_grid):
						if square.collidepoint(mouse_loc) and selected_piece is None:
							selected_piece = (2, i, player_2_pieces[i])
							player_2_pieces.pop(i)
							picked_piece = True
				if not picked_piece and mouse_x < board_width and mouse_y < board_height:
					click_loc = click_x, click_y = int(mouse_x % board_width/square_size), int(mouse_y % board_height/square_size)
					if turn % 2 == 0:
						if click_x <= 4 and selected_piece is not None:
							initiative_1.append(Piece(selected_piece[2], click_loc))
							turn += 1
							selected_piece = None
					else:
						if click_x >= 6 and selected_piece is not None:
							initiative_2.append(Piece(selected_piece[2], click_loc))
							turn += 1
							selected_piece = None
					if turn == 6:
						player_1_pieces = initiative_1
						player_2_pieces = initiative_2
						ready = True
	if not ready:
		screen.fill((25,25,25))

		for x in range(11):
			pygame.draw.line(screen, (255,255,255), (square_size*x,0), (square_size*x,board_height))
			pygame.draw.line(screen, (255,255,255), (0,square_size*x), (board_width, square_size*x))

		for piece in initiative_1:
			outline = pygame.Rect(int(piece.loc[0])*square_size+5, int(piece.loc[1])*square_size+5, 10, 10)
			pygame.draw.rect(screen, (0,0,255), outline)
			screen.blit(piece.img, (int(piece.loc[0])*square_size, int(piece.loc[1])*square_size))

		for piece in initiative_2:
			outline = pygame.Rect(int(piece.loc[0])*square_size+5, int(piece.loc[1])*square_size+5, 10, 10)
			pygame.draw.rect(screen, (0,255,0), outline)
			screen.blit(piece.img, (int(piece.loc[0])*square_size, int(piece.loc[1])*square_size))

		if turn % 2 == 0:
			screen.blit(player_1_go, (825, 400))
			screen.blit(player_2_wait, (1150, 400))
		else:
			screen.blit(player_1_wait, (825, 400))
			screen.blit(player_2_go, (1150, 400))

		for i, piece in enumerate(player_1_pieces):
			if selected_piece != (1, i, piece):
				screen.blit(piece_imgs[piece], player_1_grid[i])

		for i, piece in enumerate(player_2_pieces):
			if selected_piece != (2, i, piece):
				screen.blit(piece_imgs[piece], player_2_grid[i])

		cover_surface = pygame.Surface((square_size*6, board_height))
		cover_surface.fill((255,0,0))
		cover_surface.set_alpha(50)
		if turn % 2 == 0:
			screen.blit(cover_surface, (square_size*4, 0))
		else:
			screen.blit(cover_surface, (0, 0))

		pygame.display.flip()


init()

#game
done = False
while not done:
	checkWin()

	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done = True
			exit()
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_1:
				charInfo(players[0].getPieces()['0'].template, True)
			elif event.key == pygame.K_2:
				charInfo(players[0].getPieces()['1'].template, True)
			elif event.key == pygame.K_3:
				charInfo(players[0].getPieces()['2'].template, True)
			elif event.key == pygame.K_4:
				charInfo(players[1].getPieces()['0'].template, True)
			elif event.key == pygame.K_5:
				charInfo(players[1].getPieces()['1'].template, True)
			elif event.key == pygame.K_6:
				charInfo(players[1].getPieces()['2'].template, True)
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
				click_loc = click_x, click_y = int(mouse_x % board_width/square_size), int(mouse_y % board_height/square_size)

				if active_ability is not None and getDist(active_piece.loc, click_loc) <= abilities[ability_type][active_ability]['range']:
					if ability_type == 'attack' and not active_piece.has_attacked and active_piece.can_attack:
						player = players[(side+1)%len(players)]
						for num, piece in player.getPieces().items():
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
								if "effects" in abilities['attack'][active_ability]:
									for effect, value in abilities['attack'][active_ability]['effects'].items():
										handleEffect(effect, value, piece, abilities['attack'][active_ability]['duration'])
								if piece.health <= 0:
									piece.dead = True
								active_piece.has_attacked = True
								active_ability = None
								ability_type = ''
					elif ability_type == 'skill':
						if (not active_piece.has_attacked and active_piece.can_attack) or (not abilities['skill'][active_ability]['attack'] and active_piece.can_minor):
							if 'ground' not in abilities['skill'][active_ability]['targets']:
								for player in players:
									for num, piece in player.pieces.items():
										if piece.loc == click_loc:	
											if piece.targetable:
												handleSkill(active_ability, click_loc)
							else:
								handleSkill(active_ability, click_loc)
				elif not active_piece.has_moved and active_piece.can_move and getDist(active_piece.loc, click_loc) <= active_piece.speed:
					is_open = True
					for player in players:
						for num, piece in player.getPieces().items():
							if click_loc == piece.loc:
								is_open = False
					if is_open:
						active_piece.loc = click_loc
						active_piece.has_moved = True

	screen.fill((25,25,25))

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
				if active_piece.range_bonus != 0:
					rt = abilities[ability_type][active_ability]['range'] + active_piece.range_bonus
					r = rt if rt > 0 else 1
				else:
					r = abilities[ability_type][active_ability]['range']
				if getDist(active_piece.loc, (x, y)) <= r:
					pygame.draw.circle(screen, color, (int(x*square_size+(square_size/2)), int(y*square_size+(square_size/2))), int(square_size/2-5))
			elif not active_piece.has_moved and active_piece.can_move and getDist(active_piece.loc, (x, y)) <= active_piece.speed and not (x is active_piece.loc[0] and y is active_piece.loc[1]):
				pygame.draw.circle(screen, (0,0,255), (int(x*square_size+(square_size/2)), int(y*square_size+(square_size/2))), int(square_size/2-5))

	for index, player in enumerate(players):
		for num, piece in player.pieces.items():
			if not piece.dead:
				outline = pygame.Rect(int(piece.loc[0])*square_size+5, int(piece.loc[1])*square_size+5, 10, 10)
				if index == 0:
					pygame.draw.rect(screen, (0,0,255), outline)
				elif index == 1:
					pygame.draw.rect(screen, (0,255,0), outline)
				screen.blit(piece.img, (int(piece.loc[0])*square_size, int(piece.loc[1])*square_size))
				piece_health = font20.render(str(piece.health)+'/'+str(piece.max_health), False, (255, 255, 255))
				screen.blit(piece_health, ((int(piece.loc[0])*square_size+5, int(piece.loc[1])*square_size+70)))
				if piece.shield > 0:
					piece_shield = font20.render(str(piece.shield), False, (255, 255, 255))
					screen.blit(piece_shield, ((int(piece.loc[0])*square_size+60, int(piece.loc[1])*square_size+70)))
				n = 0
				for effect, value in piece.effects.items():
					if 'skill_' not in effect:
						screen.blit(font20.render(effect + ' ' + str(value), False, (255,255,255)), (int(piece.loc[0])*square_size, (int(piece.loc[1])*square_size)+10+(10*n)))
						n += 1

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
			#cover_surface.set_alpha(50)
			screen.blit(cover_surface, (cover[0].topleft))

	for piece_string, covers in cooldown_covers.items():
		s = str(side)+str(active_player.piece)
		if piece_string == s:
			if len(covers) > 0:
				for cover in covers:
					cover_surface = pygame.Surface(cover[1].size)
					cover_surface.fill((0,0,0))
					cover_surface.set_alpha(50)
					screen.blit(cover_surface, (cover[1].topleft))
					screen.blit(cover[3], cover[2])
		
	for i in range(6):
		if i % 2 == 0:
			screen.blit(player_1_pieces[int(i**1/2)].img, (1100, 100 + 100 * i))
		else:
			screen.blit(player_2_pieces[int((i-1)**1/2)].img, (1100, 100 + 100 * i))	

	pygame.draw.polygon(screen, (255,0,0), [(1070, 130 + 100*turn), (1070, 150+100*turn), (1090, 140+100*turn)])	

	pygame.draw.rect(screen, (255,255,255), end_button)
	screen.blit(end_text, end_text_rect)

	pygame.display.flip()