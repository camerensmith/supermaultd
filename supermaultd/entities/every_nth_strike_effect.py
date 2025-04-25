import pygame
from config import GRID_SIZE
from .effect import PulseImageEffect

class EveryNthStrikeEffect:
    """Handles the every_nth_strike special ability for towers."""
    def __init__(self, tower, target, bonus_damage, current_time):
        """
        Initialize the every_nth_strike effect.
        
        Args:
            tower: The tower that triggered the effect
            target: The enemy being attacked
            bonus_damage: The additional damage to apply
            current_time: Current game time
        """
        self.tower = tower
        self.target = target
        self.bonus_damage = bonus_damage
        self.current_time = current_time
        self.finished = False
        
    def update(self, current_time):
        """
        Update the every_nth_strike effect.
        
        Args:
            current_time: Current game time
            
        Returns:
            bool: True if effect is finished, False otherwise
        """
        if self.finished:
            return True
            
        # Apply bonus damage
        self.target.take_damage(self.bonus_damage, self.tower.damage_type)
        print(f"Every Nth Strike bonus hit {self.target.enemy_id} for {self.bonus_damage} bonus damage")
        
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
        
        self.finished = True
        return self.finished 