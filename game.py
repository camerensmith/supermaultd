import pygame
import os
from config import WIDTH, HEIGHT, FPS, WINDOWED_FULLSCREEN, FORCE_RESOLUTION, FIXED_WIDTH, FIXED_HEIGHT
from scenes.game_scene import GameScene
from ui.race_selector import RaceSelector
from entities.effects.background_effects import BackgroundManager
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
        if FORCE_RESOLUTION:
            # Use the auto-detected screen size as the fixed resolution
            self.screen_width = FIXED_WIDTH  # Auto-detected screen width
            self.screen_height = FIXED_HEIGHT  # Auto-detected screen height
            
            # Create fullscreen window at the detected resolution
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.NOFRAME)
            self.game_surface = None  # Draw directly to screen (no borders needed)
            self.offset_x = 0
            self.offset_y = 0
            
            print(f"[Game Init] Fixed Resolution Mode - Auto-Detected:")
            print(f"  Screen: {self.screen_width}x{self.screen_height}")
            print(f"  No borders needed - perfect fit!")
            
        elif WINDOWED_FULLSCREEN:
            info = pygame.display.Info()
            self.screen_width = info.current_w # Store actual width
            self.screen_height = info.current_h # Store actual height
            flags = pygame.NOFRAME
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), flags)
            self.game_surface = None  # No separate game surface needed
            print(f"[Game Init] Windowed Fullscreen: {self.screen_width}x{self.screen_height}")
        else:
            self.screen_width = WIDTH # Use config width
            self.screen_height = HEIGHT # Use config height
            flags = 0
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), flags)
            self.game_surface = None  # No separate game surface needed
            print(f"[Game Init] Windowed: {self.screen_width}x{self.screen_height}")
        
        self.clock = pygame.time.Clock()
        
        # Store game data
        self.game_data = game_data
        
        # Set up wave file path
        self.wave_file_path = os.path.join("data", "waves.json")
        
        # Initialize UI manager with correct size and theme
        self.ui_manager = pygame_gui.UIManager((self.screen_width, self.screen_height), 'theme.json') # Use actual dimensions
        
        # --- Initialize Background Effects ---
        try:
            self.background_manager = BackgroundManager(self.screen_width, self.screen_height)
            self.background_manager.set_effect("tessellation")  # Start with tessellation effect
            print(f"[Game Init] Background effects initialized successfully")
        except Exception as e:
            print(f"[Game Init] ERROR initializing background effects: {e}")
            self.background_manager = None
        
        # --- Game State and Scene Management ---
        # self.scene = None # We manage state directly first
        self.game_state = "race_selection" # Start with race selection
        self.active_game_scene = None # To hold the GameScene instance when playing
        # --------------------------------------
        
        # --- Add Wave Mode Selection State ---
        self.selected_wave_mode = "classic" # 'classic' or 'advanced' or 'wild'
        self.wave_mode_buttons = {} # To hold references to the buttons
        # --- End Wave Mode Selection State ---
        
        # --- Add Options Menu State ---
        self.options_button = None
        self.options_modal = None
        self.options_modal_visible = False
        # --- End Options Menu State ---
        
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
        
        # --- Load Cancel Sound --- 
        self.cancel_sound = None
        try:
            cancel_sound_path = os.path.join("assets", "sounds", "cancel.mp3")
            if os.path.exists(cancel_sound_path):
                self.cancel_sound = pygame.mixer.Sound(cancel_sound_path)
                print(f"[Game Init] Loaded cancel sound: {cancel_sound_path}")
            else:
                print(f"[Game Init] Warning: Cancel sound file not found: {cancel_sound_path}")
        except pygame.error as e:
            print(f"[Game Init] Error loading cancel sound: {e}")
        # --- End Cancel Sound Loading --- 
        
        # --- Load Sell Sound --- 
        self.sell_sound = None
        try:
            sell_sound_path = os.path.join("assets", "sounds", "sell.mp3")
            if os.path.exists(sell_sound_path):
                self.sell_sound = pygame.mixer.Sound(sell_sound_path)
                print(f"[Game Init] Loaded sell sound: {sell_sound_path}")
            else:
                print(f"[Game Init] Warning: Sell sound file not found: {sell_sound_path}")
        except pygame.error as e:
            print(f"[Game Init] Error loading sell sound: {e}")
        # --- End Sell Sound Loading --- 
        
        # --- Load Invalid Placement Sound --- 
        self.invalid_placement_sound = None
        try:
            invalid_sound_path = os.path.join("assets", "sounds", "invalid.mp3")
            if os.path.exists(invalid_sound_path):
                self.invalid_placement_sound = pygame.mixer.Sound(invalid_sound_path)
                print(f"[Game Init] Loaded invalid placement sound: {invalid_sound_path}")
            else:
                print(f"[Game Init] Warning: Invalid placement sound file not found: {invalid_sound_path}")
        except pygame.error as e:
            print(f"[Game Init] Error loading invalid placement sound: {e}")
        # --- End Invalid Placement Sound Loading --- 
        
        # --- Store Menu Music Paths --- 
        self.classic_music_path = None
        self.advanced_music_path = None
        self.wild_music_path = None
        try:
            classic_path = os.path.join("assets", "sounds", "Theme.mp3")
            advanced_path = os.path.join("assets", "sounds", "Theme_advanced.mp3")
            wild_path = os.path.join("assets", "sounds", "theme_wild.mp3")
            
            if os.path.exists(classic_path):
                self.classic_music_path = classic_path
                print(f"[Game Init] Found classic music: {classic_path}")
            else:
                print(f"[Game Init] Warning: Classic music file not found: {classic_path}")
                
            if os.path.exists(advanced_path):
                self.advanced_music_path = advanced_path
                print(f"[Game Init] Found advanced music: {advanced_path}")
            else:
                print(f"[Game Init] Warning: Advanced music file not found: {advanced_path}")
                
            if os.path.exists(wild_path):
                self.wild_music_path = wild_path
                print(f"[Game Init] Found wild music: {wild_path}")
            else:
                print(f"[Game Init] Warning: Wild music file not found: {wild_path}")
        except Exception as e:
             print(f"[Game Init] Error checking music paths: {e}")
        # --- End Music Path Storing ---

        # --- Load Title Images --- 
        self.title_classic_img = None
        self.title_advanced_img = None
        self.title_wild_img = None
        self.placeholder_surface = None # Single placeholder for fallback

        # Function to load and scale a title image
        def load_and_scale_title(filename):
            try:
                image_path = os.path.join("assets", "images", filename)
                absolute_image_path = os.path.abspath(image_path)
                print(f"[Game Init] Checking for title image at: {absolute_image_path}")
                if os.path.exists(absolute_image_path):
                    print(f"[Game Init] Title image FOUND. Loading {filename}...")
                    temp_image = pygame.image.load(absolute_image_path).convert_alpha()
                    target_width = int(self.screen_width * 0.6)
                    if temp_image.get_height() > 0:
                        image_ratio = temp_image.get_width() / temp_image.get_height()
                        target_height = int(target_width / image_ratio) if image_ratio > 0 else 0
                        if target_height > 0:
                            scaled_img = pygame.transform.scale(temp_image, (target_width, target_height))
                            print(f"[Game Init] Scaled {filename} to: {scaled_img.get_size()}")
                            return scaled_img
                else:
                    print(f"[Game Init] Title image NOT FOUND: {filename}")
            except Exception as e:
                print(f"[Game Init] Error loading/scaling {filename}: {e}")
            return None

        # Load classic, advanced, and wild images
        self.title_classic_img = load_and_scale_title("supermaultd.png")
        self.title_advanced_img = load_and_scale_title("supermaultd_advanced.png")
        self.title_wild_img = load_and_scale_title("supermaul_wild.png")

        # Create placeholder if either image failed (or if both failed)
        if not self.title_classic_img or not self.title_advanced_img or not self.title_wild_img:
            print("[Game Init] Creating placeholder for title image.")
            placeholder_width = int(self.screen_width * 0.6)
            placeholder_height = int(placeholder_width * 0.2)
            self.placeholder_surface = pygame.Surface((placeholder_width, placeholder_height))
            self.placeholder_surface.fill(BLUE)
            try:
                font = pygame.font.Font(None, 36)
                placeholder_text = font.render("TITLE IMG MISSING", True, WHITE)
                text_rect = placeholder_text.get_rect(center=self.placeholder_surface.get_rect().center)
                self.placeholder_surface.blit(placeholder_text, text_rect)
            except Exception as font_e:
                 print(f"[Game Init] Error rendering placeholder text: {font_e}")
        
        # Set active image initially (use placeholder if classic failed)
        self.active_title_img = self.title_classic_img if self.title_classic_img else self.placeholder_surface
        # --- End Title Image Loading --- 

        # --- Calculate Initial Title Image Position --- 
        self.title_rect = None
        if self.active_title_img:
            self.title_rect = self.active_title_img.get_rect(centerx=self.screen_width // 2)
            self.title_rect.top = 20 # Match drawing padding
        else:
             print("[Game Init] ERROR: No active title image or placeholder available!")
        # --- End Calculate Title Image Position ---
        
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
                                          self.click_sound,
                                          self.selected_wave_mode)
        
        # --- Create Options Button ---
        options_button_width = 100
        options_button_height = 40
        options_button_x = self.screen_width - options_button_width - 20  # 20px padding from right
        options_button_y = self.screen_height - options_button_height - 20  # 20px padding from bottom
        
        self.options_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(options_button_x, options_button_y, options_button_width, options_button_height),
            text='Options',
            manager=self.ui_manager,
            object_id='#options_button'
        )
        # --- End Create Options Button ---
        
        # --- Create Wave Mode Buttons (Classic/Advanced/Wild) ---
        self.wave_mode_buttons = {}
        self.selected_wave_mode = 'classic' # Default mode

        button_width = 200
        button_height = 50
        # <<< RESTORE ORIGINAL POSITIONING LOGIC >>>
        button_x_pos = 50 # Fixed X position from left
        button_y_start = self.title_rect.bottom + 20 if self.title_rect else 100 # Y position below title

        classic_rect = pygame.Rect(button_x_pos, button_y_start, button_width, button_height)
        self.wave_mode_buttons['classic'] = pygame_gui.elements.UIButton(
            relative_rect=classic_rect,
            text='Classic',
            manager=self.ui_manager,
            object_id='#classic_wave_button'
        )

        # Position Advanced below Classic
        advanced_rect = pygame.Rect(button_x_pos, button_y_start + button_height + 10, button_width, button_height)
        self.wave_mode_buttons['advanced'] = pygame_gui.elements.UIButton(
            relative_rect=advanced_rect,
            text='Advanced',
            manager=self.ui_manager,
            object_id='#advanced_wave_button'
        )

        # Position Wild below Advanced
        wild_rect = pygame.Rect(button_x_pos, button_y_start + 2 * (button_height + 10), button_width, button_height)
        self.wave_mode_buttons['wild'] = pygame_gui.elements.UIButton(
            relative_rect=wild_rect,
            text='Wild',
            manager=self.ui_manager,
            object_id='#wild_wave_button'
        )

        # Set initial selected state visually
        self.wave_mode_buttons['classic'].select()
        self.wave_mode_buttons['advanced'].unselect()
        self.wave_mode_buttons['wild'].unselect()
        print("[Game Init] Created Classic/Advanced/Wild wave mode buttons.")
        # --- End Create Wave Mode Buttons ---
        
        # --- Start Initial Menu Music --- 
        self._play_menu_music(self.classic_music_path) # Start with classic theme
        # --- End Initial Music --- 
        
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
        """Handle game events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    return
                # Handle background effect switching
                elif event.key == pygame.K_1:
                    if self.background_manager:
                        self.background_manager.set_effect("tessellation")
                        print("[Game] Switched to tessellation background")
                elif event.key == pygame.K_2:
                    if self.background_manager:
                        self.background_manager.set_effect("hexagon")
                        print("[Game] Switched to hexagon background")
                elif event.key == pygame.K_3:
                    if self.background_manager:
                        self.background_manager.set_effect("particles")
                        print("[Game] Switched to particles background")
            
            # Convert mouse position for fixed resolution mode with borders
            if FORCE_RESOLUTION and hasattr(self, 'game_surface') and self.game_surface and event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                # Convert display mouse position to game surface position
                if hasattr(event, 'pos'):
                    game_mouse_x = event.pos[0] - self.offset_x
                    game_mouse_y = event.pos[1] - self.offset_y
                    # Only process if mouse is within game area
                    if 0 <= game_mouse_x < self.screen_width and 0 <= game_mouse_y < self.screen_height:
                        # Create a new event with converted position
                        new_event = pygame.event.Event(event.type, {
                            'pos': (game_mouse_x, game_mouse_y),
                            'button': getattr(event, 'button', None),
                            'rel': getattr(event, 'rel', None)
                        })
                        processed_by_manager = self.ui_manager.process_events(new_event)
                    else:
                        processed_by_manager = False  # Mouse outside game area
                else:
                    processed_by_manager = self.ui_manager.process_events(event)
            else:
                processed_by_manager = self.ui_manager.process_events(event)
            
            # Store pending selection from listbox
            if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION and hasattr(self, 'low_effects_listbox') and event.ui_element == self.low_effects_listbox:
                self.pending_low_effects_selection = self.low_effects_listbox.get_single_selection()
            
            # Apply button applies the pending selection
            if event.type == pygame_gui.UI_BUTTON_PRESSED and hasattr(self, 'apply_options_button') and event.ui_element == self.apply_options_button:
                self.low_effects_mode = self.pending_low_effects_selection == "Low Effects Mode"
            
            # Handle options listbox
            if event.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION and hasattr(self, 'low_effects_listbox') and event.ui_element == self.low_effects_listbox:
                self.low_effects_mode = self.low_effects_listbox.get_single_selection() == "Low Effects Mode"
            
            # Radio button logic for effects mode
            if event.type == pygame_gui.UI_BUTTON_PRESSED:
                if hasattr(self, 'default_mode_button') and event.ui_element == self.default_mode_button:
                    self.pending_low_effects_selection = 'Default'
                    self.default_mode_button.select()
                    self.low_effects_mode_button.unselect()
                if hasattr(self, 'low_effects_mode_button') and event.ui_element == self.low_effects_mode_button:
                    self.pending_low_effects_selection = 'Low Effects Mode'
                    self.low_effects_mode_button.select()
                    self.default_mode_button.unselect()
                if hasattr(self, 'apply_options_button') and event.ui_element == self.apply_options_button:
                    self.low_effects_mode = self.pending_low_effects_selection == 'Low Effects Mode'
                    print(f"[Options] Apply pressed. low_effects_mode is now: {self.low_effects_mode}")
                    # Update the visual state to match the new mode
                    if self.low_effects_mode:
                        self.low_effects_mode_button.select()
                        self.default_mode_button.unselect()
                    else:
                        self.default_mode_button.select()
                        self.low_effects_mode_button.unselect()
            # Then handle game state specific logic based on events
            if self.game_state == "race_selection":
                # Allow RaceSelector to handle its internal button clicks
                if hasattr(self.race_selector, 'handle_event'):
                    self.race_selector.handle_event(event)
                
                # Check for UI Button Presses
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    # Handle Options Button
                    if event.ui_element == self.options_button:
                        self.toggle_options_modal()
                    # Handle Wave Mode Buttons
                    elif event.ui_element == self.wave_mode_buttons['classic']:
                        if self.selected_wave_mode != 'classic':
                            self.selected_wave_mode = 'classic'
                            # <<< CLEAR RACE SELECTIONS LIST >>>
                            self.race_selector.selected_races = []
                            # <<< CALL VISUAL UPDATE >>>
                            if hasattr(self.race_selector, 'update_button_visuals'):
                                self.race_selector.update_button_visuals()
                            # <<< END CLEAR >>>
                            self.wave_mode_buttons['classic'].select()
                            self.wave_mode_buttons['advanced'].unselect()
                            self.wave_mode_buttons['wild'].unselect()
                            # <<< ADD CALL TO set_selection_mode for classic >>>
                            if hasattr(self.race_selector, 'set_selection_mode'):
                                self.race_selector.set_selection_mode('classic')
                            # <<< END ADD CALL >>>
                            # Update background color scheme
                            if self.background_manager:
                                self.background_manager.set_color_scheme('classic')
                            # Update active image
                            self.active_title_img = self.title_classic_img if self.title_classic_img else self.placeholder_surface
                            if self.active_title_img:
                                self.title_rect = self.active_title_img.get_rect(centerx=self.screen_width // 2)
                                self.title_rect.top = 20
                            # Play classic music
                            self._play_menu_music(self.classic_music_path)
                            print("[Game Event] Switched to Classic wave mode.")
                            if self.click_sound: self.click_sound.play()
                    elif event.ui_element == self.wave_mode_buttons['advanced']:
                        if self.selected_wave_mode != 'advanced':
                            self.selected_wave_mode = 'advanced'
                            # <<< CLEAR RACE SELECTIONS LIST >>>
                            self.race_selector.selected_races = []
                            # <<< CALL VISUAL UPDATE >>>
                            if hasattr(self.race_selector, 'update_button_visuals'):
                                self.race_selector.update_button_visuals()
                            # <<< END CLEAR >>>
                            self.wave_mode_buttons['advanced'].select()
                            self.wave_mode_buttons['classic'].unselect()
                            self.wave_mode_buttons['wild'].unselect()
                            # <<< ADD CALL TO set_selection_mode for advanced >>>
                            if hasattr(self.race_selector, 'set_selection_mode'):
                                self.race_selector.set_selection_mode('advanced')
                            # <<< END ADD CALL >>>
                            # Update background color scheme
                            if self.background_manager:
                                self.background_manager.set_color_scheme('advanced')
                            # Update active image
                            self.active_title_img = self.title_advanced_img if self.title_advanced_img else self.placeholder_surface
                            if self.active_title_img:
                                self.title_rect = self.active_title_img.get_rect(centerx=self.screen_width // 2)
                                self.title_rect.top = 20
                            # Play advanced music
                            self._play_menu_music(self.advanced_music_path)
                            print("[Game Event] Switched to Advanced wave mode.")
                            if self.click_sound: self.click_sound.play()
                    elif event.ui_element == self.wave_mode_buttons['wild']:
                        if self.selected_wave_mode != 'wild':
                            self.selected_wave_mode = 'wild'
                            # <<< CLEAR RACE SELECTIONS LIST >>>
                            self.race_selector.selected_races = []
                            # <<< CALL VISUAL UPDATE >>>
                            if hasattr(self.race_selector, 'update_button_visuals'):
                                self.race_selector.update_button_visuals()
                            # <<< END CLEAR >>>
                            self.wave_mode_buttons['wild'].select()
                            self.wave_mode_buttons['classic'].unselect()
                            self.wave_mode_buttons['advanced'].unselect()
                            # <<< ADD CALL TO set_selection_mode for wild >>>
                            if hasattr(self.race_selector, 'set_selection_mode'):
                                self.race_selector.set_selection_mode('wild')
                            # <<< END ADD CALL >>>
                            # Update background color scheme
                            if self.background_manager:
                                self.background_manager.set_color_scheme('wild')
                            # Update active image
                            self.active_title_img = self.title_wild_img if self.title_wild_img else self.placeholder_surface
                            if self.active_title_img:
                                self.title_rect = self.active_title_img.get_rect(centerx=self.screen_width // 2)
                                self.title_rect.top = 20
                            # Play wild music
                            self._play_menu_music(self.wild_music_path)
                            print("[Game Event] Switched to Wild wave mode.")
                            if self.click_sound: self.click_sound.play()
                    # Check if the CONFIRM button in RaceSelector was pressed
                    elif hasattr(self.race_selector, 'confirm_button') and event.ui_element == self.race_selector.confirm_button:
                        # <<< GET LIST of selected races >>>
                        selected_races = self.race_selector.get_selected_races() # Expecting a list

                        # <<< VALIDATE number of races based on mode >>>
                        valid_selection = False
                        if self.selected_wave_mode == 'classic' and len(selected_races) == 1:
                            valid_selection = True
                        # <<< ADD WILD TO 2-RACE CHECK >>>
                        elif (self.selected_wave_mode == 'advanced' or self.selected_wave_mode == 'wild') and len(selected_races) == 2:
                            valid_selection = True
                        else:
                            # Provide feedback if invalid
                            if self.selected_wave_mode == 'classic':
                                print("[Game Event] Invalid Selection: Classic mode requires exactly 1 race.")
                                # TODO: Show visual feedback to user?
                            # <<< UPDATE ADVANCED/WILD MESSAGE >>>
                            elif self.selected_wave_mode == 'advanced' or self.selected_wave_mode == 'wild':
                                print(f"[Game Event] Invalid Selection: {self.selected_wave_mode.capitalize()} mode requires exactly 2 races.")
                                # TODO: Show visual feedback to user?
                            # Play an error sound?

                        if valid_selection:
                            if self.click_sound: self.click_sound.play()

                            print(f"[Game Event] Races confirmed: {selected_races}")
                            # <<< Stop Menu Music >>>
                            pygame.mixer.music.stop()
                            print("[Game Event] Stopped menu music.")

                            # Determine Wave File (Path logic is okay now)
                            current_dir = os.path.dirname(os.path.abspath(__file__))
                            data_dir = os.path.join(current_dir, 'data')
                            # <<< UPDATE WAVE FILENAME LOGIC >>>
                            if self.selected_wave_mode == 'advanced':
                                wave_filename = 'waves_advanced.json'
                            elif self.selected_wave_mode == 'wild':
                                wave_filename = 'waves_wild.json'
                            else: # Default to classic
                                wave_filename = 'waves.json'
                            # <<< END WAVE FILENAME LOGIC >>>
                            wave_file_path = os.path.join(data_dir, wave_filename)
                            print(f"[Game Event] Using wave file: {wave_file_path}")

                            # Kill UI elements
                            self.race_selector.kill()
                            self.wave_mode_buttons['classic'].kill()
                            self.wave_mode_buttons['advanced'].kill()
                            self.wave_mode_buttons['wild'].kill() # <<< KILL WILD BUTTON
                            print("[Game Event] Race selector and wave mode UI killed.")

                            try:
                                # <<< PASS LIST of races to GameScene >>>
                                self.start_game(selected_races)
                            except Exception as e:
                                print(f"[Game Event] Error starting game: {e}")
                                self.game_state = "error"
                                self.active_game_scene = None
                        # else: Handled above with validation feedback

            elif self.game_state == "playing" and self.active_game_scene:
                # Handle game scene events
                self.active_game_scene.handle_event(event)
                
        # Return True to continue the main loop unless explicitly stopped
        # return True # Not needed, loop continues based on self.running

    def update(self):
        """Update game state"""
        self.time_delta = self.clock.tick(FPS) / 1000.0
        self.current_game_time = pygame.time.get_ticks() / 1000.0
        
        # Update background effects
        if self.background_manager:
            self.background_manager.update()
        
        # Update UI manager first - crucial for button states, etc.
        self.ui_manager.update(self.time_delta)
        
        # Handle volume slider if modal is visible
        if self.options_modal_visible and hasattr(self, 'volume_slider'):
            current_value = self.volume_slider.get_current_value()
            if current_value != self.last_volume_value:
                # Update game volume
                volume = current_value / 100.0
                pygame.mixer.music.set_volume(volume)
                if self.click_sound:
                    self.click_sound.set_volume(volume)
                if self.placement_sound:
                    self.placement_sound.set_volume(volume)
                if self.cancel_sound:
                    self.cancel_sound.set_volume(volume)
                if self.sell_sound:
                    self.sell_sound.set_volume(volume)
                if self.invalid_placement_sound:
                    self.invalid_placement_sound.set_volume(volume)
                self.last_volume_value = current_value
        
        if self.game_state == "race_selection":
            # RaceSelector UI is updated by the manager
            # Our new buttons are also updated by the manager
            pass 
        elif self.game_state == "playing" and self.active_game_scene:
            # Update the active game scene
            self.active_game_scene.update(self.time_delta)
        elif self.game_state == "error":
            # Handle error state update (e.g., display error message)
            pass

    def draw(self):
        """Draw the game state to the screen"""
        # Determine which surface to draw to
        if FORCE_RESOLUTION and hasattr(self, 'game_surface') and self.game_surface:
            # Draw to game surface at fixed resolution (with borders)
            target_surface = self.game_surface
        else:
            # Draw directly to screen (no borders needed)
            target_surface = self.screen
        
        # Draw the animated background first
        if self.background_manager:
            self.background_manager.draw(target_surface)
        else:
            target_surface.fill(self.BACKGROUND_COLOR)  # Fallback to solid color
        
        # Draw based on game state
        if self.game_state == "race_selection":
            # --- Draw Title Image or Placeholder FIRST --- 
            if self.active_title_img and self.title_rect:
                target_surface.blit(self.active_title_img, self.title_rect)
            else:
                 print("[Draw] No active title image or rect available.")
            # --- End Title Image Draw --- 
            
            # UI Manager draws the RaceSelector UI elements AND our new buttons
            self.ui_manager.draw_ui(target_surface)
            
        elif self.game_state == "playing" and self.active_game_scene:
            # Draw the active game scene
            self.active_game_scene.draw(target_surface, self.time_delta, self.current_game_time)
            # UI Manager still needs to be drawn for in-game UI (if any)
            self.ui_manager.draw_ui(target_surface) 
            
        elif self.game_state == "error":
             # Example: Draw an error message
             try:
                 font = pygame.font.Font(None, 48)
                 error_text = font.render("Error Initializing Game Scene!", True, RED)
                 text_rect = error_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                 target_surface.blit(error_text, text_rect)
             except Exception as font_e:
                 print(f"[Draw] Error rendering error text: {font_e}")
             # Draw UI manager even in error state if needed
             self.ui_manager.draw_ui(target_surface)
             
        else: # Fallback if state is unknown or GameScene not ready
             # Draw UI manager which might contain some default state or message
             self.ui_manager.draw_ui(target_surface)

        # --- Draw Custom Cursor (if loaded) LAST --- 
        if self.custom_cursor_image:
            cursor_pos = pygame.mouse.get_pos()
            # Always draw cursor at the actual mouse position on the display
            self.screen.blit(self.custom_cursor_image, cursor_pos)
        # --- End Custom Cursor --- 

        # For fixed resolution mode with borders, blit the game surface to the display
        if FORCE_RESOLUTION and hasattr(self, 'game_surface') and self.game_surface:
            # Fill screen with black
            self.screen.fill((0, 0, 0))
            # Blit the game surface centered on the display
            self.screen.blit(self.game_surface, (self.offset_x, self.offset_y))

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

    def _play_menu_music(self, music_path):
        """Helper function to load and play menu music, handling errors."""
        if music_path and os.path.exists(music_path):
            try:
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1) # Play indefinitely
                print(f"[Music] Started playing: {os.path.basename(music_path)}")
            except pygame.error as e:
                print(f"[Music] Error loading/playing {os.path.basename(music_path)}: {e}")
                pygame.mixer.music.stop() # Ensure it's stopped if error occurred
        else:
            print(f"[Music] Path invalid or file not found, cannot play: {music_path}")
            pygame.mixer.music.stop() # Stop any potentially playing music

    def toggle_options_modal(self):
        if not hasattr(self, 'low_effects_mode'):
            self.low_effects_mode = False
        """Toggle the options modal overlay"""
        if not self.options_modal_visible:
            # Create modal and widgets only if they don't exist
            if not self.options_modal:
                modal_width = 400
                modal_height = 400
                modal_x = (self.screen_width - modal_width) // 2
                modal_y = (self.screen_height - modal_height) // 2
                self.options_modal = pygame_gui.elements.UIWindow(
                    pygame.Rect(modal_x, modal_y, modal_width, modal_height),
                    window_display_title='Options',
                    manager=self.ui_manager,
                    object_id='#options_modal'
                )
                button_width = 200
                button_height = 40
                button_x = (modal_width - button_width) // 2
                self.volume_slider = pygame_gui.elements.UIHorizontalSlider(
                    relative_rect=pygame.Rect(button_x, 50, button_width, button_height),
                    start_value=100,
                    value_range=(0, 100),
                    manager=self.ui_manager,
                    container=self.options_modal,
                    object_id='#volume_slider'
                )
                self.last_volume_value = 100
                self.volume_label = pygame_gui.elements.UILabel(
                    relative_rect=pygame.Rect(button_x, 20, button_width, 20),
                    text='Volume',
                    manager=self.ui_manager,
                    container=self.options_modal,
                    object_id='#volume_label'
                )
                # Radio-style buttons for effects mode
                self.default_mode_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(button_x, 110, button_width, button_height),
                    text='Default',
                    manager=self.ui_manager,
                    container=self.options_modal,
                    object_id='#default_mode_button'
                )
                self.low_effects_mode_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(button_x, 160, button_width, button_height),
                    text='Low Effects Mode',
                    manager=self.ui_manager,
                    container=self.options_modal,
                    object_id='#low_effects_mode_button'
                )
                self.apply_options_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(button_x, 220, button_width, button_height),
                    text='Apply',
                    manager=self.ui_manager,
                    container=self.options_modal,
                    object_id='#apply_options_button'
                )
                self.close_options_button = pygame_gui.elements.UIButton(
                    relative_rect=pygame.Rect(button_x, modal_height - 60, button_width, button_height),
                    text='Close',
                    manager=self.ui_manager,
                    container=self.options_modal,
                    object_id='#close_options_button'
                )
            # Set the visual state of the buttons
            self.pending_low_effects_selection = 'Low Effects Mode' if self.low_effects_mode else 'Default'
            if self.pending_low_effects_selection == 'Low Effects Mode':
                self.low_effects_mode_button.select()
                self.default_mode_button.unselect()
            else:
                self.default_mode_button.select()
                self.low_effects_mode_button.unselect()
            self.options_modal_visible = True
            self.options_modal.show()
        else:
            self.options_modal_visible = False
            self.options_modal.hide()
            
    def start_game(self, selected_races_list):
        """Start the game with the selected races."""
        # Clean up options modal if it exists
        if self.options_modal:
            self.options_modal.kill()
            self.options_modal = None
            self.options_modal_visible = False
            self.volume_slider = None
            self.volume_label = None
            self.close_options_button = None
            
        # Clean up options button
        if self.options_button:
            self.options_button.kill()
            self.options_button = None
        
        # Create game scene with selected races
        self.active_game_scene = GameScene(self, selected_races_list, self.wave_file_path,
                                         self.screen_width, self.screen_height,
                                         self.click_sound, self.placement_sound,
                                         self.cancel_sound, self.sell_sound,
                                         self.invalid_placement_sound)
        self.game_state = "playing"

