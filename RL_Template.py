# Important note: pygame and box2d has different starting axis
# pygame: (0,0) at the top-left (y-down)
# Box2D: (0,0) at the bottom-left (y-up)

import pygame
import Box2D
import time, sys, csv, os
import random

#################################################################################### World Initialization ####################################################################################

# Pygame initialization
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600                                                                                                      # Define the size of the screen
pygame.init()                                                                                                                               # Initialize Pygame
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))                                                                             # Create the screen
pygame.display.set_caption("modified ICO simulation")                                                                                       # Set the title of the screen

# Box2D Initialization
world = Box2D.b2World(gravity=(0, -9.81))                                                                                                   # Define the Box2D world with gravity
PPM = 200                                                                                                                                   # Pixel per meter; meaning that this simulation is 4m distance with 3m height

# Wall Initialization
WALL_WIDTH = 1                                                                                                                              # 1-Pixel
WALL_COLOR = (0, 0, 0)                                                                                                                      # Black

# Box2DWall located at each edge of the screen (y-up)           
ceiling_body = world.CreateStaticBody(position=(0, SCREEN_HEIGHT), shapes=Box2D.b2EdgeShape(vertices=[(0, 0), (SCREEN_WIDTH, 0)]))   
left_wall_body = world.CreateStaticBody(position=(0, 0), shapes=Box2D.b2EdgeShape(vertices=[(0, 0), (0, SCREEN_HEIGHT)]))
right_wall_body = world.CreateStaticBody(position=(SCREEN_WIDTH, 0), shapes=Box2D.b2EdgeShape(vertices=[(0, 0), (0, SCREEN_HEIGHT)]))
ground_body = world.CreateStaticBody(position=(0, WALL_WIDTH))    
ground_shape = Box2D.b2EdgeShape(vertices=[(0, 0), (SCREEN_WIDTH, 0)])
ground_fixture = ground_body.CreateFixture(shape=ground_shape, density=1.0, friction=1.0)

# Agent
# Rectangle Initialization
RECT_COLOR = (255, 0, 0)                                                                                                                    # Red
rect_width = 1 * PPM                                                                                                                        # 200 pxl; 1m
rect_height = 0.25 * PPM                                                                                                                    # 50 pxl; 0.25m
rect_center = (rect_width/2, rect_height/2)                                                                                                 # Object center-point
rect_position = (rect_center[0], rect_center[1])                                                                                            # location to place rectangle

# Tray mass and friction; This is fixed to 10kg (if tray mass is less than the obj mass, it will partly submerged the tray into the ground)
rect_mass = 10                                                                                                                                    # kg unit
rect_density = rect_mass * 1 * 0.25                                                                                                            # area; sq.meter unit
rect_friction = 1.0

# Box2Drect located at the left-bottom of the screen (y-up)
rect_body = world.CreateDynamicBody(position= (rect_position), angle =0.0)
rect_shape = Box2D.b2PolygonShape(box= rect_center)
rect_fixture = rect_body.CreateFixture(shape=rect_shape, density=rect_density, friction=rect_friction)                                                         # 10kg tray; mass(kg) = density*area(cm^2)

# Square Initialization
SQUARE_COLOR = (0, 0, 255)                                                                                                                  # Blue
square_width = 0.25 * PPM                                                                                                                   # 50 pxl
square_height = 0.25 * PPM                                                                                                                  # 50 pxl
square_center = (square_width/2, square_height/2)                                                                                           # Object center-point
square_position = (rect_center[0], rect_height+square_height/2)                                                                             # location to place square; same x-pos, y-pos = rect_height+center_sq

# Object mass and friction
## This part can be edited to change the property of the object
## Note: if the object size is changed, its initial position between box2d and pygame should be recalibrated
obj_mass = 0.3                                                                                                                             # kg unit
obj_density = obj_mass * 0.25 * 0.25                                                                                                        # area; sq.meter unit
obj_friction = 1.0

# Box2Drect located at the left-bottom of the screen (y-up)
square_body = world.CreateDynamicBody(position= square_position, angle =0.0)
square_shape = Box2D.b2PolygonShape(box=square_center) 
square_fixture = square_body.CreateFixture(shape=square_shape, density=obj_density, friction= obj_friction)                                                 #

# Define the Pygame clock
clock = pygame.time.Clock()
                                                                                                                    # Check file write available
#Internal method for resetting the attempt
def reset():
    rect_body.linearVelocity = (0, 0)                                                                                                       # MaximumlinearVelocity = 120 m/s
    rect_body.position = rect_position
    square_body.linearVelocity = (0,0)
    square_body.position = square_position
    # technically same position
    obs = 0
    info = 'reset'
    return obs, info

################################################################################ End World Initialization ####################################################################################
# environment is included in step
def step(action):

    ######################################################################################## Game Loop ###########################################################################################
    sim_time = pygame.time.get_ticks()/1000                                                                                                 # second
    # modify this for time limit to truncated the attempt
    limit = sim_time + 150

    # Define the main game loop
    while rect_body.position.x <= 699:

        # update time
        sim_time = pygame.time.get_ticks()/1000                                                                                                 # second


        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # Get the position and rotation of the rectangle/square
        rect_pos = rect_body.position
        square_pos = square_body.position
        rect_rot = rect_body.angle
        square_rot = square_body.angle

        diff_x = abs(rect_pos.x-square_pos.x)
        rect_body.linearVelocity = (action, 0)  

        if diff_x <= 30 and sim_time <= limit:
            success = True       
        else:
            success = False
            break

        ##################################################################################### Continue Game Loop ###########################################################################################

        screen.fill((255, 255, 255))                                                                                                        # Clear the screen
        
        # Draw elements on Pygame (y-down)
        # Draw walls
        pygame.draw.line(screen, WALL_COLOR, (0, SCREEN_HEIGHT), (SCREEN_WIDTH, SCREEN_HEIGHT), width = WALL_WIDTH)                         # Ground
        pygame.draw.line(screen, WALL_COLOR, (0, 0), (SCREEN_WIDTH, 0), width = WALL_WIDTH)                                                 # Ceiling
        pygame.draw.line(screen, WALL_COLOR, (0, 0), (0, SCREEN_WIDTH), width = WALL_WIDTH)                                                 # Left-Wall
        pygame.draw.line(screen, WALL_COLOR, (SCREEN_WIDTH, 0), (SCREEN_WIDTH, SCREEN_HEIGHT), width = WALL_WIDTH)                          # Right-wall

        # Draw rectangle; Rect(left, top, width, height)
        pygame.draw.rect(screen, RECT_COLOR, pygame.Rect((rect_pos.x-rect_center[0],flip_y(rect_pos.y)-rect_center[1]), (rect_width, rect_height), round=rect_rot))

        # Draw square
        pygame.draw.rect(screen, SQUARE_COLOR, pygame.Rect((square_pos.x-square_center[0],flip_y(square_pos.y)-square_center[1]), (square_width, square_height), round=square_rot))

        world.Step(1/60, 1, 1)                                                                                                             # Step the Box2D world; step(timestep, vel_step, pos_step)
        pygame.display.update()                                                                                                            # Update the Pygame display
        clock.tick(60)
             
    if success:
        reward = 10
        info = 'success'
    else:
        reward = -1
        info = 'failed'

    terminated = 1

    # observation is the last diff_x from each step
    obs = diff_x
    truncated = 0

    return obs, reward, terminated, truncated, info

    # print('Done simulation')
    # pygame.quit()                                                                                                                          # Quit Pygame

    ###################################################################################### End Game Loop #########################################################################################

####################################################################################### RL part #######################################################################################

def policy():

    # replace with policy; for now it's random speed
    result = random.randint(0,1500)
    return result


def main():
    # Initialized reset
    reset()
    for _ in range(1500):
        print('=====attempt '+str(_+1)+' ======', )
        action = policy()
    
        observation, reward, terminated, truncated, info = step(action)
        if terminated or truncated:
            reset()
        print('action: ', action)
        print('observation: ', observation)
        print('reward:', reward)        
        print('info: ', info)



####################################################################################### End RL part #######################################################################################

# Method use to rearrange the y-position between pygame and Box2D
def flip_y(y):
    return 600-y    #Maximum SCREEN_HEIGHT

if __name__ == "__main__":
    main()


'''
obs: last diff_x from each attempt
action: random speed from 0 to 1500 (can be replaced by policy)
step: 1 attempt of delivery
reward: + successful & stay within diff < 30 unit; else - failed
terminated: diff > 30 unit
truncated: maximum time limit for the attempt
'''