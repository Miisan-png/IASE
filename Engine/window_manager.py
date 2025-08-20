import pygame
import sys

class WindowManager:
    def __init__(self, title="Mushroom Lab"):
        pygame.init()
        self.title = title
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.running = True
        self.width = self.screen.get_width()
        self.height = self.screen.get_height()
        
        
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def clear_screen(self):
        self.screen.fill((0, 0, 0))
    
    def update_display(self):
        pygame.display.flip()
        self.clock.tick(60)
    
    def quit(self):
        pygame.quit()
        sys.exit()