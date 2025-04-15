import pygame
import math
import random
# Assuming config might have constants like GRID_SIZE if needed, but keeping minimal for now
# from config import * 

class OffsetBoomerangProjectile:
    """
    A projectile that travels straight out, then aims for an offset point near the tower, 
    then returns to the tower, damaging enemies it passes through.
    """
    STATE_OUTGOING = 0
    STATE_RETURNING_OFFSET = 1
    STATE_RETURNING_TOWER = 2

    def __init__(self, source_tower, initial_direction_angle, range_pixels, speed, 
                 damage_min, damage_max, damage_type, 
                 hit_cooldown, asset_id, offset_distance, asset_loader):
        
        self.source_tower = source_tower
        self.speed = speed
        self.damage_min = damage_min
        self.damage_max = damage_max
        self.damage_type = damage_type
        self.hit_cooldown = hit_cooldown
        self.asset_id = asset_id
        self.asset_loader = asset_loader # Function to load the image
        self.offset_distance = offset_distance

        # State and Position
        self.state = self.STATE_OUTGOING
        self.start_pos = pygame.Vector2(source_tower.x, source_tower.y)
        self.current_pos = pygame.Vector2(self.start_pos)
        self.distance_traveled = 0.0
        self.max_range_pixels = range_pixels
        self.finished = False # Flag to signal removal by GameScene

        # Targeting / Path Points
        self.initial_angle_rad = math.radians(initial_direction_angle)
        self.max_range_point = self.start_pos + pygame.Vector2(self.max_range_pixels, 0).rotate_rad(self.initial_angle_rad)
        self.offset_return_target = None # Calculated when reaching max range
        self.final_return_target = self.start_pos
        self.current_target_point = self.max_range_point 

        # Velocity
        self.velocity = pygame.Vector2(self.speed, 0).rotate_rad(self.initial_angle_rad)
        
        # Rotation / Drawing
        self.image = None # Loaded in _load_asset
        self.rotated_image = None
        self.rect = None
        self.current_angle_degrees = initial_direction_angle # For rotation visual
        self._load_asset()
        
        # Pass-through damage tracking
        self.recently_hit = {} # {enemy_id: last_hit_time}

    def _load_asset(self):
        """Loads the projectile image using the provided loader function."""
        if self.asset_loader and self.asset_id:
            try:
                self.image = self.asset_loader(self.asset_id) 
                if self.image:
                    self.rotated_image = self.image # Start with non-rotated
                    self.rect = self.rotated_image.get_rect(center=(int(self.current_pos.x), int(self.current_pos.y)))
                    print(f"Loaded asset {self.asset_id} for boomerang.")
                else:
                     print(f"Warning: Asset loader returned None for {self.asset_id}")
                     self._create_fallback_surface()
            except Exception as e:
                 print(f"Error loading boomerang asset '{self.asset_id}': {e}")
                 self._create_fallback_surface()
        else:
            print("Warning: No asset loader or asset_id provided for boomerang. Creating fallback.")
            self._create_fallback_surface()

    def _create_fallback_surface(self):
        """Creates a simple shape if asset loading fails."""
        self.image = pygame.Surface((10, 6), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (255, 165, 0), [(0,0), (10,3), (0,6)])
        self.rotated_image = self.image
        self.rect = self.rotated_image.get_rect(center=(int(self.current_pos.x), int(self.current_pos.y)))

    def _calculate_offset_target(self):
        """Calculates the intermediate return point beside the tower."""
        vec_to_tower = self.start_pos - self.max_range_point
        if vec_to_tower.length() > 0:
            # Get perpendicular vector (swap components, negate one)
            perp_vec = pygame.Vector2(-vec_to_tower.y, vec_to_tower.x).normalize()
        else: 
            # Fallback if somehow length is zero
            perp_vec = pygame.Vector2(0, 1) 
            
        # Add scaled perpendicular vector to tower position
        self.offset_return_target = self.start_pos + perp_vec * self.offset_distance
        print(f"Boomerang reached max range. New target (offset): {self.offset_return_target}")

    def _update_velocity_and_rotation(self):
        """Sets velocity towards the current target point and updates rotation."""
        direction_vec = self.current_target_point - self.current_pos
        distance = direction_vec.length()

        if distance > 0:
            self.velocity = direction_vec.normalize() * self.speed
            # Update visual rotation angle (angle of the velocity vector)
            self.current_angle_degrees = math.degrees(math.atan2(-self.velocity.y, self.velocity.x)) # Negate y for Pygame coords
        else:
            # Reached target point, stop velocity for this frame
            self.velocity = pygame.Vector2(0, 0)

    def update(self, time_delta, all_enemies):
        """Moves the boomerang, handles state changes, and checks for collisions."""
        if self.finished:
            return

        # 1. Move based on current velocity
        distance_this_frame = self.velocity.length() * time_delta
        self.current_pos += self.velocity * time_delta
        if self.state == self.STATE_OUTGOING:
            self.distance_traveled += distance_this_frame

        # 2. Check for state transitions
        if self.state == self.STATE_OUTGOING:
            if self.distance_traveled >= self.max_range_pixels:
                self.state = self.STATE_RETURNING_OFFSET
                self._calculate_offset_target()
                # Check if offset target calculation was successful
                if self.offset_return_target is None:
                     print("Error: Offset target is None after calculation. Finishing boomerang.")
                     self.finished = True
                     return
                self.current_target_point = self.offset_return_target
                self._update_velocity_and_rotation() # Recalculate velocity for new target

        elif self.state == self.STATE_RETURNING_OFFSET:
            # Check proximity to offset target
            # Make sure offset_return_target is not None before checking distance
            if self.offset_return_target and (self.current_pos - self.offset_return_target).length_squared() < (self.speed * time_delta)**2 * 1.1: # Allow slight overshoot
                self.state = self.STATE_RETURNING_TOWER
                self.current_target_point = self.final_return_target
                self._update_velocity_and_rotation()
                print("Boomerang reached offset point. Returning to tower.")

        elif self.state == self.STATE_RETURNING_TOWER:
            # Check proximity to tower
            if (self.current_pos - self.final_return_target).length_squared() < (self.speed * time_delta)**2 * 1.1:
                self.finished = True
                print("Boomerang returned to tower.")
                return # Stop further processing this frame

        # 3. Update rect position after moving
        if self.rect:
            self.rect.center = (int(self.current_pos.x), int(self.current_pos.y))

        # 4. Check for collisions with enemies (pass-through damage)
        current_time = pygame.time.get_ticks() / 1000.0 # Get current time for cooldown
        if self.rect:
            for enemy in all_enemies:
                if enemy.health > 0 and self.rect.colliderect(enemy.rect):
                    last_hit = self.recently_hit.get(enemy.enemy_id, 0)
                    if current_time - last_hit >= self.hit_cooldown:
                        damage = random.uniform(self.damage_min, self.damage_max)
                        enemy.take_damage(damage, self.damage_type)
                        self.recently_hit[enemy.enemy_id] = current_time
                        print(f"Boomerang hit {enemy.enemy_id} for {damage:.2f} damage.")
                        # Note: Boomerang continues, doesn't stop on hit

        # 5. Rotate visual asset (if image loaded)
        if self.image:
            try:
                self.rotated_image = pygame.transform.rotate(self.image, self.current_angle_degrees)
                # Update rect based on rotated image size and current position
                if self.rotated_image: 
                    self.rect = self.rotated_image.get_rect(center=(int(self.current_pos.x), int(self.current_pos.y)))
            except Exception as e:
                print(f"Error rotating boomerang image: {e}")

    def draw(self, screen, projectile_assets, grid_offset_x, grid_offset_y): # Added projectile_assets for consistency, though maybe unused if drawing shape
        """Draws the rotated boomerang projectile."""
        if self.finished or not self.rotated_image or not self.rect:
            return 

        # Adjust position by grid offset for drawing
        draw_pos = self.rect.move(grid_offset_x, grid_offset_y)
        screen.blit(self.rotated_image, draw_pos) 