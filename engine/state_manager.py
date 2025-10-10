import pygame
from enum import Enum

class GameState(Enum):
    SPLASH = "splash"
    PLAYING = "playing"
    PAUSED = "paused"
    DEATH = "death"
    GAME_OVER = "game_over"

class StateManager:
    def __init__(self, window_manager):
        self.window = window_manager
        self.current_state = GameState.SPLASH
        self.previous_state = None
        
        # Menu properties
        self.menu_font_large = None
        self.menu_font_medium = None
        self.menu_font_small = None
        self.selected_option = 0
        self.menu_options = []
        
        # Death system properties
        self.death_reason = ""
        self.respawn_position = (32, 32)  # Default spawn
        self.death_timer = 0.0
        self.death_delay = 1.0  # Delay before showing death menu
        
        # Pause system properties
        self.pause_overlay_alpha = 128
        
        # Key press tracking to prevent menu spam
        self.key_pressed = {}
        self.key_cooldown = 0.2
        self.key_timers = {}

        # Audio settings (0-100)
        self.sfx_volume = 100
        self.bgm_volume = 100
        self.in_options = False
        self.options_selected = 0  # 0 = SFX, 1 = BGM, 2 = Back

        self.init_fonts()
        
    def init_fonts(self):
        """Initialize fonts for menu rendering"""
        # Scale font sizes based on window base height so UI scales with resolution
        base_h = max(120, getattr(self.window, 'base_height', 180))
        large_size = max(20, int(base_h * 0.18))
        medium_size = max(14, int(base_h * 0.10))
        small_size = max(12, int(base_h * 0.06))
        # Hint font - slightly larger and clearer for on-screen hints
        hint_size = max(14, int(base_h * 0.045))
        try:
            self.menu_font_large = pygame.font.Font(None, large_size)
            self.menu_font_medium = pygame.font.Font(None, medium_size)
            self.menu_font_small = pygame.font.Font(None, small_size)
            self.hint_font = pygame.font.Font(None, hint_size)
        except Exception:
            # Fallback to default sizes
            self.menu_font_large = pygame.font.Font(None, large_size)
            self.menu_font_medium = pygame.font.Font(None, medium_size)
            self.menu_font_small = pygame.font.Font(None, small_size)
            self.hint_font = pygame.font.Font(None, hint_size)

        # Slider and layout measurements
        self.slider_width = max(100, int(getattr(self.window, 'base_width', 320) * 0.6))
        self.menu_spacing = max(20, int(base_h * 0.11))
        self.hint_margin = max(20, int(base_h * 0.08))
    
    def change_state(self, new_state, data=None):
        """Change the current game state"""
        try:
            print(f"StateManager: Changing state from {self.current_state} to {new_state}")
            self.previous_state = self.current_state
            self.current_state = new_state
            self.selected_option = 0  # Reset menu selection
            
            # Setup state-specific data
            if new_state == GameState.PAUSED:
                self.setup_pause_menu()
            elif new_state == GameState.DEATH:
                self.setup_death_menu(data)
            elif new_state == GameState.PLAYING:
                # Clear any menu-related states when returning to game
                pass
        except Exception as e:
            print(f"StateManager Error in change_state: {e}")
            # Fallback to playing state if something goes wrong
            self.current_state = GameState.PLAYING
    
    def setup_pause_menu(self):
        """Setup the pause menu options"""
        self.menu_options = [
            "Resume",
            "Options",
            "Restart Level",
            "Main Menu",
            "Selfdestruct",
            "Quit Game"
        ]
        self.selected_option = 0
    
    def setup_death_menu(self, death_data=None):
        """Setup the death menu options"""
        if death_data:
            self.death_reason = death_data.get("reason", "You died!")
            self.respawn_position = death_data.get("respawn_pos", (32, 32))
        else:
            self.death_reason = "You died!"
            self.respawn_position = (32, 32)
            
        self.menu_options = [
            "Respawn",
            "Restart Level",
            "Main Menu",
            "Quit Game"
        ]
        self.selected_option = 0
        self.death_timer = 0.0
    
    def handle_key_input(self, key, dt):
        """Handle key input with cooldown to prevent spam"""
        if key not in self.key_timers:
            self.key_timers[key] = 0.0
            
        if self.key_timers[key] <= 0:
            self.key_timers[key] = self.key_cooldown
            return True
        return False
    
    def update_key_timers(self, dt):
        """Update key press timers"""
        for key in list(self.key_timers.keys()):  # Create a copy of keys to avoid runtime error
            if self.key_timers[key] > 0:
                self.key_timers[key] -= dt
    
    def handle_pause_input(self, keys, dt):
        """Handle input while paused. Does not render anything.

        Returns a dict action (e.g. {'action':'resume'}) when a menu choice
        triggers an external action, otherwise returns None.
        """

        # Update timers first
        self.update_key_timers(dt)

        try:
            # If we're inside the Options submenu, route input there
            if self.in_options:
                # Up/Down navigates between SFX/BGM/Back
                if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.handle_key_input(pygame.K_UP, dt):
                    self.options_selected = (self.options_selected - 1) % 3
                if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.handle_key_input(pygame.K_DOWN, dt):
                    self.options_selected = (self.options_selected + 1) % 3

                # Left/Right adjust the current slider
                self.handle_options_input(keys, dt)

                # Enter/Space: Back when on Back
                if (keys[pygame.K_RETURN] or keys[pygame.K_SPACE]) and self.handle_key_input(pygame.K_RETURN, dt):
                    if self.options_selected == 2:
                        self.in_options = False
                    return None

                return None

            # Otherwise we're in the main pause menu
            if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.handle_key_input(pygame.K_UP, dt):
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.handle_key_input(pygame.K_DOWN, dt):
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)

            # Select option
            if (keys[pygame.K_RETURN] or keys[pygame.K_SPACE]) and self.handle_key_input(pygame.K_RETURN, dt):
                return self.execute_pause_menu_option()

        except (IndexError, KeyError):
            # Defensive: some key states might not be available
            pass

        return None

    def handle_options_input(self, keys, dt):
        """Handle input specific to the Options submenu (SFX/BGM sliders)"""
        # left/right change slider values, up/down handled in handle_pause_input
        try:
            if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.handle_key_input(pygame.K_LEFT, dt):
                if self.options_selected == 0:
                    self.sfx_volume = max(0, self.sfx_volume - 5)
                elif self.options_selected == 1:
                    self.bgm_volume = max(0, self.bgm_volume - 5)
            if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.handle_key_input(pygame.K_RIGHT, dt):
                if self.options_selected == 0:
                    self.sfx_volume = min(100, self.sfx_volume + 5)
                elif self.options_selected == 1:
                    self.bgm_volume = min(100, self.bgm_volume + 5)
        except (IndexError, KeyError):
            pass
        # Apply bgm volume to mixer if available
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.set_volume(self.bgm_volume / 100.0)
        except Exception:
            pass
    
    def execute_pause_menu_option(self):
        """Execute the selected pause menu option"""
        option = self.menu_options[self.selected_option]
        
        if option == "Resume":
            self.change_state(GameState.PLAYING)
            return {"action": "resume"}
        elif option == "Restart Level":
            self.change_state(GameState.PLAYING)
            return {"action": "restart_level"}
        elif option == "Options":
            # Enter options submenu
            self.in_options = True
            self.options_selected = 0
            return None
        elif option == "Main Menu":
            return {"action": "main_menu"}
        elif option == "Selfdestruct":
            self.change_state(GameState.DEATH, {"reason": "Selfdestruct triggered!", "respawn_pos": (32, 32)})
            return None
        elif option == "Quit Game":
            return {"action": "quit"}
            
        return None
    
    def execute_death_menu_option(self):
        """Execute the selected death menu option"""
        option = self.menu_options[self.selected_option]
        
        if option == "Respawn":
            self.change_state(GameState.PLAYING)
            return {
                "action": "respawn",
                "position": self.respawn_position
            }
        elif option == "Restart Level":
            self.change_state(GameState.PLAYING)
            return {"action": "restart_level"}
        elif option == "Main Menu":
            return {"action": "main_menu"}
        elif option == "Quit Game":
            return {"action": "quit"}
            
        return None
    
    def update(self, dt):
        """Update the state manager"""
        if self.current_state == GameState.DEATH:
            self.death_timer += dt

    def check_for_pause(self, keys, dt):
        """Check if pause key was pressed during gameplay and toggle pause.

        Returns True if state was changed to PAUSED, otherwise False.
        """
        if self.current_state != GameState.PLAYING:
            return False

        try:
            if keys[pygame.K_p] and self.handle_key_input(pygame.K_p, dt):
                self.change_state(GameState.PAUSED)
                return True
        except (IndexError, KeyError):
            pass

        return False
    
    def render_pause_menu(self, screen):
        """Render the pause menu (title at top, menu/items below)."""

        # Create semi-transparent overlay
        overlay = pygame.Surface((self.window.base_width, self.window.base_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(self.pause_overlay_alpha)
        screen.blit(overlay, (0, 0))

        # Large title at the top (leave plenty of room below)
        title_text = self.menu_font_large.render("PAUSED", True, (255, 220, 80))
        title_rect = title_text.get_rect(center=(self.window.base_width // 2, int(self.window.base_height * 0.14)))
        screen.blit(title_text, title_rect)

        # If in options submenu, render options well below the title
        if self.in_options:
            opt_start_y = int(self.window.base_height * 0.60)

            sfx_label = self.menu_font_medium.render(f"SFX: {self.sfx_volume}", True, (255, 255, 0) if self.options_selected == 0 else (220,220,220))
            sfx_rect = sfx_label.get_rect(center=(self.window.base_width // 2, opt_start_y))
            screen.blit(sfx_label, sfx_rect)
            self._render_slider(screen, self.window.base_width // 2, opt_start_y + int(self.menu_spacing * 0.35), self.sfx_volume)

            bgm_label = self.menu_font_medium.render(f"BGM: {self.bgm_volume}", True, (255, 255, 0) if self.options_selected == 1 else (220,220,220))
            bgm_rect = bgm_label.get_rect(center=(self.window.base_width // 2, opt_start_y + int(self.menu_spacing * 1.0)))
            screen.blit(bgm_label, bgm_rect)
            self._render_slider(screen, self.window.base_width // 2, opt_start_y + int(self.menu_spacing * 1.35), self.bgm_volume)

            back_label = self.menu_font_medium.render("Back", True, (255,255,0) if self.options_selected == 2 else (220,220,220))
            back_rect = back_label.get_rect(center=(self.window.base_width // 2, opt_start_y + int(self.menu_spacing * 2.0)))
            screen.blit(back_label, back_rect)

            hint_text = self.hint_font.render("Left/Right to adjust • Enter to Back", True, (180, 180, 180))
            hint_rect = hint_text.get_rect(center=(self.window.base_width // 2, self.window.base_height - self.hint_margin))
            screen.blit(hint_text, hint_rect)
            return

        # Main pause menu (render well below the title)
        start_y = int(self.window.base_height * 0.60) - (len(self.menu_options) * self.menu_spacing) // 2
        for i, option in enumerate(self.menu_options):
            color = (255, 255, 0) if i == self.selected_option else (220,220,220)
            option_text = self.menu_font_medium.render(option, True, color)
            option_rect = option_text.get_rect(center=(self.window.base_width // 2, start_y + i * self.menu_spacing))
            screen.blit(option_text, option_rect)
            if i == self.selected_option:
                pygame.draw.line(
                    screen,
                    (255,255,0),
                    (option_rect.left, option_rect.bottom + int(self.menu_spacing*0.12)),
                    (option_rect.right, option_rect.bottom + int(self.menu_spacing*0.12)),
                    max(2, int(self.menu_spacing*0.06))
                )

        hint_text = self.hint_font.render("P to resume • Up/Down to navigate • Enter to select", True, (180, 180, 180))
        hint_rect = hint_text.get_rect(center=(self.window.base_width // 2, self.window.base_height - self.hint_margin))
        screen.blit(hint_text, hint_rect)
    
    def render_death_menu(self, screen):
        """Render the death menu"""
        # Create dark overlay
        overlay = pygame.Surface((self.window.base_width, self.window.base_height))
        overlay.fill((50, 0, 0))  # Dark red tint
        overlay.set_alpha(200)
        screen.blit(overlay, (0, 0))

        # During the short death delay show the reason in the centre
        if self.death_timer < self.death_delay:
            death_text = self.menu_font_large.render(self.death_reason, True, (255, 100, 100))
            death_rect = death_text.get_rect(center=(self.window.base_width // 2, self.window.base_height // 2))
            screen.blit(death_text, death_rect)
            return

        # Render death title (higher up so menu can be lower)
        title_text = self.menu_font_large.render("YOU DIED", True, (255, 100, 100))
        title_rect = title_text.get_rect(center=(self.window.base_width // 2, int(self.window.base_height * 0.16)))
        screen.blit(title_text, title_rect)

        # Render death reason slightly below the title
        if self.death_reason:
            reason_text = self.hint_font.render(self.death_reason, True, (255, 200, 200))
            reason_rect = reason_text.get_rect(center=(self.window.base_width // 2, int(self.window.base_height * 0.22)))
            screen.blit(reason_text, reason_rect)

        # Render menu options further down
        start_y = int(self.window.base_height * 0.70) - (len(self.menu_options) * int(self.menu_spacing * 0.9)) // 2
        for i, option in enumerate(self.menu_options):
            color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
            option_text = self.menu_font_medium.render(option, True, color)
            option_rect = option_text.get_rect(center=(self.window.base_width // 2, start_y + i * int(self.menu_spacing * 0.95)))
            screen.blit(option_text, option_rect)

            # Render selection indicator
            if i == self.selected_option:
                indicator = self.menu_font_medium.render(">", True, (255, 255, 0))
                indicator_rect = indicator.get_rect(center=(option_rect.left - 30, option_rect.centery))
                screen.blit(indicator, indicator_rect)

        # Render controls hint
        hint_text = self.hint_font.render("Use Arrow Keys/WASD to navigate, Enter/Space to select", True, (200, 200, 200))
        hint_rect = hint_text.get_rect(center=(self.window.base_width // 2, self.window.base_height - 50))
        screen.blit(hint_text, hint_rect)
    
    def render(self, screen):
        """Render current state overlays"""
        if self.current_state == GameState.PAUSED:
            self.render_pause_menu(screen)
        elif self.current_state == GameState.DEATH:
            self.render_death_menu(screen)

    def handle_death_input(self, keys, dt):
        """Handle input while on the death menu.

        Returns a dict action (e.g. {'action':'respawn'}) when a menu choice
        triggers an external action, otherwise returns None.
        """
        # update key timers
        self.update_key_timers(dt)

        try:
            if (keys[pygame.K_UP] or keys[pygame.K_w]) and self.handle_key_input(pygame.K_UP, dt):
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            if (keys[pygame.K_DOWN] or keys[pygame.K_s]) and self.handle_key_input(pygame.K_DOWN, dt):
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)

            if (keys[pygame.K_RETURN] or keys[pygame.K_SPACE]) and self.handle_key_input(pygame.K_RETURN, dt):
                return self.execute_death_menu_option()
        except (IndexError, KeyError):
            pass

        return None

    def _render_slider(self, screen, x, y, value):
        """Render a simple horizontal slider centered at (x,y) with value 0-100"""
        width = getattr(self, 'slider_width', 200)
        height = max(6, int(self.menu_spacing * 0.15))
        left = x - width // 2
        # Background bar
        pygame.draw.rect(screen, (70,70,70), (left, y, width, height))
        # Filled portion
        filled_w = int((value / 100.0) * width)
        pygame.draw.rect(screen, (200,200,80), (left, y, filled_w, height))
        # Border
        pygame.draw.rect(screen, (200,200,200), (left, y, width, height), 1)
    
    def is_game_paused(self):
        """Check if the game is currently paused"""
        return self.current_state == GameState.PAUSED
    
    def is_player_dead(self):
        """Check if the player is currently dead"""
        return self.current_state == GameState.DEATH
    
    def is_playing(self):
        """Check if the game is in playing state"""
        return self.current_state == GameState.PLAYING
    
    def get_current_state(self):
        """Get the current game state"""
        return self.current_state
