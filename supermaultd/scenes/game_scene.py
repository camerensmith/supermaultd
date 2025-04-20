import pygame
import pygame_gui
import os # Need os for listing directory contents
import random # Import random module
from copy import deepcopy  # Import deepcopy
import config # Import config module directly
# print(f"Imported config from: {config.__file__}") # DEBUG: Print path of imported config
from ui.tower_selector import TowerSelector
from ui.tower_assets import TowerAssets
from ui.enemy_assets import EnemyAssets # Import EnemyAssets
from ui.projectile_assets import ProjectileAssets # Import ProjectileAssets
from utils.pathfinding import find_path # Import pathfinding function
from entities.enemy import Enemy # Import Enemy class
from entities.projectile import Projectile # Import Projectile class
from entities.offset_boomerang_projectile import OffsetBoomerangProjectile # <<< ADDED IMPORT
# Import all necessary effect classes at the top level
from entities.effect import Effect, FloatingTextEffect, ChainLightningVisual, RisingFadeEffect, GroundEffectZone, FlamethrowerParticleEffect, SuperchargedZapEffect, AcidSpewParticleEffect, PulseImageEffect, ExpandingCircleEffect, DrainParticleEffect # Added AcidSpewParticleEffect, PulseImageEffect, and ExpandingCircleEffect, DrainParticleEffect
from entities.orbiting_damager import OrbitingDamager # NEW IMPORT
from entities.pass_through_exploder import PassThroughExploder # NEW IMPORT
import json # Import json for loading armor data


# Define wave states
WAVE_STATE_IDLE = "IDLE"
WAVE_STATE_WAITING = "WAITING_DELAY"
WAVE_STATE_SPAWNING = "SPAWNING"
WAVE_STATE_COMPLETE = "WAVE_COMPLETE" # Optional: Wait for enemies to clear
WAVE_STATE_ALL_DONE = "ALL_WAVES_COMPLETE"
WAVE_STATE_INTERMISSION = "INTERMISSION" # Added new state

class GameScene:
    def __init__(self, game, selected_race, screen_width, screen_height, click_sound, placement_sound, cancel_sound, sell_sound, invalid_placement_sound):
        """
        Initialize the game scene with new layout using actual screen dimensions.
        
        :param game: Reference to the game instance
        :param selected_race: The race selected by the player
        :param screen_width: Actual width of the screen/window
        :param screen_height: Actual height of the screen/window
        :param click_sound: Sound to play when clicking on the UI
        :param placement_sound: Sound to play when placing a tower
        :param cancel_sound: Sound to play when canceling placement
        :param sell_sound: Sound to play when selling a tower
        :param invalid_placement_sound: Sound to play when tower placement is invalid
        """
        print(f"Initializing GameScene with race: {selected_race}")
        self.game = game
        self.selected_race = selected_race
        self.screen_width = screen_width # Store actual dimensions
        self.screen_height = screen_height
        # Restore sounds from arguments
        self.click_sound = click_sound
        self.placement_sound = placement_sound
        self.cancel_sound = cancel_sound
        self.sell_sound = sell_sound
        self.invalid_placement_sound = invalid_placement_sound

        # --- Load Death Sound --- 
        self.death_sound = None
        try:
            death_sound_path = os.path.join("assets", "sounds", "death.mp3") 
            if os.path.exists(death_sound_path):
                self.death_sound = pygame.mixer.Sound(death_sound_path)
                print(f"[GameScene Init] Loaded death sound: {death_sound_path}")
            else:
                print(f"[GameScene Init] Warning: Death sound file not found: {death_sound_path}")
        except pygame.error as e:
            print(f"[GameScene Init] Error loading death sound: {e}")
        # --- End Death Sound Loading ---

        # Get race data
        self.race_data = self.game.get_race_info(selected_race)
        if not self.race_data:
            raise ValueError(f"Race data not found for {selected_race}")
        self.available_towers = self.race_data.get("towers", {}) # <<< MOVED HERE

        # --- Get Base Directory for Path Construction ---
        # Get the directory where this game_scene.py file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go one level up to the project's root data directory (assuming data is sibling to scenes)
        data_dir = os.path.join(os.path.dirname(current_dir), 'data') 
        # --- End Base Directory ---
        
        # Game state
        self.towers = []
        self.enemies = []
        self.money = config.STARTING_MONEY
        self.lives = config.STARTING_LIVES
        self.projectiles = [] # List to hold active projectiles
        self.active_beams = [] # List to hold active beam effects { 'tower': tower, 'target': enemy, 'end_time': timestamp }
        self.effects = [] # List to hold active visual effects
        self.orbiting_damagers = [] # List for orbiting damagers (We added this earlier, maybe manually?)
        self.pass_through_exploders = [] # NEW: List for pass-through exploders
        
        # --- Wave System State --- 
        self.all_wave_data = [] # Will be loaded from waves.json
        self.current_wave_index = -1
        self.wave_state = WAVE_STATE_IDLE # Start in IDLE
        self.wave_timer = 0.0 # Used for delay between waves
        self.spawning_groups = [] # List to track groups currently spawning
        self.enemies_alive_this_wave = 0 # Track enemies spawned in current wave
        self.wave_started = False # Flag to prevent restarting wave 0
        # -------------------------
        
        # Tower Chain Link Update Timer -- REMOVED
        # self.last_link_update_time = 0.0
        # self.link_update_interval = 1.0 # Seconds between recalculating links
        
        # UI state
        self.selected_tower = None
        self.tower_preview = None
        self.hovered_tower = None # Track which tower mouse is over
        
        # --- Layout Calculations (Use screen_width, screen_height) --- 
        # Panel dimensions based on percentage
        self.panel_pixel_width = int(self.screen_width * config.UI_PANEL_WIDTH_PERCENT)
        self.panel_pixel_height = self.screen_height - (config.UI_PANEL_PADDING * 2) # Use full height minus top/bottom padding
        self.panel_x = self.screen_width - self.panel_pixel_width - config.UI_PANEL_PADDING
        self.panel_y = config.UI_PANEL_PADDING

        # Grid dimensions based on remaining space
        self.usable_grid_pixel_width = self.screen_width - self.panel_pixel_width - (config.UI_PANEL_PADDING * 2)
        # Calculate grid height based on available space first
        _available_height = self.screen_height - (config.UI_PANEL_PADDING * 2) # Use space between top/bottom padding
        self.grid_height = max(1, _available_height // config.GRID_SIZE) # Ensure at least 1 row
        # Set the usable pixel height to be an exact multiple of grid size
        self.usable_grid_pixel_height = self.grid_height * config.GRID_SIZE
        
        self.grid_width = self.usable_grid_pixel_width // config.GRID_SIZE
        self.grid_width = max(1, self.grid_width) # Ensure at least 1x1 grid
        self.grid = [[0 for _ in range(self.grid_width)] for _ in range(self.grid_height)]

        # Mark ALL restricted areas with value 2
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                is_restricted = False
                # Check side columns
                if x < config.RESTRICTED_TOWER_AREA_WIDTH or x >= self.grid_width - config.RESTRICTED_TOWER_AREA_WIDTH:
                    is_restricted = True
                # Check top rows
                if y < config.RESTRICTED_TOWER_AREA_HEIGHT:
                    is_restricted = True
                # Check bottom rows
                if y >= self.grid_height - config.RESTRICTED_TOWER_AREA_HEIGHT:
                    is_restricted = True
                
                if is_restricted:
                    self.grid[y][x] = 2 # Mark restricted

        # Calculate spawn area position (centered at top)
        self.spawn_area_x = (self.grid_width - config.SPAWN_AREA_WIDTH) // 2
        self.spawn_area_y = 0  # Top of the grid
        self.spawn_area_rect = pygame.Rect(
            self.spawn_area_x * config.GRID_SIZE + config.UI_PANEL_PADDING,
            self.spawn_area_y * config.GRID_SIZE + config.UI_PANEL_PADDING,
            config.SPAWN_AREA_WIDTH * config.GRID_SIZE,
            config.SPAWN_AREA_HEIGHT * config.GRID_SIZE
        )

        # Calculate objective area position (centered at bottom)
        self.objective_area_x = (self.grid_width - config.OBJECTIVE_AREA_WIDTH) // 2
        self.objective_area_y = self.grid_height - config.OBJECTIVE_AREA_HEIGHT  # Bottom of the grid
        self.objective_area_rect = pygame.Rect(
            self.objective_area_x * config.GRID_SIZE + config.UI_PANEL_PADDING,
            self.objective_area_y * config.GRID_SIZE + config.UI_PANEL_PADDING,
            config.OBJECTIVE_AREA_WIDTH * config.GRID_SIZE,
            config.OBJECTIVE_AREA_HEIGHT * config.GRID_SIZE
        )

        # Define Pathfinding Start/End Points (use grid coordinates)
        # Logical Path Start (Ensure it starts on the first *walkable* row)
        self.path_start_x = self.spawn_area_x + config.SPAWN_AREA_WIDTH // 2
        self.path_start_x = max(config.RESTRICTED_TOWER_AREA_WIDTH, min(self.grid_width - 1 - config.RESTRICTED_TOWER_AREA_WIDTH, self.path_start_x)) # Clamp X
        # Set Y directly to the first row *after* the top restricted area
        self.path_start_y = config.RESTRICTED_TOWER_AREA_HEIGHT 
        
        # Visual Spawn Point (Pixel coordinates, centered X in spawn area, Y at the TOP edge of spawn area)
        # This should still be based on the visual spawn area, not the logical path start
        _visual_spawn_x_grid = self.spawn_area_x + config.SPAWN_AREA_WIDTH // 2
        _visual_spawn_x_grid = max(config.RESTRICTED_TOWER_AREA_WIDTH, min(self.grid_width - 1 - config.RESTRICTED_TOWER_AREA_WIDTH, _visual_spawn_x_grid))
        self.visual_spawn_x_pixel = (_visual_spawn_x_grid * config.GRID_SIZE) + (config.GRID_SIZE // 2)
        self.visual_spawn_y_pixel = (self.spawn_area_y * config.GRID_SIZE) + (config.GRID_SIZE // 2)

        # Logical Path End (Target the last *walkable* row)
        self.path_end_x = self.objective_area_x + config.OBJECTIVE_AREA_WIDTH // 2 # Keep X centered
        # Clamp X to avoid side restricted columns
        self.path_end_x = max(config.RESTRICTED_TOWER_AREA_WIDTH, min(self.grid_width - 1 - config.RESTRICTED_TOWER_AREA_WIDTH, self.path_end_x))
        # Set Y directly to the last row *before* the bottom restricted area
        self.path_end_y = self.grid_height - 1 - config.RESTRICTED_TOWER_AREA_HEIGHT
        # Ensure it's not negative if grid/restricted areas are large
        self.path_end_y = max(self.path_start_y, self.path_end_y) # Must be at least start_y


        # Check grid value *before* potentially modifying start/end if they land on tower (unlikely here)
        start_val = self.grid[self.path_start_y][self.path_start_x] if 0 <= self.path_start_y < self.grid_height and 0 <= self.path_start_x < self.grid_width else -1
        end_val = self.grid[self.path_end_y][self.path_end_x] if 0 <= self.path_end_y < self.grid_height and 0 <= self.path_end_x < self.grid_width else -1
        print(f"DEBUG INIT: Calculated Path Start: ({self.path_start_x}, {self.path_start_y}), Grid Value: {start_val}")
        print(f"DEBUG INIT: Calculated Path End: ({self.path_end_x}, {self.path_end_y}), Grid Value: {end_val}")
        # Add a check to ensure start/end are actually walkable (value 0)
        if start_val != 0:
            print(f"ERROR: Calculated Path Start ({self.path_start_x}, {self.path_start_y}) is NOT walkable (Value: {start_val})!")
        if end_val != 0:
             print(f"ERROR: Calculated Path End ({self.path_end_x}, {self.path_end_y}) is NOT walkable (Value: {end_val})!")
        # --- END DEBUG ---

        # --- End Layout Calculations ---

        # Initialize pygame_gui Manager (Pass actual screen size)
        self.ui_manager = pygame_gui.UIManager((self.screen_width, self.screen_height), 'theme.json') 
        
        # Load and scale background texture
        try:
            # Use the correct relative path from the supermaultd working directory
            background_image = pygame.image.load("assets/images/background.jpg").convert()
            self.grid_background_texture = pygame.transform.scale(
                background_image, 
                (self.usable_grid_pixel_width, self.usable_grid_pixel_height)
            )
        except pygame.error as e:
            print(f"Error loading background.jpg: {e}")
            self.grid_background_texture = None # Fallback
        
        # --- Load Data using Constructed Paths --- 
        armor_file_path = os.path.join(data_dir, "armortypes.json")
        damage_file_path = os.path.join(data_dir, "tower_races.json")

        self.armor_data = self.load_armor_data(armor_file_path)
        # Load Damage Type Data (still from tower_races.json, but use correct path)
        self.damage_type_data = self.load_damage_types(damage_file_path)
       
        # --- End Data Loading --- 
        
        # --- Load Wave Data ---
        wave_file_path = os.path.join(data_dir, "waves.json")
        self.all_wave_data = self.load_wave_data(wave_file_path)
        # ---------------------
        
        # Initialize tower assets
        self.tower_assets = TowerAssets()
        
        # Initialize enemy assets
        self.enemy_assets = EnemyAssets()
        
        # Initialize projectile assets
        self.projectile_assets = ProjectileAssets()

        # Load effect assets
        # self.blood_splatter_frames = self.load_effect_frames("assets/effects/blood_splatter") # Old frame loading
        self.blood_splatter_base_image = self.load_single_image("assets/effects/blood_splatter0.png")
        
        # --- Load Kraken Effect Image ---
        self.kraken_effect_image = self.load_single_image("assets/effects/kraken.png")
        if not self.kraken_effect_image:
            print("Warning: Failed to load assets/effects/kraken.png")
        # --- End Kraken Loading ---

        # --- Load Glacial Heart Pulse Image ---
        self.glacial_heart_pulse_image = self.load_single_image("assets/effects/igloo_glacial_heart.png")
        if not self.glacial_heart_pulse_image:
            print("Warning: Failed to load assets/effects/igloo_glacial_heart.png")
        # --- End Glacial Heart Pulse Loading ---

        # --- Font for Countdown Timer ---
        try:
            self.timer_font = pygame.font.Font(None, 48) # Use default font, size 48
        except Exception as e:
            print(f"Error loading default font: {e}")
            self.timer_font = None # Fallback
        # -------------------------------
        
        # --- Load Attack Visual Assets --- 
        self.attack_visuals = {}
        fire_burst_img = self.load_single_image("assets/effects/fire_burst.png")
        if fire_burst_img:
            self.attack_visuals["fire_burst"] = fire_burst_img
        else:
            print("Warning: Failed to load assets/effects/fire_burst.png")
        # Add other attack visuals here as needed...
        flak_cannon_img = self.load_single_image("assets/effects/tank_aegis_flak_cannon.png")
        if flak_cannon_img:
            self.attack_visuals["tank_aegis_flak_cannon"] = flak_cannon_img
        else:
            print("Warning: Failed to load assets/effects/tank_aegis_flak_cannon.png")
        # --- End Attack Visual Loading ---

        # Initialize tower selector AFTER panel dimensions are calculated
        self.tower_selector = TowerSelector(
            available_towers=self.available_towers, 
            tower_assets=self.tower_assets, 
            manager=self.ui_manager, 
            initial_money=self.money, 
            panel_rect=pygame.Rect(self.panel_x, self.panel_y, self.panel_pixel_width, self.panel_pixel_height),
            damage_type_data=self.damage_type_data,
            click_sound=self.click_sound # Pass sound here
        )
        
        # Placeholder: Spawn a test enemy
        # TODO: Replace with actual wave spawning logic
        self.spawn_test_enemy("enemy1") # Assuming you have an enemy1.png
        
        print(f"GameScene initialized. Actual Size: {self.screen_width}x{self.screen_height}") # Use actual size
        print(f"Grid Area (Pixels): {self.usable_grid_pixel_width}x{self.usable_grid_pixel_height} | Grid Cells: {self.grid_width}x{self.grid_height}")
        print(f"UI Panel Area (Pixels): {self.panel_pixel_width}x{self.panel_pixel_height} at ({self.panel_x},{self.panel_y})")
        print(f"Enemy Preview Area: {self.objective_area_rect}")
        

        
    def handle_event(self, event):
        """Handle pygame events"""
        # Handle UI events first
        self.tower_selector.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Convert mouse position to grid coordinates
                mouse_x, mouse_y = event.pos
                # Need to account for the grid's offset from screen origin
                grid_offset_x = config.UI_PANEL_PADDING
                grid_offset_y = config.UI_PANEL_PADDING
                if (grid_offset_x <= mouse_x < grid_offset_x + self.usable_grid_pixel_width and
                    grid_offset_y <= mouse_y < grid_offset_y + self.usable_grid_pixel_height):
                    # Calculate grid coordinates relative to the grid's top-left
                    grid_x = (mouse_x - grid_offset_x) // config.GRID_SIZE
                    grid_y = (mouse_y - grid_offset_y) // config.GRID_SIZE
                    print(f"Left-clicked grid position: ({grid_x}, {grid_y})")
                    # self.handle_tower_placement(grid_x, grid_y) # REMOVED from MOUSEBUTTONDOWN
                
            elif event.button == 3: # Right click
                mouse_x, mouse_y = event.pos
                # Account for grid offset
                grid_offset_x = config.UI_PANEL_PADDING
                grid_offset_y = config.UI_PANEL_PADDING
                if (grid_offset_x <= mouse_x < grid_offset_x + self.usable_grid_pixel_width and
                    grid_offset_y <= mouse_y < grid_offset_y + self.usable_grid_pixel_height):
                    # Calculate grid coordinates relative to the grid's top-left
                    grid_x = (mouse_x - grid_offset_x) // config.GRID_SIZE
                    grid_y = (mouse_y - grid_offset_y) // config.GRID_SIZE
                    
                    # --- Check if a tower exists at the clicked location ---
                    tower_at_location = None
                    for tower in self.towers:
                        if (tower.top_left_grid_x <= grid_x < tower.top_left_grid_x + tower.grid_width and
                            tower.top_left_grid_y <= grid_y < tower.top_left_grid_y + tower.grid_height):
                            tower_at_location = tower
                            break # Found the tower

                    # --- Check if currently previewing a tower ---
                    is_previewing = self.tower_selector.get_selected_tower() is not None
                    
                    # --- Decide action based on findings ---
                    if tower_at_location:
                        # Existing behavior: Tower exists, try to sell it
                        print(f"Right-clicked grid position: ({grid_x}, {grid_y}) - Found Tower {tower_at_location.tower_id}. Attempting sell.")
                        self.sell_tower_at(grid_x, grid_y)
                    elif is_previewing:
                        # New behavior: No tower here, but we are previewing, so cancel preview
                        print(f"Right-clicked empty grid position: ({grid_x}, {grid_y}) while previewing. Cancelling placement.")
                        self.tower_selector.clear_selection()
                        self.selected_tower = None 
                        self.tower_preview = None
                        # Play cancel sound
                        if self.cancel_sound:
                            self.cancel_sound.play()
                    else:
                        # No tower here, and not previewing anything. Do nothing.
                        print(f"Right-clicked empty grid position: ({grid_x}, {grid_y}) - Not previewing. Doing nothing.")
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1: # Left mouse button release
                # Check if a tower was selected when the button was released
                selected_tower_id = self.tower_selector.get_selected_tower()
                if selected_tower_id:
                    mouse_x, mouse_y = event.pos
                    # Account for grid offset
                    grid_offset_x = config.UI_PANEL_PADDING
                    grid_offset_y = config.UI_PANEL_PADDING
                    if (grid_offset_x <= mouse_x < grid_offset_x + self.usable_grid_pixel_width and
                        grid_offset_y <= mouse_y < grid_offset_y + self.usable_grid_pixel_height):
                        # Calculate grid coordinates relative to the grid's top-left
                        grid_x = (mouse_x - grid_offset_x) // config.GRID_SIZE
                        grid_y = (mouse_y - grid_offset_y) // config.GRID_SIZE
                        print(f"Left-button released at grid position: ({grid_x}, {grid_y})")
                        self.handle_tower_placement(grid_x, grid_y) # Place tower on release
                    # else: # Optional: If released outside grid, cancel placement
                        # self.tower_selector.clear_selection()
                        # self.selected_tower = None
                        # self.tower_preview = None
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.tower_selector.clear_selection()
                self.selected_tower = None
                self.tower_preview = None
            elif event.key == pygame.K_g: # G for Gnoll
                self.spawn_test_enemy("gnoll")
                print("Spawned Gnoll (press 'G')")
            elif event.key == pygame.K_s: # S for Spectre
                self.spawn_test_enemy("quillpig")
                print("Spawned Quillpig (press 'S')")
            elif event.key == pygame.K_t: # T for Soldier (replacing generic test)
                self.spawn_test_enemy("soldier")
                print("Spawned Soldier (press 'T')")
            elif event.key == pygame.K_1: # 1 for Dust Mite
                self.spawn_test_enemy("dust_mite")
                print("Spawned Dust Mite (press '1')")
            elif event.key == pygame.K_2: # 2 for Doom Lord
                self.spawn_test_enemy("doomlord")
                print("Spawned Doom Lord (press '2')")
            elif event.key == pygame.K_3: # 3 for pixie
                self.spawn_test_enemy("dragon_whelp")
                print("Spawned Dragon Whelp (press '3')")
            elif event.key == pygame.K_4: # 4 for bloodfist ogre
                self.spawn_test_enemy("bloodfist_ogre")
                print("Spawned Bloodfist Ogre (press '4')")
            elif event.key == pygame.K_5: # 5 for cyborg
                self.spawn_test_enemy("village_peasant")
                print("Spawned Village Peasant (press '5')")
            elif event.key == pygame.K_RETURN: # ENTER key press
                print("DEBUG: ENTER key pressed.")
                if self.wave_state == WAVE_STATE_IDLE and not self.wave_started:
                    print("Starting Wave System...")
                    self.wave_started = True # Set flag
                    # Find the first wave (index 0)
                    if self.all_wave_data: # Check if waves are loaded
                        self.current_wave_index = 0
                        first_wave_data = self.all_wave_data[0]
                        self.wave_timer = first_wave_data.get('delay_before_wave', 5.0) # Use delay from JSON
                        self.wave_state = WAVE_STATE_WAITING
                        print(f"Transitioning to WAITING_DELAY. Timer set to: {self.wave_timer}")
                    else:
                        print("ERROR: No wave data loaded. Cannot start waves.")
                        self.wave_state = WAVE_STATE_IDLE # Remain idle
                else:
                    print(f"Cannot start wave. Current state: {self.wave_state}, Started: {self.wave_started}")
                
        # --- Tower Hover Detection (runs every frame essentially via event loop) ---
        mouse_x, mouse_y = pygame.mouse.get_pos()
        grid_offset_x = config.UI_PANEL_PADDING
        grid_offset_y = config.UI_PANEL_PADDING
        relative_mouse_x = mouse_x - grid_offset_x
        relative_mouse_y = mouse_y - grid_offset_y
        
        found_hover = None
        # Check only if mouse is within the grid area pixels
        if (grid_offset_x <= mouse_x < grid_offset_x + self.usable_grid_pixel_width and
            grid_offset_y <= mouse_y < grid_offset_y + self.usable_grid_pixel_height):
            # Convert relative mouse pixel coords to grid coords for rough check
            hover_grid_x = relative_mouse_x // config.GRID_SIZE
            hover_grid_y = relative_mouse_y // config.GRID_SIZE
            
            # Check against placed towers
            for tower in self.towers:
                # Check if the hover grid coord falls within the tower's footprint
                if (tower.top_left_grid_x <= hover_grid_x < tower.top_left_grid_x + tower.grid_width and
                    tower.top_left_grid_y <= hover_grid_y < tower.top_left_grid_y + tower.grid_height):
                    found_hover = tower
                    break # Found the tower under the cursor
                    
        self.hovered_tower = found_hover # Update the hovered tower (or set to None)
        # --- End Tower Hover Detection --- 

        # Update tower preview position (snap to grid based on mouse)
        if self.tower_selector.get_selected_tower():
            mouse_x, mouse_y = pygame.mouse.get_pos()
            # Account for grid offset when calculating snapped position
            grid_offset_x = config.UI_PANEL_PADDING
            grid_offset_y = config.UI_PANEL_PADDING
            relative_mouse_x = mouse_x - grid_offset_x
            relative_mouse_y = mouse_y - grid_offset_y
            
            grid_x = relative_mouse_x // config.GRID_SIZE
            grid_y = relative_mouse_y // config.GRID_SIZE
            
            # Check if the calculated grid coordinates are within the grid bounds
            if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
                self.tower_preview = (grid_x, grid_y)
            else:
                self.tower_preview = None
        else:
             self.tower_preview = None # Ensure preview is cleared if no tower selected
                
    def handle_tower_placement(self, grid_x, grid_y):
        """Handle tower placement on the grid, considering tower size."""
        selected_tower_id = self.tower_selector.get_selected_tower()
        if not selected_tower_id:
            return

        tower_data = self.available_towers.get(selected_tower_id)
        if not tower_data:
            return

        # Get tower dimensions (assuming 1x1 if not specified)
        grid_width = tower_data.get('grid_width', 1)
        grid_height = tower_data.get('grid_height', 1)

        # --- Validation Checks ---
        # Use the comprehensive validation method which includes pathfinding
        is_valid = self.is_valid_tower_placement(grid_x, grid_y, grid_width, grid_height)
        if not is_valid:
            print("Invalid tower placement location.") # is_valid prints specific reason
            if self.invalid_placement_sound:
                self.invalid_placement_sound.play()
            return

        # Check if player has enough money (separate from positional validation)
        if self.money < tower_data['cost']:
            print("Not enough money!")
            return

        # --- Placement ---
        # Calculate footprint again (needed for marking the grid)
        offset_x = (grid_width - 1) // 2
        offset_y = (grid_height - 1) // 2
        new_start_x = grid_x - offset_x
        new_end_x = new_start_x + grid_width - 1 # Corrected calculation
        new_start_y = grid_y - offset_y
        new_end_y = new_start_y + grid_height - 1 # Corrected calculation

        # Check if tower is traversable
        is_traversable = tower_data.get('traversable', False)
        print(f"DEBUG PLACEMENT: Tower {selected_tower_id} is_traversable = {is_traversable}") # DEBUG

        # Mark occupied grid cells ONLY if not traversable
        if not is_traversable:
            # --- CORRECTED FOOTPRINT CALCULATION for grid marking ---
            # Calculate the true top-left corner based on center and dimensions
            actual_top_left_x = grid_x - (grid_width - 1) // 2
            actual_top_left_y = grid_y - (grid_height - 1) // 2
            print(f"  DEBUG PLACEMENT: Calculated Top-Left ({actual_top_left_x},{actual_top_left_y}). Width={grid_width}, Height={grid_height}") # DEBUG
            # --------------------------------------------------------
            
            # Loop from the calculated top-left for the full width/height
            for y_offset in range(grid_height):
                for x_offset in range(grid_width):
                    mark_x = actual_top_left_x + x_offset
                    mark_y = actual_top_left_y + y_offset
                    # Check bounds within loop for safety
                    if 0 <= mark_y < self.grid_height and 0 <= mark_x < self.grid_width:
                        print(f"    DEBUG PLACEMENT: Marking grid cell ({mark_x},{mark_y}) = 1") # DEBUG
                        self.grid[mark_y][mark_x] = 1 # Mark as obstacle
                    else:
                        print(f"    DEBUG PLACEMENT: SKIPPING grid cell ({mark_x},{mark_y}) - out of bounds") # DEBUG
            # print(f"Marked grid for non-traversable tower at ({grid_x}, {grid_y})") # Old Print
        else:
            print(f"Skipping grid mark for traversable tower at ({grid_x}, {grid_y})")

        # Create and place the tower (using center grid coordinates)
        from entities.tower import Tower
        # Log data just before creating the tower
        # print(f"DEBUG Handle Placement: id='{selected_tower_id}', data_used={tower_data}")
        tower = Tower(grid_x, grid_y, selected_tower_id, tower_data)
        self.towers.append(tower)
        
        # Play placement sound
        if self.placement_sound:
            self.placement_sound.play()
            
        # --- Spawn Orbiting Damagers if applicable --- 
        if tower.special and tower.special.get("effect") == "orbiting_damager":
            orb_count = tower.special.get("orb_count", 1)
            orb_data = tower.special # Pass the whole special dict as orb_data
            angle_step = 360.0 / orb_count if orb_count > 0 else 0
            
            print(f"Spawning {orb_count} orbiting damagers for {tower.tower_id}")
            for i in range(orb_count):
                start_angle = i * angle_step
                # Create orbiter and associate it with the tower
                new_orbiter = OrbitingDamager(tower, orb_data, start_angle_offset=start_angle)
                tower.orbiters.append(new_orbiter) # Add to the tower's list
        # --- End Orbiter Spawning ---
        
        self.money -= tower_data['cost']
        print(f"Placed tower {selected_tower_id} (size {grid_width}x{grid_height}) at center ({grid_x}, {grid_y})")

        # Update money display
        self.tower_selector.update_money(self.money)

        # Recalculate paths for all existing enemies ONLY if the placed tower is NOT traversable
        if not is_traversable:
            print(f"  DEBUG PLACEMENT: Recalculating enemy paths because {selected_tower_id} is not traversable.") # DEBUG
            for enemy in self.enemies[:]:  # Use slice copy
                # Get enemy's current grid position
                current_grid_x = int(enemy.x // config.GRID_SIZE)
                current_grid_y = int(enemy.y // config.GRID_SIZE)
                
                # Find new path from current position to objective
                new_path = find_path(current_grid_x, current_grid_y, 
                                   self.path_end_x, self.path_end_y, 
                                   self.grid) # Use updated grid
                
                if new_path:
                    # Update enemy's path
                    enemy.grid_path = new_path
                    enemy.path_index = 0  # Reset path index
                    print(f"Updated path for enemy after non-traversable tower placement.")
                else:
                    # If no path found, remove the enemy (it's trapped)
                    print(f"Warning: No path found for enemy after non-traversable tower placement. Removing enemy.")
                    self.enemies.remove(enemy)
        else:
            print("Skipping path recalculation for traversable tower placement.")
            print(f"  DEBUG PLACEMENT: Skipping enemy path recalculation because {selected_tower_id} is traversable.") # DEBUG

        # Clear selection
        self.tower_selector.clear_selection()
        self.selected_tower = None
        self.tower_preview = None
        
        # --- Update Tower Links After Placement --- 
        self.update_tower_links()
        # --- End Link Update --- 
            
    def update(self, time_delta):
        """Update game state"""
        current_game_time = pygame.time.get_ticks() / 1000.0 # Get current time once
        
        # --- Wave System Update --- 
        self.update_wave_system(current_game_time, time_delta)
        # ------------------------
        
        # --- Update Tower Links (Periodically) --- REMOVED
        # time_since_last_link_update = current_game_time - self.last_link_update_time
        # print(f"DEBUG Link Update Check: Time since last={time_since_last_link_update:.2f}s, Interval={self.link_update_interval}s") # Debug print
        # if time_since_last_link_update >= self.link_update_interval:
        #     self.update_tower_links()
        #     self.last_link_update_time = current_game_time
        # --- End Link Update ---
        
        # Update UI
        self.tower_selector.update(time_delta)
        
        # --- Pre-calculate Tower Buff Auras (Affecting Towers) --- 
        # Store as instance variable for use in draw method
        self.tower_buff_auras = [] 
        for tower in self.towers:
            # Check if the tower has a special block and targets towers
            if tower.special and "towers" in tower.special.get('targets', []):
                is_standard_aura = (tower.attack_type == 'aura' or tower.attack_type == 'hybrid')
                is_dot_amp_aura = tower.special.get('effect') == 'dot_amplification_aura'
                
                # Process if it's a standard buff aura OR the new DoT amp aura
                if is_standard_aura or is_dot_amp_aura:
                    aura_radius_units = tower.special.get('aura_radius', 0)
                    if aura_radius_units > 0:
                        aura_radius_pixels = aura_radius_units * (config.GRID_SIZE / 200.0)
                        aura_radius_sq = aura_radius_pixels ** 2
                        self.tower_buff_auras.append({
                            'tower': tower,
                            'radius_sq': aura_radius_sq,
                            'special': tower.special
                        })
                        if is_dot_amp_aura:
                            print(f"DEBUG: Added {tower.tower_id} (dot_amp_aura) to tower_buff_auras.") # Optional debug

        # --- BEGIN Adjacency Buff Calculation --- 
        hq_towers = [t for t in self.towers if t.tower_id == 'police_police_hq']
        if hq_towers: # Only do checks if there's at least one HQ
            towers_already_buffed_by_hq = set() # Prevent double-buffing from multiple HQs
            
            for hq in hq_towers:
                # Define the HQ's bounding box in grid coordinates
                hq_start_x = hq.top_left_grid_x
                hq_end_x = hq_start_x + hq.grid_width - 1
                hq_start_y = hq.top_left_grid_y
                hq_end_y = hq_start_y + hq.grid_height - 1
                
                # Define the adjacency check area (HQ box expanded by 1 cell)
                adj_min_x = hq_start_x - 1
                adj_max_x = hq_end_x + 1
                adj_min_y = hq_start_y - 1
                adj_max_y = hq_end_y + 1
                
                # Check every other tower
                for other_tower in self.towers:
                    if other_tower == hq or other_tower in towers_already_buffed_by_hq:
                        continue # Skip self or already buffed
                        
                    # Define the other tower's bounding box
                    other_start_x = other_tower.top_left_grid_x
                    other_end_x = other_start_x + other_tower.grid_width - 1
                    other_start_y = other_tower.top_left_grid_y
                    other_end_y = other_start_y + other_tower.grid_height - 1
                    
                    # Check for AABB overlap between other tower and HQ's adjacency area
                    # Overlap exists if they are NOT separated
                    is_adjacent = not (other_end_x < adj_min_x or 
                                       other_start_x > adj_max_x or 
                                       other_end_y < adj_min_y or 
                                       other_start_y > adj_max_y)
                                       
                    if is_adjacent:
                        # Ensure the HQ special targets towers
                        if hq.special and hq.special.get('effect') == 'adjacency_damage_buff' and "towers" in hq.special.get('targets', []):
                            # Add the HQ's buff data to the list
                            print(f"DEBUG: Police HQ at ({hq.center_grid_x},{hq.center_grid_y}) applying adjacency buff to {other_tower.tower_id} at ({other_tower.center_grid_x},{other_tower.center_grid_y})")
                            self.tower_buff_auras.append({
                                'tower': hq, # The tower providing the buff
                                'radius_sq': 0, # Radius doesn't apply here
                                'special': hq.special
                            })
                            towers_already_buffed_by_hq.add(other_tower)
        # --- END Adjacency Buff Calculation --- 

        # --- BEGIN Spark Power Plant Adjacency Buff Calculation ---
        plant_towers = [t for t in self.towers if t.tower_id == 'spark_power_plant']
        if plant_towers:
            towers_already_buffed_by_plant = set() # Prevent double-buffing from multiple plants

            for plant in plant_towers:
                # Define the plant's bounding box
                plant_start_x = plant.top_left_grid_x
                plant_end_x = plant_start_x + plant.grid_width - 1
                plant_start_y = plant.top_left_grid_y
                plant_end_y = plant_start_y + plant.grid_height - 1

                # Define the adjacency check area
                adj_min_x = plant_start_x - 1
                adj_max_x = plant_end_x + 1
                adj_min_y = plant_start_y - 1
                adj_max_y = plant_end_y + 1

                # Check every other tower
                for other_tower in self.towers:
                    if other_tower == plant or other_tower in towers_already_buffed_by_plant:
                        continue

                    # Define the other tower's bounding box
                    other_start_x = other_tower.top_left_grid_x
                    other_end_x = other_start_x + other_tower.grid_width - 1
                    other_start_y = other_tower.top_left_grid_y
                    other_end_y = other_start_y + other_tower.grid_height - 1

                    # AABB overlap check for adjacency
                    is_adjacent = not (other_end_x < adj_min_x or
                                       other_start_x > adj_max_x or
                                       other_end_y < adj_min_y or
                                       other_start_y > adj_max_y)

                    if is_adjacent:
                        # Check if the plant's special is the correct buff and targets towers
                        if plant.special and plant.special.get('effect') == 'adjacency_attack_speed_buff' and "towers" in plant.special.get('targets', []):
                            print(f"DEBUG: Power Plant at ({plant.center_grid_x},{plant.center_grid_y}) applying adjacency buff to {other_tower.tower_id} at ({other_tower.center_grid_x},{other_tower.center_grid_y})")
                            # Add the plant's buff data to the list
                            self.tower_buff_auras.append({
                                'tower': plant, 
                                'radius_sq': 0, 
                                'special': plant.special
                            })
                            towers_already_buffed_by_plant.add(other_tower)
        # --- END Spark Power Plant Adjacency Buff Calculation ---

        # --- Pre-calculate Enemy Aura Towers (Affecting Enemies) --- 
        enemy_aura_towers = []
        for tower in self.towers:
            # Check if the tower has a special block and an aura radius
            if tower.special and tower.special.get('aura_radius', 0) > 0:
                effect_type = tower.special.get('effect')
                is_pulse_aura = effect_type and effect_type.endswith('_pulse_aura')
                is_continuous_aura = tower.attack_type in ['aura', 'hybrid']
                
                # Consider it if it's a standard continuous aura OR a pulse aura (even if attack_type is none)
                if is_continuous_aura or is_pulse_aura:
                    aura_targets = tower.special.get('targets', []) # Pulse auras might still define targets
                    # Check if the targets list contains enemy types or the old "enemies" string
                    # Ensure the aura isn't targeting towers (handled above in tower_buff_auras)
                    targets_enemies = any(t in ["ground", "air", "enemies"] for t in aura_targets) or aura_targets == "enemies"
                    targets_towers = tower.special.get('targets') == 'towers' # Check specifically
                    
                    # Include if it targets enemies and NOT exclusively towers
                    # Also include if it's a pulse aura, assuming pulses target enemies unless specified otherwise?
                    # Let's refine: Include if (targets enemies AND not targets towers) OR (is pulse aura)
                    if (targets_enemies and not targets_towers) or is_pulse_aura:
                        aura_radius_units = tower.special.get('aura_radius', 0)
                        aura_radius_pixels = aura_radius_units * (config.GRID_SIZE / 200.0)
                        aura_radius_sq = aura_radius_pixels ** 2
                        enemy_aura_towers.append({
                            'tower': tower,
                            'radius_sq': aura_radius_sq,
                            'special': tower.special
                        })
                        # Debug print to confirm inclusion
                        print(f"DEBUG: Included {tower.tower_id} (Type: {tower.attack_type}, Effect: {effect_type}) in enemy_aura_towers.")

        
        # --- Update Towers --- 
        for tower in self.towers:
            # --- Call Tower's Internal Update (for self-managed abilities) --- 
            # Pass current time, enemies, ALL callbacks, and the image loader
            tower.update(current_game_time, self.enemies, 
                         self.add_pass_through_exploder, # Callback 1
                         self.add_visual_effect,          # Callback 2
                         self.can_afford,                 # Callback 3 
                         self.deduct_money,               # Callback 4 
                         self.add_projectile,             # Callback 5 (NEW)
                         self.load_single_image)          # Asset Loader
            # ------------------------------------------------------------------
            
            # Calculate buffed stats once per tower update
            # Note: get_buffed_stats itself needs the list of auras
            # Pass current_game_time and self.towers along with auras
            buffed_stats = tower.get_buffed_stats(current_game_time, self.tower_buff_auras, self.towers) # Buffs influence interval/damage
            effective_interval = buffed_stats['attack_interval'] # Use the buffed interval
            
            # --- Gold Generation Check --- 
            if tower.special and tower.special.get("effect") == "gold_generation":
                interval = tower.special.get("interval", 10.0) 
                if current_game_time - tower.last_pulse_time >= interval:
                    amount = tower.special.get("amount", 0)
                    if amount > 0:
                        self.money += amount
                        self.tower_selector.update_money(self.money)
                        print(f"Tower {tower.tower_id} generated ${amount}. Current Money: ${self.money}")
                        
                        # Create Floating Text Effect
                        try:
                            # Calculate position (above tower center)
                            grid_offset_x = config.UI_PANEL_PADDING
                            grid_offset_y = config.UI_PANEL_PADDING
                            # Use tower's center pixel coordinates (self.x, self.y)
                            text_x = tower.x + grid_offset_x
                            text_y = tower.y + grid_offset_y - (tower.height_pixels / 2) # Start above tower center
                            
                            gold_text = f"+{amount} G"
                            gold_color = (255, 215, 0) # Gold color
                            text_effect = FloatingTextEffect(text_x, text_y, gold_text, color=gold_color)
                            self.effects.append(text_effect)
                        except Exception as e:
                            print(f"Error creating gold text effect: {e}")
                            
                    tower.last_pulse_time = current_game_time 
            
            # --- Specific Broadside Firing Logic --- 
            is_broadside = tower.special and tower.special.get("effect") == "broadside"
            if is_broadside:
                if current_game_time - tower.last_attack_time >= effective_interval:
                    print(f"DEBUG: Broadside tower {tower.tower_id} firing based on interval.")
                    grid_offset_x = config.UI_PANEL_PADDING
                    grid_offset_y = config.UI_PANEL_PADDING
                    # Capture and process results for broadside
                    # Pass self.towers for potential adjacency checks within attack
                    attack_results = tower.attack(None, current_game_time, self.enemies, self.tower_buff_auras, grid_offset_x, grid_offset_y, all_towers=self.towers) 
                    if isinstance(attack_results, dict):
                        new_projectiles = attack_results.get('projectiles', [])
                        if new_projectiles:
                            self.projectiles.extend(new_projectiles)
                            print(f"Added {len(new_projectiles)} broadside projectiles.")
                        new_effects = attack_results.get('effects', [])
                        if new_effects:
                            self.effects.extend(new_effects)
                    # Attack method updates last_attack_time internally now
            
            # --- Standard Attack Targeting Logic (Skip if Broadside handled above) ---
            elif not is_broadside:
                # --- 1. Find Potential Targets ---
                potential_targets = []
                for enemy in self.enemies: # Indentation Level 1 (12 spaces)
                    if enemy.health > 0 and enemy.type in tower.targets:
                        if tower.target_armor_type and enemy.armor_type not in tower.target_armor_type:
                            continue
                        if tower.is_in_range(enemy.x, enemy.y):
                            potential_targets.append(enemy)

                # --- Select Actual Target(s) ---
                actual_targets = []
                target_selection_mode = tower.tower_data.get("target_selection", "closest")

                if tower.attack_type == 'beam': # Indentation Level 2 (16 spaces)
                    potential_targets.sort(key=lambda e: (e.x - tower.x)**2 + (e.y - tower.y)**2)
                    actual_targets = potential_targets[:tower.beam_max_targets]
                    tower.beam_targets = actual_targets
                    current_primary_target = actual_targets[0] if actual_targets else None

                    # --- START Beam Sound Management ---
                    if tower.attack_sound: # Only manage if sound exists
                        if tower.beam_targets: # Beam is active (has targets)
                            if not tower.is_beam_sound_playing:
                                try:
                                    tower.attack_sound.play(loops=-1) # Start looping
                                    tower.is_beam_sound_playing = True
                                    print(f"DEBUG: Started looping beam sound for {tower.tower_id}")
                                except pygame.error as e:
                                    print(f"Error playing beam sound for {tower.tower_id}: {e}")
                        else: # Beam is inactive (no targets)
                            if tower.is_beam_sound_playing:
                                tower.attack_sound.stop()
                                tower.is_beam_sound_playing = False
                                print(f"DEBUG: Stopped looping beam sound for {tower.tower_id}")
                    # --- END Beam Sound Management ---

                    # --- Laser Painter Target Tracking ---
                    is_painter = tower.special and tower.special.get('effect') == 'laser_painter'
                    if is_painter: # Indentation Level 3 (20 spaces)
                        if current_primary_target != tower.painting_target:
                            # Target changed or lost
                            if current_primary_target: # Indentation Level 4 (24 spaces)
                                print(f"Laser Painter {tower.tower_id} started painting {current_primary_target.enemy_id}")
                                tower.paint_start_time = current_game_time # Reset timer for new target
                            else:
                                # print(f"Laser Painter {tower.tower_id} lost target.") # Optional debug
                                tower.paint_start_time = 0.0 # No target, reset time
                            tower.painting_target = current_primary_target # Update target (to new one or None)
                        # else: Target is the same, do nothing - timer continues
                    else:
                        # Ensure state is reset if it's NOT a painter
                        tower.painting_target = None
                        tower.paint_start_time = 0.0
                    # --- End Laser Painter Tracking ---

                    # --- Flamethrower Effect Management ---
                    if tower.tower_id == 'pyro_pyromaniac': # Indentation Level 3 (20 spaces) - ALIGNED WITH is_painter check
                        target_for_effect = tower.beam_targets[0] if tower.beam_targets else None # Get target from stored list
                        if target_for_effect and not tower.active_flame_effect: # Indentation Level 4 (24 spaces)
                            # Start new effect
                            print(f"Pyromaniac starting flame effect on {target_for_effect.enemy_id}")
                            flame_effect = FlamethrowerParticleEffect(tower, target_for_effect)
                            self.effects.append(flame_effect)
                            tower.active_flame_effect = flame_effect
                        elif not target_for_effect and tower.active_flame_effect:
                            # Target lost, stop spawning
                            print(f"Pyromaniac lost target, stopping flame effect spawning.")
                            tower.active_flame_effect.stop_spawning()
                            tower.active_flame_effect = None # Remove reference
                        elif target_for_effect and tower.active_flame_effect and \
                             target_for_effect != tower.active_flame_effect.target_enemy:
                            # Target changed, stop old effect, start new one
                            print(f"Pyromaniac changed target, restarting flame effect on {target_for_effect.enemy_id}")
                            tower.active_flame_effect.stop_spawning() # Stop old one
                            flame_effect = FlamethrowerParticleEffect(tower, target_for_effect) # Start new one
                            self.effects.append(flame_effect)
                            tower.active_flame_effect = flame_effect
                    # --- End Flamethrower Management ---

                    # --- Acid Spew Effect Management ---
                    elif tower.tower_id == 'zork_slime_spewer': # CORRECTED TOWER ID
                        # Initialize acid effect attribute if missing
                        if not hasattr(tower, 'active_acid_effect'): # Indentation Level 4 (24 spaces)
                            tower.active_acid_effect = None
                            
                        target_for_effect = tower.beam_targets[0] if tower.beam_targets else None # Get target from stored list
                        if target_for_effect and not tower.active_acid_effect:
                            # Start new effect
                            print(f"Acid Spewer starting effect on {target_for_effect.enemy_id}")
                            acid_effect = AcidSpewParticleEffect(tower, target_for_effect)
                            self.effects.append(acid_effect)
                            tower.active_acid_effect = acid_effect
                        elif not target_for_effect and tower.active_acid_effect:
                            # Target lost, stop spawning
                            print(f"Acid Spewer lost target, stopping effect spawning.")
                            tower.active_acid_effect.stop_spawning()
                            tower.active_acid_effect = None # Remove reference
                        elif target_for_effect and tower.active_acid_effect and \
                             target_for_effect != tower.active_acid_effect.target_enemy:
                            # Target changed, stop old effect, start new one
                            print(f"Acid Spewer changed target, restarting effect on {target_for_effect.enemy_id}")
                            tower.active_acid_effect.stop_spawning() # Stop old one
                            acid_effect = AcidSpewParticleEffect(tower, target_for_effect) # Start new one
                            self.effects.append(acid_effect)
                            tower.active_acid_effect = acid_effect
                    # --- End Acid Spew Management ---

                    # --- NEW: Drain Particle Effect Management (Husk Void Leecher) ---
                    elif tower.tower_id == 'husk_void_leecher':
                        # Ensure the attribute exists (safe check)
                        if not hasattr(tower, 'active_drain_effect'):
                            tower.active_drain_effect = None
                            
                        target_for_effect = tower.beam_targets[0] if tower.beam_targets else None
                        
                        if target_for_effect and not tower.active_drain_effect:
                            # Start new drain effect
                            print(f"Void Leecher starting drain effect from {target_for_effect.enemy_id}")
                            drain_effect = DrainParticleEffect(tower, target_for_effect)
                            self.effects.append(drain_effect)
                            tower.active_drain_effect = drain_effect
                        elif not target_for_effect and tower.active_drain_effect:
                            # Target lost, stop spawning drain particles
                            print(f"Void Leecher lost target, stopping drain effect spawning.")
                            tower.active_drain_effect.stop_spawning()
                            tower.active_drain_effect = None # Remove reference
                        elif target_for_effect and tower.active_drain_effect and \
                             target_for_effect != tower.active_drain_effect.target_enemy:
                            # Target changed, stop old drain effect, start new one
                            print(f"Void Leecher changed target, restarting drain effect from {target_for_effect.enemy_id}")
                            tower.active_drain_effect.stop_spawning() # Stop old one
                            drain_effect = DrainParticleEffect(tower, target_for_effect) # Start new one
                            self.effects.append(drain_effect)
                            tower.active_drain_effect = drain_effect
                    # --- END Drain Particle Effect Management ---
                    
                    # --- NEW: Apply Beam Effects (Damage & Slow) --- 
                    # Check adjacency requirements first
                    proceed_with_beam_effects = True
                    if tower.special and tower.special.get("effect") == "requires_solar_adjacency":
                        required_count = tower.special.get("required_count", 3)
                        race_to_check = tower.special.get("race_to_check", "solar")
                        # Assuming self.towers is accessible here
                        adjacent_count = tower.count_adjacent_race_towers(self.towers, race_to_check)
                        if adjacent_count < required_count:
                            proceed_with_beam_effects = False
                            
                    if proceed_with_beam_effects:
                        # Apply effects if interval allows (mimics the damage logic interval)
                        if current_game_time >= tower.last_attack_time + effective_interval:
                            effects_applied_this_tick = False # Flag to update attack time once
                            for target_enemy in tower.beam_targets:
                                if target_enemy.health > 0:
                                    # --- Apply Damage (Logic moved from draw) ---
                                    # Check if painter and charged
                                    apply_damage_now = False
                                    if is_painter:
                                        if target_enemy == tower.painting_target and tower.paint_start_time > 0 and \
                                           (current_game_time - tower.paint_start_time >= tower.special.get('charge_duration', 2.0)):
                                            apply_damage_now = True
                                            tower.paint_start_time = 0.0 # Reset charge
                                    else:
                                        apply_damage_now = True # Non-painters apply damage based on interval
                                        
                                    if apply_damage_now:
                                        dmg_min, dmg_max, _ = tower.get_stats_for_target(target_enemy.type)
                                        # <<< FIX: Get damage_multiplier from buffed_stats >>>
                                        current_damage_multiplier = buffed_stats.get('damage_multiplier', 1.0)
                                        damage = random.uniform(dmg_min, dmg_max) * current_damage_multiplier # Use the retrieved multiplier
                                        target_enemy.take_damage(damage, tower.damage_type)
                                        print(f"Beam tower {tower.tower_id} dealt {damage:.2f} {tower.damage_type} damage to {target_enemy.enemy_id}")
                                        effects_applied_this_tick = True
                                    # --- End Apply Damage ---
                                    
                                    # --- Apply Slow Effect --- 
                                    if tower.special and tower.special.get('effect') == 'slow':
                                        slow_percentage = tower.special.get('slow_percentage', 0)
                                        if slow_percentage > 0:
                                            slow_multiplier = 1.0 - (slow_percentage / 100.0)
                                            # <<< FIX: Use a small fixed duration instead of time_delta >>>
                                            fixed_slow_duration = 0.2 # Apply slow for 0.2 seconds each frame beam hits
                                            target_enemy.apply_status_effect('slow', fixed_slow_duration, slow_multiplier, current_game_time)
                                            # print(f"DEBUG: Freeze ray applying slow {slow_percentage}% to {target_enemy.enemy_id}") # Optional Debug
                                            effects_applied_this_tick = True
                                    # --- End Apply Slow --- 
                                    
                                    # Add other beam effects here (e.g., DoTs if beams can apply them per tick)
                            
                            # Update last attack time ONCE if any effect/damage was applied this tick
                            if effects_applied_this_tick:
                                tower.last_attack_time = current_game_time

                elif potential_targets: # Indentation Level 2 (16 spaces) - Aligned with 'if tower.attack_type == beam:'
                    if target_selection_mode == "random":
                        actual_targets = [random.choice(potential_targets)]
                    else:
                        potential_targets.sort(key=lambda e: (e.x - tower.x)**2 + (e.y - tower.y)**2)
                        actual_targets = [potential_targets[0]]
                    # --- Store target for drawing even if not a beam ---
                    tower.beam_targets = actual_targets # NEW: Store selected target(s)

                    # --- Ensure other particle effects are cleared if tower type doesn't match ---
                    # Clear flamethrower if not pyromaniac
                    if tower.active_flame_effect and tower.tower_id != 'pyro_pyromaniac':
                        tower.active_flame_effect.stop_spawning()
                        tower.active_flame_effect = None
                    # Clear acid spew if not acid spewer
                    if hasattr(tower, 'active_acid_effect') and tower.active_acid_effect and tower.tower_id != 'zork_slime_spewer': # CORRECTED TOWER ID
                        tower.active_acid_effect.stop_spawning()
                        tower.active_acid_effect = None
                    # Clear drain effect if not void leecher
                    if hasattr(tower, 'active_drain_effect') and tower.active_drain_effect and tower.tower_id != 'husk_void_leecher':
                        tower.active_drain_effect.stop_spawning()
                        tower.active_drain_effect = None
                    # ------------------------------------------------------------------------

                    # --- Attack Check and Execution for Standard/Special Towers ---
                    # Check if interval is ready AND either targets were found OR it's a specific effect tower that needs to act
                    interval_ready = current_game_time >= tower.last_attack_time + effective_interval
                    is_marking_tower = tower.special and tower.special.get("effect") == "apply_mark"
                    
                    if interval_ready and (actual_targets or is_marking_tower):
                        target_enemy = actual_targets[0] if actual_targets else None # Get target if available, else None

                        grid_offset_x = config.UI_PANEL_PADDING
                        grid_offset_y = config.UI_PANEL_PADDING

                        # --- Specific Handling for Tower Chain --- 
                        if tower.tower_id == 'spark_arc_tower':
                            # Call the specific chain zap attempt logic
                            # This function handles its own cooldowns and results
                            self.attempt_chain_zap(tower, current_game_time, self.enemies, grid_offset_x, grid_offset_y)
                            # We might not need to process results further here if attempt_chain_zap handles effects/sounds
                        else:
                            # --- Generic Attack Call for other non-beam/non-chain towers ---
                            # --- Prepare Visual Assets --- 
                            visual_assets = {}
                            # ... (Rest of the visual asset preparation logic remains the same) ...
                            if hasattr(tower, 'animations') and tower.animations:
                                # ... (animation loading logic) ...
                                direction_suffix = tower.current_direction_str if hasattr(tower, 'current_direction_str') else 'down'
                                idle_key = f"idle_{direction_suffix}"
                                attack_key = f"attack_{direction_suffix}"
                                visual_assets['idle_surface_list'] = tower.animations.get(idle_key, [])
                                visual_assets['attack_surface_list'] = tower.animations.get(attack_key, tower.animations.get(idle_key, []))
                                if not visual_assets['idle_surface_list'] and tower.image:
                                    visual_assets['idle_surface_list'] = [tower.image]
                                if not visual_assets['attack_surface_list']:
                                    visual_assets['attack_surface_list'] = visual_assets['idle_surface_list']
                            else:
                                if hasattr(tower, 'image') and tower.image:
                                    visual_assets['idle_surface_list'] = [tower.image]
                                else:
                                    visual_assets['idle_surface_list'] = []
                                visual_assets['attack_surface_list'] = visual_assets['idle_surface_list']

                            visual_assets['projectile_surface'] = getattr(tower, 'projectile_image_override', None) or getattr(tower, 'projectile_surface', None)
                            visual_assets['projectile_animation_frames'] = getattr(tower, 'projectile_animation_frames', [])
                            visual_assets['projectile_animation_speed'] = getattr(tower, 'projectile_animation_speed', 0.1)
                            # --- End Prepare Visual Assets ---

                            # Call the tower's generic attack method
                            # Pass target_enemy (which might be None if it's a marking tower with no targets in range, but attack handles that)
                            attack_results = tower.attack(
                                target_enemy, 
                                current_game_time,
                                self.enemies,           # Pass all enemies
                                self.tower_buff_auras,  # Pass buffs
                                grid_offset_x,
                                grid_offset_y,
                                visual_assets=visual_assets, # Pass the visuals
                                all_towers=self.towers      # Pass all towers
                            )

                            # --- Process Generic Attack Results ---
                            self.process_attack_results(attack_results, grid_offset_x, grid_offset_y)
                            # --- End Processing ---
                    # --- End Attack Check ---

        # --- Process Pulsed Auras (Affecting Enemies) ---
        for aura_data in enemy_aura_towers: 
            tower = aura_data['tower']
            special = aura_data['special']
            effect_type = special.get('effect')

            # Check if this aura is a pulsed type
            if effect_type and effect_type.endswith('_pulse_aura'):
                interval = special.get('interval', 1.0)
                # Check pulse timing ONCE per tower
                if current_game_time - tower.last_pulse_time >= interval:
                  
                    tower.last_pulse_time = current_game_time # Update time immediately
                    radius_sq = aura_data['radius_sq']
                    allowed_targets = special.get('targets', [])
                   
                    # --- Create Visual Pulse Effect --- 
                    if tower.tower_id == 'alchemists_miasma_pillar': # <<< CORRECTED TYPO HERE
                       
                        try:
                            # Import math if not already imported at the top
                            import math 
                            pulse_radius_pixels = math.sqrt(radius_sq)
                            pulse_color = (0, 255, 0, 100) # Faint green (RGBA)
                            pulse_duration = 0.5 # seconds
                            pulse_effect = ExpandingCircleEffect(tower.x, tower.y, 
                                                                 pulse_radius_pixels, 
                                                                 pulse_duration, 
                                                                 pulse_color, thickness=2)
                            self.effects.append(pulse_effect)
                    
                        except NameError: # Catch if ExpandingCircleEffect wasn't imported
                            print("ERROR: ExpandingCircleEffect class not found. Please ensure it's defined and imported.")
                        except Exception as e:
                            print(f"Error creating Miasma Pillar pulse effect: {e}")
                    # --- Other Pulse Visuals (e.g., Glacial Heart) ---

                    # Now find and affect ALL valid enemies in range
                    for enemy in self.enemies: # Iterate through all current enemies
                        # --- DEBUG: Target Type & Range Pre-check ---
                        if tower.tower_id == 'igloo_glacial_heart' and enemy.enemy_id == 'doomlord': # Log only for relevant combo
                            print(f"??? Pulse Check for {tower.tower_id} on {enemy.enemy_id}: \
                                  Enemy Type='{enemy.type}', Allowed Types={allowed_targets}, In Type? {enemy.type in allowed_targets}, \
                                  DistSq={ (enemy.x - tower.x)**2 + (enemy.y - tower.y)**2 :.1f}, RadiusSq={radius_sq:.1f}")
                        # --- END DEBUG ---
                        if enemy.health > 0 and enemy.type in allowed_targets:
                            dist_sq = (enemy.x - tower.x)**2 + (enemy.y - tower.y)**2
                            if dist_sq <= radius_sq:
                                # Apply the specific pulse effect
                                if effect_type == 'slow_pulse_aura':
                                    slow_percentage = special.get('slow_percentage', 0)
                                    duration = special.get('duration', 1.0)
                                    multiplier = 1.0 - (slow_percentage / 100.0)
                                    enemy.apply_status_effect('slow', duration, multiplier, current_game_time)
                                    # Optional damage
                                    pulse_damage = special.get('pulse_damage')
                                    if pulse_damage is not None and pulse_damage > 0:
                                        damage_type = special.get('pulse_damage_type', 'normal')
                                        enemy.take_damage(pulse_damage, damage_type)
                                    

                                elif effect_type == 'damage_pulse_aura':
                                    pulse_damage = special.get('pulse_damage', 0)
                                    damage_type = special.get('pulse_damage_type', 'normal')
                                    enemy.take_damage(pulse_damage, damage_type)
                   

                                elif effect_type == 'stun_pulse_aura':
                                    duration = special.get('duration', 0.5)
                                    enemy.apply_status_effect('stun', duration, None, current_game_time)
    
                                
                                # --- NEW: Bonechill Pulse --- 
                                elif effect_type == 'bonechill_pulse_aura':
                                    duration = special.get('bonechill_duration', 3.0) # Get duration from JSON, default 3s
                                    enemy.apply_status_effect('bonechill', duration, None, current_game_time)
                                    # --- ADDED BONECHILL APPLICATION LOG ---
                                    print(f"$$$ BONECHILL APPLIED by {tower.tower_id} to {enemy.enemy_id} for {duration}s at {current_game_time:.2f}s")
                                    # --- END LOG ---

                                # --- End Bonechill Pulse --- 

                                # --- NEW: DoT Pulse Aura --- 
                                elif effect_type == 'dot_pulse_aura':
                                    dot_name = special.get('dot_effect_name', 'unnamed_dot')
                                    base_dot_damage = special.get('dot_damage', 0)
                                    dot_interval = special.get('dot_interval', 1.0)
                                    dot_duration = special.get('dot_duration', 1.0)
                                    dot_damage_type = special.get('dot_damage_type', 'normal')
                                    
                                    # Get amplification from nearby Plague Reactors
                                    amp_multiplier = tower.get_dot_amplification_multiplier(self.tower_buff_auras)
                                    amplified_dot_damage = base_dot_damage * amp_multiplier
                                    
                                    # Apply the DoT to the enemy
                                    enemy.apply_dot_effect(dot_name, amplified_dot_damage, dot_interval, dot_duration, dot_damage_type, current_game_time)

                                   
                                # --- End DoT Pulse Aura ---

        # --- Update Projectiles --- 
        newly_created_projectiles = [] # List to hold projectiles from bounces/splits etc.
        newly_created_effects = [] # List to hold effects from impacts
        
        for proj in self.projectiles[:]:
            # --- CHECK IF BOOMERANG ---
            is_boomerang = type(proj).__name__ == 'OffsetBoomerangProjectile' # Dynamic check

            if is_boomerang:
                # --- Update Boomerang (which manages its own 'finished' state) ---
                proj.update(time_delta, self.enemies) # Boomerang update handles collisions and state changes internally
                if proj.finished:
                    try:
                        self.projectiles.remove(proj)
                        # print("Boomerang finished, removed.") # Optional DEBUG
                    except ValueError:
                        print("Warning: Tried to remove finished boomerang that was already removed?")
            else:
                # --- Existing Logic for Standard Projectiles ---
                proj.move(time_delta, self.enemies) 
                if proj.collided:
                    # on_collision now returns a dictionary with new projectiles/effects/gold
                    collision_results = proj.on_collision(self.enemies, current_game_time, self.tower_buff_auras)
                    
                    if collision_results:
                        # Check for and add gold
                        gold_to_add = collision_results.get('gold_added', 0)
                        if gold_to_add > 0:
                            self.money += gold_to_add
                            self.tower_selector.update_money(self.money)
                            # Optional: Create floating text effect for gold gain
                            try:
                                grid_offset_x = config.UI_PANEL_PADDING
                                grid_offset_y = config.UI_PANEL_PADDING
                                # Use projectile position BEFORE removal
                                text_x = proj.x + grid_offset_x 
                                text_y = proj.y + grid_offset_y 
                                gold_text = f"+{gold_to_add} G"
                                gold_color = (255, 215, 0) # Gold color
                                text_effect = FloatingTextEffect(text_x, text_y, gold_text, color=gold_color, font_size=18)
                                self.effects.append(text_effect)
                            except Exception as e:
                                print(f"Error creating gold text effect: {e}")
                                
                        # Add any new projectiles (e.g., from bounce)
                        new_projs = collision_results.get('new_projectiles', [])
                        if new_projs:
                            newly_created_projectiles.extend(new_projs)
                        
                        
                        # Add any new effects (e.g., fallout zone)
                        new_effects = collision_results.get('new_effects', [])
                        if new_effects:
                            newly_created_effects.extend(new_effects)
                        
                    
                    # Always remove the original projectile after collision is processed
                    try:
                        self.projectiles.remove(proj)
                    except ValueError:
                        # Keep this block aligned with try
                        print(f"Warning: Tried to remove projectile that was already removed?") 
                        
        # Add any newly created items to the main lists AFTER iterating
        if newly_created_projectiles:
            self.projectiles.extend(newly_created_projectiles)
            # print(f"Added {len(newly_created_projectiles)} new projectiles to main list.")
        if newly_created_effects:
            self.effects.extend(newly_created_effects)
            # print(f"Added {len(newly_created_effects)} new effects to main list.")

        # --- Update Orbiting Damagers --- 
        # Need to get current time again or pass it down
        current_time_seconds = pygame.time.get_ticks() / 1000.0
        for tower in self.towers:
            for orb in tower.orbiters[:]: # Use slice copy for potential removal
                if orb.update(time_delta, self.enemies, current_time_seconds):
                    # If update returns True (e.g., lifetime expired), remove
                    # tower.orbiters.remove(orb) 
                    pass # No removal logic yet
        # --- End Orbiter Update ---

        # --- Update Pass-Through Exploders --- 
        for exploder in self.pass_through_exploders[:]: # Use slice copy for safe removal
            should_remove, new_effect = exploder.update(time_delta, self.enemies, current_time_seconds)
            if new_effect:
                # Need to adjust position by offset before adding to scene effects
                grid_offset_x = config.UI_PANEL_PADDING
                grid_offset_y = config.UI_PANEL_PADDING
                # Assuming the effect stores its world coords (x,y) and needs offset for drawing
                # If the Effect class handles offsets itself, this might not be needed
                # For now, let's assume we add it as is, and Effect's draw handles offset
                # OR, we adjust the Effect's position here. Let's try adding as is.
                if hasattr(new_effect, 'x') and hasattr(new_effect, 'y'): # Check if effect has position
                     # We might need to adjust the coordinates if Effect expects screen coords
                     # new_effect.x += grid_offset_x 
                     # new_effect.y += grid_offset_y
                     pass # Add effect as is for now
                self.effects.append(new_effect) # Add the visual effect to the main list
            if should_remove:
                # update returns True when max distance is reached and explosion is done
                self.pass_through_exploders.remove(exploder)
        # --- End Pass-Through Exploder Update ---

        # --- Update GROUND Effects (Like Fallout Zone) --- 
        for ground_effect in [ef for ef in self.effects if isinstance(ef, GroundEffectZone)][:]:
             if ground_effect.update(time_delta, self.enemies):
                 try:
                     self.effects.remove(ground_effect)
                 except ValueError:
                     pass # Already removed?
        # --- End Ground Effects ---

        # --- Update Standard Effects --- 
        for effect in [ef for ef in self.effects if not isinstance(ef, GroundEffectZone)][:]:
            if isinstance(effect, FlamethrowerParticleEffect):
                # Flamethrower effect update doesn't return True/False for finish status yet
                # It sets self.finished internally
                effect.update(time_delta)
                if effect.finished:
                    try: self.effects.remove(effect) 
                    except ValueError: pass
            elif isinstance(effect, AcidSpewParticleEffect): # Added check for AcidSpew
                effect.update(time_delta)
                if effect.finished:
                    try: self.effects.remove(effect) 
                    except ValueError: pass
            elif isinstance(effect, DrainParticleEffect): # NEW: Check for DrainParticleEffect
                effect.update(time_delta)
                if effect.finished:
                    try: self.effects.remove(effect) 
                    except ValueError: pass
            elif effect.update(time_delta): # Standard effects return True when finished
                try: self.effects.remove(effect)
                except ValueError: pass
            
        # --- NEW: Apply Enemy Aura Effects --- 
        # Reset aura effects on all enemies first
        for enemy in self.enemies:
            enemy.aura_armor_reduction = 0
            # Reset other potential enemy aura effects here
        
        # Find towers with enemy-affecting auras
        enemy_aura_towers_to_process = [t for t in self.towers if t.special and t.special.get("targets") and ("enemies" in t.special.get("targets") or "ground" in t.special.get("targets") or "air" in t.special.get("targets")) and t.special.get("effect") == "enemy_armor_reduction_aura"]
        
        # Apply effects
        for aura_tower in enemy_aura_towers_to_process:
            reduction_amount = aura_tower.special.get("reduction_amount", 0)
            if reduction_amount > 0:
                aura_radius_sq = aura_tower.aura_radius_pixels ** 2
                for enemy in self.enemies:
                    if enemy.health > 0:
                        dist_sq = (enemy.x - aura_tower.x)**2 + (enemy.y - aura_tower.y)**2
                        if dist_sq <= aura_radius_sq:
                            # Apply the reduction - use max if multiple auras could stack, or just set if non-stacking
                            enemy.aura_armor_reduction = max(enemy.aura_armor_reduction, reduction_amount)
                            # print(f"DEBUG: Applied aura reduction {reduction_amount} from {aura_tower.tower_id} to {enemy.enemy_id}. Current total: {enemy.aura_armor_reduction}") # Optional Debug
        # --- END Enemy Aura Effects ---
        
        # --- Update Enemies (Main Loop) --- 
        for enemy in self.enemies[:]:
            # --- Apply Continuous Auras (Affecting Enemies) --- 
            if enemy.health > 0:
                # Ensure this loop uses enemy_aura_towers
                for aura_data in enemy_aura_towers:
                    tower = aura_data['tower']
                    special = aura_data['special']
                    radius_sq = aura_data['radius_sq']
                    effect_type = special.get('effect')

                    # Skip pulsed auras (handled above)
                    if effect_type and effect_type.endswith('_pulse_aura'):
                        continue 
                    
                    # Check distance
                    dist_sq = (enemy.x - tower.x)**2 + (enemy.y - tower.y)**2
                    if dist_sq <= radius_sq:
                        allowed_targets = special.get('targets', []) 
                        if enemy.type in allowed_targets:
                            # Handle Continuous Auras 
                            if effect_type == 'damage_aura':
                                dot_damage = special.get('dot_damage', 0)
                                dot_interval = special.get('dot_interval', 1.0)
                                if dot_interval > 0:
                                    damage_per_sec = dot_damage / dot_interval
                                    damage_this_frame = damage_per_sec * time_delta
                                    damage_type = special.get('dot_damage_type', 'normal')
                                    enemy.take_damage(damage_this_frame, damage_type)
                                    
                            elif effect_type == 'slow_aura':
                                slow_percentage = special.get('slow_percentage', 0)
                                multiplier = 1.0 - (slow_percentage / 100.0)
                                enemy.apply_status_effect('slow', time_delta * 1.5, multiplier, current_game_time)
                                
                            elif effect_type == 'storm_aura': # Added check for storm_aura
                                # Apply Damage Component
                                dot_damage = special.get('dot_damage', 0)
                                dot_interval = special.get('dot_interval', 1.0)
                                if dot_interval > 0:
                                    damage_per_sec = dot_damage / dot_interval
                                    damage_this_frame = damage_per_sec * time_delta
                                    damage_type = special.get('dot_damage_type', 'arcane') # Default to arcane for storm?
                                    enemy.take_damage(damage_this_frame, damage_type)
                                # Apply Slow Component
                                slow_percentage = special.get('slow_percentage', 0)
                                if slow_percentage > 0:
                                    multiplier = 1.0 - (slow_percentage / 100.0)
                                    enemy.apply_status_effect('slow', time_delta * 1.5, multiplier, current_game_time)

            # --- Move Enemy --- 
            # Enemy.move() handles status updates internally
            enemy.move(current_game_time)
            
            # --- Check for Walkover Tower Trigger --- 
            if enemy.health > 0:
                current_grid_x = int(enemy.x // config.GRID_SIZE)
                current_grid_y = int(enemy.y // config.GRID_SIZE)
                
                for tower in self.towers:
                    # Check if tower triggers on walkover and enemy is on its tile
                    # Assumes walkover towers are 1x1 for simplicity now
                    if tower.tower_data.get("trigger_on_walkover", False) and \
                       tower.top_left_grid_x == current_grid_x and \
                       tower.top_left_grid_y == current_grid_y:
                           
                       # Check if enemy type is a valid target
                       if enemy.type in tower.targets:
                            # Apply the special effect (e.g., burn DoT)
                            if tower.special:
                                effect_type = tower.special.get("effect")
                                if effect_type == "burn":
                                    base_dot_damage = tower.special.get("dot_damage", 0)
                                    dot_interval = tower.special.get("dot_interval", 1.0)
                                    dot_duration = tower.special.get("dot_duration", 1.0)
                                    dot_damage_type = tower.special.get("dot_damage_type", tower.damage_type)
                                    # Get amplification
                                    amp_multiplier = tower.get_dot_amplification_multiplier(self.tower_buff_auras)
                                    amplified_dot_damage = base_dot_damage * amp_multiplier
                                    # Apply the burn DoT
                                    enemy.apply_dot_effect(effect_type, amplified_dot_damage, dot_interval, dot_duration, dot_damage_type, current_game_time)
                                    print(f"Enemy {enemy.enemy_id} walked over Fire Pit {tower.tower_id}, applied burn.")
                                # --- Add check for Earth Spine --- 
                                elif effect_type == "ground_spike_dot":
                                    base_dot_damage = tower.special.get("dot_damage", 0)
                                    dot_interval = tower.special.get("dot_interval", 1.0)
                                    dot_duration = tower.special.get("dot_duration", 1.0)
                                    dot_damage_type = tower.special.get("dot_damage_type", tower.damage_type)
                                    # Get amplification
                                    amp_multiplier = tower.get_dot_amplification_multiplier(self.tower_buff_auras)
                                    amplified_dot_damage = base_dot_damage * amp_multiplier
                                    # Apply the spike DoT
                                    enemy.apply_dot_effect(effect_type, amplified_dot_damage, dot_interval, dot_duration, dot_damage_type, current_game_time)
                                    print(f"Enemy {enemy.enemy_id} walked over Earth Spine {tower.tower_id}, applied {effect_type}.")
                                # Add other walkover effects here if needed (e.g., instant damage)
                                # elif effect_type == "walkover_damage": ... 
                                break # Stop checking towers for this enemy once triggered
            # --- End Walkover Check --- 

            # --- Objective check --- 
            if enemy.path_index >= len(enemy.grid_path):
                self.lives -= 1
                print(f"*** OBJECTIVE REACHED by {enemy.enemy_id}. Decrementing wave counter from {self.enemies_alive_this_wave}...") # DEBUG
                if self.enemies_alive_this_wave > 0: self.enemies_alive_this_wave -= 1 
                self.enemies.remove(enemy)
                print(f"Enemy reached objective. Lives remaining: {self.lives}")
                print(f"  Enemies left this wave NOW: {self.enemies_alive_this_wave}") # DEBUG
                if self.lives <= 0:
                    print("Game Over!")
                    # TODO: Handle game over state
                    continue # Skip death check if already removed
        
        # --- Remove dead enemies --- 
        # Check remaining enemies for death AFTER objective check
        for enemy in self.enemies[:]: 
            if enemy.health <= 0: # Check health AFTER objective check

                # <<< PLAY DEATH SOUND >>>
                if self.death_sound:
                    self.death_sound.play()
                # <<< END PLAY DEATH SOUND >>>

                # Create blood splatter effect at enemy's current position
                # Need to adjust for grid offset to get absolute screen coords
                grid_offset_x = config.UI_PANEL_PADDING
                grid_offset_y = config.UI_PANEL_PADDING
                effect_x = enemy.x + grid_offset_x 
                effect_y = enemy.y + grid_offset_y
                

                
                # if self.blood_splatter_frames: # Only create if frames loaded (Old check)
                if self.blood_splatter_base_image: # Check if base image loaded

                    # Create a fading effect instead of frame-based
                    splatter = Effect(effect_x, effect_y, 
                                      self.blood_splatter_base_image, # Pass base image
                                      config.BLOOD_SPLATTER_FADE_DURATION, # Pass fade duration
                                      (config.GRID_SIZE * 3, config.GRID_SIZE * 3), # Pass target size (3x3 grid cells)
                                      hold_duration=config.BLOOD_SPLATTER_HOLD_DURATION) # Pass hold duration
                    self.effects.append(splatter)

                    
                # TODO: Add money/score for killing enemy?
                self.money += enemy.value # Add enemy value to player money
                self.tower_selector.update_money(self.money) # UPDATE UI DISPLAY
                print(f"*** ENEMY KILLED: {enemy.enemy_id}. Decrementing wave counter from {self.enemies_alive_this_wave}...") # DEBUG
                if self.enemies_alive_this_wave > 0: self.enemies_alive_this_wave -= 1 
                self.enemies.remove(enemy)
                print(f"Enemy {enemy.enemy_id} defeated. Gained ${enemy.value}. Current Money: ${self.money}")
                print(f"  Enemies left this wave NOW: {self.enemies_alive_this_wave}") # DEBUG
            
    def draw(self, screen, time_delta, current_game_time):
        """Draw the game scene with new layout"""
        # Fill background - Cover the whole screen first
        screen.fill((0, 0, 0)) # Black background
        
        # --- Draw Lives Display (Removed from here) --- 
        
        # Draw grid background 
        grid_bg_surface = pygame.Surface((self.usable_grid_pixel_width, self.usable_grid_pixel_height))
        if self.grid_background_texture:
            grid_bg_surface.blit(self.grid_background_texture, (0, 0))
        else:
            grid_bg_surface.fill((20, 20, 20)) # Fallback dark background
        
        # Draw restricted side columns overlay
        restricted_col_color = (40, 40, 40, 200) # Darker gray, more opaque
        restricted_outline_color = (180, 180, 180) # Light gray outline
        restricted_surface = pygame.Surface((self.usable_grid_pixel_width, self.usable_grid_pixel_height), pygame.SRCALPHA)
        
        # Top restricted area fill and outline
        top_rect = pygame.Rect(0, 0, self.usable_grid_pixel_width, config.RESTRICTED_TOWER_AREA_HEIGHT * config.GRID_SIZE)
        pygame.draw.rect(restricted_surface, restricted_col_color, top_rect)
        pygame.draw.rect(restricted_surface, restricted_outline_color, top_rect, 2) # Add outline

        # Bottom restricted area fill and outline
        # Calculate starting Y based on grid index to ensure alignment
        bottom_restricted_start_y_grid = self.grid_height - config.RESTRICTED_TOWER_AREA_HEIGHT
        bottom_restricted_start_y_pixel = bottom_restricted_start_y_grid * config.GRID_SIZE
        bottom_rect = pygame.Rect(0, bottom_restricted_start_y_pixel, 
                                self.usable_grid_pixel_width, config.RESTRICTED_TOWER_AREA_HEIGHT * config.GRID_SIZE)
        pygame.draw.rect(restricted_surface, restricted_col_color, bottom_rect)
        pygame.draw.rect(restricted_surface, restricted_outline_color, bottom_rect, 2) # Add outline
        
        # Left restricted area fill and outline
        left_rect = pygame.Rect(0, 0, config.RESTRICTED_TOWER_AREA_WIDTH * config.GRID_SIZE, self.usable_grid_pixel_height)
        pygame.draw.rect(restricted_surface, restricted_col_color, left_rect)
        pygame.draw.rect(restricted_surface, restricted_outline_color, left_rect, 2) # Add outline
        
        # Right restricted area fill and outline
        right_rect = pygame.Rect(self.usable_grid_pixel_width - config.RESTRICTED_TOWER_AREA_WIDTH * config.GRID_SIZE, 0, config.RESTRICTED_TOWER_AREA_WIDTH * config.GRID_SIZE, self.usable_grid_pixel_height)
        pygame.draw.rect(restricted_surface, restricted_col_color, right_rect)
        pygame.draw.rect(restricted_surface, restricted_outline_color, right_rect, 2) # Add outline
        
        grid_bg_surface.blit(restricted_surface, (0, 0))

        # Draw grid lines (on grid_bg_surface)
        for x_line in range(0, self.usable_grid_pixel_width + 1, config.GRID_SIZE):
            pygame.draw.line(grid_bg_surface, (80, 80, 80), (x_line, 0), (x_line, self.usable_grid_pixel_height))
        for y_line in range(0, self.usable_grid_pixel_height + 1, config.GRID_SIZE):
            pygame.draw.line(grid_bg_surface, (80, 80, 80), (0, y_line), (self.usable_grid_pixel_width, y_line))
            
        # Blit the completed grid surface onto the main screen at top-left
        screen.blit(grid_bg_surface, (config.UI_PANEL_PADDING, config.UI_PANEL_PADDING)) # Add top/left padding

        # --- Draw Spawn and Objective Areas (AFTER grid background is blitted) ---
        # Draw spawn area
        spawn_outline_color = (100, 255, 100) # Light green outline
        spawn_surface = pygame.Surface((self.spawn_area_rect.width, self.spawn_area_rect.height))
        spawn_surface.fill(config.SPAWN_AREA_COLOR) 
        spawn_surface.set_alpha(200)  # Increased opacity
        screen.blit(spawn_surface, self.spawn_area_rect)
        pygame.draw.rect(screen, spawn_outline_color, self.spawn_area_rect, 2) # Add outline
        
        # Draw objective area
        objective_outline_color = (255, 100, 100) # Light red outline
        objective_surface = pygame.Surface((self.objective_area_rect.width, self.objective_area_rect.height))
        objective_surface.fill(config.OBJECTIVE_AREA_COLOR)
        objective_surface.set_alpha(200)  # Increased opacity
        screen.blit(objective_surface, self.objective_area_rect)
        pygame.draw.rect(screen, objective_outline_color, self.objective_area_rect, 2) # Add outline
        # --- End Spawn/Objective Drawing ---

        # Draw towers (coordinates are relative to grid, need offset)
        grid_offset_x = config.UI_PANEL_PADDING
        grid_offset_y = config.UI_PANEL_PADDING
        for tower in self.towers:
            tower.draw(screen, self.tower_assets, grid_offset_x, grid_offset_y)
            
        # Draw enemies using EnemyAssets
        for enemy in self.enemies:
            enemy.draw(screen, self.enemy_assets, grid_offset_x, grid_offset_y) # Pass enemy_assets and offsets
            
        # Draw projectiles
        for proj in self.projectiles:
            proj.draw(screen, self.projectile_assets, grid_offset_x, grid_offset_y)
            
        # --- Draw Orbiting Damagers --- 
        for tower in self.towers:
            for orb in tower.orbiters:
                # Assuming projectile_assets handles orb visuals via asset_id
                # Pass the projectile_assets manager to the draw method
                orb.draw(screen, self.projectile_assets, grid_offset_x, grid_offset_y)
        # --- End Orbiter Draw ---

        # --- Draw Pass-Through Exploders --- 
        for exploder in self.pass_through_exploders:
            # Assuming projectile_assets handles the visual via asset_id
            exploder.draw(screen, self.projectile_assets, grid_offset_x, grid_offset_y)
        # --- End Pass-Through Exploder Draw --- 
            
        # Draw Active Effects (on top of enemies/projectiles)
        # Draw Ground Effects first, then others
        for effect in self.effects:
            if isinstance(effect, GroundEffectZone):
                effect.draw(screen, grid_offset_x, grid_offset_y) # Pass offsets
            elif isinstance(effect, FlamethrowerParticleEffect):
                effect.draw(screen, grid_offset_x, grid_offset_y) # Pass offsets
            elif isinstance(effect, AcidSpewParticleEffect): # Added check for AcidSpew
                effect.draw(screen, grid_offset_x, grid_offset_y) # Pass offsets
            elif isinstance(effect, DrainParticleEffect): # NEW: Check for DrainParticleEffect
                effect.draw(screen, grid_offset_x, grid_offset_y) # Pass offsets
            elif isinstance(effect, ExpandingCircleEffect): # Handle new effect type
                effect.draw(screen, grid_offset_x, grid_offset_y) # Pass offsets
            elif hasattr(effect, 'draw'):
                effect.draw(screen)
            
        # Draw Active Beams 
        # This is where beam damage/effects per frame should be applied too
        for tower in self.towers:
            # --- Draw Beam Visual Condition --- 
            # Draw if it's a beam OR the specific facet_focuser
            should_draw_beam_visual = False
            if tower.attack_type == 'beam' and tower.beam_targets:
                should_draw_beam_visual = True
            elif tower.tower_id == 'crystal_castle_facet_focuser' and tower.beam_targets:
                 should_draw_beam_visual = True 
                 # Note: Damage/effects for instant towers are handled in tower.attack, not here.
            # --------------------------------
                 
            if should_draw_beam_visual:
                # --- Adjacency Check for Beams (e.g., UltraMirror) --- 
                proceed_with_beam = True # Assume we can proceed unless check fails
                if tower.special and tower.special.get("effect") == "requires_solar_adjacency":
                    required_count = tower.special.get("required_count", 3)
                    race_to_check = tower.special.get("race_to_check", "solar")
                    # We have access to self.towers here in GameScene
                    adjacent_count = tower.count_adjacent_race_towers(self.towers, race_to_check)
                    
                    if adjacent_count < required_count:
                        proceed_with_beam = False # Check failed, do not draw/damage

                        
                if proceed_with_beam: # Only draw/damage if check passed
                    # Indent this entire block
                    start_pos = (int(tower.x + grid_offset_x), int(tower.y + grid_offset_y))
                    
                    # Get beam properties (color, painter info)
                    is_painter = False
                    charge_duration = 0.0
                    slow_percentage = 0 # Can be used by normal slow or painter slow
                    beam_color = tower.tower_data.get('beam_color', config.CYAN) # Default color
                    
                    # --- Try to parse the color from tower_data/special --- 
                    raw_color_value = tower.tower_data.get('beam_color') # Check base data first
                    if tower.special and tower.special.get('beam_color'): # Check special override
                        raw_color_value = tower.special.get('beam_color')
                        
                    parsed_color = None
                    if isinstance(raw_color_value, list) and len(raw_color_value) == 3:
                        try:
                            parsed_color = tuple(int(c) for c in raw_color_value)
                        except (ValueError, TypeError):
                            parsed_color = None # Failed conversion
                    elif isinstance(raw_color_value, str):
                        # Try to lookup color name in config
                        if hasattr(config, raw_color_value):
                            config_color = getattr(config, raw_color_value)
                            # Ensure it's a valid tuple
                            if isinstance(config_color, tuple) and len(config_color) == 3:
                               parsed_color = config_color
                               
                    # Use the parsed color if valid, otherwise keep the default
                    if parsed_color:
                        beam_color = parsed_color
                    # --- End Color Parsing ---

                    if tower.special:
                        effect_type = tower.special.get('effect')
                        if effect_type == 'laser_painter':
                            is_painter = True
                            charge_duration = tower.special.get('charge_duration', 2.0)
                            slow_percentage = tower.special.get('slow_percentage', 0)
                        elif effect_type == 'slow': # Handle normal slow beams
                            slow_percentage = tower.special.get('slow_percentage', 0)
                        
                        # Allow beam color override from special
                        if tower.special.get('beam_color'):
                            try:
                                color_val = tower.special.get('beam_color')
                                if isinstance(color_val, list) and len(color_val) == 3:
                                    beam_color = tuple(color_val)
                            except Exception: pass # Ignore parsing errors

                    # Iterate through all targets the beam is visually hitting this frame
                    for target_enemy in tower.beam_targets:
                        if target_enemy.health > 0: # Only draw/affect live targets
                            end_pos = (int(target_enemy.x + grid_offset_x), int(target_enemy.y + grid_offset_y))
                            
                            # --- Draw Main Beam Visual --- 
                            pygame.draw.aaline(screen, beam_color, start_pos, end_pos) 
                            # ----------------------------------------------------

                            # --- Draw Extra Visual Beams for UltraMirror --- 
                            if tower.tower_id == "solar_ultramirror":
                                tower_half_height = tower.height_pixels // 2
                                top_start_pos = (start_pos[0], start_pos[1] - tower_half_height)
                                bottom_start_pos = (start_pos[0], start_pos[1] + tower_half_height)
                                # Draw extra beams converging on the target
                                pygame.draw.aaline(screen, beam_color, top_start_pos, end_pos)
                                pygame.draw.aaline(screen, beam_color, bottom_start_pos, end_pos)
                            # --- End Extra Visual Beams ---
                            
                            # --- Apply Damage & Effects (Conditional) --- 
                            # Ensure this block is aligned correctly with the drawing call above
                            # --- IMPORTANT: Only apply beam damage/effects if it IS a beam attack type --- 
                            if tower.attack_type == 'beam':
                                apply_effects_now = False
                                if is_painter:
                                    # Check if this target is THE painted target AND charge time is met
                                    if target_enemy == tower.painting_target and tower.paint_start_time > 0 and \
                                       (current_game_time - tower.paint_start_time >= charge_duration):
                                        print(f"Laser Painter {tower.tower_id} FIRE! Target: {target_enemy.enemy_id}")
                                        apply_effects_now = True
                                        # Reset paint time after firing to require re-charge
                                        tower.paint_start_time = 0.0 
                                else:
                                    # For non-painter towers (normal beams), effects apply every frame
                                    apply_effects_now = True
                                    
                                # Calculate buffed damage (only needed when applying effects)
                                buffed_stats = tower.get_buffed_stats(current_game_time, self.tower_buff_auras, self.towers) 
                                damage_multiplier = buffed_stats.get('damage_multiplier', 1.0)
                                
                                # Only apply damage if enough time has passed since last attack
                                if current_game_time - tower.last_attack_time >= tower.attack_interval:
                                    # Calculate and apply beam damage
                                    damage_min = tower.base_damage_min
                                    damage_max = tower.base_damage_max
                                    damage = random.uniform(damage_min, damage_max) * damage_multiplier
                                    
                                    # Apply damage to the target
                                    target_enemy.take_damage(damage, tower.damage_type)
                                    print(f"Beam tower {tower.tower_id} dealt {damage} {tower.damage_type} damage to {target_enemy.enemy_id}")
                                    
                                    # Update last attack time
                                    tower.last_attack_time = current_game_time
                                
                else:
                    # For non-painter towers (normal beams), effects apply every frame
                    apply_effects_now = True
                    
                    # Ensure this block is aligned correctly too
                    if apply_effects_now:
                        # Calculate buffed damage (only needed when applying effects)
                        buffed_stats = tower.get_buffed_stats(current_game_time, self.tower_buff_auras, self.towers) 
                        damage_multiplier = buffed_stats.get('damage_multiplier', 1.0)
                            
                # --- End Apply Damage & Effects --- 

        # Draw Tower Previews (Hover and Placement)
        if self.tower_preview:
            grid_x, grid_y = self.tower_preview
            selected_tower_id = self.tower_selector.get_selected_tower()
            if selected_tower_id:
                tower_data = self.available_towers.get(selected_tower_id)
                if tower_data: # Level 3
                    grid_width = tower_data.get('grid_width', 1)
                    grid_height = tower_data.get('grid_height', 1)
                    
                    is_valid_placement = self.is_valid_tower_placement(grid_x, grid_y, grid_width, grid_height)

                    # --- Draw preview image centered on the SNAPPED grid cell --- 
                    tower_pixel_width = grid_width * config.GRID_SIZE
                    tower_pixel_height = grid_height * config.GRID_SIZE
                    
                    # Calculate the center point using the same method as tower placement
                    offset_x = (grid_width - 1) // 2
                    offset_y = (grid_height - 1) // 2
                    start_x = grid_x - offset_x
                    start_y = grid_y - offset_y
                    
                    # Convert to pixel coordinates
                    tower_left = (start_x * config.GRID_SIZE) + config.UI_PANEL_PADDING
                    tower_top = (start_y * config.GRID_SIZE) + config.UI_PANEL_PADDING
                    
                    # Calculate the absolute center point in pixels
                    center_pixel_x = tower_left + (tower_pixel_width // 2)
                    center_pixel_y = tower_top + (tower_pixel_height // 2)
                    
                    # Calculate preview position so cursor is at true center
                    preview_pixel_x = center_pixel_x - (tower_pixel_width // 2)
                    preview_pixel_y = center_pixel_y - (tower_pixel_height // 2)
                    
                    # Draw tower call (Level 4)
                    self.tower_assets.draw_tower(screen, selected_tower_id,
                                              preview_pixel_x, preview_pixel_y,
                                              is_preview=True)

                    # --- Draw cell outlines based on snapped grid position --- 
                    indicator_color = config.GREEN if is_valid_placement else config.RED
                    for y_offset in range(grid_height):
                        for x_offset in range(grid_width):
                            cell_x = start_x + x_offset
                            cell_y = start_y + y_offset
                            if 0 <= cell_x < self.grid_width and 0 <= cell_y < self.grid_height:
                                cell_rect = pygame.Rect(
                                    (cell_x * config.GRID_SIZE) + config.UI_PANEL_PADDING, 
                                    (cell_y * config.GRID_SIZE) + config.UI_PANEL_PADDING, 
                                    config.GRID_SIZE, 
                                    config.GRID_SIZE
                                )
                                pygame.draw.rect(screen, indicator_color, cell_rect, 2)

                    # --- Draw Range Preview ---
                    tower_data = self.available_towers.get(selected_tower_id)
                    if tower_data and tower_data.get('attack_type') != 'aura':
                        range_units = tower_data.get('range', 0)
                        if range_units > 0:
                            range_pixels = int(range_units * (config.GRID_SIZE / 200.0))
                            range_color = (0, 255, 0, 100)  # Green, semi-transparent
                            
                            # Use the exact same center point as the tower preview
                            pygame.draw.circle(screen, range_color, (int(center_pixel_x), int(center_pixel_y)), range_pixels, 2)
                            
                            # Draw min range if applicable
                            min_range_units = tower_data.get('range_min', 0)
                            if min_range_units > 0:
                                min_range_pixels = int(min_range_units * (config.GRID_SIZE / 200.0))
                                min_range_color = (255, 100, 0, 100)  # Orange, semi-transparent
                                pygame.draw.circle(screen, min_range_color, (int(center_pixel_x), int(center_pixel_y)), min_range_pixels, 2)

        # --- Draw Enemy Preview Area Placeholder ---
        pygame.draw.rect(screen, (40, 40, 40), self.objective_area_rect) # Dark gray placeholder
        # TODO: Draw actual enemy previews here later

        # --- Draw Countdown Timer ---
        if self.wave_state == WAVE_STATE_WAITING and self.timer_font:
            # Format the timer to one decimal place
            timer_text = f"Next Wave: {max(0, self.wave_timer):.1f}s"
            gold_color = (255, 215, 0) # Define gold color
            text_surface = self.timer_font.render(timer_text, True, gold_color)

            # Calculate position: Centered horizontally, vertically centered in top restricted area
            text_rect = text_surface.get_rect(
                centerx=(config.UI_PANEL_PADDING + self.usable_grid_pixel_width // 2),
                centery=(config.UI_PANEL_PADDING + (config.RESTRICTED_TOWER_AREA_HEIGHT * config.GRID_SIZE) // 2)
            )
            screen.blit(text_surface, text_rect)
        # -------------------------

        # --- Draw UI elements --- 
        self.ui_manager.draw_ui(screen)

        # --- Draw Lives Display (AFTER UI) --- 
        try:
            lives_font = pygame.font.Font(None, 24) # Create smaller, local font
            if lives_font: 

                lives_text = f"Lives: {self.lives}"
                lives_surface = lives_font.render(lives_text, True, config.WHITE) # Use white color
                lives_rect = lives_surface.get_rect(topleft=(10, 10)) # Position with padding
                screen.blit(lives_surface, lives_rect)
            else:
                print("DEBUG: Failed to create local lives_font.")
        except Exception as e:
             print(f"ERROR drawing lives: {e}")
        # --- End Lives Display ---

        # --- Draw Hovered Tower Range Indicator ---
        if self.hovered_tower:
            grid_offset_x = config.UI_PANEL_PADDING # Get grid offset
            grid_offset_y = config.UI_PANEL_PADDING
            
            # Calculate the tower's center point in pixels
            tower_center_x = (self.hovered_tower.top_left_grid_x * config.GRID_SIZE) + (self.hovered_tower.grid_width * config.GRID_SIZE) // 2 + grid_offset_x
            tower_center_y = (self.hovered_tower.top_left_grid_y * config.GRID_SIZE) + (self.hovered_tower.grid_height * config.GRID_SIZE) // 2 + grid_offset_y
            center_pos = (int(tower_center_x), int(tower_center_y))

            # --- Draw Aura Radius (if applicable) --- 
            if (self.hovered_tower.attack_type == 'aura' or self.hovered_tower.attack_type == 'hybrid') and self.hovered_tower.special: 
                aura_radius_units = self.hovered_tower.special.get('aura_radius', 0)
                if aura_radius_units > 0:
                    aura_radius_pixels = int(aura_radius_units * (config.GRID_SIZE / 200.0))
                    aura_color = (0, 100, 255, 100) # Blueish, semi-transparent
                    if aura_radius_pixels > 0:
                        pygame.draw.circle(screen, aura_color, center_pos, aura_radius_pixels, 2)

            # --- Draw Attack Range (if applicable) --- 
            if self.hovered_tower.attack_type != 'aura':
                # Max range
                if hasattr(self.hovered_tower, 'range') and self.hovered_tower.range is not None and self.hovered_tower.range > 0:
                    max_range_pixels = int(self.hovered_tower.range)
                    range_color = (0, 255, 0, 100) # Green, alpha 100
                    if max_range_pixels > 0:
                        pygame.draw.circle(screen, range_color, center_pos, max_range_pixels, 2)
                    
                    # Min range (dead zone) - Draw ONLY if min_range > 0
                    if hasattr(self.hovered_tower, 'range_min_pixels') and self.hovered_tower.range_min_pixels > 0:
                        min_range_pixels = int(self.hovered_tower.range_min_pixels)
                        if min_range_pixels > 0:
                            # Draw a slightly different inner circle (e.g., dashed or different color/thickness)
                            dead_zone_color = (255, 100, 0, 100) # Orange-ish, semi-transparent
                            # Draw outline for dead zone
                            pygame.draw.circle(screen, dead_zone_color, center_pos, min_range_pixels, 2) # Use thickness 2 like outer range

        # --- End Hovered Range Indicator ---
        
    def draw_ui(self, screen):
        """Draw UI elements"""
        # Draw money and lives
        font = pygame.font.Font(None, 36)
        # money_text = font.render(f"Money: ${self.money}", True, (255, 255, 255)) # Commented out money rendering
        lives_text = font.render(f"Lives: {self.lives}", True, (255, 255, 255))
        # screen.blit(money_text, (10, 10)) # Commented out money drawing
        screen.blit(lives_text, (10, 50))
        
        # Draw tower selection UI
        # TODO: Implement tower selection UI
        # This could include:
        # 1. Tower icons in a bar at the bottom
        # 2. Tower costs
        # 3. Tower descriptions
        # 4. Selected tower highlight

    def is_valid_tower_placement(self, grid_x, grid_y, grid_width, grid_height):
        """Check if a tower can be placed at the given position"""
        # Calculate footprint of the tower to be placed
        offset_x = (grid_width - 1) // 2
        offset_y = (grid_height - 1) // 2
        new_start_x = grid_x - offset_x
        new_end_x = new_start_x + grid_width - 1 # Corrected calculation
        new_start_y = grid_y - offset_y
        new_end_y = new_start_y + grid_height - 1 # Corrected calculation

        # 1. Check Grid Bounds
        if not (0 <= new_start_x < self.grid_width and 0 <= new_end_x < self.grid_width and
                0 <= new_start_y < self.grid_height and 0 <= new_end_y < self.grid_height):
            print("Validation failed: Outside grid bounds.")
            return False

        # 2. Check for Existing Towers (Overlap Check)
        for existing_tower in self.towers:
            existing_start_x = existing_tower.top_left_grid_x
            existing_end_x = existing_tower.top_left_grid_x + existing_tower.grid_width - 1
            existing_start_y = existing_tower.top_left_grid_y
            existing_end_y = existing_tower.top_left_grid_y + existing_tower.grid_height - 1

            # Simple Axis-Aligned Bounding Box (AABB) overlap check
            if not (new_end_x < existing_start_x or new_start_x > existing_end_x or
                    new_end_y < existing_start_y or new_start_y > existing_end_y):
                print("Validation failed: Cannot place on existing tower.")
                return False # Found an overlap

        # 3. Check for Restricted Cells ('2') and Non-Traversable Towers ('1')
        for y in range(new_start_y, new_end_y + 1):
            for x in range(new_start_x, new_end_x + 1):
                # Check if the cell is restricted ('2')
                if self.grid[y][x] == 2:
                    print("Validation failed: Cannot place in restricted area.")
                    return False
                # Check if the cell is occupied by a non-traversable tower ('1')
                # (This might be redundant with the overlap check above, but is safe)
                if self.grid[y][x] == 1:
                    print("Validation failed: Cannot place on existing non-traversable tower footprint.")
                    return False
                    
        # --- 4. Pathfinding Check --- 
        # Get the tower data to check if it's traversable
        selected_tower_id = self.tower_selector.get_selected_tower() # Assumes tower is selected
        if not selected_tower_id: # Should not happen if called from placement, but safety check
            print("Validation Error: No tower selected for pathfinding check.")
            return False 
        tower_data = self.available_towers.get(selected_tower_id)
        if not tower_data:
            print(f"Validation Error: Tower data not found for {selected_tower_id}")
            return False
        is_traversable = tower_data.get('traversable', False)

        # Only modify temp_grid for path check IF the tower is NOT traversable
        if not is_traversable:
            # Create a temporary copy of the grid
            temp_grid = deepcopy(self.grid)
            # Simulate placing the tower on the temporary grid
            for y in range(new_start_y, new_end_y + 1):
                for x in range(new_start_x, new_end_x + 1):
                    # Bounds check again for safety
                    if 0 <= y < self.grid_height and 0 <= x < self.grid_width:
                        temp_grid[y][x] = 1 # Mark as obstacle

            # Check if a path still exists on the modified temp grid
            path = find_path(self.path_start_x, self.path_start_y, self.path_end_x, self.path_end_y, temp_grid)
            if not path: 
                print(f"Pathfinding failed: Placing non-traversable tower at ({grid_x},{grid_y}) would block the path.")
                return False
        # If traversable, skip the temp_grid modification and path check above
        # else: # Implicitly uses self.grid for path check if traversable
            # path = find_path(self.path_start_x, self.path_start_y, self.path_end_x, self.path_end_y, self.grid)
            # if not path: ... # Path check for traversable is likely redundant if placement rules are correct
            
        # All checks passed
        return True

    # --- Placeholder Enemy Spawning --- 
    def spawn_test_enemy(self, enemy_id):
        """Spawns a test enemy of the given ID."""
        # Get enemy data from config
        enemy_data = config.ENEMY_DATA.get(enemy_id)
        if not enemy_data:
            print(f"Warning: Enemy data not found for ID '{enemy_id}' in config.ENEMY_DATA. Cannot spawn.")
            return
        
        # Determine if the unit is an air unit
        is_air = enemy_data.get("type", "ground") == "air"
        
        # Get armor details based on enemy data
        armor_type_name = enemy_data.get("armor_type", "Unarmored") # Default to Unarmored if missing
        armor_details = self.armor_data.get(armor_type_name)
        if not armor_details:
            print(f"Warning: Armor details not found for type '{armor_type_name}'. Using defaults for enemy '{enemy_id}'.")
            # Use default Unarmored modifiers if lookup fails
            default_unarmored = self.armor_data.get("Unarmored", {})
            damage_modifiers = default_unarmored.get("damage_modifiers", {"normal": 1.0}) # Absolute fallback
        else:
            damage_modifiers = armor_details.get("damage_modifiers", {"normal": 1.0})
        
        # Find path first, passing the unit type
        grid_path = find_path(self.path_start_x, self.path_start_y, 
                              self.path_end_x, self.path_end_y, self.grid,
                              is_air_unit=is_air)

        if not grid_path:
            print(f"Warning: Could not find path to spawn enemy '{enemy_id}'.")
            return

        # Create the enemy with specific data including armor
        enemy = Enemy(self.visual_spawn_x_pixel, self.visual_spawn_y_pixel, 
                      grid_path, 
                      enemy_id=enemy_id, 
                      enemy_data=enemy_data, 
                      armor_type=armor_type_name, # Pass armor name
                      damage_modifiers=damage_modifiers) # Pass modifiers dict
        self.enemies.append(enemy)
        print(f"Spawned test enemy: {enemy_id} (Armor: {armor_type_name}) with path length {len(grid_path)}")

    def sell_tower_at(self, grid_x, grid_y):
        """Finds and sells a tower located at the given grid coordinates."""
        tower_to_sell = None
        for tower in self.towers:
            # Check if the click coordinates fall within the tower's footprint
            if (tower.top_left_grid_x <= grid_x < tower.top_left_grid_x + tower.grid_width and
                tower.top_left_grid_y <= grid_y < tower.top_left_grid_y + tower.grid_height):
                tower_to_sell = tower
                break # Found the tower
                
        if tower_to_sell:
            sell_value = int(tower_to_sell.cost * 0.5) # 50% sell value, rounded down
            self.money += sell_value
            print(f"Sold {tower_to_sell.tower_id} for ${sell_value}. Current Money: ${self.money}")

            # Play sell sound
            if self.sell_sound:
                self.sell_sound.play()

            # --- Stop Beam Sound If Playing ---
            if hasattr(tower_to_sell, 'is_beam_sound_playing') and tower_to_sell.is_beam_sound_playing and tower_to_sell.attack_sound:
                tower_to_sell.attack_sound.stop()
                print(f"DEBUG: Stopped beam sound for sold tower {tower_to_sell.tower_id}")
            # --- End Stop Beam Sound ---

            # Update UI display
            self.tower_selector.update_money(self.money)
            
            # Check if the sold tower was traversable before clearing grid cells
            is_traversable = tower_to_sell.tower_data.get('traversable', False)
            
            if not is_traversable:
                # Clear grid cells occupied by the non-traversable tower
                for y in range(tower_to_sell.top_left_grid_y, tower_to_sell.top_left_grid_y + tower_to_sell.grid_height):
                    for x in range(tower_to_sell.top_left_grid_x, tower_to_sell.top_left_grid_x + tower_to_sell.grid_width):
                        # Bounds check just in case
                        if 0 <= y < self.grid_height and 0 <= x < self.grid_width:
                            # Only clear if it was marked as 1 (tower), leave restricted areas (2) alone
                            if self.grid[y][x] == 1:
                                self.grid[y][x] = 0 # Set back to empty
                print(f"Cleared grid cells for sold non-traversable tower {tower_to_sell.tower_id}.")
            else:
                print(f"Skipped clearing grid cells for sold traversable tower {tower_to_sell.tower_id}.")
                        
            # Remove tower from list
            self.towers.remove(tower_to_sell)
            
            # --- Update Tower Links After Sell --- 
            self.update_tower_links()
            # --- End Link Update --- 
            
            # Potentially force enemy path recalculation if needed
            # self.recalculate_all_enemy_paths() # Add this if pathing doesn't auto-update
            
        else:
            print("No tower found at that location to sell.")
            
    def load_single_image(self, image_path):
        """Loads a single image, handling errors."""
        try:
            # Ensure path uses correct separators for the OS
            full_path = os.path.join(*image_path.split('/')) # Split by / and rejoin with os separator
            print(f"Attempting to load single image: {full_path}") # Debug print
            image = pygame.image.load(full_path).convert_alpha()
            print(f"  Successfully loaded: {full_path}")
            return image
        except pygame.error as e:
            print(f"Error loading image '{full_path}': {e}")
            return None
        except FileNotFoundError:
            print(f"Error: File not found at '{full_path}'")
            return None

    def load_armor_data(self, file_path):
        """Loads armor type data from a JSON file."""
        armor_types = {}
        if not os.path.isfile(file_path):
            print(f"Warning: Armor data file not found: {file_path}")
            return armor_types
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            for armor in data.get("armor_types", []):
                if "name" in armor and "damage_modifiers" in armor:
                    armor_types[armor["name"]] = armor # Store the whole armor object
            print(f"Loaded {len(armor_types)} armor types.")
        except json.JSONDecodeError as e:
            print(f"Error decoding armor JSON file {file_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred loading armor data {file_path}: {e}")
        return armor_types

    def load_damage_types(self, file_path):
        """Loads damage type descriptions from the tower races JSON file."""
        damage_types = {}
        if not os.path.isfile(file_path):
            print(f"Warning: Damage type data file not found: {file_path}")
            return damage_types
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            # Access the specific 'damagetypes' section within the JSON
            for dtype_name, dtype_data in data.get("damagetypes", {}).items():
                if "description" in dtype_data:
                    damage_types[dtype_name] = dtype_data # Store the whole dict
            print(f"Loaded {len(damage_types)} damage types.")
        except json.JSONDecodeError as e:
            print(f"Error decoding damage type JSON file {file_path}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred loading damage type data {file_path}: {e}")
        return damage_types

    def update_tower_links(self):
        """Calculate and update the linked_neighbors list for all Arc Towers."""
        arc_towers = [t for t in self.towers if t.tower_id == 'spark_arc_tower'] # Corrected ID
        if len(arc_towers) < 2: 
            for t in arc_towers:
                t.linked_neighbors = []
            return

        print(f"DEBUG: Updating tower links for {len(arc_towers)} Arc Towers...") # Keep this print
        for tower1 in arc_towers:
            tower1.linked_neighbors = [] 
            link_radius_units = tower1.tower_data.get("chain_link_radius", 0)
            if link_radius_units <= 0:
                continue 
                
            link_radius_pixels = link_radius_units * (config.GRID_SIZE / 200.0)
            link_radius_sq = link_radius_pixels ** 2
            print(f"  DEBUG: Tower1 ({tower1.center_grid_x},{tower1.center_grid_y}) LinkRadiusSq={link_radius_sq:.1f}") # Added detail
            
            for tower2 in arc_towers:
                if tower1 == tower2: 
                    continue
                
                dist_sq = (tower1.x - tower2.x)**2 + (tower1.y - tower2.y)**2
                # Enhanced Debug Print
                print(f"    DEBUG: Check ({tower1.center_grid_x},{tower1.center_grid_y})<->({tower2.center_grid_x},{tower2.center_grid_y}) | DistSq={dist_sq:.1f} | RadiusSq={link_radius_sq:.1f} | Link? {dist_sq <= link_radius_sq}")
                
                if dist_sq <= link_radius_sq:
                    if tower2 not in tower1.linked_neighbors:
                        tower1.linked_neighbors.append(tower2)
                        # Enhanced Debug Print
                        print(f"      DEBUG: LINK ADDED: ({tower1.center_grid_x},{tower1.center_grid_y}) -> ({tower2.center_grid_x},{tower2.center_grid_y})")
            # Print final list for tower1
            final_linked_ids = [f"({t.center_grid_x},{t.center_grid_y})" for t in tower1.linked_neighbors]
            print(f"  DEBUG: Tower1 ({tower1.center_grid_x},{tower1.center_grid_y}) final links: {final_linked_ids}")

    def process_attack_results(self, attack_results, grid_offset_x, grid_offset_y):
        """Helper function to process the results dictionary from standard tower attacks."""
        if isinstance(attack_results, dict):
            # Add any projectiles created
            new_projectiles = attack_results.get('projectiles', [])
            if new_projectiles:
                self.projectiles.extend(new_projectiles)
            # Add any visual effects created
            new_effects = attack_results.get('effects', [])
            if new_effects:
                self.effects.extend(new_effects)
            # Handle legacy chain visual return 
            if attack_results.get("type") == "chain_visual":
                chain_path = attack_results.get("path", [])
                if len(chain_path) >= 2:
                    adjusted_path = [(int(x + grid_offset_x), int(y + grid_offset_y)) for x, y in chain_path]
                    chain_effect = ChainLightningVisual(adjusted_path, duration=0.3)
                    self.effects.append(chain_effect)
        elif isinstance(attack_results, list):
             # Handle legacy list return 
             if attack_results: 
                 self.projectiles.extend(attack_results)

    def attempt_chain_zap(self, initiating_tower, current_time, all_enemies, grid_offset_x, grid_offset_y):
        """Attempts to find the longest chain and trigger a zap, or fallback to standard attack."""
        # Check if tower is on cooldown from previous chain participation
        # (Need attack_interval accessible, maybe pass buffed_stats or get here?)
        # For now, just use base interval for simplicity
        if current_time - initiating_tower.last_chain_participation_time < initiating_tower.attack_interval:
             return # Still on cooldown from last chain zap
             
        # Check standard attack interval as well (prevent spamming attempts)
        if current_time - initiating_tower.last_attack_time < initiating_tower.attack_interval:
             return # Standard attack interval cooldown

        print(f"Tower ({initiating_tower.center_grid_x},{initiating_tower.center_grid_y}) attempting chain zap...") # Keep
        linked_ids = [f"({t.center_grid_x},{t.center_grid_y})" for t in initiating_tower.linked_neighbors]
        print(f"  Initiator neighbors: {linked_ids}") # Keep

        # --- Pathfinding (DFS to find longest chain) --- 
        longest_chain = [initiating_tower] 
        stack = [(initiating_tower, [initiating_tower])] 
        max_len = 1

        while stack:
            current_node, path = stack.pop() 
            current_node_id = f"({current_node.center_grid_x},{current_node.center_grid_y})"
            path_ids = [f"({t.center_grid_x},{t.center_grid_y})" for t in path]
            print(f"    DFS Pop: Node={current_node_id}, Path={path_ids}") # Keep

            if len(path) > max_len:
                max_len = len(path)
                longest_chain = path
                path_ids = [f"({t.center_grid_x},{t.center_grid_y})" for t in path] # Re-calculate for print
                print(f"      DFS: New longest_chain found! Length={max_len}, Path={path_ids}") # Keep

            for neighbor in current_node.linked_neighbors:
                neighbor_id = f"({neighbor.center_grid_x},{neighbor.center_grid_y})"
                if neighbor not in path: 
                     new_path = path + [neighbor]
                     stack.append((neighbor, new_path))
                     new_path_ids = [f"({t.center_grid_x},{t.center_grid_y})" for t in new_path]
                     print(f"        DFS Pushing: Node={neighbor_id}, Path={new_path_ids}") # Keep
        # --- End DFS --- 

        # Check if a chain longer than 1 was found
        chain_found = len(longest_chain) > 1
        end_node_tower = longest_chain[-1] if chain_found else initiating_tower

        if chain_found:
            # Correctly indent this block
            print(f"... found chain: {[t.tower_id for t in longest_chain]}")
            # --- Target from End Node --- 
            target = None
            potential_targets = []
            for enemy in all_enemies:
                 if enemy.health > 0 and enemy.type in end_node_tower.targets and end_node_tower.is_in_range(enemy.x, enemy.y):
                     potential_targets.append(enemy)
            
            if potential_targets:
                potential_targets.sort(key=lambda e: (e.x - end_node_tower.x)**2 + (e.y - end_node_tower.y)**2)
                target = potential_targets[0]
                print(f"... end node {end_node_tower.tower_id} targeting {target.enemy_id}")
            else:
                print(f"... end node {end_node_tower.tower_id} found no targets in range.")

            if target:
                # --- Apply Chain Zap Damage & Effects --- 
                num_towers = len(longest_chain)
                damage_per_tower = initiating_tower.tower_data.get("chain_zap_damage_per_tower", 0)
                total_damage = num_towers * damage_per_tower
                damage_type = initiating_tower.damage_type
                
                print(f"... ZAPPING {target.enemy_id} for {total_damage} damage ({num_towers} towers)")
                target.take_damage(total_damage, damage_type)
                
                # --- Create Chain Link Visual --- 
                tower_positions = []
                for tower in longest_chain:
                    # Use tower's center pixel coords + grid offset for visual path
                    screen_x = int(tower.x + grid_offset_x)
                    screen_y = int(tower.y + grid_offset_y)
                    tower_positions.append((screen_x, screen_y))
                
                if len(tower_positions) >= 2:
                    link_visual = ChainLightningVisual(tower_positions, duration=0.4, line_type='tower_link') # Use tower_link type
                    self.effects.append(link_visual)
                # --- End Chain Link Visual ---
                
                # --- Create Supercharged Zap Visual --- 
                start_pos = (int(end_node_tower.x + grid_offset_x), int(end_node_tower.y + grid_offset_y))
                end_pos = (int(target.x + grid_offset_x), int(target.y + grid_offset_y))
                zap_visual = SuperchargedZapEffect(start_pos, end_pos, duration=0.25, thickness=5) # Adjust duration/thickness
                self.effects.append(zap_visual)
                # --- End Supercharged Zap Visual ---
                
                # Set cooldown for ALL participating towers
                for tower in longest_chain:
                    tower.last_chain_participation_time = current_time
                    tower.last_attack_time = current_time
            else:
                # Chain formed but no target found - Fallback?
                print("... Chain formed but no target. Initiator goes on cooldown.")
                initiating_tower.last_attack_time = current_time
        else:
            # --- Fallback to Standard Attack --- 
            print("... no chain found. Falling back to standard attack.")
            fallback_target = None
            potential_targets = []
            for enemy in all_enemies:
                 if enemy.health > 0 and enemy.type in initiating_tower.targets and initiating_tower.is_in_range(enemy.x, enemy.y):
                     potential_targets.append(enemy)
            if potential_targets:
                 potential_targets.sort(key=lambda e: (e.x - initiating_tower.x)**2 + (e.y - initiating_tower.y)**2)
                 fallback_target = potential_targets[0]
                 
            if fallback_target:
                 print(f"... initiator {initiating_tower.tower_id} firing standard projectile at {fallback_target.enemy_id}")
                 # Directly create the projectile instead of calling tower.attack
                 
                 # Calculate base damage (ignoring buffs for fallback simplicity for now)
                 dmg_min = initiating_tower.base_damage_min
                 dmg_max = initiating_tower.base_damage_max
                 base_damage = random.uniform(dmg_min, dmg_max)
                 is_crit = False # Fallback doesn't crit for now?
                 
                 # Get projectile speed and asset ID
                 proj_speed = initiating_tower.projectile_speed
                 proj_id = initiating_tower.tower_data.get('projectile_asset_id', initiating_tower.tower_id)
                 
                 # Create projectile
                 fallback_projectile = Projectile(
                     initiating_tower.x, initiating_tower.y, 
                     base_damage, proj_speed, proj_id,
                     target_enemy=fallback_target, 
                     splash_radius=initiating_tower.splash_radius_pixels, 
                     source_tower=initiating_tower, 
                     is_crit=is_crit,
                     damage_type=initiating_tower.damage_type,
                     # Pass 0 for bounce/pierce for standard fallback shot?
                     bounces_remaining=0, 
                     bounce_range_pixels=0,
                     bounce_damage_falloff=0,
                     pierce_adjacent=0
                 )
                 self.projectiles.append(fallback_projectile)
                 initiating_tower.last_attack_time = current_time # Set cooldown
                 
                 # Remove the recursive call and result processing
                 # attack_results = initiating_tower.attack(fallback_target, current_time, all_enemies, [], grid_offset_x, grid_offset_y, visual_assets=None)
                 # self.process_attack_results(attack_results, grid_offset_x, grid_offset_y)
            else:
                 print("... no standard target found either.")
                 initiating_tower.last_attack_time = current_time

    def load_wave_data(self, file_path):
        """Loads wave definitions from a JSON file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                print(f"Successfully loaded wave data from {file_path}. Found {len(data)} waves.")
                # TODO: Add validation logic here if needed
                return data
        except FileNotFoundError:
            print(f"ERROR: Wave data file not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to decode JSON from {file_path}: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred loading wave data: {e}")
            return []

    # --- Wave System Logic --- 
    def update_wave_system(self, current_time, delta_time):
        """Manages wave states, timers, and enemy spawning."""

        if self.wave_state == WAVE_STATE_WAITING:
            self.wave_timer -= delta_time
            if self.wave_timer <= 0:
                # Start spawning the current wave
                if 0 <= self.current_wave_index < len(self.all_wave_data):
                    current_wave = self.all_wave_data[self.current_wave_index]
                    self.spawning_groups = []
                    self.enemies_alive_this_wave = 0 # Reset counter for the new wave
                    print(f"--- Starting Wave {self.current_wave_index + 1} ---")
                    for group_data in current_wave.get('enemies', []):
                        # Prepare group state for spawning logic
                        self.spawning_groups.append({
                            'type': group_data['type'],
                            'remaining': group_data['count'],
                            'interval': group_data['spawn_interval'],
                            'interval_timer': group_data.get('initial_delay', 0.0), # Start with initial delay
                            'initial_delay_timer': group_data.get('initial_delay', 0.0)
                        })
                    self.wave_state = WAVE_STATE_SPAWNING
                else:
                    print("ERROR: Invalid wave index. Transitioning back to IDLE.")
                    self.wave_state = WAVE_STATE_IDLE # Should not happen
        
        elif self.wave_state == WAVE_STATE_SPAWNING:
            # Check if all groups have finished spawning
            if not self.spawning_groups:
                print(f"Wave {self.current_wave_index + 1} finished spawning. Total Spawned Counted: {self.enemies_alive_this_wave}") # DEBUG
                # Transition to INTERMISSION state
                self.wave_state = WAVE_STATE_INTERMISSION # CORRECTED TRANSITION
                print(f"--> Entering INTERMISSION state. Waiting for count to reach 0.") # DEBUG
                return # Stop processing spawns for this frame

            # Process active spawning groups
            # Iterate over a copy of the list in case we remove items
            for group in list(self.spawning_groups):
                # Handle initial delay first
                if group['initial_delay_timer'] > 0:
                    group['initial_delay_timer'] -= delta_time
                    continue # Skip spawning until initial delay is over
                    
                # Handle spawn interval
                group['interval_timer'] -= delta_time
                if group['interval_timer'] <= 0:
                    if group['remaining'] > 0:
                        self.spawn_enemy(group['type'])
                        group['remaining'] -= 1
                        group['interval_timer'] = group['interval'] # Reset timer
                    
                    # Check if this group is finished
                    if group['remaining'] <= 0:
                        self.spawning_groups.remove(group)

        elif self.wave_state == WAVE_STATE_INTERMISSION: # CORRECTED BLOCK
            # In this state, we wait until all enemies spawned *in this wave* are gone
            # (enemies_alive_this_wave is decremented on death or objective reach)
            print(f"DEBUG: In INTERMISSION. Checking enemies_alive_this_wave: {self.enemies_alive_this_wave}") # DEBUG
            if self.enemies_alive_this_wave <= 0:
                print(f"Wave {self.current_wave_index + 1} cleared!")
                
                # --- Award Wave Completion Bonus --- 
                # Make sure we have a valid current wave index
                if 0 <= self.current_wave_index < len(self.all_wave_data):
                    completed_wave_data = self.all_wave_data[self.current_wave_index]
                    bonus = completed_wave_data.get("wave_completion_bonus", 0)
                    if bonus > 0:
                        self.money += bonus
                        self.tower_selector.update_money(self.money) # Update UI
                        print(f"$$$ Wave Bonus Added: +{bonus}. Current Money: {self.money}")
                        # Optional: Add a floating text effect for the bonus?
                # --- End Bonus Award --- 
                
                # Current wave is fully cleared, prepare for the next one
                self.wave_state = WAVE_STATE_IDLE # Transition back to IDLE
                self.current_wave_index += 1
                if self.current_wave_index < len(self.all_wave_data):
                    next_wave_data = self.all_wave_data[self.current_wave_index]
                    self.wave_timer = next_wave_data.get('delay_before_wave', 10.0)
                    self.wave_state = WAVE_STATE_WAITING
                    print(f"Wave complete. Waiting {self.wave_timer:.1f}s for Wave {self.current_wave_index + 1}")
                else:
                    print("--- All waves spawned! --- ")
                    self.wave_state = WAVE_STATE_ALL_DONE # Or potentially WAVE_COMPLETE to wait for kills
                return # Stop processing spawns for this frame

    # --- Spawn Enemy Helper --- 
    def spawn_enemy(self, enemy_id):
        """Spawns a single enemy of the specified type at the visual spawn point."""
        # Get enemy data from config
        enemy_base_data = config.ENEMY_DATA.get(enemy_id)
        if not enemy_base_data:
            print(f"ERROR: Could not find enemy data for ID: {enemy_id}")
            return

        # Get armor data
        armor_type_name = enemy_base_data.get('armor_type', 'Unarmored')
        armor_info = self.armor_data.get(armor_type_name, {})
        damage_modifiers = armor_info.get('damage_modifiers', {})

        # --- Determine if enemy is air unit ---
        is_air = enemy_base_data.get("type", "ground") == "air"
        print(f"DEBUG Spawn: Spawning {enemy_id}, Type={enemy_base_data.get('type', 'ground')}, Is Air? {is_air}") # DEBUG
        # -------------------------------------

        # Find initial path, passing air unit status
        path = find_path(self.path_start_x, self.path_start_y, 
                         self.path_end_x, self.path_end_y, self.grid,
                         is_air_unit=is_air) # Pass the flag

        if path:
            # Use VISUAL spawn coordinates for initial position
            enemy = Enemy(self.visual_spawn_x_pixel, self.visual_spawn_y_pixel, 
                          path, enemy_id, enemy_base_data, armor_type_name, damage_modifiers)
            self.enemies.append(enemy)
            self.enemies_alive_this_wave += 1 # Increment count for wave tracking
            print(f"Spawned enemy: {enemy_id} (Wave: {self.current_wave_index + 1})")
        else:
            print(f"ERROR: Could not find path for enemy: {enemy_id}. Enemy not spawned.")
            # Handle this case - maybe game over or error message?

    # --- NEW: Callback for Towers to Add Entities --- 
    def add_pass_through_exploder(self, exploder_instance):
        """Callback method for towers to add newly created PassThroughExploders to the scene."""
        if isinstance(exploder_instance, PassThroughExploder):
            self.pass_through_exploders.append(exploder_instance)
        else:
            print(f"Warning: Attempted to add non-PassThroughExploder instance via callback: {exploder_instance}")
    # --- End Callback --- 

    # --- NEW: Callback Method for Adding Standard Effects ---
    def add_visual_effect(self, effect):
        """Simple callback to add a visual effect to the main effects list."""
        if effect:
            self.effects.append(effect)
    # --- END NEW CALLBACK ---

    # --- NEW: Money Callback Methods ---
    def can_afford(self, cost):
        """Checks if the player has enough money."""
        return self.money >= cost

    def deduct_money(self, cost):
        """Deducts money and updates the UI."""
        if self.can_afford(cost):
            self.money -= cost
            self.tower_selector.update_money(self.money) # Ensure UI is updated
            print(f"$$$ Deducted {cost}. Current Money: {self.money}") # Optional log
            return True
        else:
            print(f"Warning: Attempted to deduct {cost} but only have {self.money}.")
            return False
    # --- END Money Callbacks ---

    # --- NEW: Callback to add projectiles (used by Tower.update) ---
    def add_projectile(self, projectile):
        """Callback for towers to add projectiles created during their update phase."""
        if projectile:
            self.projectiles.append(projectile)
    # --- END Projectile Callback ---
