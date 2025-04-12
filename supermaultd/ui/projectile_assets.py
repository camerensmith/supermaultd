#!/usr/bin/env python
# coding=utf-8
import pygame
import os
from config import *

class ProjectileAssets:
    def __init__(self, base_path="assets/images/projectiles"):
        self.base_path = base_path
        self.projectile_images = {}
        print(f"Initializing ProjectileAssets from: {self.base_path}")

    def _load_image(self, projectile_id):
        """Loads a projectile image, scales it down if larger than GRID_SIZE, handles errors."""
        image_path = os.path.join(self.base_path, f"{projectile_id}.png")
        # --- DEBUG PRINT --- 
        print(f"DEBUG: Attempting to load projectile image from: {image_path}") 
        # -------------------
        try:
            image = pygame.image.load(image_path).convert_alpha()
            original_width, original_height = image.get_size()
            
            # Check if scaling down is needed
            if original_width > GRID_SIZE or original_height > GRID_SIZE:
                print(f"  Scaling down projectile image: {image_path} from {original_width}x{original_height} to {GRID_SIZE}x{GRID_SIZE}")
                scaled_image = pygame.transform.scale(image, (GRID_SIZE, GRID_SIZE))
                return scaled_image # Return the scaled-down image
            else:
                # Image is already small enough or equal, use original
                print(f"  Successfully loaded projectile image (no scaling needed): {image_path}")
                return image # Return the original image
                
        except pygame.error as e:
            print(f"Error loading projectile image '{image_path}': {e}")
            # Return a placeholder surface (e.g., a small colored square) if loading fails
            placeholder = pygame.Surface((10, 10))
            placeholder.fill(RED) # Use RED for error placeholder
            return placeholder

    def get_projectile_image(self, projectile_id):
        """Gets the image for a projectile ID, loading if necessary."""
        if projectile_id not in self.projectile_images:
            self.projectile_images[projectile_id] = self._load_image(projectile_id)
        return self.projectile_images[projectile_id]

    def draw_projectile(self, screen, projectile_id, x, y):
        """Draws the specified projectile image centered at (x, y)."""
        print(f"  ProjectileAssets drawing: {projectile_id}") # DEBUG PRINT
        image = self.get_projectile_image(projectile_id)
        rect = image.get_rect(center=(int(x), int(y)))
        screen.blit(image, rect)
 