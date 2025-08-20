from Engine.window_manager import WindowManager

def main():
    window = WindowManager()
    
    while window.running:
        window.handle_events()
        window.clear_screen()
        window.update_display()
    
    window.quit()

main()