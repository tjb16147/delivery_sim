# Important note: pygame and box2d has different starting axis
# pygame: (0,0) at the top-left (y-down)
# Box2D: (0,0) at the bottom-left (y-up)

import pygame
import Box2D
import time, sys, csv, os

def main():

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

    # Objects information
    # rect_mass = rect_fixture.body.mass
    # rect_inertia = rect_fixture.body.inertia
    # print(f"Rectangle mass: {rect_mass:.2f}, inertia: {rect_inertia:.2f}")
    # square_mass = square_fixture.body.mass
    # square_inertia = square_fixture.body.inertia
    # print(f"Square mass: {square_mass:.2f}, inertia: {square_inertia:.2f}")

    # Define the Pygame clock
    clock = pygame.time.Clock()
                                                                                                                     # Check file write available

    #Internal method for resetting the attempt
    def reset():
        rect_body.linearVelocity = (0, 0)                                                                                                       # MaximumlinearVelocity = 120 m/s
        rect_body.position = rect_position
        square_body.linearVelocity = (0,0)
        square_body.position = square_position

    ################################################################################ End World Initialization ####################################################################################

    ######################################################################################## Game Loop ###########################################################################################

    # Define the main game loop
    while True:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # Handle key presses
        ## LinearVelocity is pixel/second (considering on PPM) i.e., if we want 2 m/s then we should use 2*PPM = 400
        ## The rect_body.linearVelocity() will be the major output method in case of applying the other learning.
        ## In this case we use the velocity unit of 1500 to make the object intentionally slide off the tray. The speed lower than that does not trigger the learning as it does not move through the reflexive area.
        ## Enable the comment to manually control the tray with left and right arrow at 1500 pixel/s

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            rect_body.linearVelocity = (-1500, 0)                                                                                           # For manual test; moving to the left
            print(rect_body.linearVelocity)
        if keys[pygame.K_RIGHT]:
            rect_body.linearVelocity = (8, 0)                                                                                                # For manual test; moving to the right
            print(rect_body.linearVelocity)
        if keys[pygame.K_DOWN]:
            rect_body.linearVelocity = (0, 0)                                                                                                # For manual test; moving to the right
            print(rect_body.linearVelocity)

        if keys[pygame.K_r]:                                                                                                                    
            reset()                                                                                                                             # For manula test; manual reset position
        if keys[pygame.K_ESCAPE]:
            pygame.quit()
            exit()

        # Get the position and rotation of the rectangle/square
        rect_pos = rect_body.position
        rect_rot = rect_body.angle
        square_pos = square_body.position
        square_rot = square_body.angle

        print('Rectangle position: ',rect_pos)
        print('Square position:', square_pos)

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
        clock.tick(60)                                                                                                                     # Limit the Pygame frame rate

    print('Done simulation')
    pygame.quit()                                                                                                                          # Quit Pygame

    ###################################################################################### End Game Loop #########################################################################################

# Method use to rearrange the y-position between pygame and Box2D
def flip_y(y):
    return 600-y    #Maximum SCREEN_HEIGHT

if __name__ == "__main__":
    main()