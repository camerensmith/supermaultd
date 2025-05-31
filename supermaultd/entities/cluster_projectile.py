import pygame
import math
import random
from config import *
from entities.projectile import Projectile
from entities.effect import Effect
from entities.grenade_projectile import GrenadeProjectile

class ClusterProjectile(Projectile):
    def __init__(self, start_x, start_y, damage, speed, projectile_id,
                 direction_angle, max_distance, splash_radius,
                 source_tower=None, is_crit=False, special_effect=None,
                 damage_type="normal", asset_loader=None,
                 pellets=5,  # Number of pellets in the spread
                 spread_angle=30,  # Total spread angle in degrees
                 detonation_time=2.0,  # Time until explosion
                 explosion_radius=100):  # Radius of final explosion
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
        
        # Cluster-specific properties
        self.pellets = pellets
        self.spread_angle = spread_angle
        self.detonation_time = detonation_time
        self.explosion_radius = explosion_radius
        self.spawn_time = pygame.time.get_ticks() / 1000.0  # Current time in seconds
        self.has_detonated = False
        
        # Store world angle for drawing
        self.world_angle_degrees = math.degrees(direction_angle)
        
        # Set initial velocity with slight random variation
        self.vx = math.cos(direction_angle) * speed * random.uniform(0.9, 1.1)
        self.vy = math.sin(direction_angle) * speed * random.uniform(0.9, 1.1)
        
        # Add slight random initial vertical movement
        self.vy += random.uniform(-20, 20)
        
        # Movement properties
        self.float_speed = 50  # Base floating speed
        self.float_time = 0  # Time counter for floating motion
        self.float_direction = random.uniform(0, 2 * math.pi)  # Random initial float direction

    def move(self, time_delta, enemies):
        """Move the cluster projectile with floaty movement and check for detonation."""
        if self.collided or self.has_detonated:
            return
            
        # Update float time
        self.float_time += time_delta
        
        # Calculate float movement (sine wave pattern)
        float_offset_x = math.sin(self.float_time * 2) * self.float_speed * time_delta
        float_offset_y = math.cos(self.float_time * 2) * self.float_speed * time_delta
        
        # Update position with float movement
        self.x += self.vx * time_delta + float_offset_x
        self.y += self.vy * time_delta + float_offset_y
        
        # Update world angle based on combined velocity
        combined_vx = self.vx + float_offset_x / time_delta
        combined_vy = self.vy + float_offset_y / time_delta
        if combined_vx != 0 or combined_vy != 0:
            self.world_angle_degrees = math.degrees(math.atan2(-combined_vy, combined_vx))
        
        # Check for detonation timer
        current_time = pygame.time.get_ticks() / 1000.0
        if current_time - self.spawn_time >= self.detonation_time:
            self.detonate(enemies)
            return

    def detonate(self, enemies):
        """Create multiple pellets in a spread pattern and handle their explosions."""
        self.has_detonated = True
        self.collided = True
        
        # Calculate spread angles
        base_angle = math.radians(self.world_angle_degrees)
        spread_rad = math.radians(self.spread_angle)
        angle_step = spread_rad / (self.pellets - 1) if self.pellets > 1 else 0
        
        # Create pellets in spread pattern
        pellets = []
        for i in range(self.pellets):
            # Calculate angle for this pellet
            pellet_angle = base_angle - (spread_rad / 2) + (angle_step * i)
            
            # Add slight random variation to each pellet's angle
            pellet_angle += random.uniform(-0.1, 0.1)
            
            # Create pellet projectile that will detonate
            pellet = GrenadeProjectile(
                start_x=self.x,
                start_y=self.y,
                damage=self.damage / self.pellets,  # Split damage among pellets
                speed=self.speed * 0.8,  # Slightly slower than parent
                projectile_id=self.projectile_id,
                direction_angle=pellet_angle,
                max_distance=self.explosion_radius,  # Travel to explosion radius
                splash_radius=self.splash_radius,
                source_tower=self.source_tower,
                is_crit=self.is_crit,
                special_effect=self.special_effect,
                damage_type=self.damage_type,
                asset_loader=self.asset_loader,
                detonation_time=self.detonation_time,  # Use the same detonation time
                max_bounces=0,  # No bounces for pellets
                explosion_radius=self.explosion_radius  # Use the same explosion radius
            )
            pellets.append(pellet)
        
        # Create initial explosion effect
        explosion = Effect(
            self.x,
            self.y,
            self.asset_loader("assets/effects/fire_burst.png") if self.asset_loader else None,
            duration=0.1,
            target_size=(80, 80)
        )
        
        # Return pellets and explosion for game scene to handle
        return {
            'projectiles': pellets,
            'new_effects': [explosion]
        } 