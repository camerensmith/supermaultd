import pygame
import math
from config import GRID_SIZE # Assuming GRID_SIZE is in config
# from .effect import Effect # Import if needed for explosion visual
from .effect import Effect 

# Need os for path joining
import os 

class PassThroughExploder:
    """
    Represents an entity that travels a fixed distance, damages enemies it
    passes through, and explodes upon reaching its destination.
    """
    def __init__(self, parent_tower, target_enemy, special_data, asset_loader):
        """
        Initialize the PassThroughExploder.

        Args:
            parent_tower: The Tower entity that launched this.
            target_enemy: The initial enemy targeted to determine direction.
            special_data: Dictionary containing parameters from the tower's special block.
            asset_loader: A callable function (e.g., game_scene.load_single_image) to load assets.
        """
        self.parent_tower = parent_tower
        self.special_data = special_data
        self.asset_loader = asset_loader # Store the loader function
        self.start_x = parent_tower.x
        self.start_y = parent_tower.y
        self.x = self.start_x
        self.y = self.start_y

        # Extract parameters
        self.asset_id = self.special_data.get("pass_through_asset_id", parent_tower.tower_id)
        self.travel_speed = self.special_data.get("travel_speed", 300)
        distance_units = self.special_data.get("fixed_travel_distance_units", 500)
        self.pass_through_damage = self.special_data.get("pass_through_damage", 0)
        self.pass_through_damage_type = self.special_data.get("pass_through_damage_type", "normal")
        self.pass_through_hit_cooldown = self.special_data.get("pass_through_hit_cooldown", 0.5)

        # Convert distance units to pixels
        range_scale_factor = GRID_SIZE / 200.0 # Adjust scale factor if needed
        self.fixed_travel_distance_pixels = distance_units * range_scale_factor

        # Extract explosion parameters (needed for trigger_explosion)
        self.explosion_radius_units = self.special_data.get("explosion_radius_units", 100)
        self.explosion_damage = self.special_data.get("explosion_damage", 0)
        self.explosion_damage_type = self.special_data.get("explosion_damage_type", "normal")
        self.explosion_effect_asset_id = self.special_data.get("explosion_effect_asset_id") # Optional
        self.explosion_radius_pixels = self.explosion_radius_units * range_scale_factor
        # --- Load Explosion Effect Image --- 
        self.explosion_image_surface = None
        if self.explosion_effect_asset_id and self.asset_loader:
            # Construct path relative to effects directory
            effect_image_path = os.path.join("assets", "effects", f"{self.explosion_effect_asset_id}.png")
            self.explosion_image_surface = self.asset_loader(effect_image_path)
        # -----------------------------------

        # Calculate initial direction vector (normalized)
        if target_enemy:
            dx = target_enemy.x - self.start_x
            dy = target_enemy.y - self.start_y
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                self.dir_x = dx / distance
                self.dir_y = dy / distance
            else:
                self.dir_x = 1.0 # Default direction if target is exactly at start
                self.dir_y = 0.0
        else:
            # Handle case where no target was found (shouldn't happen if tower range > 0)
            print(f"Warning: {self.__class__.__name__} launched without target. Defaulting direction.")
            self.dir_x = 1.0
            self.dir_y = 0.0

        # State
        self.distance_traveled = 0.0
        self.pass_through_hit_times = {} # Key: enemy.enemy_id, Value: timestamp
        self.is_active = True # Flag to indicate if it should be updated/drawn

        print(f"Launched {self.asset_id} towards ({self.dir_x:.2f}, {self.dir_y:.2f}), max dist: {self.fixed_travel_distance_pixels:.1f}px")

    def update(self, time_delta, all_enemies, current_time):
        """
        Move the entity, check for pass-through collisions, and check max distance.

        Args:
            time_delta: Time elapsed since the last frame.
            all_enemies: List of all active Enemy objects.
            current_time: The current game time in seconds.

        Returns:
            True if the entity should be removed (e.g., max distance reached), False otherwise.
        """
        if not self.is_active:
            return True # Already finished

        # 1. Calculate Movement for this frame
        move_dist = self.travel_speed * time_delta
        delta_x = self.dir_x * move_dist
        delta_y = self.dir_y * move_dist

        # Store previous position for line segment check
        prev_x, prev_y = self.x, self.y

        # Update position
        self.x += delta_x
        self.y += delta_y
        self.distance_traveled += move_dist

        # 2. Pass-Through Collision Check
        segment_vec_x = self.x - prev_x
        segment_vec_y = self.y - prev_y
        segment_len_sq = segment_vec_x**2 + segment_vec_y**2

        if segment_len_sq > 1e-6: # Avoid division by zero if no movement
            for enemy in all_enemies:
                if enemy.health <= 0:
                    continue

                # Estimate enemy radius (consistent with OrbitingDamager, maybe centralize later)
                enemy_radius_approx = 16
                enemy_radius_sq = enemy_radius_approx**2

                # Vector from segment start to enemy center
                w_x = enemy.x - prev_x
                w_y = enemy.y - prev_y

                # Project W onto segment vector V
                dot_w_v = w_x * segment_vec_x + w_y * segment_vec_y
                t = dot_w_v / segment_len_sq

                # Clamp t to the segment [0, 1]
                t_clamped = max(0, min(1, t))

                # Find the closest point on the segment to the enemy center
                closest_x = prev_x + t_clamped * segment_vec_x
                closest_y = prev_y + t_clamped * segment_vec_y

                # Check distance squared from closest point to enemy center
                dist_sq_to_enemy = (closest_x - enemy.x)**2 + (closest_y - enemy.y)**2

                # Collision if distance squared is less than enemy radius squared
                if dist_sq_to_enemy < enemy_radius_sq:
                    # Collision detected!
                    last_hit = self.pass_through_hit_times.get(enemy.enemy_id, -1.0)
                    if current_time - last_hit > self.pass_through_hit_cooldown:
                        print(f"PassThroughExploder ({self.asset_id}) hit {enemy.enemy_id}")
                        enemy.take_damage(self.pass_through_damage, self.pass_through_damage_type)
                        self.pass_through_hit_times[enemy.enemy_id] = current_time

        # 3. Check Max Distance Reached
        if self.distance_traveled >= self.fixed_travel_distance_pixels:
            print(f"{self.asset_id} reached max distance.")
            self.is_active = False # Stop moving/damaging
            explosion_effect = self.trigger_explosion(all_enemies) # Handle explosion effect
            return True, explosion_effect # Signal removal AND return the effect instance

        return False, None # Still active, no effect created this frame

    # Note: check_segment_collision was integrated directly into update loop
    # def check_segment_collision(self, x1, y1, x2, y2, enemy):
    #     """ Placeholder for line segment vs circle collision check """
    #     # TODO: Implement geometry check here
    #     return False

    def trigger_explosion(self, all_enemies):
        """ Handle the explosion effect at the end location. 
            Returns the created visual Effect instance, or None.
        """
        print(f"BOOM! {self.asset_id} exploding at ({int(self.x)}, {int(self.y)})")
        explosion_radius_sq = self.explosion_radius_pixels ** 2
        enemies_hit = 0

        for enemy in all_enemies:
            if enemy.health <= 0:
                continue

            dist_sq = (self.x - enemy.x)**2 + (self.y - enemy.y)**2
            if dist_sq < explosion_radius_sq:
                print(f"...Explosion hitting {enemy.enemy_id}")
                enemy.take_damage(self.explosion_damage, self.explosion_damage_type)
                enemies_hit += 1
        
        if enemies_hit > 0:
             print(f"...Explosion hit {enemies_hit} enemies.")

        # Create and return the visual Effect instance
        if self.explosion_image_surface:
            # Use explosion_radius_pixels to determine size, ensure it's a tuple (width, height)
            effect_size = (int(self.explosion_radius_pixels * 2), int(self.explosion_radius_pixels * 2))
            return Effect(self.x, self.y, self.explosion_image_surface, duration=0.5, target_size=effect_size)
        else:
            return None

    def draw(self, screen, assets, offset_x, offset_y):
        """
        Draw the travelling entity.

        Args:
            screen: The pygame surface to draw on.
            assets: The asset manager (e.g., projectile_assets) containing the visual.
            offset_x: Grid offset X.
            offset_y: Grid offset Y.
        """
        if not self.is_active:
             return # Don't draw if inactive (already exploded)

        draw_x = self.x + offset_x
        draw_y = self.y + offset_y

        # Assuming projectile_assets handles drawing via asset_id
        try:
            assets.draw_projectile(screen, self.asset_id, draw_x, draw_y)
        except AttributeError:
             print(f"Warning: Could not find draw method for asset '{self.asset_id}' in provided asset manager.")
             pygame.draw.circle(screen, (0, 0, 255), (int(draw_x), int(draw_y)), 5) # Blue fallback
        except Exception as e:
            print(f"Error drawing {self.asset_id}: {e}")
            pygame.draw.circle(screen, (255, 0, 0), (int(draw_x), int(draw_y)), 5) # Red fallback