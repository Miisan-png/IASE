import pygame
import json
import os

class Tilemap:
    def __init__(self):
        self.tile_size = 16
        self.grid_width = 0
        self.grid_height = 0
        self.world_data = []
        self.collision_data = []
        self.tileset_image = None
        self.tile_surfaces = []
        
    def load_tilemap(self, filepath):
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            self.tile_size = data.get('tile_size', 16)
            self.grid_width = data.get('grid_width', 100)
            self.grid_height = data.get('grid_height', 100)
            self.world_data = data.get('world_data', [])
            self.collision_data = data.get('collision_data', [])
            
            return True
        except Exception as e:
            print(f"Failed to load tilemap: {e}")
            return False
    
    def load_tileset(self, tileset_path):
        try:
            self.tileset_image = pygame.image.load(tileset_path).convert_alpha()
            self.extract_tiles()
            return True
        except Exception as e:
            print(f"Failed to load tileset: {e}")
            return False
    
    def extract_tiles(self):
        if not self.tileset_image:
            return
        
        self.tile_surfaces = []
        tiles_x = self.tileset_image.get_width() // self.tile_size
        tiles_y = self.tileset_image.get_height() // self.tile_size
        
        for y in range(tiles_y):
            for x in range(tiles_x):
                rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                tile_surface = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                tile_surface.blit(self.tileset_image, (0, 0), rect)
                self.tile_surfaces.append(tile_surface)
    
    def get_tile_at_position(self, x, y):
        grid_x = int(x // self.tile_size)
        grid_y = int(y // self.tile_size)
        
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return self.world_data[grid_y][grid_x]
        return 0
    
    def is_collision_at_position(self, x, y):
        grid_x = int(x // self.tile_size)
        grid_y = int(y // self.tile_size)
        
        if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
            return self.collision_data[grid_y][grid_x]
        return False
    
    def check_collision_rect(self, rect):
        left = rect.left
        right = rect.right
        top = rect.top
        bottom = rect.bottom
        
        corners = [
            (left, top),
            (right - 1, top),
            (left, bottom - 1),
            (right - 1, bottom - 1)
        ]
        
        for x, y in corners:
            if self.is_collision_at_position(x, y):
                return True
        return False
    
    def get_collision_tiles_in_rect(self, rect):
        collision_tiles = []
        
        start_x = max(0, int(rect.left // self.tile_size))
        end_x = min(self.grid_width, int(rect.right // self.tile_size) + 1)
        start_y = max(0, int(rect.top // self.tile_size))
        end_y = min(self.grid_height, int(rect.bottom // self.tile_size) + 1)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                if self.collision_data[y][x]:
                    tile_rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                    collision_tiles.append(tile_rect)
        
        return collision_tiles
    
    def render(self, screen, camera_x=0, camera_y=0):
        if not self.tile_surfaces or not self.world_data:
            return
        
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        start_x = max(0, int(camera_x // self.tile_size))
        end_x = min(self.grid_width, int((camera_x + screen_width) // self.tile_size) + 1)
        start_y = max(0, int(camera_y // self.tile_size))
        end_y = min(self.grid_height, int((camera_y + screen_height) // self.tile_size) + 1)
        
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile_id = self.world_data[y][x]
                if tile_id > 0 and tile_id <= len(self.tile_surfaces):
                    screen_x = x * self.tile_size - camera_x
                    screen_y = y * self.tile_size - camera_y
                    screen.blit(self.tile_surfaces[tile_id - 1], (screen_x, screen_y))