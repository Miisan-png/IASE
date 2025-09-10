import pygame
from engine.window_manager import WindowManager
from engine.splash_screen import SplashScreen
from core.player import Player

class Game:
    def __init__(self):
        self.window = WindowManager()
        self.splash = SplashScreen(self.window)
        self.player = Player(160, 90)
        self.game_started = False
        
    def update(self):
        if not self.game_started:
            splash_done = self.splash.update(self.window.dt)
            if splash_done:
                self.game_started = True
        else:
            keys = pygame.key.get_pressed()
            self.player.update(keys, self.window.dt)
        
    def render(self):
        if not self.game_started:
            self.splash.render()
        else:
            self.window.clear((50, 120, 200))
            self.player.render(self.window.virtual_screen)
        
    def run(self):
        while self.window.running:
            self.window.handle_events()
            self.update()
            self.render()
            self.window.present()
        
        self.window.quit()