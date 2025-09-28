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
        
        self.max_speed = 120
        self.acceleration = 600
        self.friction = 1200
        self.air_friction = 300
        self.gravity = 800
        self.max_fall_speed = 300
        
        self.jump_force = 220
        self.max_jump_time = 0.2
        self.jump_time = 0
        self.is_jumping = False
        self.on_ground = False
        self.coyote_time = 0.08
        self.coyote_timer = 0
        self.jump_buffer = 0.1
        self.jump_buffer_timer = 0
        
        self.surface = pygame.Surface((self.width, self.height))
        self.surface.fill((255, 100, 100))
        
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
        
    def update(self, keys, dt, collision_system=None, tilemap=None):
        self.handle_input(keys, dt)
        self.apply_physics(dt)
        
        if collision_system and tilemap:
            collision_system.handle_entity_collision(self, tilemap, dt)
        
    def handle_input(self, keys, dt):
        moving = False
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x -= self.acceleration * dt
            moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x += self.acceleration * dt
            moving = True
            
        if not moving:
            current_friction = self.friction if self.on_ground else self.air_friction
            if abs(self.vel_x) < 20:
                self.vel_x = 0
            elif self.vel_x > 0:
                self.vel_x = max(0, self.vel_x - current_friction * dt)
            elif self.vel_x < 0:
                self.vel_x = min(0, self.vel_x + current_friction * dt)
        
        self.vel_x = max(-self.max_speed, min(self.max_speed, self.vel_x))
        
        if keys[pygame.K_SPACE] or keys[pygame.K_x] or keys[pygame.K_UP] or keys[pygame.K_w]:
            if not self.is_jumping and (self.on_ground or self.coyote_timer > 0):
                self.start_jump()
            elif self.is_jumping and self.jump_time < self.max_jump_time:
                self.continue_jump(dt)
        else:
            if self.is_jumping:
                self.is_jumping = False
                if self.vel_y < -self.jump_force * 0.3:
                    self.vel_y = -self.jump_force * 0.3
                    
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
        jump_strength = jump_strength * jump_strength
        self.vel_y -= self.jump_force * 0.8 * jump_strength * dt
        
    def apply_physics(self, dt):
        if not self.on_ground:
            self.vel_y += self.gravity * dt
            self.vel_y = min(self.vel_y, self.max_fall_speed)
            self.coyote_timer -= dt
        else:
            self.coyote_timer = self.coyote_time
            
    def render(self, screen, camera_x=0, camera_y=0):
        screen_x = self.x - camera_x
        screen_y = self.y - camera_y
        screen.blit(self.surface, (int(screen_x), int(screen_y)))