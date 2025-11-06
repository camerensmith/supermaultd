import pygame
import math
from config import GRID_SIZE

class HarpoonProjectile:
    """
    A completely independent harpoon projectile that pulls enemies towards its source tower.
    This is its own separate attack type and does not interfere with other projectile types.
    """
    def __init__(self, start_x, start_y, target_enemy, tower, special_data):
        """
        Initialize a harpoon projectile.
        
        Args:
            start_x: Starting X position
            start_y: Starting Y position
            target_enemy: The enemy being targeted
            tower: The source tower
            special_data: Dictionary containing harpoon-specific parameters
        """
        self.x = start_x
        self.y = start_y
        self.target_enemy = target_enemy
        self.tower = tower
        self.special_data = special_data
        
        # Extract harpoon-specific parameters
        self.pull_distance = special_data.get("pull_distance", 400) * (GRID_SIZE / 200.0)
        self.pull_duration = special_data.get("pull_duration", 0.5)
        self.shear_multiplier = special_data.get("shear_multiplier", 1.1)
        
        # Calculate tower's collision radius (half of its width/height)
        self.tower_radius = (tower.width_pixels / 2) * 1.1  # Add 10% buffer
        
        # State
        self.is_active = True
        self.pull_start_time = 0
        self.pull_progress = 0
        self.damage_per_tick = 0
        self.current_damage_multiplier = 1.0
        self.collided = False
        
        # Store initial enemy position for pull calculation
        self.initial_enemy_x = target_enemy.x
        self.initial_enemy_y = target_enemy.y
        
        # Calculate initial direction (from tower to enemy)
        dx = target_enemy.x - start_x
        dy = target_enemy.y - start_y
        distance = math.sqrt(dx**2 + dy**2)
        if distance > 0:
            self.dir_x = dx / distance
            self.dir_y = dy / distance
        else:
            self.dir_x = 1.0
            self.dir_y = 0.0
            
        # Initialize active harpoons tracking if needed
        if not hasattr(target_enemy, 'active_harpoons'):
            target_enemy.active_harpoons = []
            
        # Add this harpoon to the enemy's active harpoons
        target_enemy.active_harpoons.append(self)
            
        # Apply initial strike damage with shear multiplier
        initial_damage = tower.base_damage_min * self.shear_multiplier
        target_enemy.take_damage(initial_damage, tower.damage_type)
        
        # Calculate base pull damage per tick (total damage over duration)
        # We want to deal the same amount of damage over the pull duration as the initial strike
        self.base_pull_damage = tower.base_damage_min / (self.pull_duration * 60)  # Assuming 60 FPS
        
        # Visual effect properties
        self.chain_alpha = 255  # For chain fade effect
        self.pull_effect_radius = 0  # For pull visual effect
        self.pull_effect_max_radius = GRID_SIZE * 0.5  # Maximum radius for pull effect
        
    def update(self, time_delta, current_time):
        """
        Update the harpoon's state.
        
        Args:
            time_delta: Time since last update
            current_time: Current game time
            
        Returns:
            True if the harpoon should be removed, False otherwise
        """
        if not self.is_active:
            return True
            
        if not self.target_enemy or self.target_enemy.health <= 0:
            if self in self.target_enemy.active_harpoons:
                self.target_enemy.active_harpoons.remove(self)
            return True
            
        # Start pull if not already started
        if self.pull_start_time == 0:
            self.pull_start_time = current_time
            
        # Calculate pull progress with easing
        elapsed = current_time - self.pull_start_time
        raw_progress = min(1.0, elapsed / self.pull_duration)
        # Use cubic easing for smoother pull
        self.pull_progress = raw_progress * raw_progress * (3 - 2 * raw_progress)
        
        # Update visual effects
        self.chain_alpha = int(255 * (1 - self.pull_progress * 0.5))  # Fade chain as pull progresses
        self.pull_effect_radius = self.pull_effect_max_radius * self.pull_progress
        
        # Count active harpoons on this enemy
        active_harpoons = len(self.target_enemy.active_harpoons)
            
        # Calculate compounded shear multiplier
        compounded_multiplier = self.shear_multiplier ** (active_harpoons - 1)
        
        # Apply pull damage with compounded shear
        # Base damage is already scaled by time_delta in take_damage
        pull_damage = self.base_pull_damage * compounded_multiplier
        self.target_enemy.take_damage(pull_damage, self.tower.damage_type)
        
        # Calculate pull position - gradually move from initial position to tower edge
        pull_distance = self.pull_distance * self.pull_progress
        
        # Calculate position at tower edge
        edge_x = self.tower.x + self.dir_x * self.tower_radius
        edge_y = self.tower.y + self.dir_y * self.tower_radius
        
        # Interpolate between initial position and tower edge
        target_x = self.initial_enemy_x - (self.initial_enemy_x - edge_x) * self.pull_progress
        target_y = self.initial_enemy_y - (self.initial_enemy_y - edge_y) * self.pull_progress
        
        # Update enemy position
        self.target_enemy.x = target_x
        self.target_enemy.y = target_y
        
        # Check if pull is complete
        if self.pull_progress >= 1.0:
            # Apply stun effect after pull completes
            stun_duration = 0.2  # 0.2 seconds of stun
            self.target_enemy.apply_status_effect('stun', stun_duration, True, current_time)
            
            # Release the enemy
            self.is_active = False
            if self in self.target_enemy.active_harpoons:
                self.target_enemy.active_harpoons.remove(self)
            return True
            
        return False
        
    def move(self, time_delta, all_enemies):
        """
        Move the harpoon projectile. For harpoons, this just updates the pull effect.
        
        Args:
            time_delta: Time since last update
            all_enemies: List of all enemies (not used for harpoons)
            
        Returns:
            True if the harpoon should be removed, False otherwise
        """
        return self.update(time_delta, pygame.time.get_ticks() / 1000.0)
        
    def draw(self, screen, projectile_assets, grid_offset_x=0, grid_offset_y=0):
        """
        Draw the harpoon projectile and its chain.
        
        Args:
            screen: Pygame screen surface
            projectile_assets: ProjectileAssets instance
            grid_offset_x: X offset for drawing
            grid_offset_y: Y offset for drawing
        """
        if not self.is_active:
            return
            
        # Draw harpoon head
        harpoon_image = projectile_assets.get_projectile_image("harpoon")
        if harpoon_image:
            # Calculate angle for harpoon head
            angle = math.degrees(math.atan2(-self.dir_y, self.dir_x)) - 90
            rotated_image = pygame.transform.rotate(harpoon_image, angle)
            rect = rotated_image.get_rect(center=(self.target_enemy.x + grid_offset_x, self.target_enemy.y + grid_offset_y))
            screen.blit(rotated_image, rect)
            
        # Draw chain with fade effect
        chain_color = (200, 200, 200, self.chain_alpha)  # Light gray with alpha
        chain_width = 2
        start_pos = (self.tower.x + grid_offset_x, self.tower.y + grid_offset_y)
        end_pos = (self.target_enemy.x + grid_offset_x, self.target_enemy.y + grid_offset_y)
        
        # Create a surface for the chain with alpha
        chain_surface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
        pygame.draw.line(chain_surface, chain_color, start_pos, end_pos, chain_width)
        screen.blit(chain_surface, (0, 0))
        
        # Draw pull effect circle
        if self.pull_effect_radius > 0:
            effect_surface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
            effect_color = (255, 255, 255, int(100 * (1 - self.pull_progress)))
            pygame.draw.circle(effect_surface, effect_color, 
                             (int(self.target_enemy.x + grid_offset_x), int(self.target_enemy.y + grid_offset_y)),
                             int(self.pull_effect_radius))
            screen.blit(effect_surface, (0, 0)) 