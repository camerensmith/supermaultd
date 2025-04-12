import pygame
import math
# Assuming config might be needed later, e.g., for enemy radius approximations
# import config 

class OrbitingDamager:
    """
    Represents an orbiting object that deals damage to nearby enemies on contact.
    """
    def __init__(self, parent_tower, orb_data, start_angle_offset=0.0):
        """
        Initialize the orbiting damager.

        Args:
            parent_tower: The Tower entity this orbiter belongs to.
            orb_data: Dictionary containing orb parameters from the tower's special block.
                      Expected keys: 'orb_asset_id', 'orb_orbit_radius', 'orb_angular_speed',
                                     'orb_damage', 'orb_damage_type', 'orb_hit_cooldown', 
                                     'orb_collision_radius'.
            start_angle_offset: Initial angle offset in degrees (for spacing multiple orbs).
        """
        self.parent_tower = parent_tower
        self.orb_data = orb_data

        # Extract parameters from orb_data with defaults
        self.asset_id = self.orb_data.get("orb_asset_id", "default_orb") # Need a default visual
        self.orbit_radius = self.orb_data.get("orb_orbit_radius", 50)
        self.angular_speed = self.orb_data.get("orb_angular_speed", 90) # Degrees per second
        self.damage = self.orb_data.get("orb_damage", 10)
        self.damage_type = self.orb_data.get("orb_damage_type", "normal")
        self.hit_cooldown = self.orb_data.get("orb_hit_cooldown", 0.5) # Seconds
        self.collision_radius = self.orb_data.get("orb_collision_radius", 10)
        self.collision_radius_sq = self.collision_radius ** 2

        # State
        self.current_angle = start_angle_offset # Start at the specified offset
        self.last_hit_times = {} # Key: enemy.enemy_id, Value: timestamp
        self.x = 0.0 # Current world X (relative to grid, like tower/enemy)
        self.y = 0.0 # Current world Y
        
        # Calculate initial position immediately
        self._update_position() 

    def _update_position(self):
        """Helper method to calculate x, y based on current angle and parent."""
        angle_rad = math.radians(self.current_angle)
        self.x = self.parent_tower.x + self.orbit_radius * math.cos(angle_rad)
        self.y = self.parent_tower.y + self.orbit_radius * math.sin(angle_rad)

    def update(self, time_delta, all_enemies, current_time):
        """
        Update the orbiter's position and check for collisions.

        Args:
            time_delta: Time elapsed since the last frame.
            all_enemies: List of all active Enemy objects.
            current_time: The current game time in seconds.
            
        Returns:
            False (unless lifetime logic is added later).
        """
        # 1. Update Angle
        self.current_angle += self.angular_speed * time_delta
        self.current_angle %= 360 # Keep angle within 0-360

        # 2. Update Position
        self._update_position()

        # 3. Collision Check
        for enemy in all_enemies:
            if enemy.health <= 0:
                continue

            # --- Refined Collision Check --- 
            # Estimate enemy radius (can be refined later if enemies have explicit radius)
            # Assuming config is imported or GRID_SIZE is globally accessible
            # If not, we might need to pass GRID_SIZE in
            try: 
                # Try accessing GRID_SIZE via parent_tower if available
                # This assumes Tower has access to GRID_SIZE or config
                # A better approach might be to pass GRID_SIZE to __init__
                # For now, let's estimate based on a common value
                enemy_radius_approx = 16 # Estimate based on GRID_SIZE=32 or similar 
            except NameError:
                enemy_radius_approx = 10 # Fallback if GRID_SIZE isn't accessible easily
                
            # Calculate combined radius squared
            combined_radius = self.collision_radius + enemy_radius_approx
            combined_radius_sq = combined_radius ** 2
            
            # Calculate distance squared between centers
            dist_sq = (self.x - enemy.x)**2 + (self.y - enemy.y)**2

            # Check if distance is less than combined radius
            if dist_sq < combined_radius_sq:
                # --- DEBUG PRINT --- 
                print(f"DEBUG: Orb collision detected! Orb @ ({int(self.x)},{int(self.y)}) - Enemy {enemy.enemy_id} @ ({int(enemy.x)},{int(enemy.y)}) DistSq: {dist_sq:.1f}, CombinedRadSq: {combined_radius_sq:.1f}")
                # -----------------
                
                # Check hit cooldown for this specific enemy
                last_hit = self.last_hit_times.get(enemy.enemy_id, -1.0) # Get last hit time, default to -1
                
                if current_time - last_hit > self.hit_cooldown:
                    print(f"OrbitingDamager from {self.parent_tower.tower_id} hit {enemy.enemy_id}")
                    enemy.take_damage(self.damage, self.damage_type)
                    self.last_hit_times[enemy.enemy_id] = current_time # Record the hit time

        # Return False indicates it should not be removed (unless lifetime is added)
        return False

    def draw(self, screen, assets, offset_x, offset_y):
        """
        Draw the orbiting damager.

        Args:
            screen: The pygame surface to draw on.
            assets: The asset manager (e.g., projectile_assets) containing the orb visual.
            offset_x: Grid offset X.
            offset_y: Grid offset Y.
        """
        draw_x = self.x + offset_x
        draw_y = self.y + offset_y
        
        # Assuming projectile_assets has a generic way to draw based on asset_id
        # If not, this might need adjustment or a dedicated OrbiterAssets manager
        try:
            # Use the correct asset manager method if draw_projectile is specific
            # For now, assuming a generic draw method exists based on ID
            # If using ProjectileAssets, ensure 'alien_orb' is loaded like other projectiles
            assets.draw_projectile(screen, self.asset_id, draw_x, draw_y) 
        except AttributeError:
             # Fallback if draw_projectile doesn't exist or fails
             print(f"Warning: Could not find draw method for orb asset '{self.asset_id}' in provided asset manager.")
             # Draw a simple circle as a fallback
             pygame.draw.circle(screen, (255, 0, 255), (int(draw_x), int(draw_y)), self.collision_radius)
        except Exception as e:
            print(f"Error drawing orb {self.asset_id}: {e}")
            pygame.draw.circle(screen, (255, 0, 0), (int(draw_x), int(draw_y)), self.collision_radius) # Draw red circle on error
