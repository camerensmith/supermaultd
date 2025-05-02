import pygame
from config import GRID_SIZE

class StatusEffectVisualizer:
    """Displays a visual effect over a tower when a specific status is active."""

    def __init__(self, tower, effect_type, color=(255, 0, 0, 100)):
        """
        Initialize the visualizer.

        :param tower: The Tower instance this visualizer is attached to.
        :param effect_type: The string identifier of the effect to monitor (e.g., 'berserk').
        :param color: The RGBA color tuple for the visual overlay.
        """
        self.tower = tower
        self.effect_type = effect_type
        self.color = color
        self.is_active = False # Track if the visual should be drawn

        # Pre-calculate tower pixel dimensions (assuming tower object has these)
        self.width_pixels = getattr(tower, 'width_pixels', GRID_SIZE * getattr(tower, 'grid_width', 1))
        self.height_pixels = getattr(tower, 'height_pixels', GRID_SIZE * getattr(tower, 'grid_height', 1))

    def update(self, current_time):
        """
        Update the active state based on the linked tower's status.
        Needs current_time if checking timed effects directly.
        """
        if self.effect_type == 'berserk':
            # Check the tower's specific flag for berserk
            self.is_active = getattr(self.tower, 'is_berserk', False)
        # Add other effect_type checks here later if needed
        # E.g., elif self.effect_type == 'some_other_effect':
        #          self.is_active = getattr(self.tower, 'some_other_flag', False)
        
        # This visualizer doesn't 'finish' on its own, it mirrors the tower state.
        # No need to return True/False like a standard Effect.

    def draw(self, screen, offset_x, offset_y):
        """Draw the visual effect if active."""
        if not self.is_active:
            return

        try:
            # Calculate draw position (top-left corner of the tower)
            draw_pixel_x = (self.tower.top_left_grid_x * GRID_SIZE) + offset_x
            draw_pixel_y = (self.tower.top_left_grid_y * GRID_SIZE) + offset_y

            # Create a temporary surface for the overlay with alpha
            overlay_surface = pygame.Surface((self.width_pixels, self.height_pixels), pygame.SRCALPHA)
            overlay_surface.fill(self.color) # Fill with the specified RGBA color

            # Blit the overlay onto the main screen
            screen.blit(overlay_surface, (draw_pixel_x, draw_pixel_y))

        except AttributeError as e:
            # Handle cases where the tower might be missing expected attributes (e.g., if sold mid-frame)
            # print(f"Error drawing StatusEffectVisualizer for tower {getattr(self.tower, 'tower_id', 'UNKNOWN')}: {e}")
            self.is_active = False # Stop trying to draw if tower data is bad
        except Exception as e:
            # Catch other potential drawing errors
            # print(f"Unexpected error drawing StatusEffectVisualizer: {e}")
            self.is_active = False 