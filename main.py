import pygame
import math

pygame.init()
size = width, height = 1000,800
screen = pygame.display.set_mode((size))

player1_img = pygame.image.load('img/player.jpg')
player2_img = pygame.image.load('img/player2.jpg')

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
	def __init__(self, loc, speed, img):
		self.loc = loc
		self.speed = speed
		self.img = img

def getDist(loc1, loc2):
	return math.sqrt(math.pow((loc1[0]-loc2[0]),2)+math.pow((loc1[1]-loc2[1]),2))

players = [Player(), Player()]

players[0].addPieces([Piece((1,1), 2, player1_img), Piece((1,3), 2, player1_img)])
players[1].addPieces([Piece((7,8), 2, player2_img), Piece((6,7), 2, player2_img)])


done = False
while not done:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done = True
		elif event.type == pygame.MOUSEBUTTONDOWN:
			move = True
			mouse_loc = mousex, mousey = pygame.mouse.get_pos()
			click_loc = click_x, click_y = mousex % board_width/square_size, mousey % board_height/square_size
			for piece in players[turn].getPieces():
				if(getDist(piece.loc, click_loc) == 0):
					print piece
					active_piece = piece
					move = False
			if move == True and active_piece is not None and getDist(active_piece.loc, click_loc) <= active_piece.speed:
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
				if getDist(active_piece.loc, (x, y)) <= active_piece.speed and not (x is active_piece.loc[0] and y is active_piece.loc[1]):
					pygame.draw.circle(screen, (0,0,255), (x*square_size+(square_size/2), y*square_size+(square_size/2)), square_size/2)

	for player in players:
		for piece in player.pieces:
			screen.blit(piece.img, (piece.loc[0]*square_size+10, piece.loc[1]*square_size+10))

	pygame.display.flip()