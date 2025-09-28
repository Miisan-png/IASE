import pygame

class CollisionSystem:
    def __init__(self):
        self.debug_enabled = False
        self.collision_rects = []
        
    def enable_debug(self, enabled=True):
        self.debug_enabled = enabled
        
    def check_horizontal_collision(self, entity, tilemap, dt):
        old_x = entity.x
        entity.x += entity.vel_x * dt
        
        entity_rect = entity.get_rect()
        collision_tiles = tilemap.get_collision_tiles_in_rect(entity_rect)
        
        for tile_rect in collision_tiles:
            if entity_rect.colliderect(tile_rect):
                if entity.vel_x > 0:
                    entity.x = tile_rect.left - entity.width
                elif entity.vel_x < 0:
                    entity.x = tile_rect.right
                entity.vel_x = 0
                break
                
    def check_vertical_collision(self, entity, tilemap, dt):
        old_y = entity.y
        entity.y += entity.vel_y * dt
        
        entity_rect = entity.get_rect()
        collision_tiles = tilemap.get_collision_tiles_in_rect(entity_rect)
        
        was_on_ground = entity.on_ground
        entity.on_ground = False
        
        for tile_rect in collision_tiles:
            if entity_rect.colliderect(tile_rect):
                if entity.vel_y > 0:
                    entity.y = tile_rect.top - entity.height
                    entity.vel_y = 0
                    entity.on_ground = True
                    entity.is_jumping = False
                    entity.jump_time = 0
                elif entity.vel_y < 0:
                    entity.y = tile_rect.bottom
                    entity.vel_y = 0
                    entity.is_jumping = False
                break
                
        if self.debug_enabled:
            self.collision_rects = collision_tiles
            
    def handle_entity_collision(self, entity, tilemap, dt):
        self.check_horizontal_collision(entity, tilemap, dt)
        self.check_vertical_collision(entity, tilemap, dt)
        
    def render_debug(self, screen, camera_x=0, camera_y=0):
        if not self.debug_enabled:
            return
            
        for tile_rect in self.collision_rects:
            debug_rect = pygame.Rect(
                tile_rect.x - camera_x,
                tile_rect.y - camera_y,
                tile_rect.width,
                tile_rect.height
            )
            pygame.draw.rect(screen, (255, 0, 0, 100), debug_rect, 2)
            
    def render_entity_debug(self, screen, entity, camera_x=0, camera_y=0):
        if not self.debug_enabled:
            return
            
        entity_rect = pygame.Rect(
            entity.x - camera_x,
            entity.y - camera_y,
            entity.width,
            entity.height
        )
        
        color = (0, 255, 0) if entity.on_ground else (255, 255, 0)
        pygame.draw.rect(screen, color, entity_rect, 2)
        
        vel_end_x = entity.x - camera_x + entity.vel_x * 0.1
        vel_end_y = entity.y - camera_y + entity.vel_y * 0.1
        
        pygame.draw.line(screen, (0, 0, 255), 
                        (entity.x - camera_x + entity.width//2, entity.y - camera_y + entity.height//2),
                        (vel_end_x + entity.width//2, vel_end_y + entity.height//2), 3)