#!/usr/bin/env python
# coding=utf-8
import pygame
import math
import random # Import random module
from config import *
# Import GroundEffectZone
from entities.effect import GroundEffectZone
# Import base Effect class as well
from .effect import Effect
# Need os for path joining
import os 

class Projectile:
    def __init__(self, start_x, start_y, damage, speed, projectile_id,
                 target_enemy=None, # Made optional
                 direction_angle=None, # New: Angle in degrees
                 max_distance=None, # New: Max travel distance in pixels
                 splash_radius=0, # Accept radius in pixels
                 source_tower=None, is_crit=False, special_effect=None,
                 damage_type="normal", pierce_adjacent=0,
                 bounces_remaining=0, bounce_range_pixels=0, bounce_damage_falloff=0.7,
                 hit_enemies_in_sequence=None, asset_loader=None, is_visual_only=False):
        """
        Initialize a projectile. Can be homing (target_enemy) or straight-flying (direction_angle).
        
        :param start_x: Starting pixel x
        :param start_y: Starting pixel y
        :param damage: Damage amount to deal on hit
        :param speed: Pixels per second speed
        :param projectile_id: String identifier for the visual asset
        :param target_enemy: The Enemy object to home towards (optional)
        :param direction_angle: Angle in degrees for straight-flying projectiles (optional)
        :param max_distance: Max travel distance in pixels for straight-flying projectiles (optional)
        :param splash_radius: Radius in pixels for splash damage (already scaled)
        :param source_tower: Reference to the tower that fired this
        :param is_crit: Boolean indicating if this was a critical hit
        :param special_effect: Dictionary describing special effect (e.g., slow) to apply
        :param damage_type: String identifier for the damage type
        :param pierce_adjacent: Int, number of adjacent targets to pierce
        :param bounces_remaining: Int, number of bounces remaining
        :param bounce_range_pixels: Int, range in pixels for bounce
        :param bounce_damage_falloff: Float, damage falloff factor for bounce
        :param hit_enemies_in_sequence: Set of Enemy objects hit in sequence
        :param asset_loader: Function to load images (optional)
        :param is_visual_only: Boolean indicating if the projectile is visual only
        """
        self.x = start_x
        self.y = start_y
        self.damage = damage
        self.speed = speed if speed is not None else 1 # Prevent crash if speed is None
        self.projectile_id = projectile_id
        self.splash_radius = splash_radius
        self.splash_radius_sq = splash_radius ** 2 # Pre-calculate squared value
        self.source_tower = source_tower
        self.is_crit = is_crit
        self.special_effect = special_effect
        self.damage_type = damage_type
        self.pierce_adjacent = pierce_adjacent
        self.asset_loader = asset_loader # Store the loader function
        self.is_visual_only = is_visual_only # Store the flag

        # Bounce parameters
        self.bounces_remaining = bounces_remaining
        self.bounce_range_pixels = bounce_range_pixels
        self.bounce_damage_falloff = bounce_damage_falloff
        # Use a copy of the passed set or create a new one if None
        self.hit_enemies_in_sequence = set(hit_enemies_in_sequence) if hit_enemies_in_sequence else set()

        self.collided = False
        self.hit_enemy = None # Stores the enemy hit by a non-homing projectile

        # Movement attributes
        self.target = target_enemy # Store target if homing
        self.vx = 0.0 # Velocity x
        self.vy = 0.0 # Velocity y
        self.distance_traveled_sq = 0.0
        self.max_distance_sq = max_distance**2 if max_distance is not None else float('inf')
        self.world_angle_degrees = 0.0 # Store the world angle (0=right, 90=up)
        self._drawn_once = False # Debug flag for initial draw

        # Determine movement type and initial angle
        if target_enemy is not None:
            # Homing projectile: Calculate initial world angle towards target
            initial_dx = target_enemy.x - self.x
            initial_dy = target_enemy.y - self.y
            if abs(initial_dx) > 0.001 or abs(initial_dy) > 0.001:
                initial_angle_rad = math.atan2(-initial_dy, initial_dx) # Use -dy for Pygame coords
                self.world_angle_degrees = math.degrees(initial_angle_rad)
                print(f"[Projectile Init Homing] Target: {target_enemy.enemy_id}, Initial World Angle: {self.world_angle_degrees:.1f}")
            else:
                print(f"[Projectile Init Homing] Warning: Starting exactly on target {target_enemy.enemy_id}. Using default angle 0.")
                self.world_angle_degrees = 0.0 # Default to pointing right if starting on target
        elif direction_angle is not None:
            # Straight-flying projectile based on angle
            self.target = None 
            self.world_angle_degrees = direction_angle # Assume direction_angle is world angle
            # Convert initial angle to velocity components
            angle_rad = math.radians(self.world_angle_degrees)
            self.vx = math.cos(angle_rad) * self.speed
            self.vy = math.sin(angle_rad) * self.speed # Use sin for y
            self.world_angle_degrees = self.world_angle_degrees # Store for drawing
        else:
            # Invalid state - needs either target or direction
            print("[Projectile Init] Warning: Projectile created without target OR direction. Will not move.")
            self.collided = True # Mark as collided immediately

        # --- Store Special Data if Relevant --- 
        self.special_on_kill_data = None
        self.shatter_data = None # NEW: For Shatter effect
        self.max_hp_reduction_data = None # For Max HP Reduction
        self.ignore_armor_data = None # For Chance Ignore Armor
        # --- DEBUG SPECIAL DATA --- 
        if source_tower:
            print(f"DEBUG Projectile Init: Proj ID: {self.projectile_id}, Tower ID: {source_tower.tower_id}, \
                  Tower Special: {source_tower.special}")
        else:
            print(f"DEBUG Projectile Init: Proj ID: {self.projectile_id}, No source_tower provided.")
        # --- END DEBUG SPECIAL DATA --- 
        if source_tower and source_tower.special:
            effect = source_tower.special.get("effect")
            # print(f"DEBUG Projectile Init: Tower '{source_tower.tower_id}' has effect: '{effect}'") # Optional finer debug
            if effect == "gold_on_kill":
                 self.special_on_kill_data = source_tower.special
                 print(f"DEBUG: Projectile {self.projectile_id} initialized with gold_on_kill data.") # Optional Debug
            elif effect == "shatter": # NEW CHECK
                self.shatter_data = source_tower.special
                print(f"DEBUG: Projectile {self.projectile_id} initialized with shatter data.") # Optional Debug
            elif effect == "max_hp_reduction_on_hit": # NEW CHECK
                 self.max_hp_reduction_data = source_tower.special
                 print(f"DEBUG: Projectile {self.projectile_id} initialized with max_hp_reduction data.")
            elif effect == "chance_ignore_armor_on_hit": # NEW CHECK
                 self.ignore_armor_data = source_tower.special
                 print(f"DEBUG: Projectile {self.projectile_id} initialized with chance_ignore_armor data.")
            # else: print(f"DEBUG Projectile Init: Effect '{effect}' not handled for special data.") # Optional else debug
        # --- End Store Special Data ---

        # --- Load Impact Effect Image (General) --- 
        self.impact_effect_surface = None
        if self.asset_loader:
            # Try to load an effect image based on projectile ID
            effect_image_path = os.path.join("assets", "effects", f"{self.projectile_id}.png")
            # Check if the file exists before attempting to load
            if os.path.exists(effect_image_path):
                print(f"[Projectile Init] Found potential impact effect: {effect_image_path}. Loading...")
                self.impact_effect_surface = self.asset_loader(effect_image_path)
                if self.impact_effect_surface:
                    print(f"[Projectile Init] Successfully loaded impact effect surface for {self.projectile_id}.")
                else:
                    print(f"[Projectile Init] Warning: Failed to load impact effect for {self.projectile_id} from {effect_image_path}")
            # else: # Optional: print if effect file not found
            #    print(f"[Projectile Init] No specific impact effect found for {self.projectile_id} at {effect_image_path}")
        # --------------------------------------------

    def move(self, time_delta, enemies):
        """Move the projectile towards its target (if homing) or in a straight line."""
        if self.collided:
            return # Already collided or expired

        # --- Non-Homing Logic ---
        if self.target is None:
            # Update position based on velocity
            delta_x = self.vx * time_delta
            delta_y = self.vy * time_delta
            self.x += delta_x
            self.y += delta_y

            # Update distance traveled
            dist_moved_sq = delta_x**2 + delta_y**2
            self.distance_traveled_sq += dist_moved_sq

            # Check for max range expiry
            if self.distance_traveled_sq >= self.max_distance_sq:
                #print(f"Non-homing projectile {self.projectile_id} expired (max range).")
                self.collided = True
                return # <<< RETURN HERE

            # Check for collision with any enemy
            collision_radius_sq = (GRID_SIZE * 0.4)**2 # Adjust as needed
            for enemy in enemies:
                if enemy.health > 0:
                    dx = enemy.x - self.x
                    dy = enemy.y - self.y
                    dist_sq = dx**2 + dy**2
                    if dist_sq <= collision_radius_sq:
                        #print(f"Non-homing projectile {self.projectile_id} collided with {enemy.enemy_id}.")
                        self.collided = True
                        self.hit_enemy = enemy # Store the enemy that was actually hit
                        # Optional: Snap position to enemy center on collision
                        self.x = enemy.x
                        self.y = enemy.y
                        return # <<< RETURN HERE (after collision)

            # If non-homing logic finished without collision or expiry, we're done for this frame.
            return # <<< RETURN HERE (end of non-homing block)

        # --- Homing Logic ---
        # Check if target is still valid
        if not self.target or self.target.health <= 0:
            self.collided = True
            return

        # Calculate direction to target
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist_sq = dx**2 + dy**2
        
        # Check for collision with target
        collision_radius_sq = (GRID_SIZE * 0.4)**2
        if dist_sq <= collision_radius_sq:
            self.collided = True
            self.hit_enemy = self.target
            # Snap to target position
            self.x = self.target.x
            self.y = self.target.y
            return

        # Update velocity towards target
        dist = math.sqrt(dist_sq)
        if dist > 0:  # Avoid division by zero
            self.vx = (dx / dist) * self.speed
            self.vy = (dy / dist) * self.speed
            
            # Update position
            self.x += self.vx * time_delta
            self.y += self.vy * time_delta
            
            # Update world angle towards target
            angle_rad = math.atan2(-dy, dx) # Use -dy for Pygame coords
            self.world_angle_degrees = math.degrees(angle_rad)

    def draw(self, screen, projectile_assets, offset_x=0, offset_y=0):
        """Draw the projectile using its asset image, rotated to face its direction."""
        if not self.collided:
            base_image = projectile_assets.get_projectile_image(self.projectile_id)
            if not base_image:
                return 
            
            draw_center_x = self.x + offset_x
            draw_center_y = self.y + offset_y
            
            # Calculate rotation needed for Pygame (counter-clockwise)
            # *** REVERTING ASSUMPTION: Base image points UP (world 90) ***
            # Rotation needed = world_angle - 90
            angle_for_pygame = self.world_angle_degrees - 90.0
            
            if not self._drawn_once and self.target:
                # Update debug print to reflect the reverted assumption
                print(f"[Projectile Draw FIRST (Assume Up Base)] Proj: {self.projectile_id}, Target: {self.target.enemy_id}, World Angle: {self.world_angle_degrees:.1f}, Pygame Angle Used: {angle_for_pygame:.1f}")
                self._drawn_once = True
                
            rotated_image = pygame.transform.rotate(base_image, angle_for_pygame)
            rotated_rect = rotated_image.get_rect(center=(draw_center_x, draw_center_y))
            screen.blit(rotated_image, rotated_rect.topleft)

    def on_collision(self, enemies, current_time, tower_buff_auras=None):
        """Handles what happens when the projectile collides with an enemy or reaches its target location.
           Returns a dictionary containing results like damage dealt, new effects, etc.
        """
        # --- Visual Only Check --- 
        if self.is_visual_only:
            print(f"DEBUG: Visual projectile {self.projectile_id} collided, ignoring.") # Optional debug
            # Return an empty results dict for visual projectiles
            return {
                'damage_dealt': [], 
                'special_effects_applied': [], 
                'new_projectiles': [], 
                'new_effects': [], 
                'enemies_killed': [],
                'gold_added': 0
            }
        # --- END Visual Only Check ---

        # Initialize results dictionary with all expected keys
        results = {
            'damage_dealt': [], 
            'special_effects_applied': [], 
            'new_projectiles': [], 
            'new_effects': [], 
            'enemies_killed': [],
            'gold_added': 0
        }
        
        # Mark as collided first
        self.collided = True
        impact_pos = (self.x, self.y) # Use current position as impact point

        # --- Get Tower Buff Auras (needed for DoT amplification) ---
        # Default to empty list if not provided
        tower_buff_auras = tower_buff_auras if tower_buff_auras is not None else [] 

        # --- Create Impact Visual Effect (If image loaded) --- 
        if self.impact_effect_surface:
            effect_diameter = 2 * GRID_SIZE # Default diameter
            # --- Check for Nuke Custom Visual Size --- 
            if self.special_effect and self.special_effect.get("effect") == "fallout":
                custom_diameter = self.special_effect.get("explosion_visual_diameter")
                if custom_diameter and isinstance(custom_diameter, (int, float)) and custom_diameter > 0:
                    effect_diameter = custom_diameter
                    print(f"[Projectile Collision] Using custom Nuke visual diameter: {effect_diameter}")
                else:
                    print(f"[Projectile Collision] Warning: Nuke fallout effect missing or invalid 'explosion_visual_diameter'. Using default: {effect_diameter}")
            # --- End Nuke Check ---
            
            effect_duration = 0.75 # Seconds - Adjust duration as needed
            impact_effect = Effect(impact_pos[0], impact_pos[1], 
                                     self.impact_effect_surface, 
                                     duration=effect_duration, 
                                     target_size=(int(effect_diameter), int(effect_diameter))) # Use the determined diameter
            results['new_effects'].append(impact_effect)
            # Update print statement to reflect potentially custom size
            print(f"[Projectile Collision] Created impact effect for {self.projectile_id} at ({int(impact_pos[0])}, {int(impact_pos[1])}) size {int(effect_diameter)}")
        # --- End Impact Visual --- 

        # --- Create Fallout Zone if Applicable ---
        if self.special_effect and self.special_effect.get("effect") == "fallout":
            radius_units = self.special_effect.get("radius", 900)
            duration = self.special_effect.get("duration", 15.0)
            dot_damage = self.special_effect.get("dot_damage", 150)
            dot_interval = self.special_effect.get("dot_interval", 0.5)
            dot_damage_type = self.special_effect.get("dot_damage_type", "chaos")
            valid_targets = self.special_effect.get("fallout_targets", ["ground"])
            
            print(f"[DEBUG] Creating fallout zone with: radius={radius_units}, duration={duration}, damage={dot_damage}/{dot_interval}s, type={dot_damage_type}")
            
            # Create the fallout zone
            fallout_zone = GroundEffectZone(
                x=impact_pos[0],
                y=impact_pos[1],
                radius_units=radius_units,
                duration=duration,
                dot_damage=dot_damage,
                dot_interval=dot_interval,
                damage_type=dot_damage_type,
                valid_targets=valid_targets
            )
            results['new_effects'].append(fallout_zone)
            print(f"[Projectile Collision] Created fallout zone at ({int(impact_pos[0])}, {int(impact_pos[1])}) with radius {radius_units}")
        # --- End Fallout Zone Creation ---

        # --- Get Initial Target (if exists) --- 
        initial_target = self.target if self.target else None 
        # --- Determine Collision Point Enemy (if applicable) --- 
        collided_enemy = None
        if initial_target and (abs(self.x - initial_target.x) < 5 and abs(self.y - initial_target.y) < 5): 
             collided_enemy = initial_target
        else: 
             # If no specific target or target far away, check for any enemy at impact point
             collision_radius_sq = (GRID_SIZE * 0.4)**2 # Small radius to detect collision
             for enemy in enemies:
                 if enemy.health > 0 and enemy.type in self.source_tower.targets:
                     dist_sq = (self.x - enemy.x)**2 + (self.y - enemy.y)**2
                     if dist_sq < collision_radius_sq:
                         collided_enemy = enemy
                         break
        
        # --- Distance Damage Bonus (Applied BEFORE other effects) ---
        # USE PARENTHESES for multi-line condition
        if (self.source_tower and self.source_tower.special and 
            self.source_tower.special.get("effect") == "distance_damage_bonus"):
            
            max_bonus = self.source_tower.special.get("max_bonus_percentage", 0.0)
            tower_range = self.source_tower.range # Use tower's actual range
            
            if tower_range > 0 and max_bonus > 0 and collided_enemy: # Added check for collided_enemy
                # Calculate distance at impact using 'collided_enemy'
                dx = collided_enemy.x - self.source_tower.x
                dy = collided_enemy.y - self.source_tower.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                distance_ratio = min(1.0, max(0.0, distance / tower_range))
                bonus_multiplier = 1.0 + (distance_ratio * max_bonus)
                
                # Modify the local 'damage_to_apply' variable
                original_damage = self.damage
                self.damage *= bonus_multiplier
                print(f"    -> Distance Bonus Applied! Dist: {distance:.1f}/{tower_range}, Ratio: {distance_ratio:.2f}, Mult: {bonus_multiplier:.2f}, Dmg: {original_damage:.2f} -> {self.damage:.2f}")
        
        # --- Main Damage Application and Effects --- 
        primary_damage_dealt = 0 # Track damage dealt to primary target
        if collided_enemy:
            print(f"Projectile collided with {collided_enemy.enemy_id} at ({int(impact_pos[0])}, {int(impact_pos[1])}).")
            # --- Killing Blow Check --- 
            health_before = collided_enemy.health
            # --- End Killing Blow Check ---
            # Capture the full result dictionary from apply_damage
            damage_result = self.apply_damage(collided_enemy)
            was_killed = damage_result.get('was_killed', False)
            primary_damage_dealt = damage_result.get('damage_dealt', 0)
            bounty_triggered = damage_result.get('bounty_triggered', False)
            gold_penalty = damage_result.get('gold_penalty', 0)
            # --- End capture result ---
            
            self.hit_enemies_in_sequence.add(collided_enemy) # Track hit for bounce/pierce

            # --- Apply On-Hit Special Effects from Tower (BEFORE processing projectile effects) ---
            if self.source_tower and self.source_tower.special: 
                special_effect = self.source_tower.special.get("effect")
                if special_effect == "armor_reduction_on_hit":
                    amount = self.source_tower.special.get("armor_reduction_amount", 1)
                    # Check if the enemy has the method before calling
                    if hasattr(collided_enemy, 'reduce_armor'):
                        collided_enemy.reduce_armor(amount)
                        print(f"... applied armor reduction ({amount}) to {collided_enemy.enemy_id}")
                # Add other on-hit tower specials here (e.g., stun on hit)
                # elif special_effect == "stun_on_hit": ... 
            # --- End On-Hit Tower Special Effects ---

            # --- Trigger Gold On Kill (After damage applied) ---
            if was_killed and self.special_on_kill_data:
                chance = self.special_on_kill_data.get("chance_percent", 0)
                amount = self.special_on_kill_data.get("gold_amount", 0)
                if amount > 0 and random.random() * 100 < chance:
                    print(f"$$$ Gold on Kill triggered for {self.source_tower.tower_id}! Adding {amount} gold.")
                    results['gold_added'] = amount # Add gold amount to results dictionary
            # --- End Gold On Kill ---

            # --- NEW: Handle Bounty Gold Penalty ---
            if bounty_triggered and gold_penalty > 0:
                # Add the penalty to the results dictionary (GameScene will handle deduction)
                results['gold_penalty'] = gold_penalty
                print(f"!!! Bounty Hunter Penalty triggered! Adding {gold_penalty} gold penalty to results.")
            # --- END Bounty Gold Penalty ---

            # --- NEW: Generic DoT Application on Impact --- 
            # Check if the special effect block contains DoT parameters
            if (self.special_effect and # First check if special_effect exists
                "dot_damage" in self.special_effect and 
                "dot_interval" in self.special_effect and 
                "duration" in self.special_effect and # Use "duration" from JSON for direct DoTs
                collided_enemy): # Make sure we actually hit something

                # Extract DoT parameters
                dot_name = self.special_effect.get("effect", "unknown_dot") # Use 'effect' as the DoT name
                base_dot_damage = self.special_effect.get("dot_damage", 0)
                dot_interval = self.special_effect.get("dot_interval", 1.0)
                dot_duration = self.special_effect.get("duration", 1.0) # Use "duration" from JSON
                dot_damage_type = self.special_effect.get("dot_damage_type", "normal")

                # Apply amplification (if source tower and aura system exist)
                amplified_dot_damage = base_dot_damage
                if self.source_tower and hasattr(self.source_tower, 'get_dot_amplification_multiplier'):
                    amp_multiplier = self.source_tower.get_dot_amplification_multiplier(tower_buff_auras)
                    amplified_dot_damage = base_dot_damage * amp_multiplier

                # Apply the DoT to the enemy that was hit
                if amplified_dot_damage > 0: # Only apply if damage is positive
                    collided_enemy.apply_dot_effect(
                        dot_name, amplified_dot_damage, dot_interval, 
                        dot_duration, dot_damage_type, current_time
                    )
                    print(f"... projectile applied {dot_name} DoT ({amplified_dot_damage:.1f}/{dot_interval}s for {dot_duration}s) to {collided_enemy.enemy_id}")
                    # Record that this effect was applied in results (optional)
                    results['special_effects_applied'].append(f'{dot_name}_dot')

            if was_killed:
                results['enemies_killed'].append(collided_enemy)
                # Check for gold on kill (only primary target for projectile)
                if self.special_on_kill_data:
                    chance = self.special_on_kill_data.get("chance_percent", 0)
                    amount = self.special_on_kill_data.get("gold_amount", 0)
                    if amount > 0 and random.random() * 100 < chance:
                        results['gold_added'] = results.get('gold_added', 0) + amount
                # Check for bounty penalty
                if bounty_triggered:
                    results['gold_penalty'] = results.get('gold_penalty', 0) + gold_penalty

            # --- Apply standard on-hit effects AFTER primary damage --- 
            if collided_enemy and collided_enemy.health > 0: # Only apply effects if target survived
                # Apply special effects from projectile/tower
                if self.special_effect:
                    effect_result = self.apply_special_effects(collided_enemy, current_time)
                    if effect_result:
                        results['special_effects_applied'].append((collided_enemy, effect_result))
                
                # --- NEW: Apply Bash Chance from Source Tower --- 
                if self.source_tower and self.source_tower.special:
                    effect_type = self.source_tower.special.get("effect")
                    if effect_type == "bash_chance":
                        chance = self.source_tower.special.get("chance_percent", 0)
                        if random.random() * 100 < chance:
                            stun_duration = self.source_tower.special.get("stun_duration", 0.1)
                            if stun_duration > 0:
                                collided_enemy.apply_status_effect('stun', stun_duration, True, current_time)
                                print(f"Projectile from {self.source_tower.tower_id} BASHED {collided_enemy.enemy_id} for {stun_duration}s (Chance: {chance}%)")
                # --- END Bash Chance --- 
                
                # --- Apply Armor Reduction on Hit (from source tower's special) --- 
                if self.source_tower and self.source_tower.special and self.source_tower.special.get("effect") == "armor_reduction_on_hit":
                    amount = self.source_tower.special.get("armor_reduction_amount", 1)
                    if hasattr(collided_enemy, 'reduce_armor'):
                        collided_enemy.reduce_armor(amount)
                        print(f"... applied armor reduction ({amount}) to {collided_enemy.enemy_id}")

        else:
            print(f"Projectile reached max distance or target location ({int(impact_pos[0])}, {int(impact_pos[1])}) without hitting valid enemy.")
            # Even if no direct hit, splash/fallout can still occur at impact point

        # --- Special Effect Processing (At Impact Point) --- 
        if self.special_effect:
            effect_type = self.special_effect.get("effect")
            
            # --- Blast Zone (Full Damage AoE) --- 
            if effect_type == "blast_zone" and primary_damage_dealt > 0: 
                radius_units = self.special_effect.get("radius", 50)
                blast_targets = self.special_effect.get("targets", ["ground"])
                blast_radius_pixels = radius_units * (GRID_SIZE / 200.0)
                blast_radius_sq = blast_radius_pixels ** 2
                
                print(f"... applying blast zone (Radius: {blast_radius_pixels:.1f}px, Full Damage: {primary_damage_dealt:.2f})")
                enemies_blasted = 0
                for enemy in enemies:
                    if (enemy.type in blast_targets and enemy.health > 0 and 
                        enemy != collided_enemy and 
                        (enemy.x - impact_pos[0])**2 + (enemy.y - impact_pos[1])**2 <= blast_radius_sq):
                        
                        print(f"...... blasting {enemy.enemy_id} for {primary_damage_dealt:.2f}")
                        self.apply_damage(enemy, damage_override=primary_damage_dealt) # Apply the exact damage
                        enemies_blasted += 1
                if enemies_blasted > 0:
                    print(f"... blast zone hit {enemies_blasted} additional enemies.")
                        
            # Add other special effects like DoT application here if needed...
            # elif effect_type == "dot": ... 
        
        # --- Standard Splash Damage (Percentage Based) --- 
        if self.splash_radius > 0:
            splash_damage_amount = self.damage * 0.25 # Changed from 0.5 to 0.25
            
            # --- NEW: Check for Crit Splash Increase --- 
            effective_splash_radius_sq = self.splash_radius_sq # Start with base squared radius
            crit_splash_multiplier = 1.0 # Default multiplier
            if self.is_crit and self.source_tower and self.source_tower.special and self.source_tower.special.get("effect") == "crit_splash_increase":
                crit_splash_multiplier = self.source_tower.special.get("crit_splash_multiplier", 1.0)
                if crit_splash_multiplier != 1.0:
                    # Calculate new radius and square it
                    crit_radius = self.splash_radius * crit_splash_multiplier
                    effective_splash_radius_sq = crit_radius ** 2
                    print(f"    CRITICAL LANDSLIDE! Splash Radius increased to {crit_radius:.1f} (Multiplier: x{crit_splash_multiplier})")
            # --- END Crit Splash Check --- 
            
            # Use pre-calculated splash_radius_sq (now potentially modified by crit)
            print(f"... applying splash damage (Radius: {math.sqrt(effective_splash_radius_sq):.1f}, Base Damage: {splash_damage_amount:.2f})")
            
            enemies_splashed = 0
            for enemy in enemies:
                if enemy != collided_enemy and enemy.health > 0: 
                    dist_sq = (enemy.x - impact_pos[0])**2 + (enemy.y - impact_pos[1])**2
                    # Use the EFFECTIVE splash radius squared for check
                    if dist_sq <= effective_splash_radius_sq: 
                        print(f"...... splashing {enemy.enemy_id} for {splash_damage_amount:.2f}")
                        self.apply_damage(enemy, damage_override=splash_damage_amount) # Override damage for splash
                        enemies_splashed += 1
            if enemies_splashed > 0:
                 print(f"... splashed {enemies_splashed} enemies.")
        # --- End Splash --- 
        
        # --- Bounce Logic --- 
        if self.bounces_remaining > 0 and collided_enemy:
            # Find potential bounce targets
            potential_targets = []
            bounce_range_sq = self.bounce_range_pixels ** 2
            for enemy in enemies:
                # Check if enemy is valid target, alive, within range, and not already hit in this sequence
                if (enemy.health > 0 and
                    enemy.type in self.source_tower.targets and
                    enemy not in self.hit_enemies_in_sequence and
                    (enemy.x - impact_pos[0])**2 + (enemy.y - impact_pos[1])**2 <= bounce_range_sq):
                    # Calculate distance squared for sorting
                    dist_sq = (enemy.x - impact_pos[0])**2 + (enemy.y - impact_pos[1])**2
                    potential_targets.append((dist_sq, enemy))

            if potential_targets:
                # Sort by distance (closest first)
                potential_targets.sort(key=lambda item: item[0])
                
                # Select the closest valid target
                bounce_target = potential_targets[0][1]
                print(f"... bouncing from {collided_enemy.enemy_id} to {bounce_target.enemy_id} ({self.bounces_remaining} bounces left)")

                # Calculate bounced projectile damage
                bounced_damage = self.damage * self.bounce_damage_falloff

                # Create the new projectile for the bounce
                new_projectile = Projectile(
                    start_x=impact_pos[0],
                    start_y=impact_pos[1],
                    damage=bounced_damage,
                    speed=self.speed,
                    projectile_id=self.projectile_id,
                    target_enemy=bounce_target,
                    splash_radius=self.splash_radius,
                    source_tower=self.source_tower,
                    is_crit=self.is_crit,
                    special_effect=self.special_effect,
                    damage_type=self.damage_type,
                    pierce_adjacent=0, 
                    bounces_remaining=self.bounces_remaining - 1,
                    bounce_range_pixels=self.bounce_range_pixels,
                    bounce_damage_falloff=self.bounce_damage_falloff,
                    hit_enemies_in_sequence=self.hit_enemies_in_sequence.union({collided_enemy}), # Pass updated history
                    asset_loader=self.asset_loader,
                    is_visual_only=self.is_visual_only
                )
                results['new_projectiles'].append(new_projectile)
            else:
                 print(f"... no valid bounce targets found for {collided_enemy.enemy_id}.")

        # --- Pierce Adjacent Logic --- 
        if self.pierce_adjacent > 0 and collided_enemy and not results['new_projectiles']: # Only pierce if direct hit and didn't bounce
            pierced_count = 0
            potential_pierce_targets = []
            # Set pierce search radius to 175 pixels (squared for efficiency)
            pierce_range_sq = 175**2 
            # print(f"[Pierce Check] Search Radius Squared: {pierce_range_sq:.1f}") # DEBUG
            for enemy in enemies:
                 if (enemy.health > 0 and 
                     enemy != collided_enemy and 
                     enemy not in self.hit_enemies_in_sequence and
                     enemy.type in self.source_tower.targets):
                    dist_sq = (enemy.x - impact_pos[0])**2 + (enemy.y - impact_pos[1])**2
                    if dist_sq <= pierce_range_sq:
                        potential_pierce_targets.append((dist_sq, enemy))
                        # print(f"[Pierce Check]   -> Potential Target: {enemy.enemy_id} (DistSq: {dist_sq:.1f})") # DEBUG
            if potential_pierce_targets:
                potential_pierce_targets.sort()
                for dist_sq, enemy_to_pierce in potential_pierce_targets:
                    if pierced_count >= self.pierce_adjacent:
                        break
                    if enemy_to_pierce.health > 0:
                        # Apply damage and get the result dictionary
                        damage_result = self.apply_damage(enemy_to_pierce)
                        # Extract needed values safely
                        damage_dealt = damage_result.get("damage_dealt", 0)
                        was_killed = damage_result.get("was_killed", False)

                        self.hit_enemies_in_sequence.add(enemy_to_pierce) # Track pierce hits for bounce logic
                        if damage_dealt > 0:
                            results['damage_dealt'].append((enemy_to_pierce, damage_dealt, self.damage_type))
                            # Apply standard effects to pierced target?
                            if self.special_effect:
                                effect_result = self.apply_special_effects(enemy_to_pierce, current_time)
                                if effect_result:
                                   results['special_effects_applied'].append((enemy_to_pierce, effect_result))
                            # Apply tower-specific on-hit effects?
                            # ... add logic if needed ...
                        if was_killed:
                            results['enemies_killed'].append(enemy_to_pierce)
                            # Gold on kill for pierced?
                            if self.special_on_kill_data:
                                chance = self.special_on_kill_data.get("chance_percent", 0)
                                amount = self.special_on_kill_data.get("gold_amount", 0)
                                if amount > 0 and random.random() * 100 < chance:
                                    results['gold_added'] = results.get('gold_added', 0) + amount
                        pierced_count += 1
        # --- End Pierce Adjacent --- 
        
        # self.collided = True # Already set at the start
        return results

    def apply_damage(self, enemy, damage_override=None):
        """Applies damage to an enemy, considering damage type, crits, and effects.
        Returns the full result dictionary from enemy.take_damage
        """
        if not enemy or enemy.health <= 0:
            # Return a default dictionary structure if no damage is applied
            return {
                "damage_dealt": 0,
                "was_killed": False,
                "bounty_triggered": False,
                "gold_penalty": 0
            }

        base_damage = damage_override if damage_override is not None else self.damage
        
        # --- Check Chance Ignore Armor --- 
        ignore_armor_flag = False # Use a distinct name for the boolean flag
        if self.ignore_armor_data and random.random() < self.ignore_armor_data.get("chance", 0):
            ignore_armor_flag = True
            print(f"DEBUG: Armor ignore CHANCE triggered for hit on {enemy.enemy_id} by {self.projectile_id}")
        # --- End Check Ignore Armor ---

        # --- Calculate ignore_armor_amount based on the flag --- 
        ignore_armor_amount = 0
        if ignore_armor_flag:
            # Check if enemy has armor value attribute before accessing
            if hasattr(enemy, 'current_armor_value'):
                 ignore_armor_amount = enemy.current_armor_value
                 print(f"DEBUG: Armor ignore AMOUNT set to {ignore_armor_amount} for {enemy.enemy_id}")
            else:
                 print(f"DEBUG: Warning - Tried to ignore armor, but enemy {enemy.enemy_id} lacks 'current_armor_value' attribute.")
        # --- End Calculate ignore_armor_amount ---
        
        # --- Check for Shatter Effect ---
        bonus_multiplier = 1.0
        if self.shatter_data:
            target_debuff = self.shatter_data.get("shatter_target_debuff", "")
            if target_debuff in enemy.status_effects:
                shatter_multiplier = self.shatter_data.get("shatter_damage_multiplier", 1.0)
                bonus_multiplier = shatter_multiplier
                print(f"DEBUG: Shatter effect triggered! Applying {shatter_multiplier}x damage to {enemy.enemy_id} with {target_debuff} debuff")
        # --- End Shatter Check ---
        
        # Call enemy.take_damage and store the returned dictionary
        # Pass self.source_tower.special, NOT self.special_effect for bounty check
        # Because the bounty effect is defined on the TOWER, not the projectile's special effect block
        source_special_for_bounty = self.source_tower.special if self.source_tower else None
        damage_result_dict = enemy.take_damage(base_damage, self.damage_type,
                                             bonus_multiplier=bonus_multiplier,
                                             ignore_armor_amount=ignore_armor_amount,
                                             source_special=source_special_for_bounty) # Pass TOWER's special for bounty check
        
        # Optional: Add visual effect for crit damage
        if self.is_crit:
            pass 
            
        # Return the entire dictionary received from enemy.take_damage
        return damage_result_dict

    def apply_special_effects(self, enemy, current_time):
        """Applies special effects defined in self.special_effect to the enemy."""
        if not self.special_effect or not enemy or enemy.health <= 0:
            return

        effect_type = self.special_effect.get("effect")

        # --- Handle Damage Over Time ---
        # Check if required DoT keys exist
        if ("dot_damage" in self.special_effect and
            "dot_interval" in self.special_effect and
            "duration" in self.special_effect): # Check for 'duration'

            dot_damage = self.special_effect["dot_damage"]
            dot_interval = self.special_effect["dot_interval"]
            dot_duration = self.special_effect["duration"] # Read 'duration'
            # Use effect_type as the identifier, allow specific damage type override
            dot_damage_type = self.special_effect.get("dot_damage_type", "normal") # Default DoT type

            # Call a new method on the enemy to apply/refresh the DoT
            enemy.apply_dot_effect(effect_type, dot_damage, dot_interval, dot_duration, dot_damage_type, current_time)

        # --- Handle Slow Effect (Example, if needed) ---
        elif effect_type == "slow":
            slow_percentage = self.special_effect.get('slow_percentage', 20)
            slow_duration = self.special_effect.get('duration', 2.0) # Assuming 'duration' key for slow
            slow_multiplier = 1.0 - (slow_percentage / 100.0)
            enemy.apply_status_effect('slow', slow_duration, slow_multiplier, current_time)

        # --- Handle Stun Effect ---
        elif effect_type == "stun" and "duration" in self.special_effect:
            stun_duration = self.special_effect["duration"]
            enemy.apply_status_effect('stun', stun_duration, True, current_time) # Value (True) is ignored for stun

        # --- Handle Max HP Reduction ---
        if self.max_hp_reduction_data and hasattr(enemy, 'reduce_max_health'):
            percentage = self.max_hp_reduction_data.get("reduction_percentage", 0)
            if percentage > 0:
                enemy.reduce_max_health(percentage)
        # --- End Max HP Reduction ---

        # --- Add other special effect types here ---
        
        # TODO: Handle bounce - projectile could create a new projectile on hit? 