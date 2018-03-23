import pygame
import math

pygame.init()
size = width, height = 1000,800
screen = pygame.display.set_mode((size))

player_img = pygame.image.load('img/player.jpg')

board_size = board_width, board_height = 800, 800

square_size = board_width/10

player_loc = (0,0)
speed = 4

def getDist(loc1, loc2):
	return math.sqrt(math.pow((loc1[0]-loc2[0]),2)+math.pow((loc1[1]-loc2[1]),2))

done = False
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    screen.fill((0,0,0))

    if pygame.mouse.get_pressed()[0]:
    	mouse_loc = mousex, mousey = pygame.mouse.get_pos()
    	click_loc = click_x, click_y = mousex % board_width/square_size, mousey % board_height/square_size
    	if getDist(player_loc, click_loc) <= speed:
    		player_loc = click_loc


    for x in range(11):
    	pygame.draw.line(screen, (255,255,255), (square_size*x,0), (square_size*x,board_height))
    	pygame.draw.line(screen, (255,255,255), (0,square_size*x), (board_width, square_size*x))

    for x in range(10):
    	for y in range(10):
    		if(getDist(player_loc, (x, y)) <= speed and not (x is player_loc[0] and y is player_loc[1])):
    			pygame.draw.circle(screen, (0,0,255), (x*square_size+(square_size/2), y*square_size+(square_size/2)), square_size/2)

    screen.blit(player_img, (player_loc[0]*square_size+10, player_loc[1]*square_size+10))

    pygame.display.flip()