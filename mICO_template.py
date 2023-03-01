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
    obj_mass = 0.03                                                                                                                             # kg unit
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

    # mICO Initialization
    attempt = 1
    t_prev = 0
    sr_prev = 0
    wa = 0.0
    filename = 'mICO_template.csv'                                                                                                              # Output filename
    redo = 0
    filecheck(filename)                                                                                                                         # Check file write available

    #Internal method for resetting the attempt
    def reset():
        rect_body.linearVelocity = (0, 0)                                                                                                       # MaximumlinearVelocity = 120 m/s
        rect_body.position = rect_position
        square_body.linearVelocity = (0,0)
        square_body.position = square_position

    ################################################################################ End World Initialization ####################################################################################

    ######################################################################################## Game Loop ###########################################################################################

    # Define the main game loop
    while redo < 2:
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
            pass
            rect_body.linearVelocity = (-1500, 0)                                                                                           # For manual test; moving to the left
            print(rect_body.linearVelocity)
        if keys[pygame.K_RIGHT]:
            pass
            rect_body.linearVelocity = (1.5*PPM, 0)                                                                                                # For manual test; moving to the right
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

        ######################################################################################## mICO loop part ###########################################################################################

        # start message: print attempt number
        print('==============================================================================')
        print('attempt: ', attempt)

        # Simulation time
        sim_time = pygame.time.get_ticks()/1000                                                                                                 # second
        print("sim_time: ", sim_time)

        # signal generator
        xc = square_pos.x                                                                                                                       # Current X-position of the square object
        xr = rect_pos.x                                                                                                                         # Reference X-position of the rectangle cart
        so, sp, sr = signal_generator(xc, xr)                                                                                                   

        # Signal log for debugging purpose
        # print("SO: ", so)
        # print("SP: ", sp)
        # print("SR: ", sr)

        # load the adaptive weight
        wa = load(filename)

        # In case of adaptive weight is more than 1, the learning is automatically failed due to the weight updated too fast. Try to tune the learning weight.
        if wa > 1:
            print("Failed on learning")
            time.sleep(30)
            sys.exit()
   
        # When the object is out of the learning area. Reset position, previous reflexive signal and increase attempt
        if so == 0 or sr == 1:
            reset()                                                                                                                            
            sr_prev = 0.0
            print('-----------------------------------------------resetting-----------------------------------------------')
            attempt += 1                                                                                                                      


        else: 
            o_neural, new_w, d, t, s = o_learning(filename, so, sp, sr, sim_time, t_prev, wa, sr_prev)                                          # main mICO method

            # Store the previous time, reflex signal
            t_prev = t
            sr_prev = s

            # variables output log
            # print("w_after:", new_w)
            # print("o_nueral:", o_neural)
            # print("t_prev: ", t)
            # print("s_prev: ",s)

            # convert neural output to rectangle output
            speed = o_speed(o_neural)

            # Save everything to csv file
            save(filename, attempt, sim_time, new_w, sp, sr,  d, o_neural, speed)

            # If the speed is lower than the threshold without reaching the goal, it has to be stopped and move on to the next attempt
            if speed  < 1:
                speed = 0
                reset()
                attempt +=1

            # Output to simulation
            print("o_speed: ", speed)
            rect_body.linearVelocity = (speed, 0)  

            # This condition is used to execute one more attempt to confirm the weight.
            if rect_pos.x >=699:
                reset()
                sr_prev = 0.0
                redo += 1
                attempt +=1

        ###################################################################################### End mICO loop part ##########################################################################################

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


######################################################################################### Simplified mICO (1-dim) part #########################################################################################

def signal_generator(xc,  xr):
    diff_x = abs(xc-xr)                                                         
    
    # Range threshold between current position (object) and reference position (center of the tray)
    et = 10                                                                                                                                # Exemption threshold; allows the object to move without triggering learning mechanism
    pt = 30                                                                                                                                # Predictive threshold; prior signal for the robot to 'soft-adapt' itself (reduce speed without any learning)
    rt = 70                                                                                                                                # Reflexive threshold; later signal used to trigger learning mechanism

    # Conditions for each threshold (with the normalization)
    if diff_x >= 0 and diff_x < et:
        so = 1.0
        sp = 0.0
        sr = 0.0

    elif diff_x >= et and diff_x < pt:
        so = 1.0
        sp = round((diff_x-et)/(pt-et)+0.005, 2)
        sr = 0.0

    elif diff_x >= pt and diff_x < rt:
        so = 1.0
        sp = 1.0
        sr = round((diff_x-pt)/(rt-pt)+0.005,2)
    
    else:
        so = 0.0
        sp = 1.0
        sr = 1.0

    return so, sp, sr

def o_learning(filename, so, sp, sr, t, t_prev, wa, sr_prev):

    # Constant factor
    co = 1
    cp = 0.01
    wr = 1

    # Neural nodes
    so_term = co*so*wa
    sp_term = cp*sp*wa
    sr_term = sr*wr

    # Debugging log
    # print('so_term', so_term)
    # print('sp_term', sp_term)
    # print('sr_term', sr_term)

    # mICO output generated from 
    o_neural = so_term+sp_term+sr_term

    # Update new 
    new_wa, delta = update_weight(sp, sr ,sr_prev, wa, t, t_prev)

    # forward back some values to use as the previous signals
    sr_prev = sr
    t_prev = t

    return o_neural, new_wa, delta, t_prev, sr_prev

def update_weight(sp, sr, sr_prev, wa, t, t_prev):

    # This learning rate has to be adjusted in case that the weight reaches 1 too fast.
    l_rate = 0.01

    # delta terms
    sr_delta = sr-sr_prev
    t_delta = t-t_prev

    # Debugging log
    # print('sr_prev: ', sr_prev)
    # print('sr_delta: ', sr_delta)
    # print('t_delta: ',  t_delta)

    # This condition is used to cover on the first tick of learning
    if t_delta == 0:
        print("no t diff please check or first time")
        delta = 0

    else:
        # This condition is a constraint for learning where we use the rising signal only.
        if sr >=  sr_prev:
            delta = sr_delta/t_delta
    
        else:
            delta = 0.0
            
    # Weight update methods
    wa_delta = l_rate * sp * delta
    new_wa = wa_delta+wa
    
    # Debugging log
    # print('delta: ', delta)
    # print('new_wa:', new_wa)

    return new_wa, delta

def o_speed(o_learning):
    # This is the maximum speed available in the simulation (pixel/s)
    max = 1500
    o_speed = max - (max * o_learning)
    return o_speed

####################################################################################### End Simplified mICO (1-dim) part #######################################################################################


####################################################################################### Data management part #######################################################################################

def filepath(filename):
    script_path = os.path.abspath(__file__)
    script_dir = os.path.split(script_path)[0]
    rel_path = "data/"+filename
    path = os.path.join(script_dir, rel_path)
    #print(path)
    return path

#Create CSV file
def create(filename):
    try:
        #create file
        path = filepath(filename)
        with open(path,'w') as open_dat:
            #create header
            writer = csv.writer(open_dat)
            #Header
            writer.writerow(["Timestamp", "Attempt", "Weight", "Predictive", "Reflexive", "Derivative", "o_neural", "o_speed"])
            print("[INFO]: File: "+filename+" has been created")
    except:
        print("[ERROR]: Cannot create: ", filename)
        time.sleep(30)
        sys.exit()     

def filecheck(filename):
    path = filepath(filename)
    print(path)
    try:
        if (os.path.exists(path) == True):
            print("[INFO]: File exists")
        else:
            print("[INFO]: Creates a new file")
            create(filename)
    except: 
        print("[ERROR]: File check error, please check filename")
        time.sleep(30)
        sys.exit()
   

#Save information to the target file.
def save(filename, attempt, stamp, weight, predict, reflex, derivative, o_nueral, o_speed):
    path = filepath(filename)
    try:
        with open(path,'a', newline='') as open_dat:        #newline='' is added to fix the extra carriage return
            writer = csv.writer(open_dat)
            writer.writerow([stamp, attempt, weight, predict, reflex, derivative, o_nueral, o_speed])
            print("[INFO]: Information has been saved")
    except:
        print("[ERROR]]: Cannot save: ", filename)
        time.sleep(30)
        sys.exit()

#Load weight information from the target file.
def load(filename):
    path = filepath(filename)
    try:        
        with open(path, 'r') as f:
            try:
                last_line = f.readlines()[-1]
                line = last_line.split(',')
                weight = float(line[2])
                return weight
            except:
                print("[INFO]: No trace of previous weight, return 0.0")
                return 0.0

    except:
        print("[ERRROR]: Cannot load weight from: ", filename)
        time.sleep(30)
        sys.exit()

##################################################################################### End Data management part #####################################################################################


# Method use to rearrange the y-position between pygame and Box2D
def flip_y(y):
    return 600-y    #Maximum SCREEN_HEIGHT

if __name__ == "__main__":
    main()