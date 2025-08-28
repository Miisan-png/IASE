from Engine.window_manager import WindowManager
from Engine.scene_loader import SceneLoader
from Game.player import Player
from Game.camera import Camera

def main():
    window = WindowManager()
    scene = SceneLoader()
    camera = Camera(window.width, window.height)
    
    scene.load_scene("Game/level1.json")
    
    player = Player(100, 100, scene)
    camera.set_target(player)
    
    dt = 0
    
    while window.running:
        dt = window.clock.tick(60) / 1000.0
        
        window.handle_events()
        
        player.update(dt)
        camera.update(dt)
        
        window.clear_screen()
        
        scene.render(window.screen, camera.x, camera.y)
        player.render(window.screen, camera.x, camera.y)
        
        window.update_display()
    
    window.quit()

main()