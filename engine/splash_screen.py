import pygame
import os

class SplashScreen:
    def __init__(self, window_manager):
        self.window = window_manager
        self.engine_logo_img = None
        
        self.load_images()
        
        self.fade_duration = 1.0
        self.display_duration = 1.5
        
        self.state = "fade_in_powered"
        self.timer = 0.0
        self.alpha = 0
        
        pygame.font.init()
        self.font = pygame.font.Font(None, 20)
        
    def load_images(self):
        engine_logo_path = os.path.join("Assets", "Util", "engine_logo.png")
        
        if os.path.exists(engine_logo_path):
            original_img = pygame.image.load(engine_logo_path).convert_alpha()
            self.engine_logo_img = self.scale_image_to_fit(original_img)
        else:
            self.engine_logo_img = pygame.Surface((200, 100))
            self.engine_logo_img.fill((100, 255, 100))
    
    def scale_image_to_fit(self, image):
        img_width, img_height = image.get_size()
        screen_width, screen_height = self.window.base_width, self.window.base_height
        
        scale_x = screen_width / img_width
        scale_y = screen_height / img_height
        scale = min(scale_x, scale_y) * 0.8
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        scaled_img = pygame.Surface((new_width, new_height))
        scaled_img = pygame.transform.scale(image, (new_width, new_height))
        return scaled_img
    
    def update(self, dt):
        self.timer += dt
        
        if self.state == "fade_in_powered":
            self.alpha = min(255, (self.timer / self.fade_duration) * 255)
            if self.timer >= self.fade_duration:
                self.timer = 0
                self.state = "display_powered"
                
        elif self.state == "display_powered":
            if self.timer >= self.display_duration:
                self.timer = 0
                self.state = "fade_out_powered"
                
        elif self.state == "fade_out_powered":
            self.alpha = max(0, 255 - (self.timer / self.fade_duration) * 255)
            if self.timer >= self.fade_duration:
                self.timer = 0
                self.alpha = 0
                self.state = "fade_in_engine"
                
        elif self.state == "fade_in_engine":
            self.alpha = min(255, (self.timer / self.fade_duration) * 255)
            if self.timer >= self.fade_duration:
                self.timer = 0
                self.state = "display_engine"
                
        elif self.state == "display_engine":
            if self.timer >= self.display_duration:
                self.timer = 0
                self.state = "fade_out_engine"
                
        elif self.state == "fade_out_engine":
            self.alpha = max(0, 255 - (self.timer / self.fade_duration) * 255)
            if self.timer >= self.fade_duration:
                return True
                
        return False
    
    def render(self):
        self.window.clear((0, 0, 0))
        
        if self.state in ["fade_in_powered", "display_powered", "fade_out_powered"]:
            text_surface = self.font.render("powered by", False, (255, 255, 255))
            text_surface = text_surface.convert_alpha()
            text_surface.set_alpha(self.alpha)
            
            text_rect = text_surface.get_rect()
            center_x = (self.window.base_width - text_rect.width) // 2
            center_y = (self.window.base_height - text_rect.height) // 2
            
            self.window.virtual_screen.blit(text_surface, (center_x, center_y))
        else:
            current_img = self.engine_logo_img
            img_copy = current_img.copy()
            img_copy.set_alpha(self.alpha)
            
            img_rect = img_copy.get_rect()
            center_x = (self.window.base_width - img_rect.width) // 2
            center_y = (self.window.base_height - img_rect.height) // 2
            
            self.window.virtual_screen.blit(img_copy, (center_x, center_y))