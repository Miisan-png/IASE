import pygame
import os
from engine.window_manager import WindowManager
from engine.splash_screen import SplashScreen
from Core.player import Player
from Core.tilemap import Tilemap
from Core.collision_system import CollisionSystem
from Core.debug_system import DebugSystem

class Game:
    def __init__(self):
        self.window = WindowManager()
        self.splash = SplashScreen(self.window)
        self.player = Player(32, 32)
        self.tilemap = Tilemap()
        self.collision_system = CollisionSystem()
        self.debug_system = DebugSystem()
        self.game_started = False
        
        self.camera_x = 0
        self.camera_y = 0
        
        self.load_level()
        
    def load_level(self):
        tilemap_path = os.path.join("Assets","lvl.json")
        tileset_path = os.path.join("Assets","world_tileset.png")
        
        if os.path.exists(tilemap_path):
            self.tilemap.load_tilemap(tilemap_path)
        
        if os.path.exists(tileset_path):
            self.tilemap.load_tileset(tileset_path)
        
    def handle_debug_input(self, keys):
        if keys[pygame.K_F1]:
            self.debug_system.toggle()
            self.collision_system.enable_debug(self.debug_system.enabled)
        
    def update_camera(self):
        target_x = self.player.x - self.window.base_width // 2
        target_y = self.player.y - self.window.base_height // 2
        
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
        
        world_width = self.tilemap.grid_width * self.tilemap.tile_size
        world_height = self.tilemap.grid_height * self.tilemap.tile_size
        
        self.camera_x = max(0, min(self.camera_x, world_width - self.window.base_width))
        self.camera_y = max(0, min(self.camera_y, world_height - self.window.base_height))
        
    def update(self):
        if not self.game_started:
            splash_done = self.splash.update(self.window.dt)
            if splash_done:
                self.game_started = True
        else:
            keys = pygame.key.get_pressed()
            self.handle_debug_input(keys)
            
            self.player.update(keys, self.window.dt, self.collision_system, self.tilemap)
            self.update_camera()
            
            if self.debug_system.enabled:
                self.debug_system.clear_info()
                self.debug_system.add_info("Player X", f"{self.player.x:.1f}")
                self.debug_system.add_info("Player Y", f"{self.player.y:.1f}")
                self.debug_system.add_info("Vel X", f"{self.player.vel_x:.1f}")
                self.debug_system.add_info("Vel Y", f"{self.player.vel_y:.1f}")
                self.debug_system.add_info("On Ground", self.player.on_ground)
                self.debug_system.add_info("Camera X", f"{self.camera_x:.1f}")
                self.debug_system.add_info("Camera Y", f"{self.camera_y:.1f}")
        
    def render(self):
        if not self.game_started:
            self.splash.render()
        else:
            self.window.clear((135, 206, 235))
            
            self.tilemap.render(self.window.virtual_screen, self.camera_x, self.camera_y)
            self.player.render(self.window.virtual_screen, self.camera_x, self.camera_y)
            
            if self.debug_system.enabled:
                self.debug_system.render_grid(self.window.virtual_screen, self.tilemap.tile_size, self.camera_x, self.camera_y)
                self.collision_system.render_debug(self.window.virtual_screen, self.camera_x, self.camera_y)
                self.collision_system.render_entity_debug(self.window.virtual_screen, self.player, self.camera_x, self.camera_y)
                
            self.debug_system.render_info(self.window.virtual_screen)
            self.debug_system.render_fps(self.window.virtual_screen, self.window.clock)
        
    def run(self):
        while self.window.running:
            self.window.handle_events()
            self.update()
            self.render()
            self.window.present()
        
        self.window.quit()