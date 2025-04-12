import pygame
import os
from config import WIDTH, HEIGHT, FPS, WINDOWED_FULLSCREEN
from scenes.menu import MenuScene
from scenes.game_scene import GameScene
from ui.race_selector import RaceSelector
import pygame_gui

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
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND) # Set the system cursor to a hand
        
        self.clock = pygame.time.Clock()
        
        # Store game data
        self.game_data = game_data
        
        # Initialize UI manager with correct size and theme
        self.ui_manager = pygame_gui.UIManager((self.screen_width, self.screen_height), 'theme.json') # Use actual dimensions
        
        # Initialize scenes
        self.scene = None
        self.game_state = "race_selection"
        
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
        self.load_assets()
        
        # --- Load UI Click Sound --- 
        self.click_sound = None
        try:
            # Use the correct path provided by the user
            click_sound_path = "assets/sounds/click.mp3" 
            if os.path.exists(click_sound_path):
                self.click_sound = pygame.mixer.Sound(click_sound_path)
                print(f"Loaded click sound: {click_sound_path}")
            else:
                print(f"Warning: Click sound file not found: {click_sound_path}")
        except pygame.error as e:
            print(f"Error loading click sound: {e}")
        # --- End Sound Loading --- 
        
        # --- Load Placement Sound --- 
        self.placement_sound = None
        try:
            placement_sound_path = "assets/sounds/building.mp3"
            if os.path.exists(placement_sound_path):
                self.placement_sound = pygame.mixer.Sound(placement_sound_path)
                print(f"Loaded placement sound: {placement_sound_path}")
            else:
                print(f"Warning: Placement sound file not found: {placement_sound_path}")
        except pygame.error as e:
            print(f"Error loading placement sound: {e}")
        # --- End Placement Sound Loading --- 
        
        # --- Load and Play Menu Music --- 
        try:
            # !!! IMPORTANT: Replace with the actual path to your music file !!!
            music_path = "assets/sounds/Theme.mp3" 
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1) # Play indefinitely (-1)
                print(f"Loaded and playing race selection music: {music_path}")
            else:
                print(f"Warning: Race selection music file not found: {music_path}")
        except pygame.error as e:
            print(f"Error loading or playing music: {e}")
        # --- End Music Loading --- 
        
        # Initialize race selector, passing screen dimensions and click sound
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
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                    
            if self.game_state == "race_selection":
                # Handle race selection events
                if self.race_selector.handle_event(event):
                    selected_race = self.race_selector.get_selected_race()
                    if selected_race:
                        print(f"Race selected: {selected_race}")
                        pygame.mixer.music.stop() # Stop menu music
                        print("Stopped race selection music.")
                        
                        # Kill the race selector UI before creating the game scene
                        self.race_selector.kill()
                        
                        try:
                            # Pass actual screen dimensions and sounds to GameScene
                            self.scene = GameScene(self, selected_race, 
                                                   self.screen_width, self.screen_height, 
                                                   self.click_sound, # Pass click sound
                                                   self.placement_sound) # Pass placement sound
                            self.game_state = "playing"
                            print("Game scene initialized successfully")
                        except Exception as e:
                            print(f"Error initializing game scene: {e}")
                            self.game_state = "race_selection"
                            self.scene = None
                            # If scene fails, need to re-create race selector?
                            # For now, just stays in a broken state.
            elif self.game_state == "playing" and self.scene:
                # Handle game scene events
                self.scene.handle_event(event)
                
            # Pass events to UI Manager regardless of game state
            self.ui_manager.process_events(event)
                
        return True

    def update(self):
        """Update game state"""
        # Store time_delta and current_time for use in draw method
        self.time_delta = self.clock.tick(FPS) / 1000.0
        self.current_game_time = pygame.time.get_ticks() / 1000.0
        
        # Update UI manager first
        self.ui_manager.update(self.time_delta)
        
        if self.game_state == "race_selection":
            # Race selector itself doesn't need per-frame update beyond the manager
            # self.race_selector.update(time_delta) # Usually not needed if just UI elements
            pass 
        elif self.game_state == "playing" and self.scene:
            # Pass time_delta to the scene's update method
            self.scene.update(self.time_delta)

    def draw(self):
        """Draw the game state to the screen"""
        # Clear the screen
        self.screen.fill(self.BACKGROUND_COLOR)
        
        # Draw game scene if it exists, passing required time variables
        if self.game_state == "playing" and self.scene:
            # Pass screen, time_delta, and current_game_time to scene's draw
            self.scene.draw(self.screen, self.time_delta, self.current_game_time)
        
        # Draw UI Manager - handles drawing RaceSelector panel/buttons when active
        self.ui_manager.draw_ui(self.screen)
        
        # Remove explicit RaceSelector draw call if manager handles it
        # if self.game_state == "race_selection":
        #     self.race_selector.draw(self.screen)
        
        # Update the display
        pygame.display.flip()

    def run(self):
        """Main game loop"""
        print("Starting game loop")
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            
        # Stop music explicitly before quitting (optional, quit usually handles it)
        # pygame.mixer.music.stop()
        pygame.quit()
