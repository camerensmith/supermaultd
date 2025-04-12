import pygame
import os
from config import WIDTH, HEIGHT, FPS, WINDOWED_FULLSCREEN
from scenes.menu import MenuScene
from scenes.game_scene import GameScene
from ui.race_selector import RaceSelector
import pygame_gui

# Define colors if not in config
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

class Game:
    def __init__(self, game_data):
        """
        Initialize the game with consolidated game data.
        
        :param game_data: Dictionary containing all game definitions (races, towers, types, etc.)
        """
        pygame.init()
        pygame.mixer.init() # Initialize the mixer
        pygame.display.set_caption("SuperMauL TD")
        
        # Determine screen dimensions
        if WINDOWED_FULLSCREEN:
            info = pygame.display.Info()
            self.screen_width = info.current_w # Store actual width
            self.screen_height = info.current_h # Store actual height
            flags = pygame.NOFRAME
        else:
            self.screen_width = WIDTH # Use config width
            self.screen_height = HEIGHT # Use config height
            flags = 0
        
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), flags)
        print(f"[Game Init] Screen Initialized: {self.screen_width}x{self.screen_height}")
        
        self.clock = pygame.time.Clock()
        
        # Store game data
        self.game_data = game_data
        
        # Initialize UI manager with correct size and theme
        self.ui_manager = pygame_gui.UIManager((self.screen_width, self.screen_height), 'theme.json') # Use actual dimensions
        
        # --- Game State and Scene Management ---
        # self.scene = None # We manage state directly first
        self.game_state = "race_selection" # Start with race selection
        self.active_game_scene = None # To hold the GameScene instance when playing
        # --------------------------------------
        
        # Extract specific data sections for easier access (optional but recommended)
        self.ranges = game_data.get("ranges", {})
        self.damage_types = game_data.get("damagetypes", {})
        self.tower_sizes = game_data.get("tower_sizes", {})
        self.races = game_data.get("races", {})
        
        # Game state
        self.running = True
        self.selected_race = None
        
        # Colors
        self.BACKGROUND_COLOR = (30, 30, 30)
        
        # Load assets
        self.load_assets() # General assets
        
        # --- Load UI Click Sound --- 
        self.click_sound = None
        try:
            click_sound_path = os.path.join("assets", "sounds", "click.mp3") 
            if os.path.exists(click_sound_path):
                self.click_sound = pygame.mixer.Sound(click_sound_path)
                print(f"[Game Init] Loaded click sound: {click_sound_path}")
            else:
                print(f"[Game Init] Warning: Click sound file not found: {click_sound_path}")
        except pygame.error as e:
            print(f"[Game Init] Error loading click sound: {e}")
        # --- End Sound Loading --- 
        
        # --- Load Placement Sound --- 
        self.placement_sound = None
        try:
            placement_sound_path = os.path.join("assets", "sounds", "building.mp3")
            if os.path.exists(placement_sound_path):
                self.placement_sound = pygame.mixer.Sound(placement_sound_path)
                print(f"[Game Init] Loaded placement sound: {placement_sound_path}")
            else:
                print(f"[Game Init] Warning: Placement sound file not found: {placement_sound_path}")
        except pygame.error as e:
            print(f"[Game Init] Error loading placement sound: {e}")
        # --- End Placement Sound Loading --- 
        
        # --- Load and Play Menu Music --- 
        try:
            music_path = os.path.join("assets", "sounds", "Theme.mp3") 
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1) # Play indefinitely (-1)
                print(f"[Game Init] Loaded and playing race selection music: {music_path}")
            else:
                print(f"[Game Init] Warning: Race selection music file not found: {music_path}")
        except pygame.error as e:
            print(f"[Game Init] Error loading or playing music: {e}")
        # --- End Music Loading --- 
        
        # --- Load Title Image --- 
        self.title_image = None
        self.placeholder_surface = None
        try:
            image_path = os.path.join("assets", "images", "supermaultd.png")
            absolute_image_path = os.path.abspath(image_path)
            print(f"[Game Init] Checking for title image at: {absolute_image_path}")
            if os.path.exists(absolute_image_path):
                print(f"[Game Init] Title image FOUND. Loading...")
                temp_image = pygame.image.load(absolute_image_path).convert_alpha()
                print(f"[Game Init] Title image loaded. Original size: {temp_image.get_size()}")
                target_width = int(self.screen_width * 0.6)
                if temp_image.get_height() > 0:
                    image_ratio = temp_image.get_width() / temp_image.get_height()
                    target_height = int(target_width / image_ratio) if image_ratio > 0 else 0
                    if target_height > 0:
                        self.title_image = pygame.transform.scale(temp_image, (target_width, target_height))
                        print(f"[Game Init] Scaled title image to: {self.title_image.get_size()}")
                    else: self.title_image = None
                else: self.title_image = None
            else:
                print(f"[Game Init] Title image NOT FOUND at {absolute_image_path}")
                self.title_image = None
        except Exception as e:
            print(f"[Game Init] Error loading/scaling title image: {e}")
            self.title_image = None
            
        if self.title_image is None:
            print("[Game Init] Creating placeholder for title image.")
            placeholder_width = int(self.screen_width * 0.6)
            placeholder_height = int(placeholder_width * 0.2)
            self.placeholder_surface = pygame.Surface((placeholder_width, placeholder_height))
            self.placeholder_surface.fill(BLUE)
            try: # Ensure font is loaded before rendering
                font = pygame.font.Font(None, 36)
                placeholder_text = font.render("TITLE IMG MISSING", True, WHITE)
                text_rect = placeholder_text.get_rect(center=self.placeholder_surface.get_rect().center)
                self.placeholder_surface.blit(placeholder_text, text_rect)
            except Exception as font_e:
                 print(f"[Game Init] Error rendering placeholder text: {font_e}")
        # --- End Load Title Image --- 
        
        # --- Load Custom Cursor --- 
        self.custom_cursor_image = None
        try:
            cursor_path = os.path.join("assets", "images", "cursor.png")
            absolute_cursor_path = os.path.abspath(cursor_path)
            print(f"[Game Init] Checking for cursor image at: {absolute_cursor_path}")
            if os.path.exists(absolute_cursor_path):
                 self.custom_cursor_image = pygame.image.load(absolute_cursor_path).convert_alpha()
                 print(f"[Game Init] Custom cursor loaded. Size: {self.custom_cursor_image.get_size()}")
                 pygame.mouse.set_visible(False) # Hide default cursor
                 print("[Game Init] System cursor hidden.")
            else:
                print(f"[Game Init] Custom cursor image NOT FOUND at {absolute_cursor_path}. Using system cursor.")
                pygame.mouse.set_visible(True) # Ensure system cursor is visible if custom fails
        except Exception as e:
            print(f"[Game Init] Error loading custom cursor: {e}. Using system cursor.")
            pygame.mouse.set_visible(True)
        # --- End Custom Cursor --- 
        
        # Initialize race selector AFTER loading title image
        self.race_selector = RaceSelector(self.game_data, self.ui_manager, 
                                          self.screen_width, self.screen_height,
                                          self.click_sound) # Pass sound
        
        print("Game initialized")
        if WINDOWED_FULLSCREEN:
            print(f"Running in windowed fullscreen mode ({self.screen_width}x{self.screen_height})")
        else:
            print(f"Running in windowed mode ({self.screen_width}x{self.screen_height})")

    def get_range_value(self, range_type):
        """
        Get the min and max range values for a given range type.
        
        :param range_type: The type of range (melee, short, medium, long)
        :return: Tuple of (min_range, max_range)
        """
        # Use the ranges data stored in self
        range_data = self.ranges.get(range_type.lower())
        if range_data:
            return range_data["min"], range_data["max"]
        return None, None # Or maybe raise an error for unknown range type?

    # Add similar helper methods for other data if needed:
    def get_damage_type_info(self, damage_type):
        return self.damage_types.get(damage_type.lower())
        
    def get_tower_size_info(self, size_type):
        return self.tower_sizes.get(size_type.lower())
        
    def get_race_info(self, race_name):
        """
        Get information about a specific race.
        
        :param race_name: Name of the race to get info for
        :return: Dictionary containing race information
        """
        # Ensure we are using the most up-to-date game_data 
        # (Assuming self.game_data might be updated elsewhere, otherwise this won't fix stale file loads)
        current_races = self.game_data.get("races", {})

        # Handle case where race_name is a tuple (from UI selection)
        if isinstance(race_name, tuple):
            race_name = race_name[0]
            
        # Convert to lowercase for case-insensitive lookup
        race_name = race_name.lower()
        # return self.races.get(race_name) # Old way - using potentially stale self.races
        return current_races.get(race_name) # New way - using freshly extracted data
        
    def get_tower_definition(self, race_name, tower_id):
        race_info = self.get_race_info(race_name)
        if race_info:
            return race_info.get("towers", {}).get(tower_id.lower())
        return None

    def load_assets(self):
        """Load game assets (images, sounds, etc.)"""
        # Create assets directory if it doesn't exist
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        sounds_dir = os.path.join(assets_dir, 'sounds') # Ensure sounds dir exists
        os.makedirs(sounds_dir, exist_ok=True) 
        images_dir = os.path.join(assets_dir, 'images') # Ensure images dir exists
        os.makedirs(images_dir, exist_ok=True) 
        
        # TODO: Load game assets based on races/towers in game_data
        # Example:
        # for race_id, race_data in self.races.items():
        #     for tower_id, tower_data in race_data.get("towers", {}).items():
        #         # Load image based on tower_id, e.g., crystal_castle_shard_launcher.png
        #         pass 

    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False # Set running to False to exit loop
                return # Exit event handling for this frame
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False # Allow ESC to quit
                    return # Exit event handling
                    
            # Pass events to UI Manager FIRST - essential for pygame_gui
            # The manager will dispatch events to the RaceSelector and other UI elements
            self.ui_manager.process_events(event)
            
            # Then handle game state specific logic based on events
            if self.game_state == "race_selection":
                # Allow RaceSelector to handle its internal button clicks (selection, preview update)
                if hasattr(self.race_selector, 'handle_event'): # Check if method exists
                    self.race_selector.handle_event(event) 
                
                # Check if the CONFIRM button in RaceSelector was pressed (for state transition)
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    # Ensure race_selector and its confirm_button exist before checking
                    if hasattr(self.race_selector, 'confirm_button') and event.ui_element == self.race_selector.confirm_button:
                        selected_race = self.race_selector.get_selected_race()
                        if selected_race:
                            # Play click sound if confirm is successful
                            if self.click_sound: self.click_sound.play()
                                
                            print(f"[Game Event] Race confirmed: {selected_race}")
                            pygame.mixer.music.stop() # Stop menu music
                            print("[Game Event] Stopped race selection music.")
                            
                            self.race_selector.kill() # Remove race selector UI
                            print("[Game Event] Race selector UI killed.")
                            
                            try:
                                # Create the actual GameScene instance
                                self.active_game_scene = GameScene(self, selected_race, 
                                                       self.screen_width, self.screen_height, 
                                                       self.click_sound, 
                                                       self.placement_sound)
                                self.game_state = "playing"
                                print("[Game Event] Game scene initialized successfully")
                            except Exception as e:
                                print(f"[Game Event] Error initializing game scene: {e}")
                                # Revert state? Show error message?
                                self.game_state = "error" # Example: go to an error state
                                self.active_game_scene = None 
                        else:
                            # Optional: Add feedback if confirm is pressed with no race selected
                            print("[Game Event] Confirm button pressed, but no race selected.")
                            # Maybe play an error sound?
                                
            elif self.game_state == "playing" and self.active_game_scene:
                # Handle game scene events
                self.active_game_scene.handle_event(event)
                
            # No need to process manager events again here
                
        # Return True to continue the main loop unless explicitly stopped
        # return True # Not needed, loop continues based on self.running

    def update(self):
        """Update game state"""
        self.time_delta = self.clock.tick(FPS) / 1000.0
        self.current_game_time = pygame.time.get_ticks() / 1000.0
        
        # Update UI manager first - crucial for button states, etc.
        self.ui_manager.update(self.time_delta)
        
        if self.game_state == "race_selection":
            # RaceSelector UI is updated by the manager
            pass 
        elif self.game_state == "playing" and self.active_game_scene:
            # Update the active game scene
            self.active_game_scene.update(self.time_delta)
        elif self.game_state == "error":
            # Handle error state update (e.g., display error message)
            pass

    def draw(self):
        """Draw the game state to the screen"""
        self.screen.fill(self.BACKGROUND_COLOR)
        
        # Draw based on game state
        if self.game_state == "race_selection":
            # --- Draw Title Image or Placeholder FIRST --- 
            image_to_draw = self.title_image if self.title_image else self.placeholder_surface
            if image_to_draw:
                # Position near top, centered horizontally
                title_rect = image_to_draw.get_rect(centerx=self.screen_width // 2)
                title_rect.top = 20 # 20 pixels padding from the top
                
                self.screen.blit(image_to_draw, title_rect)
                # pygame.draw.rect(self.screen, RED, title_rect, 1) # Debug border removed
            else:
                 print("[Draw] No title image or placeholder available.") # Should not happen if placeholder logic works
            # --- End Title Image Draw --- 
            
            # UI Manager draws the RaceSelector UI elements
            self.ui_manager.draw_ui(self.screen)
            
        elif self.game_state == "playing" and self.active_game_scene:
            # Draw the active game scene
            self.active_game_scene.draw(self.screen, self.time_delta, self.current_game_time)
            # UI Manager still needs to be drawn for in-game UI (if any)
            self.ui_manager.draw_ui(self.screen) 
            
        elif self.game_state == "error":
             # Example: Draw an error message
             try:
                 font = pygame.font.Font(None, 48)
                 error_text = font.render("Error Initializing Game Scene!", True, RED)
                 text_rect = error_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                 self.screen.blit(error_text, text_rect)
             except Exception as font_e:
                 print(f"[Draw] Error rendering error text: {font_e}")
             # Draw UI manager even in error state if needed
             self.ui_manager.draw_ui(self.screen)
             
        else: # Fallback if state is unknown or GameScene not ready
             # Draw UI manager which might contain some default state or message
             self.ui_manager.draw_ui(self.screen)

        # --- Draw Custom Cursor (if loaded) LAST --- 
        if self.custom_cursor_image:
            cursor_pos = pygame.mouse.get_pos()
            # Draw the cursor image with its top-left corner at the mouse position
            self.screen.blit(self.custom_cursor_image, cursor_pos)
        # --- End Custom Cursor --- 

        # Flip the display AFTER all drawing is done
        pygame.display.flip()

    def run(self):
        """Main game loop"""
        print("Starting game loop")
        self.running = True
        while self.running:
            self.handle_events() # Will set self.running to False if quit
            # Only update and draw if still running after handling events
            if self.running:
                self.update()
                self.draw()

        print("Exiting game loop")
        pygame.quit()
