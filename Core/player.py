import pygame
import math

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 16
        self.height = 16
        
        self.vel_x = 0
        self.vel_y = 0
        
        self.max_speed = 80
        self.acceleration = 400
        self.friction = 800
        self.gravity = 400
        self.max_fall_speed = 200
        
        self.jump_force = 150
        self.max_jump_time = 0.25
        self.jump_time = 0
        self.is_jumping = False
        self.on_ground = False
        self.coyote_time = 0.1
        self.coyote_timer = 0
        self.jump_buffer = 0.15
        self.jump_buffer_timer = 0
        
        self.ground_y = 140
        
        self.surface = pygame.Surface((self.width, self.height))
        self.surface.fill((255, 100, 100))
        
    def update(self, keys, dt):
        self.handle_input(keys, dt)
        self.apply_physics(dt)
        self.check_ground_collision()
        
    def handle_input(self, keys, dt):
        if keys[pygame.K_LEFT]:
            self.vel_x -= self.acceleration * dt
        elif keys[pygame.K_RIGHT]:
            self.vel_x += self.acceleration * dt
        else:
            if abs(self.vel_x) < 10:
                self.vel_x = 0
            elif self.vel_x > 0:
                self.vel_x = max(0, self.vel_x - self.friction * dt)
            elif self.vel_x < 0:
                self.vel_x = min(0, self.vel_x + self.friction * dt)
        
        self.vel_x = max(-self.max_speed, min(self.max_speed, self.vel_x))
        
        if keys[pygame.K_x]:
            if not self.is_jumping and (self.on_ground or self.coyote_timer > 0):
                self.start_jump()
            elif self.is_jumping and self.jump_time < self.max_jump_time:
                self.continue_jump(dt)
            else:
                self.jump_buffer_timer = self.jump_buffer
        else:
            self.is_jumping = False
            self.jump_time = self.max_jump_time
            
        if self.jump_buffer_timer > 0:
            self.jump_buffer_timer -= dt
            if (self.on_ground or self.coyote_timer > 0) and not self.is_jumping:
                self.start_jump()
                self.jump_buffer_timer = 0
                
    def start_jump(self):
        self.vel_y = -self.jump_force
        self.is_jumping = True
        self.jump_time = 0
        self.on_ground = False
        self.coyote_timer = 0
        
    def continue_jump(self, dt):
        self.jump_time += dt
        jump_strength = 1.0 - (self.jump_time / self.max_jump_time)
        self.vel_y -= self.jump_force * 0.5 * jump_strength * dt
        
    def apply_physics(self, dt):
        if not self.on_ground:
            self.vel_y += self.gravity * dt
            self.vel_y = min(self.vel_y, self.max_fall_speed)
            self.coyote_timer -= dt
        else:
            self.coyote_timer = self.coyote_time
            
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        
    def check_ground_collision(self):
        if self.y + self.height >= self.ground_y:
            self.y = self.ground_y - self.height
            if self.vel_y > 0:
                self.vel_y = 0
                self.on_ground = True
                self.is_jumping = False
                self.jump_time = 0
        else:
            self.on_ground = False
            
    def render(self, screen):
        screen.blit(self.surface, (int(self.x), int(self.y)))