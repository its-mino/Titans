import pygame
import math
import json

pygame.init()
pygame.font.init()

size = width, height = 1000,800
screen = pygame.display.set_mode((size))
font30 = pygame.font.SysFont('Calibri', 30)
font20 = pygame.font.SysFont('Calibri', 20)

piece_imgs = {'melee': pygame.image.load('img/melee.jpg'), 'ranged': pygame.image.load('img/ranged.jpg')}

piece_types = json.load(open('templates/piece_types.json'))
attacks = json.load(open('templates/attacks.json'))
active_attack = None
attack_buttons = []

board_size = board_width, board_height = 800, 800

square_size = board_width/10

turn = 0
all_pieces = []
active_piece = None

class Player:
	def __init__(self):
		self.pieces = []

	def addPieces(self, pieces):
		for piece in pieces:
			all_pieces.append(piece)
			self.pieces.append(piece)

	def getPieces(self):
		return self.pieces

class Piece:
	def __init__(self, loc, template):
		self.loc = loc
		self.health = piece_types[template]['health']
		self.max_health = piece_types[template]['health']
		self.speed = piece_types[template]['speed']
		self.attacks = piece_types[template]['attacks']
		self.img = piece_imgs[template]


def getDist(loc1, loc2):
	return math.sqrt(math.pow((loc1[0]-loc2[0]),2)+math.pow((loc1[1]-loc2[1]),2))

players = [Player(), Player()]

players[0].addPieces([Piece((1,1), 'melee'), Piece((1,3), 'ranged')])
players[1].addPieces([Piece((7,8), 'melee'), Piece((6,7), 'ranged')])


done = False
while not done:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done = True
		elif event.type == pygame.MOUSEBUTTONDOWN:
			move = True
			mouse_loc = mouse_x, mouse_y = pygame.mouse.get_pos()
			button_clicked = False
			for button in attack_buttons:
				if button[2].collidepoint(mouse_loc):
					if(active_attack == button[1]):
						active_attack = None
					else:
						active_attack = button[1]
					button_clicked = True
			if not button_clicked:
				click_loc = click_x, click_y = mouse_x % board_width/square_size, mouse_y % board_height/square_size
				for piece in players[turn].getPieces():
					if(getDist(piece.loc, click_loc) == 0):
						if(piece is active_piece):
							active_piece = None
							active_attack = None
							attack_buttons = []
						else:
							attack_buttons = []
							active_piece = piece
							active_attack = None
							for i in range(len(active_piece.attacks)):
								attack_text = font30.render(active_piece.attacks[i], False, (255, 255, 255))
								button = pygame.Rect(board_width+10, 210*i, width-board_width-20, 100)
								pygame.draw.rect(screen, (255, 0, 255), button)
								text_rect = attack_text.get_rect()
								text_rect.center = button.center
								screen.blit(attack_text, text_rect)
								attack_buttons.append((attack_text, active_piece.attacks[i], button, text_rect))
						move = False
				if move == True and active_attack == None and active_piece is not None and getDist(active_piece.loc, click_loc) <= active_piece.speed:
					is_open = True
					for piece in all_pieces:
						if click_loc == piece.loc:
							is_open = False
					if is_open:
						active_piece.loc = click_loc
						turn = (turn+1)%len(players)
						active_piece = None

	screen.fill((0,0,0))

	for x in range(11):
		pygame.draw.line(screen, (255,255,255), (square_size*x,0), (square_size*x,board_height))
		pygame.draw.line(screen, (255,255,255), (0,square_size*x), (board_width, square_size*x))

	for x in range(10):
		for y in range(10):
			if active_piece != None:
				if active_attack != None:
					if getDist(active_piece.loc, (x, y)) <= attacks[active_attack]['range'] and not (x is active_piece.loc[0] and y is active_piece.loc[1]):
						pygame.draw.circle(screen, (0,255,0), (x*square_size+(square_size/2), y*square_size+(square_size/2)), square_size/2-5)
				elif getDist(active_piece.loc, (x, y)) <= active_piece.speed and not (x is active_piece.loc[0] and y is active_piece.loc[1]):
					pygame.draw.circle(screen, (0,0,255), (x*square_size+(square_size/2), y*square_size+(square_size/2)), square_size/2-5)

	for index, player in enumerate(players):
		for piece in player.pieces:
			outline = pygame.Rect(piece.loc[0]*square_size+5, piece.loc[1]*square_size+5, 70, 70)
			if(index == 0):
				pygame.draw.rect(screen, (0,0,255), outline)
			elif(index == 1):
				pygame.draw.rect(screen, (0,255,0), outline)
			screen.blit(piece.img, (piece.loc[0]*square_size+10, piece.loc[1]*square_size+10))
			piece_health = font20.render(str(piece.health)+'/'+str(piece.max_health), False, (255, 255, 255))
			screen.blit(piece_health, ((piece.loc[0]*square_size+10, piece.loc[1]*square_size+70)))


	if(active_piece != None):
		for button in attack_buttons:
			pygame.draw.rect(screen, (255, 0, 255), button[2])
			screen.blit(button[0], button[3])

	pygame.display.flip()