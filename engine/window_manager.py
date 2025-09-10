import pygame
import sys

class WindowManager:
    def __init__(self, width=320, height=180, title="2D Platformer"):
        pygame.init()
        
        pygame.transform.set_smoothscale_backend('GENERIC')
        
        self.base_width = width
        self.base_height = height
        self.scale = self.calculate_scale()
        
        self.screen = pygame.display.set_mode((self.base_width * self.scale, self.base_height * self.scale))
        self.virtual_screen = pygame.Surface((self.base_width, self.base_height))
        
        pygame.display.set_caption(title)
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0
        
    def calculate_scale(self):
        info = pygame.display.Info()
        scale_x = info.current_w // self.base_width
        scale_y = info.current_h // self.base_height
        return max(1, min(scale_x, scale_y))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def clear(self, color=(0, 0, 0)):
        self.virtual_screen.fill(color)
    
    def present(self):
        scaled_surface = pygame.transform.scale(self.virtual_screen, 
                                              (self.base_width * self.scale, self.base_height * self.scale))
        pygame.transform.set_smoothscale_backend('GENERIC')
        self.screen.blit(scaled_surface, (0, 0))
        pygame.display.flip()
        self.dt = self.clock.tick(60) / 1000.0
    
    def quit(self):
        pygame.quit()
        sys.exit()