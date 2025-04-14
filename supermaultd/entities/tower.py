import pygame
import math
import random
from config import *
# from .unique import UNIQUE_ABILITIES # Commented out
from entities.projectile import Projectile # Ensure Projectile is imported
from entities.effect import Effect, FloatingTextEffect, ChainLightningVisual, OrbitingOrbsEffect, DrainParticleEffect, RisingFadeEffect # Import new class
import json # Import json for loading armor data
from .pass_through_exploder import PassThroughExploder # ADD THIS IMPORT

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
        print(f"DEBUG Tower INIT: Assigned self.tower_id = {self.tower_id}")
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
        print(f"INIT Tower {self.tower_id}: Attack Type = {self.attack_type}, ProjSpeed = {self.projectile_speed}")
        
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
        if self.special and 'aura_radius' in self.special:
             aura_units = self.special.get('aura_radius', 0)
             self.aura_radius_pixels = aura_units * (GRID_SIZE / 200.0)
        
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

        # Calculate derived stats
        self.calculate_derived_stats()
        
        # Added for projectile asset loading
        self.asset_loader = None
        
        self.broadside_angle_offset = tower_data.get('broadside_angle_offset', 0)

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

        # Calculate bounce range pixels (already handled in __init__ if bounce > 0)
        # If bounce range wasn't calculated in __init__, add it here:
        # json_bounce_range = self.tower_data.get("bounce_range")
        # self.bounce_range_pixels = json_bounce_range * range_scale_factor if json_bounce_range is not None else 0
        
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
        """Check buff auras for nearby DoT amplification and return the highest multiplier."""
        highest_multiplier = 1.0 # Default: no amplification
        for aura_data in tower_buff_auras:
            # Check if the aura is the correct type
            if aura_data['special'].get('effect') == 'dot_amplification_aura':
                buff_tower = aura_data['tower']
                aura_radius_sq = aura_data['radius_sq']
                
                # Check if this tower (self) is within the buff tower's aura range
                dist_sq = (self.x - buff_tower.x)**2 + (self.y - buff_tower.y)**2
                if dist_sq <= aura_radius_sq:
                    # Get the multiplier from this specific aura
                    multiplier = aura_data['special'].get('dot_damage_multiplier', 1.0)
                    # Keep the highest multiplier found
                    highest_multiplier = max(highest_multiplier, multiplier)
                    # print(f"DEBUG: Tower {self.tower_id} affected by {buff_tower.tower_id} DoT amp aura. Multiplier: {multiplier}") # Optional debug
        
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
        """Calculates effective stats based on active tower buff auras."""
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
        
        # Apply damage buffs (from auras)
        damage *= damage_multiplier
        
        # --- Apply Air Damage Multiplier --- 
        if enemy.type == "air":
            air_multiplier = buffed_stats.get('air_damage_multiplier', 1.0)
            if air_multiplier != 1.0:
                damage *= air_multiplier
                print(f"Tower {self.tower_id} applying x{air_multiplier:.2f} damage multiplier vs Air target {enemy.enemy_id}.")
        # ----------------------------------

        # Check for critical hit using BUFFED crit stats
        is_crit = False
        effective_crit_chance = buffed_stats.get('crit_chance', self.critical_chance)
        effective_crit_multiplier = buffed_stats.get('crit_multiplier', self.critical_multiplier)

        if effective_crit_chance > 0 and random.random() < effective_crit_chance: # Level 2 (12 spaces)
            damage *= effective_crit_multiplier
            is_crit = True
            print(f"Tower {self.tower_id} CRITICAL HIT! (Chance: {effective_crit_chance:.2f}, Mult: {effective_crit_multiplier:.2f}) Damage: {damage:.2f}")

        # --- Apply Berserk Self-Buff --- 
        if self.is_berserk and current_time < self.berserk_end_time: # Level 1 (8 spaces)
            damage *= self.berserk_bonus_multiplier
            print(f"Tower {self.tower_id} BERSERK active! Applying x{self.berserk_bonus_multiplier:.2f}. Damage: {damage:.2f}")
        elif self.is_berserk and current_time >= self.berserk_end_time:
            self.is_berserk = False
            self.berserk_bonus_multiplier = 1.0
            print(f"Tower {self.tower_id} Berserk expired.")

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
        """Calculates damage, creates projectiles/effects, or applies instant damage based on attack type.
        
        Args:
            target: The target Enemy object (can be None for some attack types).
            current_time: The current game time.
            all_enemies: List of all current enemies (for splash/AoE).
            tower_buff_auras: List of active auras affecting towers.
            grid_offset_x: X offset for drawing.
            grid_offset_y: Y offset for drawing.
            visual_assets: Dictionary of loaded visual assets.
            all_towers: List of all placed towers (for adjacency checks).

        Returns:
            A dictionary containing lists of 'projectiles' and 'effects' created, or None if no attack occurs.
        """
        results = {'projectiles': [], 'effects': []}
        
        # --- Adjacency Requirement Check --- 
        if self.special and self.special.get("effect") == "requires_solar_adjacency":
            if not all_towers:
                print(f"Warning: Tower {self.tower_id} requires adjacency check but 'all_towers' list was not provided.")
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
            self.last_attack_time = current_time # Update time since we are firing
            initial_damage = random.uniform(self.base_damage_min, self.base_damage_max) * damage_multiplier 
            is_crit = False 
            
            cannons_per_side = self.special.get("cannons_per_side", 1)
            print(f"Tower {self.tower_id} firing timed BROADSIDE ({cannons_per_side} cannons per side)")
            
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
            if not target: # If broadside wasn't triggered, we MUST have a target now
                 print(f"ERROR: Tower {self.tower_id} attack called without target (and not broadside).")
                 return None # Should not happen if called correctly from GameScene

            # --- Check for Salvo Attack Initiation --- 
            if is_salvo_tower:
                # Only start a new salvo if one isn't already in progress (checked above)
                print(f"Tower {self.tower_id} initiating SALVO attack on {target.enemy_id}")
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

                print(f"Tower {self.tower_id} firing SHOTGUN ({pellets} pellets, spread {spread_angle_degrees} deg) at {target.enemy_id}")

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
            
            # --- NEW: Quillspray Logic ---
            elif self.special and self.special.get("effect") == "quillspray":
                self.last_attack_time = current_time # Update attack time
                quill_count = self.special.get("quill_count", 1) # Get count, default to 1 if missing
                # Use specific projectile asset if defined, otherwise default
                projectile_id = self.tower_data.get('projectile_asset_id', self.tower_id) 
                projectile_speed = self.projectile_speed if self.projectile_speed is not None else 100 # Default speed if None

                # Calculate base damage ONCE for all quills in this spray
                initial_damage, is_crit = self.calculate_damage(target, buffed_stats, current_time, damage_multiplier=damage_multiplier)

                print(f"Tower {self.tower_id} firing QUILLSPRAY ({quill_count} quills, ProjID: {projectile_id})")

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

            # else: # Only run standard logic if NOT a salvo, shotgun, or quillspray tower
            # --- Standard Projectile / Instant Attack Logic --- 
            # (The check for is_salvo_tower above prevents this running for salvo towers) #<- This comment is slightly wrong now, fixed below
            # (The checks above prevent this running for special attack types like salvo, shotgun, quillspray)
            self.last_attack_time = current_time # Update attack time HERE for standard attacks
            initial_damage, is_crit = self.calculate_damage(target, buffed_stats, current_time, damage_multiplier=damage_multiplier)

            # --- Specific Tower Effect Creation (On Attack) --- 
            # Re-add Zork Horde Hurler Orb Effect
            if self.tower_id == "zork_horde_hurler":
                orb_effect = OrbitingOrbsEffect(target, duration=2.0, num_orbs=4)
                results['effects'].append(orb_effect)
            # Add other specific on-attack effect creations here if needed (like Void Leecher drain)
            # --- END Specific Tower Effect Creation ---

            # --- Gattling Level Up & Visual Effect Logic --- 
            is_gattling = self.special and self.special.get("effect") == "gattling_spin_up"
            if is_gattling:
                # --- Gattling Level Up Logic --- 
                self.gattling_last_attack_time = current_time 
                max_level = self.special.get("levels", 0)
                if self.gattling_level < max_level: 
                    time_needed_per_level = self.special.get("time_per_level_sec", 1.5)
                    if self.gattling_continuous_fire_start_time == 0.0:
                        self.gattling_continuous_fire_start_time = current_time
                        print(f"Gattling {self.tower_id} started spinning up.")
                    time_needed_for_next_level = time_needed_per_level * (self.gattling_level + 1)
                    if current_time - self.gattling_continuous_fire_start_time >= time_needed_for_next_level:
                        self.gattling_level += 1
                        print(f"Gattling {self.tower_id} reached Level {self.gattling_level}!")
                # --- END Gattling Level Up --- 
                
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
            if self.attack_type == 'projectile' and not is_gattling:
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
                # Apply instant damage if needed (some instant types might only apply effects)
                # Example: Simple instant damage (adjust if specific instant towers have no base damage)
                if initial_damage > 0: 
                   target.take_damage(initial_damage, self.damage_type) 
                   results['damage_dealt'] = initial_damage # Track damage for results if needed
                # Apply INSTANT special effects (like stun from instant attacks) - if not handled by collision
                self.apply_instant_special_effects(target, current_time) 
                
                # --- Create Instant Attack Visual Effect --- 
                visual_effect_name = self.tower_data.get("attack_visual_effect")
                if visual_effect_name and visual_assets: # Check if name and assets exist
                    visual_img = visual_assets.get(visual_effect_name)
                    if visual_img:
                        print(f"... creating instant visual effect '{visual_effect_name}' at target {target.enemy_id}")
                        # Calculate screen coordinates
                        effect_x = target.x + grid_offset_x
                        effect_y = target.y + grid_offset_y
                        # Create a standard fading effect (adjust duration/size as needed)
                        vis_effect = Effect(effect_x, effect_y, visual_img, 
                                            duration=0.5, # Example duration
                                            target_size=(GRID_SIZE, GRID_SIZE), # Example size
                                            hold_duration=0.1)
                        results['effects'].append(vis_effect)
                    else:
                        print(f"Warning: Could not load visual asset '{visual_effect_name}' for tower {self.tower_id}")
                # --- End Instant Visual Effect ---
                
                # --- Instant Splash Damage Logic --- 
                effective_splash_radius_pixels = buffed_stats.get('splash_radius_pixels', 0)
                if effective_splash_radius_pixels > 0 and initial_damage > 0: # Only splash if radius > 0 and damage > 0
                    splash_damage = initial_damage * 0.25 # 25% splash damage
                    splash_radius_sq = effective_splash_radius_pixels ** 2
                    primary_target_pos = (target.x, target.y)
                    print(f"... Applying INSTANT splash (Radius: {effective_splash_radius_pixels:.1f}, Dmg: {splash_damage:.2f})")
                    
                    enemies_splashed = 0
                    for enemy in all_enemies:
                        # Skip primary target and dead enemies
                        if enemy == target or enemy.health <= 0:
                            continue
                            
                        dist_sq = (enemy.x - primary_target_pos[0])**2 + (enemy.y - primary_target_pos[1])**2
                        if dist_sq <= splash_radius_sq:
                            print(f"    ... splashing {enemy.enemy_id} for {splash_damage:.2f}")
                            enemy.take_damage(splash_damage, self.damage_type)
                            # Also apply instant special effects (like stun) to splashed targets?
                            self.apply_instant_special_effects(enemy, current_time) 
                            enemies_splashed += 1
                    if enemies_splashed > 0:
                         print(f"... splashed {enemies_splashed} enemies.")
                # --- End Instant Splash ---
                 
            # --- Apply effects common to both standard projectile/instant that are triggered ON ATTACK (not collision) --- 
            # Example: Rampage Stacks - This should happen *when* the tower attacks, regardless of projectile hit
            if self.special and self.special.get("effect") == "rampage_damage_stack":
                self.rampage_stacks = min(self.special.get('max_stacks', 10), self.rampage_stacks + 1)
                self.rampage_last_hit_time = current_time
                print(f"Tower {self.tower_id} gained rampage stack. Stacks: {self.rampage_stacks}")
            # NOTE: Armor shred, pierce adjacent usually happen on COLLISION (handled in Projectile/Enemy)
            #       Or need specific logic here if INSTANT attacks should trigger them.
            #       Let's assume they are handled on collision for now unless specified otherwise.

        # --- Beam Logic --- 
        # ... (existing beam logic) ...

        return results

    def apply_instant_special_effects(self, target, current_time):
        """Applies NON-projectile special effects directly (e.g., stun from instant attack)."""
        if not self.special or not target or target.health <= 0:
            return

        effect_type = self.special.get("effect")

        # Example: Apply stun if it's an instant attack
        if effect_type == "stun" and "duration" in self.special:
            stun_duration = self.special["duration"]
            target.apply_status_effect('stun', stun_duration, True, current_time)
            print(f"Tower {self.tower_id} applied instant STUN to {target.enemy_id} for {stun_duration}s")

        # Add other instant-applicable effects here (e.g., direct DoT application?)
        # Careful not to duplicate effects handled by projectiles
        
    def draw(self, screen, tower_assets, offset_x=0, offset_y=0):
        """Draw the tower using its associated image, scaled to its grid footprint, with a border and offset."""
        draw_pixel_x = (self.top_left_grid_x * GRID_SIZE) + offset_x
        draw_pixel_y = (self.top_left_grid_y * GRID_SIZE) + offset_y

        # --- Draw Pulsing Heat Effect (Incinerator) --- 
        if self.tower_id == "pyro_incinerator":
            current_time_ms = pygame.time.get_ticks()
            pulse_duration_ms = 1500 # How long one pulse cycle takes (1.5 seconds)
            max_alpha = 120 # Max transparency (0-255)
            
            # Calculate pulse progress (0.0 to 1.0)
            pulse_progress = (current_time_ms % pulse_duration_ms) / pulse_duration_ms
            # Use sine wave for smooth pulsing alpha (abs ensures positive)
            current_alpha = int(max_alpha * abs(math.sin(pulse_progress * math.pi * 2))) # Full sine wave (0->1->0->-1->0)
            
            center_x = int(self.x + offset_x)
            center_y = int(self.y + offset_y)
            radius = int(self.range) # Use tower's range
            pulse_color = (255, 50, 50, current_alpha) # Reddish color with pulsing alpha
            
            if radius > 0 and current_alpha > 10: # Draw only if radius/alpha are meaningful
                try:
                    # Create a temporary surface for alpha blending
                    temp_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                    # Draw the circle onto the center of the temporary surface
                    pygame.draw.circle(temp_surface, pulse_color, (radius, radius), radius)
                    # Blit the temporary surface onto the main screen, centered correctly
                    screen.blit(temp_surface, (center_x - radius, center_y - radius))
                except Exception as e:
                    print(f"Error drawing incinerator pulse effect: {e}")
        # --- End Pulsing Heat Effect ---

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
                    print(f"Error drawing creep colony glow effect: {e}")
        # --- End Creep Colony Glow --- 

        # --- Special Handling for Storm Generator Aura Visual Path --- 
        aura_visual_img = None # Initialize
        if self.tower_id == "spark_storm_generator":
            # Load storm effect specifically from assets/effects
            aura_visual_img = tower_assets.get_effect_image("storm_effect") 
            if not aura_visual_img:
                print(f"WARNING: Failed to load storm_effect.png from assets/effects for {self.tower_id}")
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
                    print(f"Error drawing rotated/scaled aura visual for {self.tower_id}: {e}")

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
                print(f"Error drawing overlay visual for {self.tower_id}: {e}")
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
        self_start_y = self_start_y
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
               game_scene_can_afford_callback,   # New money callback 1
               game_scene_deduct_money_callback, # New money callback 2
               game_scene_add_projectile_callback, # New projectile callback
               asset_loader):
        """
        Handles tower-specific updates, including salvo firing.
        Called by GameScene each frame.

        Args:
            current_time: The current game time in seconds.
            all_enemies: List of all active enemies (for targeting).
            game_scene_add_exploder_callback: Callback for PassThroughExploder.
            game_scene_add_effect_callback: Callback for standard visual effects.
            game_scene_can_afford_callback: Callback to check player money.
            game_scene_deduct_money_callback: Callback to deduct player money.
            game_scene_add_projectile_callback: Callback to add projectiles.
            asset_loader: Function to load assets.
        """
        self.asset_loader = asset_loader 

        # --- Salvo Firing Logic (Runs every frame if active) ---
        if self.salvo_shots_remaining > 0 and current_time >= self.salvo_next_shot_time:
            if self.salvo_target and self.salvo_target.health > 0:
                # Target still valid, fire next shot
                print(f"... Salvo Firing shot {self.special.get('salvo_count', 1) - self.salvo_shots_remaining + 1} for {self.tower_id}")
                # Calculate damage (can reuse calculate_damage or simplify)
                # Simplifying here - assuming no buffs needed for subsequent salvo shots
                base_dmg = random.uniform(self.base_damage_min, self.base_damage_max)
                is_crit = False # Salvo shots don't crit by default?
                
                # Use buffed stats for splash radius
                # Note: This requires buffed_stats to be calculated or passed differently if needed here
                # Using base splash for simplicity in update loop
                splash_rad_pixels = self.splash_radius_pixels 
                
                projectile = Projectile(self.x, self.y, base_dmg, self.projectile_speed, 
                                      self.tower_data.get('projectile_asset_id', self.tower_id),
                                      target_enemy=self.salvo_target, 
                                      splash_radius=splash_rad_pixels,
                                      source_tower=self, is_crit=is_crit, 
                                      special_effect=self.special,
                                      damage_type=self.damage_type,
                                      bounces_remaining=self.bounce,
                                      bounce_range_pixels=self.bounce_range_pixels,
                                      bounce_damage_falloff=self.bounce_damage_falloff,
                                      pierce_adjacent=self.pierce_adjacent,
                                      asset_loader=self.asset_loader)
                game_scene_add_projectile_callback(projectile)

                # Decrement and schedule next shot
                self.salvo_shots_remaining -= 1
                if self.salvo_shots_remaining > 0:
                    salvo_interval = self.special.get("salvo_interval", 0.1)
                    self.salvo_next_shot_time = current_time + salvo_interval
                else:
                    # Salvo finished
                    print(f"... Salvo complete for {self.tower_id}")
                    self.salvo_target = None # Clear target
            else:
                # Target lost or died during salvo
                print(f"... Salvo target lost for {self.tower_id}, stopping salvo.")
                self.salvo_shots_remaining = 0
                self.salvo_target = None
        # --- END Salvo Firing Logic ---

        # --- Fixed Distance Pass Through Exploder Logic --- 
        if self.special and self.special.get("effect") == "fixed_distance_pass_through_explode":
            # Check cooldown based on tower's attack_interval
            if current_time - self.last_attack_time >= self.attack_interval:
                # Find target simply to determine initial direction
                target = None
                potential_targets = []
                for enemy in all_enemies:
                    if enemy.health > 0 and enemy.type in self.targets and self.is_in_range(enemy.x, enemy.y):
                        potential_targets.append(enemy)
                
                if potential_targets:
                    # Simple targeting: closest or first (doesn't really matter as it only sets direction)
                    potential_targets.sort(key=lambda e: (e.x - self.x)**2 + (e.y - self.y)**2)
                    target = potential_targets[0]
                    
                    print(f"Tower {self.tower_id} launching PassThroughExploder towards {target.enemy_id}")
                    # Create the new entity, passing the asset_loader
                    exploder = PassThroughExploder(self, target, self.special, asset_loader) 
                    # Use the CORRECT callback for exploders
                    game_scene_add_exploder_callback(exploder)
                    
                    # Update tower's cooldown timer
                    self.last_attack_time = current_time
                # else: # No target in range, do nothing this frame
                    # print(f"Tower {self.tower_id} PassThroughExploder ready, but no target in range.")
                    
        # --- NEW: Random Bombardment Logic ---
        if self.special and self.special.get("effect") == "random_bombardment":
            interval = self.special.get("interval", 5.0) # Get interval from special
            if current_time - self.last_attack_time >= interval:
                bombard_radius_units = self.special.get("bombardment_radius", 0)
                # --- Apply the same scaling as standard range ---
                range_scale_factor = GRID_SIZE / 200.0 
                bombard_radius = bombard_radius_units * range_scale_factor # Convert to pixels/game units
                # --- End Scaling ---
                strike_aoe_radius = self.special.get("strike_aoe_radius", 0)
                strike_aoe_radius_sq = strike_aoe_radius ** 2

                if bombard_radius > 0 and strike_aoe_radius > 0:
                    # Pick a random angle and distance within the bombardment radius
                    rand_angle = random.uniform(0, 2 * math.pi)
                    # Use sqrt(random) for uniform area distribution
                    rand_dist = bombard_radius * math.sqrt(random.random()) # Use the scaled radius
                    
                    # Calculate strike point coordinates relative to tower center
                    strike_x = self.x + math.cos(rand_angle) * rand_dist
                    strike_y = self.y + math.sin(rand_angle) * rand_dist
                    
                    print(f"Tower {self.tower_id} triggering random bombardment at ({strike_x:.1f}, {strike_y:.1f})")

                    # Calculate damage for this strike
                    strike_dmg_min = self.special.get("strike_damage_min", 0)
                    strike_dmg_max = self.special.get("strike_damage_max", 0)
                    strike_dmg_type = self.special.get("strike_damage_type", "normal")
                    strike_damage = random.uniform(strike_dmg_min, strike_dmg_max)

                    # Find enemies within the strike AOE
                    enemies_hit_count = 0
                    for enemy in all_enemies:
                        if enemy.health > 0:
                            dist_sq = (enemy.x - strike_x)**2 + (enemy.y - strike_y)**2
                            if dist_sq <= strike_aoe_radius_sq:
                                print(f"... hitting {enemy.enemy_id} for {strike_damage:.2f}")
                                enemy.take_damage(strike_damage, strike_dmg_type)
                                enemies_hit_count += 1
                    
                    # Create visual explosion effect at strike point
                    try:
                        # Use game scene callback to add the effect
                        # We need grid offsets passed into update or calculated here
                        # Correctly access imported config constants
                        grid_offset_x = UI_PANEL_PADDING
                        grid_offset_y = UI_PANEL_PADDING
                        # Calculate screen coords for the effect
                        effect_screen_x = strike_x + grid_offset_x
                        effect_screen_y = strike_y + grid_offset_y
                        
                        # Create a simple effect (like RisingFadeEffect or a new ExplosionEffect)
                        # Load the specific bombardment image
                        if self.asset_loader:
                            explosion_img = self.asset_loader("assets/effects/bomb_barrage_beacon.png") # Use the correct image path
                            if explosion_img:
                                # Using RisingFadeEffect - scales and fades. Adjust class/params if needed.
                                explosion_effect = RisingFadeEffect(effect_screen_x, effect_screen_y, explosion_img, duration=0.6, start_scale=0.1, end_scale=1.5)
                                # Use the CORRECT callback for visual effects
                                game_scene_add_effect_callback(explosion_effect)
                            else: 
                                print("Warning: Could not load bomb_barrage_beacon.png for bombardment effect.")
                        else:
                             print("Warning: Asset loader not available in Tower.update for bombardment effect.")
                             
                    except Exception as e:
                        print(f"Error creating bombardment visual effect: {e}")

                    # Update tower's cooldown timer
                    self.last_attack_time = current_time 
        # --- END Random Bombardment Logic ---

        # --- NEW: Bribe Kill Logic ---
        if self.special and self.special.get("effect") == "bribe_kill":
            interval = self.special.get("interval", 3.0) 
            if current_time - self.last_pulse_time >= interval:
                bribe_chance = self.special.get("bribe_chance_percent", 0)
                # Roll the dice
                if random.random() * 100 < bribe_chance:
                    bribe_radius = self.special.get("bribe_radius", 0)
                    bribe_radius_sq = bribe_radius ** 2
                    bribe_cost = self.special.get("bribe_cost", 0)
                    excluded_ids = self.special.get("excluded_enemy_ids", [])

                    if bribe_radius > 0 and bribe_cost > 0:
                        # Find closest valid target
                        closest_target = None
                        min_dist_sq = float('inf')

                        for enemy in all_enemies:
                            if (enemy.health > 0 and 
                                enemy.enemy_id not in excluded_ids):
                                dist_sq = (enemy.x - self.x)**2 + (enemy.y - self.y)**2
                                if dist_sq <= bribe_radius_sq and dist_sq < min_dist_sq:
                                    min_dist_sq = dist_sq
                                    closest_target = enemy
                        
                        # Attempt bribe if target found
                        if closest_target:
                            print(f"Tower {self.tower_id} attempting bribe on {closest_target.enemy_id} (Cost: {bribe_cost}). Chance: {bribe_chance}%")
                            # Check affordability using callback
                            if game_scene_can_afford_callback(bribe_cost):
                                # Deduct money using callback
                                if game_scene_deduct_money_callback(bribe_cost):
                                    print(f"$$$ BRIBE SUCCESSFUL on {closest_target.enemy_id}! Deducted {bribe_cost}.")
                                    # Instantly kill the enemy
                                    closest_target.take_damage(999999, "bribe") # Use high damage and unique type
                                    # Create visual effect (e.g., floating money sign)
                                    try:
                                        # Assuming config access is fixed
                                        grid_offset_x = UI_PANEL_PADDING
                                        grid_offset_y = UI_PANEL_PADDING
                                        text_x = closest_target.x + grid_offset_x
                                        text_y = closest_target.y + grid_offset_y - (GRID_SIZE * 0.5) # Above enemy
                                        bribe_text = "$ BRIBE $"
                                        bribe_color = (0, 200, 0) # Green
                                        text_effect = FloatingTextEffect(text_x, text_y, bribe_text, color=bribe_color, font_size=20, duration=1.5)
                                        game_scene_add_effect_callback(text_effect)
                                    except Exception as e:
                                        print(f"Error creating bribe text effect: {e}")
                                else:
                                     print(f"... Bribe failed (Deduction callback returned False?)") # Should not happen if can_afford passed
                            else:
                                print(f"... Bribe failed (Cannot afford {bribe_cost})")
                        # else: print(f"... No valid target found for bribe attempt.") # Optional
                # Update tower's cooldown timer regardless of success/target found AFTER chance roll passes
                self.last_pulse_time = current_time 
        # --- END Bribe Kill Logic ---

        # --- Rampage Stack Decay Logic ---
        if self.rampage_stacks > 0 and self.special and self.special.get("effect") == "rampage_damage_stack":
            decay_duration = self.special.get("decay_duration", 3.0)
            time_since_last_hit = current_time - self.rampage_last_hit_time # Use current_time passed into update

            if time_since_last_hit > decay_duration:
                print(f"### RAMPAGE RESET: Tower {self.tower_id} stacks expired after {time_since_last_hit:.2f}s. Resetting {self.rampage_stacks} stacks.")
                self.rampage_stacks = 0
                # self.rampage_last_hit_time = 0.0 # Optional: reset time too
        # --- END Rampage Decay ---

        # --- Gattling Spin-Down Logic --- 
        if self.gattling_level > 0 and self.special and self.special.get("effect") == "gattling_spin_up":
            decay_time = self.special.get("decay_time_sec", 2.0)
            if current_time - self.gattling_last_attack_time > decay_time:
                print(f"Gattling {self.tower_id} spun down from Level {self.gattling_level}.") # Debug
                self.gattling_level = 0
                self.gattling_continuous_fire_start_time = 0.0 # Reset tracking
        # --- END Gattling Spin-Down ---
                                    
        # --- Add other tower-specific update logic here if needed --- 
