import pygame
import math
import pymunk
from config import *
from entities.projectile import Projectile
from entities.effect import Effect

class GrenadeProjectile(Projectile):
    def __init__(self, start_x, start_y, damage, speed, projectile_id,
                 direction_angle, max_distance, splash_radius,
                 source_tower=None, is_crit=False, special_effect=None,
                 damage_type="normal", asset_loader=None,
                 detonation_time=2.0,  # Time until explosion
                 max_bounces=3,        # Maximum number of bounces
                 bounce_speed_loss=0.2, # Speed loss per bounce (20%)
                 explosion_radius=100): # Radius of final explosion
        # Initialize base projectile with direction angle in degrees
        super().__init__(start_x, start_y, damage, speed, projectile_id,
                        direction_angle=math.degrees(direction_angle),  # Convert to degrees for parent
                        max_distance=max_distance,
                        splash_radius=splash_radius,
                        source_tower=source_tower,
                        is_crit=is_crit,
                        special_effect=special_effect,
                        damage_type=damage_type,
                        asset_loader=asset_loader)
        
        # Grenade-specific properties
        self.detonation_time = detonation_time
        self.max_bounces = max_bounces
        self.bounce_speed_loss = bounce_speed_loss
        self.explosion_radius = explosion_radius
        self.bounces_remaining = max_bounces
        self.spawn_time = pygame.time.get_ticks() / 1000.0  # Current time in seconds
        self.has_detonated = False
        
        # Store world angle for drawing
        self.world_angle_degrees = math.degrees(direction_angle)
        
        # Set initial velocity with higher initial speed and upward component
        initial_speed = speed * 1.5  # Increase initial speed
        self.vx = math.cos(direction_angle) * initial_speed
        self.vy = math.sin(direction_angle) * initial_speed - 100  # Add slight upward component

    def move(self, time_delta, enemies, towers):
        """Move the grenade using simple physics."""
        if self.collided or self.has_detonated:
            return

        # Apply lighter gravity
        self.vy += 200 * time_delta  # Reduced gravity effect
        
        # Update position
        self.x += self.vx * time_delta
        self.y += self.vy * time_delta
        
        # Update angle based on velocity
        if self.vx != 0 or self.vy != 0:
            self.world_angle_degrees = math.degrees(math.atan2(-self.vy, self.vx))

        # Check for detonation timer
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.spawn_time >= self.detonation_time:
            self.detonate(enemies)
            return

        # Check for enemy collisions
        collision_radius_sq = (GRID_SIZE * 0.4)**2
        for enemy in enemies:
            if enemy.health > 0:
                dx = enemy.x - self.x
                dy = enemy.y - self.y
                dist_sq = dx**2 + dy**2
                if dist_sq <= collision_radius_sq:
                    self.detonate(enemies)
                    return

        # Check for tower collisions
        for tower in towers:
            if tower != self.source_tower:  # Don't collide with source tower
                dx = tower.x - self.x
                dy = tower.y - self.y
                dist_sq = dx**2 + dy**2
                if dist_sq <= (GRID_SIZE * 0.8)**2:  # Tower collision radius
                    self.bounces_remaining -= 1
                    if self.bounces_remaining <= 0:
                        self.detonate(enemies)
                        return
                    
                    # Calculate bounce direction
                    normal = pymunk.Vec2d(dx, dy).normalized()
                    velocity = pymunk.Vec2d(self.vx, self.vy)
                    
                    # Manual vector reflection: v' = v - 2(v·n)n
                    dot_product = velocity.dot(normal)
                    new_velocity = velocity - 2 * dot_product * normal
                    
                    # Apply speed loss
                    new_velocity *= (1 - self.bounce_speed_loss)
                    
                    self.vx = new_velocity.x
                    self.vy = new_velocity.y

    def detonate(self, enemies):
        """Create explosion effect and deal damage in radius."""
        self.has_detonated = True
        self.collided = True
        
        # Play explosion sound
        try:
            explosion_sound = pygame.mixer.Sound("assets/sounds/grenade_explode.mp3")
            explosion_sound.play()
        except:
            #print("Could not play grenade explosion sound")
            pass
        
        # Create explosion effect
        explosion = Effect(
            self.x,
            self.y,
            self.source_tower.asset_loader("assets/effects/fire_burst.png"),
            duration=0.1,
            target_size=(80, 80)
        )
        
        # Deal damage to enemies in radius
        explosion_radius_sq = self.explosion_radius ** 2
        for enemy in enemies:
            if enemy.health > 0:
                dx = enemy.x - self.x
                dy = enemy.y - self.y
                dist_sq = dx**2 + dy**2
                if dist_sq <= explosion_radius_sq:
                    # Calculate damage falloff based on distance
                    distance = math.sqrt(dist_sq)
                    falloff = 1.0 - (distance / self.explosion_radius)
                    damage = self.damage * falloff
                    enemy.take_damage(damage, self.damage_type)
        
        # Return explosion for game scene to handle
        return {
            'projectiles': [],
            'new_effects': [explosion]
        } 