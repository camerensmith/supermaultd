import pygame
import math
import random
from config import *
import time

# Pre-calculate the armor constant for efficiency
ARMOR_CONSTANT = 0.06

class Enemy:
    """Represents an enemy unit in the game."""
    def __init__(self, x, y, grid_path, enemy_id, enemy_data, armor_type, damage_modifiers, wave_index=None):
        """
        Initialize an enemy.

        :param x: Starting X pixel coordinate.
        :param y: Starting Y pixel coordinate.
        :param grid_path: List of (grid_x, grid_y) tuples for the path.
        :param enemy_id: Unique identifier string for the enemy type (e.g., 'gnoll').
        :param enemy_data: Dictionary containing stats for this enemy type from config.ENEMY_DATA.
        :param armor_type: String name of the armor type (e.g., 'Light').
        :param damage_modifiers: Dictionary of damage type -> multiplier for this armor.
        :param wave_index: Index of the wave this enemy belongs to (for tracking purposes).
        """
        self.x = x
        self.y = y
        self.grid_path = grid_path
        self.path_index = 0
        self.enemy_id = enemy_id
        self.image = None  # Will be set during draw based on assets
        self.wave_index = wave_index  # Track which wave this enemy belongs to

        # --- ADDED: Rect for Collision Detection ---
        # Initialize rect with placeholder size, then center it
        self.rect = pygame.Rect(0, 0, GRID_SIZE, GRID_SIZE) # Default size
        self.rect.center = (self.x, self.y) # Center on initial position
        # ------------------------------------------

        # Enemy properties from data
        self.max_health = enemy_data.get("health", 100) # Use .get for default values
        self.health = self.max_health
        self.base_speed = enemy_data.get("speed", 2.0)
        self.speed = self.base_speed # Current speed, possibly affected by slows
        self.value = enemy_data.get("value", 10)  # Money earned when killed
        self.armor_type = armor_type # Store armor type name
        self.damage_modifiers = damage_modifiers # Store damage modifier dict
        
        # --- NEW: Armor Value --- 
        self.base_armor_value = enemy_data.get("armor_value", 0) # Get from data, default 0
        self.current_armor_value = self.base_armor_value # Initialize current value
        # ------------------------
        
        # --- NEW: Aura Armor Reduction State ---
        self.aura_armor_reduction = 0 # Amount of armor reduction currently applied by auras
        # ---------------------------------------
        
        # Determine enemy type (e.g., ground, air) - needed for tower targeting/stats
        self.type = enemy_data.get("type", "ground") # Default to ground if not specified
        
        self.status_effects = {} # To track effects like { 'slow': { 'end_time': timestamp, 'multiplier': 0.8 } }
        self.active_dots = {} # Store active DoT effects
        
        # <<< ADDED: Initialize gold_on_kill attribute >>>
        self.pending_gold_on_kill = 0
        
        # Movement properties
        self.wander_radius = 10  # How far the enemy can wander from the direct path
        self.wander_angle = random.uniform(0, 2 * math.pi)  # Random starting angle
        self.wander_change = 0.5  # How quickly the wander angle changes
        
    def update_status_effects(self, current_time):
        """Remove expired effects and recalculate speed."""
        effects_removed = False
        for effect_type, data in list(self.status_effects.items()): # Iterate over copy
            if current_time >= data['end_time']:
                del self.status_effects[effect_type]
                effects_removed = True
                #print(f"Enemy {self.enemy_id}: {effect_type} expired.")
        
        if effects_removed:
            self.recalculate_speed()

    def apply_status_effect(self, effect_type, duration, value, current_time):
        """Apply or refresh a status effect (e.g., slow, stun)."""
        end_time = current_time + duration
        
        # Store effect data - value is used for slow multiplier, ignored for stun
        if effect_type == 'dot_amplification':
            self.status_effects[effect_type] = { 'end_time': end_time, 'multiplier': value }
        else:
            self.status_effects[effect_type] = { 'end_time': end_time, 'value': value }
        
        #print(f"Enemy {self.enemy_id}: Applied {effect_type} until {end_time:.2f}")
        # Recalculate speed immediately after applying any status effect
        self.recalculate_speed()

    def recalculate_speed(self):
        """Recalculate current speed based on active status effects."""
        # Check for stun first
        if 'stun' in self.status_effects:
            self.speed = 0
            # print(f"Enemy {self.enemy_id} is STUNNED. Speed set to 0.")
            return # Stun overrides slow
        
        # If not stunned, calculate slow
        slow_multiplier = 1.0
        if 'slow' in self.status_effects:
            slow_multiplier = min(slow_multiplier, self.status_effects['slow']['value'])
        
        self.speed = self.base_speed * slow_multiplier
        # print(f"Enemy {self.enemy_id} speed recalculated to {self.speed}")
        
    def apply_dot_effect(self, effect_name, damage, interval, duration, damage_type, current_time):
        """Applies or refreshes a Damage Over Time effect."""
        if interval <= 0 or duration <= 0 or damage <= 0: # Basic validation
            return

        end_time = current_time + duration
        next_tick_time = current_time + interval # First tick after one interval

        # Check if overwriting existing effect of the same name
        if effect_name in self.active_dots:
            #print(f"Enemy {self.enemy_id}: Refreshing DoT '{effect_name}'.")
            pass # Overwrite below

        # Store base damage and let update_dots handle amplification
        self.active_dots[effect_name] = {
            'base_damage': damage,
            'interval': interval,
            'next_tick': next_tick_time,
            'end_time': end_time,
            'damage_type': damage_type
        }
        #print(f"Enemy {self.enemy_id}: Applied DoT '{effect_name}' (Base: {damage}/{interval}s for {duration}s, type: {damage_type}). Ends at {end_time:.2f}.")

    def update_dots(self, current_time):
        """Processes active DoT effects, applying damage and removing expired ones."""
        if not self.active_dots:
            return

        # Get dot amplification multiplier from status effects
        dot_amp_multiplier = 1.0
        if 'dot_amplification' in self.status_effects:
            dot_amp_multiplier = self.status_effects['dot_amplification']['multiplier']
            #print(f"Enemy {self.enemy_id}: DoT amplification active (x{dot_amp_multiplier})")

        # Use list keys for safe iteration if removing items
        for effect_name in list(self.active_dots.keys()):
            dot_data = self.active_dots[effect_name]

            # Check for expiry
            if current_time >= dot_data['end_time']:
                #print(f"Enemy {self.enemy_id}: DoT '{effect_name}' expired.")
                del self.active_dots[effect_name]
                continue # Move to next DoT

            # Check for tick time
            if current_time >= dot_data['next_tick']:
                # Apply dot amplification multiplier to base damage
                amplified_damage = dot_data['base_damage'] * dot_amp_multiplier
                #print(f"Enemy {self.enemy_id}: DoT '{effect_name}' ticking for {amplified_damage} damage (base: {dot_data['base_damage']}, amp: x{dot_amp_multiplier}, type: {dot_data['damage_type']}).")
                self.take_damage(amplified_damage, dot_data['damage_type'])
                # Schedule next tick
                dot_data['next_tick'] += dot_data['interval']
                # Ensure next_tick doesn't fall behind current_time excessively due to lag
                if dot_data['next_tick'] < current_time:
                    dot_data['next_tick'] = current_time + dot_data['interval']

    def move(self, current_time, tile_size=None):
        """Move the enemy towards the next waypoint with wandering behavior."""
        self.update_status_effects(current_time) # Update effects first (slows)
        self.update_dots(current_time) # Process DoT effects
        
        # Use provided tile_size or fall back to GRID_SIZE for compatibility
        use_tile_size = tile_size if tile_size is not None else GRID_SIZE
        
        if self.path_index < len(self.grid_path):
            # Get the target grid cell coordinates
            target_grid_x, target_grid_y = self.grid_path[self.path_index]
            
            # Convert target grid cell to target pixel coordinates (center of cell)
            target_x_pixel = (target_grid_x * use_tile_size) + (use_tile_size // 2)
            target_y_pixel = (target_grid_y * use_tile_size) + (use_tile_size // 2)

            # Calculate direction to target
            dx = target_x_pixel - self.x
            dy = target_y_pixel - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                # Calculate base movement direction (towards target)
                base_dir_x = dx / distance
                base_dir_y = dy / distance
                
                # Update wander angle
                self.wander_angle += random.uniform(-self.wander_change, self.wander_change)
                
                # Calculate wander offset
                wander_x = math.cos(self.wander_angle) * self.wander_radius
                wander_y = math.sin(self.wander_angle) * self.wander_radius
                
                # Combine base direction with wander
                move_x = base_dir_x + (wander_x / distance)
                move_y = base_dir_y + (wander_y / distance)
                
                # Normalize the combined direction
                move_length = math.sqrt(move_x**2 + move_y**2)
                if move_length > 0:
                    move_x /= move_length
                    move_y /= move_length
                
                # Apply movement
                self.x += move_x * self.speed
                self.y += move_y * self.speed
                
                # Check if we've reached the target area
                if distance <= self.wander_radius * 2:
                    self.path_index += 1
                    #print(f"Enemy reached waypoint {self.path_index-1}, moving to next waypoint")
            else:
                # If we're already at the target, move to next waypoint
                self.path_index += 1
                # print(f"Enemy {self.enemy_id} already at waypoint {self.path_index-1}, moving to next waypoint") # Less noisy
        
        # --- ADDED: Update Rect Position ---
        self.rect.center = (int(self.x), int(self.y)) # Keep rect centered on enemy
        # ------------------------------------
        
    def take_damage(self, base_damage, damage_type="normal", bonus_multiplier=1.0, ignore_armor_amount=0, source_special=None):
        """Apply damage to the enemy, taking into account resistances, status effects, and armor."""
        #print(f" >>> ENTERING Enemy.take_damage for {self.enemy_id} (Damage: {base_damage}, Type: {damage_type}, IgnoreArmor: {ignore_armor_amount})") # <<< ADDED DEBUG & IgnoreArmor
        # 1. Apply Armor Type vs Damage Type multiplier
        type_modifier = self.damage_modifiers.get(damage_type, 1.0)
        damage_after_type = base_damage * type_modifier

        # Note: We don't apply dot_amplification here anymore since it's already applied when creating the DoT
        # The amplification is handled in apply_dot_effect and other places where DoTs are created

        # --- Apply Aura Armor Reduction ---
        if self.aura_armor_reduction > 0:
            ignore_armor_amount += self.aura_armor_reduction # Add aura reduction to any passed-in ignore
            #print(f"... Applying aura armor reduction ({self.aura_armor_reduction}). Total ignore: {ignore_armor_amount}")
        # --- End Aura Armor Reduction ---

        # 2. Apply Armor Value reduction/amplification
        # Calculate effective armor using the potentially increased ignore_amount
        effective_armor = self.current_armor_value - ignore_armor_amount
        armor_multiplier = 1.0
        if effective_armor >= 0:
            armor_multiplier = 1.0 / (1.0 + ARMOR_CONSTANT * effective_armor) # Use effective_armor
        else: # effective_armor < 0
            armor_multiplier = 1.0 - ARMOR_CONSTANT * effective_armor # Use effective_armor
            
        actual_damage = damage_after_type * armor_multiplier
        
        # --- NEW: Apply Marked for Death Multiplier --- 
        mark_multiplier = 1.0
        if "marked_for_death" in self.status_effects:
            mark_multiplier = 1.5 # Apply 1.5x damage
            #print(f"... Enemy {self.enemy_id} is marked_for_death, applying x{mark_multiplier} multiplier.")
        # --- END Marked for Death --- 
        
        # 3. Apply Bonus Multiplier (e.g., from Shatter)
        final_damage = actual_damage * bonus_multiplier * mark_multiplier # Include mark multiplier
        
        self.health -= final_damage # Use final_damage
        # Update log to show effective armor if different
        log_armor_part = f"Armor: {self.current_armor_value}"
        if ignore_armor_amount > 0:
            log_armor_part = f"EffArmor: {effective_armor:.1f} (Base: {self.current_armor_value}, Ign: {ignore_armor_amount})"
            
        # More detailed debug print
        #print(f"Enemy {self.enemy_id}: Took {final_damage:.2f} damage." # Use final_damage
              #f" (Base: {base_damage:.1f}, Type: {damage_type}, TypeMod: {type_modifier:.2f}, {log_armor_part}, ArmorMod: {armor_multiplier:.2f}, BonusMult: {bonus_multiplier:.2f}, MarkMult: {mark_multiplier:.2f})." # Added MarkMult to log
              #f" Health: {self.health:.2f}/{self.max_health}")
        
        was_killed = self.health <= 0
        bounty_triggered = False # Initialize bounty flag
        gold_penalty = 0 # Initialize penalty
        gold_on_kill_triggered = False # Initialize gold_on_kill flag
        gold_on_kill_amount = 0 # Initialize gold_on_kill amount

        if was_killed:
            # <<< START RE-ADDED BOUNTY CHECK >>>
            if source_special and source_special.get("effect") == "bounty_on_kill":
                bounty_triggered = True
                gold_penalty = source_special.get("gold_penalty", 1) # Default penalty to 1
                #print(f"!!! Enemy {self.enemy_id} killed by Bounty Hunter! Triggering {gold_penalty} gold penalty.")
                # Store the tower that killed this enemy - THIS IS THE CRITICAL LINE
                if hasattr(source_special, 'get') and callable(source_special.get):
                     # Assuming source_special is a dict containing tower reference
                     # Adjust key if needed (e.g., 'parent_tower', 'source_tower')
                     if 'source_tower' in source_special: # Make sure key exists
                         self.killed_by = source_special.get("source_tower")
                     else:
                         #print("Warning: bounty_on_kill special missing 'source_tower' key.")
                         self.killed_by = None # Or handle error appropriately
                else:
                     #print("Warning: source_special is not a dict or missing get method for bounty_on_kill.")
                     self.killed_by = None
            # <<< END RE-ADDED BOUNTY CHECK >>>
            # Check for gold_on_kill as a separate possibility
            elif source_special and source_special.get("effect") == "gold_on_kill":
                chance = source_special.get("chance_percent", 0)
                amount = source_special.get("gold_amount", 0)
                if random.random() * 100 < chance:
                    gold_on_kill_triggered = True
                    gold_on_kill_amount = amount
                    # <<< ADDED: Store amount on enemy object >>>
                    self.pending_gold_on_kill = amount 
                    #print(f"$$$ Gold on Kill CHANCE ({chance}%) SUCCEEDED! Granting {amount} extra gold for killing {self.enemy_id}.")
                # else: # Optional log for failure
                #    print(f"... Gold on Kill CHANCE ({chance}%) failed for killing {self.enemy_id}.")

        # Return a dictionary with results
        return {
            "damage_dealt": final_damage,
            "was_killed": was_killed,
            "bounty_triggered": bounty_triggered,
            "gold_penalty": gold_penalty, # Return penalty amount (0 if not triggered)
            "gold_on_kill_triggered": gold_on_kill_triggered, # ADDED
            "gold_on_kill_amount": gold_on_kill_amount      # ADDED
        }
        
    def reduce_armor(self, amount):
        """Reduces the enemy's current armor value by the specified amount."""
        # Optional: Define a minimum armor value if needed (e.g., -20)
        min_armor = -20 
        
        old_armor = self.current_armor_value
        self.current_armor_value -= amount
        self.current_armor_value = max(min_armor, self.current_armor_value) # Clamp to minimum
        
        if self.current_armor_value != old_armor:
            print(f"Enemy {self.enemy_id} armor reduced by {amount}. New armor: {self.current_armor_value}")
            # Note: No need to recalculate anything immediately, 
            # take_damage will use the updated current_armor_value next time it's hit.
            
    def reduce_max_health(self, percentage):
        """Reduces the enemy's current maximum health by a percentage."""
        if self.max_health <= 1: # Already at minimum
            return

        reduction_amount = self.max_health * (percentage / 100.0)
        old_max_health = self.max_health
        
        # Reduce max health, ensuring it doesn't go below 1
        self.max_health = max(1.0, self.max_health - reduction_amount)
        
        # Clamp current health to the new max health
        self.health = min(self.health, self.max_health)
        
        #print(f"### MAX HP REDUCED for {self.enemy_id}: {old_max_health:.1f} -> {self.max_health:.1f} (-{reduction_amount:.1f}). Current HP: {self.health:.1f}")

    def draw(self, screen, enemy_assets, grid_offset_x=0, grid_offset_y=0):
        """Draw the enemy using its sprite and a health bar, applying grid offset."""
        # Calculate draw position with offset
        draw_x = self.x + grid_offset_x
        draw_y = self.y + grid_offset_y

        # Get the base image for this enemy
        base_image = enemy_assets.get_image(self.enemy_id)
        if not base_image:
             return # Cannot draw if image failed to load

        image_to_draw = base_image # Start with the original image

        # --- DEBUG: Print status effects --- 
        # print(f"DEBUG Draw Enemy {self.enemy_id}: Status Effects = {list(self.status_effects.keys())}")
        # --- End Debug ---

        # --- Apply Bonechill Tint --- 
        is_bonechilled = 'bonechill' in self.status_effects
        # if is_bonechilled:
        #     # --- Alternative Tint Logic: Additive Blend --- 
        #     tinted_image = base_image.copy()
        #     # Create a surface for the blue overlay with per-pixel alpha
        #     overlay = pygame.Surface(tinted_image.get_size(), pygame.SRCALPHA)
        #     # Fill it with a semi-transparent blue (adjust alpha 0-255 for strength)
        #     overlay.fill((0, 0, 255, 80)) # Light blue tint (80 alpha)
        #     # Blit the overlay onto the image copy using default blend (additive)
        #     tinted_image.blit(overlay, (0,0))
        #     image_to_draw = tinted_image
        #     # --- End Alternative Tint --- 
        # --- End Bonechill Tint ---

        # Draw enemy sprite (always draw original now)
        rect = base_image.get_rect(center=(int(draw_x), int(draw_y)))
        screen.blit(base_image, rect)

        # --- Draw Status Effect Overlays (after main sprite) --- 
        if is_bonechilled:
            overlay_image = enemy_assets.get_status_overlay_image('bonechill')
            # --- DEBUG: Check if overlay image was retrieved ---
            #print(f"DEBUG Draw Enemy {self.enemy_id}: Bonechilled! Overlay image found? {overlay_image is not None}")
            # --- End Debug ---
            if overlay_image:
                # Draw overlay centered on the same position as the enemy
                overlay_rect = overlay_image.get_rect(center=(int(draw_x), int(draw_y)))
                screen.blit(overlay_image, overlay_rect)
        
        # --- NEW: Draw Marked for Death Overlay --- 
        if "marked_for_death" in self.status_effects:
            mark_overlay_image = enemy_assets.get_status_overlay_image('marked_for_death')
            if mark_overlay_image:
                mark_rect = mark_overlay_image.get_rect(center=(int(draw_x), int(draw_y)))
                screen.blit(mark_overlay_image, mark_rect)
            else:
                # Optional fallback: Draw a simple red circle if image missing
                pygame.draw.circle(screen, (255, 0, 0), (int(draw_x), int(draw_y)), 10, 2) 
        # --- END Marked for Death Overlay --- 

        # Draw health bar above the enemy sprite (using draw coordinates)
        health_width = GRID_SIZE * 0.8  
        health_height = 5
        health_x = draw_x - health_width // 2
        health_y = draw_y - GRID_SIZE // 2 - health_height - 2 
        
        # Background (red)
        pygame.draw.rect(screen, RED, 
                        (health_x, health_y, health_width, health_height))
        
        # Health (green)
        health_percent = max(0, self.health / self.max_health) 
        current_health_width = int(health_width * health_percent)
        pygame.draw.rect(screen, GREEN,
                        (health_x, health_y, 
                         current_health_width, health_height))

    def rewind_waypoints(self, num_waypoints):
        """Instantly moves the enemy back a specified number of waypoints."""
        if num_waypoints <= 0 or self.path_index == 0:
            return # Nothing to rewind

        current_index = self.path_index
        new_index = max(0, current_index - num_waypoints)

        if new_index == current_index:
            return # No change in index

        #print(f"REWIND: Enemy {self.enemy_id} moving from waypoint {current_index} back to {new_index} (rewound {num_waypoints} steps)")

        self.path_index = new_index

        # Get target grid cell coords for the NEW waypoint
        target_grid_x, target_grid_y = self.grid_path[self.path_index]
        
        # Convert target grid cell to target pixel coordinates (center of cell)
        target_x_pixel = (target_grid_x * GRID_SIZE) + (GRID_SIZE // 2)
        target_y_pixel = (target_grid_y * GRID_SIZE) + (GRID_SIZE // 2)
        
        # Instantly update position to the center of the new target waypoint
        self.x = target_x_pixel
        self.y = target_y_pixel
        self.rect.center = (int(self.x), int(self.y)) # Update rect position too

        # --- Optional: Recalculate direction immediately (to prevent weird initial movement) ---
        # Get the NEXT waypoint after the rewind
        next_waypoint_index = self.path_index + 1
        if next_waypoint_index < len(self.grid_path):
            next_grid_x, next_grid_y = self.grid_path[next_waypoint_index]
            next_x_pixel = (next_grid_x * GRID_SIZE) + (GRID_SIZE // 2)
            next_y_pixel = (next_grid_y * GRID_SIZE) + (GRID_SIZE // 2)
            
            dx = next_x_pixel - self.x
            dy = next_y_pixel - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > 0:
                # Update internal direction if your movement logic uses it
                # Assuming self.direction is used, otherwise adapt to your specific move logic
                # If move() calculates direction on the fly, this might not be needed
                # self.direction = pygame.Vector2(dx / distance, dy / distance) 
                pass # If move() recalculates direction each time, no need to set it here
        # --- End Optional Direction Recalculation ---
