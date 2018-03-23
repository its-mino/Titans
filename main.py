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

class Player:
	speed = 4
	def __init__(self, loc, img):
		self.loc = loc
		self.img = img

def getDist(loc1, loc2):
	return math.sqrt(math.pow((loc1[0]-loc2[0]),2)+math.pow((loc1[1]-loc2[1]),2))

players = [Player((1,1), player1_img), Player((6,5), player2_img)]

done = False
while not done:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			done = True
		elif event.type == pygame.MOUSEBUTTONDOWN:
			mouse_loc = mousex, mousey = pygame.mouse.get_pos()
			click_loc = click_x, click_y = mousex % board_width/square_size, mousey % board_height/square_size
			if getDist(players[turn].loc, click_loc) <= players[turn].speed:
				players[turn].loc = click_loc
				turn = (turn+1)%len(players)
				print turn

	screen.fill((0,0,0))

	for x in range(11):
		pygame.draw.line(screen, (255,255,255), (square_size*x,0), (square_size*x,board_height))
		pygame.draw.line(screen, (255,255,255), (0,square_size*x), (board_width, square_size*x))

	for x in range(10):
		for y in range(10):
			if(getDist(players[turn].loc, (x, y)) <= players[turn].speed and not (x is players[turn].loc[0] and y is players[turn].loc[1])):
				pygame.draw.circle(screen, (0,0,255), (x*square_size+(square_size/2), y*square_size+(square_size/2)), square_size/2)

	for player in players:
		screen.blit(player.img, (player.loc[0]*square_size+10, player.loc[1]*square_size+10))

	pygame.display.flip()