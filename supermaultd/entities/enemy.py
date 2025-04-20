import pygame
import math
import random
from config import *

# Pre-calculate the armor constant for efficiency
ARMOR_CONSTANT = 0.06

class Enemy:
    """Represents an enemy unit in the game."""
    def __init__(self, x, y, grid_path, enemy_id, enemy_data, armor_type, damage_modifiers):
        """
        Initialize an enemy.

        :param x: Starting X pixel coordinate.
        :param y: Starting Y pixel coordinate.
        :param grid_path: List of (grid_x, grid_y) tuples for the path.
        :param enemy_id: Unique identifier string for the enemy type (e.g., 'gnoll').
        :param enemy_data: Dictionary containing stats for this enemy type from config.ENEMY_DATA.
        :param armor_type: String name of the armor type (e.g., 'Light').
        :param damage_modifiers: Dictionary of damage type -> multiplier for this armor.
        """
        self.x = x
        self.y = y
        self.grid_path = grid_path
        self.path_index = 0
        self.enemy_id = enemy_id
        self.image = None  # Will be set during draw based on assets

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
                print(f"Enemy {self.enemy_id}: {effect_type} expired.")
        
        if effects_removed:
            self.recalculate_speed()

    def apply_status_effect(self, effect_type, duration, value, current_time):
        """Apply or refresh a status effect (e.g., slow, stun)."""
        end_time = current_time + duration
        
        # Store effect data - value is used for slow multiplier, ignored for stun
        self.status_effects[effect_type] = { 'end_time': end_time, 'value': value }
        
        print(f"Enemy {self.enemy_id}: Applied {effect_type} until {end_time:.2f}")
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
            print(f"Enemy {self.enemy_id}: Refreshing DoT '{effect_name}'.")
            pass # Overwrite below

        self.active_dots[effect_name] = {
            'damage': damage,
            'interval': interval,
            'next_tick': next_tick_time,
            'end_time': end_time,
            'damage_type': damage_type
        }
        print(f"Enemy {self.enemy_id}: Applied DoT '{effect_name}' ({damage}/{interval}s for {duration}s, type: {damage_type}). Ends at {end_time:.2f}.")

    def update_dots(self, current_time):
        """Processes active DoT effects, applying damage and removing expired ones."""
        if not self.active_dots:
            return

        # Use list keys for safe iteration if removing items
        for effect_name in list(self.active_dots.keys()):
            dot_data = self.active_dots[effect_name]

            # Check for expiry
            if current_time >= dot_data['end_time']:
                print(f"Enemy {self.enemy_id}: DoT '{effect_name}' expired.")
                del self.active_dots[effect_name]
                continue # Move to next DoT

            # Check for tick time
            if current_time >= dot_data['next_tick']:
                print(f"Enemy {self.enemy_id}: DoT '{effect_name}' ticking for {dot_data['damage']} damage ({dot_data['damage_type']}).")
                self.take_damage(dot_data['damage'], dot_data['damage_type'])
                # Schedule next tick
                dot_data['next_tick'] += dot_data['interval']
                # Ensure next_tick doesn't fall behind current_time excessively due to lag
                if dot_data['next_tick'] < current_time:
                     dot_data['next_tick'] = current_time + dot_data['interval']

    def move(self, current_time):
        """Move the enemy towards the next waypoint with wandering behavior."""
        self.update_status_effects(current_time) # Update effects first (slows)
        self.update_dots(current_time) # Process DoT effects
        
        if self.path_index < len(self.grid_path):
            # Get the target grid cell coordinates
            target_grid_x, target_grid_y = self.grid_path[self.path_index]
            
            # Convert target grid cell to target pixel coordinates (center of cell)
            target_x_pixel = (target_grid_x * GRID_SIZE) + (GRID_SIZE // 2)
            target_y_pixel = (target_grid_y * GRID_SIZE) + (GRID_SIZE // 2)

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
                    print(f"Enemy reached waypoint {self.path_index-1}, moving to next waypoint")
            else:
                # If we're already at the target, move to next waypoint
                self.path_index += 1
                # print(f"Enemy {self.enemy_id} already at waypoint {self.path_index-1}, moving to next waypoint") # Less noisy
        
        # --- ADDED: Update Rect Position ---
        self.rect.center = (int(self.x), int(self.y)) # Keep rect centered on enemy
        # ------------------------------------
        
    def take_damage(self, base_damage, damage_type="normal", bonus_multiplier=1.0, ignore_armor_amount=0, source_special=None):
        """Apply damage to the enemy, considering armor type, armor value, bonus multipliers, and armor ignore.

        Args:
            base_damage: The raw damage value.
            damage_type: The type of damage (e.g., 'normal', 'piercing').
            bonus_multiplier: Additional multiplier (e.g., from Shatter).
            ignore_armor_amount: Base amount of armor to ignore (e.g., from target debuffs).
            source_special: The 'special' dictionary from the attacking tower/projectile (optional).
        """
        # 1. Apply Armor Type vs Damage Type multiplier
        type_modifier = self.damage_modifiers.get(damage_type, 1.0)
        damage_after_type = base_damage * type_modifier

        # --- NEW: Check source_special for 'ignore_armor_on_hit' --- 
        if source_special and source_special.get("effect") == "ignore_armor_on_hit":
            ignore_amount_from_source = source_special.get("amount", 0)
            ignore_armor_amount += ignore_amount_from_source # Add to existing ignore amount
            print(f"... Applying ignore_armor_on_hit ({ignore_amount_from_source}) from source. Total ignore: {ignore_armor_amount}")
        # --- END NEW CHECK ---

        # --- Apply Aura Armor Reduction ---
        if self.aura_armor_reduction > 0:
            ignore_armor_amount += self.aura_armor_reduction
            print(f"... Applying aura armor reduction ({self.aura_armor_reduction}). Total ignore: {ignore_armor_amount}")
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
        
        # 3. Apply Bonus Multiplier (e.g., from Shatter)
        final_damage = actual_damage * bonus_multiplier
        
        self.health -= final_damage # Use final_damage
        # Update log to show effective armor if different
        log_armor_part = f"Armor: {self.current_armor_value}"
        if ignore_armor_amount > 0:
            log_armor_part = f"EffArmor: {effective_armor:.1f} (Base: {self.current_armor_value}, Ign: {ignore_armor_amount})"
            
        # More detailed debug print
        print(f"Enemy {self.enemy_id}: Took {final_damage:.2f} damage." # Use final_damage
              f" (Base: {base_damage:.1f}, Type: {damage_type}, TypeMod: {type_modifier:.2f}, {log_armor_part}, ArmorMod: {armor_multiplier:.2f}, BonusMult: {bonus_multiplier:.2f})."
              f" Health: {self.health:.2f}/{self.max_health}")
        
        # Return both the damage dealt and whether it was killed
        was_killed = self.health <= 0
        return final_damage, was_killed
        
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
        
        print(f"### MAX HP REDUCED for {self.enemy_id}: {old_max_health:.1f} -> {self.max_health:.1f} (-{reduction_amount:.1f}). Current HP: {self.health:.1f}")

    def draw(self, screen, enemy_assets, offset_x=0, offset_y=0):
        """Draw the enemy using its sprite and a health bar, applying grid offset."""
        # Calculate draw position with offset
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y

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
            print(f"DEBUG Draw Enemy {self.enemy_id}: Bonechilled! Overlay image found? {overlay_image is not None}")
            # --- End Debug ---
            if overlay_image:
                # Draw overlay centered on the same position as the enemy
                overlay_rect = overlay_image.get_rect(center=(int(draw_x), int(draw_y)))
                screen.blit(overlay_image, overlay_rect)
        # Add checks for other status overlays here if needed
        # elif 'burning' in self.status_effects:
        #    overlay_image = enemy_assets.get_status_overlay_image('burning')
        #    if overlay_image: ...
        # --- End Status Overlays ---

        # --- Draw DoT Visual Effects --- 
        # Check if the 'spore_dot' effect is active
        if "spore_dot" in self.active_dots:
            dot_visual = enemy_assets.dot_effect_visuals.get("spore_dot")
            if dot_visual:
                # Draw the visual centered on the enemy
                visual_rect = dot_visual.get_rect(center=(int(draw_x), int(draw_y)))
                screen.blit(dot_visual, visual_rect.topleft)

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
