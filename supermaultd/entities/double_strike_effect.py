import pygame
import random
from .effect import PulseImageEffect
from config import GRID_SIZE

class DoubleStrikeEffect:
    """Handles the double strike special ability for towers."""
    def __init__(self, tower, target, damage, current_time):
        """
        Initialize the double strike effect.
        
        Args:
            tower: The tower that triggered the effect
            target: The enemy being attacked
            damage: The base damage of the attack
            current_time: Current game time
        """
        self.tower = tower
        self.target = target
        self.damage = damage
        self.current_time = current_time
        self.strike_count = 0
        self.max_strikes = 2
        self.strike_interval = 0.1  # Time between strikes in seconds
        self.next_strike_time = current_time + self.strike_interval
        self.finished = False
        
    def update(self, current_time):
        """
        Update the double strike effect.
        
        Args:
            current_time: Current game time
            
        Returns:
            bool: True if effect is finished, False otherwise
        """
        if self.finished:
            return True
            
        if current_time >= self.next_strike_time and self.strike_count < self.max_strikes:
            # Apply damage
            self.target.take_damage(self.damage, self.tower.damage_type)
            print(f"Double Strike {self.strike_count + 1} hit {self.target.enemy_id} for {self.damage} damage")
            
            # Create visual effect
            if self.tower.game_scene_add_effect_callback:
                effect = PulseImageEffect(
                    self.target.x,
                    self.target.y,
                    self.tower.attack_effect_image,
                    duration=0.2,
                    start_scale=0.8,
                    end_scale=1.5
                )
                self.tower.game_scene_add_effect_callback(effect)
            
            self.strike_count += 1
            self.next_strike_time = current_time + self.strike_interval
            
        if self.strike_count >= self.max_strikes:
            self.finished = True
            
        return self.finished 