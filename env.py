import pygame
import Box2D
import time, sys, os
import random

from gymnasium import spaces
import numpy as np

import gymnasium as gym


class DeliveryEnv(gym.Env):
    metadata = {}

    def __init__(self, display=False):


        # gym setup
        self.observation_space = spaces.Box(low=-1000, high=1000, shape=(5,), dtype=np.float32)
        self.action_space = spaces.Box(low=-1000, high=1000, shape=(1,), dtype=np.float32)

        SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
        if display:
            pygame.init()
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


        self.SCREEN_WIDTH = SCREEN_WIDTH
        self.SCREEN_HEIGHT = SCREEN_HEIGHT
        self.TARGET_FPS = 1000 #60
        self.TIME_STEP  = 1.0 / self.TARGET_FPS

        self.clock = pygame.time.Clock()


        self.world = Box2D.b2World(gravity=(0, -9.81))
        PPM = 200     

        WALL_WIDTH = 1 
        WALL_COLOR = (0, 0, 0)
        self.WALL_WIDTH = WALL_WIDTH
        self.WALL_COLOR = WALL_COLOR
        ceiling_body = self.world.CreateStaticBody(position=(0, SCREEN_HEIGHT), shapes=Box2D.b2EdgeShape(vertices=[(0, 0), (SCREEN_WIDTH, 0)]))
        left_wall_body = self.world.CreateStaticBody(position=(0, 0), shapes=Box2D.b2EdgeShape(vertices=[(0, 0), (0, SCREEN_HEIGHT)]))
        right_wall_body = self.world.CreateStaticBody(position=(SCREEN_WIDTH, 0), shapes=Box2D.b2EdgeShape(vertices=[(0, 0), (0, SCREEN_HEIGHT)]))
        ground_body = self.world.CreateStaticBody(position=(0, WALL_WIDTH)) 
        ground_shape = Box2D.b2EdgeShape(vertices=[(0, 0), (SCREEN_WIDTH, 0)])
        ground_fixture = ground_body.CreateFixture(shape=ground_shape, density=1.0, friction=1.0)


        # tray setup
        RECT_COLOR = (255, 0, 0)
        self.RECT_COLOR = RECT_COLOR
        rect_width = 1 * PPM
        self.rect_width = rect_width
        rect_height = 0.25 * PPM
        self.rect_height = rect_height
        rect_center = (rect_width/2, rect_height/2)
        self.rect_center = rect_center
        rect_position = (rect_center[0], rect_center[1])
        self.rect_position = rect_position
        rect_mass = 10
        rect_density = rect_mass * 1 * 0.25 
        rect_friction = 1.0

        self.rect_body = self.world.CreateDynamicBody(position= (rect_position), angle =0.0)
        rect_shape = Box2D.b2PolygonShape(box= rect_center)
        rect_fixture = self.rect_body.CreateFixture(shape=rect_shape, density=rect_density, friction=rect_friction)

        # object on tray
        SQUARE_COLOR = (0, 0, 255)
        self.SQUARE_COLOR = SQUARE_COLOR
        square_width = 0.25 * PPM 
        self.square_width =square_width
        square_height = 0.25 * PPM  
        self.square_height = square_height
        square_center = (square_width/2, square_height/2) 
        self.square_center = square_center
        square_position = (rect_center[0], rect_height+square_height/2)
        self.square_position = square_position
        obj_mass = 0.3
        obj_density = obj_mass * 0.25 * 0.25 
        obj_friction = 1.0

        self.square_body = self.world.CreateDynamicBody(position= square_position, angle =0.0)
        square_shape = Box2D.b2PolygonShape(box=square_center) 
        square_fixture = self.square_body.CreateFixture(shape=square_shape, density=obj_density, friction= obj_friction) 


    def reset(self, seed=None, options=None):
        self.rect_body.linearVelocity = (0, 0)
        self.rect_body.position = self.rect_position
        self.square_body.linearVelocity = (0,0)
        self.square_body.position = self.square_position

        return self.get_observation(), {}


    def get_observation(self):
        diff      =  self.rect_body.position.x - self.square_body.position.x
        return np.array((self.rect_body.position.x, 
                         self.rect_body.linearVelocity.x,
                         self.square_body.position.x,
                         self.square_body.linearVelocity.x,
                         diff))

    def get_reward(self):
        
        diff_x = (self.rect_body.position.x-self.square_body.position.x)
        # reward manipulation
        
        reward = 0 

        # fail delivery
        if diff_x > 30:
            reward += -1

        # success delivery
        if self.rect_body.position.x >=699:
            reward += 1
        
        # distance to the goal
        #reward += 0.001  * (1 - (699 - self.rect_body.position.x)/699.)
        


        return reward


    def terminate_cond(self):

        # calculate object deviation
        diff_x = (self.rect_body.position.x-self.square_body.position.x)
        # reward manipulation
        if diff_x > 30 or self.rect_body.position.x >=699:
            terminated = 1
        else:
            terminated = 0

        return terminated


    def step(self, action):

        # rescale action
        action = float(action) * 10

        self.rect_body.linearVelocity = (action, 0)

        # apply the same action for 10 steps
        skip = 10
        for _ in range(skip):
            self.world.Step(self.TIME_STEP, 1, 1)
            self.clock.tick(self.TARGET_FPS)

        obs = self.get_observation()
        reward = self.get_reward()
        terminal = self.terminate_cond()

        return obs, reward, terminal, False, {}
        
    def flip_y(self, y):
        return 600-y 

    def draw(self):
        rect_pos = self.rect_body.position
        square_pos = self.square_body.position
        rect_rot = self.rect_body.angle
        square_rot = self.square_body.angle

        self.screen.fill((255, 255, 255)) 
        pygame.draw.line(self.screen, self.WALL_COLOR, (0, self.SCREEN_HEIGHT), (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), width = self.WALL_WIDTH)                         # Ground
        pygame.draw.line(self.screen, self.WALL_COLOR, (0, 0), (self.SCREEN_WIDTH, 0), width = self.WALL_WIDTH)                                                 # Ceiling
        pygame.draw.line(self.screen, self.WALL_COLOR, (0, 0), (0, self.SCREEN_WIDTH), width = self.WALL_WIDTH)                                                 # Left-Wall
        pygame.draw.line(self.screen, self.WALL_COLOR, (self.SCREEN_WIDTH, 0), (self.SCREEN_WIDTH, self.SCREEN_HEIGHT), width = self.WALL_WIDTH)                          # Right-wall

        pygame.draw.rect(self.screen, 
            self.RECT_COLOR, 
            pygame.Rect((rect_pos.x-self.rect_center[0],
                self.flip_y(rect_pos.y)-self.rect_center[1]), 
                (self.rect_width, self.rect_height), round=rect_rot))


        pygame.draw.rect(self.screen, 
            self.SQUARE_COLOR, 
            pygame.Rect((square_pos.x-self.square_center[0],
                self.flip_y(square_pos.y)-self.square_center[1]), 
                (self.square_width, self.square_height), round=square_rot))

        pygame.display.flip()
        pygame.display.update()

    def close(self):
        pygame.quit()


if __name__ == "__main__":

    env = DeliveryEnv(display=True)
    env.reset()

    for epoch in range(10):
        env.reset()
        epoch_reward = 0
        num_step = 0
        terminal = False

        while not terminal:
            action = [100]
            obs,reward,terminal,_ ,_ =  env.step(action)
            epoch_reward += reward
            num_step += 1
            env.draw()

        print(epoch_reward)
        print(num_step)


