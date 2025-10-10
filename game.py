import pygame
import os
from engine.window_manager import WindowManager
from engine.splash_screen import SplashScreen
# === STATE MANAGER INTEGRATION (Added by teammate for pause/death menus) ===
from engine.state_manager import StateManager, GameState
# ========================================================================
from Core.player import Player
from Core.tilemap import Tilemap
from Core.collision_system import CollisionSystem
from Core.debug_system import DebugSystem

class Game:
    def __init__(self):
        self.window = WindowManager()
        self.splash = SplashScreen(self.window)
        # === STATE MANAGER INITIALIZATION (Added by teammate) ===
        self.state_manager = StateManager(self.window)
        # ========================================================
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
        
    # === STATE MANAGER: Menu action handler (Added by teammate) ===
    def handle_menu_action(self, menu_result):
        """Handle actions from pause/death menus"""
        action = menu_result.get("action")
        
        if action == "resume":
            # Game resumes automatically via state change
            pass
        elif action == "respawn":
            # Reset player to respawn position
            respawn_pos = menu_result.get("position", (32, 32))
            self.player.x, self.player.y = respawn_pos
            self.player.vel_x = 0
            self.player.vel_y = 0
        elif action == "restart_level":
            # Reset player to starting position
            self.player.x, self.player.y = 32, 32
            self.player.vel_x = 0
            self.player.vel_y = 0
            # Could reload level here if needed
        elif action == "main_menu":
            # TODO: Implement main menu transition
            # For now, just restart the level
            self.player.x, self.player.y = 32, 32
            self.player.vel_x = 0
            self.player.vel_y = 0
            self.state_manager.change_state(GameState.PLAYING)
        elif action == "quit":
            # Quit the game
            self.window.running = False
    # =============================================================
        
    def update(self):
        # === STATE MANAGER UPDATE (Added by teammate) ===
        # Only update state manager if it exists and pygame is initialized
        if hasattr(self, 'state_manager') and self.state_manager:
            self.state_manager.update(self.window.dt)
            
            # Handle pause menu input if game is paused
            if self.state_manager.is_game_paused():
                keys = pygame.key.get_pressed()
                menu_result = self.state_manager.handle_pause_input(keys, self.window.dt)
                if menu_result:
                    self.handle_menu_action(menu_result)
                return
            
            # Handle death menu input if player is dead
            if self.state_manager.is_player_dead():
                keys = pygame.key.get_pressed()
                menu_result = self.state_manager.handle_death_input(keys, self.window.dt)
                if menu_result:
                    self.handle_menu_action(menu_result)
                return
        # ==============================================
        
        if not self.game_started:
            splash_done = self.splash.update(self.window.dt)
            if splash_done:
                self.game_started = True
                # === STATE MANAGER: Set to playing state ===
                if hasattr(self, 'state_manager') and self.state_manager:
                    self.state_manager.change_state(GameState.PLAYING)
                # ==========================================
        else:
            keys = pygame.key.get_pressed()
            
            # === STATE MANAGER: Check for pause input ===
            if hasattr(self, 'state_manager') and self.state_manager:
                if self.state_manager.check_for_pause(keys, self.window.dt):
                    return  # Game was paused, skip rest of update
            # ============================================
            
            self.handle_debug_input(keys)
            
            self.player.update(keys, self.window.dt, self.collision_system, self.tilemap)
            
            # === STATE MANAGER: Example death trigger (you can customize this) ===
            # Check if player fell off the world or other death conditions
            if hasattr(self, 'state_manager') and self.state_manager and self.player.y > 1000:  # Fell off bottom of world
                self.state_manager.trigger_death("Fell off the world!", (32, 32))
                return
            # ====================================================================
            
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
                # === STATE MANAGER: Add state info to debug ===
                if hasattr(self, 'state_manager') and self.state_manager:
                    self.debug_system.add_info("Game State", self.state_manager.get_current_state().value)
                # ==============================================
        
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
            
            # === STATE MANAGER: Render pause/death menus (Added by teammate) ===
            if hasattr(self, 'state_manager') and self.state_manager:
                self.state_manager.render(self.window.virtual_screen)
            # ===================================================================
        
    def run(self):
        while self.window.running:
            self.window.handle_events()
            self.update()
            self.render()
            self.window.present()
        
        self.window.quit()