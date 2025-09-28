import pygame

class DebugSystem:
    def __init__(self):
        self.enabled = False
        self.font = None
        self.info_lines = []
        
    def enable(self, enabled=True):
        self.enabled = enabled
        if self.enabled and not self.font:
            pygame.font.init()
            self.font = pygame.font.Font(None, 16)
            
    def toggle(self):
        self.enable(not self.enabled)
        
    def add_info(self, label, value):
        if self.enabled:
            self.info_lines.append(f"{label}: {value}")
            
    def clear_info(self):
        self.info_lines = []
        
    def render_info(self, screen):
        if not self.enabled or not self.font:
            return
            
        y_offset = 5
        for line in self.info_lines:
            text_surface = self.font.render(line, False, (255, 255, 255))
            
            bg_rect = pygame.Rect(5, y_offset, text_surface.get_width() + 4, text_surface.get_height() + 2)
            pygame.draw.rect(screen, (0, 0, 0, 128), bg_rect)
            
            screen.blit(text_surface, (7, y_offset + 1))
            y_offset += 18
            
    def render_fps(self, screen, clock):
        if not self.enabled or not self.font:
            return
            
        fps = int(clock.get_fps())
        fps_text = f"FPS: {fps}"
        text_surface = self.font.render(fps_text, False, (255, 255, 255))
        
        screen_width = screen.get_width()
        x_pos = screen_width - text_surface.get_width() - 7
        
        bg_rect = pygame.Rect(x_pos - 2, 5, text_surface.get_width() + 4, text_surface.get_height() + 2)
        pygame.draw.rect(screen, (0, 0, 0, 128), bg_rect)
        
        screen.blit(text_surface, (x_pos, 7))
        
    def render_grid(self, screen, tile_size, camera_x=0, camera_y=0):
        if not self.enabled:
            return
            
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        start_x = int(camera_x // tile_size) * tile_size - camera_x
        start_y = int(camera_y // tile_size) * tile_size - camera_y
        
        x = start_x
        while x < screen_width:
            pygame.draw.line(screen, (100, 100, 100, 50), (x, 0), (x, screen_height))
            x += tile_size
            
        y = start_y
        while y < screen_height:
            pygame.draw.line(screen, (100, 100, 100, 50), (0, y), (screen_width, y))
            y += tile_size