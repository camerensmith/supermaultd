import pygame
import pygame_gui
import os # Need os for listing directory contents
import random # Import random module
import glob # <<< ADD IMPORT
import math
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
from entities.grenade_projectile import GrenadeProjectile # <<< ADDED IMPORT
from entities.cluster_projectile import ClusterProjectile # <<< ADDED IMPORT
# Import all necessary effect classes at the top level
from entities.effect import Effect, FloatingTextEffect, ChainLightningVisual, RisingFadeEffect, GroundEffectZone, FlamethrowerParticleEffect, SuperchargedZapEffect, AcidSpewParticleEffect, PulseImageEffect, ExpandingCircleEffect, DrainParticleEffect, WhipVisual # Added AcidSpewParticleEffect, PulseImageEffect, ExpandingCircleEffect, DrainParticleEffect, WhipVisual
from entities.orbiting_damager import OrbitingDamager # NEW IMPORT
from entities.pass_through_exploder import PassThroughExploder # NEW IMPORT
from entities.status_effect_visualizer import StatusEffectVisualizer # <<< ADD IMPORT
import json # Import json for loading armor data
import pymunk

# Define wave states
WAVE_STATE_IDLE = "IDLE"
WAVE_STATE_WAITING = "WAITING_DELAY"
WAVE_STATE_SPAWNING = "SPAWNING"
WAVE_STATE_COMPLETE = "WAVE_COMPLETE" # Optional: Wait for enemies to clear
WAVE_STATE_ALL_DONE = "ALL_WAVES_COMPLETE"
WAVE_STATE_INTERMISSION = "INTERMISSION" # Added new state

# --- Game State ---
GAME_STATE_RUNNING = "RUNNING"
GAME_STATE_GAME_OVER = "GAME_OVER"
GAME_STATE_VICTORY = "VICTORY" # <<< ADDED NEW STATE

# --- Global Constants ---
MUSIC_END_EVENT = pygame.USEREVENT + 0 # Custom event for music track ending
# ----------------------

class GameScene:
    def __init__(self, game, selected_races_list, wave_file_path, screen_width, screen_height, click_sound, placement_sound, cancel_sound, sell_sound, invalid_placement_sound):
        """
        Initialize the game scene with new layout using actual screen dimensions.
        
        :param game: Reference to the game instance
        :param selected_races_list: LIST of race IDs selected by the player
        :param wave_file_path: Path to the wave definition file to load
        :param screen_width: Actual width of the screen/window
        :param screen_height: Actual height of the screen/window
        :param click_sound: Sound to play when clicking on the UI
        :param placement_sound: Sound to play when placing a tower
        :param cancel_sound: Sound to play when canceling placement
        :param sell_sound: Sound to play when selling a tower
        :param invalid_placement_sound: Sound to play when tower placement is invalid
        """
        print(f"Initializing GameScene with races: {selected_races_list}")
        self.game = game
        self.selected_races = selected_races_list # Store the list
        self.wave_file_path = wave_file_path
        self.screen_width = screen_width
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
                #print(f"[GameScene Init] Loaded death sound: {death_sound_path}")
            else:
                pass
        except pygame.error as e:
            pass
        # --- End Death Sound Loading ---

        # --- Load Life Loss Sound ---
        self.loss_life_sound = None
        try:
            loss_life_sound_path = os.path.join("assets", "sounds", "loss_life.mp3")
            if os.path.exists(loss_life_sound_path):
                self.loss_life_sound = pygame.mixer.Sound(loss_life_sound_path)
                #print(f"[GameScene Init] Loaded life loss sound: {loss_life_sound_path}")
            else:
                pass
        except pygame.error as e:
            pass
        # --- End Life Loss Sound Loading ---

        # --- Load Start Game Sound ---
        self.start_game_sound = None
        try:
            start_game_sound_path = os.path.join("assets", "sounds", "start_game.mp3")
            if os.path.exists(start_game_sound_path):
                self.start_game_sound = pygame.mixer.Sound(start_game_sound_path)
                #print(f"[GameScene Init] Loaded start game sound: {start_game_sound_path}")
            else:
                pass
        except pygame.error as e:
            pass
        # --- End Start Game Sound Loading ---

        # --- Load Game Over Sound --- 
        self.game_over_sound = None
        try:
            game_over_sound_path = os.path.join("assets", "sounds", "game_over.mp3")
            if os.path.exists(game_over_sound_path):
                self.game_over_sound = pygame.mixer.Sound(game_over_sound_path)
                #print(f"[GameScene Init] Loaded game over sound: {game_over_sound_path}")
            else:
                pass
               # print(f"[GameScene Init] Warning: Game over sound file not found: {game_over_sound_path}")
        except pygame.error as e:
            #print(f"[GameScene Init] Error loading game over sound: {e}")
            pass
        # --- End Game Over Sound Loading ---

        # --- Load Game Over Image --- 
        self.game_over_image = None
        try:
            game_over_image_path = os.path.join("assets", "images", "game_over.png")
            if os.path.exists(game_over_image_path):
                # Load with convert_alpha for potential transparency
                self.game_over_image = pygame.image.load(game_over_image_path).convert_alpha()
                #print(f"[GameScene Init] Loaded game over image: {game_over_image_path}")
            else:
                pass
                #print(f"[GameScene Init] Warning: Game over image file not found: {game_over_image_path}")
        except pygame.error as e:
            #print(f"[GameScene Init] Error loading game over image: {e}")
            pass
        # --- End Game Over Image Loading ---

        # --- Load Winner Image --- 
        self.winner_image = None
        try:
            winner_image_path = os.path.join("assets", "images", "winner.png")
            if os.path.exists(winner_image_path):
                self.winner_image = pygame.image.load(winner_image_path).convert_alpha()
                #print(f"[GameScene Init] Loaded winner image: {winner_image_path}")
            else:
                print(f"[GameScene Init] Warning: Winner image file not found: {winner_image_path}")
        except pygame.error as e:
            print(f"[GameScene Init] Error loading winner image: {e}")
        # --- End Winner Image Loading ---

        # --- Load Winner Sound --- 
        self.winner_sound = None
        try:
            winner_sound_path = os.path.join("assets", "sounds", "winner.mp3") 
            if os.path.exists(winner_sound_path):
                self.winner_sound = pygame.mixer.Sound(winner_sound_path)
                #print(f"[GameScene Init] Loaded winner sound: {winner_sound_path}")
            else:
                print(f"[GameScene Init] Warning: Winner sound file not found: {winner_sound_path}")
        except pygame.error as e:
            print(f"[GameScene Init] Error loading winner sound: {e}")
        # --- End Winner Sound Loading ---

        # --- Load Goblin Destruct Sound --- 
        self.goblin_destruct_sound = None
        try:
            destruct_sound_path = os.path.join("assets", "sounds", "goblin_destruct.mp3")
            if os.path.exists(destruct_sound_path):
                self.goblin_destruct_sound = pygame.mixer.Sound(destruct_sound_path)
                #print(f"[GameScene Init] Loaded goblin destruct sound: {destruct_sound_path}")
            else:
                pass
                #print(f"[GameScene Init] Warning: Goblin destruct sound file not found: {destruct_sound_path}")
        except pygame.error as e:
            #print(f"[GameScene Init] Error loading goblin destruct sound: {e}")
            pass
        # --- End Goblin Destruct Sound Loading ---

        # --- Load Explosion Effect Image (Placeholder) --- 
        self.explosion_effect_image = self.load_single_image("assets/effects/explosion.png") # Adjust path if needed
        if not self.explosion_effect_image:
            pass
            #print("Warning: Failed to load assets/effects/explosion.png for self-destruct effect.")
        # --- End Explosion Effect Image Loading ---

        # --- Load Play Area Frame Overlay (single PNG with transparent center) ---
        self.play_area_frame_image = None
        try:
            frame_path = os.path.join("assets", "images", "play_area_frame.png")
            if os.path.exists(frame_path):
                self.play_area_frame_image = pygame.image.load(frame_path).convert_alpha()
            else:
                # Optional: log a warning once
                pass
        except pygame.error:
            # If image fails to load, continue without overlay
            self.play_area_frame_image = None
        # --- End Play Area Frame Overlay Loading ---

        # --- Wave Menu Icon Toggle Button ---
        self.debug_toggle_state = False # State of the toggle (False = OFF, True = ON)
        self.toggle_off_surface = None
        self.toggle_on_surface = None
        self.toggle_button_rect = None # Rect for clicking
        self.toggle_padding = 10 # Pixels from corner
        try:
            # Load wave icon
            wave_icon_path = os.path.join("assets", "images", "wave.png")
            if os.path.exists(wave_icon_path):
                base_icon = pygame.image.load(wave_icon_path).convert_alpha()
                # Scale icon to a consistent UI size
                icon_size = 40
                base_icon = pygame.transform.smoothscale(base_icon, (icon_size, icon_size))
                # On state: original icon
                self.toggle_on_surface = base_icon
                # Off state: dimmed icon
                dim_icon = base_icon.copy()
                dim_icon.fill((120, 120, 120, 255), special_flags=pygame.BLEND_RGBA_MULT)
                self.toggle_off_surface = dim_icon
            else:
                # Fallback simple colored surfaces if icon not found
                fallback_size = (40, 40)
                self.toggle_off_surface = pygame.Surface(fallback_size, pygame.SRCALPHA)
                self.toggle_off_surface.fill((100, 0, 0, 255))
                self.toggle_on_surface = pygame.Surface(fallback_size, pygame.SRCALPHA)
                self.toggle_on_surface.fill((0, 100, 0, 255))
        except Exception:
            # Robust fallback in case image load fails
            fallback_size = (40, 40)
            self.toggle_off_surface = pygame.Surface(fallback_size, pygame.SRCALPHA)
            self.toggle_off_surface.fill((100, 0, 0, 255))
            self.toggle_on_surface = pygame.Surface(fallback_size, pygame.SRCALPHA)
            self.toggle_on_surface.fill((0, 100, 0, 255))
        # --- End Wave Menu Icon Toggle Button ---

        # --- Debug Menu Panel --- 
        self.debug_menu_open = False # Is the menu visible?
        self.debug_menu_width = 200
        self.debug_menu_height = 380 # <<< INCREASED HEIGHT SLIGHTLY
        self.debug_menu_surface = None
        self.debug_menu_rect = None # Rect for positioning
        self.debug_menu_font = None
        try:
            # Use a smaller font for the menu content to fit container
            from utils.fonts import get_font
            self.debug_menu_font = get_font(16)
            # <<< REMOVED SURFACE CREATION FROM INIT >>>
            # self.debug_menu_surface = pygame.Surface((self.debug_menu_width, self.debug_menu_height))
            # self.debug_menu_surface.fill((30, 30, 30)) # Dark gray background
            # # Draw a border
            # pygame.draw.rect(self.debug_menu_surface, (100, 100, 100), self.debug_menu_surface.get_rect(), 1)
            # 
            # # Add placeholder text
            # placeholder_text = "Debug Info:"
            # text_color = (220, 220, 220) # Light gray text
            # text_surf = self.debug_menu_font.render(placeholder_text, True, text_color)
            # text_rect = text_surf.get_rect(topleft=(5, 5)) # Add padding
            # self.debug_menu_surface.blit(text_surf, text_rect)
            #print("[GameScene Init] Loaded debug menu font.") # Adjusted print
        except Exception as e:
            #print(f"[GameScene Init] Error loading debug menu font: {e}")
            # Leave self.debug_menu_surface as None if error
            self.debug_menu_surface = None # Explicitly set to None on error
        # --- End Debug Menu Panel ---

        # --- MERGE Tower Data from Selected Races --- 
        self.available_towers = {}
        self.locked_race_towers = {}  # Store second race towers for later unlock
        
        # Load only the first race's towers initially
        if len(self.selected_races) > 0:
            first_race_id = self.selected_races[0]
            race_info = self.game.get_race_info(first_race_id)
            if race_info:
                race_towers = race_info.get("towers", {})
                self.available_towers.update(race_towers)
                print(f"[GameScene] Loaded {len(race_towers)} towers from first race: {first_race_id}")
        
        # Store second race towers for unlock at wave 10
        if len(self.selected_races) > 1:
            second_race_id = self.selected_races[1]
            race_info = self.game.get_race_info(second_race_id)
            if race_info:
                race_towers = race_info.get("towers", {})
                self.locked_race_towers = race_towers
                print(f"[GameScene] Stored {len(race_towers)} towers from second race: {second_race_id} (unlocks at wave 10)")
        
        print(f"[GameScene] Initialized with {len(self.available_towers)} available towers from races: {self.selected_races}")
        # --- End Merging Tower Data --- 

        # --- Get Base Directory for Path Construction ---
        # Get the directory where this game_scene.py file is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Go one level up to the project's root data directory (assuming data is sibling to scenes)
        data_dir = os.path.join(os.path.dirname(current_dir), 'data') 
        # --- End Base Directory ---
        
        # --- Load Armor Data Based on Game Mode ---
        armor_filename = 'armortypes.json' # Default
        if self.game.selected_wave_mode == 'classic':
            armor_filename = 'armortypes_advanced.json'
        elif self.game.selected_wave_mode == 'wild':
            armor_filename = 'armortypes_wild.json'
        
        armor_file_path = os.path.join(data_dir, armor_filename)
        #print(f"[GameScene Init] Determined armor file path based on mode '{self.game.selected_wave_mode}': {armor_file_path}")
        self.armor_data = self.load_armor_data(armor_file_path)
        if not self.armor_data:
            #print(f"WARNING: Failed to load armor data from {armor_file_path}. Enemies might use default modifiers.")
            pass
            # Optionally, try loading the default as a fallback
            # default_armor_path = os.path.join(data_dir, 'armortypes.json')
            # print(f"Attempting fallback load from: {default_armor_path}")
            # self.armor_data = self.load_armor_data(default_armor_path)
            # if not self.armor_data:
            #     print("ERROR: Fallback armor data load also failed!")
            #     self.armor_data = {} # Ensure it's at least an empty dict
        # --- End Armor Data Loading ---
        
        # Game state
        self.towers = []
        self.enemies = []
        # --- Load Money/Lives Based on Difficulty (Inferred from wave file path) ---
        if "advanced" in self.wave_file_path.lower(): # Check if it's advanced waves (now used by classic mode)
            #print(f"[GameScene Init] Loading ADVANCED settings (money/lives) due to wave file: {self.wave_file_path}")
            self.money = getattr(config, 'STARTING_MONEY_ADVANCED', config.STARTING_MONEY) # Fallback to default if advanced not found
            self.lives = getattr(config, 'STARTING_LIVES_ADVANCED', config.STARTING_LIVES) # Fallback to default if advanced not found
        else:
            #print(f"[GameScene Init] Loading DEFAULT settings (money/lives) for wave file: {self.wave_file_path}")
            self.money = config.STARTING_MONEY
            self.lives = config.STARTING_LIVES
        # --- End Money/Lives Loading ---
        # self.money = config.STARTING_MONEY # <<< REMOVED OLD ASSIGNMENT
        # self.lives = config.STARTING_LIVES # <<< REMOVED OLD ASSIGNMENT
        self.projectiles = [] # List to hold active projectiles
        self.active_beams = [] # List to hold active beam effects { 'tower': tower, 'target': enemy, 'end_time': timestamp }
        self.effects = [] # List to hold active visual effects
        self.orbiting_damagers = [] # List for orbiting damagers (We added this earlier, maybe manually?)
        self.pass_through_exploders = [] # NEW: List for pass-through exploders
        self.status_visualizers = [] # <<< ADDED: List for tower status visuals
        
        # --- Wave System State --- 
        self.all_wave_data = [] # Will be loaded from waves.json
        self.current_wave_index = -1
        self.wave_state = WAVE_STATE_IDLE # Start in IDLE
        self.wave_timer = 0.0 # Used for delay between waves
        self.spawning_groups = [] # List to track groups currently spawning
        self.enemies_alive_this_wave = 0 # Track enemies spawned in current wave
        self.wave_started = False # Flag to prevent restarting wave 0
        self.game_state = GAME_STATE_RUNNING # Initial game state
        self.is_paused = False
        
        # --- Wave Time Limit Timer ---
        self.wave_time_limit_timer = 0.0 # 60-second timer per wave
        self.wave_time_limit = 60.0 # 60 seconds to complete each wave
        self.wave_time_limit_expired = False # Flag if timer expired
        self.wave_bonus_gold = 0 # Bonus gold earned for completing wave in time
        self.final_countdown_played = False # Flag to track if countdown sound was played for current wave
        
        # --- Load Final Countdown Sound ---
        self.final_countdown_sound = None
        try:
            final_countdown_path = os.path.join("assets", "sounds", "finalcountdown.mp3")
            if os.path.exists(final_countdown_path):
                self.final_countdown_sound = pygame.mixer.Sound(final_countdown_path)
                #print(f"[GameScene Init] Loaded final countdown sound: {final_countdown_path}")
            else:
                pass
        except pygame.error as e:
            pass
        # --- End Final Countdown Sound Loading ---
        
        # --- Story Overlay Text ---
        self.story_overlay_active = True
        self.story_overlay_timer = 0.0
        self.story_overlay_duration = 40.0  
        self.story_text = "After a bunch of really powerful wizards imprisoned him in an icy tomb for eons, Lord Supermaul has somehow awakened and opened a demonic portal at his gravesite! Don't let these monstrosities escape the mountain, or else they'll destroy the world. Gather your defenses, slay these beasts and defeat Lord Supermaul for good!"
        self.story_font = None
        self.story_font_large = None
        # --- End Story Overlay Text ---
        
        # --- Hint Message System ---
        self.hint_message_active = False
        self.hint_message_start_time = 0.0
        self.hint_message_duration = 10.0  # Show for 10 seconds
        self.hint_triggered = False  # Track if hint has been shown for wave 2
        # --- End Hint Message System ---
        
        # -------------------------
        
        # Tower Chain Link Update Timer -- REMOVED
        # self.last_link_update_time = 0.0
        # self.link_update_interval = 1.0 # Seconds between recalculating links
        
        # UI state
        self.selected_tower = None
        self.tower_preview = None
        self.hovered_tower = None # Track which tower mouse is over
        
        # Drag state tracking
        self.is_dragging = False
        self.drag_start_pos = None
        self.drag_preview_positions = []
        
        # --- Layout Calculations (Use screen_width, screen_height) --- 
        # Panel dimensions based on percentage
        self.panel_pixel_width = int(self.screen_width * config.UI_PANEL_WIDTH_PERCENT)
        self.panel_pixel_height = self.screen_height - (config.UI_PANEL_PADDING * 2) # Use full height minus top/bottom padding
        # Position panel at right edge
        self.panel_x = self.screen_width - self.panel_pixel_width
        self.panel_y = config.UI_PANEL_PADDING

        # Grid dimensions: lock to fixed tile counts regardless of screen size
        self.grid_width = config.FIXED_TOTAL_GRID_WIDTH_TILES
        self.grid_height = config.FIXED_TOTAL_GRID_HEIGHT_TILES
        
        # Calculate playable area boundaries dynamically based on screen size
        # Boundaries extend to entire screen edges with 1 square of padding on all sides
        # Tower selector will overlay on top, so game area uses full screen
        # 
        # The grid must extend to full screen width with 1 square padding around:
        # - Left: 1 square padding
        # - Right: extends to screen edge (no padding)
        # - Top: 1 square padding
        # - Bottom: 1 square padding
        #
        # Calculate tile size: grid_width tiles fit in (screen_width - 1 tile padding on left)
        # grid_width * tile_size = screen_width - tile_size
        # (grid_width + 1) * tile_size = screen_width
        # tile_size = screen_width / (grid_width + 1)
        estimated_tile_width = self.screen_width / (self.grid_width + 1)  # +1 for left padding only
        
        # For height: grid_height tiles fit in (screen_height - 2 tile padding: top + bottom)
        # grid_height * tile_size = screen_height - 2*tile_size
        # (grid_height + 2) * tile_size = screen_height
        # tile_size = screen_height / (grid_height + 2)
        estimated_tile_height = self.screen_height / (self.grid_height + 2)  # +2 for top and bottom padding
        
        # Use the smaller tile size to ensure grid fits within bounds
        final_tile_size = min(estimated_tile_width, estimated_tile_height)
        
        # Set boundaries with 1 tile padding on left/top/bottom, full screen width on right
        padding = final_tile_size  # Use calculated tile size for padding
        self.play_area_left = int(padding)  # 1 tile from left edge
        self.play_area_top = int(padding)  # 1 tile from top edge
        self.play_area_right = int(self.screen_width)  # Full screen width (extends to right edge)
        self.play_area_bottom = int(self.screen_height - padding)  # 1 tile from bottom edge
        
        # Calculate available pixel space within the playable area boundaries
        # Right boundary extends to full screen width, left has padding
        play_area_width = self.play_area_right - self.play_area_left  # Full screen minus left padding
        play_area_height = self.play_area_bottom - self.play_area_top
        
        # Use the calculated play area for tile sizes
        # CRITICAL: usable_grid_pixel_width must extend to full screen minus left padding
        # Force right boundary to screen width and recalculate width
        self.play_area_right = int(self.screen_width)  # Force to full screen width
        play_area_width = self.play_area_right - self.play_area_left  # Recalculate with full screen width
        self.usable_grid_pixel_width = play_area_width  # Full screen minus left padding
        self.usable_grid_pixel_height = play_area_height
        
        # Debug: Verify boundaries extend to full screen
        # print(f"DEBUG: Screen width: {self.screen_width}, Play area left: {self.play_area_left}, Play area right: {self.play_area_right}, Play area width: {play_area_width}, Usable width: {self.usable_grid_pixel_width}")
        # Calculate actual tile sizes based on the playable area bounds
        # Tiles must fit exactly within the bounded area
        self.actual_tile_width = self.usable_grid_pixel_width / self.grid_width
        self.actual_tile_height = self.usable_grid_pixel_height / self.grid_height
        # Use average tile size for coordinate conversions (matches tower placement)
        self.avg_tile_size = (self.actual_tile_width + self.actual_tile_height) // 2

        # Align grid area with left padding and leave remaining space to the right for panel
        # Ensure panel position remains where it was computed above
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
            self.spawn_area_x * self.actual_tile_width,  # Grid starts at x=0 now
            self.spawn_area_y * self.actual_tile_height + config.UI_PANEL_PADDING,
            config.SPAWN_AREA_WIDTH * self.actual_tile_width,
            config.SPAWN_AREA_HEIGHT * self.actual_tile_height
        )

        # Calculate objective area position (centered at bottom)
        self.objective_area_x = (self.grid_width - config.OBJECTIVE_AREA_WIDTH) // 2
        self.objective_area_y = self.grid_height - config.OBJECTIVE_AREA_HEIGHT  # Bottom of the grid
        self.objective_area_rect = pygame.Rect(
            self.objective_area_x * self.actual_tile_width,  # Grid starts at x=0 now
            self.objective_area_y * self.actual_tile_height + config.UI_PANEL_PADDING,
            config.OBJECTIVE_AREA_WIDTH * self.actual_tile_width,
            config.OBJECTIVE_AREA_HEIGHT * self.actual_tile_height
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
        # Store grid-relative pixel coords (draw adds play area offsets)
        self.visual_spawn_x_pixel = (_visual_spawn_x_grid * self.avg_tile_size) + (self.avg_tile_size // 2)
        # Place spawn at the very top edge of the grid (restricted boundary)
        self.visual_spawn_y_pixel = -15

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
        #print(f"DEBUG INIT: Calculated Path Start: ({self.path_start_x}, {self.path_start_y}), Grid Value: {start_val}")
        #print(f"DEBUG INIT: Calculated Path End: ({self.path_end_x}, {self.path_end_y}), Grid Value: {end_val}")
        # Add a check to ensure start/end are actually walkable (value 0)
        if start_val != 0:
            #print(f"ERROR: Calculated Path Start ({self.path_start_x}, {self.path_start_y}) is NOT walkable (Value: {start_val})!")
            pass
        if end_val != 0:
            #print(f"ERROR: Calculated Path End ({self.path_end_x}, {self.path_end_y}) is NOT walkable (Value: {end_val})!")
            pass
        # --- END DEBUG ---

        # --- End Layout Calculations ---

        # Initialize pygame_gui Manager (Pass actual screen size)
        self.ui_manager = pygame_gui.UIManager((self.screen_width, self.screen_height), 'theme.json') 
        
        # Load background textures (store original, will scale during draw)
        self.original_background_image = None
        self.original_background2_image = None
        try:
            # Use the correct relative path from the supermaultd working directory
            self.original_background_image = pygame.image.load("assets/images/background.jpg").convert()
        except pygame.error as e:
            #print(f"Error loading background.jpg: {e}")
            self.original_background_image = None # Fallback
        try:
            # Load the border/mountain background for non-playable areas
            self.original_background2_image = pygame.image.load("assets/images/background2.jpg").convert()
        except pygame.error as e:
            #print(f"Error loading background2.jpg: {e}")
            self.original_background2_image = None # Fallback
        
        # Load spawn and objective marker images
        self.spawn_image = None
        self.objective_image = None
        try:
            self.spawn_image = pygame.image.load("assets/images/spawn.png").convert_alpha()
        except pygame.error as e:
            #print(f"Error loading spawn.png: {e}")
            self.spawn_image = None # Fallback
        try:
            self.objective_image = pygame.image.load("assets/images/objective.png").convert_alpha()
        except pygame.error as e:
            #print(f"Error loading objective.png: {e}")
            self.objective_image = None # Fallback
        
        # --- Grid Visibility ---
        # Get grid visibility from Game level (set in options menu)
        self.show_grid = getattr(game, 'show_grid', getattr(config, 'SHOW_GRID', False))
        
        # --- Camera / Edge Scroll ---
        # World camera for true panning (applied to grid/entities)
        self.cam_x = 0.0
        self.cam_y = 0.0
        # Background parallax camera (visual, follows the same inputs)
        self.bg_cam_x = 0.0
        self.bg_cam_y = 0.0
        self.bg_pan_range = 40  # Max pixels to pan background/frame (parallax)
        # Allow world camera to pan farther than background, revealing black beyond art
        self.cam_pan_range_x = int(self.screen_width)  # 1 screen width in each direction
        self.cam_pan_range_y = int(self.screen_height) # 1 screen height in each direction
        self.edge_scroll_margin = 24  # Pixels from screen edge to trigger scroll
        # Get edge scroll speed from Game level (set in options menu)
        self.edge_scroll_speed = getattr(game, 'edge_scroll_speed', 150.0)  # Pixels per second
        
        # --- Load Data using Constructed Paths --- 
        armor_file_path = os.path.join(data_dir, "armortypes.json")
        damage_file_path = os.path.join(data_dir, "tower_races.json")

        self.armor_data = self.load_armor_data(armor_file_path)
        # Load Damage Type Data (still from tower_races.json, but use correct path)
        self.damage_type_data = self.load_damage_types(damage_file_path)
       
        # --- End Data Loading --- 
        
        # --- Load Wave Data --- 
        # Remove the hardcoded path construction here
        # wave_file_path = os.path.join(data_dir, "waves.json") 
        # Call load_wave_data with the path passed to __init__
        self.all_wave_data = self.load_wave_data(self.wave_file_path) 
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
            #print("Warning: Failed to load assets/effects/kraken.png")
            pass
        # --- End Kraken Loading ---

        # --- Load Glacial Heart Pulse Image ---
        self.glacial_heart_pulse_image = self.load_single_image("assets/effects/igloo_glacial_heart.png")
        if not self.glacial_heart_pulse_image:
            #print("Warning: Failed to load assets/effects/igloo_glacial_heart.png")
            pass
        # --- End Glacial Heart Pulse Loading ---

        # --- Font for Countdown Timer ---
        try:
            from utils.fonts import get_font
            self.timer_font = get_font(42)
        except Exception as e:
            #print(f"Error loading default font: {e}")
            pass
            self.timer_font = None # Fallback
        # -------------------------------
        
        # --- Fonts for Story Overlay ---
        try:
            from utils.fonts import get_font
            self.story_font = get_font(24)  # Regular size for body text
            self.story_font_large = get_font(32)  # Larger size for title
            self.pulse_font = get_font(48)  # Large font for pulsing text
        except Exception as e:
            #print(f"Error loading story fonts: {e}")
            self.story_font = pygame.font.Font(None, 24)  # Fallback
            self.story_font_large = pygame.font.Font(None, 32)  # Fallback
            self.pulse_font = pygame.font.Font(None, 48)  # Fallback
        # -------------------------------
        
        # --- Load Attack Visual Assets --- 
        self.attack_visuals = {}
        fire_burst_img = self.load_single_image("assets/effects/fire_burst.png")
        if fire_burst_img:
            self.attack_visuals["fire_burst"] = fire_burst_img
        else:
            #print("Warning: Failed to load assets/effects/fire_burst.png")
            pass
        # Add other attack visuals here as needed...
        flak_cannon_img = self.load_single_image("assets/effects/tank_aegis_flak_cannon.png")
        if flak_cannon_img:
            self.attack_visuals["tank_aegis_flak_cannon"] = flak_cannon_img
        else:
            #print("Warning: Failed to load assets/effects/tank_aegis_flak_cannon.png")
            pass
        # --- End Attack Visual Loading ---

        # Initialize tower selector AFTER panel dimensions are calculated
        self.tower_selector = TowerSelector(
            available_towers=self.available_towers, 
            tower_assets=self.tower_assets, 
            manager=self.ui_manager, 
            initial_money=self.money,
            initial_lives=self.lives,
            panel_rect=pygame.Rect(self.panel_x, self.panel_y, self.panel_pixel_width, self.panel_pixel_height),
            damage_type_data=self.damage_type_data,
            click_sound=self.click_sound # Pass sound here
        )
        

        self.spawn_test_enemy("enemy1") # Assuming you have an enemy1.png
        
        #print(f"GameScene initialized. Actual Size: {self.screen_width}x{self.screen_height}") # Use actual size
        #print(f"Grid Area (Pixels): {self.usable_grid_pixel_width}x{self.usable_grid_pixel_height} | Grid Cells: {self.grid_width}x{self.grid_height}")
        #print(f"UI Panel Area (Pixels): {self.panel_pixel_width}x{self.panel_pixel_height} at ({self.panel_x},{self.panel_y})")
        #print(f"Enemy Preview Area: {self.objective_area_rect}")
        
        # --- Soundtrack Initialization (Added at the very end) --- 
        self.soundtrack_files = []
        self.current_track_index = -1
        try:
            soundtrack_dir = os.path.join("assets", "sounds")
            # Use absolute path for glob to be safe
            abs_soundtrack_dir = os.path.abspath(soundtrack_dir)
            track_pattern = os.path.join(abs_soundtrack_dir, "track*.mp3")
            #print(f"[Soundtrack Init] Searching for tracks: {track_pattern}")
            self.soundtrack_files = glob.glob(track_pattern)
            
            if not self.soundtrack_files:
                #print(f"[Soundtrack Init] No 'track*.mp3' files found in {abs_soundtrack_dir}")
                pass
            else:
                #print(f"[Soundtrack Init] Found tracks: {[os.path.basename(t) for t in self.soundtrack_files]}")
                random.shuffle(self.soundtrack_files)
                self.current_track_index = 0
                track_to_play = self.soundtrack_files[self.current_track_index]
                #print(f"[Soundtrack Init] Loading and playing first track: {os.path.basename(track_to_play)}")
                pygame.mixer.music.load(track_to_play)
                # Get volume from config, default to 0.4 if not found
                volume = getattr(config, 'SOUNDTRACK_VOLUME', 0.4) 
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.play(loops=0)
                print(f"[Soundtrack Init] First track started at volume {volume}.")
        except Exception as e:
            print(f"[Soundtrack Init] Error during initialization: {e}")
            self.current_track_index = -1 # Ensure playback doesn't start if error
        # --- End Soundtrack Initialization ---

        # Add tower limit tracking
        self.tower_counts = {}  # Track number of each tower type built

        # --- In-game Console State (backtick ` to toggle) ---
        self.console_active = False
        self.console_text = ""
        self.show_coordinates = False  # Toggle for showing coordinates near cursor

    def handle_event(self, event):
        """Handle pygame events"""
        # --- Handle Story Overlay Dismissal ---
        if self.story_overlay_active and event.type == pygame.KEYDOWN:
            self.story_overlay_active = False
            return  # Don't process other events while overlay is active
        # --- End Story Overlay Dismissal ---

        # --- Toggle Console with Backtick (`) ---
        if event.type == pygame.KEYDOWN:
            try:
                is_backtick = (event.key == pygame.K_BACKQUOTE) or (hasattr(event, 'unicode') and event.unicode == '`')
            except Exception:
                is_backtick = False
            if is_backtick:
                self.console_active = not self.console_active
                if self.console_active:
                    self.console_text = ""
                return

        # --- Handle Console Input When Active ---
        if self.console_active:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.console_active = False
                    return
                if event.key == pygame.K_RETURN:
                    self.execute_console_command(self.console_text.strip())
                    self.console_active = False
                    return
                if event.key == pygame.K_BACKSPACE:
                    if self.console_text:
                        self.console_text = self.console_text[:-1]
                    return
                # Append printable characters
                if hasattr(event, 'unicode') and event.unicode and event.unicode.isprintable():
                    self.console_text += event.unicode
                    return
            # While console is active, consume all events
            return
        
        # --- Check Game State First ---
        if self.game_state == GAME_STATE_GAME_OVER:
            if event.type == pygame.QUIT:
                self.game.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print("Game Over - ESC pressed. Returning to menu (TODO)")
            return

        # Handle pause toggle
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.is_paused = not self.is_paused
                # Clear any ongoing interactions when pausing
                if self.is_paused:
                    self.is_dragging = False
                    self.drag_start_pos = None
                    self.drag_preview_positions = []
                    self.tower_selector.clear_selection()
                    self.selected_tower = None
                    self.tower_preview = None
                return

        # Block all game interactions if paused
        if self.is_paused:
            return

        # Handle UI events first
        self.tower_selector.handle_event(event)
        
        # Handle Toggle Button Click
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.toggle_button_rect and self.toggle_button_rect.collidepoint(event.pos):
                    self.debug_toggle_state = not self.debug_toggle_state
                    self.debug_menu_open = self.debug_toggle_state
                    return
                
                # Start drag if a tower is selected
                selected_tower_id = self.tower_selector.get_selected_tower()
                if selected_tower_id:
                    mouse_x, mouse_y = event.pos
                    grid_offset_x = self.play_area_left - int(self.cam_x)
                    grid_offset_y = self.play_area_top - int(self.cam_y)
                    # Use average tile size to match preview calculation
                    avg_tile_size = (self.actual_tile_width + self.actual_tile_height) // 2
                    if (grid_offset_x <= mouse_x < grid_offset_x + self.usable_grid_pixel_width and
                        grid_offset_y <= mouse_y < grid_offset_y + self.usable_grid_pixel_height):
                        rel_x = mouse_x - grid_offset_x
                        rel_y = mouse_y - grid_offset_y
                        sel_id = self.tower_selector.get_selected_tower()
                        tw = 1
                        th = 1
                        if sel_id:
                            td = self.available_towers.get(sel_id)
                            if td:
                                tw = int(td.get('grid_width', 1))
                                th = int(td.get('grid_height', 1))
                        # Center the tower footprint on cursor: derive start cell then anchor center
                        center_gx = rel_x / avg_tile_size
                        center_gy = rel_y / avg_tile_size
                        start_x = int(round(center_gx - (tw / 2.0)))
                        start_y = int(round(center_gy - (th / 2.0)))
                        offset_x = (tw - 1) // 2
                        offset_y = (th - 1) // 2
                        grid_x = start_x + offset_x
                        grid_y = start_y + offset_y
                        self.is_dragging = True
                        self.drag_start_pos = (grid_x, grid_y)
                        self.drag_preview_positions = [(grid_x, grid_y)]
                
            elif event.button == 3:  # Right click
                mouse_x, mouse_y = event.pos
                grid_offset_x = self.play_area_left - int(self.cam_x)
                grid_offset_y = self.play_area_top - int(self.cam_y)
                # Use average tile size to match preview calculation
                avg_tile_size = (self.actual_tile_width + self.actual_tile_height) // 2
                if (grid_offset_x <= mouse_x < grid_offset_x + self.usable_grid_pixel_width and
                    grid_offset_y <= mouse_y < grid_offset_y + self.usable_grid_pixel_height):
                    rel_x = mouse_x - grid_offset_x
                    rel_y = mouse_y - grid_offset_y
                    sel_id = self.tower_selector.get_selected_tower()
                    tw = 1
                    th = 1
                    if sel_id:
                        td = self.available_towers.get(sel_id)
                        if td:
                            tw = int(td.get('grid_width', 1))
                            th = int(td.get('grid_height', 1))
                    center_gx = rel_x / avg_tile_size
                    center_gy = rel_y / avg_tile_size
                    start_x = int(round(center_gx - (tw / 2.0)))
                    start_y = int(round(center_gy - (th / 2.0)))
                    offset_x = (tw - 1) // 2
                    offset_y = (th - 1) // 2
                    grid_x = start_x + offset_x
                    grid_y = start_y + offset_y
                    
                    tower_at_location = None
                    for tower in self.towers:
                        if (tower.top_left_grid_x <= grid_x < tower.top_left_grid_x + tower.grid_width and
                            tower.top_left_grid_y <= grid_y < tower.top_left_grid_y + tower.grid_height):
                            tower_at_location = tower
                            break

                    is_previewing = self.tower_selector.get_selected_tower() is not None
                    
                    if tower_at_location:
                        self.sell_tower_at(grid_x, grid_y)
                    elif is_previewing:
                        self.tower_selector.clear_selection()
                        self.selected_tower = None 
                        self.tower_preview = None
                        if self.cancel_sound:
                            self.cancel_sound.play()
                
        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging and self.drag_start_pos:
                mouse_x, mouse_y = event.pos
                # Use selected tower size for snapping calculation
                sel_id = self.tower_selector.get_selected_tower()
                tw = 1
                th = 1
                if sel_id:
                    td = self.available_towers.get(sel_id)
                    if td:
                        tw = int(td.get('grid_width', 1))
                        th = int(td.get('grid_height', 1))
                
                # Calculate snapped grid position with 20% threshold
                snapped_x, snapped_y = self._calculate_snapped_grid_position(mouse_x, mouse_y, tw, th)
                
                if snapped_x is not None and snapped_y is not None:
                    current_grid_x = snapped_x
                    current_grid_y = snapped_y
                else:
                    # Outside grid bounds, skip drag preview
                    current_grid_x = None
                    current_grid_y = None
                
                if current_grid_x is not None and current_grid_y is not None:
                    start_x, start_y = self.drag_start_pos
                    positions = []
                    
                    selected_tower_id = self.tower_selector.get_selected_tower()
                    if selected_tower_id:
                        tower_data = self.available_towers.get(selected_tower_id)
                        if tower_data:
                            grid_width = tower_data.get('grid_width', 1)
                            grid_height = tower_data.get('grid_height', 1)
                            cost = tower_data.get('cost', 0)
                            
                            dx = current_grid_x - start_x
                            dy = current_grid_y - start_y
                            
                            # Calculate step sizes based on tower dimensions
                            step_x = grid_width if dx > 0 else -grid_width
                            step_y = grid_height if dy > 0 else -grid_height
                            
                            # Determine if we're moving more horizontally or vertically
                            abs_dx = abs(dx)
                            abs_dy = abs(dy)
                            
                            if abs_dx > abs_dy:  # More horizontal movement
                                # Place towers horizontally
                                int_start_x = int(start_x)
                                int_current_grid_x = int(current_grid_x)
                                int_step_x = 1 if dx > 0 else -1
                                for x in range(int_start_x, int_current_grid_x + int_step_x, int_step_x):
                                    positions.append((x, start_y))
                            elif abs_dy > abs_dx:  # More vertical movement
                                # Place towers vertically
                                int_start_y = int(start_y)
                                int_current_grid_y = int(current_grid_y)
                                int_step_y = 1 if dy > 0 else -1
                                for y in range(int_start_y, int_current_grid_y + int_step_y, int_step_y):
                                    positions.append((start_x, y))
                            else:  # Equal movement (diagonal)
                                # Place towers diagonally
                                steps = int(min(abs_dx // abs(step_x), abs_dy // abs(step_y)))
                                for i in range(int(steps) + 1):
                                    x = start_x + (i * step_x)
                                    y = start_y + (i * step_y)
                                    positions.append((x, y))
                            
                            max_towers = self.money // cost
                            
                            valid_positions = []
                            for pos in positions:
                                if len(valid_positions) >= max_towers:
                                    break
                                if self.is_valid_tower_placement(pos[0], pos[1], grid_width, grid_height):
                                    valid_positions.append(pos)
                            
                            self.drag_preview_positions = valid_positions
                
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Left mouse button release
                if self.is_dragging:
                    selected_tower_id = self.tower_selector.get_selected_tower()
                    if selected_tower_id and self.drag_preview_positions:
                        tower_data = self.available_towers.get(selected_tower_id)
                        if tower_data:
                            cost = tower_data.get('cost', 0)
                            total_cost = cost * len(self.drag_preview_positions)
                            
                            if self.money >= total_cost:
                                for pos in self.drag_preview_positions:
                                    self.handle_tower_placement(pos[0], pos[1], is_drag_placement=True)
                                if self.placement_sound:
                                    self.placement_sound.play()
                            else:
                                if self.invalid_placement_sound:
                                    self.invalid_placement_sound.play()
                    
                    self.is_dragging = False
                    self.drag_start_pos = None
                    self.drag_preview_positions = []
                    
                    self.tower_selector.clear_selection()
                    self.selected_tower = None
                    self.tower_preview = None
                
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.tower_selector.clear_selection()
                self.selected_tower = None
                self.tower_preview = None
            elif event.key == pygame.K_t:
                # Toggle tower selector panel visibility
                self.tower_selector.toggle_panel()
            elif event.key == pygame.K_w:
                # Toggle wave/debug menu
                self.debug_toggle_state = not self.debug_toggle_state
                self.debug_menu_open = self.debug_toggle_state
            elif event.key == pygame.K_g:
                self.spawn_test_enemy("crone")
            elif event.key == pygame.K_s:
                self.spawn_test_enemy("quillpig")
            # Tower selection keys: 1-9, 0, Shift+1-9, Shift+0
            # Map keys to tower indices: 1->0, 2->1, ..., 9->8, 0->9
            # Shift+1->10, Shift+2->11, ..., Shift+9->18, Shift+0->19
            elif event.key == pygame.K_1:
                if hasattr(self, 'tower_selector') and self.tower_selector:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.tower_selector.select_tower_by_index(10)  # Shift+1 = index 10
                    else:
                        self.tower_selector.select_tower_by_index(0)  # 1 = index 0
            elif event.key == pygame.K_2:
                if hasattr(self, 'tower_selector') and self.tower_selector:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.tower_selector.select_tower_by_index(11)  # Shift+2 = index 11
                    else:
                        self.tower_selector.select_tower_by_index(1)  # 2 = index 1
            elif event.key == pygame.K_3:
                if hasattr(self, 'tower_selector') and self.tower_selector:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.tower_selector.select_tower_by_index(12)  # Shift+3 = index 12
                    else:
                        self.tower_selector.select_tower_by_index(2)  # 3 = index 2
            elif event.key == pygame.K_4:
                if hasattr(self, 'tower_selector') and self.tower_selector:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.tower_selector.select_tower_by_index(13)  # Shift+4 = index 13
                    else:
                        self.tower_selector.select_tower_by_index(3)  # 4 = index 3
            elif event.key == pygame.K_5:
                if hasattr(self, 'tower_selector') and self.tower_selector:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.tower_selector.select_tower_by_index(14)  # Shift+5 = index 14
                    else:
                        self.tower_selector.select_tower_by_index(4)  # 5 = index 4
            elif event.key == pygame.K_6:
                if hasattr(self, 'tower_selector') and self.tower_selector:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.tower_selector.select_tower_by_index(15)  # Shift+6 = index 15
                    else:
                        self.tower_selector.select_tower_by_index(5)  # 6 = index 5
            elif event.key == pygame.K_7:
                if hasattr(self, 'tower_selector') and self.tower_selector:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.tower_selector.select_tower_by_index(16)  # Shift+7 = index 16
                    else:
                        self.tower_selector.select_tower_by_index(6)  # 7 = index 6
            elif event.key == pygame.K_8:
                if hasattr(self, 'tower_selector') and self.tower_selector:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.tower_selector.select_tower_by_index(17)  # Shift+8 = index 17
                    else:
                        self.tower_selector.select_tower_by_index(7)  # 8 = index 7
            elif event.key == pygame.K_9:
                if hasattr(self, 'tower_selector') and self.tower_selector:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.tower_selector.select_tower_by_index(18)  # Shift+9 = index 18
                    else:
                        self.tower_selector.select_tower_by_index(8)  # 9 = index 8
            elif event.key == pygame.K_0:
                if hasattr(self, 'tower_selector') and self.tower_selector:
                    if event.mod & pygame.KMOD_SHIFT:
                        self.tower_selector.select_tower_by_index(19)  # Shift+0 = index 19
                    else:
                        self.tower_selector.select_tower_by_index(9)   # 0 = index 9
            elif event.key == pygame.K_RETURN:
                if self.wave_state == WAVE_STATE_IDLE and not self.wave_started:
                    self.wave_started = True
                    if self.all_wave_data:
                        self.current_wave_index = 0
                        first_wave_data = self.all_wave_data[0]
                        self.wave_timer = first_wave_data.get('delay_before_wave', 5.0)
                        self.wave_state = WAVE_STATE_WAITING
                        
                        # Play start game sound for first wave
                        if self.start_game_sound:
                            self.start_game_sound.play()
                        
                        # Notify race selector about first wave start
                        self.notify_wave_change()
                    else:
                        self.wave_state = WAVE_STATE_IDLE

        # Tower Hover Detection
        mouse_x, mouse_y = pygame.mouse.get_pos()
        grid_offset_x = self.play_area_left - int(self.cam_x)
        grid_offset_y = self.play_area_top - int(self.cam_y)
        relative_mouse_x = mouse_x - grid_offset_x
        relative_mouse_y = mouse_y - grid_offset_y
        
        found_hover = None
        if (grid_offset_x <= mouse_x < grid_offset_x + self.usable_grid_pixel_width and
            grid_offset_y <= mouse_y < grid_offset_y + self.usable_grid_pixel_height):
            # Use average tile size for grid coordinate conversion to match tower positioning (nearest center)
            avg_tile_size = (self.actual_tile_width + self.actual_tile_height) // 2
            hover_grid_x = (relative_mouse_x + (avg_tile_size // 2)) // avg_tile_size
            hover_grid_y = (relative_mouse_y + (avg_tile_size // 2)) // avg_tile_size
            
            for tower in self.towers:
                if (tower.top_left_grid_x <= hover_grid_x < tower.top_left_grid_x + tower.grid_width and
                    tower.top_left_grid_y <= hover_grid_y < tower.top_left_grid_y + tower.grid_height):
                    found_hover = tower
                    break
                    
        self.hovered_tower = found_hover

        # Update tower preview position
        if not self.is_dragging and self.tower_selector.get_selected_tower():
            mouse_x, mouse_y = pygame.mouse.get_pos()
            selected_tower_id = self.tower_selector.get_selected_tower()
            tower_data = self.available_towers.get(selected_tower_id) if selected_tower_id else None
            grid_width = tower_data.get('grid_width', 1) if tower_data else 1
            grid_height = tower_data.get('grid_height', 1) if tower_data else 1
            
            # Calculate snapped grid position with 20% threshold
            snapped_x, snapped_y = self._calculate_snapped_grid_position(mouse_x, mouse_y, grid_width, grid_height)
            
            if snapped_x is not None and snapped_y is not None:
                if 0 <= snapped_x < self.grid_width and 0 <= snapped_y < self.grid_height:
                    self.tower_preview = (snapped_x, snapped_y)
                else:
                    self.tower_preview = None
            else:
                self.tower_preview = None
        elif not self.is_dragging:
            self.tower_preview = None

    def _calculate_snapped_grid_position(self, mouse_x, mouse_y, grid_width, grid_height):
        """
        Calculate snapped grid position with 20% threshold.
        If mouse is at least 20% into the next grid square, snap to that square.
        Otherwise, snap to the current square.
        Returns (snapped_grid_x, snapped_grid_y) or (None, None) if outside grid bounds.
        """
        grid_offset_x = self.play_area_left - int(self.cam_x)
        grid_offset_y = self.play_area_top - int(self.cam_y)
        
        # Check if mouse is within grid bounds
        if not (grid_offset_x <= mouse_x < grid_offset_x + self.usable_grid_pixel_width and
                grid_offset_y <= mouse_y < grid_offset_y + self.usable_grid_pixel_height):
            return (None, None)
        
        # Use average tile size for consistency
        avg_tile_size = (self.actual_tile_width + self.actual_tile_height) // 2
        
        # Calculate relative position within grid
        rel_x = mouse_x - grid_offset_x
        rel_y = mouse_y - grid_offset_y
        
        # Calculate grid position as float (center of tower)
        center_gx = rel_x / avg_tile_size
        center_gy = rel_y / avg_tile_size
        
        # Calculate the top-left grid cell that would contain the center
        # For multi-tile towers, we need to account for the offset
        offset_x = (grid_width - 1) // 2
        offset_y = (grid_height - 1) // 2
        start_x_float = center_gx - (grid_width / 2.0)
        start_y_float = center_gy - (grid_height / 2.0)
        
        # Get the integer part (current cell) and fractional part
        current_cell_x = int(start_x_float)
        current_cell_y = int(start_y_float)
        frac_x = start_x_float - current_cell_x
        frac_y = start_y_float - current_cell_y
        
        # Apply 20% threshold: if >= 20% into next cell, snap to next cell
        SNAP_THRESHOLD = 0.2
        if frac_x >= SNAP_THRESHOLD:
            snapped_start_x = current_cell_x + 1
        else:
            snapped_start_x = current_cell_x
            
        if frac_y >= SNAP_THRESHOLD:
            snapped_start_y = current_cell_y + 1
        else:
            snapped_start_y = current_cell_y
        
        # Calculate the center grid position from the snapped start position
        snapped_grid_x = snapped_start_x + offset_x
        snapped_grid_y = snapped_start_y + offset_y
        
        return (snapped_grid_x, snapped_grid_y)

    def handle_tower_placement(self, grid_x, grid_y, is_drag_placement=False):
        """Handle tower placement on the grid, considering tower size."""
        selected_tower_id = self.tower_selector.get_selected_tower()
        if not selected_tower_id:
            return

        tower_data = self.available_towers.get(selected_tower_id)
        if not tower_data:
            return

        # Check tower limit
        tower_limit = tower_data.get('limit')
        if tower_limit is not None:
            current_count = self.tower_counts.get(selected_tower_id, 0)
            if current_count >= tower_limit:
                if self.invalid_placement_sound:
                    self.invalid_placement_sound.play()
                return

        # Get tower dimensions (assuming 1x1 if not specified)
        grid_width = tower_data.get('grid_width', 1)
        grid_height = tower_data.get('grid_height', 1)

        # --- Validation Checks ---
        # Use the comprehensive validation method which includes pathfinding
        is_valid = self.is_valid_tower_placement(grid_x, grid_y, grid_width, grid_height)
        if not is_valid:
            if self.invalid_placement_sound:
                self.invalid_placement_sound.play()
            return

        # Check if player has enough money (separate from positional validation)
        if self.money < tower_data['cost']:
            return

        # --- Placement ---
        # Calculate footprint again (needed for marking the grid)
        offset_x = (grid_width - 1) // 2
        offset_y = (grid_height - 1) // 2
        new_start_x = grid_x - offset_x
        new_end_x = new_start_x + grid_width - 1
        new_start_y = grid_y - offset_y
        new_end_y = new_start_y + grid_height - 1

        # Check if tower is traversable
        is_traversable = tower_data.get('traversable', False)

        # Mark occupied grid cells ONLY if not traversable
        if not is_traversable:
            # Ensure grid coordinates are integers for grid indexing
            grid_x = int(grid_x)
            grid_y = int(grid_y)
            grid_width = int(grid_width)
            grid_height = int(grid_height)
            
            # Calculate the true top-left corner based on center and dimensions
            actual_top_left_x = grid_x - (grid_width - 1) // 2
            actual_top_left_y = grid_y - (grid_height - 1) // 2
            
            # Loop from the calculated top-left for the full width/height
            for y_offset in range(grid_height):
                for x_offset in range(grid_width):
                    mark_x = int(actual_top_left_x + x_offset)
                    mark_y = int(actual_top_left_y + y_offset)
                    # Check bounds within loop for safety
                    if 0 <= mark_y < self.grid_height and 0 <= mark_x < self.grid_width:
                        self.grid[mark_y][mark_x] = 1 # Mark as obstacle

        # Create and place the tower (using center grid coordinates)
        from entities.tower import Tower
        tower = Tower(grid_x, grid_y, selected_tower_id, tower_data)
        self.towers.append(tower)
        
        # Update tower count
        self.tower_counts[selected_tower_id] = self.tower_counts.get(selected_tower_id, 0) + 1
        
        # Update tower selector UI
        self.tower_selector.update_tower_counts(self.tower_counts)
        
        # Deduct money
        self.deduct_money(tower_data['cost'])

        # Recalculate paths for all existing enemies ONLY if the placed tower is NOT traversable
        if not is_traversable:
            for enemy in self.enemies[:]:  # Use slice copy
                # Get enemy's current grid position (use avg_tile_size for consistency)
                current_grid_x = int(enemy.x // self.avg_tile_size)
                current_grid_y = int(enemy.y // self.avg_tile_size)
                
                # Skip path recalculation for air units
                if enemy.type == 'air':
                    continue
                
                # Find new path from current position to objective
                new_path = find_path(current_grid_x, current_grid_y, 
                                   self.path_end_x, self.path_end_y, 
                                   self.grid)
                
                if new_path:
                    # Update enemy's path
                    enemy.grid_path = new_path
                    enemy.path_index = 0  # Reset path index
                else:
                    # If no path found, remove the enemy (it's trapped)
                    self.enemies.remove(enemy)

        # Only clear selection if this is not part of a drag placement
        if not is_drag_placement:
            self.tower_selector.clear_selection()
            self.selected_tower = None
            self.tower_preview = None
        
        # Update Tower Links After Placement
        self.update_tower_links()

    def update(self, time_delta):
        """Update game state"""
        # Skip updates if paused
        if self.is_paused:
            return

        # --- Story Overlay Timer Update ---
        if self.story_overlay_active:
            self.story_overlay_timer += time_delta
            if self.story_overlay_timer >= self.story_overlay_duration:
                self.story_overlay_active = False
        # --- End Story Overlay Timer Update ---

        # --- Hint Message Timer Update ---
        current_time = pygame.time.get_ticks() / 1000.0
        if self.hint_message_active and current_time >= self.hint_message_start_time:
            # Check if hint message should be hidden (after 10 seconds)
            if current_time >= self.hint_message_start_time + self.hint_message_duration:
                self.hint_message_active = False
        # --- End Hint Message Timer Update ---

        # --- Game State Check ---        
        # <<< MODIFIED: Check for running state >>>
        if self.game_state != GAME_STATE_RUNNING:
            return # Don't update anything if game is not running
        # --- End Game State Check ---

        current_time = pygame.time.get_ticks() / 1000.0 # Get current time once

        # --- Edge Scroll (Drives both camera and parallax) ---
        try:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = 0.0
            dy = 0.0
            if mouse_x < self.edge_scroll_margin:
                dx = -1.0
            elif mouse_x > (self.screen_width - self.edge_scroll_margin):
                dx = 1.0
            if mouse_y < self.edge_scroll_margin:
                dy = -1.0
            elif mouse_y > (self.screen_height - self.edge_scroll_margin):
                dy = 1.0
            if dx != 0.0 or dy != 0.0:
                delta_x = dx * self.edge_scroll_speed * time_delta
                delta_y = dy * self.edge_scroll_speed * time_delta
                self.cam_x += delta_x
                self.cam_y += delta_y
                self.bg_cam_x += delta_x
                self.bg_cam_y += delta_y
                # Clamp world camera to a larger range (allows black zone)
                if self.cam_x < -self.cam_pan_range_x: self.cam_x = -self.cam_pan_range_x
                if self.cam_x > self.cam_pan_range_x: self.cam_x = self.cam_pan_range_x
                if self.cam_y < -self.cam_pan_range_y: self.cam_y = -self.cam_pan_range_y
                if self.cam_y > self.cam_pan_range_y: self.cam_y = self.cam_pan_range_y
                # Clamp background parallax separately to smaller range
                if self.bg_cam_x < -self.bg_pan_range: self.bg_cam_x = -self.bg_pan_range
                if self.bg_cam_x > self.bg_pan_range: self.bg_cam_x = self.bg_pan_range
                if self.bg_cam_y < -self.bg_pan_range: self.bg_cam_y = -self.bg_pan_range
                if self.bg_cam_y > self.bg_pan_range: self.bg_cam_y = self.bg_pan_range
        except Exception:
            pass
        # --- End Edge Scroll ---

        # --- Helper function to trigger game end state ---
        def trigger_game_end(is_victory):
            if self.game_state != GAME_STATE_RUNNING: return # Already ended

            if is_victory:
                self.game_state = GAME_STATE_VICTORY
                #print("Victory!")
                pygame.mixer.music.fadeout(500)
                if self.winner_sound:
                    self.winner_sound.play()
            else:
                self.game_state = GAME_STATE_GAME_OVER
                #print("Game Over!")
                pygame.mixer.music.fadeout(500)
                if self.game_over_sound:
                    self.game_over_sound.play()
        # --- End Helper ---

        # --- Soundtrack Advancement (Manual Check) --- 
        if self.soundtrack_files and self.current_track_index != -1: # Check if music should be playing
            if not pygame.mixer.music.get_busy():
                #print(f"[Soundtrack Update] Mixer not busy, track likely finished.")
                # Advance index and wrap around
                self.current_track_index = (self.current_track_index + 1) % len(self.soundtrack_files)
                next_track_path = self.soundtrack_files[self.current_track_index]
                #print(f"[Soundtrack Update] Attempting to play next track ({self.current_track_index + 1}/{len(self.soundtrack_files)}): {os.path.basename(next_track_path)}")
                try:
                    pygame.mixer.music.load(next_track_path)
                    pygame.mixer.music.play(loops=0) # Play once
                    #print(f"[Soundtrack Update] Successfully started next track.")
                except pygame.error as e:
                    #print(f"[Soundtrack Update] Error loading/playing track {next_track_path}: {e}")
                    # Stop trying if error occurs
                    try: pygame.mixer.music.stop()
                    except: pass
                    self.current_track_index = -1
        # --- END Soundtrack Advancement --- 

        # --- Wave System Update --- 
        self.update_wave_system(current_time, time_delta)
        # ------------------------
        
        # --- Update Tower Links (Periodically) --- REMOVED
        # time_since_last_link_update = current_time - self.last_link_update_time
        # print(f"DEBUG Link Update Check: Time since last={time_since_last_link_update:.2f}s, Interval={self.link_update_interval}s") # Debug print
        # if time_since_last_link_update >= self.link_update_interval:
        #     self.update_tower_links()
        #     self.last_link_update_time = current_time
        # --- End Link Update ---
        
        # Update UI
        self.tower_selector.update(time_delta)
        
        # --- Pre-calculate Tower Buff Auras (Affecting Towers) --- 
        # Store as instance variable for use in draw method
        self.tower_buff_auras = []
        # processed_tower_ids = set() # Track which tower IDs we've already processed # REMOVE THIS LINE

        for tower in self.towers:
            # Skip if we've already processed this tower # REMOVE THIS BLOCK
            # if tower.tower_id in processed_tower_ids:
            #     continue
            # processed_tower_ids.add(tower.tower_id)
            
            # Check if the tower has a special block
            if tower.special:
                effect_type = tower.special.get('effect')
                is_standard_aura = (tower.attack_type == 'aura' or tower.attack_type == 'hybrid')
                is_dot_amp_aura = effect_type == 'dot_amplification_aura'
                is_attack_speed_aura = effect_type == 'adjacency_attack_speed_buff' # <<< ADDED CHECK FOR ADJACENCY BUFF
                
                # Process if it's a standard buff aura OR the DoT amp aura OR the attack speed aura
                # MODIFIED CONDITION: Include 'adjacency_attack_speed_buff' here
                if is_standard_aura or is_dot_amp_aura or is_attack_speed_aura:
                # --- END MODIFICATION ---
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
                            #print(f"DEBUG: Added {tower.tower_id} (dot_amp_aura) to tower_buff_auras with radius {aura_radius_pixels:.1f}px")
                            pass

        # --- BEGIN Adjacency Buff Calculation ---
        # This section already correctly processes individual towers (Police HQ)
        # No change needed here, it adds entries for each HQ affecting neighbors
        hq_towers = [t for t in self.towers if t.tower_id == 'police_hq']
        if hq_towers: # Only do checks if there's at least one HQ
            # towers_already_buffed_by_hq = set() # Prevent double-buffing from multiple HQs # REMOVE THIS LINE
            
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
                    # if other_tower == hq or other_tower in towers_already_buffed_by_hq: # REMOVE THIS CHECK
                    if other_tower == hq:
                        continue # Skip self
                        
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
                        # Additional check to ensure towers only share an edge, not just a corner
                        shares_edge = (
                            # Tower is directly to the left or right of HQ
                            (other_end_x == adj_min_x or other_start_x == adj_max_x) and
                            (other_end_y >= hq_start_y and other_start_y <= hq_end_y)
                        ) or (
                            # Tower is directly above or below HQ
                            (other_end_y == adj_min_y or other_start_y == adj_max_y) and
                            (other_end_x >= hq_start_x and other_start_x <= hq_end_x)
                        )
                        
                        print(f"DEBUG: Checking tower {other_tower.tower_id} at ({other_tower.center_grid_x},{other_tower.center_grid_y})")
                        print(f"  HQ bounds: ({hq_start_x},{hq_start_y}) to ({hq_end_x},{hq_end_y})")
                        print(f"  Tower bounds: ({other_start_x},{other_start_y}) to ({other_end_x},{other_end_y})")
                        print(f"  Adjacency area: ({adj_min_x},{adj_min_y}) to ({adj_max_x},{adj_max_y})")
                        print(f"  Is adjacent: {is_adjacent}")
                        print(f"  Shares edge: {shares_edge}")
                        
                        if shares_edge:
                            # Ensure the HQ special targets towers
                            if hq.special and hq.special.get('effect') == 'adjacency_damage_buff' and "towers" in hq.special.get('targets', []):
                                print(f"  Applying buff to {other_tower.tower_id}")
                                # Add the HQ's buff data to the list
                                self.tower_buff_auras.append({
                                    'tower': hq, # The tower providing the buff
                                    'radius_sq': 0, # Radius doesn't apply here
                                    'special': hq.special
                                })
        # --- END Adjacency Buff Calculation --- 

        # --- BEGIN Spark Power Plant Adjacency Buff Calculation ---
        # This section also processes individual towers correctly
        # No change needed here.
        plant_towers = [t for t in self.towers if t.tower_id == 'spark_power_plant']
        if plant_towers:
            # towers_already_buffed_by_plant = set() # Prevent double-buffing from multiple plants # REMOVE THIS LINE

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
                    # if other_tower == plant or other_tower in towers_already_buffed_by_plant: # REMOVE THIS CHECK
                    if other_tower == plant:
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
                            #print(f"DEBUG: Power Plant at ({plant.center_grid_x},{plant.center_grid_y}) applying adjacency buff to {other_tower.tower_id} at ({other_tower.center_grid_x},{other_tower.center_grid_y})")
                            pass
                            # Add the plant's buff data to the list
                            self.tower_buff_auras.append({
                                'tower': plant,
                                'radius_sq': 0,
                                'special': plant.special
                            })
                            # towers_already_buffed_by_plant.add(other_tower) # REMOVE THIS LINE
        # --- END Spark Power Plant Adjacency Buff Calculation ---

        # --- Pre-calculate Enemy Aura Towers (Affecting Enemies) --- 
        enemy_aura_towers = []
        for tower in self.towers:
            # Check if the tower has a special block and an aura radius
            if tower.special and tower.special.get('aura_radius', 0) > 0:
                effect_type = tower.special.get('effect')
                # Skip dot_amplification_aura as it affects towers, not enemies
                if effect_type == 'dot_amplification_aura':
                    continue
                    
                is_pulse_aura = effect_type and effect_type.endswith('_pulse_aura')
                is_continuous_aura = tower.attack_type in ['aura', 'hybrid']
                
                # Consider it if it's a standard continuous aura OR a pulse aura OR radiance_aura
                if is_continuous_aura or is_pulse_aura or effect_type == 'radiance_aura':
                    aura_targets = tower.special.get('targets', []) # Pulse auras might still define targets
                    # Check if the targets list contains enemy types or the old "enemies" string
                    # Ensure the aura isn't targeting towers (handled above in tower_buff_auras)
                    targets_enemies = any(t in ["ground", "air", "enemies"] for t in aura_targets) or aura_targets == "enemies"
                    targets_towers = "towers" in aura_targets or aura_targets == "towers" # Check specifically
                    
                    # Include if it targets enemies and NOT exclusively towers
                    if targets_enemies and not targets_towers:
                        aura_radius_units = tower.special.get('aura_radius', 0)
                        aura_radius_pixels = aura_radius_units * (config.GRID_SIZE / 200.0)
                        aura_radius_sq = aura_radius_pixels ** 2
                        enemy_aura_towers.append({
                            'tower': tower,
                            'radius_sq': aura_radius_sq,
                            'special': tower.special
                        })
                        # Debug print to confirm inclusion
                        #print(f"DEBUG: Included {tower.tower_id} (Type: {tower.attack_type}, Effect: {effect_type}) in enemy_aura_towers.")
                        pass

        
        # --- NEW: Process Tower-Targeting PULSE Auras --- 
        pulse_aura_towers = [
            t for t in self.towers 
            if t.special and 
            t.special.get("effect") == "crit_damage_pulse_aura" and # Or other pulse effects targeting towers
            "towers" in t.special.get("targets", [])
        ]
        
        for pulse_tower in pulse_aura_towers:
            special = pulse_tower.special
            interval = special.get("interval", 1.0)
            duration = special.get("duration", 1.0)
            crit_bonus = special.get("crit_multiplier_bonus", 0.0)
            aura_radius_sq = pulse_tower.aura_radius_pixels ** 2
            
            # Check if it's time to pulse
            if current_time >= pulse_tower.last_pulse_time + interval:
                pulse_tower.last_pulse_time = current_time # Update last pulse time
                #print(f"--- Tower {pulse_tower.tower_id} pulsing crit damage buff! ---")

                # <<< ADDED: Create Visual Pulse Effect for Tower Buff Auras >>>
                try:
                    # Use the pre-calculated aura_radius_pixels if available
                    if hasattr(pulse_tower, 'aura_radius_pixels'):
                        pulse_radius_pixels = pulse_tower.aura_radius_pixels
                    else: # Fallback: Calculate from special data if needed
                        aura_radius_units = special.get('aura_radius', 0)
                        pulse_radius_pixels = aura_radius_units * (config.GRID_SIZE / 200.0) 
                        
                    pulse_color = (255, 0, 0, 100) # Faint RED (RGBA)
                    pulse_duration = 0.5 # seconds
                    pulse_effect = ExpandingCircleEffect(pulse_tower.x, pulse_tower.y, 
                                                         pulse_radius_pixels, 
                                                         pulse_duration, 
                                                         pulse_color, thickness=2)
                    self.effects.append(pulse_effect)
                except NameError: # Catch if ExpandingCircleEffect wasn't imported
                    print("ERROR: ExpandingCircleEffect class not found. Please ensure it's defined and imported.")
                except Exception as e:
                    print(f"Error creating {pulse_tower.tower_id} pulse effect: {e}")
                # <<< END Added Visual Effect >>>

                # Find target towers within range
                targets_found = 0
                for target_tower in self.towers:
                    if target_tower == pulse_tower: continue # Don't buff self
                    
                    dist_sq = (target_tower.x - pulse_tower.x)**2 + (target_tower.y - pulse_tower.y)**2
                    if dist_sq <= aura_radius_sq:
                        # Apply the temporary buff
                        target_tower.apply_pulsed_buff('crit_damage', crit_bonus, duration, current_time)
                        targets_found += 1
                        #print(f"    -> Applied pulsed crit buff (+{crit_bonus}) to {target_tower.tower_id}")
                        pass
                
                if targets_found > 0:
                    #print(f"--- Pulse buff applied to {targets_found} towers. ---")
                    pass
        # --- END Tower Pulse Aura Processing ---
        
        # --- Update Towers --- 
        for tower in self.towers:
            # --- Call Tower's Internal Update (for self-managed abilities) --- 
            # Pass current time, enemies, ALL callbacks, and the image loader
            tower.update(current_time, self.enemies, 
                         self.add_pass_through_exploder, # Callback 1
                         self.add_visual_effect,          # Callback 2
                         self.can_afford,                 # Callback 3 
                         self.deduct_money,               # Callback 4 
                         self.add_projectile,             # Callback 5 (NEW)
                         self.load_single_image,          # Asset Loader
                         self.towers)                     # All towers list
            # ------------------------------------------------------------------
            
            # Calculate buffed stats once per tower update
            # Note: get_buffed_stats itself needs the list of auras
            # Pass current_time and self.towers along with auras
            buffed_stats = tower.get_buffed_stats(current_time, self.tower_buff_auras, self.towers) # Buffs influence interval/damage
            effective_interval = buffed_stats['attack_interval'] # Use the buffed interval
            
            # --- Gold Generation Check (Modified for Random) --- 
            if tower.special:
                effect_type = tower.special.get("effect")
                amount = 0 # Initialize amount
                interval = tower.special.get("interval", 10.0) 
                
                if current_time - tower.last_pulse_time >= interval:
                    if effect_type == "random_gold_generation":
                        min_gold = tower.special.get("min_gold", 1)
                        max_gold = tower.special.get("max_gold", 1)
                        amount = random.randint(min_gold, max_gold) # Generate random amount
                    elif effect_type == "gold_generation":
                        amount = tower.special.get("amount", 0) # Get fixed amount
                    
                    if amount > 0:
                        self.money += amount
                        self.tower_selector.update_money(self.money)
                        #print(f"Tower {tower.tower_id} generated ${amount}. Current Money: ${self.money}")
                        
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
                            #print(f"Error creating gold text effect: {e}")
                            pass
                            
                    # Update pulse time ONLY if the interval check passed
                    tower.last_pulse_time = current_time 
            # --- End Gold Generation --- 
            
            # --- Specific Broadside Firing Logic --- 
            is_broadside = tower.special and tower.special.get("effect") == "broadside"
            if is_broadside:
                if current_time - tower.last_attack_time >= effective_interval:
                    # Check if there are any enemies within range before firing
                    enemies_in_range = False
                    for enemy in self.enemies:
                        if enemy.health > 0 and enemy.type in tower.targets:
                            if tower.is_in_range(enemy.x, enemy.y):
                                enemies_in_range = True
                                break
                    
                    # Only fire if enemies are in range
                    if enemies_in_range:
                        #print(f"DEBUG: Broadside tower {tower.tower_id} firing based on interval with enemies in range.")
                        grid_offset_x = 0  # Grid starts at left edge to fill space
                        grid_offset_y = config.UI_PANEL_PADDING
                        # Capture and process results for broadside
                        # Pass self.towers for potential adjacency checks within attack
                        attack_results = tower.attack(None, current_time, self.enemies, self.tower_buff_auras, grid_offset_x, grid_offset_y, all_towers=self.towers) 
                        if isinstance(attack_results, dict):
                            new_projectiles = attack_results.get('projectiles', [])
                            if new_projectiles:
                                self.projectiles.extend(new_projectiles)
                                #print(f"Added {len(new_projectiles)} broadside projectiles.")
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
                # target_selection_mode = tower.tower_data.get("target_selection", "closest") # Old logic

                if tower.attack_type == 'beam': # Indentation Level 2 (16 spaces)
                    # Beam logic remains the same: target closest up to max_targets
                    if tower.tower_data.get("target_priority") == "current" and tower.beam_targets:
                        # Keep current targets if they're still valid
                        valid_current_targets = []
                        for target in tower.beam_targets:
                            if target.health > 0 and tower.is_in_range(target.x, target.y):
                                valid_current_targets.append(target)
                        if valid_current_targets:
                            tower.beam_targets = valid_current_targets
                            current_primary_target = valid_current_targets[0]
                        else:
                            # If no valid current targets, fall back to closest targeting
                            potential_targets.sort(key=lambda e: (e.x - tower.x)**2 + (e.y - tower.y)**2)
                            actual_targets = potential_targets[:tower.beam_max_targets]
                            tower.beam_targets = actual_targets
                            current_primary_target = actual_targets[0] if actual_targets else None
                    else:
                        # Default beam targeting behavior
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
                                    #print(f"DEBUG: Started looping beam sound for {tower.tower_id}")
                                except pygame.error as e:
                                    #print(f"Error playing beam sound for {tower.tower_id}: {e}")
                                    pass
                        else: # Beam is inactive (no targets)
                            if tower.is_beam_sound_playing:
                                tower.attack_sound.stop()
                                tower.is_beam_sound_playing = False
                                #print(f"DEBUG: Stopped looping beam sound for {tower.tower_id}")
                    # --- END Beam Sound Management ---

                    # --- Laser Painter Target Tracking ---
                    is_painter = tower.special and tower.special.get('effect') == 'laser_painter'
                    if is_painter: # Indentation Level 3 (20 spaces)
                        if current_primary_target != tower.painting_target:
                            # Target changed or lost
                            if current_primary_target: # Indentation Level 4 (24 spaces)
                                #print(f"Laser Painter {tower.tower_id} started painting {current_primary_target.enemy_id}")
                                tower.paint_start_time = current_time # Reset timer for new target
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
                            #print(f"Pyromaniac starting flame effect on {target_for_effect.enemy_id}")
                            flame_effect = FlamethrowerParticleEffect(tower, target_for_effect)
                            self.effects.append(flame_effect)
                            tower.active_flame_effect = flame_effect
                        elif not target_for_effect and tower.active_flame_effect:
                            # Target lost, stop spawning
                            #print(f"Pyromaniac lost target, stopping flame effect spawning.")
                            tower.active_flame_effect.stop_spawning()
                            tower.active_flame_effect = None # Remove reference
                        elif target_for_effect and tower.active_flame_effect and \
                             target_for_effect != tower.active_flame_effect.target_enemy:
                            # Target changed, stop old effect, start new one
                            #print(f"Pyromaniac changed target, restarting flame effect on {target_for_effect.enemy_id}")
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
                            #print(f"Acid Spewer starting effect on {target_for_effect.enemy_id}")
                            acid_effect = AcidSpewParticleEffect(tower, target_for_effect)
                            self.effects.append(acid_effect)
                            tower.active_acid_effect = acid_effect
                        elif not target_for_effect and tower.active_acid_effect:
                            # Target lost, stop spawning
                            #print(f"Acid Spewer lost target, stopping effect spawning.")
                            tower.active_acid_effect.stop_spawning()
                            tower.active_acid_effect = None # Remove reference
                        elif target_for_effect and tower.active_acid_effect and \
                             target_for_effect != tower.active_acid_effect.target_enemy:
                            # Target changed, stop old effect, start new one
                            #print(f"Acid Spewer changed target, restarting effect on {target_for_effect.enemy_id}")
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
                            #print(f"Void Leecher starting drain effect from {target_for_effect.enemy_id}")
                            drain_effect = DrainParticleEffect(tower, target_for_effect)
                            self.effects.append(drain_effect)
                            tower.active_drain_effect = drain_effect
                        elif not target_for_effect and tower.active_drain_effect:
                            # Target lost, stop spawning drain particles
                            #print(f"Void Leecher lost target, stopping drain effect spawning.")
                            tower.active_drain_effect.stop_spawning()
                            tower.active_drain_effect = None # Remove reference
                        elif target_for_effect and tower.active_drain_effect and \
                             target_for_effect != tower.active_drain_effect.target_enemy:
                            # Target changed, stop old drain effect, start new one
                            #print(f"Void Leecher changed target, restarting drain effect from {target_for_effect.enemy_id}")
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
                        if current_time >= tower.last_attack_time + effective_interval:
                            effects_applied_this_tick = False # Flag to update attack time once
                            for target_enemy in tower.beam_targets:
                                if target_enemy.health > 0:
                                    # --- Apply Damage (Logic moved from draw) ---
                                    # Check if painter and charged
                                    apply_damage_now = False
                                    if is_painter:
                                        if target_enemy == tower.painting_target and tower.paint_start_time > 0 and \
                                           (current_time - tower.paint_start_time >= tower.special.get('charge_duration', 2.0)):
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
                                        #print(f"Beam tower {tower.tower_id} dealt {damage:.2f} {tower.damage_type} damage to {target_enemy.enemy_id}")
                                        effects_applied_this_tick = True
                                    # --- End Apply Damage ---
                                    
                                    # --- Apply Slow Effect --- 
                                    if tower.special and tower.special.get('effect') == 'slow':
                                        slow_percentage = tower.special.get('slow_percentage', 0)
                                        if slow_percentage > 0:
                                            # Calculate slow multiplier (e.g., 50% slow means 0.5x speed)
                                            slow_multiplier = 1.0 - (slow_percentage / 100.0)
                                            # Use a small fixed duration for beam attacks
                                            fixed_slow_duration = 0.2
                                            target_enemy.apply_status_effect('slow', fixed_slow_duration, slow_multiplier, current_time)
                                            effects_applied_this_tick = True
                                    # --- End Apply Slow ---
                                    
                                    # Add other beam effects here (e.g., DoTs if beams can apply them per tick)
                            
                            # Update last attack time ONCE if any effect/damage was applied this tick
                            if effects_applied_this_tick:
                                tower.last_attack_time = current_time

                elif potential_targets: # Indentation Level 2 (16 spaces) - Non-beam tower with potential targets
                    # --- NEW: Target Priority Logic --- 
                    target_priority = tower.tower_data.get("target_priority", "closest") # Default to closest
                    
                    # Perform sorting based on priority
                    if target_priority == "highest_health":
                        potential_targets.sort(key=lambda e: getattr(e, 'health', 0), reverse=True) # Use getattr for safety
                    elif target_priority == "lowest_health":
                        potential_targets.sort(key=lambda e: getattr(e, 'health', 0)) # Use getattr for safety
                    elif target_priority == "furthest":
                        potential_targets.sort(key=lambda e: (e.x - tower.x)**2 + (e.y - tower.y)**2, reverse=True)
                    elif target_priority == "random":
                        pass # Don't sort for random, pick later
                    else: # Default is "closest"
                        potential_targets.sort(key=lambda e: (e.x - tower.x)**2 + (e.y - tower.y)**2)
                    
                    # Select the target
                    if target_priority == "random":
                        if potential_targets: # Ensure list is not empty before choosing
                            actual_targets = [random.choice(potential_targets)]
                        else:
                            actual_targets = [] # No target if list was empty
                    elif potential_targets: # If list not empty after sorting (and not random)
                        actual_targets = [potential_targets[0]] # Select the first one
                    else: # Should not happen if potential_targets was initially non-empty, but safety check
                        actual_targets = []
                    # --- END: Target Priority Logic --- 
                    
                    # --- Store target for drawing --- 
                    tower.beam_targets = actual_targets # Store selected target(s) for visual cues if needed
                # End of target selection logic for non-beam

                    # --- Attack Check and Execution for Standard/Special Towers --- 
                    # (This block remains largely the same, using the `actual_targets` list determined above)
                    interval_ready = current_time >= tower.last_attack_time + effective_interval
                    is_marking_tower = tower.special and tower.special.get("effect") == "apply_mark"
                    is_whip_tower = tower.attack_type == 'whip'

                    if interval_ready and (actual_targets or is_marking_tower or is_whip_tower):
                        target_enemy = actual_targets[0] if actual_targets else None # Get target if available

                        grid_offset_x = config.UI_PANEL_PADDING
                        grid_offset_y = config.UI_PANEL_PADDING

                        # --- Specific Handling for Tower Chain --- 
                        if tower.tower_id == 'spark_arc_tower':
                            self.attempt_chain_zap(tower, current_time, self.enemies, grid_offset_x, grid_offset_y)
                        else:
                            # --- Generic Attack Call --- 
                            # ... [visual asset prep] ...
                            visual_assets = {}
                            if hasattr(tower, 'animations') and tower.animations:
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
                            
                            attack_results = tower.attack(
                                target_enemy, 
                                current_time,
                                self.enemies,
                                self.tower_buff_auras,
                                grid_offset_x,
                                grid_offset_y,
                                visual_assets=visual_assets,
                                all_towers=self.towers
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
            
            # Special debug for miasma pillar
            if tower.tower_id == 'alchemists_miasma_pillar':
                #print(f"DEBUG: Found miasma_pillar in aura towers loop with effect_type={effect_type}")
                pass

            # Check if this aura is a pulsed type
            if effect_type and effect_type.endswith('_pulse_aura'):
                interval = special.get('interval', 1.0)
                # Check pulse timing ONCE per tower
                #print(f"PULSE-DEBUG: Tower {tower.tower_id} checking pulse timing | Current time: {current_time:.2f} | Last pulse: {tower.last_pulse_time:.2f} | Interval: {interval}")
                pass
                if current_time - tower.last_pulse_time >= interval:
                    #print(f"PULSE-DEBUG: Tower {tower.tower_id} TRIGGERING PULSE NOW!")
                    tower.last_pulse_time = current_time # Update time immediately

                    radius_sq = aura_data['radius_sq']
                    allowed_targets = special.get('targets', [])
                   
                    # --- Create Visual Pulse Effect --- 
                    try:
                        # Import math if not already imported at the top
                        pulse_radius_pixels = math.sqrt(radius_sq)
                        
                        # Set color based on tower type
                        if tower.tower_id == 'alchemists_miasma_pillar':
                            # Super bright visible green with maximum opacity
                            pulse_color = (0, 255, 0, 120)  # Fully bright green with some transparency 
                            pulse_thickness = 0  # Not used for filled circle
                            
                            pulse_duration = 0.8  # Longer duration to be more visible
                            pulse_effect = ExpandingCircleEffect(
                                tower.x, 
                                tower.y, 
                                pulse_radius_pixels, 
                                pulse_duration, 
                                pulse_color, 
                                thickness=pulse_thickness,
                                filled=True  # Use filled circle instead of outline
                            )
                            self.effects.append(pulse_effect)
                            #print(f"ULTRA-VISIBLE: Created FILLED miasma_pillar effect")
                        elif tower.tower_id == 'igloo_frost_pulse':
                            pulse_color = (0, 200, 255, 120)  # Light blue with transparency
                            pulse_thickness = 0  # Use filled circle
                            pulse_duration = 0.8  # Longer duration to be more visible
                            pulse_effect = ExpandingCircleEffect(
                                tower.x, 
                                tower.y, 
                                pulse_radius_pixels, 
                                pulse_duration, 
                                pulse_color, 
                                thickness=pulse_thickness,
                                filled=True  # Use filled circle instead of outline
                            )
                            self.effects.append(pulse_effect)
                            #print(f"PULSE-DEBUG: Created {pulse_color} pulse effect for {tower.tower_id} with radius {pulse_radius_pixels:.1f}px")
                        else:
                            pulse_color = (255, 0, 0, 100)  # Default faint red (RGBA)
                            pulse_thickness = 2  # Default thickness
                            
                            pulse_duration = 0.5  # seconds
                            pulse_effect = ExpandingCircleEffect(tower.x, tower.y, 
                                                                pulse_radius_pixels, 
                                                                pulse_duration, 
                                                                pulse_color, thickness=pulse_thickness)
                            self.effects.append(pulse_effect)
                            #print(f"PULSE-DEBUG: Created {pulse_color} pulse effect for {tower.tower_id} with radius {pulse_radius_pixels:.1f}px")
                
                    except NameError: # Catch if ExpandingCircleEffect wasn't imported
                        #print(f"ERROR: ExpandingCircleEffect class not found for {tower.tower_id}. Please ensure it's defined and imported.")
                        pass
                    except Exception as e:
                        #print(f"Error creating pulse effect for {tower.tower_id}: {e}")
                        pass
                    # --- End Visual Pulse Effect ---

                    # Now find and affect ALL valid enemies in range
                    for enemy in self.enemies: # Iterate through all current enemies
                        # --- DEBUG: Target Type & Range Pre-check ---
                        if tower.tower_id == 'igloo_frost_pulse': # Log for frost pulse
                            #print(f"FROST PULSE DEBUG: Checking {enemy.enemy_id} at distance {math.sqrt((enemy.x - tower.x)**2 + (enemy.y - tower.y)**2):.1f}px")
                            pass
                        # --- END DEBUG ---
                        
                        # Handle both array format ["ground", "air"] and string format "enemies"
                        is_valid_target = False
                        if isinstance(allowed_targets, list):
                            is_valid_target = enemy.type in allowed_targets
                        elif allowed_targets == "enemies":
                            is_valid_target = True  # "enemies" means all enemy types
                        
                        if enemy.health > 0 and is_valid_target:
                            dist_sq = (enemy.x - tower.x)**2 + (enemy.y - tower.y)**2
                            if dist_sq <= radius_sq:
                                # Apply the specific pulse effect
                                if effect_type == 'slow_pulse_aura':
                                    slow_percentage = special.get('slow_percentage', 0)
                                    duration = special.get('duration', 1.0)
                                    multiplier = 1.0 - (slow_percentage / 100.0)
                                    enemy.apply_status_effect('slow', duration, multiplier, current_time)
                                elif effect_type == 'damage_pulse_aura':
                                    pulse_damage = special.get('pulse_damage', 0)
                                    damage_type = special.get('pulse_damage_type', 'normal')
                                    enemy.take_damage(pulse_damage, damage_type)
                   

                                elif effect_type == 'stun_pulse_aura':
                                    duration = special.get('duration', 0.5)
                                    enemy.apply_status_effect('stun', duration, None, current_time)
    
                                
                                # --- NEW: Bonechill Pulse --- 
                                elif effect_type == 'bonechill_pulse_aura':
                                    duration = special.get('bonechill_duration', 3.0) # Get duration from JSON, default 3s
                                    enemy.apply_status_effect('bonechill', duration, None, current_time)
                                    # --- ADDED BONECHILL APPLICATION LOG ---
                                    print(f"$$$ BONECHILL APPLIED by {tower.tower_id} to {enemy.enemy_id} for {duration}s at {current_time:.2f}s")
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
                                    enemy.apply_dot_effect(dot_name, amplified_dot_damage, dot_interval, dot_duration, dot_damage_type, current_time)
                                    
                                    # --- CHECK FOR SLOW EFFECT IN DOT PULSE ---
                                    slow_percentage = special.get('slow_percentage', 0)
                                    if slow_percentage > 0:
                                        slow_duration = special.get('duration', 1.0)
                                        slow_multiplier = 1.0 - (slow_percentage / 100.0)
                                        enemy.apply_status_effect('slow', slow_duration, slow_multiplier, current_time)
                                    # --- END SLOW EFFECT CHECK ---
                                   
                                # --- End DoT Pulse Aura ---

        # --- Update Projectiles --- 
        newly_created_projectiles = [] # List to hold projectiles from bounces/splits etc.
        newly_created_effects = [] # List to hold effects from impacts
        
        for proj in self.projectiles[:]:
            # --- CHECK PROJECTILE TYPE ---
            is_boomerang = type(proj).__name__ == 'OffsetBoomerangProjectile'
            is_grenade = type(proj).__name__ == 'GrenadeProjectile'
            is_cluster = type(proj).__name__ == 'ClusterProjectile'
            is_harpoon = type(proj).__name__ == 'HarpoonProjectile'

            if is_boomerang:
                # --- Update Boomerang (which manages its own 'finished' state) ---
                proj.update(time_delta, self.enemies) # Boomerang update handles collisions and state changes internally
                if proj.finished:
                    try:
                        self.projectiles.remove(proj)
                        # print("Boomerang finished, removed.") # Optional DEBUG
                    except ValueError:
                        print("Warning: Tried to remove finished boomerang that was already removed?")
            elif is_grenade:
                # --- Update Grenade (which handles its own collisions and detonation) ---
                proj.move(time_delta, self.enemies, self.towers)
                if proj.has_detonated:
                    # Get explosion result
                    explosion_result = proj.detonate(self.enemies)
                    # Add any new effects
                    if explosion_result.get('new_effects'):
                        newly_created_effects.extend(explosion_result['new_effects'])
                    # Remove the grenade
                    self.projectiles.remove(proj)
            elif is_cluster:
                # --- Update Cluster Projectile ---
                proj.move(time_delta, self.enemies)
                if proj.has_detonated:
                    # Get detonation result
                    detonation_result = proj.detonate(self.enemies)
                    # Add any new projectiles
                    if detonation_result.get('projectiles'):
                        newly_created_projectiles.extend(detonation_result['projectiles'])
                    # Add any new effects
                    if detonation_result.get('new_effects'):
                        newly_created_effects.extend(detonation_result['new_effects'])
                    # Remove the cluster projectile
                    self.projectiles.remove(proj)
            elif is_harpoon:
                # --- Update Harpoon Projectile ---
                # HarpoonProjectile has its own update logic
                if hasattr(proj, 'update'):
                    proj.update(time_delta, current_time)
                if hasattr(proj, 'collided') and proj.collided:
                    self.projectiles.remove(proj)
            else:
                # --- Standard Projectile Update ---
                # Check if projectile is a Projectile instance with lingering capability
                is_standard_projectile = isinstance(proj, Projectile)
                
                # Check if projectile is lingering (collided but still visible)
                # Only Projectile instances have the is_lingering attribute
                if is_standard_projectile and hasattr(proj, 'is_lingering') and proj.is_lingering:
                    # Update linger timer
                    still_lingering = proj.update_linger(time_delta)
                    if not still_lingering:
                        # Linger timer expired, remove the projectile
                        self.projectiles.remove(proj)
                else:
                    # Normal projectile movement
                    if is_standard_projectile:
                        proj.move(time_delta, self.enemies)
                        if proj.collided:
                            # Get collision results
                            collision_result = proj.on_collision(self.enemies, current_time, self.tower_buff_auras)
                            # Add any new projectiles
                            if collision_result.get('new_projectiles'):
                                newly_created_projectiles.extend(collision_result['new_projectiles'])
                            # Add any new effects
                            if collision_result.get('new_effects'):
                                newly_created_effects.extend(collision_result['new_effects'])
                            # Check if projectile should linger (e.g., alien_prober)
                            # Only Projectile instances can linger
                            if hasattr(proj, 'is_lingering') and not proj.is_lingering:
                                # Remove the projectile immediately if not lingering
                                self.projectiles.remove(proj)
                    else:
                        # Handle other projectile types (HarpoonProjectile, etc.)
                        # These have their own update logic
                        if hasattr(proj, 'move'):
                            proj.move(time_delta, self.enemies)
                        if hasattr(proj, 'collided') and proj.collided:
                            self.projectiles.remove(proj)

        # Add any newly created items to the main lists AFTER iterating
        if newly_created_projectiles:
            self.projectiles.extend(newly_created_projectiles)
            # print(f"Added {len(newly_created_projectiles)} new projectiles to main list.")
        if newly_created_effects:
            self.effects.extend(newly_created_effects)
            # print(f"Added {len(newly_created_effects)} new effects to main list.")

        # --- Update Visual Effects ---
        for effect in self.effects[:]:  # Use a slice copy for safe removal
            try:
                # Call update() and check if effect is finished
                if hasattr(effect, 'update') and callable(effect.update):
                    if isinstance(effect, GroundEffectZone):
                        if effect.update(time_delta, self.enemies):
                            self.effects.remove(effect)
                    else:
                        if effect.update(time_delta):
                            self.effects.remove(effect)
                elif hasattr(effect, 'finished') and effect.finished:
                    self.effects.remove(effect)
            except Exception as e:
                print(f"Error updating effect: {e}")
                try:
                    self.effects.remove(effect)  # Remove problematic effect
                except ValueError:
                    pass  # Already removed
        # --- End Update Visual Effects ---

        # --- Update Status Visualizers --- <<< ADDED BLOCK
        for viz in self.status_visualizers[:]: # Iterate copy for potential removal if tower is gone
            if viz.tower in self.towers: # Check if the tower still exists
                viz.update(current_time)
            else: # Tower was likely sold or removed
                self.status_visualizers.remove(viz)
        # --- End Update Status Visualizers --- 

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
            should_remove = exploder.update(time_delta, self.enemies, current_time_seconds)
            if should_remove:
                # update returns True when max distance is reached and explosion is done
                self.pass_through_exploders.remove(exploder)
        # --- End Pass-Through Exploder Update ---

        # --- Update GROUND Effects (Like Fallout Zone) --- 
        # This section can be removed since we now handle GroundEffectZone in the main loop
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
                            #print(f"DEBUG: Applied aura reduction {reduction_amount} from {aura_tower.tower_id} to {enemy.enemy_id}. Current total: {enemy.aura_armor_reduction}") # Optional Debug
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
                                    
                            elif effect_type == 'radiance_aura': # Handle Sun King's Radiance
                                dot_damage = special.get('dot_damage', 0)
                                dot_interval = special.get('dot_interval', 1.0)
                                if dot_interval > 0:
                                    damage_per_sec = dot_damage / dot_interval
                                    damage_this_frame = damage_per_sec * time_delta
                                    damage_type = special.get('dot_damage_type', 'fire') # Use fire as default for radiance
                                    enemy.take_damage(damage_this_frame, damage_type)

                            elif effect_type == 'slow_aura':
                                slow_percentage = special.get('slow_percentage', 0)
                                multiplier = 1.0 - (slow_percentage / 100.0)
                                enemy.apply_status_effect('slow', time_delta * 1.5, multiplier, current_time)
                                
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
                                    enemy.apply_status_effect('slow', time_delta * 1.5, multiplier, current_time)
                                    
                            # --- NEW: Vortex Damage Aura --- 
                            elif effect_type == 'vortex_damage_aura':
                                tick_interval = special.get('tick_interval', 0.1) 
                                # Check interval using the tower's last_aura_tick_time
                                if current_time >= tower.last_aura_tick_time + tick_interval:
                                    # Update tick time ONCE per tower, after interval check
                                    tower.last_aura_tick_time = current_time 
                                    # Get damage parameters
                                    min_dmg = special.get('min_damage_at_edge', 0)
                                    max_dmg = special.get('max_damage_at_center', 0)
                                    damage_type = special.get('damage_type', 'arcane')
                                    aura_radius = special.get('aura_radius', 0) # Radius in abstract units
                                    
                                    # Calculate radius squared in pixels
                                    radius_scale_factor = config.GRID_SIZE / 200.0
                                    aura_radius_pixels = aura_radius * radius_scale_factor
                                    aura_radius_pixels_sq = aura_radius_pixels ** 2

                                    # Calculate distance squared (already have dist_sq from outer loop)
                                    # dist_sq = (enemy.x - tower.x)**2 + (enemy.y - tower.y)**2
                                    
                                    if aura_radius_pixels > 0: # Avoid division by zero if radius is 0
                                        # Calculate normalized distance (0 at center, 1 at edge)
                                        normalized_distance = math.sqrt(dist_sq) / aura_radius_pixels
                                        normalized_distance = max(0.0, min(1.0, normalized_distance)) # Clamp between 0 and 1
                                        
                                        # Calculate damage scale factor (1 at center, 0 at edge)
                                        damage_scale_factor = 1.0 - normalized_distance
                                        
                                        # Calculate damage for this tick
                                        damage_range = max_dmg - min_dmg
                                        damage_this_tick = min_dmg + (damage_range * damage_scale_factor)
                                        
                                        if damage_this_tick > 0:
                                            # print(f"DEBUG Vortex: Dist={math.sqrt(dist_sq):.1f}/{aura_radius_pixels:.1f}, NormDist={normalized_distance:.2f}, Scale={damage_scale_factor:.2f}, Dmg={damage_this_tick:.2f}") # Debug
                                            enemy.take_damage(damage_this_tick, damage_type)
                                            # Note: Need to update tower.last_aura_tick_time outside this inner enemy loop << FIXED
                            # --- END Vortex Damage Aura --- 

            # --- Move Enemy --- 
            # Enemy.move() handles status updates internally
            # Pass avg_tile_size for consistent coordinate conversion
            enemy.move(current_time, tile_size=self.avg_tile_size)
            
            # --- Continue moving towards objective midpoint if path finished ---
            # Calculate midpoint of objective area in grid-relative pixel coordinates
            objective_midpoint_x_grid = self.objective_area_x + config.OBJECTIVE_AREA_WIDTH // 2
            objective_midpoint_y_grid = self.objective_area_y + config.OBJECTIVE_AREA_HEIGHT // 2
            objective_midpoint_x = objective_midpoint_x_grid * self.avg_tile_size + (self.avg_tile_size // 2)
            objective_midpoint_y = objective_midpoint_y_grid * self.avg_tile_size + (self.avg_tile_size // 2)
            
            # If enemy has finished the path but hasn't reached the midpoint yet, continue moving
            if enemy.path_index >= len(enemy.grid_path):
                # Calculate direction to midpoint
                dx = objective_midpoint_x - enemy.x
                dy = objective_midpoint_y - enemy.y
                distance = math.sqrt(dx**2 + dy**2)
                
                if distance > 0:
                    # Move towards midpoint (enemy.speed is already in pixels per frame, no time_delta needed)
                    move_x = (dx / distance) * enemy.speed
                    move_y = (dy / distance) * enemy.speed
                    enemy.x += move_x
                    enemy.y += move_y
                    # Update rect position
                    enemy.rect.center = (int(enemy.x), int(enemy.y))
            
            # --- Check for Walkover Tower Trigger --- 
            if enemy.health > 0:
                current_grid_x = int(enemy.x // self.avg_tile_size)
                current_grid_y = int(enemy.y // self.avg_tile_size)
                
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
                                    enemy.apply_dot_effect(effect_type, amplified_dot_damage, dot_interval, dot_duration, dot_damage_type, current_time)
                                    #print(f"Enemy {enemy.enemy_id} walked over Fire Pit {tower.tower_id}, applied burn.")
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
                                    enemy.apply_dot_effect(effect_type, amplified_dot_damage, dot_interval, dot_duration, dot_damage_type, current_time)
                                    #print(f"Enemy {enemy.enemy_id} walked over Earth Spine {tower.tower_id}, applied {effect_type}.")
                                # Add other walkover effects here if needed (e.g., instant damage)
                                # elif effect_type == "walkover_damage": ... 
                                break # Stop checking towers for this enemy once triggered
            # --- End Walkover Check --- 

            # --- Objective check --- 
            # Reuse the midpoint calculation from above (already calculated before walkover check)
            # Check if enemy has reached the midpoint of the objective area
            # For Y: enemy must have reached or passed the midpoint (since enemies move top to bottom)
            # For X: enemy should be within a reasonable range of the midpoint (within half the objective width)
            x_tolerance = (config.OBJECTIVE_AREA_WIDTH * self.avg_tile_size) // 2
            has_reached_objective = (enemy.y >= objective_midpoint_y and 
                                    abs(enemy.x - objective_midpoint_x) <= x_tolerance)
            
            # If enemy has reached the midpoint, remove them
            if has_reached_objective:
                
                # --- Check for Boss Reaching Objective (Loss Condition) ---
                instant_loss = False
                game_mode = self.game.selected_wave_mode
                boss_ids_for_loss = []
                if game_mode == 'classic' or game_mode == 'plus':
                    boss_ids_for_loss = ['lord_supermaul']
                elif game_mode == 'advanced' or game_mode == 'wild':
                    boss_ids_for_loss = ['lord_supermaul', 'lord_supermaul_reborn']
                
                if enemy.enemy_id in boss_ids_for_loss:
                    #print(f"!!! BOSS LOSS CONDITION MET: {enemy.enemy_id} reached objective in {game_mode} mode.")
                    trigger_game_end(is_victory=False)
                    instant_loss = True # Game ended, stop further processing
                # --- End Boss Check ---

                if not instant_loss and self.game_state == GAME_STATE_RUNNING:
                    # Only deduct life if game hasn't ended due to boss
                    self.lives -= 1
                    # Update tower selector lives display if present
                    if hasattr(self, 'tower_selector') and self.tower_selector:
                        try:
                            self.tower_selector.update_lives(self.lives)
                        except Exception:
                            pass
                    # --- Play Life Loss Sound ---
                    if self.loss_life_sound:
                        self.loss_life_sound.play()
                    # --- End Play Sound ---
                    #print(f"*** OBJECTIVE REACHED by {enemy.enemy_id}. Decrementing wave counter from {self.enemies_alive_this_wave}...") # DEBUG
                    if self.enemies_alive_this_wave > 0: self.enemies_alive_this_wave -= 1
                    self.enemies.remove(enemy)
                    #print(f"Enemy reached objective. Lives remaining: {self.lives}")
                    #print(f"  Enemies left this wave NOW: {self.enemies_alive_this_wave}") # DEBUG
                    
                    # --- Check Lives <= 0 (Loss Condition) ---
                    if self.lives <= 0:
                        trigger_game_end(is_victory=False)
                    # --- End Lives Check ---
                elif enemy in self.enemies: # Only remove if not already removed by state change
                    # Remove enemy even if game ended, but don't process further
                    self.enemies.remove(enemy)
                    if self.enemies_alive_this_wave > 0: self.enemies_alive_this_wave -= 1 
                
                # Continue to next enemy in the loop regardless of state change this iteration
                continue # Skip death check below if enemy reached objective 
        
        # --- Remove dead enemies & Check for Win Condition--- 
        # Check remaining enemies for death AFTER objective check
        for enemy in self.enemies[:]: 
            if enemy.health <= 0: 
                
                # --- Check for Boss Defeat (Win Condition) ---
                is_win_condition_met = False
                game_mode = self.game.selected_wave_mode
                win_boss_id = None
                if game_mode == 'classic' or game_mode == 'plus':
                    win_boss_id = 'lord_supermaul'
                elif game_mode == 'advanced' or game_mode == 'wild':
                    win_boss_id = 'lord_supermaul_reborn'
                    
                if win_boss_id and enemy.enemy_id == win_boss_id:
                   #print(f"!!! WIN CONDITION MET: {enemy.enemy_id} defeated in {game_mode} mode.")
                   trigger_game_end(is_victory=True)
                   is_win_condition_met = True # Game ended
                # --- End Win Condition Check ---

                # --- Process Normal Death (If game still running) ---
                if self.game_state == GAME_STATE_RUNNING:
                    # <<< PLAY DEATH SOUND >>>
                    if self.death_sound:
                        self.death_sound.play()
                    # <<< END PLAY DEATH SOUND >>>

                    # Create blood splatter effect 
                    # Store world-space coordinates in the effect (enemy.x and enemy.y are in world space)
                    # Camera offsets will be applied when drawing each frame
                    effect_x = enemy.x
                    effect_y = enemy.y
                    if self.blood_splatter_base_image:
                        splatter = Effect(effect_x, effect_y, 
                                          self.blood_splatter_base_image,
                                          config.BLOOD_SPLATTER_FADE_DURATION, 
                                          (config.GRID_SIZE * 3, config.GRID_SIZE * 3), 
                                          hold_duration=config.BLOOD_SPLATTER_HOLD_DURATION)
                        self.effects.append(splatter)
                    
                    # Process reward/bounty 
                    reward = enemy.value
                    if hasattr(enemy, 'killed_by') and enemy.killed_by: # Simplified bounty check
                         reward = max(0, enemy.value - 1) 
                    self.money += reward
                    if hasattr(enemy, 'pending_gold_on_kill') and enemy.pending_gold_on_kill > 0:
                        self.money += enemy.pending_gold_on_kill
                    self.tower_selector.update_money(self.money)
                    
                    # Decrement wave counter and remove enemy
                    #print(f"*** ENEMY KILLED: {enemy.enemy_id}. Decrementing wave counter from {self.enemies_alive_this_wave}...")
                    if self.enemies_alive_this_wave > 0: self.enemies_alive_this_wave -= 1 
                    self.enemies.remove(enemy)
                    #print(f"Enemy {enemy.enemy_id} defeated. Gained ${reward}. Current Money: ${self.money}") 
                    #print(f"  Enemies left this wave NOW: {self.enemies_alive_this_wave}") 
                elif enemy in self.enemies: # Only remove if not already removed by state change
                    # Remove enemy even if game ended due to win, but don't process reward/effects
                    self.enemies.remove(enemy)
                    if self.enemies_alive_this_wave > 0: self.enemies_alive_this_wave -= 1 
            
    def draw(self, screen, time_delta, current_time):
        """Draw the game scene"""
        # Fill background - Cover the whole screen first
        screen.fill((0, 0, 0)) # Black background
        
        # --- Draw Lives Display (Removed from here) --- 
        
        # Draw background2.jpg (border/mountain image) for the entire screen first
        # This covers all non-playable areas
        full_screen_width = self.screen_width
        full_screen_height = self.screen_height
        if self.original_background2_image:
            # Tie background2 to world camera so it stays fixed relative to towers/grid
            scaled_background2 = pygame.transform.scale(
                self.original_background2_image,
                (full_screen_width, full_screen_height)
            )
            offset_x = -int(self.cam_x)
            offset_y = -int(self.cam_y)
            screen.blit(scaled_background2, (offset_x, offset_y))
        elif self.original_background_image:
            # Fallback: use background.jpg if background2.jpg not available
            scaled_background = pygame.transform.scale(
                self.original_background_image,
                (full_screen_width, full_screen_height)
            )
            offset_x = -int(self.cam_x)
            offset_y = -int(self.cam_y)
            screen.blit(scaled_background, (offset_x, offset_y))
        else:
            screen.fill((20, 20, 20))  # Fallback dark background
        
        # Draw background.jpg only within the playable tower area (inside white borders)
        if self.original_background_image:
            # Calculate playable area bounds (same as border calculation)
            avg_tile_size_bg = (self.actual_tile_width + self.actual_tile_height) // 2
            placeable_left = self.play_area_left - int(self.cam_x) + (config.RESTRICTED_TOWER_AREA_WIDTH * avg_tile_size_bg)
            placeable_top = self.play_area_top - int(self.cam_y) + (config.RESTRICTED_TOWER_AREA_HEIGHT * avg_tile_size_bg)
            placeable_width = config.FIXED_PLACEABLE_WIDTH_TILES * avg_tile_size_bg
            placeable_height = config.FIXED_PLACEABLE_HEIGHT_TILES * avg_tile_size_bg
            
            # Create a subsurface or clip region for the playable area
            # Scale background.jpg to cover the playable area
            scaled_playable_bg = pygame.transform.scale(
                self.original_background_image,
                (int(placeable_width), int(placeable_height))
            )
            # Draw background.jpg only in the playable area
            screen.blit(scaled_playable_bg, (int(placeable_left), int(placeable_top)))
        
        # Draw grid background (only for grid lines, restricted areas, etc.)
        # Grid must be drawn at the play area boundaries to match placement calculations
        # Grid extends to full screen width (tower selector overlays on top)
        # CRITICAL: Force right boundary to full screen width and update usable width
        self.play_area_right = int(self.screen_width)  # Force to full screen width
        # Update usable width to match full screen (minus left padding only)
        self.usable_grid_pixel_width = self.screen_width - self.play_area_left
        # Calculate grid surface width from updated boundaries - MUST extend to full screen
        grid_surface_width = self.screen_width - self.play_area_left  # Full screen minus left padding only
        # Calculate EXACT height needed to fill from play area top to play area bottom
        # Extend grid surface upward by two tiles to show top restricted area two squares higher
        avg_tile_size_for_offset = (self.actual_tile_width + self.actual_tile_height) // 2
        # Apply camera offset to grid
        grid_topleft = (self.play_area_left - int(self.cam_x), self.play_area_top - (avg_tile_size_for_offset * 2) - int(self.cam_y))
        # Grid should fill from play_area_top to play_area_bottom, plus two tiles above for top restricted area
        grid_surface_height = self.play_area_bottom - self.play_area_top + (avg_tile_size_for_offset * 2)
        # Ensure height is at least 1 pixel to avoid errors
        if grid_surface_height < 1:
            grid_surface_height = 1
        
        # Use pre-calculated actual tile sizes
        actual_tile_width = self.actual_tile_width
        actual_tile_height = self.actual_tile_height
        
        # Create grid surface for grid lines and restricted areas (transparent where not needed)
        grid_bg_surface = pygame.Surface((grid_surface_width, grid_surface_height), pygame.SRCALPHA)
        
        # Optionally draw restricted perimeter overlays (light blue). Controlled by config.DRAW_RESTRICTED_OVERLAY.
        if getattr(config, 'DRAW_RESTRICTED_OVERLAY', True):
            restricted_col_color = (120, 180, 255, 200)
            restricted_surface = pygame.Surface((grid_surface_width, grid_surface_height), pygame.SRCALPHA)
            avg_tile_size_restricted = (actual_tile_width + actual_tile_height) // 2
            # Top restricted area fill
            top_rect = pygame.Rect(0, 0, grid_surface_width, config.RESTRICTED_TOWER_AREA_HEIGHT * avg_tile_size_restricted)
            pygame.draw.rect(restricted_surface, restricted_col_color, top_rect)
            # Bottom restricted area fill (account for two-tile extension at top)
            bottom_restricted_start_y_grid = self.grid_height - config.RESTRICTED_TOWER_AREA_HEIGHT
            bottom_restricted_start_y_pixel = (bottom_restricted_start_y_grid + 2) * avg_tile_size_restricted
            bottom_rect = pygame.Rect(0, bottom_restricted_start_y_pixel, 
                                    grid_surface_width, config.RESTRICTED_TOWER_AREA_HEIGHT * avg_tile_size_restricted)
            pygame.draw.rect(restricted_surface, restricted_col_color, bottom_rect)
            # Left restricted area fill
            left_rect = pygame.Rect(0, 0, config.RESTRICTED_TOWER_AREA_WIDTH * avg_tile_size_restricted, grid_surface_height)
            pygame.draw.rect(restricted_surface, restricted_col_color, left_rect)
            # Right restricted area fill
            right_rect = pygame.Rect(grid_surface_width - config.RESTRICTED_TOWER_AREA_WIDTH * avg_tile_size_restricted, 0, config.RESTRICTED_TOWER_AREA_WIDTH * avg_tile_size_restricted, grid_surface_height)
            pygame.draw.rect(restricted_surface, restricted_col_color, right_rect)
            grid_bg_surface.blit(restricted_surface, (0, 0))

        # Draw grid lines (on grid_bg_surface) - only if show_grid is enabled
        if self.show_grid:
            # Icy blue grid lines
            icy_grid_color = (120, 180, 255)
            # Use average tile size to match placement calculations (which use avg_tile_size)
            avg_tile_size = (actual_tile_width + actual_tile_height) // 2
            int_tile_size = int(avg_tile_size)
            # Draw grid lines using the same tile size as placement calculations
            # Ensure lines extend to the full grid surface width (full screen minus left padding)
            # Note: Surface extends two tiles above the play area, so grid lines start at that offset
            grid_line_start_y = int(avg_tile_size * 2)  # Start two tiles down from top of extended surface (must be int for range)
            # Draw vertical grid lines
            for x_line in range(0, grid_surface_width + 1, int_tile_size):
                pygame.draw.line(grid_bg_surface, icy_grid_color, (x_line, 0), (x_line, grid_surface_height))
            # Draw horizontal grid lines - start from the top of the actual playable grid (one tile down)
            for y_line in range(grid_line_start_y, int(grid_surface_height) + 1, int_tile_size):
                pygame.draw.line(grid_bg_surface, icy_grid_color, (0, y_line), (grid_surface_width, y_line))
            # Draw the top edge line of the playable grid (one tile down from surface top)
            pygame.draw.line(grid_bg_surface, icy_grid_color, (0, grid_line_start_y), (grid_surface_width, grid_line_start_y))
            # Ensure final vertical line at right edge to visually extend to full screen
            if grid_surface_width > 0:
                pygame.draw.line(grid_bg_surface, icy_grid_color, (grid_surface_width - 1, 0), (grid_surface_width - 1, grid_surface_height))
        
        # Blit the completed grid surface onto the main screen at top-left (no left padding to fill space)
        # Grid should fill from top padding all the way to just above enemy preview area
        screen.blit(grid_bg_surface, grid_topleft)
        
        # --- TEMP: Draw solid border around tower-placeable area ---
        if getattr(config, 'DRAW_PLACEABLE_BORDER', False):
            try:
                avg_tile_size_border = (self.actual_tile_width + self.actual_tile_height) // 2
                placeable_left = self.play_area_left - int(self.cam_x) + (config.RESTRICTED_TOWER_AREA_WIDTH * avg_tile_size_border)
                placeable_top = self.play_area_top - int(self.cam_y) + (config.RESTRICTED_TOWER_AREA_HEIGHT * avg_tile_size_border)
                placeable_width = config.FIXED_PLACEABLE_WIDTH_TILES * avg_tile_size_border
                placeable_height = config.FIXED_PLACEABLE_HEIGHT_TILES * avg_tile_size_border
                border_rect = pygame.Rect(int(placeable_left), int(placeable_top), int(placeable_width), int(placeable_height))
                pygame.draw.rect(screen, (255, 255, 255), border_rect, 3)
            except Exception:
                pass
        
        # --- Draw markers for spawn and objective areas ---
        if getattr(config, 'DRAW_SPAWN_OBJECTIVE_MARKERS', False):
            try:
                avg_tile_size_m = (self.actual_tile_width + self.actual_tile_height) // 2
                # Spawn area marker - draw spawn.png image
                if self.spawn_image:
                    spawn_px = self.play_area_left - int(self.cam_x) + (self.spawn_area_x * avg_tile_size_m)
                    spawn_py = self.play_area_top - int(self.cam_y) + (self.spawn_area_y * avg_tile_size_m)
                    spawn_w = config.SPAWN_AREA_WIDTH * avg_tile_size_m
                    spawn_h = config.SPAWN_AREA_HEIGHT * avg_tile_size_m
                    # Scale spawn image to match spawn area size
                    scaled_spawn = pygame.transform.scale(self.spawn_image, (int(spawn_w), int(spawn_h)))
                    screen.blit(scaled_spawn, (int(spawn_px), int(spawn_py)))
                else:
                    # Fallback to colored box if image not loaded
                    spawn_px = self.play_area_left - int(self.cam_x) + (self.spawn_area_x * avg_tile_size_m)
                    spawn_py = self.play_area_top - int(self.cam_y) + (self.spawn_area_y * avg_tile_size_m)
                    spawn_w = config.SPAWN_AREA_WIDTH * avg_tile_size_m
                    spawn_h = config.SPAWN_AREA_HEIGHT * avg_tile_size_m
                    pygame.draw.rect(screen, getattr(config, 'SPAWN_MARKER_COLOR', (0,200,255)),
                                     pygame.Rect(int(spawn_px), int(spawn_py), int(spawn_w), int(spawn_h)), 0)

                # Objective area marker - draw objective.png image
                if self.objective_image:
                    obj_px = self.play_area_left - int(self.cam_x) + (self.objective_area_x * avg_tile_size_m)
                    obj_py = self.play_area_top - int(self.cam_y) + (self.objective_area_y * avg_tile_size_m)
                    obj_w = config.OBJECTIVE_AREA_WIDTH * avg_tile_size_m
                    obj_h = config.OBJECTIVE_AREA_HEIGHT * avg_tile_size_m
                    # Scale objective image to match objective area size
                    scaled_objective = pygame.transform.scale(self.objective_image, (int(obj_w), int(obj_h)))
                    screen.blit(scaled_objective, (int(obj_px), int(obj_py)))
                else:
                    # Fallback to colored box if image not loaded
                    obj_px = self.play_area_left - int(self.cam_x) + (self.objective_area_x * avg_tile_size_m)
                    obj_py = self.play_area_top - int(self.cam_y) + (self.objective_area_y * avg_tile_size_m)
                    obj_w = config.OBJECTIVE_AREA_WIDTH * avg_tile_size_m
                    obj_h = config.OBJECTIVE_AREA_HEIGHT * avg_tile_size_m
                    pygame.draw.rect(screen, getattr(config, 'OBJECTIVE_MARKER_COLOR', (255,200,0)),
                                     pygame.Rect(int(obj_px), int(obj_py), int(obj_w), int(obj_h)), 0)
            except Exception:
                pass
        
        # DEBUG: Verify grid fills correctly - uncomment to check
        # expected_bottom_y = config.UI_PANEL_PADDING + grid_surface_height
        # target_bottom_y = self.screen_height - config.ENEMY_PREVIEW_HEIGHT
        # print(f"Grid top: {grid_topleft[1]}, Grid height: {grid_surface_height}, Expected bottom: {expected_bottom_y}, Target bottom: {target_bottom_y}, Screen height: {self.screen_height}, Enemy preview: {config.ENEMY_PREVIEW_HEIGHT}")

        # Draw play area frame overlay tied to world camera as well
        if self.play_area_frame_image:
            try:
                frame_scaled = pygame.transform.scale(
                    self.play_area_frame_image,
                    (full_screen_width, full_screen_height)
                )
                offset_x = -int(self.cam_x)
                offset_y = -int(self.cam_y)
                screen.blit(frame_scaled, (offset_x, offset_y))
            except Exception:
                pass

        # --- Draw Spawn and Objective Areas (AFTER grid background is blitted) ---
        # Spawn and objective area overlays removed as requested
        # --- End Spawn/Objective Drawing ---

        # Draw towers (coordinates are relative to grid, need offset)
        # Grid is positioned at playable area boundaries
        grid_offset_x = self.play_area_left - int(self.cam_x)
        grid_offset_y = self.play_area_top - int(self.cam_y)
        for tower in self.towers:
            tower.draw(screen, self.tower_assets, grid_offset_x, grid_offset_y, 
                      actual_tile_width=self.actual_tile_width, 
                      actual_tile_height=self.actual_tile_height)
            
        # Draw enemies using EnemyAssets
        # Enemies store pixel coordinates directly, so they just need the grid offset
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
                # For regular Effect objects (like blood splatter), pass camera offsets
                # They will use stored offsets if available, or the passed offsets
                effect.draw(screen, grid_offset_x, grid_offset_y)
            
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
                                       (current_time - tower.paint_start_time >= charge_duration):
                                        print(f"Laser Painter {tower.tower_id} FIRE! Target: {target_enemy.enemy_id}")
                                        apply_effects_now = True
                                        # Reset paint time after firing to require re-charge
                                        tower.paint_start_time = 0.0 
                                else:
                                    # For non-painter towers (normal beams), effects apply every frame
                                    apply_effects_now = True
                                    
                                # Calculate buffed damage (only needed when applying effects)
                                buffed_stats = tower.get_buffed_stats(current_time, self.tower_buff_auras, self.towers) 
                                damage_multiplier = buffed_stats.get('damage_multiplier', 1.0)
                                
                                # Only apply damage if enough time has passed since last attack
                                if current_time - tower.last_attack_time >= tower.attack_interval:
                                    # Calculate and apply beam damage
                                    damage_min = tower.base_damage_min
                                    damage_max = tower.base_damage_max
                                    damage = random.uniform(damage_min, damage_max) * damage_multiplier
                                    
                                    # Apply damage to the target
                                    target_enemy.take_damage(damage, tower.damage_type)
                                    print(f"Beam tower {tower.tower_id} dealt {damage} {tower.damage_type} damage to {target_enemy.enemy_id}")
                                    
                                    # Update last attack time
                                    tower.last_attack_time = current_time
                                
                else:
                    # For non-painter towers (normal beams), effects apply every frame
                    apply_effects_now = True
                    
                    # Ensure this block is aligned correctly too
                    if apply_effects_now:
                        # Calculate buffed damage (only needed when applying effects)
                        buffed_stats = tower.get_buffed_stats(current_time, self.tower_buff_auras, self.towers) 
                        damage_multiplier = buffed_stats.get('damage_multiplier', 1.0)
                            
                # --- End Apply Damage & Effects --- 

        # Draw Tower Previews (Hover and Placement)
        if self.is_dragging and self.drag_preview_positions:
            selected_tower_id = self.tower_selector.get_selected_tower()
            if selected_tower_id:
                tower_data = self.available_towers.get(selected_tower_id)
                if tower_data:
                    grid_width = tower_data.get('grid_width', 1)
                    grid_height = tower_data.get('grid_height', 1)
                    
                    # Draw preview for each valid position
                    for grid_x, grid_y in self.drag_preview_positions:
                        is_valid_placement = self.is_valid_tower_placement(grid_x, grid_y, grid_width, grid_height)
                        
                        # Calculate preview position - center the tower on the grid cell
                        offset_x = (grid_width - 1) // 2
                        offset_y = (grid_height - 1) // 2
                        start_x = grid_x - offset_x
                        start_y = grid_y - offset_y
                        
                        # Use average tile size to maintain aspect ratio
                        avg_tile_size = (self.actual_tile_width + self.actual_tile_height) // 2
                        
                        # Convert to pixel coordinates using play area offset (grid starts at play area)
                        tower_left = self.play_area_left - int(self.cam_x) + (start_x * avg_tile_size)
                        tower_top = self.play_area_top - int(self.cam_y) + (start_y * avg_tile_size)
                        
                        # Calculate the absolute center point in pixels
                        tower_pixel_width = grid_width * avg_tile_size
                        tower_pixel_height = grid_height * avg_tile_size
                        
                        # Preview position: use snapped grid position (where tower will actually be placed)
                        # This snaps to grid squares with 20% threshold
                        preview_pixel_x = tower_left
                        preview_pixel_y = tower_top
                        
                        # Draw tower preview
                        self.tower_assets.draw_tower(screen, selected_tower_id,
                                                     preview_pixel_x, preview_pixel_y,
                                                     width=tower_pixel_width,
                                                     height=tower_pixel_height,
                                                     is_preview=False)
                        
                        # Draw colored overlay box
                        overlay_color = (0, 255, 0, 100) if is_valid_placement else (255, 0, 0, 100)
                        overlay_surface = pygame.Surface((tower_pixel_width, tower_pixel_height), pygame.SRCALPHA)
                        overlay_surface.fill(overlay_color)
                        screen.blit(overlay_surface, (preview_pixel_x, preview_pixel_y))
                        
                        # Draw outline
                        indicator_color = config.GREEN if is_valid_placement else config.RED
                        outline_rect = pygame.Rect(preview_pixel_x, preview_pixel_y, tower_pixel_width, tower_pixel_height)
                        pygame.draw.rect(screen, indicator_color, outline_rect, 2)
        elif self.tower_preview:
            grid_x, grid_y = self.tower_preview
            selected_tower_id = self.tower_selector.get_selected_tower()
            if selected_tower_id:
                tower_data = self.available_towers.get(selected_tower_id)
                if tower_data: # Level 3
                    grid_width = tower_data.get('grid_width', 1)
                    grid_height = tower_data.get('grid_height', 1)
                    
                    is_valid_placement = self.is_valid_tower_placement(grid_x, grid_y, grid_width, grid_height)

                    # --- Draw preview image at the snapped grid position (where it will actually be placed) ---
                    # Use average tile size to maintain aspect ratio
                    avg_tile_size_hover = (self.actual_tile_width + self.actual_tile_height) // 2
                    tower_pixel_width = grid_width * avg_tile_size_hover
                    tower_pixel_height = grid_height * avg_tile_size_hover
                    
                    # Calculate where the tower will actually be placed (snapped to grid)
                    offset_x = (grid_width - 1) // 2
                    offset_y = (grid_height - 1) // 2
                    start_x = grid_x - offset_x
                    start_y = grid_y - offset_y
                    
                    # Convert to pixel coordinates using play area offset with camera applied
                    tower_left = self.play_area_left - int(self.cam_x) + (start_x * avg_tile_size_hover)
                    tower_top = self.play_area_top - int(self.cam_y) + (start_y * avg_tile_size_hover)
                    
                    # Preview position: use snapped grid position (where tower will actually be placed)
                    # This snaps to grid squares with 20% threshold
                    preview_pixel_x = tower_left
                    preview_pixel_y = tower_top
                    
                    # Calculate center for range circles (use snapped position)
                    center_pixel_x = tower_left + (tower_pixel_width // 2)
                    center_pixel_y = tower_top + (tower_pixel_height // 2)
                    
                    # Draw tower preview with proper scaling to maintain aspect ratio
                    self.tower_assets.draw_tower(screen, selected_tower_id,
                                              preview_pixel_x, preview_pixel_y,
                                              width=tower_pixel_width,
                                              height=tower_pixel_height,
                                              is_preview=False)  # Use normal draw with scaling
                    
                    # Draw colored overlay to indicate valid/invalid placement
                    overlay_color = (0, 255, 0, 100) if is_valid_placement else (255, 0, 0, 100)  # Green or red with transparency
                    overlay_surface = pygame.Surface((tower_pixel_width, tower_pixel_height), pygame.SRCALPHA)
                    overlay_surface.fill(overlay_color)
                    screen.blit(overlay_surface, (preview_pixel_x, preview_pixel_y))
                    
                    # Draw cell outline box at the SAME position as preview image (snapped to grid)
                    indicator_color = config.GREEN if is_valid_placement else config.RED
                    outline_rect = pygame.Rect(preview_pixel_x, preview_pixel_y, tower_pixel_width, tower_pixel_height)
                    pygame.draw.rect(screen, indicator_color, outline_rect, 2)
        
        # --- Draw Console Overlay ---
        if self.console_active:
            overlay_height = 40
            overlay_surface = pygame.Surface((self.screen_width, overlay_height), pygame.SRCALPHA)
            overlay_surface.fill((0, 0, 0, 180))
            screen.blit(overlay_surface, (0, 0))
            # Render input text
            try:
                font = pygame.font.Font(None, 28)
            except Exception:
                font = pygame.font.SysFont(None, 28)
            display_text = "> " + self.console_text
            text_surf = font.render(display_text, True, (255, 255, 255))
            screen.blit(text_surf, (10, 8))
        
        # --- Draw Coordinates Display Near Cursor ---
        if self.show_coordinates:
            try:
                coord_font = pygame.font.Font(None, 20)
            except Exception:
                coord_font = pygame.font.SysFont(None, 20)
            
            mouse_x, mouse_y = pygame.mouse.get_pos()
            
            # Calculate grid coordinates if within grid area
            grid_offset_x = self.play_area_left
            grid_offset_y = self.play_area_top
            if (grid_offset_x <= mouse_x < grid_offset_x + self.usable_grid_pixel_width and
                grid_offset_y <= mouse_y < grid_offset_y + self.usable_grid_pixel_height):
                avg_tile_size = (self.actual_tile_width + self.actual_tile_height) // 2
                rel_x = mouse_x - grid_offset_x
                rel_y = mouse_y - grid_offset_y
                grid_x = (rel_x + (avg_tile_size // 2)) // avg_tile_size
                grid_y = (rel_y + (avg_tile_size // 2)) // avg_tile_size
                coords_text = f"Screen: ({mouse_x}, {mouse_y}) | Grid: ({grid_x}, {grid_y})"
            else:
                coords_text = f"Screen: ({mouse_x}, {mouse_y})"
            
            # Position text near cursor (offset to avoid covering it)
            text_surf = coord_font.render(coords_text, True, (255, 255, 0))  # Yellow text
            # Draw background for readability
            bg_rect = text_surf.get_rect()
            bg_rect.x = mouse_x + 15
            bg_rect.y = mouse_y + 15
            bg_surface = pygame.Surface((bg_rect.width + 4, bg_rect.height + 4), pygame.SRCALPHA)
            bg_surface.fill((0, 0, 0, 200))
            screen.blit(bg_surface, (bg_rect.x - 2, bg_rect.y - 2))
            screen.blit(text_surf, (bg_rect.x, bg_rect.y))


        # --- Draw Enemy Preview Area Placeholder ---
        # Dark gray placeholder removed as requested
        # TODO: Draw actual enemy previews here later

        # --- Draw Countdown Timer (Delay Before Wave) ---
        if self.wave_state == WAVE_STATE_WAITING and self.timer_font:
            # Format the timer to one decimal place
            timer_text = f"Next Wave: {max(0, self.wave_timer):.1f}s"
            gold_color = (255, 215, 0) # Define gold color
            text_surface = self.timer_font.render(timer_text, True, gold_color)

            # Calculate position: Further top left of the game area
            text_rect = text_surface.get_rect(
                topleft=(config.UI_PANEL_PADDING, config.UI_PANEL_PADDING)
            )
            screen.blit(text_surface, text_rect)
        # -------------------------
        
        # --- Draw Wave Time Limit Timer (Centered at Top) ---
        if self.wave_state in [WAVE_STATE_SPAWNING, WAVE_STATE_INTERMISSION] and self.timer_font:
            remaining_seconds = max(0, int(self.wave_time_limit_timer))
            # Format timer text
            timer_text = f"{remaining_seconds}s"
            
            # Color based on remaining time
            if remaining_seconds >= 20:
                timer_color = (0, 255, 0) # Green for 20+ seconds
            elif remaining_seconds >= 10:
                timer_color = (255, 255, 0) # Yellow for 10-19 seconds
            else:
                timer_color = (255, 0, 0) # Red for <10 seconds
            
            text_surface = self.timer_font.render(timer_text, True, timer_color)
            
            # Center at the top of the screen
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, config.UI_PANEL_PADDING + 20))
            screen.blit(text_surface, text_rect)
        # -------------------------

        # --- Draw UI elements --- 
        self.ui_manager.draw_ui(screen)

        # --- Draw Lives Display (Using the dedicated method) ---
        self.draw_ui(screen)
        # --- End Lives Display ---

        # --- Draw Hovered Tower Range Indicator ---
        if self.hovered_tower:
            # Use the same grid offsets as tower drawing (accounts for camera and play area)
            grid_offset_x = self.play_area_left - int(self.cam_x)
            grid_offset_y = self.play_area_top - int(self.cam_y)
            
            # Use tower's center pixel coordinates (already calculated in world space)
            # tower.x and tower.y are the center coordinates in world space
            tower_center_x = self.hovered_tower.x + grid_offset_x
            tower_center_y = self.hovered_tower.y + grid_offset_y
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

            # --- NEW: Draw Tooltip ---
            try:
                tooltip_font = pygame.font.Font(None, 22) # Small font for tooltip
                text_color = (255, 255, 255)
                bg_color = (30, 30, 30, 200) # Dark semi-transparent background
                buff_color = (100, 255, 100) # Green for buffs
                padding = 5

                # Gather data
                tower = self.hovered_tower
                name = tower.tower_data.get('name', 'Unknown')
                # <<< Get base stats - might need adjustment if using type-specific DPS >>>
                dmg_min, dmg_max, _ = tower.get_stats_for_target("ground") 
                # dmg_min = tower.base_damage_min # Old way
                # dmg_max = tower.base_damage_max # Old way
                dmg_type = tower.damage_type
                sell_price = int(tower.cost * 0.5)

                # <<< MODIFIED: Safely calculate buffs and DPS >>>
                buff_lines = []
                calculated_dps = 0.0 # Initialize DPS
                try: # Add inner try block for buff/DPS calculation
                    buffed_stats = tower.get_buffed_stats(current_time, self.tower_buff_auras, self.towers)
                    calculated_dps = tower.get_current_dps(buffed_stats) # <<< CALL NEW DPS METHOD

                    # --- Damage Display --- 
                    # <<< ADDED: Display Aura Name if Active >>>
                    active_auras = buffed_stats.get('active_aura_names', set()) # Get the set, default empty
                    if "Adjacency Damage Buff" in active_auras:
                        buff_lines.append("  Adjacency Damage Buff")
                    elif "Damage Aura" in active_auras: # Example if we add regular damage aura later
                        buff_lines.append("  Damage Aura") 
                    # <<< END ADDED >>>
                    
                    # Calculate and display Damage Multiplier Percentage
                    base_dmg_mult = 1.0
                    current_dmg_mult = buffed_stats.get('damage_multiplier', base_dmg_mult)
                    if current_dmg_mult > base_dmg_mult:
                        buff_lines.append(f"  Damage: +{((current_dmg_mult - base_dmg_mult) * 100):.1f}%")
                    # --- End Damage Display --- 

                    # --- Attack Speed Display --- 
                    # Use getattr for base_attack_interval as it might not exist on all towers (e.g., walls)
                    base_interval = getattr(tower, 'base_attack_interval', 0) 
                    current_interval = buffed_stats.get('attack_interval', base_interval)
                    
                    # <<< ADDED: Display Aura Name if Active >>>
                    active_auras = buffed_stats.get('active_aura_names', set()) # Get the set, default empty
                    if "Attack Speed Aura" in active_auras:
                        buff_lines.append("  Attack Speed Aura")
                    # <<< ADDED: Swarm Power Check >>>
                    if "Swarm Power" in active_auras:
                        buff_lines.append("  Swarm Power")
                    # <<< END ADDED >>>
                    
                    if base_interval is not None and current_interval is not None: # Check if intervals exist
                        if base_interval > 0 and current_interval < base_interval:
                            speed_increase_percent = ((base_interval / current_interval) - 1) * 100
                            buff_lines.append(f"  Speed: +{speed_increase_percent:.1f}%")
                        elif base_interval > 0 and current_interval > base_interval:
                            # Avoid division by zero if current_interval is 0 (shouldn't happen, but safe)
                            if current_interval > 0: 
                                speed_decrease_percent = (1 - (base_interval / current_interval)) * 100
                                buff_lines.append(f"  Speed: -{speed_decrease_percent:.1f}% (Slowed)")

                    # Range (Attack Range)
                    # Calculate base range pixels safely using getattr and default
                    base_range_units = getattr(tower, 'range', 0) 
                    base_range_pixels = base_range_units * (config.GRID_SIZE / 200.0) if base_range_units else 0
                    current_range_pixels = buffed_stats.get('range_pixels', base_range_pixels)
                    if current_range_pixels > base_range_pixels:
                        buff_lines.append(f"  Range: +{(current_range_pixels - base_range_pixels):.0f}px")

                    # Crit Chance
                    base_crit_chance = getattr(tower, 'critical_chance', 0.0)
                    current_crit_chance = buffed_stats.get('crit_chance', base_crit_chance)
                    # Display if buffed OR if base is non-zero and it changed
                    if current_crit_chance != base_crit_chance: 
                         buff_lines.append(f"  Crit Chance: {current_crit_chance*100:.1f}%")

                    # Crit Multiplier
                    base_crit_mult = getattr(tower, 'critical_multiplier', 1.0)
                    current_crit_mult = buffed_stats.get('crit_multiplier', base_crit_mult)
                    if current_crit_mult != base_crit_mult:
                         buff_lines.append(f"  Crit Damage: x{current_crit_mult:.2f}")
                         
                    # <<< ADDED: Splash Radius Check >>>
                    base_splash_pixels = getattr(tower, 'splash_radius_pixels', 0) # Get base splash in pixels
                    current_splash_pixels = buffed_stats.get('splash_radius_pixels', base_splash_pixels)
                    if current_splash_pixels > base_splash_pixels:
                        buff_lines.append(f"  Splash: +{(current_splash_pixels - base_splash_pixels):.0f}px")
                    # <<< END ADDED >>>
                         
                    # --- ADDED: Specific State/Stacking Effect Checks ---
                    # Reaper Mech Bonus
                    if tower.tower_id == 'tac_reaper_mech' and hasattr(tower, 'kill_count') and tower.kill_count > 0:
                        # Assuming reaper bonus is 0.25 per kill (could read from tower.special if needed)
                        reaper_bonus = 0.25 * tower.kill_count
                        # Optional: Add max cap display if defined
                        # max_reaper_bonus = tower.special.get('total_damage', float('inf')) if tower.special else float('inf')
                        # display_bonus = min(reaper_bonus, max_reaper_bonus)
                        buff_lines.append(f"  Reaper Bonus: +{reaper_bonus:.2f} dmg")

                    # Berserk Status
                    if getattr(tower, 'is_berserk', False):
                        # Optionally show remaining duration if available?
                        # remaining_berserk = tower.berserk_end_time - current_time if hasattr(tower, 'berserk_end_time') else 0
                        # buff_lines.append(f"  Berserk Active! ({remaining_berserk:.1f}s)") 
                        buff_lines.append("  Berserk Active!")
                        
                    # Rampage Stacks (using handler)
                    if hasattr(tower, 'rampage_handler') and tower.rampage_handler:
                        current_stacks = tower.rampage_handler.get_current_stacks()
                        if current_stacks > 0:
                            bonus_damage = tower.rampage_handler.get_bonus_damage()
                            max_stacks = getattr(tower.rampage_handler, 'max_stacks', '?') # Get max stacks from handler
                            buff_lines.append(f"  Rampage: +{bonus_damage:.0f} dmg ({current_stacks}/{max_stacks} stacks)")
                            
                    # Add checks for other specific effects here...
                    # e.g., if getattr(tower, 'some_other_flag', False): buff_lines.append("  Some Other Effect Active")
                    # --- END Specific Checks ---
                         
                    # <<< ADDED: Display Aura Name if Active >>>
                    active_auras = buffed_stats.get('active_aura_names', set()) # Get the set, default empty
                    if "Adjacency Damage Buff" in active_auras:
                        buff_lines.append("  Adjacency Damage Buff")
                    elif "Damage Aura" in active_auras: # Example if we add regular damage aura later
                        buff_lines.append("  Damage Aura") 
                    # <<< END ADDED >>>
                        
                    if current_dmg_mult > base_dmg_mult:
                        buff_lines.append(f"  Damage: +{((current_dmg_mult - base_dmg_mult) * 100):.1f}%")

                    # Attack Speed (Interval)
                    # Use getattr for base_attack_interval as it might not exist on all towers (e.g., walls)
                    base_interval = getattr(tower, 'base_attack_interval', 0) 
                    current_interval = buffed_stats.get('attack_interval', base_interval)
                    
                    # <<< ADDED: Display Aura Name if Active >>>
                    active_auras = buffed_stats.get('active_aura_names', set()) # Get the set, default empty
                    if "Attack Speed Aura" in active_auras:
                        buff_lines.append("  Attack Speed Aura")
                    # <<< ADDED: Swarm Power Check >>>
                    if "Swarm Power" in active_auras:
                        buff_lines.append("  Swarm Power")
                    # <<< END ADDED >>>
                    
                    if base_interval is not None and current_interval is not None: # Check if intervals exist
                        if base_interval > 0 and current_interval < base_interval:
                            speed_increase_percent = ((base_interval / current_interval) - 1) * 100
                            buff_lines.append(f"  Speed: +{speed_increase_percent:.1f}%")
                        elif base_interval > 0 and current_interval > base_interval:
                            # Avoid division by zero if current_interval is 0 (shouldn't happen, but safe)
                            if current_interval > 0: 
                                speed_decrease_percent = (1 - (base_interval / current_interval)) * 100
                                buff_lines.append(f"  Speed: -{speed_decrease_percent:.1f}% (Slowed)")

                    # Range (Attack Range)
                    # Calculate base range pixels safely using getattr and default
                    base_range_units = getattr(tower, 'range', 0) 
                    base_range_pixels = base_range_units * (config.GRID_SIZE / 200.0) if base_range_units else 0
                    current_range_pixels = buffed_stats.get('range_pixels', base_range_pixels)
                    if current_range_pixels > base_range_pixels:
                        buff_lines.append(f"  Range: +{(current_range_pixels - base_range_pixels):.0f}px")

                    # Crit Chance
                    base_crit_chance = getattr(tower, 'critical_chance', 0.0)
                    current_crit_chance = buffed_stats.get('crit_chance', base_crit_chance)
                    # Display if buffed OR if base is non-zero and it changed
                    if current_crit_chance != base_crit_chance: 
                         buff_lines.append(f"  Crit Chance: {current_crit_chance*100:.1f}%")

                    # Crit Multiplier
                    base_crit_mult = getattr(tower, 'critical_multiplier', 1.0)
                    current_crit_mult = buffed_stats.get('crit_multiplier', base_crit_mult)
                    if current_crit_mult != base_crit_mult:
                         buff_lines.append(f"  Crit Damage: x{current_crit_mult:.2f}")
                         
                    # <<< ADDED: Splash Radius Check >>>
                    base_splash_pixels = getattr(tower, 'splash_radius_pixels', 0) # Get base splash in pixels
                    current_splash_pixels = buffed_stats.get('splash_radius_pixels', base_splash_pixels)
                    if current_splash_pixels > base_splash_pixels:
                        buff_lines.append(f"  Splash: +{(current_splash_pixels - base_splash_pixels):.0f}px")
                    # <<< END ADDED >>>
                         
                    # --- ADDED: Specific State/Stacking Effect Checks ---
                    # Reaper Mech Bonus
                    if tower.tower_id == 'tac_reaper_mech' and hasattr(tower, 'kill_count') and tower.kill_count > 0:
                        # Assuming reaper bonus is 0.25 per kill (could read from tower.special if needed)
                        reaper_bonus = 0.25 * tower.kill_count
                        # Optional: Add max cap display if defined
                        # max_reaper_bonus = tower.special.get('total_damage', float('inf')) if tower.special else float('inf')
                        # display_bonus = min(reaper_bonus, max_reaper_bonus)
                        buff_lines.append(f"  Reaper Bonus: +{reaper_bonus:.2f} dmg")

                    # Berserk Status
                    if getattr(tower, 'is_berserk', False):
                        # Optionally show remaining duration if available?
                        # remaining_berserk = tower.berserk_end_time - current_time if hasattr(tower, 'berserk_end_time') else 0
                        # buff_lines.append(f"  Berserk Active! ({remaining_berserk:.1f}s)") 
                        buff_lines.append("  Berserk Active!")
                        
                    # Rampage Stacks (using handler)
                    if hasattr(tower, 'rampage_handler') and tower.rampage_handler:
                        current_stacks = tower.rampage_handler.get_current_stacks()
                        if current_stacks > 0:
                            bonus_damage = tower.rampage_handler.get_bonus_damage()
                            max_stacks = getattr(tower.rampage_handler, 'max_stacks', '?') # Get max stacks from handler
                            buff_lines.append(f"  Rampage: +{bonus_damage:.0f} dmg ({current_stacks}/{max_stacks} stacks)")
                            
                    # Add checks for other specific effects here...
                    # e.g., if getattr(tower, 'some_other_flag', False): buff_lines.append("  Some Other Effect Active")
                    # --- END Specific Checks ---
                         
                except Exception as buff_error:
                    print(f"Error calculating buffs for tooltip: {buff_error}")
                    buff_lines.append("  Error loading buffs")
                # <<< END MODIFIED >>>


                # Format text lines
                lines = [
                    f"Name: {name}",
                    f"Damage: {dmg_min}-{dmg_max} {dmg_type}",
                    f"DPS: {calculated_dps:.1f}", # <<< ADD DPS LINE
                    f"Sell: {sell_price} G"
                ]
                
                # <<< ADDED: Kill Count Display >>>
                if hasattr(tower, 'kill_count') and tower.kill_count > 0:
                    lines.append(f"Kills: {tower.kill_count}")
                # <<< END ADDED >>>
                
                if buff_lines:
                    lines.append("Buffs:")
                    lines.extend(buff_lines)


                # Render lines and calculate size
                rendered_lines = []
                max_width = 0
                total_height = 0
                line_height = 0 

                for i, line in enumerate(lines):
                    is_buff_line = line.startswith("  ") 
                    color = buff_color if is_buff_line else text_color
                    line_surface = tooltip_font.render(line, True, color)
                    rendered_lines.append(line_surface)
                    max_width = max(max_width, line_surface.get_width())
                    if i == 0: line_height = line_surface.get_height() 

                # Ensure line_height is valid before using it
                if line_height > 0:
                    total_height = (line_height * len(lines)) + (padding * (len(lines) + 1))
                else: # Fallback if font rendering failed somehow
                    total_height = padding * (len(lines) + 1) 
                
                tooltip_width = max_width + (padding * 2)
                tooltip_height = total_height

                # Calculate position near mouse, with screen boundary checks
                mouse_x, mouse_y = pygame.mouse.get_pos()
                tooltip_x = mouse_x + 15 
                tooltip_y = mouse_y + 15 

                if tooltip_x + tooltip_width > self.screen_width:
                    tooltip_x = mouse_x - tooltip_width - 15
                if tooltip_y + tooltip_height > self.screen_height:
                    tooltip_y = mouse_y - tooltip_height - 15
                if tooltip_x < 0:
                    tooltip_x = 0
                if tooltip_y < 0:
                    tooltip_y = 0
                    
                tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
                tooltip_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
                tooltip_surface.fill(bg_color)
                screen.blit(tooltip_surface, tooltip_rect.topleft)
                
                current_y = tooltip_y + padding
                for line_surface in rendered_lines:
                    screen.blit(line_surface, (tooltip_x + padding, current_y))
                    current_y += line_surface.get_height() + padding

            except Exception as e:
                # <<< Added specific error print >>>
                print(f"Error drawing tooltip for {self.hovered_tower.tower_id if self.hovered_tower else 'None'}: {e}") 
                import traceback
                traceback.print_exc() # Print full traceback for debugging
            # --- END NEW Tooltip ---

        # --- End Hovered Range Indicator ---
        
        # Draw tower placement preview - REMOVED as it's drawn above and this causes AttributeError
        # if self.tower_preview:
        #    self.tower_preview.draw(screen, self.tower_assets, grid_offset_x, grid_offset_y)

        # Draw UI elements (Tower selector, money, lives etc.)
        self.draw_ui(screen)

        # <<< START ADDED CODE >>>
        # --- Draw Placeholder Toggle Button (Draw LAST to overlay everything) ---
        if self.toggle_off_surface and self.toggle_on_surface: # Check if surfaces exist
            surface_to_draw = self.toggle_on_surface if self.debug_toggle_state else self.toggle_off_surface
            # Calculate position based on screen width and padding
            button_rect = surface_to_draw.get_rect()
            button_rect.topright = (self.screen_width - self.toggle_padding, self.toggle_padding)
            # Update the stored rect for click detection
            self.toggle_button_rect = button_rect 
            # Draw the button
            screen.blit(surface_to_draw, button_rect)

            # <<< START ADDED CODE >>>
            # --- Draw Debug Menu if Open --- 
            # <<< MODIFIED BLOCK START >>>
            if self.debug_menu_open and self.debug_menu_font: # Check if open and font loaded
                # --- Helper function to get wave info string list ---
                def get_wave_info_lines(wave_index, label):
                    lines = [f"{label}:"]
                    if 0 <= wave_index < len(self.all_wave_data):
                        wave_data = self.all_wave_data[wave_index]
                        enemy_groups = wave_data.get('enemies', [])
                        if enemy_groups:
                            first_enemy_id = enemy_groups[0].get('type')
                            if first_enemy_id:
                                enemy_data = config.ENEMY_DATA.get(first_enemy_id)
                                if enemy_data:
                                    enemy_name = enemy_data.get('name', first_enemy_id)
                                    hp = enemy_data.get('health', '?') # Use 'health' key
                                    armor_value = enemy_data.get('armor_value', '?')
                                    armor_type = enemy_data.get('armor_type', 'unknown')
                                    enemy_type = enemy_data.get('type', 'unknown') # <<< GET ENEMY TYPE >>>
                                    speed = enemy_data.get('speed', '?') # <<< GET ENEMY SPEED >>>
                                    lines.append(f"  Name: {enemy_name}")
                                    lines.append(f"  Health: {hp}")
                                    lines.append(f"  Armor: {armor_value} ({armor_type})")
                                    lines.append(f"  Type: {enemy_type}") # <<< ADD TYPE DISPLAY >>>
                                    lines.append(f"  Speed: {speed}") # <<< ADD SPEED DISPLAY >>>
                                else:
                                    lines.append(f"  ID '{first_enemy_id}' (No Data)")
                            else:
                                lines.append("  (Invalid Group)")
                        else:
                            lines.append("  (No Enemies)")
                    elif self.wave_state == WAVE_STATE_ALL_DONE and wave_index >= len(self.all_wave_data):
                         lines.append("  All Waves Complete")
                    else: # Index out of bounds or wave data error
                         lines.append("  -")
                    return lines
                # --- End Helper ---

                # --- Re-render Surface Content --- 
                # Create or reuse the surface (adjust height)
                if self.debug_menu_surface is None or self.debug_menu_surface.get_height() != self.debug_menu_height:
                    self.debug_menu_surface = pygame.Surface((self.debug_menu_width, self.debug_menu_height))
                
                # Clear surface
                self.debug_menu_surface.fill((30, 30, 30)) # Dark gray background
                # Draw border
                pygame.draw.rect(self.debug_menu_surface, (100, 100, 100), self.debug_menu_surface.get_rect(), 1)
                
                # Basic padding and color
                padding = 5
                text_color = (220, 220, 220)
                current_y = padding

                # Draw title
                title_text = "Info"
                title_surf = self.debug_menu_font.render(title_text, True, text_color)
                self.debug_menu_surface.blit(title_surf, (padding, current_y))
                current_y += title_surf.get_height() + padding // 2
                
                # --- Get and Render Info for Next Two Waves --- 
                all_lines_to_render = []
                next_wave_index_0 = self.current_wave_index
                next_wave_index_1 = self.current_wave_index + 1
                next_wave_index_2 = self.current_wave_index + 2
                next_wave_index_3 = self.current_wave_index + 3

                all_lines_to_render.extend(get_wave_info_lines(next_wave_index_0, "Current wave:"))
                all_lines_to_render.append("") # Add a blank line for spacing
                all_lines_to_render.extend(get_wave_info_lines(next_wave_index_1, "Upcoming wave:"))
                all_lines_to_render.append("") # Add a blank line for spacing
                all_lines_to_render.extend(get_wave_info_lines(next_wave_index_2, "Future wave:"))


                # Render and draw each line
                for line_text in all_lines_to_render:
                    if current_y + self.debug_menu_font.get_height() < self.debug_menu_height - padding: # Check height bounds
                        line_surf = self.debug_menu_font.render(line_text, True, text_color)
                        self.debug_menu_surface.blit(line_surf, (padding, current_y))
                        current_y += line_surf.get_height() # Move down for next line
                    else:
                        break # Stop rendering if out of vertical space

                # --- Position and Draw the Menu --- 
                menu_rect = self.debug_menu_surface.get_rect()
                menu_rect.topleft = button_rect.bottomleft # Align top-left of menu with bottom-left of button
                menu_rect.clamp_ip(screen.get_rect()) # Clamp to screen
                self.debug_menu_rect = menu_rect # Store rect
                screen.blit(self.debug_menu_surface, menu_rect) # Draw updated surface
            
            # <<< MODIFIED BLOCK END >>>
            else:
                # Ensure menu rect is None when closed
                self.debug_menu_rect = None 
            # --- End Debug Menu Drawing ---
            # <<< END ADDED CODE >>>
            
        # --- End Placeholder Toggle Button ---
        # <<< END ADDED CODE >>>

        # Update the display
        # pygame.display.flip() # REMOVED - Main game loop should handle flip

        # --- Draw Story Overlay (If Active) ---
        if self.story_overlay_active and self.story_font and self.story_font_large:
            # Create semi-transparent grey overlay
            overlay_surface = pygame.Surface((self.screen_width, self.screen_height))
            overlay_surface.fill((50, 50, 50))  # Dark grey background
            overlay_surface.set_alpha(200)  # Semi-transparent
            screen.blit(overlay_surface, (0, 0))
            
            # Draw title
            title_text = "LORD SUPERMAUL AWAKENS!"
            title_surface = self.story_font_large.render(title_text, True, (255, 255, 150))  # Light yellow
            title_rect = title_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 100))
            screen.blit(title_surface, title_rect)
            
            # Draw story text (wrapped)
            words = self.story_text.split()
            lines = []
            current_line = []
            max_width = self.screen_width - 100  # Leave margins
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                test_surface = self.story_font.render(test_line, True, (255, 255, 150))  # Light yellow
                if test_surface.get_width() <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)  # Single word too long
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw each line
            line_height = 30
            start_y = self.screen_height // 2 - 50
            for i, line in enumerate(lines):
                line_surface = self.story_font.render(line, True, (255, 255, 150))  # Light yellow
                line_rect = line_surface.get_rect(center=(self.screen_width // 2, start_y + i * line_height))
                screen.blit(line_surface, line_rect)
            
            # Draw "Press any key to continue" text
            continue_text = "Press any key to continue..."
            continue_surface = self.story_font.render(continue_text, True, (200, 200, 100))  # Slightly dimmer yellow
            continue_rect = continue_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 150))
            screen.blit(continue_surface, continue_rect)
        # --- End Story Overlay ---

        # --- Draw Pulsing "Press Enter to begin..." Text ---
        if not self.story_overlay_active and not self.wave_started and self.pulse_font:
            # Calculate pulsing alpha based on time
            pulse_time = pygame.time.get_ticks() / 1000.0  # Convert to seconds
            pulse_alpha = int(128 + 127 * math.sin(pulse_time * 3))  # Pulsing between 128-255
            
            # Create text surface with pulsing alpha
            pulse_text = "Press Enter to begin..."
            text_surface = self.pulse_font.render(pulse_text, True, (255, 255, 150))  # Light yellow text
            
            # Center the text on screen
            text_rect = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            
            # Create a surface with alpha for the pulsing effect
            alpha_surface = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
            alpha_surface.blit(text_surface, (0, 0))
            alpha_surface.set_alpha(pulse_alpha)
            
            screen.blit(alpha_surface, text_rect)
        # --- End Pulsing Text ---

        # --- Draw Hint Message ---
        if self.hint_message_active and self.pulse_font:
            current_time = pygame.time.get_ticks() / 1000.0
            if current_time >= self.hint_message_start_time:
                # Calculate pulsing alpha for hint message
                hint_pulse_time = current_time - self.hint_message_start_time
                hint_alpha = int(128 + 127 * math.sin(hint_pulse_time * 4))  # Faster pulsing
                
                # Create hint text surface
                hint_text = "(Hint: You can press Spacebar to Pause...)"
                hint_surface = self.pulse_font.render(hint_text, True, (255, 255, 150))  # Light yellow
                
                # Center the text on screen
                hint_rect = hint_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 100))
                
                # Create a surface with alpha for the pulsing effect
                hint_alpha_surface = pygame.Surface(hint_surface.get_size(), pygame.SRCALPHA)
                hint_alpha_surface.blit(hint_surface, (0, 0))
                hint_alpha_surface.set_alpha(hint_alpha)
                
                screen.blit(hint_alpha_surface, hint_rect)
        # --- End Hint Message ---

        # --- Draw Game Over Overlay (If Applicable) ---
        if self.game_state == GAME_STATE_GAME_OVER and self.game_over_image:
            overlay_rect = self.game_over_image.get_rect(center=screen.get_rect().center)
            screen.blit(self.game_over_image, overlay_rect)
        # --- End Game Over Overlay ---

        # --- Draw Victory Overlay (If Applicable) ---
        elif self.game_state == GAME_STATE_VICTORY and self.winner_image: # <<< Use elif
            overlay_rect = self.winner_image.get_rect(center=screen.get_rect().center)
            screen.blit(self.winner_image, overlay_rect)
        # --- End Victory Overlay ---

        # --- Draw Status Visualizers (After Towers, Before Other Effects/UI?) --- <<< ADDED
        for viz in self.status_visualizers:
            viz.draw(screen, grid_offset_x, grid_offset_y)
        # --- End Draw Status Visualizers ---

        # Draw pause overlay if paused
        if self.is_paused:
            # Create semi-transparent overlay
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Black with 50% opacity
            screen.blit(overlay, (0, 0))

            # Draw "PAUSED" text
            font = pygame.font.Font(None, 72)  # Use default font, size 72
            text = font.render("PAUSED", True, (255, 255, 255))  # White text
            text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            screen.blit(text, text_rect)

    def draw_ui(self, screen):
        """Draw UI elements"""
        # Lives now display in tower selector panel; nothing to draw here
        return
        


    def is_valid_tower_placement(self, grid_x, grid_y, grid_width, grid_height):
        """Check if a tower can be placed at the given position"""
        # Ensure grid coordinates are integers for range() operations
        grid_x = int(grid_x)
        grid_y = int(grid_y)
        grid_width = int(grid_width)
        grid_height = int(grid_height)
        
        # Calculate footprint of the tower to be placed
        offset_x = (grid_width - 1) // 2
        offset_y = (grid_height - 1) // 2
        new_start_x = grid_x - offset_x
        new_end_x = new_start_x + grid_width - 1 # Corrected calculation
        new_start_y = grid_y - offset_y
        new_end_y = new_start_y + grid_height - 1 # Corrected calculation

        # --- NEW: Prevent placement in spawn area and two squares directly in front ---
        spawn_area_start_x = self.spawn_area_x
        spawn_area_end_x = self.spawn_area_x + config.SPAWN_AREA_WIDTH - 1
        spawn_area_start_y = self.spawn_area_y
        spawn_area_end_y = self.spawn_area_y + config.SPAWN_AREA_HEIGHT - 1

        # Restrict the TWO squares directly in front of spawn area (centered, like objective area)
        # These are the same X columns as the spawn area, one row below
        below_spawn_start_x = self.spawn_area_x
        below_spawn_end_x = self.spawn_area_x + config.SPAWN_AREA_WIDTH - 1
        below_spawn_start_y = self.spawn_area_y + config.SPAWN_AREA_HEIGHT
        below_spawn_end_y = below_spawn_start_y  # Only one row

        # Check overlap with spawn area
        if not (new_end_x < spawn_area_start_x or new_start_x > spawn_area_end_x or
                new_end_y < spawn_area_start_y or new_start_y > spawn_area_end_y):
            #print("Validation failed: Cannot place in spawn area.")
            return False # Overlaps with spawn area

        # Check overlap with two squares directly in front of spawn area
        if not (new_end_x < below_spawn_start_x or new_start_x > below_spawn_end_x or
                new_end_y < below_spawn_start_y or new_start_y > below_spawn_end_y):
            #print("Validation failed: Cannot place in area below spawn.")
            return False # Overlaps with area below spawn
        # --- END NEW: Prevent placement ---

        # --- NEW: Prevent placement in objective area and tiles above ---
        objective_area_start_x = self.objective_area_x
        objective_area_end_x = self.objective_area_x + config.OBJECTIVE_AREA_WIDTH - 1
        objective_area_start_y = self.objective_area_y
        objective_area_end_y = self.objective_area_y + config.OBJECTIVE_AREA_HEIGHT - 1

        above_objective_start_x = self.objective_area_x
        above_objective_end_x = self.objective_area_x + config.OBJECTIVE_AREA_WIDTH - 1
        above_objective_start_y = self.objective_area_y - 1  # One row above
        above_objective_end_y = above_objective_start_y  # Only one row

        # Check overlap with objective area
        if not (new_end_x < objective_area_start_x or new_start_x > objective_area_end_x or
                new_end_y < objective_area_start_y or new_start_y > objective_area_end_y):
            #print("Validation failed: Cannot place in objective area.")
            return False # Overlaps with objective area

        # Check overlap with tiles above objective area
        if not (new_end_x < above_objective_start_x or new_start_x > above_objective_end_x or
                new_end_y < above_objective_start_y or new_start_y > above_objective_end_y):
            #print("Validation failed: Cannot place in area above objective.")
            return False # Overlaps with area above objective
        # --- END NEW: Prevent objective placement ---


        # 1. Check Grid Bounds
        if not (0 <= new_start_x < self.grid_width and 0 <= new_end_x < self.grid_width and
                0 <= new_start_y < self.grid_height and 0 <= new_end_y < self.grid_height):
            #print("Validation failed: Outside grid bounds.")
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
                #print("Validation failed: Cannot place on existing tower.")
                return False # Found an overlap

        # 3. Check for Restricted Cells ('2') and Non-Traversable Towers ('1')
        for y in range(new_start_y, new_end_y + 1):
            for x in range(new_start_x, new_end_x + 1):
                # Check if the cell is restricted ('2')
                if self.grid[y][x] == 2:
                    #print("Validation failed: Cannot place in restricted area.")
                    return False
                # Check if the cell is occupied by a non-traversable tower ('1')
                # (This might be redundant with the overlap check above, but is safe)
                if self.grid[y][x] == 1:
                    #print("Validation failed: Cannot place on existing non-traversable tower footprint.")
                    return False

        # --- 4. Pathfinding Check ---
        # Get the tower data to check if it's traversable
        selected_tower_id = self.tower_selector.get_selected_tower() # Assumes tower is selected
        if not selected_tower_id: # Should not happen if called from placement, but safety check
            #print("Validation Error: No tower selected for pathfinding check.")
            return False
        tower_data = self.available_towers.get(selected_tower_id)
        if not tower_data:
            #print(f"Validation Error: Tower data not found for {selected_tower_id}")
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
                #print(f"Pathfinding failed: Placing non-traversable tower at ({grid_x},{grid_y}) would block the path.")
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
            #print(f"Warning: Enemy data not found for ID '{enemy_id}' in config.ENEMY_DATA. Cannot spawn.")
            return
        
        # Determine if the unit is an air unit
        is_air = enemy_data.get("type", "ground") == "air"
        
        # Get armor details based on enemy data
        armor_type_name = enemy_data.get("armor_type", "Unarmored") # Default to Unarmored if missing
        armor_details = self.armor_data.get(armor_type_name)
        if not armor_details:
            #print(f"Warning: Armor details not found for type '{armor_type_name}'. Using defaults for enemy '{enemy_id}'.")
            # Use default Unarmored modifiers if lookup fails
            default_unarmored = self.armor_data.get("Unarmored", {})
            damage_modifiers = default_unarmored.get("damage_modifiers", {"normal": 1.0}) # Absolute fallback
        else:
            damage_modifiers = armor_details.get("damage_modifiers", {"normal": 1.0})
        
        # Find path first, passing the unit type
        grid_path = find_path(self.path_start_x, self.path_start_y, 
                              self.path_end_x, self.path_end_y, self.grid,
                              is_air_unit=is_air) # Pass the flag

        if not grid_path:
            #print(f"Warning: Could not find path to spawn enemy '{enemy_id}'.")
            return

        # Create the enemy with specific data including armor
        enemy = Enemy(self.visual_spawn_x_pixel, self.visual_spawn_y_pixel, 
                      grid_path, 
                      enemy_id=enemy_id, 
                      enemy_data=enemy_data, 
                      armor_type=armor_type_name, # Pass armor name
                      damage_modifiers=damage_modifiers) # Pass modifiers dict
        self.enemies.append(enemy)
        #print(f"Spawned test enemy: {enemy_id} (Armor: {armor_type_name}) with path length {len(grid_path)}")

    def sell_tower_at(self, grid_x, grid_y):
        """Finds and sells a tower located at the given grid coordinates."""

        # --- NEW: Prevent selling during active wave ---
        if self.wave_state in [WAVE_STATE_SPAWNING, WAVE_STATE_INTERMISSION]:
            #print("Cannot sell towers during a wave.") # Optional debug
            if self.invalid_placement_sound:
                self.invalid_placement_sound.play()
            return # Stop the sell action
        # --- END Prevent selling during active wave ---

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
            #print(f"Sold {tower_to_sell.tower_id} for ${sell_value}. Current Money: ${self.money}")

            # Play sell sound
            if self.sell_sound:
                self.sell_sound.play()

            # --- Stop Beam Sound If Playing ---
            if hasattr(tower_to_sell, 'is_beam_sound_playing') and tower_to_sell.is_beam_sound_playing and tower_to_sell.attack_sound:
                tower_to_sell.attack_sound.stop()
                #print(f"DEBUG: Stopped beam sound for sold tower {tower_to_sell.tower_id}")
            # --- End Stop Beam Sound ---

            # --- NEW: Stop Looping Sound (Ogre War Drums) --- 
            if tower_to_sell.tower_id == 'ogre_war_drums':
                if hasattr(tower_to_sell, 'looping_sound_channel') and tower_to_sell.looping_sound_channel:
                    #print(f"Stopping looping sound for sold {tower_to_sell.tower_id} on channel {tower_to_sell.looping_sound_channel}")
                    tower_to_sell.looping_sound_channel.stop()
                    tower_to_sell.looping_sound_channel = None # Clear reference
            # --- END Stop Looping Sound ---

            # --- NEW: Stop Looping Sound (Goblin Shredder) --- 
            if tower_to_sell.tower_id == 'goblin_shredder':
                if hasattr(tower_to_sell, 'looping_sound_channel') and tower_to_sell.looping_sound_channel:
                    #print(f"Stopping looping sound for sold {tower_to_sell.tower_id} on channel {tower_to_sell.looping_sound_channel}")
                    tower_to_sell.looping_sound_channel.stop()
                    tower_to_sell.looping_sound_channel = None # Clear reference
            # --- END Stop Looping Sound ---

            # --- NEW: Stop Looping Sound (Bomb Barrage Beacon) --- 
            if tower_to_sell.tower_id == 'bomb_barrage_beacon':
                if hasattr(tower_to_sell, 'looping_sound_channel') and tower_to_sell.looping_sound_channel:
                    #   print(f"Stopping looping sound for sold {tower_to_sell.tower_id} on channel {tower_to_sell.looping_sound_channel}")
                    tower_to_sell.looping_sound_channel.stop()
                    tower_to_sell.looping_sound_channel = None # Clear reference
            # --- END Stop Looping Sound ---

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
                #print(f"Cleared grid cells for sold non-traversable tower {tower_to_sell.tower_id}.")
            else:
                pass
                #print(f"Skipped clearing grid cells for sold traversable tower {tower_to_sell.tower_id}.")
                        
            # Remove tower from list
            self.towers.remove(tower_to_sell)
            
            # --- Update Tower Links After Sell --- 
            self.update_tower_links()
            # --- End Link Update --- 
            
            # Potentially force enemy path recalculation if needed
            # self.recalculate_all_enemy_paths() # Add this if pathing doesn't auto-update
            
            # Update tower count
            self.tower_counts[tower_to_sell.tower_id] = max(0, self.tower_counts.get(tower_to_sell.tower_id, 0) - 1)
            
            # Update tower selector UI
            self.tower_selector.update_tower_counts(self.tower_counts)
            
        else:
            #print("No tower found at that location to sell.")
            pass
            
    def load_single_image(self, image_path):
        """Loads a single image, handling errors."""
        try:
            # Ensure path uses correct separators for the OS
            full_path = os.path.join(*image_path.split('/')) # Split by / and rejoin with os separator
            #print(f"Attempting to load single image: {full_path}") # Debug print
            image = pygame.image.load(full_path).convert_alpha()
            #print(f"  Successfully loaded: {full_path}")
            return image
        except pygame.error as e:
            #print(f"Error loading image '{full_path}': {e}")
            return None
        except FileNotFoundError:
            #print(f"Error: File not found at '{full_path}'")
            return None

    def load_armor_data(self, file_path):
        """Loads armor type data from a JSON file."""
        armor_types = {}
        if not os.path.isfile(file_path):
            #print(f"Warning: Armor data file not found: {file_path}")
            return armor_types
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            for armor in data.get("armor_types", []):
                if "name" in armor and "damage_modifiers" in armor:
                    armor_types[armor["name"]] = armor # Store the whole armor object
            #print(f"Loaded {len(armor_types)} armor types.")
        except json.JSONDecodeError as e:
            #print(f"Error decoding armor JSON file {file_path}: {e}")
            pass
        except Exception as e:
            #print(f"An unexpected error occurred loading armor data {file_path}: {e}")
            pass
        return armor_types

    def load_damage_types(self, file_path):
        """Loads damage type descriptions from the tower races JSON file."""
        damage_types = {}
        if not os.path.isfile(file_path):
            #print(f"Warning: Damage type data file not found: {file_path}")
            return damage_types
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            # Access the specific 'damagetypes' section within the JSON
            for dtype_name, dtype_data in data.get("damagetypes", {}).items():
                if "description" in dtype_data:
                    damage_types[dtype_name] = dtype_data # Store the whole dict
            #print(f"Loaded {len(damage_types)} damage types.")
        except json.JSONDecodeError as e:
            #print(f"Error decoding damage type JSON file {file_path}: {e}")
            pass
        except Exception as e:
            #print(f"An unexpected error occurred loading damage type data {file_path}: {e}")
            pass
        return damage_types

    def update_tower_links(self):
        """Calculate and update the linked_neighbors list for all Arc Towers."""
        arc_towers = [t for t in self.towers if t.tower_id == 'spark_arc_tower'] # Corrected ID
        if len(arc_towers) < 2: 
            for t in arc_towers:
                t.linked_neighbors = []
            return

        #print(f"DEBUG: Updating tower links for {len(arc_towers)} Arc Towers...") # Keep this print
        for tower1 in arc_towers:
            tower1.linked_neighbors = [] 
            link_radius_units = tower1.tower_data.get("chain_link_radius", 0)
            if link_radius_units <= 0:
                continue 
                
            link_radius_pixels = link_radius_units * (config.GRID_SIZE / 200.0)
            link_radius_sq = link_radius_pixels ** 2
            #print(f"  DEBUG: Tower1 ({tower1.center_grid_x},{tower1.center_grid_y}) LinkRadiusSq={link_radius_sq:.1f}") # Added detail
            
            for tower2 in arc_towers:
                if tower1 == tower2: 
                    continue
                
                dist_sq = (tower1.x - tower2.x)**2 + (tower1.y - tower2.y)**2
                # Enhanced Debug Print
                #print(f"    DEBUG: Check ({tower1.center_grid_x},{tower1.center_grid_y})<->({tower2.center_grid_x},{tower2.center_grid_y}) | DistSq={dist_sq:.1f} | RadiusSq={link_radius_sq:.1f} | Link? {dist_sq <= link_radius_sq}")
                
                if dist_sq <= link_radius_sq:
                    if tower2 not in tower1.linked_neighbors:
                        tower1.linked_neighbors.append(tower2)
                        # Enhanced Debug Print
                        #print(f"      DEBUG: LINK ADDED: ({tower1.center_grid_x},{tower1.center_grid_y}) -> ({tower2.center_grid_x},{tower2.center_grid_y})")
            # Print final list for tower1
            final_linked_ids = [f"({t.center_grid_x},{t.center_grid_y})" for t in tower1.linked_neighbors]
            #print(f"  DEBUG: Tower1 ({tower1.center_grid_x},{tower1.center_grid_y}) final links: {final_linked_ids}")

    def process_attack_results(self, attack_results, grid_offset_x, grid_offset_y):
        """Helper function to process the results dictionary from standard tower attacks."""
        if isinstance(attack_results, dict):
            # Handle self-destruct action
            if attack_results.get('action') == 'self_destruct':
                tower = attack_results.get('tower_instance')
                if tower:
                    # Play destruct sound if available
                    if hasattr(self, 'goblin_destruct_sound') and self.goblin_destruct_sound:
                        self.goblin_destruct_sound.play()
                    
                    # Create explosion effect
                    if self.explosion_effect_image:
                        effect = Effect(
                            tower.x + grid_offset_x,
                            tower.y + grid_offset_y,
                            self.explosion_effect_image,
                            duration=0.5,
                            target_size=(config.GRID_SIZE * 4, config.GRID_SIZE * 4)
                        )
                        self.effects.append(effect)
                    
                    # Apply damage to enemies in range
                    radius = attack_results.get('radius', 0)
                    damage = attack_results.get('damage', 0)
                    damage_type = attack_results.get('damage_type', 'normal')
                    targets = attack_results.get('targets', ['ground', 'air'])
                    
                    for enemy in self.enemies:
                        if enemy.health > 0 and enemy.type in targets:
                            dx = enemy.x - tower.x
                            dy = enemy.y - tower.y
                            dist_sq = dx*dx + dy*dy
                            if dist_sq <= radius * radius:
                                enemy.take_damage(damage, damage_type)
                    
                    # Clear grid cells before removing tower
                    if not tower.tower_data.get('traversable', False):
                        for y in range(tower.top_left_grid_y, tower.top_left_grid_y + tower.grid_height):
                            for x in range(tower.top_left_grid_x, tower.top_left_grid_x + tower.grid_width):
                                if 0 <= y < self.grid_height and 0 <= x < self.grid_width:
                                    if self.grid[y][x] == 1:  # Only clear if it was marked as tower
                                        self.grid[y][x] = 0
                    
                    # Remove the tower
                    self.towers.remove(tower)
                    return
            
            # Add any projectiles created
            new_projectiles = attack_results.get('projectiles', [])
            if new_projectiles:
                for proj in new_projectiles:
                    if isinstance(proj, PassThroughExploder):
                        # PassThroughExploders are handled by the callback, don't add them here
                        pass
                    else:
                        self.projectiles.append(proj)
            # Add any visual effects created
            new_effects = attack_results.get('effects', [])
            if new_effects:
                self.effects.extend(new_effects)
            # Handle legacy chain visual return 
            if attack_results.get("type") == "chain_visual":
                chain_path = attack_results.get("path", [])
                if len(chain_path) >= 2:
                    # Original chain visual assumed path was relative, needed offset
                    # adjusted_path = [(int(x + grid_offset_x), int(y + grid_offset_y)) for x, y in chain_path]
                    # For whip, the path is already screen-adjusted from Tower.attack
                    chain_effect = ChainLightningVisual(chain_path, duration=0.3)
                    self.effects.append(chain_effect)
            # --- NEW: Handle Whip Visual --- 
            elif attack_results.get("type") == "whip_visual":
                visual_path = attack_results.get("visual_path", [])
                duration = attack_results.get("duration", 0.2)
                if len(visual_path) >= 2: # Need at least tower pos and one target
                    # Use the NEW WhipVisual class
                    # Path coordinates are in world-space (draw will apply camera offsets)
                    whip_effect = WhipVisual(visual_path, duration=duration) # No need to specify line_type, defaults to 'whip'
                    self.effects.append(whip_effect)
            # --- END Whip Visual Handling ---

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

        #print(f"Tower ({initiating_tower.center_grid_x},{initiating_tower.center_grid_y}) attempting chain zap...") # Keep
        linked_ids = [f"({t.center_grid_x},{t.center_grid_y})" for t in initiating_tower.linked_neighbors]
        #print(f"  Initiator neighbors: {linked_ids}") # Keep

        # --- Pathfinding (DFS to find longest chain) --- 
        longest_chain = [initiating_tower] 
        stack = [(initiating_tower, [initiating_tower])] 
        max_len = 1

        while stack:
            current_node, path = stack.pop() 
            current_node_id = f"({current_node.center_grid_x},{current_node.center_grid_y})"
            path_ids = [f"({t.center_grid_x},{t.center_grid_y})" for t in path]
            #print(f"    DFS Pop: Node={current_node_id}, Path={path_ids}") # Keep

            if len(path) > max_len:
                max_len = len(path)
                longest_chain = path
                path_ids = [f"({t.center_grid_x},{t.center_grid_y})" for t in path] # Re-calculate for print
                #print(f"      DFS: New longest_chain found! Length={max_len}, Path={path_ids}") # Keep

            for neighbor in current_node.linked_neighbors:
                neighbor_id = f"({neighbor.center_grid_x},{neighbor.center_grid_y})"
                if neighbor not in path: 
                     new_path = path + [neighbor]
                     stack.append((neighbor, new_path))
                     new_path_ids = [f"({t.center_grid_x},{t.center_grid_y})" for t in new_path]
                     #print(f"        DFS Pushing: Node={neighbor_id}, Path={new_path_ids}") # Keep
        # --- End DFS --- 

        # Check if a chain longer than 1 was found
        chain_found = len(longest_chain) > 1
        end_node_tower = longest_chain[-1] if chain_found else initiating_tower

        if chain_found:
            # Correctly indent this block
            #print(f"... found chain: {[t.tower_id for t in longest_chain]}")
            # --- Target from End Node --- 
            target = None
            potential_targets = []
            for enemy in all_enemies:
                 if enemy.health > 0 and enemy.type in end_node_tower.targets and end_node_tower.is_in_range(enemy.x, enemy.y):
                     potential_targets.append(enemy)
            
            if potential_targets:
                potential_targets.sort(key=lambda e: (e.x - end_node_tower.x)**2 + (e.y - end_node_tower.y)**2)
                target = potential_targets[0]
                #print(f"... end node {end_node_tower.tower_id} targeting {target.enemy_id}")
            else:
                #print(f"... end node {end_node_tower.tower_id} found no targets in range.")
                pass

            if target:
                # --- Apply Chain Zap Damage & Effects --- 
                num_towers = len(longest_chain)
                damage_per_tower = initiating_tower.tower_data.get("chain_zap_damage_per_tower", 0)
                total_damage = num_towers * damage_per_tower
                damage_type = initiating_tower.damage_type
                
                #print(f"... ZAPPING {target.enemy_id} for {total_damage} damage ({num_towers} towers)")
                target.take_damage(total_damage, damage_type)
                
                # --- Create Chain Link Visual --- 
                tower_positions = []
                for tower in longest_chain:
                    # Use world coordinates (draw will apply camera offsets)
                    tower_positions.append((int(tower.x), int(tower.y)))
                
                if len(tower_positions) >= 2:
                    link_visual = ChainLightningVisual(tower_positions, duration=0.4, line_type='tower_link') # Use tower_link type
                    self.effects.append(link_visual)
                # --- End Chain Link Visual ---
                
                # --- Create Supercharged Zap Visual --- 
                # Use world coordinates (draw will apply camera offsets)
                start_pos = (int(end_node_tower.x), int(end_node_tower.y))
                end_pos = (int(target.x), int(target.y))
                zap_visual = SuperchargedZapEffect(start_pos, end_pos, duration=0.25, thickness=5) # Adjust duration/thickness
                self.effects.append(zap_visual)
                # --- End Supercharged Zap Visual ---
                initiating_tower_sound_object = initiating_tower.attack_sound # Get the loaded sound object
                if initiating_tower_sound_object:
                    try:
                        initiating_tower_sound_object.play() # Try playing the sound object directly
                        #print(f"Attempting to play chain zap sound for {initiating_tower.tower_id}") # Simpler debug print
                    except AttributeError as e:
                        # This error means the object doesn't have a .play() method
                        #print(f"Error: initiating_tower.attack_sound (type: {type(initiating_tower_sound_object)}) has no play() method. Problem loading sound? Error: {e}")
                        pass
                    except Exception as e:
                        # Catch any other sound playing errors
                        #print(f"Error playing sound object for {initiating_tower.tower_id}: {e}")
                        pass
                else:
                    # This means the sound object wasn't loaded correctly in Tower.__init__
                    #print(f"Warning: initiating_tower.attack_sound is None for {initiating_tower.tower_id}. Cannot play sound.")
                    pass
                # +++ END: ADD THIS CODE BLOCK +++
                # Set cooldown for ALL participating towers
                for tower in longest_chain:
                    tower.last_chain_participation_time = current_time
                    tower.last_attack_time = current_time
            else:
                # Chain formed but no target found - Fallback?
                #print("... Chain formed but no target. Initiator goes on cooldown.")
                initiating_tower.last_attack_time = current_time
        else:
            # --- Fallback to Standard Attack --- 
            #print("... no chain found. Falling back to standard attack.")
            fallback_target = None
            potential_targets = []
            for enemy in all_enemies:
                 if enemy.health > 0 and enemy.type in initiating_tower.targets and initiating_tower.is_in_range(enemy.x, enemy.y):
                     potential_targets.append(enemy)
            if potential_targets:
                 potential_targets.sort(key=lambda e: (e.x - initiating_tower.x)**2 + (e.y - initiating_tower.y)**2)
                 fallback_target = potential_targets[0]
                 
            if fallback_target:
                 #print(f"... initiator {initiating_tower.tower_id} firing standard projectile at {fallback_target.enemy_id}")
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
                 #print("... no standard target found either.")
                 pass
                 initiating_tower.last_attack_time = current_time

    def load_wave_data(self, file_path):
        """Loads wave data from the specified JSON file."""
        #print(f"[GameScene] Attempting to load waves from: {file_path}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            #print(f"[GameScene] Successfully loaded {len(data)} waves from {file_path}")
            return data
        except FileNotFoundError:
            #print(f"[GameScene] Error: Wave file not found at {file_path}")
            return [] # Return empty list on error
        except json.JSONDecodeError as e:
            #print(f"[GameScene] Error decoding JSON from wave file {file_path}: {e}")
            return [] # Return empty list on error
        except Exception as e:
            #print(f"[GameScene] An unexpected error occurred loading wave data from {file_path}: {e}")
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
                    #print(f"--- Starting Wave {self.current_wave_index + 1} ---")
                    
                    # Trigger hint message for wave 2 (index 1) after 15 seconds
                    if self.current_wave_index == 1 and not self.hint_triggered:
                        self.hint_triggered = True
                        self.hint_message_active = True
                        self.hint_message_start_time = current_time + 15.0  # Show after 15 seconds
                    
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
                    # Start the 60-second timer when wave begins spawning
                    self.wave_time_limit_timer = self.wave_time_limit
                    self.wave_time_limit_expired = False
                    self.wave_bonus_gold = 0
                    self.final_countdown_played = False # Reset countdown sound flag for new wave
                else:
                    #print("ERROR: Invalid wave index. Transitioning back to IDLE.")
                    self.wave_state = WAVE_STATE_IDLE # Should not happen
        
        elif self.wave_state == WAVE_STATE_SPAWNING:
            # Update wave time limit timer
            if self.wave_time_limit_timer > 0:
                self.wave_time_limit_timer -= delta_time
                
                # Play final countdown sound when 5 seconds remain (only once per wave)
                if not self.final_countdown_played and self.wave_time_limit_timer <= 5.0:
                    if self.final_countdown_sound:
                        self.final_countdown_sound.play()
                        self.final_countdown_played = True
                
                if self.wave_time_limit_timer <= 0:
                    self.wave_time_limit_timer = 0.0
                    self.wave_time_limit_expired = True
                    # Immediately start next wave if timer expires
                    # (but continue current wave spawning)
            
            # Check if all groups have finished spawning
            if not self.spawning_groups:
                #print(f"Wave {self.current_wave_index + 1} finished spawning. Total Spawned Counted: {self.enemies_alive_this_wave}") # DEBUG
                # Transition to INTERMISSION state
                self.wave_state = WAVE_STATE_INTERMISSION # CORRECTED TRANSITION
                #print(f"--> Entering INTERMISSION state. Waiting for count to reach 0.") # DEBUG
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
            # Update wave time limit timer during intermission
            if self.wave_time_limit_timer > 0:
                self.wave_time_limit_timer -= delta_time
                
                # Play final countdown sound when 5 seconds remain (only once per wave)
                if not self.final_countdown_played and self.wave_time_limit_timer <= 5.0:
                    if self.final_countdown_sound:
                        self.final_countdown_sound.play()
                        self.final_countdown_played = True
                
                if self.wave_time_limit_timer <= 0:
                    self.wave_time_limit_timer = 0.0
                    self.wave_time_limit_expired = True
                    # If timer expires, immediately start next wave
                    if self.current_wave_index + 1 < len(self.all_wave_data):
                        self.current_wave_index += 1
                        self.wave_state = WAVE_STATE_SPAWNING
                        next_wave_data = self.all_wave_data[self.current_wave_index]
                        self.spawning_groups = []
                        self.enemies_alive_this_wave = 0
                        self.wave_time_limit_timer = self.wave_time_limit
                        self.wave_time_limit_expired = False
                        self.wave_bonus_gold = 0
                        self.final_countdown_played = False # Reset countdown sound flag for new wave
                        
                        for group_data in next_wave_data.get('enemies', []):
                            self.spawning_groups.append({
                                'type': group_data['type'],
                                'remaining': group_data['count'],
                                'interval': group_data['spawn_interval'],
                                'interval_timer': group_data.get('initial_delay', 0.0),
                                'initial_delay_timer': group_data.get('initial_delay', 0.0)
                            })
                        self.notify_wave_change()
                        return # Stop processing for this frame
            
            # In this state, we wait until all enemies spawned *in this wave* are gone
            # (enemies_alive_this_wave is decremented on death or objective reach)
            #print(f"DEBUG: In INTERMISSION. Checking enemies_alive_this_wave: {self.enemies_alive_this_wave}") # DEBUG
            if self.enemies_alive_this_wave <= 0:
                #print(f"Wave {self.current_wave_index + 1} cleared!")
                
                # --- Award Wave Completion Bonus --- 
                # Make sure we have a valid current wave index
                if 0 <= self.current_wave_index < len(self.all_wave_data):
                    completed_wave_data = self.all_wave_data[self.current_wave_index]
                    bonus = completed_wave_data.get("wave_completion_bonus", 0)
                    if bonus > 0:
                        self.money += bonus
                        self.tower_selector.update_money(self.money) # Update UI
                        #print(f"$$$ Wave Bonus Added: +{bonus}. Current Money: {self.money}")
                        
                        # Create floating text effect for wave completion bonus
                        try:
                            # Position text near center of screen (slightly above center)
                            text_x = self.screen_width // 2
                            text_y = self.screen_height // 2 - 50
                            bonus_text = f"Wave Complete: +{bonus} G"
                            bonus_color = (0, 255, 0) # Green color for wave bonus
                            text_effect = FloatingTextEffect(text_x, text_y, bonus_text, color=bonus_color, font_size=36, duration=3.5)
                            self.effects.append(text_effect)
                        except Exception as e:
                            #print(f"Error creating wave bonus text effect: {e}")
                            pass
                
                # --- Calculate and Award Time-Based Bonus Gold ---
                # Calculate bonus based on remaining seconds (max 20 gold)
                if self.wave_time_limit_timer > 0:
                    remaining_seconds = int(self.wave_time_limit_timer)
                    if remaining_seconds >= 20:
                        # Max bonus: 20 gold for 20+ seconds remaining
                        self.wave_bonus_gold = 20
                    else:
                        # Bonus decreases per second after 20 seconds
                        self.wave_bonus_gold = remaining_seconds
                    
                    if self.wave_bonus_gold > 0:
                        self.money += self.wave_bonus_gold
                        self.tower_selector.update_money(self.money) # Update UI
                        #print(f"$$$ Time Bonus Added: +{self.wave_bonus_gold}. Current Money: {self.money}")
                        
                        # Create floating text effect for time bonus
                        try:
                            # Position text near center of screen (slightly below wave bonus text)
                            text_x = self.screen_width // 2
                            text_y = self.screen_height // 2
                            time_bonus_text = f"Time Bonus: +{self.wave_bonus_gold} G"
                            time_bonus_color = (255, 215, 0) # Gold color for time bonus
                            text_effect = FloatingTextEffect(text_x, text_y, time_bonus_text, color=time_bonus_color, font_size=36, duration=3.5)
                            self.effects.append(text_effect)
                        except Exception as e:
                            #print(f"Error creating time bonus text effect: {e}")
                            pass
                # --- End Time-Based Bonus ---
                # --- End Bonus Award --- 
                
                # Current wave is fully cleared, prepare for the next one
                self.wave_state = WAVE_STATE_IDLE # Transition back to IDLE
                self.current_wave_index += 1
                
                # Notify race selector about wave change (for unlock system)
                self.notify_wave_change()
                
                # Only start delay_before_wave if timer hasn't expired
                # If timer expired, next wave already started above
                if not self.wave_time_limit_expired:
                    if self.current_wave_index < len(self.all_wave_data):
                        next_wave_data = self.all_wave_data[self.current_wave_index]
                        self.wave_timer = next_wave_data.get('delay_before_wave', 10.0)
                        self.wave_state = WAVE_STATE_WAITING
                        #print(f"Wave complete. Waiting {self.wave_timer:.1f}s for Wave {self.current_wave_index + 1}")
                    else:
                        #print("--- All waves spawned! --- ")
                        self.wave_state = WAVE_STATE_ALL_DONE # Or potentially WAVE_COMPLETE to wait for kills
                return # Stop processing spawns for this frame

    def notify_wave_change(self):
        """Notify the race selector about wave changes for unlock system."""
        if hasattr(self.game, 'race_selector') and self.game.race_selector:
            wave_number = self.current_wave_index + 1  # Convert 0-based index to 1-based wave number
            self.game.race_selector.update_wave(wave_number)
            
        # Check if second race towers should be unlocked
        if wave_number == 10 and self.locked_race_towers:
            self.unlock_second_race_towers()
    
    def unlock_second_race_towers(self):
        """Unlock the second race's towers and update the tower selector."""
        if not self.locked_race_towers:
            return
        
        # Cache locked towers before clearing
        newly_unlocked_towers = dict(self.locked_race_towers)
            
        # Add locked towers to available towers
        self.available_towers.update(newly_unlocked_towers)
        print(f"[GameScene] Unlocked {len(newly_unlocked_towers)} towers from second race at wave 10!")
        
        # Clear the locked towers
        self.locked_race_towers = {}
        
        # Update the tower selector with new towers
        if hasattr(self, 'tower_selector') and self.tower_selector:
            self.tower_selector.available_towers = self.available_towers
            # Precompute tooltip HTML for newly unlocked towers
            for tower_id, tower_data in newly_unlocked_towers.items():
                if tower_id not in self.tower_selector._tooltip_html_cache:
                    self.tower_selector._tooltip_html_cache[tower_id] = self.tower_selector._build_tooltip_html(tower_data)
            # Rebuild the tower selector UI (use create_icon_buttons for new UI)
            self.tower_selector.create_icon_buttons()
            # Update button states after adding new towers
            self.tower_selector.update_button_states()
            print("[GameScene] Tower selector updated with unlocked towers!")
    
    # --- Spawn Enemy Helper --- 
    def spawn_enemy(self, enemy_id):
        """Spawns a single enemy of the specified type at the visual spawn point."""
        # Get enemy data from config
        enemy_base_data = config.ENEMY_DATA.get(enemy_id)
        if not enemy_base_data:
            #print(f"ERROR: Could not find enemy data for ID: {enemy_id}")
            return

        # Get armor data
        armor_type_name = enemy_base_data.get('armor_type', 'Unarmored')
        armor_info = self.armor_data.get(armor_type_name, {})
        damage_modifiers = armor_info.get('damage_modifiers', {})

        # --- Determine if enemy is air unit ---
        is_air = enemy_base_data.get("type", "ground") == "air"
        #print(f"DEBUG Spawn: Spawning {enemy_id}, Type={enemy_base_data.get('type', 'ground')}, Is Air? {is_air}") # DEBUG
        # -------------------------------------

        # Find initial path, passing air unit status
        path = find_path(self.path_start_x, self.path_start_y, 
                         self.path_end_x, self.path_end_y, self.grid,
                         is_air_unit=is_air) # Pass the flag

        if path:
            # Spawn at the visual spawn point (center of spawn area)
            # Use the same coordinates as spawn_test_enemy() for consistency
            enemy = Enemy(self.visual_spawn_x_pixel, self.visual_spawn_y_pixel, 
                          path, enemy_id, enemy_base_data, armor_type_name, damage_modifiers)
            self.enemies.append(enemy)
            self.enemies_alive_this_wave += 1 # Increment count for wave tracking
            #print(f"Spawned enemy: {enemy_id} (Wave: {self.current_wave_index + 1})")
        else:
            pass
            #print(f"ERROR: Could not find path for enemy: {enemy_id}. Enemy not spawned.")
            # Handle this case - maybe game over or error message?

    # --- NEW: Callback for Towers to Add Entities --- 
    def add_pass_through_exploder(self, exploder_instance):
        """Callback method for towers to add newly created PassThroughExploders to the scene."""
        if isinstance(exploder_instance, PassThroughExploder):
            self.pass_through_exploders.append(exploder_instance)
        else:
            #print(f"Warning: Attempted to add non-PassThroughExploder instance via callback: {exploder_instance}")
            pass
    # --- End Callback --- 

    # --- NEW: Callback Method for Adding Standard Effects ---
    def add_visual_effect(self, effect):
        """Add a visual effect to the scene, respecting low effects mode if enabled."""
        # Check for low effects mode
        if hasattr(self.game, 'low_effects_mode') and getattr(self.game, 'low_effects_mode', False):
            if len(self.effects) >= 10:
                return  # Do not add more effects
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
            #print(f"$$$ Deducted {cost}. Current Money: {self.money}") # Optional log
            return True
        else:
            #print(f"Warning: Attempted to deduct {cost} but only have {self.money}.")
            return False
    
    # --- In-game Console Commands ---
    def execute_console_command(self, command_line):
        """Parse and execute a simple console command string."""
        if not command_line:
            return
        parts = command_line.strip().split()
        if not parts:
            return
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd in ("addmoney", "add_money", "money"):
            if not args:
                print("Usage: addmoney <amount>")
                return
            try:
                amount = int(float(args[0]))
            except ValueError:
                print("addmoney: amount must be a number")
                return
            if amount != 0:
                self.money += amount
                if self.tower_selector:
                    self.tower_selector.update_money(self.money)
                print(f"Added ${amount}. Current Money: ${self.money}")
            return

        if cmd in ("addlives", "add_lives", "lives"):
            if not args:
                print("Usage: addlives <amount>")
                return
            try:
                amount = int(float(args[0]))
            except ValueError:
                print("addlives: amount must be a number")
                return
            if amount != 0:
                self.lives += amount
                if self.tower_selector:
                    self.tower_selector.update_lives(self.lives)
                print(f"Adjusted lives by {amount}. Current Lives: {self.lives}")
            return

        if cmd in ("showcoordinates", "show_coordinates", "coords", "coordinates"):
            self.show_coordinates = not self.show_coordinates
            status = "enabled" if self.show_coordinates else "disabled"
            print(f"Show coordinates: {status}")
            return

        if cmd in ("mainmenu", "menu", "main_menu"):
            # Return to main menu / race selection screen
            if hasattr(self.game, 'return_to_menu'):
                self.game.return_to_menu()
                print("Returning to main menu...")
            else:
                print("Error: Cannot return to menu (method not found)")
            return

        print(f"Unknown command: {cmd}")
    # --- END Money Callbacks ---

    # --- NEW: Callback to add projectiles (used by Tower.update) ---
    def add_projectile(self, projectile):
        """Callback for towers to add projectiles created during their update phase."""
        if projectile:
            self.projectiles.append(projectile)
    # --- END Projectile Callback ---
