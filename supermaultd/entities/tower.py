import pygame
import math
import pymunk
import random
import os # <<< ADDED IMPORT
from config import *
# from .unique import UNIQUE_ABILITIES # Commented out
from entities.projectile import Projectile # Ensure Projectile is imported
from entities.effect import Effect, FloatingTextEffect, ChainLightningVisual, OrbitingOrbsEffect, DrainParticleEffect, RisingFadeEffect # Import new class
import json # Import json for loading armor data
from .pass_through_exploder import PassThroughExploder # ADD THIS IMPORT
from entities.offset_boomerang_projectile import OffsetBoomerangProjectile # <<< ADDED IMPORT
from entities.orbiting_damager import OrbitingDamager
# from entities.orbiting_orbs_effect import OrbitingOrbsEffect # Removed import
from entities.effect import Effect, FloatingTextEffect, ChainLightningVisual, RisingFadeEffect, GroundEffectZone # Added GroundEffectZone
from entities.harpoon_projectile import HarpoonProjectile
from entities.grenade_projectile import GrenadeProjectile
from entities.cluster_projectile import ClusterProjectile
from .double_strike_effect import DoubleStrikeEffect
from .every_nth_strike_effect import EveryNthStrikeEffect
from .strategic_strike_effect import StrategicStrikeEffect

class Tower:
    def __init__(self, x, y, tower_id, tower_data):
        """
        Initialize a tower.
        
        :param x: Center grid x position
        :param y: Center grid y position
        :param tower_id: ID of the tower type
        :param tower_data: Dictionary containing tower properties
        """
        # Log the received data for debugging
        # print(f"DEBUG Tower INIT: id='{tower_id}', received_data={tower_data}")
        
        # Store center grid position
        self.center_grid_x = x
        self.center_grid_y = y
        
        # Store basic info
        self.tower_id = tower_id
        # --- DEBUG PRINT ---
        #print(f"DEBUG Tower INIT: Assigned self.tower_id = {self.tower_id}")
        # -------------------
        self.tower_data = tower_data
        
        # Size properties (Grid units)
        self.grid_width = tower_data.get('grid_width', 1)
        self.grid_height = tower_data.get('grid_height', 1)
        
        # New mechanics from JSON
        self.critical_chance = tower_data.get('critical_chance', 0.0)
        self.critical_multiplier = tower_data.get('critical_multiplier', 1.0)
        self.bounce = tower_data.get('bounce', 0)
        # self.splash = tower_data.get('splash', None) # Requires splash_radius
        # Read splash radius in abstract units and convert to pixels
        json_splash_radius = tower_data.get('splash_radius', 0)
        # Handle case where splash_radius might be explicitly null/None in JSON
        if json_splash_radius is None:
            json_splash_radius = 0
        # Store the original abstract unit value    
        self.splash_radius = json_splash_radius
        # Calculate and store pixel value (or move this calc to calculate_derived_stats)
        self.splash_radius_pixels = json_splash_radius * (GRID_SIZE / 200.0)
        self.targets = tower_data.get('targets', ["ground"]) # Default to ground
        self.target_armor_type = tower_data.get('target_armor_type', []) # Load specific armor types this tower can target, default to empty (no restriction)
        self.special = tower_data.get('special', None)
        self.attack_type = tower_data.get('attack_type', 'projectile')
        self.projectile_speed = tower_data.get('projectile_speed', None) # Default to None
        #print(f"INIT Tower {self.tower_id}: Attack Type = {self.attack_type}, ProjSpeed = {self.projectile_speed}")
        
        # Beam specific state
        self.beam_color = tower_data.get('beam_color', None) # Load optional beam color
        self.beam_max_targets = tower_data.get('beam_max_targets', 1) # Max simultaneous beam targets
        self.beam_targets = [] # List of current Enemy objects being targeted
        self.next_damage_time = 0 
        self.active_drain_effect = None # NEW: Store active drain particle effect instance
        # Laser Painter State
        self.painting_target = None # Current enemy being painted (for laser_painter)
        self.paint_start_time = 0.0 # Game time when painting started on current target
        # Flamethrower Effect State
        self.active_flame_effect = None # Stores the active particle effect instance
        # Tower Chain State
        self.linked_neighbors = [] # List of tower objects this tower is linked to
        self.last_chain_participation_time = 0.0 # Game time when this tower last participated in a successful chain zap
        
        # Calculate derived position/size properties
        self.width_pixels = self.grid_width * GRID_SIZE
        self.height_pixels = self.grid_height * GRID_SIZE
        
        # Calculate top-left grid position for drawing
        offset_x = (self.grid_width - 1) // 2
        offset_y = (self.grid_height - 1) // 2
        self.top_left_grid_x = self.center_grid_x - offset_x
        self.top_left_grid_y = self.center_grid_y - offset_y

        # Calculate center pixel position for logic (range, targeting)
        self.x = self.center_grid_x * GRID_SIZE + GRID_SIZE // 2 
        self.y = self.center_grid_y * GRID_SIZE + GRID_SIZE // 2
        
        # Base stats (used if type-specific stats aren't present)
        self.base_damage_min = tower_data.get('damage_min', 0)
        self.base_damage_max = tower_data.get('damage_max', 0)
        self.base_attack_speed = tower_data.get('attack_speed', 1.0)
        # Load type-specific stats if they exist
        self.stats_ground = tower_data.get('stats_ground', None)
        self.stats_air = tower_data.get('stats_air', None)
        # Store damage type
        self.damage_type = tower_data.get('damage_type', 'normal')
        
        # Initialize salvo attack state
        self.salvo_shots_remaining = 0
        self.salvo_interval = 0.1  # Time between shots in a salvo
        self.last_salvo_shot_time = 0.0  # Time of last shot in current salvo
        self.salvo_next_shot_time = 0.0  # Time when next salvo shot should fire
        self.salvo_target = None  # Current target for salvo attack
        
        # Initialize gattling state
        self.gattling_level = 0
        self.gattling_continuous_fire_start_time = 0.0
        self.gattling_last_attack_time = 0.0
        
        # Initialize attack timing
        self.last_attack_time = 0.0  # Time of last regular attack
        
        # Convert abstract range units (from JSON) to pixel radius
        # User defined scale: 200 range units = 1 tile = GRID_SIZE pixels
        json_range = tower_data.get('range', 200) # Default to 1 tile range (200 units)
        json_range_min = tower_data.get('range_min', 0) # Default minimum range to 0
        self.range = json_range * (GRID_SIZE / 200.0) # Calculate max pixel radius
        self.range_min_pixels = json_range_min * (GRID_SIZE / 200.0) # Calculate min pixel radius
        
        # --- Bounce Parameters (New) ---
        self.bounce = tower_data.get('bounce', 0)
        json_bounce_range = tower_data.get('bounce_range', 300) # Default 300 abstract units
        self.bounce_range_pixels = json_bounce_range * (GRID_SIZE / 200.0)
        self.bounce_damage_falloff = tower_data.get('bounce_damage_falloff', 0.5) # Changed default from 0.7 to 0.5
        # --- End Bounce Parameters ---
        
        # --- Pierce Parameter --- 
        self.pierce_adjacent = tower_data.get('pierce_adjacent', 0) # Load pierce amount
        # --- End Pierce Parameter ---
        
        # self.range = tower_data.get('range', 3) * GRID_SIZE # Old category logic removed
        self.cost = tower_data['cost']
        self.description = tower_data.get('description', '')
        self.last_pulse_time = 0 # For aura pulse effects
        
        # Basic properties
        self.level = 1
        # Directly read attack_interval from data, default if necessary
        # self.attack_interval = tower_data.get('attack_interval', 1.0) 
        # Use attack_speed to calculate interval if interval isn't specified
        self.attack_interval = tower_data.get('attack_interval', 1.0 / self.base_attack_speed)
        
        # Calculate and store aura radius in pixels if applicable
        self.aura_radius_pixels = 0
        aura_units = 0
        if self.special and 'aura_radius' in self.special:
            aura_units = self.special.get('aura_radius', 0)
        self.aura_radius_pixels = aura_units * (GRID_SIZE / 200.0)
        print(f"DEBUG: {self.tower_id} aura radius set to {self.aura_radius_pixels} pixels")
        
        # Initialize unique ability if tower has one
        self.unique_ability = None
        # unique_desc = tower_data.get("unique", "").lower()
        # if "pierce" in unique_desc:
        #     self.unique_ability = UNIQUE_ABILITIES["pierce"](self)
        # elif "chain" in unique_desc:
        #     self.unique_ability = UNIQUE_ABILITIES["chain"](self)
        # elif "splash" in unique_desc:
        #     self.unique_ability = UNIQUE_ABILITIES["splash"](self)
        # elif "buff" in unique_desc:
        #     self.unique_ability = UNIQUE_ABILITIES["buff"](self)
        # elif "critical" in unique_desc:
        #     self.unique_ability = UNIQUE_ABILITIES["critical"](self)
        
        # Visual properties (TODO: Load from assets - currently unused)
        self.color = BLUE
        self.radius = 15
        
        # Berserk State (for self-buffs)
        self.is_berserk = False
        self.berserk_end_time = 0
        self.berserk_bonus_multiplier = 1.0
        
        # --- NEW: List to hold orbiting damagers associated with this tower --- 
        self.orbiters = []
        # --- End Orbiter List ---

        # --- NEW: Rampage State ---
        self.rampage_stacks = 0
        self.rampage_last_hit_time = 0.0
        # --- END Rampage State ---

        # --- NEW: Salvo State ---
        self.salvo_shots_remaining = 0
        self.salvo_next_shot_time = 0.0
        self.salvo_target = None
        # --- END Salvo State ---

        # --- NEW: Pulsed Buff State ---
        self.pulsed_buffs = {} # Stores temporary buffs like { 'crit_damage': {'value': 0.5, 'end_time': 123.4} }
        # --- END Pulsed Buff State ---

        # --- NEW: Pulse Animation State ---
        self.pulse_start_time = 0
        self.pulse_radius = 0
        self.pulse_alpha = 255
        self.pulse_duration = 2.5  # Match the interval from tower_races.json
        # --- END Pulse Animation State ---

        # Calculate derived stats
        self.calculate_derived_stats()
        
        # Added for projectile asset loading
        self.asset_loader = None
        
        self.broadside_angle_offset = tower_data.get('broadside_angle_offset', 0)

        # --- Load Attack Sound ---
        self.attack_sound = None
        sound_dir = os.path.join("assets", "sounds") # <<< CORRECT
        # Use 'attack_sound' from JSON if available, otherwise use tower_id
        sound_basename = self.tower_data.get("attack_sound", self.tower_id) # <<< CHANGE THIS LINE
        # Try MP3 first, then WAV
        possible_paths = [
            os.path.join(sound_dir, f"{sound_basename}.mp3"),
            os.path.join(sound_dir, f"{sound_basename}.wav")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    self.attack_sound = pygame.mixer.Sound(path)
                    #print(f"Loaded attack sound for {self.tower_id} from {path}")
                    break # Sound found, stop searching
                except pygame.error as e:
                    #print(f"Error loading sound {path}: {e}")
                    pass
        if not self.attack_sound:
            #print(f"Warning: No attack sound file found for {self.tower_id} (checked: {sound_basename}.mp3/wav)")
            pass

        # --- NEW: Looping sound for Ogre War Drums ---
        self.looping_sound_channel = None # Initialize attribute
        if self.tower_id == 'ogre_war_drums':
            drums_sound_path = os.path.join(sound_dir, "ogre_war_drums.mp3") # Assuming mp3
            if os.path.exists(drums_sound_path):
                try:
                    drum_sound = pygame.mixer.Sound(drums_sound_path)
                    self.looping_sound_channel = pygame.mixer.find_channel() # Find an available channel
                    if self.looping_sound_channel:
                        self.looping_sound_channel.play(drum_sound, loops=-1) # Start looping indefinitely
                        #print(f"Started looping war drums sound for {self.tower_id} on channel {self.looping_sound_channel}")
                    else:
                        #print(f"Warning: Could not find available channel for looping {self.tower_id} sound.")
                        pass
                except pygame.error as e:
                    #print(f"Error loading or playing looping sound {drums_sound_path}: {e}")
                    pass
            else:
                #print(f"Warning: Looping sound file not found: {drums_sound_path}")
                pass
                
        # --- Beam Sound State ---
        self.is_beam_sound_playing = False # Flag to track if the beam sound is currently looping
        # --- End Beam Sound State ---
        
        # --- Jaguar Double Strike Sound (Specific Loading) ---
        self.double_strike_sound = None
        if self.tower_id == 'tac_jaguar_mech':
            double_strike_sound_path = os.path.join(sound_dir, "jaguar_growl.mp3")
            if os.path.exists(double_strike_sound_path):
                try:
                    self.double_strike_sound = pygame.mixer.Sound(double_strike_sound_path)
                    #print(f"Loaded double strike sound for {self.tower_id} from {double_strike_sound_path}")
                except pygame.error as e:
                    #print(f"Error loading double strike sound {double_strike_sound_path}: {e}")
                    pass
            else:
                #print(f"Warning: Double strike sound file not found: {double_strike_sound_path}")
                pass
                
        # --- Samurai Armor Ignore Sound (Specific Loading) ---
        self.ignore_armor_sound = None
        if self.tower_id == 'tac_samurai_mech':
            ignore_armor_sound_path = os.path.join(sound_dir, "samurai.mp3")
            if os.path.exists(ignore_armor_sound_path):
                try:
                    self.ignore_armor_sound = pygame.mixer.Sound(ignore_armor_sound_path)
                    #print(f"Loaded ignore armor sound for {self.tower_id} from {ignore_armor_sound_path}")
                except pygame.error as e:
                    #print(f"Error loading ignore armor sound {ignore_armor_sound_path}: {e}")
                    pass
            else:
                #print(f"Warning: Ignore armor sound file not found: {ignore_armor_sound_path}")
                pass
                
        # --- Pass Through Launch Sound (Conditional Loading) ---
        self.pass_through_launch_sound = None
        if self.special and self.special.get("effect") == "fixed_distance_pass_through_explode":
            sound_filename = self.special.get("pass_through_launch_sound_file")
            if sound_filename:
                launch_sound_path = os.path.join(sound_dir, sound_filename)
                if os.path.exists(launch_sound_path):
                    try:
                        self.pass_through_launch_sound = pygame.mixer.Sound(launch_sound_path)
                        #print(f"Loaded pass through launch sound for {self.tower_id} from {launch_sound_path}")
                    except pygame.error as e:
                        #print(f"Error loading pass through launch sound {launch_sound_path}: {e}")
                        pass
                else:
                    #print(f"Warning: Pass through launch sound file not found: {launch_sound_path}")
                    pass
            else:
                 #print(f"Warning: Tower {self.tower_id} has fixed_distance_pass_through_explode effect but no 'pass_through_launch_sound_file' key in special.")
                 pass

        # --- NEW: Looping sound for Spark Storm Generator ---
        if self.tower_id == 'spark_storm_generator':
            storm_sound_path = os.path.join(sound_dir, "spark_thunderstorm.mp3")
            if os.path.exists(storm_sound_path):
                try:
                    storm_sound = pygame.mixer.Sound(storm_sound_path)
                    self.looping_sound_channel = pygame.mixer.find_channel()
                    if self.looping_sound_channel:
                        self.looping_sound_channel.play(storm_sound, loops=-1)
                        #print(f"Started looping sound {storm_sound_path} on channel {self.looping_sound_channel}")
                    else:
                        #print("Warning: No available sound channels for spark_storm_generator loop.")
                        pass
                except pygame.error as e:
                    print(f"Error loading or playing spark_storm_generator sound {storm_sound_path}: {e}")
            else:
                print(f"Warning: Looping sound file not found: {storm_sound_path}")
        # --- END Spark Storm Generator Sound ---

        # --- NEW: Looping sound for Goblin Shredder ---
        if self.tower_id == 'goblin_shredder':
            shredder_sound_path = os.path.join(sound_dir, "goblin_shredder_on.mp3")
            if os.path.exists(shredder_sound_path):
                try:
                    shredder_sound = pygame.mixer.Sound(shredder_sound_path)
                    self.looping_sound_channel = pygame.mixer.find_channel()
                    if self.looping_sound_channel:
                        self.looping_sound_channel.play(shredder_sound, loops=-1)
                        #print(f"Started looping sound {shredder_sound_path} on channel {self.looping_sound_channel}")
                    else:
                        #print("Warning: No available sound channels for goblin_shredder loop.")
                        pass
                except pygame.error as e:
                    #print(f"Error loading or playing goblin_shredder sound {shredder_sound_path}: {e}")
                    pass
            else:
                #print(f"Warning: Looping sound file not found: {shredder_sound_path}")
                pass
        # --- END Goblin Shredder Sound ---

        # --- NEW: Load Miss Sound for Goblin Catapult Brigade ---
        if self.tower_id == 'goblin_catapult_brigade':
            miss_sound_path = os.path.join(sound_dir, "goblin_catapult_misfire.mp3")
            if os.path.exists(miss_sound_path):
                try:
                    self.miss_sound = pygame.mixer.Sound(miss_sound_path)
                    #print(f"Loaded miss sound for {self.tower_id} from {miss_sound_path}")
                except pygame.error as e:
                    #print(f"Error loading miss sound {miss_sound_path}: {e}")
                    pass
            else:
                #print(f"Warning: Miss sound file not found: {miss_sound_path}")
                pass
        # --- END Miss Sound Loading ---

        # --- NEW: Continuous Aura Tick Timer ---
        self.last_aura_tick_time = 0.0
        # --- END Continuous Aura Tick Timer ---
        
        # --- Vortex Visual Rotation Timing --- <<< ADDED
        self.vortex_visual_last_update_time = 0.0
        self.vortex_visual_update_interval = 0.02 # Update ~20 times/sec
        self.vortex_current_angle = 0.0
        self.vortex_overlay_image = None # Initialize overlay storage
        # --- END Vortex Visual Timing --- <<< ADDED

        # --- Load Vortex Overlay Image (Specific Load) --- <<< ADDED
        if self.tower_id == 'brine_vortex_monument':
            vortex_image_path = os.path.join("assets", "effects", "brine_vortex_monument.png")
            if os.path.exists(vortex_image_path):
                try:
                    self.vortex_overlay_image = pygame.image.load(vortex_image_path).convert_alpha()
                    #print(f"Loaded vortex overlay for {self.tower_id}")
                except pygame.error as e:
                    #print(f"Error loading vortex overlay image {vortex_image_path}: {e}")
                    pass
            else:
                #print(f"Warning: Vortex overlay image not found: {vortex_image_path}")
                pass
        # --- END Vortex Overlay Load --- <<< ADDED

        # --- NEW: Execute Ability State --- 
        self.execute_cooldown = 0.0
        self.execute_last_time = 0.0
        self.execute_health_threshold = 0.0
        self.special_ability_sound = None # Sound for execute/other specials
        
        if self.special and self.special.get("effect") == "execute":
            self.execute_cooldown = self.special.get("execute_cooldown", 5.0)
            self.execute_health_threshold = self.special.get("execute_health_threshold", 0.10)
            # Load the special sound
            ability_sound_id = self.special.get("ability_sound_id")
            if ability_sound_id:
                # Assuming sound_dir is already defined earlier in __init__
                possible_paths = [
                    os.path.join(sound_dir, f"{ability_sound_id}.mp3"),
                    os.path.join(sound_dir, f"{ability_sound_id}.wav")
                ]
                for path in possible_paths:
                    if os.path.exists(path):
                        try:
                            self.special_ability_sound = pygame.mixer.Sound(path)
                            #print(f"Loaded special ability sound for {self.tower_id} ({ability_sound_id}) from {path}")
                            break
                        except pygame.error as e:
                            #print(f"Error loading special ability sound {path}: {e}")
                            pass
                if not self.special_ability_sound:
                    #print(f"Warning: No special ability sound file found for {self.tower_id} (checked: {ability_sound_id}.mp3/wav)")
                    pass
        # --- END Execute Ability State ---

        # --- Miasma Pulse Animation State ---
        self.miasma_pulse_start_time = 0.0
        self.miasma_pulse_duration = 1.0  # 1 second for full pulse cycle
        self.miasma_pulse_radius = 0
        self.miasma_pulse_alpha = 255
        # --- End Miasma Pulse State ---

        # --- NEW: Looping sound for Bomb Barrage Beacon ---
        if self.tower_id == 'bomb_barrage_beacon':
            beacon_sound_path = os.path.join(sound_dir, "bomb_barrage_beacon.mp3")
            if os.path.exists(beacon_sound_path):
                try:
                    beacon_sound = pygame.mixer.Sound(beacon_sound_path)
                    self.looping_sound_channel = pygame.mixer.find_channel()
                    if self.looping_sound_channel:
                        self.looping_sound_channel.play(beacon_sound, loops=-1)
                        #print(f"Started looping sound {beacon_sound_path} on channel {self.looping_sound_channel}")
                    else:
                        #print("Warning: No available sound channels for bomb_barrage_beacon loop.")
                        pass
                except pygame.error as e:
                    #print(f"Error loading or playing bomb_barrage_beacon sound {beacon_sound_path}: {e}")
                    pass
            else:
                #print(f"Warning: Looping sound file not found: {beacon_sound_path}")
                pass
        # --- END Bomb Barrage Beacon Sound ---

        # Set last_attack_time to trigger first strike immediately for bombardment
        if tower_data.get("special", {}).get("effect") == "random_bombardment":
            self.last_attack_time = -tower_data["special"]["interval"]  # Set to negative interval to trigger immediately
        else:
            self.last_attack_time = 0

        # Initialize strike counter for every_nth_strike effect
        self.strike_counter = 0

        # Initialize special effects if tower has them
        if hasattr(self, 'special') and self.special:
            if self.special.get('effect') == 'strategic_strike':
                self.strategic_strike_effect = StrategicStrikeEffect(self)

        # --- Kill Counter --- # NEW
        self.kill_count = 0
        # --- End Kill Counter ---

        # --- NEW: Time Machine Rewind Sound --- 
        self.rewind_sound = None
        if self.tower_id == 'tech_time_machine':
            rewind_sound_path = os.path.join(sound_dir, "tech_rewind.mp3")
            if os.path.exists(rewind_sound_path):
                try:
                    self.rewind_sound = pygame.mixer.Sound(rewind_sound_path)
                    #print(f"Loaded rewind sound for {self.tower_id} from {rewind_sound_path}")
                except pygame.error as e:
                    #print(f"Error loading rewind sound {rewind_sound_path}: {e}")
                    pass
            else:
                #print(f"Warning: Rewind sound file not found: {rewind_sound_path}")
                pass
        # --- END Time Machine Rewind Sound ---

        # --- NEW: Time Machine Rewind Visual --- 
        self.rewind_visual_surface = None
        if self.tower_id == 'tech_time_machine':
            visual_path = os.path.join("assets", "effects", "warp.png")
            if os.path.exists(visual_path):
                try:
                    # Load image directly here, similar to sounds
                    self.rewind_visual_surface = pygame.image.load(visual_path).convert_alpha()
                    print(f"Loaded rewind visual for {self.tower_id} from {visual_path}")
                except pygame.error as e:
                    #print(f"Error loading rewind visual {visual_path}: {e}")
                    pass
            else:
                #print(f"Warning: Rewind visual file not found: {visual_path}")
                pass
        # --- END Time Machine Rewind Visual ---

    def calculate_derived_stats(self):
        """Calculates pixel dimensions and ranges based on grid size and tower data."""
        # Pixel dimensions based on grid size
        self.width_pixels = self.grid_width * GRID_SIZE
        self.height_pixels = self.grid_height * GRID_SIZE
        
        # Calculate tower center pixel coordinates relative to grid origin
        self.x = (self.center_grid_x * GRID_SIZE) + (GRID_SIZE // 2)
        self.y = (self.center_grid_y * GRID_SIZE) + (GRID_SIZE // 2)
        
        # Convert base range (usually in design units) to pixels
        # Assuming range in JSON is based on a 200 unit = GRID_SIZE scale
        # (Adjust scale factor if your design units are different)
        range_scale_factor = GRID_SIZE / 200.0 
        self.range_pixels = self.range * range_scale_factor if self.range is not None else 0
        
        # Calculate min range in pixels (if min_range is defined in tower_data)
        json_min_range = self.tower_data.get("min_range")
        self.range_min_pixels = json_min_range * range_scale_factor if json_min_range is not None else 0
        
        # Convert splash radius (usually in design units) to pixels
        self.splash_radius_pixels = self.splash_radius * range_scale_factor if self.splash_radius is not None else 0

        # Aura radius is now handled in __init__ with direct 1:1 conversion
        
    def can_attack(self, current_time):
        """Check if the tower can attack based on its attack interval"""
        return current_time - self.last_attack_time >= self.attack_interval
        
    def is_in_range(self, target_x, target_y):
        """Check if a target pixel coordinate is within the tower's pixel range radius.
           Considers both maximum and minimum range.
        """
        # Calculate distance squared first for efficiency
        distance_sq = (target_x - self.x)**2 + (target_y - self.y)**2
        
        # Check if outside minimum range (or if min range is 0) AND inside maximum range
        within_max_range = distance_sq <= self.range**2
        outside_min_range = distance_sq >= self.range_min_pixels**2
        
        return within_max_range and outside_min_range
        
    def get_dot_amplification_multiplier(self, tower_buff_auras):
        """Get the highest dot amplification multiplier from nearby Plague Reactors"""
        if not tower_buff_auras:
            return 1.0
            
        highest_multiplier = 1.0
        processed_towers = set()  # Track which towers we've already processed
        
        for aura in tower_buff_auras:
            buff_tower = aura['tower']
            if buff_tower.tower_id in processed_towers:
                continue
            processed_towers.add(buff_tower.tower_id)
            
            # Check if this is a dot amplification aura
            if buff_tower.special and buff_tower.special.get('effect') == 'dot_amplification_aura':
                # Calculate distance to buff tower
                dx = self.x - buff_tower.x
                dy = self.y - buff_tower.y
                distance_sq = dx * dx + dy * dy
                
                # Check if within aura range
                if distance_sq <= aura['radius_sq']:
                    multiplier = buff_tower.special.get('multiplier', 1.0)
                    if multiplier > highest_multiplier:
                        highest_multiplier = multiplier
                        #print(f"DEBUG: Tower {self.tower_id} affected by {buff_tower.tower_id}'s dot_amp_aura: {multiplier}x")
        
        return highest_multiplier

    def get_stats_for_target(self, target_type):
        """Return the appropriate damage/speed values for the target type."""
        damage_min = self.base_damage_min
        damage_max = self.base_damage_max
        attack_speed = self.base_attack_speed

        specific_stats = None
        if target_type == "ground" and self.stats_ground:
            specific_stats = self.stats_ground
        elif target_type == "air" and self.stats_air:
            specific_stats = self.stats_air
        
        if specific_stats:
            damage_min = specific_stats.get('damage_min', damage_min)
            damage_max = specific_stats.get('damage_max', damage_max)
            attack_speed = specific_stats.get('attack_speed', attack_speed)
            # Add other stats like crit chance/multiplier if they can differ
            
        return damage_min, damage_max, attack_speed

    def get_buffed_stats(self, current_time, tower_buff_auras, all_towers):
        """Calculates effective stats based on active tower buff auras and pulsed buffs."""
        total_speed_bonus_percent = 0.0
        total_damage_bonus_percent = 0.0
        total_crit_chance_bonus = 0.0
        total_crit_multiplier_bonus = 0.0
        # Initialize air damage multiplier
        effective_air_damage_multiplier = 1.0
        # Initialize splash radius increase
        total_splash_radius_increase = 0.0 
        # Add other potential buffs here (e.g., range)

        for aura_data in tower_buff_auras:
            aura_tower = aura_data['tower']
            aura_radius_sq = aura_data['radius_sq']
            aura_special = aura_data['special']
            effect_type = aura_special.get('effect')

            # Check if this tower is within the buff aura's range OR if it's an adjacency buff (which bypasses range)
            dist_sq = (self.x - aura_tower.x)**2 + (self.y - aura_tower.y)**2
            # Updated condition to include both adjacency buffs
            is_adjacent_buff = effect_type in ('adjacency_damage_buff', 'adjacency_attack_speed_buff') 
            if dist_sq <= aura_radius_sq or is_adjacent_buff:
                # Apply relevant buff percentages/bonuses
                if effect_type == 'attack_speed_aura':
                    total_speed_bonus_percent += aura_special.get('speed_increase_percentage', 0.0)
                elif effect_type == 'damage_aura': 
                    total_damage_bonus_percent += aura_special.get('damage_bonus_percentage', 0.0)
                elif effect_type == 'crit_aura':
                    total_crit_chance_bonus += aura_special.get('crit_chance_bonus', 0.0)
                    total_crit_multiplier_bonus += aura_special.get('crit_multiplier_bonus', 0.0)
                # --- Add Air Damage Aura Check ---    
                elif effect_type == 'air_damage_aura':
                    air_mult = aura_special.get('air_damage_multiplier', 1.0)
                    effective_air_damage_multiplier *= air_mult # Multiply for stacking
                # --- Add Adjacency Damage Buff Check ---
                elif effect_type == 'adjacency_damage_buff':
                    print(f"DEBUG: Tower {self.tower_id} receiving adjacency damage buff: +{aura_special.get('damage_bonus_percentage', 0.0)}%") # Debug print
                    total_damage_bonus_percent += aura_special.get('damage_bonus_percentage', 0.0)
                # --- Add Adjacency Attack Speed Buff Check ---
                elif effect_type == 'adjacency_attack_speed_buff':
                    print(f"DEBUG: Tower {self.tower_id} receiving adjacency speed buff: +{aura_special.get('attack_speed_bonus_percentage', 0.0)}%") # Debug print
                    total_speed_bonus_percent += aura_special.get('attack_speed_bonus_percentage', 0.0)
                # NEW: Apply Splash Radius Buff
                elif effect_type == "splash_radius_buff_aura":
                    total_splash_radius_increase += aura_special.get('splash_radius_increase', 0)
                # Add other buff types like range here

        # --- Swarm Power Check (Specific to zork_swarmers) ---
        if self.tower_id == "zork_swarmers" and self.special and self.special.get("effect") == "swarm_power":
            nearby_swarmer_count = 0
            check_radius_units = self.special.get("check_radius", 0)
            bonus_per_swarmer = self.special.get("attack_speed_bonus_per_swarmer", 0)

            if check_radius_units > 0 and bonus_per_swarmer > 0:
                # Convert check radius to pixels squared
                check_radius_pixels = check_radius_units * (GRID_SIZE / 200.0)
                check_radius_sq = check_radius_pixels ** 2

                for other_tower in all_towers:
                    # Skip self and non-swarmers
                    if other_tower == self or other_tower.tower_id != "zork_swarmers":
                        continue
                    
                    # Check distance
                    dist_sq = (self.x - other_tower.x)**2 + (self.y - other_tower.y)**2
                    if dist_sq <= check_radius_sq:
                        nearby_swarmer_count += 1
                
                # Calculate and add the bonus
                if nearby_swarmer_count > 0:
                    swarm_bonus_percent = nearby_swarmer_count * bonus_per_swarmer
                    #print(f"DEBUG: {self.tower_id} ({self.center_grid_x},{self.center_grid_y}) found {nearby_swarmer_count} nearby swarmers. Applying +{swarm_bonus_percent}% speed bonus.") # Debug
                    total_speed_bonus_percent += swarm_bonus_percent
        # --- End Swarm Power Check ---

        # Check for expired pulsed buffs and remove them
        expired_pulsed_keys = [k for k, v in self.pulsed_buffs.items() if current_time >= v['end_time']]
        for key in expired_pulsed_keys:
            del self.pulsed_buffs[key]
            # Optional: print(f"DEBUG Tower {self.tower_id}: Pulsed buff '{key}' expired.")

        # Apply active pulsed buffs
        if 'crit_damage' in self.pulsed_buffs:
            pulsed_crit_bonus = self.pulsed_buffs['crit_damage']['value']
            total_crit_multiplier_bonus += pulsed_crit_bonus
            # Optional: print(f"DEBUG Tower {self.tower_id}: Applying pulsed crit damage bonus: +{pulsed_crit_bonus}")
        # Add checks for other pulsed buff types here if needed (e.g., 'attack_speed')
        # if 'attack_speed' in self.pulsed_buffs:
        #    pulsed_speed_bonus = self.pulsed_buffs['attack_speed']['value'] # Assuming value is % bonus
        #    total_speed_bonus_percent += pulsed_speed_bonus

        # Calculate final multipliers and effective stats
        speed_multiplier = 1.0 + (total_speed_bonus_percent / 100.0)
        if speed_multiplier <= 0: speed_multiplier = 0.01 
        effective_attack_interval = self.attack_interval / speed_multiplier
        
        damage_multiplier = 1.0 + (total_damage_bonus_percent / 100.0)
        
        # Calculate effective crit stats (additive bonuses)
        effective_crit_chance = self.critical_chance + total_crit_chance_bonus
        effective_crit_multiplier = self.critical_multiplier + total_crit_multiplier_bonus

        # --- Calculate Effective Splash Radius --- 
        # Start with the tower's base value (already in pixels from calculate_derived_stats)
        base_splash_pixels = self.splash_radius_pixels 
        effective_splash_radius_pixels = base_splash_pixels + total_splash_radius_increase
        # Ensure it doesn't go below zero
        effective_splash_radius_pixels = max(0, effective_splash_radius_pixels)
        # --- End Splash Radius Calc ---

        # --- Apply Gattling Spin-Up --- 
        if self.special and self.special.get("effect") == "gattling_spin_up" and self.gattling_level > 0:
            gattling_mult = self.special.get("speed_multiplier_per_level", 1.0) ** self.gattling_level
            effective_attack_interval *= gattling_mult
            # Clamp minimum interval? Maybe 0.05s? (Optional)
            # effective_attack_interval = max(0.05, effective_attack_interval)
        # --- END Gattling Spin-Up ---
        
        # Clamp effective interval to avoid negative or zero values
        effective_attack_interval = max(0.01, effective_attack_interval) # Ensure minimum interval > 0

        return {
            'attack_interval': effective_attack_interval,
            'damage_multiplier': damage_multiplier,
            'crit_chance': effective_crit_chance,
            'crit_multiplier': effective_crit_multiplier,
            'air_damage_multiplier': effective_air_damage_multiplier,
            'splash_radius_pixels': effective_splash_radius_pixels # Return the buffed value
        }

    def calculate_damage(self, enemy, buffed_stats, current_time, damage_multiplier=1.0):
        """Calculate damage, applying buffs, critical hits, and self-buffs."""
        # Level 1 indentation (8 spaces)
        dmg_min, dmg_max, _ = self.get_stats_for_target(enemy.type)
        
        damage = random.uniform(dmg_min, dmg_max)
        
        # --- Reaper Mech Bonus Damage --- # NEW
        if self.tower_id == "tac_reaper_mech" and self.kill_count > 0:
            reaper_bonus = 0.25 * self.kill_count
            #print(f"+++ Reaper Mech ({self.tower_id}) applying +{reaper_bonus:.2f} bonus damage (Kills: {self.kill_count}). Base Dmg: {damage:.2f} -> {damage + reaper_bonus:.2f}")
            damage += reaper_bonus
        # --- End Reaper Mech Bonus ---
        
        # Apply damage buffs (from auras)
        damage *= damage_multiplier
        
        # --- Apply Air Damage Multiplier --- 
        if enemy.type == "air":
            air_multiplier = buffed_stats.get('air_damage_multiplier', 1.0)
            if air_multiplier != 1.0:
                damage *= air_multiplier
                #print(f"Tower {self.tower_id} applying x{air_multiplier:.2f} damage multiplier vs Air target {enemy.enemy_id}.")
        # ----------------------------------

        # Check for critical hit using BUFFED crit stats
        is_crit = False
        effective_crit_chance = buffed_stats.get('crit_chance', self.critical_chance)
        effective_crit_multiplier = buffed_stats.get('crit_multiplier', self.critical_multiplier)

        if effective_crit_chance > 0 and random.random() < effective_crit_chance: # Level 2 (12 spaces)
            damage *= effective_crit_multiplier
            is_crit = True
            #print(f"Tower {self.tower_id} CRITICAL HIT! (Chance: {effective_crit_chance:.2f}, Mult: {effective_crit_multiplier:.2f}) Damage: {damage:.2f}")

        # --- Apply Berserk Self-Buff --- 
        if self.is_berserk and current_time < self.berserk_end_time: # Level 1 (8 spaces)
            damage *= self.berserk_bonus_multiplier
            #print(f"Tower {self.tower_id} BERSERK active! Applying x{self.berserk_bonus_multiplier:.2f}. Damage: {damage:.2f}")
        elif self.is_berserk and current_time >= self.berserk_end_time:
            self.is_berserk = False
            self.berserk_bonus_multiplier = 1.0
            #print(f"Tower {self.tower_id} Berserk expired.")

        # --- Check for Berserk Trigger --- 
        # Correct Level 1 indentation (8 spaces)
        if self.special and self.special.get("effect") == "berserk_trigger":
            chance = self.special.get("chance", 0.0) # Level 2 (12 spaces)
            if random.random() < chance:
                duration = self.special.get("duration", 0.0) # Level 3 (16 spaces)
                bonus_percent = self.special.get("damage_bonus_percentage", 0.0)
                if duration > 0 and bonus_percent > 0:
                    self.is_berserk = True # Level 4 (20 spaces)
                    self.berserk_end_time = current_time + duration
                    self.berserk_bonus_multiplier = 1.0 + (bonus_percent / 100.0)
                    print(f"Tower {self.tower_id} triggered BERSERK! (Chance: {chance:.2f}, Duration: {duration:.1f}s, Bonus: x{self.berserk_bonus_multiplier:.2f})")
        
        # Apply unique ability modifications (keep commented)
        # if self.unique_ability and self.unique_ability.get('modifies_damage'):
        #     damage = self.unique_ability['apply'](self, enemy, damage)
            
        return damage, is_crit # Level 1 (8 spaces)

    def attack(self, target, current_time, all_enemies, tower_buff_auras, grid_offset_x, grid_offset_y, visual_assets=None, all_towers=None):
        """Perform an attack. Return a list of projectiles, effects, or None."""
        # --- BEGIN ADDED CODE: Self-Destruct Check ---
        if self.special and self.special.get("effect") == "self_destruct":
            chance = self.special.get("self_destruct_percentage_chance", 0)
            if random.uniform(0, 100) < chance:
                #print(f"Tower {self.tower_id} is self-destructing!")
                # Return dictionary indicating self-destruct action and parameters
                return {
                    'action': 'self_destruct',
                    'radius': self.special.get("self_destruct_radius", 0),
                    'damage': self.special.get("self_destruct_damage", 0),
                    'damage_type': self.special.get("self_destruct_damage_type", "normal"),
                    'targets': self.special.get("self_destruct_targets", ["ground", "air"]),
                    'tower_instance': self # Pass self for position/removal in GameScene
                }
            # Else: Chance failed, proceed to normal attack logic (if applicable)
        # --- END ADDED CODE: Self-Destruct Check ---

        # Determine target for salvo if applicable
        if self.tower_id.endswith('gattling_turret'):
            # Implement gattling turret logic
            pass

        results = {'projectiles': [], 'effects': []}
        
        # --- Adjacency Requirement Check --- 
        if self.special and self.special.get("effect") == "requires_solar_adjacency":
            if not all_towers:
                #print(f"Warning: Tower {self.tower_id} requires adjacency check but 'all_towers' list was not provided.")
                return None # Cannot function without the list
                
            required_count = self.special.get("required_count", 3)
            race_to_check = self.special.get("race_to_check", "solar") # Get the race ID from JSON
            
            adjacent_count = self.count_adjacent_race_towers(all_towers, race_to_check)
            
            if adjacent_count < required_count:
                # print(f"DEBUG: Tower {self.tower_id} adjacency check failed. Found {adjacent_count}/{required_count} {race_to_check} towers.") # Optional Debug
                return None # Not enough adjacent towers, do not attack
            # else:
                # print(f"DEBUG: Tower {self.tower_id} adjacency check PASSED. Found {adjacent_count}/{required_count} {race_to_check} towers.") # Optional Debug
        # --- End Adjacency Check ---

        # --- Calculate Buffed Stats --- 
        # Recalculate here to ensure buffs are current *at the time of attack*
        buffed_stats = self.get_buffed_stats(current_time, tower_buff_auras, all_towers)
        effective_interval = buffed_stats['attack_interval']
        damage_multiplier = buffed_stats['damage_multiplier']
        # Get buffed splash radius
        effective_splash_radius_pixels = buffed_stats['splash_radius_pixels'] 
        
        # --- Interval Check (Moved to be universal for non-beam) ---
        # <<< ADDED DEBUG PRINT >>>
        #print(f"DEBUG Interval Check: Tower={self.tower_id}, Time={current_time:.2f}, LastAttack={self.last_attack_time:.2f}, Interval={effective_interval:.2f}, SalvoRem={self.salvo_shots_remaining}")
        # Allow attack if interval ready OR if a salvo is currently active (but attack shouldn't proceed if active)
        is_salvo_tower = self.special and self.special.get("effect") == "salvo_attack"
        if current_time - self.last_attack_time < effective_interval and self.salvo_shots_remaining <= 0:
            return None # Not ready to attack / start new salvo
        # If a salvo is active, let the update loop handle it, don't proceed in attack
        if is_salvo_tower and self.salvo_shots_remaining > 0:
                return None
        # ---------------------------------------------------------
        
        # --- Special Broadside Handling (No Target Needed) --- 
        is_broadside = self.special and self.special.get("effect") == "broadside"
        if is_broadside:
            # <<< PLAY SOUND >>>
            if self.attack_sound:
                self.attack_sound.play()
            # <<< END PLAY SOUND >>>
            self.last_attack_time = current_time # Update time since we are firing
            initial_damage = random.uniform(self.base_damage_min, self.base_damage_max) * damage_multiplier 
            is_crit = False 
            
            cannons_per_side = self.special.get("cannons_per_side", 1)
            #print(f"Tower {self.tower_id} firing timed BROADSIDE ({cannons_per_side} cannons per side)")
            
            # Fire direction: Left (-1, 0) and Right (1, 0)
            left_dir_angle = 180 
            right_dir_angle = 0  
            
            # Side offset distance (how far left/right from center)
            side_offset_dist = self.width_pixels / 2 
            
            # Vertical spacing along the side
            # Use tower height for spacing reference
            vertical_spacing = self.height_pixels * 0.75 / max(1, cannons_per_side) # Spread along 75% of height
            start_vert_offset = - (vertical_spacing * (cannons_per_side - 1)) / 2 # Center the group vertically
            
            proj_speed = self.projectile_speed
            projectile_id = self.tower_data.get('projectile_asset_id', self.tower_id)

            for i in range(cannons_per_side):
                current_vert_offset = start_vert_offset + i * vertical_spacing
                
                # Calculate origin points offset HORIZONTALLY and spaced VERTICALLY
                origin_x_left = self.x - side_offset_dist
                origin_x_right = self.x + side_offset_dist
                origin_y = self.y + current_vert_offset # Apply vertical spacing offset to tower's Y center
                
                # Create left projectile (fires left from LEFT side)
                proj_l = Projectile(origin_x_left, origin_y, initial_damage, proj_speed, projectile_id,
                                   direction_angle=left_dir_angle, max_distance=self.range,
                                   splash_radius=effective_splash_radius_pixels, source_tower=self, is_crit=is_crit,
                                   special_effect=self.special,
                                   damage_type=self.damage_type, asset_loader=self.asset_loader)
                results['projectiles'].append(proj_l)
                
                # Create right projectile (fires right from RIGHT side)
                proj_r = Projectile(origin_x_right, origin_y, initial_damage, proj_speed, projectile_id,
                                   direction_angle=right_dir_angle, max_distance=self.range,
                                   splash_radius=effective_splash_radius_pixels, source_tower=self, is_crit=is_crit,
                                   special_effect=self.special,
                                   damage_type=self.damage_type, asset_loader=self.asset_loader)
                results['projectiles'].append(proj_r)
            return results # Broadside handled
        # --- End Broadside Handling ---

        # --- Standard Attack Logic (Requires Target) --- 
        if self.attack_type != 'beam': # Exclude beam, broadside already handled
            # <<< MODIFIED: Added check to allow whip attack type without target >>>
            if not target and self.attack_type != 'whip': 
                 #print(f"ERROR: Tower {self.tower_id} attack called without target (and not broadside/whip).") # Updated print
                 return None # Should not happen if called correctly from GameScene

            # --- NEW: Miss Chance Check --- 
            if self.special and self.special.get("effect") == "miss_chance":
                miss_chance = self.special.get("chance", 0)
                if random.random() * 100 < miss_chance:
                    #print(f"Tower {self.tower_id} MISSED due to {miss_chance}% miss chance!")
                    # Play miss sound if available
                    if hasattr(self, 'miss_sound') and self.miss_sound:
                        self.miss_sound.play()
                    
                    # Create floating text effect for MISS!
                    try:
                        # Calculate position (above tower center)
                        text_x = self.x
                        text_y = self.y - (self.height_pixels / 2) # Start above tower center
                        
                        miss_text = "MISFIRE!"
                        miss_color = (255, 0, 0) # Red color
                        text_effect = FloatingTextEffect(text_x, text_y, miss_text, 
                                                       duration=1.5, 
                                                       color=miss_color, 
                                                       font_size=40, 
                                                       rise_speed=30)
                        self.game_scene_add_effect_callback(text_effect)
                    except Exception as e:
                        #print(f"Error creating miss text effect: {e}")
                        pass
                    
                    self.last_attack_time = current_time # Consume the attack cooldown
                    return None # Return None to prevent any attack effects
            # --- END Miss Chance Check ---

            # --- Check for Salvo Attack Initiation --- 
            if is_salvo_tower:
                # <<< PLAY SOUND (First Shot) >>>
                if self.attack_sound:
                    self.attack_sound.play()
                # <<< END PLAY SOUND >>>
                # Only start a new salvo if one isn't already in progress (checked above)
                #print(f"Tower {self.tower_id} initiating SALVO attack on {target.enemy_id}")
                # Calculate damage for the *first* shot
                initial_damage, is_crit = self.calculate_damage(target, buffed_stats, current_time, damage_multiplier=damage_multiplier)
                
                # Fire the first projectile
                first_projectile = Projectile(self.x, self.y, initial_damage, self.projectile_speed, 
                                                self.tower_data.get('projectile_asset_id', self.tower_id),
                                                target_enemy=target, 
                                                splash_radius=effective_splash_radius_pixels, # Use buffed splash 
                                                source_tower=self, is_crit=is_crit, 
                                                special_effect=self.special,
                                                damage_type=self.damage_type,
                                                bounces_remaining=self.bounce,
                                                bounce_range_pixels=self.bounce_range_pixels,
                                                bounce_damage_falloff=self.bounce_damage_falloff,
                                                pierce_adjacent=self.pierce_adjacent,
                                                asset_loader=self.asset_loader)
                results['projectiles'].append(first_projectile)
                
                # Set up salvo state
                salvo_count = self.special.get("salvo_count", 1)
                salvo_interval = self.special.get("salvo_interval", 0.1)
                self.salvo_shots_remaining = max(0, salvo_count - 1) # Start count for remaining shots
                self.salvo_next_shot_time = current_time + salvo_interval
                self.salvo_target = target # Store the initial target
                self.last_attack_time = current_time # Reset main attack timer (reload)
                
                return results # Return immediately after first shot
            # --- END Salvo Check --- 

            # --- Shotgun Logic --- 
            elif self.special and self.special.get("effect") == "shotgun":
                # <<< PLAY SOUND >>>
                if self.attack_sound:
                    self.attack_sound.play()
                # <<< END PLAY SOUND >>>
                self.last_attack_time = current_time
                pellets = self.special.get("pellets", 1)
                spread_angle_degrees = self.special.get("spread_angle", 15)
                spread_angle_rad = math.radians(spread_angle_degrees)

                # Calculate base damage ONCE for all pellets in this shot
                initial_damage, is_crit = self.calculate_damage(target, buffed_stats, current_time, damage_multiplier=damage_multiplier)

                # Calculate base direction towards the target
                dx = target.x - self.x
                dy = target.y - self.y
                base_angle_rad = math.atan2(dy, dx) # Use dy, dx for atan2

                projectile_id = self.tower_data.get('projectile_asset_id', self.tower_id)

                #print(f"Tower {self.tower_id} firing SHOTGUN ({pellets} pellets, spread {spread_angle_degrees} deg) at {target.enemy_id}")

                for _ in range(pellets):
                    # Calculate random offset within the spread angle
                    angle_offset = random.uniform(-spread_angle_rad / 2, spread_angle_rad / 2)
                    pellet_angle_rad = base_angle_rad + angle_offset
                    # Convert to degrees for the Projectile constructor
                    pellet_angle_degrees = math.degrees(pellet_angle_rad)

                    # Create a non-homing projectile for each pellet
                    pellet_projectile = Projectile(
                        self.x, self.y, initial_damage, self.projectile_speed,
                        projectile_id,
                        target_enemy=None, # Not homing
                        direction_angle=pellet_angle_degrees, # Fire in calculated direction
                        max_distance=self.range,
                        splash_radius=0, # Pellets typically don't splash individually
                        source_tower=self, is_crit=is_crit,
                        special_effect=None, # Pellets don't inherit the shotgun special
                        damage_type=self.damage_type,
                        # Pellets generally don't bounce/pierce unless specified
                        bounces_remaining=0, 
                        pierce_adjacent=0,
                        asset_loader=self.asset_loader,
                        is_visual_only=False
                    )
                    results['projectiles'].append(pellet_projectile)
                
                return results # Shotgun attack handled
            # --- END Shotgun Logic ---
            
            # --- BEGIN Apply Mark Logic --- REVERTED TO USE PASSED TARGET
            elif self.special and self.special.get("effect") == "apply_mark":
                # Relies on GameScene passing the correct target
                if target:
                    self.last_attack_time = current_time # Update attack time only if target found
                    mark_status_effect = self.special.get("mark_status_effect", "marked_for_death")
                    mark_duration = self.special.get("mark_duration", 0.3) 
                    #print(f"Tower {self.tower_id} applying mark '{mark_status_effect}' to {target.enemy_id} for {mark_duration}s")
                    target.apply_status_effect(mark_status_effect, mark_duration, 1.0, current_time)
                    # <<< PLAY SOUND (Mark Apply) >>>
                    if self.attack_sound:
                         self.attack_sound.play()
                    # <<< END PLAY SOUND >>>
                # else: # Debugging if target is None
                    # print(f"Tower {self.tower_id} tried to apply mark, but no target was passed.")
                    
                return None # No damage/projectiles, just applied the mark
            # --- END Apply Mark Logic ---
            
            # --- NEW: Quillspray Logic ---
            elif self.special and self.special.get("effect") == "quillspray":
                # <<< PLAY SOUND >>>
                if self.attack_sound:
                    self.attack_sound.play()
                # <<< END PLAY SOUND >>>
                self.last_attack_time = current_time # Update attack time
                quill_count = self.special.get("quill_count", 1) # Get count, default to 1 if missing
                # Use specific projectile asset if defined, otherwise default
                projectile_id = self.tower_data.get('projectile_asset_id', self.tower_id) 
                projectile_speed = self.projectile_speed if self.projectile_speed is not None else 100 # Default speed if None

                # Calculate base damage ONCE for all quills in this spray
                initial_damage, is_crit = self.calculate_damage(target, buffed_stats, current_time, damage_multiplier=damage_multiplier)

                #print(f"Tower {self.tower_id} firing QUILLSPRAY ({quill_count} quills, ProjID: {projectile_id})")

                angle_increment = 360.0 / quill_count # Spread evenly in 360 degrees

                for i in range(quill_count):
                    quill_angle_degrees = angle_increment * i

                    # Create a non-homing projectile for each quill
                    quill_projectile = Projectile(
                        self.x, self.y, initial_damage, projectile_speed,
                        projectile_id,
                        target_enemy=None, # Not homing
                        direction_angle=quill_angle_degrees, # Fire in calculated direction
                        max_distance=self.range, # Use tower's range
                        splash_radius=0, # Quills typically don't splash individually
                        source_tower=self,
                        is_crit=is_crit,
                        special_effect=None, # Special is the firing pattern, not on the quill itself
                        damage_type=self.damage_type,
                        asset_loader=self.asset_loader,
                        is_visual_only=False
                    )
                    results['projectiles'].append(quill_projectile)

                return results # Quillspray attack handled
            # --- END Quillspray Logic ---

            # <<< --- ADDED WHIP ATTACK LOGIC --- >>>
            elif self.attack_type == 'whip':
                #print(f"DEBUG: Entered whip attack block for {self.tower_id} at time {current_time:.2f}")
                # Whip logic needs to find its own targets within range
                whip_targets_in_range = []
                for enemy in all_enemies:
                    if enemy.health > 0 and enemy.type in self.targets and self.is_in_range(enemy.x, enemy.y):
                        whip_targets_in_range.append(enemy)

                if not whip_targets_in_range:
                    #print(f"  DEBUG: Whip attack - No targets found in range.")
                    self.last_attack_time = current_time # Still update cooldown even if no target found?
                    return results # No targets, nothing to do

                # --- Play Sound ---
                if self.attack_sound:
                    self.attack_sound.play()
                # --- End Play Sound ---

                self.last_attack_time = current_time # Update attack time

                # Sort targets by distance (closest first)
                whip_targets_in_range.sort(key=lambda e: (e.x - self.x)**2 + (e.y - self.y)**2)

                # Get whip parameters from special
                max_whip_targets = self.special.get("whip_targets", 1)
                damage_multiplier_first = self.special.get("whip_damage_multiplier", 0.5)
                visual_duration = self.special.get("whip_visual_duration", 0.2)

                # Select actual targets up to the max count
                actual_whip_targets = whip_targets_in_range[:max_whip_targets]
                target_ids = [t.enemy_id for t in actual_whip_targets]
                #print(f"  DEBUG: Whip attacking targets: {target_ids}")

                # Create visual path (adjusting for screen offset)
                visual_path = [(self.x + grid_offset_x, self.y + grid_offset_y)] # Start at tower center (screen coords)
                
                # Apply damage
                for i, whip_target in enumerate(actual_whip_targets):
                    # Calculate base damage (needs buffed stats)
                    # Assume calculate_damage is safe to call even if target was initially None
                    base_whip_damage, is_crit = self.calculate_damage(whip_target, buffed_stats, current_time, damage_multiplier=damage_multiplier)
                    
                    # Apply multiplier (last target gets full damage, others get reduced)
                    final_damage = base_whip_damage
                    if i < len(actual_whip_targets) - 1: # If not the last target
                        final_damage *= damage_multiplier_first
                    
                    #print(f"    DEBUG: Whipping {whip_target.enemy_id} for {final_damage:.2f} damage (Multiplier: {damage_multiplier_first if i < len(actual_whip_targets) - 1 else 1.0})")
                    # Pass tower special for potential on-hit effects
                    whip_target.take_damage(final_damage, self.damage_type, source_special=self.special)
                    
                    # Add target position to visual path (screen coords)
                    visual_path.append((whip_target.x + grid_offset_x, whip_target.y + grid_offset_y))

                # Create whip visual effect
                if len(visual_path) > 1:
                    results["type"] = "whip_visual" # Signal to GameScene
                    results["visual_path"] = visual_path
                    results["duration"] = visual_duration
                    #   print(f"  DEBUG: Created whip visual effect with {len(visual_path)} points.")

                return results # Whip attack handled
            # <<< --- END WHIP ATTACK LOGIC --- >>>

            # --- Harpoon Attack Logic ---
            elif self.attack_type == 'harpoon':
                # <<< PLAY SOUND >>>
                if self.attack_sound:
                    self.attack_sound.play()
                # <<< END PLAY SOUND >>>
                self.last_attack_time = current_time # Update attack time
                
                # Create the harpoon projectile
                harpoon = HarpoonProjectile(
                    self.x, self.y, target, self, self.special
                )
                results['projectiles'].append(harpoon)
                return results
            # --- END Harpoon Attack Logic ---

            # --- Gattling Level Up & Visual Effect Logic --- 
            is_gattling = self.special and self.special.get("effect") == "gattling_spin_up"
            if is_gattling:
                # <<< PLAY SOUND >>>
                if self.attack_sound:
                    self.attack_sound.play()
                # <<< END PLAY SOUND >>>
                # --- Gattling Level Up Logic --- 
                self.gattling_last_attack_time = current_time 
                max_level = self.special.get("levels", 0)
                if self.gattling_level < max_level: 
                    time_needed_per_level = self.special.get("time_per_level_sec", 1.5)
                    if self.gattling_continuous_fire_start_time == 0.0:
                        self.gattling_continuous_fire_start_time = current_time
                        #print(f"Gattling {self.tower_id} started spinning up.")
                    time_needed_for_next_level = time_needed_per_level * (self.gattling_level + 1)
                    if current_time - self.gattling_continuous_fire_start_time >= time_needed_for_next_level:
                        self.gattling_level += 1
                        #print(f"Gattling {self.tower_id} reached Level {self.gattling_level}!")
                # --- END Gattling Level Up --- 
                
                # Calculate damage for the gattling attack
                initial_damage, is_crit = self.calculate_damage(target, buffed_stats, current_time, damage_multiplier=damage_multiplier)
                
                # --- Gattling Dual Projectile Visual --- 
                if self.attack_type == 'projectile':
                    visual_offset_x = 10 # Pixels offset from center for visual streams
                    origin_left = (self.x - visual_offset_x, self.y)
                    origin_right = (self.x + visual_offset_x, self.y)
                    projectile_asset_id = self.tower_data.get('projectile_asset_id', self.tower_id)
                    
                    # Real Projectile (Left)
                    real_projectile = Projectile(origin_left[0], origin_left[1], initial_damage, self.projectile_speed, 
                                                   projectile_asset_id, target_enemy=target, 
                                                   splash_radius=effective_splash_radius_pixels, 
                                                   source_tower=self, is_crit=is_crit, 
                                                   special_effect=self.special,
                                                   damage_type=self.damage_type, 
                                                   bounces_remaining=self.bounce,
                                                   bounce_range_pixels=self.bounce_range_pixels,
                                                   bounce_damage_falloff=self.bounce_damage_falloff,
                                                   pierce_adjacent=self.pierce_adjacent,
                                                   asset_loader=self.asset_loader, 
                                                   is_visual_only=False)
                    results['projectiles'].append(real_projectile)
                    
                    # Visual Projectile (Right)
                    visual_projectile = Projectile(origin_right[0], origin_right[1], 0, self.projectile_speed, # Damage 0 
                                                     projectile_asset_id, target_enemy=target, 
                                                     splash_radius=0, # No splash for visual 
                                                     source_tower=self, is_crit=False, # No crit visual 
                                                     special_effect=self.special,
                                                     damage_type=self.damage_type, # Type doesn't matter much
                                                     bounces_remaining=self.bounce,
                                                     bounce_range_pixels=self.bounce_range_pixels,
                                                     bounce_damage_falloff=self.bounce_damage_falloff,
                                                     pierce_adjacent=self.pierce_adjacent,
                                                     asset_loader=self.asset_loader, 
                                                     is_visual_only=True) # Mark as visual only
                    results['projectiles'].append(visual_projectile)
                    # Skip the standard projectile creation below for gattling
            # --- END Gattling Logic --- 
            
            # --- Standard Projectile Creation / Instant Damage (if NOT gattling projectile) --- 
            else: # This else now correctly signifies it's NOT broadside, salvo, shotgun, quillspray
                # <<< INSERT DAMAGE CALCULATION HERE >>>
                self.last_attack_time = current_time # Update attack time HERE for standard attacks
                initial_damage, is_crit = self.calculate_damage(target, buffed_stats, current_time, damage_multiplier=damage_multiplier)
                # <<< END INSERT DAMAGE CALCULATION >>>

                # --- Specific Tower Effect Creation (On Attack) --- 
                if self.tower_id == "zork_horde_hurler":
                    orb_effect = OrbitingOrbsEffect(target, duration=2.0, num_orbs=4)
                    results['effects'].append(orb_effect)
                # --- END Specific Tower Effect Creation ---

                # Check attack type *after* calculating damage
                # <<< FIX INDENTATION START >>>
                if self.attack_type == 'projectile' and not is_gattling:
                    # --- Check for Offset Boomerang ---
                    if self.special and self.special.get("effect") == "offset_boomerang_path":
                        # <<< PLAY SOUND >>>
                        if self.attack_sound:
                            self.attack_sound.play()
                        # <<< END PLAY SOUND >>>
                        self.last_attack_time = current_time # Update attack time
                        # Calculate direction angle to the initial target
                        if not target:
                            #print(f"Warning: Boomeranger {self.tower_id} has no target for initial angle.")
                            return results # Cannot fire without target for angle
                        dx = target.x - self.x
                        dy = target.y - self.y
                        initial_angle_degrees = math.degrees(math.atan2(dy, dx))

                        # Get specific boomerang parameters from special
                        hit_cooldown = self.special.get("hit_cooldown", 0.5)
                        offset_distance = self.special.get("return_offset_distance", 50)
                        projectile_asset_id = self.special.get("projectile_asset_id", self.tower_id) # Use specific or default
                        
                        # Damage is calculated per-hit inside the boomerang class, so pass min/max
                        # Use base damage from tower, buffs don't apply directly to boomerang creation
                        damage_min = self.base_damage_min
                        damage_max = self.base_damage_max
                        
                        #print(f"Tower {self.tower_id} firing OFFSET BOOMERANG (ProjID: {projectile_asset_id})")

                        boomerang = OffsetBoomerangProjectile(
                            source_tower=self,
                            initial_direction_angle=initial_angle_degrees,
                            range_pixels=self.range, # Use tower's range
                            speed=self.projectile_speed,
                            damage_min=damage_min,
                            damage_max=damage_max,
                            damage_type=self.damage_type,
                            hit_cooldown=hit_cooldown,
                            asset_id=projectile_asset_id,
                            offset_distance=offset_distance,
                            asset_loader=self.asset_loader # Pass the loader function
                        )
                        results['projectiles'].append(boomerang)
                    # --- Check for Pass-Through Exploder ---
                    elif self.special and self.special.get("effect") == "fixed_distance_pass_through_explode":
                        # <<< PLAY SOUND >>> 
                        if hasattr(self, 'pass_through_launch_sound') and self.pass_through_launch_sound:
                            self.pass_through_launch_sound.play()
                        # <<< END PLAY SOUND >>> 
                        self.last_attack_time = current_time # Update attack time
                        
                        # Create the exploder
                        exploder = PassThroughExploder(
                            parent_tower=self,
                            target_enemy=target,
                            special_data=self.special,
                            asset_loader=self.asset_loader
                        )
                        
                        # Set up the effect callback
                        exploder.game_scene_add_effect_callback = self.game_scene_add_effect_callback
                        
                        # Add to results
                        results['projectiles'].append(exploder)
                        
                        # Add to game scene's exploders list
                        self.game_scene_add_exploder_callback(exploder)
                    # --- Check for Grenade Launcher ---
                    elif self.special and self.special.get("effect") == "grenade_launcher":
                        # Play attack sound if available
                        if hasattr(self, 'attack_sound') and self.attack_sound:
                            self.attack_sound.play()
                        
                        # Calculate base direction to target
                        dx = target.x - self.x
                        dy = target.y - self.y
                        base_angle = math.atan2(dy, dx)
                        
                        # Add random spread (30 degrees in either direction)
                        spread_angle = random.uniform(-30, 30) * (math.pi / 180)  # Convert to radians
                        direction_angle = base_angle + spread_angle
                        
                        # Create grenade projectile
                        grenade = GrenadeProjectile(
                            start_x=self.x,
                            start_y=self.y,
                            damage=initial_damage,
                            speed=self.projectile_speed,
                            projectile_id="police_grenade_launcher",
                            direction_angle=direction_angle,
                            max_distance=self.range,
                            splash_radius=self.splash_radius,
                            source_tower=self,
                            is_crit=is_crit,
                            special_effect=self.special,
                            damage_type=self.damage_type,
                            asset_loader=self.asset_loader,  # Use tower's asset loader
                            detonation_time=self.special.get("detonation_time", 2.0),
                            max_bounces=self.special.get("max_bounces", 3),
                            bounce_speed_loss=self.special.get("bounce_speed_loss", 0.2),
                            explosion_radius=self.special.get("explosion_radius", 100)
                        )
                        
                        results['projectiles'].append(grenade)
                    else:
                        # --- Normal Projectile Creation ---
                        # <<< PLAY SOUND >>>
                        if self.attack_sound:
                            self.attack_sound.play()
                        # <<< END PLAY SOUND >>>
                        # Update attack time here if it's NOT a boomerang
                        # self.last_attack_time = current_time # Already set above this else block
                        projectile = Projectile(self.x, self.y, initial_damage, self.projectile_speed, 
                                              self.tower_data.get('projectile_asset_id', self.tower_id),
                                              target_enemy=target, 
                                              splash_radius=effective_splash_radius_pixels, 
                                              source_tower=self, is_crit=is_crit, 
                                              special_effect=self.special,
                                              damage_type=self.damage_type,
                                              bounces_remaining=self.bounce,
                                              bounce_range_pixels=self.bounce_range_pixels,
                                              bounce_damage_falloff=self.bounce_damage_falloff,
                                              pierce_adjacent=self.pierce_adjacent,
                                              asset_loader=self.asset_loader,
                                              is_visual_only=False) 
                        results['projectiles'].append(projectile)
                elif self.attack_type == 'instant':
                    #print(f"DEBUG: Executing INSTANT attack for {self.tower_id}") # <<< ADDED DEBUG PRINT
                    # <<< PLAY SOUND >>>
                    if self.attack_sound:
                        self.attack_sound.play()
                    # <<< END PLAY SOUND >>>
                    
                    # <<< ADD ARMOR IGNORE LOGIC HERE (BEFORE DAMAGE) >>>
                    effective_armor_ignore = 0 # Default to 0
                    if self.special: # Check if special exists first
                        effect_type = self.special.get("effect")
                        # Handle Samurai's CHANCE to ignore armor
                        if effect_type == "chance_ignore_armor_on_hit" and self.tower_id == 'tac_samurai_mech':
                            chance = self.special.get("chance_percent", 25)
                            if random.random() * 100 < chance:
                                if hasattr(self, 'ignore_armor_sound') and self.ignore_armor_sound:
                                    self.ignore_armor_sound.play()
                                effective_armor_ignore = self.special.get("ignore_amount", 15)
                                #print(f"Samurai Mech ({self.tower_id}) triggered CHANCE ARMOR IGNORE! (Ignoring {effective_armor_ignore} armor)")
                        # Handle GUARANTEED ignore armor (like Archangel)
                        elif effect_type == "ignore_armor_on_hit": 
                            effective_armor_ignore = self.special.get("amount", 0) # Use 'amount' key from JSON
                            if effective_armor_ignore > 0:
                                #print(f"Tower ({self.tower_id}) applying GUARANTEED ARMOR IGNORE! (Ignoring {effective_armor_ignore} armor)")
                                pass
                    # <<< END ARMOR IGNORE LOGIC >>>
                            
                    # <<< ADD PRIMARY INSTANT DAMAGE APPLICATION HERE >>>
                    if initial_damage > 0:
                        # Apply only base damage and type here.
                        # Special effects like stun/DoT are handled later or by source_special in take_damage.
                        # <<< PASS source_special AND ignore amount HERE >>>
                        target.take_damage(
                            initial_damage, 
                            self.damage_type, 
                            source_special=self.special, 
                            ignore_armor_amount=effective_armor_ignore # Pass the calculated ignore amount
                        )
                        # Keep the kill count check associated with this primary damage application.
                        damage_result = {'was_killed': target.health <= 0} # Simplification, assuming take_damage modified health
                        if damage_result.get("was_killed", False):
                            self.kill_count += 1
                            #print(f"+++ Kill registered for Tower {self.tower_id} (via instant attack). Total kills: {self.kill_count}")
                            # If target is killed by first hit, don't proceed to double strike
                            was_killed_by_first_hit = True
                        else:
                            was_killed_by_first_hit = False
                    else:
                        was_killed_by_first_hit = False
                    # <<< END PRIMARY INSTANT DAMAGE >>>

                    # <<< ADD DOUBLE STRIKE LOGIC HERE (for Instant Attacks) >>>
                    if not was_killed_by_first_hit and self.special and self.special.get("effect") == "double_strike":
                        chance = self.special.get("chance_percent", 20) # Default 20%
                        if random.random() * 100 < chance:
                            # <<< PLAY DOUBLE STRIKE SOUND >>>
                            if hasattr(self, 'double_strike_sound') and self.double_strike_sound:
                                self.double_strike_sound.play()
                            # <<< END PLAY SOUND >>>
                            #print(f"Double Strike triggered on {target.enemy_id} with {chance:.0f}% chance! Applying second hit.")
                            # Apply the same damage again
                            if initial_damage > 0:
                                # Pass special again in case take_damage needs it for armor ignore etc.
                                # <<< PASS ignore amount HERE TOO FOR SECOND HIT >>>
                                second_damage_result = target.take_damage(
                                    initial_damage, 
                                    self.damage_type, 
                                    source_special=self.special,
                                    ignore_armor_amount=effective_armor_ignore # Pass ignore amount for second hit
                                )
                                # Check for kill on second hit
                                if second_damage_result.get("was_killed", False):
                                    self.kill_count += 1
                                    #print(f"+++ Kill registered for Tower {self.tower_id} (via double strike). Total kills: {self.kill_count}")

                    
                    # Apply INSTANT special effects (DoT, Max HP Reduction, etc.)
                    self.apply_instant_special_effects(target, current_time) 
                    
                    # --- Try to Create Projectile-Style Visual First ---
                    try:
                        # Try to get projectile image using tower_id like projectiles do
                        projectile_img = self.asset_loader.get_projectile_image(self.tower_id)
                        if projectile_img:
                            # Calculate angle from tower to target
                            dx = target.x - self.x
                            dy = target.y - self.y
                            angle = math.degrees(math.atan2(-dy, dx))
                            
                            # Create projectile-style effect
                            projectile_effect = Effect(
                                target.x + grid_offset_x,
                                target.y + grid_offset_y,
                                projectile_img,
                                duration=0.1,  # Short duration
                                target_size=(GRID_SIZE * 2, GRID_SIZE * 2),  # Scale up for storm generator
                                hold_duration=0.1,  # Hold for 0.1s
                                rotation=angle  # Rotate to point from tower to target
                            )
                            results['effects'].append(projectile_effect)
                            #print(f"Created projectile-style visual for {self.tower_id} instant attack")
                    except Exception as e:
                        pass
                        # Fall through to normal instant attack visual handling
                    
                    # --- Fallback to Normal Instant Attack Visual Effect --- 
                    visual_effect_name = self.tower_data.get("attack_visual_effect")
                    if visual_effect_name and visual_assets: # Check if name and assets exist
                        visual_img = visual_assets.get(visual_effect_name)
                        if visual_img:
                            #print(f"... creating instant visual effect '{visual_effect_name}' at target {target.enemy_id}")
                            # Calculate screen coordinates
                            effect_x = target.x + grid_offset_x
                            effect_y = target.y + grid_offset_y
                            
                            # Get hold duration from tower data, default to 0.1 if not specified
                            hold_duration = self.tower_data.get("instant_hold", 0.1)
                            
                            # Create a standard fading effect
                            vis_effect = Effect(effect_x, effect_y, visual_img, 
                                                duration=0.5, # Example duration
                                                target_size=(GRID_SIZE, GRID_SIZE), # Example size
                                                hold_duration=hold_duration)
                            results['effects'].append(vis_effect)
                        else:
                            #print(f"Warning: Could not load visual asset '{visual_effect_name}' for tower {self.tower_id}")
                            pass
                    # --- End Instant Visual Effect ---

                    # --- Special Case: Storm Generator Lightning Bolt ---
                    if self.tower_id == "spark_storm_generator" and visual_assets:
                        try:
                            # Try to get the lightning bolt image from the projectiles directory
                            projectile_path = os.path.join("assets", "images", "projectiles", "spark_storm_generator.png")
                            lightning_img = self.asset_loader(projectile_path)
                            if lightning_img:
                                # Calculate angle from tower to target
                                dx = target.x - self.x
                                dy = target.y - self.y
                                angle = math.degrees(math.atan2(-dy, dx))
                                
                                # Get hold duration from tower data, default to 0.1 if not specified
                                hold_duration = self.tower_data.get("instant_hold", 0.1)
                                
                                # Create lightning effect
                                lightning_effect = Effect(
                                    target.x + grid_offset_x,
                                    target.y + grid_offset_y,
                                    lightning_img,
                                    duration=0.1,  # Very short duration
                                    target_size=(GRID_SIZE * 2, GRID_SIZE * 2),  # Scale up the lightning
                                    hold_duration=hold_duration  # Use the hold duration from tower data
                                )
                                # Store the rotation angle as a custom attribute
                                lightning_effect.rotation_angle = angle
                                # Override the draw method to handle rotation
                                original_draw = lightning_effect.draw
                                def rotated_draw(screen):
                                    if not lightning_effect.finished and lightning_effect.image:
                                        # Create a rotated copy of the image
                                        rotated_img = pygame.transform.rotate(lightning_effect.image, lightning_effect.rotation_angle)
                                        # Get the rect of the rotated image
                                        rotated_rect = rotated_img.get_rect(center=lightning_effect.rect.center)
                                        # Draw the rotated image
                                        screen.blit(rotated_img, rotated_rect)
                                lightning_effect.draw = rotated_draw
                                results['effects'].append(lightning_effect)
                        except Exception as e:
                            print(f"Note: Could not create lightning bolt visual for spark_storm_generator: {e}")
                    # --- End Storm Generator Lightning Bolt ---
                    
                    # --- Instant Splash Damage Logic --- 
                    effective_splash_radius_pixels = buffed_stats.get('splash_radius_pixels', 0)
                    if effective_splash_radius_pixels > 0 and initial_damage > 0: # Only splash if radius > 0 and damage > 0
                        splash_damage = initial_damage * 0.25 # 25% splash damage
                        splash_radius_sq = effective_splash_radius_pixels ** 2
                        primary_target_pos = (target.x, target.y)
                        #print(f"... Applying INSTANT splash (Radius: {effective_splash_radius_pixels:.1f}, Dmg: {splash_damage:.2f})")
                        
                        enemies_splashed = 0
                        for enemy in all_enemies:
                            # Skip primary target and dead enemies
                            if enemy == target or enemy.health <= 0:
                                continue
                                
                            dist_sq = (enemy.x - primary_target_pos[0])**2 + (enemy.y - primary_target_pos[1])**2
                            if dist_sq <= splash_radius_sq:
                                #print(f"    ... splashing {enemy.enemy_id} for {splash_damage:.2f}")
                                # Pass the tower's special dict to take_damage for instant splash attacks
                                splash_damage_result = enemy.take_damage(splash_damage, self.damage_type, source_special=self.special)
                                # --- Check for Splash Kill & Increment Count --- # NEW
                                if splash_damage_result.get("was_killed", False):
                                     self.kill_count += 1 # Attributed to the tower that caused the splash
                                     #print(f"+++ Kill registered for Tower {self.tower_id} (via instant splash). Total kills: {self.kill_count}")
                                # --- End Check --- 
                                # Also apply instant special effects (like stun) to splashed targets?
                                self.apply_instant_special_effects(enemy, current_time) 
                                enemies_splashed += 1
                        if enemies_splashed > 0:
                             #print(f"... splashed {enemies_splashed} enemies.")
                             pass
                    # --- End Instant Splash ---

                    # --- Chain Lightning Logic (for instant attack) ---
                    if self.special and self.special.get("effect") == "chain_lightning":
                        max_jumps = self.special.get("chain_targets", 3)
                        radius_units = self.special.get("chain_radius", 250)
                        damage_falloff = self.special.get("chain_damage_falloff", 0.3)
                        radius_pixels_sq = (radius_units * (GRID_SIZE / 200.0)) ** 2

                        current_chain_target = target # Start chain from the initial target
                        current_chain_damage = initial_damage # Use damage dealt to primary target
                        targets_hit = {target} # Keep track of enemies already hit
                        # Start visual path from tower to first target
                        chain_path_visual = [(self.x, self.y), (current_chain_target.x, current_chain_target.y)] 

                        #print(f"... Initiating chain lightning from {current_chain_target.enemy_id} (Radius: {math.sqrt(radius_pixels_sq):.1f}px)")

                        for _ in range(max_jumps):
                            next_target = None
                            min_dist_sq = float('inf')

                            # Find the closest valid enemy within range of the *current chain target*
                            for enemy in all_enemies:
                                if enemy not in targets_hit and enemy.health > 0:
                                    # Check if enemy type is valid for this tower
                                    if enemy.type not in self.targets:
                                        continue
                                    # Check distance from the *current* chain target
                                    dist_sq = (enemy.x - current_chain_target.x)**2 + (enemy.y - current_chain_target.y)**2
                                    if dist_sq <= radius_pixels_sq and dist_sq < min_dist_sq:
                                        min_dist_sq = dist_sq
                                        next_target = enemy

                            if next_target:
                                # Apply falloff
                                current_chain_damage *= (1.0 - damage_falloff)
                                #print(f"    ... chaining to {next_target.enemy_id} for {current_chain_damage:.2f} damage")
                                # Pass the tower's special dict to take_damage for chain lightning attacks
                                chain_damage_result = next_target.take_damage(current_chain_damage, self.damage_type, source_special=self.special)
                                # --- Check for Chain Kill & Increment Count --- # NEW
                                if chain_damage_result.get("was_killed", False):
                                    self.kill_count += 1 # Attributed to the tower that started the chain
                                    #print(f"+++ Kill registered for Tower {self.tower_id} (via chain lightning). Total kills: {self.kill_count}")
                                # --- End Check --- 
                                targets_hit.add(next_target)
                                chain_path_visual.append((next_target.x, next_target.y)) # Add position for visual
                                current_chain_target = next_target # Move to the next link
                            else:
                                break # No more valid targets found

                        # Create the visual effect if chain jumped at least once
                        if len(chain_path_visual) > 2: 
                            # Adjust coordinates for screen offset before creating visual
                            adjusted_path = [(int(x + grid_offset_x), int(y + grid_offset_y)) for x, y in chain_path_visual]
                            chain_effect = ChainLightningVisual(adjusted_path, duration=0.3) # Use existing visual
                            results['effects'].append(chain_effect)
                    # --- END Chain Lightning Logic ---

        # --- Special Projectile Types ---
        if self.special and self.special.get("effect") == "cluster_shot":
            # Create cluster projectile
            cluster = ClusterProjectile(
                start_x=self.x,
                start_y=self.y,
                damage=initial_damage,
                speed=self.projectile_speed,
                projectile_id=self.tower_data.get('projectile_asset_id', self.tower_id),
                direction_angle=math.atan2(-(target.y - self.y), target.x - self.x),
                max_distance=self.range,
                splash_radius=effective_splash_radius_pixels,
                source_tower=self,
                is_crit=is_crit,
                special_effect=self.special,
                damage_type=self.damage_type,
                asset_loader=self.asset_loader,
                pellets=self.special.get("pellets", 5),
                spread_angle=self.special.get("spread_angle", 30),
                detonation_time=self.special.get("detonation_time", 2.0),
                explosion_radius=self.special.get("explosion_radius", 100)
            )
            results['projectiles'].append(cluster)
            return results

        # --- Beam Logic --- 
        # ... (existing beam logic - sound doesn't make sense here) ...

        # Calculate initial damage
        initial_damage, is_crit = self.calculate_damage(target, buffed_stats, current_time)
        
        # Apply primary damage for instant attacks here -- THIS LINE SHOULD BE REMOVED
        # target.take_damage(initial_damage, self.damage_type) # REMOVED
        
        # Check for double strike special effect
        if self.special and self.special.get("effect") == "double_strike":
            chance = self.special.get("chance_percent", 20)
            if random.random() * 100 < chance:
                # Create double strike effect
                double_strike = DoubleStrikeEffect(self, target, initial_damage, current_time)
                if self.game_scene_add_effect_callback:
                    self.game_scene_add_effect_callback(double_strike)
                #print(f"Double Strike triggered on {target.enemy_id} with {chance}% chance")
        # REMOVED else block that contained take_damage

        # Check for every_nth_strike special effect
        if self.special and self.special.get("effect") == "every_nth_strike":
            self.strike_counter += 1
            n = self.special.get("n", 5)
            bonus_damage = self.special.get("bonus_damage", 50)
            
            # REMOVED Apply normal damage call from here
            
            # Check if it's the nth strike
            if self.strike_counter >= n:
                # Create every_nth_strike effect
                nth_strike = EveryNthStrikeEffect(self, target, bonus_damage, current_time)
                if self.game_scene_add_effect_callback:
                    self.game_scene_add_effect_callback(nth_strike)
                #print(f"Every Nth Strike triggered on {target.enemy_id} (strike {self.strike_counter})")
                self.strike_counter = 0  # Reset counter

        return results

    def apply_instant_special_effects(self, target, current_time):
        """Applies NON-projectile special effects directly (e.g., stun from instant attack)."""
        if not self.special or not target or target.health <= 0:
            return

        effect_type = self.special.get("effect")

        # --- Handle Max HP Reduction --- # <<<< ADDED HERE
        if effect_type == "max_hp_reduction_on_hit":
            percentage = self.special.get("reduction_percentage", 0)
            if percentage > 0 and hasattr(target, 'reduce_max_health'): # Changed method name check
                # Call the existing method on the enemy object
                target.reduce_max_health(percentage) # Use the correct method name
                # The log message is now handled inside Enemy.reduce_max_health
                # Potentially return an indicator if needed, otherwise just proceed

        # --- Handle DoT Effects ---
        # Using elif now, assuming an instant attack has only ONE primary special effect
        elif ("dot_damage" in self.special and 
            "dot_interval" in self.special and 
              "duration" in self.special):
            # Extract DoT parameters
            dot_name = effect_type if effect_type else "unknown_instant_dot" # Use effect_type as the DoT name
            base_dot_damage = self.special.get("dot_damage", 0)
            dot_interval = self.special.get("dot_interval", 1.0)
            dot_duration = self.special.get("duration", 1.0) # Use "duration" from JSON
            dot_damage_type = self.special.get("dot_damage_type", "normal")

            # Apply the DoT to the enemy
            if base_dot_damage > 0: # Only apply if damage is positive
                target.apply_dot_effect(
                    dot_name, base_dot_damage, dot_interval, 
                    dot_duration, dot_damage_type, current_time
                )
                #print(f"... instant attack applied {dot_name} DoT ({base_dot_damage}/{dot_interval}s for {dot_duration}s) to {target.enemy_id}")
        # --- End DoT Effects ---
        
    def draw(self, screen, tower_assets, offset_x=0, offset_y=0):
        """Draw the tower using its associated image, scaled to its grid footprint, with a border and offset."""
        draw_pixel_x = (self.top_left_grid_x * GRID_SIZE) + offset_x
        draw_pixel_y = (self.top_left_grid_y * GRID_SIZE) + offset_y

        # --- SPECIAL CASE: Pulse Animation for miasma_pillar and frost_pulse ---
        if self.tower_id in ['alchemists_miasma_pillar', 'igloo_frost_pulse']:
            current_time = pygame.time.get_ticks() / 1000.0  # Convert to seconds
            
            # Initialize pulse if not started
            if self.pulse_start_time == 0:
                self.pulse_start_time = current_time
            
            # Calculate pulse progress (0 to 1)
            pulse_progress = (current_time - self.pulse_start_time) / self.pulse_duration
            
            # Reset pulse if complete
            if pulse_progress >= 1.0:
                self.pulse_start_time = current_time
                pulse_progress = 0.0
            
            # Calculate expanding radius (0 to aura_radius)
            self.pulse_radius = int(self.aura_radius_pixels * pulse_progress)
            
            # Calculate fading alpha (255 to 0)
            self.pulse_alpha = int(255 * (1.0 - pulse_progress))
            
            # Draw the pulsing circle
            if self.pulse_radius > 0 and self.pulse_alpha > 0:
                try:
                    center_x = int(self.x + offset_x)
                    center_y = int(self.y + offset_y)
                    
                    # Create a surface for alpha blending
                    temp_surface = pygame.Surface((self.pulse_radius * 2, self.pulse_radius * 2), pygame.SRCALPHA)
                    
                    # Set color based on tower type
                    if self.tower_id == 'alchemists_miasma_pillar':
                        circle_color = (0, 255, 0, self.pulse_alpha)  # Green for miasma
                    else:  # igloo_frost_pulse
                        circle_color = (0, 200, 255, self.pulse_alpha)  # Light blue for frost
                    
                    pygame.draw.circle(temp_surface, circle_color, (self.pulse_radius, self.pulse_radius), self.pulse_radius, 6)
                    # Blit the temporary surface to the screen
                    screen.blit(temp_surface, (center_x - self.pulse_radius, center_y - self.pulse_radius))
                except Exception as e:
                    pass
                    #print(f"Error drawing pulse effect for {self.tower_id}: {e}")

            # --- Draw Ground Effect Zone for Nuclear Silo ---
            if self.tower_id == 'industry_nuclear_silo' and self.aura_radius_pixels > 0:
                try:
                    center_x = int(self.x + offset_x)
                    center_y = int(self.y + offset_y)
                    radius = int(self.aura_radius_pixels)
                    
                    # Create a surface for the ground effect zone
                    zone_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    # Draw a semi-transparent orange circle for the zone
                    zone_color = (255, 165, 0, 50)  # Orange with low opacity
                    pygame.draw.circle(zone_surface, zone_color, (radius, radius), radius)
                    # Blit the zone surface to the screen
                    screen.blit(zone_surface, (center_x - radius, center_y - radius))
                except Exception as e:
                    pass
                    #print(f"Error drawing nuclear silo ground effect zone: {e}")
        # --- End Pulse Animation and Ground Effect ---

        # --- Draw Creep Colony Glow --- 
        elif self.tower_id == "zork_creep_colony" and self.aura_radius_pixels > 0:
            center_x = int(self.x + offset_x)
            center_y = int(self.y + offset_y)
            radius = int(self.aura_radius_pixels)
            # Use config PURPLE with low alpha for faintness
            glow_color = (*PURPLE[:3], 51) # Alpha 51 (20% of 255)
            
            if radius > 0:
                try:
                    # Create a temporary surface for alpha blending
                    temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    # Draw the circle onto the center of the temporary surface
                    pygame.draw.circle(temp_surface, glow_color, (radius, radius), radius)
                    # Blit the temporary surface onto the main screen, centered correctly
                    screen.blit(temp_surface, (center_x - radius, center_y - radius))
                except Exception as e:
                    pass
                    #print(f"Error drawing creep colony glow effect: {e}")
        # --- End Creep Colony Glow --- 

        # --- NEW: Draw Heaven Radiant Tower Aura --- 
        elif self.tower_id == "heaven_radiant_tower" and self.aura_radius_pixels > 0:
            center_x = int(self.x + offset_x)
            center_y = int(self.y + offset_y)
            radius = int(self.aura_radius_pixels)
            # Define a light blue color with some transparency
            aura_color = (173, 216, 230, 80) # Light blue with 80 alpha (approx 31% opaque)
            
            if radius > 0:
                try:
                    # Create a temporary surface for alpha blending
                    temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    # Draw the circle onto the center of the temporary surface
                    pygame.draw.circle(temp_surface, aura_color, (radius, radius), radius, 2) # Draw outline (width 2)
                    # Blit the temporary surface onto the main screen, centered correctly
                    screen.blit(temp_surface, (center_x - radius, center_y - radius))
                except Exception as e:
                    pass
                    #print(f"Error drawing heaven_radiant_tower aura effect: {e}")
        # --- END Heaven Radiant Tower Aura --- 

        # --- Special Handling for Storm Generator Aura Visual Path --- 
        aura_visual_img = None # Initialize
        if self.tower_id == "spark_storm_generator":
            # Load storm effect specifically from assets/effects
            aura_visual_img = tower_assets.get_effect_image("storm_effect") 
            if not aura_visual_img:
                #print(f"WARNING: Failed to load storm_effect.png from assets/effects for {self.tower_id}")
                pass
        else:
            # Default path for other towers
            aura_visual_img = tower_assets.get_aura_visual(self.tower_id)

        # --- Draw Aura Visual (if applicable) --- 
        if aura_visual_img and self.aura_radius_pixels > 0:
            current_time_ms = pygame.time.get_ticks()
            
            # --- Calculate Base Target Size FIRST --- 
            base_target_diameter = int(self.aura_radius_pixels * 2)
            target_diameter = base_target_diameter # Initialize here
            
            # --- Set Defaults --- 
            rotation_speed_degrees = 30 # Default degrees per second
            use_mask = True
            pulsing_scale = False
            
            # --- Tower Specific Visuals --- 
            if self.tower_id == "spark_storm_generator":
                rotation_speed_degrees = 0 # No rotation for storm
                use_mask = False # Don't apply circular mask
                pulsing_scale = True # Enable pulsing scale
                
                # --- Lightning Flash Logic --- 
                # Initialize flash timer if it doesn't exist
                if not hasattr(self, 'next_flash_time'):
                    self.next_flash_time = 0
                    self.flash_duration = 0.2 # Seconds the flash stays visible (Increased)
                    self.flash_active = False
                    self.flash_image = None # Store the loaded image
                    
                # Check if it's time for a new flash attempt
                if current_time_ms >= self.next_flash_time:
                    if not self.flash_active:
                        # Random chance to flash
                        flash_chance_roll = random.random()
                        if flash_chance_roll < 0.15: # 15% chance per interval (Increased)
                            self.flash_active = True
                            self.flash_end_time = current_time_ms + self.flash_duration * 1000
                            # Load/prepare flash image only when needed
                            if not self.flash_image:
                                # This line loads the image using the asset manager
                                lightning_img_raw = tower_assets.get_effect_image("lightning_flash")
                                if lightning_img_raw:
                                    self.flash_image = lightning_img_raw
                                else:
                                    print("Warning: Failed to load 'lightning_flash.png' for storm generator.") # Added check
                        
                        # Schedule next flash attempt time (random interval)
                        self.next_flash_time = current_time_ms + random.randint(500, 2000) # 0.5 to 2 seconds
                    else:
                        # Flash is currently active, check if duration ended
                        if current_time_ms >= self.flash_end_time:
                            self.flash_active = False # Turn off flash
                            # Don't reset next_flash_time here, it was set when the flash started

                # Draw the flash if active and image is loaded
                if self.flash_active and self.flash_image:
                    # Scale flash to match the current pulsing aura size (using target_diameter)
                    flash_scaled = pygame.transform.smoothscale(self.flash_image, (target_diameter, target_diameter))
                    flash_rect = flash_scaled.get_rect(center=(int(self.x + offset_x), int(self.y + offset_y)))
                    screen.blit(flash_scaled, flash_rect.topleft)
                # --- End Lightning Flash --- 
                    
            # Add elif blocks here for other tower-specific aura visuals if needed

            # --- Calculate Rotation --- 
            if rotation_speed_degrees != 0:
                rotation_angle = (current_time_ms / 1000.0 * rotation_speed_degrees) % 360
                rotated_img = pygame.transform.rotate(aura_visual_img, rotation_angle)
            else:
                rotated_img = aura_visual_img # No rotation needed
                
            # Rotation changes size, get new rect centered at original position
            rotated_rect = rotated_img.get_rect(center=aura_visual_img.get_rect().center)
            
            # --- Conditionally Apply Circular Mask --- 
            image_to_process = None # Initialize variable
            if use_mask:
                mask_radius = min(rotated_img.get_width(), rotated_img.get_height()) // 2
                mask_surface = pygame.Surface(rotated_img.get_size(), pygame.SRCALPHA)
                pygame.draw.circle(mask_surface, (255, 255, 255, 255), rotated_rect.center, mask_radius)
                
                masked_rotated_img = pygame.Surface(rotated_img.get_size(), pygame.SRCALPHA)
                masked_rotated_img.blit(rotated_img, (0, 0))
                masked_rotated_img.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                image_to_process = masked_rotated_img # Use the masked image
            else:
                image_to_process = rotated_img # Use the raw (rotated or original) image

            # --- Calculate Target Size (Potentially Pulsing) --- 
            if pulsing_scale:
                pulse_duration_ms = 4000 # Slower pulse (4 seconds)
                pulse_range = 0.1 # Pulse between 90% and 110% of base size
                pulse_progress = (current_time_ms % pulse_duration_ms) / pulse_duration_ms
                scale_factor = 1.0 + pulse_range * math.sin(pulse_progress * math.pi * 2) # Use sine wave for smooth pulse
                target_diameter = int(base_target_diameter * scale_factor)

            fixed_alpha = 180 # Set a fixed transparency level (adjust as needed)

            # --- Scale and Apply Alpha --- 
            if target_diameter > 0 and image_to_process: # Check if image_to_process is valid
                try:
                    # Scale the chosen image to the fixed size
                    final_scaled_image = pygame.transform.smoothscale(image_to_process, (target_diameter, target_diameter))
                    final_scaled_image.set_alpha(fixed_alpha)
                    
                    # --- Draw the Final Image --- 
                    # Center the final visual on the tower's center pixel coords
                    final_rect = final_scaled_image.get_rect(center=(int(self.x + offset_x), int(self.y + offset_y)))
                    screen.blit(final_scaled_image, final_rect.topleft)
                except ValueError: 
                    pass 
                except Exception as e:
                    pass
                    #print(f"Error drawing rotated/scaled aura visual for {self.tower_id}: {e}")

        # Draw the tower image scaled to its full pixel size (drawn on top of aura/pulse)
        tower_assets.draw_tower(screen, self.tower_id, 
                              draw_pixel_x, draw_pixel_y, 
                              width=self.width_pixels, 
                              height=self.height_pixels, 
                              is_preview=False)
        
        # Draw a 2 pixel thick black border around the placed tower image
        border_rect = pygame.Rect(draw_pixel_x, draw_pixel_y, self.width_pixels, self.height_pixels)
        pygame.draw.rect(screen, BLACK, border_rect, 2) # 2 pixel thick black border

        # --- Draw Overlay Visual (if applicable) --- 
        # REMOVED: overlay_visual_img = tower_assets.get_overlay_visual(self.tower_id)
        # Check for the specifically loaded vortex image first
        if self.tower_id == "brine_vortex_monument" and self.vortex_overlay_image:
            # --- RE-ADDED ROTATION --- 
            current_time_ms = pygame.time.get_ticks()
            current_time_sec = current_time_ms / 1000.0
            rotation_speed_degrees = -45 # Clockwise 45 deg/sec
            
            # Update Angle Periodically
            if current_time_sec - self.vortex_visual_last_update_time >= self.vortex_visual_update_interval:
                time_since_last_update = current_time_sec - self.vortex_visual_last_update_time
                self.vortex_current_angle = (self.vortex_current_angle + rotation_speed_degrees * time_since_last_update) % 360
                self.vortex_visual_last_update_time = current_time_sec
                
            # Rotate the original overlay image using the current angle
            overlay_image_to_draw = pygame.transform.rotate(self.vortex_overlay_image, self.vortex_current_angle)
            # --- END RE-ADDED ROTATION --- 
            
            # No scaling calculation needed
            
            # Determine center point for blitting (center on tower's logical center)
            center_x = int(self.x + offset_x)
            center_y = int(self.y + offset_y)
            
            # Get rect centered correctly and blit the ROTATED image
            overlay_rect = overlay_image_to_draw.get_rect(center=(center_x, center_y))
            screen.blit(overlay_image_to_draw, overlay_rect.topleft)

        # --- Fallback for other overlays (unchanged) --- 
        else:
            overlay_visual_img = tower_assets.get_overlay_visual(self.tower_id)
            if overlay_visual_img: 
                current_time_ms = pygame.time.get_ticks()
                rotation_speed_degrees = 0
                target_scale_factor = 1.0 # Scale relative to tower size (1.0 = same size)
                target_size = (self.width_pixels, self.height_pixels) # Default to tower footprint size
                center_on_tower = True # Default to centering on tower footprint
                
                # Specific logic for different overlays
                if self.tower_id == "alien_black_hole_generator": 
                    rotation_speed_degrees = 10 # Clockwise rotation for black hole
                    if self.aura_radius_pixels > 0: # Scale to aura if defined
                        target_diameter = int(self.aura_radius_pixels * 2)
                        target_size = (target_diameter, target_diameter)
                    center_on_tower = False # Center on logical center for aura match
                elif self.tower_id == "industry_smog_generator": # <<< ADDED BLOCK
                    rotation_speed_degrees = -5 # Slow counter-clockwise rotation for smog
                    if self.aura_radius_pixels > 0: # Scale to aura if defined
                        target_diameter = int(self.aura_radius_pixels * 2)
                        target_size = (target_diameter, target_diameter)
                    center_on_tower = False # Center on logical center for aura match
                elif self.tower_id == "spark_storm_generator":
                    rotation_speed_degrees = 0 # No rotation for storm
                    # Scale to tower's range instead of aura radius
                    target_diameter = int(self.range * 2) # Double the range for full diameter
                    target_size = (target_diameter, target_diameter)
                elif self.tower_id == "pyro_flame_dancer":
                    rotation_speed_degrees = 360 # Fast clockwise rotation for flame ring
                    # Keep default target_size (tower footprint) and center_on_tower
                elif self.tower_id == "goblin_shredder":
                     rotation_speed_degrees = 720 # Very fast clockwise rotation for buzzsaw
                    # Keep default target_size (tower footprint) and center_on_tower
                
                # Apply rotation if needed
                if rotation_speed_degrees != 0:
                    rotation_angle = (current_time_ms / 1000.0 * rotation_speed_degrees) % 360
                    rotated_overlay = pygame.transform.rotate(overlay_visual_img, rotation_angle)
                else:
                    rotated_overlay = overlay_visual_img # No rotation needed
                    
                # Apply scaling
                try:
                    # Check if target size is different from the rotated image size
                    if target_size[0] != rotated_overlay.get_width() or target_size[1] != rotated_overlay.get_height():
                        scaled_rotated_overlay = pygame.transform.smoothscale(rotated_overlay, target_size)
                    else:
                        scaled_rotated_overlay = rotated_overlay # No scaling needed
                    
                    # Determine center point for blitting
                    if center_on_tower:
                         center_x = draw_pixel_x + self.width_pixels // 2
                         center_y = draw_pixel_y + self.height_pixels // 2
                    else: # Use tower's logical center (self.x, self.y) + offset
                        center_x = int(self.x + offset_x)
                        center_y = int(self.y + offset_y)
                    
                    # Get rect centered correctly and blit
                    overlay_rect = scaled_rotated_overlay.get_rect(center=(center_x, center_y))
                    screen.blit(scaled_rotated_overlay, overlay_rect.topleft)
                except ValueError: # Catch potential zero dimensions during scaling
                     pass 
                except Exception as e:
                    pass
                    #print(f"Error drawing overlay visual for {self.tower_id}: {e}")
        # --- End Overlay Visual --- 

        # REMOVE Range indicator drawing from here
        # center_x_offset = self.x + offset_x
        # center_y_offset = self.y + offset_y
        # pygame.draw.circle(screen, (0, 255, 0, 50),
        #                  (int(center_x_offset), int(center_y_offset)), 
        #                  int(self.range), 1)

    # --- NEW: Adjacency Check Helper --- 
    def count_adjacent_race_towers(self, all_towers, required_race_id):
        """Counts how many towers of a specific race are adjacent to this tower."""
        count = 0
        
        # Define this tower's bounding box in grid coordinates
        self_start_x = self.top_left_grid_x
        self_end_x = self_start_x + self.grid_width - 1
        self_start_y = self.top_left_grid_y # Corrected assignment
        self_end_y = self_start_y + self.grid_height - 1
        
        # Define the adjacency check area (this tower's box expanded by 1 cell)
        adj_min_x = self_start_x - 1
        adj_max_x = self_end_x + 1
        adj_min_y = self_start_y - 1
        adj_max_y = self_end_y + 1
        
        for other_tower in all_towers:
            if other_tower == self:
                continue # Skip self
                
            # Check if the other tower belongs to the required race
            # Extract race name from the tower_id (e.g., "solar_sun_king" -> "solar")
            try:
                other_race_id = other_tower.tower_id.split('_')[0]
            except IndexError:
                continue # Skip if tower_id format is unexpected
            
            if other_race_id == required_race_id:
                # Define the other tower's bounding box
                other_start_x = other_tower.top_left_grid_x
                other_end_x = other_start_x + other_tower.grid_width - 1
                other_start_y = other_tower.top_left_grid_y
                other_end_y = other_start_y + other_tower.grid_height - 1
                
                # Check for AABB overlap between other tower and this tower's adjacency area
                is_adjacent = not (other_end_x < adj_min_x or 
                                   other_start_x > adj_max_x or 
                                   other_end_y < adj_min_y or 
                                   other_start_y > adj_max_y)
                                   
                if is_adjacent:
                    count += 1
                    
        return count
    # --- End Adjacency Helper ---

    def update(self, current_time, all_enemies, 
               game_scene_add_exploder_callback, 
               game_scene_add_effect_callback,   
               game_scene_can_afford_callback,   
               game_scene_deduct_money_callback, 
               game_scene_add_projectile_callback,
               asset_loader,
               all_towers):
        """
        Handles tower-specific updates, including salvo firing.
        Called by GameScene each frame.

        Args:
            current_time: The current game time in seconds.
            all_enemies: List of all active enemies (for targeting).
            game_scene_add_exploder_callback: Callback for PassThroughExploder.
            game_scene_add_effect_callback: Callback for standard visual effects.
            game_scene_can_afford_callback: Callback to check if player can afford something.
            game_scene_deduct_money_callback: Callback to deduct player money.
            game_scene_add_projectile_callback: Callback to add projectiles.
            asset_loader: Function to load assets.
            all_towers: List of all placed towers (for aura effects).
        """
        self.asset_loader = asset_loader 
        self.game_scene_add_exploder_callback = game_scene_add_exploder_callback
        self.game_scene_add_effect_callback = game_scene_add_effect_callback
        self.game_scene_can_afford_callback = game_scene_can_afford_callback
        self.game_scene_deduct_money_callback = game_scene_deduct_money_callback
        self.game_scene_add_projectile_callback = game_scene_add_projectile_callback

        # --- Frost Pulse Aura Effect ---
        if self.special and self.special.get("effect") == "slow_pulse_aura":
            # Check if it's time for a new pulse
            if current_time - self.last_pulse_time >= self.special.get("interval", 2.5):
                self.last_pulse_time = current_time
                pulse_duration = self.special.get("duration", 1.0)
                slow_percentage = self.special.get("slow_percentage", 80)
                slow_multiplier = 1.0 - (slow_percentage / 100.0)
                targets = self.special.get("targets", ["ground", "air"])
                
                # Find enemies in range
                for enemy in all_enemies:
                    if enemy.health > 0 and enemy.type in targets:
                        # Calculate distance to enemy
                        dx = enemy.x - self.x
                        dy = enemy.y - self.y
                        dist_sq = dx*dx + dy*dy
                        if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                            # Apply slow effect
                            enemy.apply_status_effect('slow', pulse_duration, slow_multiplier, current_time)
                            #print(f"Frost Pulse from {self.tower_id} slowed {enemy.enemy_id} by {slow_percentage}% for {pulse_duration}s")
        # --- End Frost Pulse Aura Effect ---

        # --- Miasma Pillar DOT Pulse Effect ---
        if self.special and self.special.get("effect") == "dot_pulse_aura":
            # Check if it's time for a new pulse
            if current_time - self.last_pulse_time >= self.special.get("pulse_interval", 0.5):
                self.last_pulse_time = current_time
                pulse_duration = self.special.get("pulse_duration", 5.0)
                slow_percentage = self.special.get("slow_percentage", 0.3)
                slow_multiplier = 1.0 - slow_percentage
                damage = self.special.get("damage", 18.0)
                damage_type = self.special.get("damage_type", "arcane")
                targets = self.special.get("targets", ["ground", "air"])
                
                # Find enemies in range
                for enemy in all_enemies:
                    if enemy.health > 0 and enemy.type in targets:
                        # Calculate distance to enemy
                        dx = enemy.x - self.x
                        dy = enemy.y - self.y
                        dist_sq = dx*dx + dy*dy
                        if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                            # Apply DOT effect
                            enemy.apply_dot_effect(
                                "miasma_pillar",
                                damage,
                                self.special.get("pulse_interval", 0.5),
                                pulse_duration,
                                damage_type,
                                current_time
                            )
                            # Apply slow effect
                            enemy.apply_status_effect('slow', pulse_duration, slow_multiplier, current_time)
                            #print(f"Miasma Pillar from {self.tower_id} applied DOT and slow to {enemy.enemy_id}")
        # --- End Miasma Pillar DOT Pulse Effect ---

        # --- Vortex Damage Aura Effect ---
        if self.special and self.special.get("effect") == "vortex_damage_aura":
            # Check if it's time for a new tick
            if current_time - self.last_aura_tick_time >= self.special.get("tick_interval", 0.1):
                self.last_aura_tick_time = current_time
                min_damage = self.special.get("min_damage_at_edge", 1.0)
                max_damage = self.special.get("max_damage_at_center", 25.0)
                damage_type = self.special.get("damage_type", "arcane")
                targets = self.special.get("targets", ["ground", "air"])
                
                # Find enemies in range
                for enemy in all_enemies:
                    if enemy.health > 0 and enemy.type in targets:
                        # Calculate distance to enemy
                        dx = enemy.x - self.x
                        dy = enemy.y - self.y
                        dist_sq = dx*dx + dy*dy
                        if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                            # Calculate damage based on distance (more damage closer to center)
                            distance = math.sqrt(dist_sq)
                            distance_ratio = 1.0 - (distance / self.aura_radius_pixels)
                            damage = min_damage + (max_damage - min_damage) * distance_ratio
                            
                            # Apply damage
                            enemy.take_damage(damage, damage_type)
                            #print(f"Vortex from {self.tower_id} dealt {damage:.1f} {damage_type} damage to {enemy.enemy_id}")
        # --- End Vortex Damage Aura Effect ---

        # --- Glacial Heart Bonechill Pulse Effect ---
        if self.special and self.special.get("effect") == "bonechill_pulse_aura":
            # Check if it's time for a new pulse
            if current_time - self.last_pulse_time >= self.special.get("interval", 0.5):
                self.last_pulse_time = current_time
                bonechill_duration = self.special.get("bonechill_duration", 4.0)
                targets = self.special.get("targets", ["ground", "air"])
                
                # Find enemies in range
                for enemy in all_enemies:
                    if enemy.health > 0 and enemy.type in targets:
                        # Calculate distance to enemy
                        dx = enemy.x - self.x
                        dy = enemy.y - self.y
                        dist_sq = dx*dx + dy*dy
                        if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                            # Apply bonechill effect
                            enemy.apply_status_effect('bonechill', bonechill_duration, 1.0, current_time)
                            #print(f"Glacial Heart from {self.tower_id} applied bonechill to {enemy.enemy_id} for {bonechill_duration}s")
        # --- End Glacial Heart Bonechill Pulse Effect ---

        # --- Black Hole Generator Damage Pulse Effect ---
        if self.special and self.special.get("effect") == "damage_pulse_aura":
            # Check if it's time for a new pulse
            if current_time - self.last_pulse_time >= self.special.get("interval", 7.0):
                self.last_pulse_time = current_time
                pulse_damage = self.special.get("pulse_damage", 4000)
                pulse_damage_type = self.special.get("pulse_damage_type", "chaos")
                targets = self.special.get("targets", ["ground", "air"])
                
                # Find enemies in range
                for enemy in all_enemies:
                    if enemy.health > 0 and enemy.type in targets:
                        # Calculate distance to enemy
                        dx = enemy.x - self.x
                        dy = enemy.y - self.y
                        dist_sq = dx*dx + dy*dy
                        if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                            # Apply damage
                            enemy.take_damage(pulse_damage, pulse_damage_type)
                            #print(f"Black Hole Generator from {self.tower_id} dealt {pulse_damage} {pulse_damage_type} damage to {enemy.enemy_id}")
        # --- End Black Hole Generator Damage Pulse Effect ---

        # --- Crit Damage Pulse Aura Effect ---
        if self.special and self.special.get("effect") == "crit_damage_pulse_aura":
            # Check if it's time for a new pulse
            if current_time - self.last_pulse_time >= self.special.get("interval", 5.0):
                self.last_pulse_time = current_time 
                pulse_duration = self.special.get("duration", 5.0)
                crit_multiplier_bonus = self.special.get("crit_multiplier_bonus", 0.5)
                targets = self.special.get("targets", ["towers"])
                
                # Find towers in range
                for tower in all_towers:
                    if tower != self:  # Don't affect self
                        # Calculate distance to tower
                        dx = tower.x - self.x
                        dy = tower.y - self.y
                        dist_sq = dx*dx + dy*dy
                        if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                            # Apply crit damage buff
                            tower.apply_status_effect('crit_damage_buff', pulse_duration, crit_multiplier_bonus, current_time)
                            #print(f"War Drums from {self.tower_id} buffed {tower.tower_id} with +{crit_multiplier_bonus} crit damage for {pulse_duration}s")
        # --- End Crit Damage Pulse Aura Effect ---

        # --- Rampage Stack Decay Logic ---
        if self.rampage_stacks > 0 and self.special and self.special.get("effect") == "rampage_damage_stack":
            decay_duration = self.special.get("decay_duration", 3.0)
            time_since_last_hit = current_time - self.rampage_last_hit_time

            if time_since_last_hit > decay_duration:
                #print(f"### RAMPAGE RESET: Tower {self.tower_id} stacks expired after {time_since_last_hit:.2f}s. Resetting {self.rampage_stacks} stacks.")
                self.rampage_stacks = 0
        # --- END Rampage Decay ---

        # --- Gattling Spin-Down Logic --- 
        if self.gattling_level > 0 and self.special and self.special.get("effect") == "gattling_spin_up":
            decay_time = self.special.get("decay_time_sec", 2.0)
            if current_time - self.gattling_last_attack_time > decay_time:
                #print(f"Gattling {self.tower_id} spun down from Level {self.gattling_level}.")
                self.gattling_level = 0
                self.gattling_continuous_fire_start_time = 0.0
        # --- END Gattling Spin-Down ---
                                    
        # --- Execute Ability Logic --- 
        if self.special and self.special.get("effect") == "execute" and self.execute_cooldown > 0:
            # Check cooldown
            if current_time - self.execute_last_time >= self.execute_cooldown:
                valid_targets = []
                # Scan enemies in range
                for enemy in all_enemies:
                    # Check if enemy is alive, in range, and meets health threshold
                    if (enemy.health > 0 and 
                        self.is_in_range(enemy.x, enemy.y) and
                        enemy.max_health > 0 and 
                        (enemy.health / enemy.max_health) <= self.execute_health_threshold):
                        valid_targets.append(enemy)
                
                if valid_targets:
                    # Choose a target (e.g., the first one found)
                    target_to_execute = valid_targets[0]
                    #print(f"!!! {self.tower_id} EXECUTE triggered on {target_to_execute.enemy_id} (HP: {target_to_execute.health}/{target_to_execute.max_health}) !!!")
                    
                    # Instantly kill the target
                    target_to_execute.take_damage(999999, "execute") 
                    
                    # Play the special sound if loaded
                    if self.special_ability_sound:
                        self.special_ability_sound.play()
                    
                    # Reset cooldown
                    self.execute_last_time = current_time

        # --- Attack Speed Aura Effect ---
        if self.special and self.special.get("effect") == "attack_speed_aura":
            # Check if it's time for a new tick
            if current_time - self.last_aura_tick_time >= 0.1:  # Check every 0.1 seconds
                self.last_aura_tick_time = current_time
                speed_multiplier = self.special.get("attack_speed_multiplier", 1.3)
                required_race = self.special.get("required_race", "zork")
                
                #print(f"DEBUG: {self.tower_id} checking attack speed aura (radius: {self.aura_radius_pixels})")
                
                # Find towers in range
                for tower in all_towers:
                    if tower != self:  # Don't affect self
                        # Calculate distance to tower
                        dx = tower.x - self.x
                        dy = tower.y - self.y
                        dist_sq = dx*dx + dy*dy
                        dist = math.sqrt(dist_sq)
                        
                        # Check if tower belongs to the required race
                        tower_race = tower.tower_id.split('_')[0]  # Extract race from tower_id
                        #print(f"DEBUG: Checking tower {tower.tower_id} (race: {tower_race}, distance: {dist:.1f})")
                        
                        # <<< Check if the tower is the required race >>>
                        if tower_race == required_race:
                            if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                                # <<< APPLY BUFF >>>
                                # Ensure the buff isn't already maximally applied or something similar if needed
                                # Example: Tower applies buff directly
                                # tower.apply_attack_speed_buff(speed_multiplier) 
                                pass # Assume buff application logic is elsewhere or handled by buff system
                        # --- End Attack Speed Aura Effect ---

        # --- Time Machine Rewind Logic --- 
        if self.special and self.special.get("effect") == "rewind_waypoints":
            # Check cooldown based on attack_interval
            if hasattr(self, 'last_attack_time') and current_time - self.last_attack_time >= self.attack_interval:
                #print(f"TIME MACHINE {self.tower_id}: Cooldown ready. Scanning for target...")
                # Find the valid target furthest along the path
                best_target = None
                max_path_index = -1

                for enemy in all_enemies:
                    # Check if enemy is alive, of a valid target type, and in range
                    if (enemy.health > 0 and 
                        enemy.type in self.targets and 
                        self.is_in_range(enemy.x, enemy.y)):
                        
                        # Check progress
                        if enemy.path_index > max_path_index:
                            max_path_index = enemy.path_index
                            best_target = enemy
                
                # If a valid target was found
                if best_target:
                    waypoints_to_rewind = self.special.get("waypoints_to_rewind", 3)
                    #print(f"TIME MACHINE {self.tower_id}: Targeting {best_target.enemy_id} (at waypoint {best_target.path_index}). Rewinding {waypoints_to_rewind} waypoints.")
                    
                    # Call the enemy's rewind method
                    best_target.rewind_waypoints(waypoints_to_rewind)
                    
                    # <<< PLAY REWIND SOUND >>>
                    if hasattr(self, 'rewind_sound') and self.rewind_sound:
                        self.rewind_sound.play()
                    # <<< END PLAY SOUND >>>

                    # Reset cooldown timer
                    self.last_attack_time = current_time
                    
                    # --- Create Rewind Visual Effect --- 
                    if hasattr(self, 'rewind_visual_surface') and self.rewind_visual_surface:
                        if hasattr(self, 'game_scene_add_effect_callback') and callable(self.game_scene_add_effect_callback):
                            try:
                                effect_instance = Effect(
                                    self.x, # Center effect on tower's X
                                    self.y, # Center effect on tower's Y
                                    self.rewind_visual_surface, # Use pre-loaded image
                                    duration=0.5, # Quick fade-out duration
                                    target_size=(self.width_pixels, self.height_pixels), # Match tower size
                                    fade_type='fade_out' # Default fade out is fine
                                )
                                self.game_scene_add_effect_callback(effect_instance)
                                print(f"TIME MACHINE {self.tower_id}: Created rewind visual effect.")
                            except Exception as e:
                                print(f"Error creating rewind visual effect: {e}")
 
        # --- Splash Radius Buff Aura Effect ---
        if self.special and self.special.get("effect") == "splash_radius_buff_aura":
            # Check if it's time for a new tick
            if current_time - self.last_aura_tick_time >= 1.0:  # Check every 1.0 seconds
                self.last_aura_tick_time = current_time
                splash_radius_increase = self.special.get("splash_radius_increase", 175)
                targets = self.special.get("targets", ["towers"])
                
                print(f"DEBUG: {self.tower_id} checking splash radius buff aura (radius: {self.aura_radius_pixels})")
                
                # Find towers in range
                for tower in all_towers:
                    if tower != self:  # Don't affect self
                        # Calculate distance to tower
                        dx = tower.x - self.x
                        dy = tower.y - self.y
                        dist_sq = dx*dx + dy*dy
                        dist = math.sqrt(dist_sq)
                        
                        if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                            # Apply splash radius buff with longer duration
                            tower.apply_pulsed_buff('splash_radius_buff', splash_radius_increase, 1.5, current_time)
                            #print(f"DEBUG: Splash Radius Aura from {self.tower_id} buffed {tower.tower_id} with +{splash_radius_increase} splash radius")
                        else:
                            #print(f"DEBUG: Tower {tower.tower_id} is too far away ({dist:.1f} > {self.aura_radius_pixels})")
                            pass
        # --- End Splash Radius Buff Aura Effect ---

        # --- Adjacency Attack Speed Buff Effect ---
        if self.special and self.special.get("effect") == "adjacency_attack_speed_buff":
            # Check if it's time for a new tick
            if current_time - self.last_aura_tick_time >= 0.1:  # Check every 0.1 seconds
                self.last_aura_tick_time = current_time
                speed_bonus_percent = self.special.get("attack_speed_bonus_percentage", 20)
                speed_multiplier = 1.0 + (speed_bonus_percent / 100.0)
                targets = self.special.get("targets", ["towers"])
                
                #print(f"DEBUG: {self.tower_id} checking adjacency attack speed buff")
                
                # Find adjacent towers
                for tower in all_towers:
                    if tower != self:  # Don't affect self
                        # Check if towers are adjacent (1 grid cell away)
                        dx = abs(tower.center_grid_x - self.center_grid_x)
                        dy = abs(tower.center_grid_y - self.center_grid_y)
                        
                        if (dx <= 1 and dy <= 1) and (dx == 1 or dy == 1):  # Only adjacent, not diagonal
                            # Apply attack speed buff
                            tower.apply_pulsed_buff('attack_speed_buff', speed_multiplier, 0.2, current_time)
                            #print(f"DEBUG: Adjacency Attack Speed Buff from {self.tower_id} buffed {tower.tower_id} with +{speed_bonus_percent}% attack speed")
        # --- End Adjacency Attack Speed Buff Effect ---

        # --- Adjacency Damage Buff Effect ---
        if self.special and self.special.get("effect") == "adjacency_damage_buff":
            # Check if it's time for a new tick
            if current_time - self.last_aura_tick_time >= 1.0:  # Check every 1.0 seconds
                self.last_aura_tick_time = current_time
                damage_bonus_percent = self.special.get("damage_bonus_percentage", 15)
                damage_multiplier = 1.0 + (damage_bonus_percent / 100.0)
                targets = self.special.get("targets", ["towers"])
                
                print(f"DEBUG: {self.tower_id} checking adjacency damage buff")
                
                # Find adjacent towers
                for tower in all_towers:
                    if tower != self:  # Don't affect self
                        # Check if towers are adjacent (1 grid cell away)
                        dx = abs(tower.center_grid_x - self.center_grid_x)
                        dy = abs(tower.center_grid_y - self.center_grid_y)
                        
                        if (dx <= 1 and dy <= 1) and (dx == 1 or dy == 1):  # Only adjacent, not diagonal
                            # Apply damage buff
                            tower.apply_pulsed_buff('damage_buff', damage_multiplier, 1.5, current_time)
                            #print(f"DEBUG: Adjacency Damage Buff from {self.tower_id} buffed {tower.tower_id} with +{damage_bonus_percent}% damage")
        # --- End Adjacency Damage Buff Effect ---

        # --- Air Damage Aura Effect ---
        if self.special and self.special.get("effect") == "air_damage_aura":
            # Check if it's time for a new tick
            if current_time - self.last_aura_tick_time >= 1.0:  # Check every 1.0 seconds
                self.last_aura_tick_time = current_time
                air_damage_multiplier = self.special.get("air_damage_multiplier", 1.1)
                targets = self.special.get("targets", ["towers"])
                
                #print(f"DEBUG: {self.tower_id} checking air damage aura (radius: {self.aura_radius_pixels})")
                
                # Find towers in range
                for tower in all_towers:
                    if tower != self:  # Don't affect self
                        # Only affect projectile towers
                        if tower.attack_type == 'projectile':
                            # Calculate distance to tower
                            dx = tower.x - self.x
                            dy = tower.y - self.y
                            dist_sq = dx*dx + dy*dy
                            dist = math.sqrt(dist_sq)
                            
                            if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                                # Apply air damage buff
                                tower.apply_pulsed_buff('air_damage_buff', air_damage_multiplier, 1.5, current_time)
                                #print(f"DEBUG: Air Damage Aura from {self.tower_id} buffed {tower.tower_id} with x{air_damage_multiplier} air damage")
                            else:
                                #print(f"DEBUG: Tower {tower.tower_id} is too far away ({dist:.1f} > {self.aura_radius_pixels})")
                                pass
                        else:
                            #print(f"DEBUG: Tower {tower.tower_id} is not a projectile tower, skipping air damage buff")
                            pass
        # --- End Air Damage Aura Effect ---

        # --- Damage Aura Effect ---
        if self.special and self.special.get("effect") == "damage_aura":
            # Check if it's time for a new tick
            if current_time - self.last_aura_tick_time >= 1.0:  # Check every 1.0 seconds
                self.last_aura_tick_time = current_time
                damage_bonus_percent = self.special.get("damage_bonus_percentage", 10)
                damage_multiplier = 1.0 + (damage_bonus_percent / 100.0)
                targets = self.special.get("targets", ["towers"])
                
                #print(f"DEBUG: {self.tower_id} checking damage aura (radius: {self.aura_radius_pixels})")
                
                # Find towers in range
                for tower in all_towers:
                    if tower != self:  # Don't affect self
                        # Calculate distance to tower
                        dx = tower.x - self.x
                        dy = tower.y - self.y
                        dist_sq = dx*dx + dy*dy
                        dist = math.sqrt(dist_sq)
                        
                        if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                            # Apply damage buff
                            tower.apply_pulsed_buff('damage_buff', damage_multiplier, 1.5, current_time)
                            #print(f"DEBUG: Damage Aura from {self.tower_id} buffed {tower.tower_id} with +{damage_bonus_percent}% damage")
                        else:
                            pass
                            #print(f"DEBUG: Tower {tower.tower_id} is too far away ({dist:.1f} > {self.aura_radius_pixels})")
        # --- End Damage Aura Effect ---

        # --- Crit Aura Effect ---
        if self.special and self.special.get("effect") == "crit_aura":
            # Check if it's time for a new tick
            if current_time - self.last_aura_tick_time >= 1.0:  # Check every 1.0 seconds
                self.last_aura_tick_time = current_time
                crit_chance_bonus = self.special.get("crit_chance_bonus", 0.50)
                crit_multiplier_bonus = self.special.get("crit_multiplier_bonus", 0.5)
                targets = self.special.get("targets", ["towers"])
                
                print(f"DEBUG: {self.tower_id} checking crit aura (radius: {self.aura_radius_pixels})")
                
                # Find towers in range
                for tower in all_towers:
                    if tower != self:  # Don't affect self
                        # Calculate distance to tower
                        dx = tower.x - self.x
                        dy = tower.y - self.y
                        dist_sq = dx*dx + dy*dy
                        dist = math.sqrt(dist_sq)
                        
                        if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                            # Apply crit chance buff
                            tower.apply_pulsed_buff('crit_chance_buff', crit_chance_bonus, 1.5, current_time)
                            # Apply crit multiplier buff
                            tower.apply_pulsed_buff('crit_multiplier_buff', crit_multiplier_bonus, 1.5, current_time)
                            #print(f"DEBUG: Crit Aura from {self.tower_id} buffed {tower.tower_id} with +{crit_chance_bonus*100}% crit chance and +{crit_multiplier_bonus} crit multiplier")
                        else:
                            pass
                            #print(f"DEBUG: Tower {tower.tower_id} is too far away ({dist:.1f} > {self.aura_radius_pixels})")
        # --- End Crit Aura Effect ---

        # --- DoT Amplification Aura Effect ---
        if self.special and self.special.get("effect") == "dot_amplification_aura":
            # Check if it's time for a new tick
            if current_time - self.last_aura_tick_time >= 1.0:  # Check every 1.0 seconds
                self.last_aura_tick_time = current_time
                dot_damage_multiplier = self.special.get("dot_damage_multiplier", 2.5)
                targets = self.special.get("targets", ["ground", "air"])
                
                #print(f"DEBUG: {self.tower_id} checking DoT amplification aura (radius: {self.aura_radius_pixels})")
                
                # Find enemies in range
                for enemy in all_enemies:
                    if enemy.health > 0 and enemy.type in targets:
                        # Calculate distance to enemy
                        dx = enemy.x - self.x
                        dy = enemy.y - self.y
                        dist_sq = dx*dx + dy*dy
                        dist = math.sqrt(dist_sq)
                        
                        if dist_sq <= self.aura_radius_pixels * self.aura_radius_pixels:
                            # Apply DoT damage multiplier to the enemy with a longer duration that matches the check interval
                            enemy.apply_status_effect('dot_amplification', 2.0, dot_damage_multiplier, current_time)
                            #print(f"DEBUG: DoT Amplification Aura from {self.tower_id} amplified DoTs on {enemy.enemy_id} by x{dot_damage_multiplier}")
                        else:
                            pass
                            #print(f"DEBUG: Enemy {enemy.enemy_id} is too far away ({dist:.1f} > {self.aura_radius_pixels})")
        # --- End DoT Amplification Aura Effect ---

        # --- Random Bombardment Effect ---
        if self.special and self.special.get("effect") == "random_bombardment":
            # Check if it's time for a new strike
            if current_time - self.last_attack_time >= self.special["interval"]:  # Use exact interval from tower data
                self.last_attack_time = current_time
                
                # Get bombardment parameters
                bombardment_radius = self.special.get("bombardment_radius", 2750)
                strike_aoe_radius = self.special.get("strike_aoe_radius", 250)
                strike_damage_min = self.special.get("strike_damage_min", 800)
                strike_damage_max = self.special.get("strike_damage_max", 900)
                strike_damage_type = self.special.get("strike_damage_type", "normal")
                
                # Calculate random strike position within bombardment radius
                angle = random.uniform(0, 2 * math.pi)
                distance = random.uniform(0, bombardment_radius)
                strike_x = self.x + math.cos(angle) * distance
                strike_y = self.y + math.sin(angle) * distance
                
                # Convert grid coordinates to pixel coordinates and ensure strike stays within bounds
                # Grid coordinates: (26,1), (1,24), (1,1), (24,1)
                # Convert to pixel coordinates (assuming 50 pixels per grid)
                min_x = 1 * 50  # Left boundary
                max_x = 26 * 50  # Right boundary
                min_y = 1 * 50  # Top boundary
                max_y = 24 * 50  # Bottom boundary
                
                strike_x = max(min_x, min(strike_x, max_x))
                strike_y = max(min_y, min(strike_y, max_y))
                
                # Create explosion effect
                explosion = Effect(
                    strike_x,
                    strike_y,
                    self.asset_loader("assets/effects/fire_burst.png"),
                    duration=0.5,
                    target_size=(strike_aoe_radius, strike_aoe_radius)  # Make visual effect match actual radius
                )
                
                # Deal damage to enemies in radius
                strike_radius_sq = strike_aoe_radius ** 2
                for enemy in all_enemies:
                    if enemy.health > 0:
                        dx = enemy.x - strike_x
                        dy = enemy.y - strike_y
                        dist_sq = dx**2 + dy**2
                        if dist_sq <= strike_radius_sq:
                            # Calculate damage falloff based on distance
                            distance = math.sqrt(dist_sq)
                            falloff = 1.0 - (distance / strike_aoe_radius)
                            damage = random.uniform(strike_damage_min, strike_damage_max) * falloff
                            enemy.take_damage(damage, strike_damage_type)
                
                # Add explosion to game scene
                if self.game_scene_add_effect_callback:
                    self.game_scene_add_effect_callback(explosion)
                
                #print(f"Random bombardment strike at ({int(strike_x)}, {int(strike_y)})")
        # --- End Random Bombardment Effect ---

        # --- Salvo Attack Logic ---
        if self.special and self.special.get("effect") == "salvo_attack" and self.salvo_shots_remaining > 0:
            if current_time >= self.salvo_next_shot_time:
                # Fire next salvo shot
                salvo_interval = self.special.get("salvo_interval", 0.1)
                self.salvo_next_shot_time = current_time + salvo_interval
                self.salvo_shots_remaining -= 1
                
                # Calculate damage for this shot
                buffed_stats = self.get_buffed_stats(current_time, [], all_towers)
                damage_multiplier = buffed_stats['damage_multiplier']
                effective_splash_radius_pixels = buffed_stats['splash_radius_pixels']
                
                initial_damage, is_crit = self.calculate_damage(self.salvo_target, buffed_stats, current_time, damage_multiplier=damage_multiplier)
                
                # Create and fire the projectile
                projectile = Projectile(
                    self.x, self.y, initial_damage, self.projectile_speed,
                    self.tower_data.get('projectile_asset_id', self.tower_id),
                    target_enemy=self.salvo_target,
                    splash_radius=effective_splash_radius_pixels,
                    source_tower=self,
                    is_crit=is_crit,
                    special_effect=self.special,
                    damage_type=self.damage_type,
                    bounces_remaining=self.bounce,
                    bounce_range_pixels=self.bounce_range_pixels,
                    bounce_damage_falloff=self.bounce_damage_falloff,
                    pierce_adjacent=self.pierce_adjacent,
                    asset_loader=self.asset_loader
                )
                
                # Add projectile to game scene
                if self.game_scene_add_projectile_callback:
                    self.game_scene_add_projectile_callback(projectile)
                
                # Play sound for each shot
                if self.attack_sound:
                    self.attack_sound.play()
        # --- END Salvo Attack Logic ---

    # --- NEW: Method to apply temporary pulsed buffs ---
    def apply_pulsed_buff(self, buff_type, value, duration, current_time):
        """Applies a temporary buff received from a pulse aura."""
        if duration <= 0:
            return
        end_time = current_time + duration
        self.pulsed_buffs[buff_type] = {'value': value, 'end_time': end_time}
    # --- END apply_pulsed_buff ---

    def sell(self):
        """Sell the tower and return its sell value"""
        # Stop any looping sounds
        if hasattr(self, 'looping_sound_channel') and self.looping_sound_channel:
            self.looping_sound_channel.stop()
            self.looping_sound_channel = None
            print(f"Stopped looping sound for {self.tower_id}")
            
        # Calculate sell value (50% of cost)
        sell_value = self.cost // 2
        return sell_value

    def find_target(self, enemies):
        """
        Find the optimal target based on tower's special effects.
        
        Args:
            enemies: List of potential target enemies
            
        Returns:
            The optimal target enemy, or None if no valid targets
        """
        if self.strategic_strike_effect:
            return self.strategic_strike_effect.find_optimal_target(enemies)
            
        # Default targeting behavior
        return super().find_target(enemies)
