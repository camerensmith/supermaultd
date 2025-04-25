class StrategicStrikeEffect:
    """Handles the strategic strike targeting behavior for towers."""
    def __init__(self, tower):
        """
        Initialize the strategic strike effect.
        
        Args:
            tower: The tower that has this effect
        """
        self.tower = tower
        
    def find_optimal_target(self, enemies):
        """
        Find the enemy with the highest current health within range.
        
        Args:
            enemies: List of potential target enemies
            
        Returns:
            The enemy with highest health, or None if no valid targets
        """
        if not enemies:
            return None
            
        # Filter enemies in range
        in_range_enemies = [
            enemy for enemy in enemies 
            if enemy.health > 0 and self.tower.is_in_range(enemy.x, enemy.y)
        ]
        
        if not in_range_enemies:
            return None
            
        # Find enemy with highest current health
        return max(in_range_enemies, key=lambda e: e.health) 