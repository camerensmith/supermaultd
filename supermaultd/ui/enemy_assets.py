import pygame
import os
from config import ENEMY_IMAGES_DIR, GRID_SIZE

class EnemyAssets:
    def __init__(self):
        self.images = {}
        self.dot_effect_visuals = {} # Dictionary for DoT effect visuals
        self.status_overlay_images = {} # NEW: Dictionary for status overlays
        self.load_enemy_images()
        self.load_dot_effect_images() # Call new method
        self.load_status_overlay_images() # NEW: Call overlay loader

    def load_enemy_images(self):
        """Load all enemy images from the specified directory."""
        if not os.path.exists(ENEMY_IMAGES_DIR):
            print(f"Warning: Enemy images directory not found: {ENEMY_IMAGES_DIR}")
            return

        for filename in os.listdir(ENEMY_IMAGES_DIR):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                enemy_id = os.path.splitext(filename)[0] # Use filename without extension as ID
                path = os.path.join(ENEMY_IMAGES_DIR, filename)
                try:
                    image = pygame.image.load(path).convert_alpha()
                    # Scale image to fit within a grid cell by default
                    scaled_image = pygame.transform.scale(image, (GRID_SIZE, GRID_SIZE))
                    self.images[enemy_id] = scaled_image
                    print(f"Loaded enemy image: {enemy_id}")
                except pygame.error as e:
                    print(f"Error loading enemy image {filename}: {e}")

    def load_dot_effect_images(self):
        """Load images associated with specific DoT effects."""
        effects_dir = "assets/effects"
        dot_map = {
            "spore_dot": "purple_smoke.png"  # Map effect name to image filename
            # Add other DoT effect visuals here
        }

        for effect_name, filename in dot_map.items():
            path = os.path.join(effects_dir, filename)
            if not os.path.isfile(path):
                print(f"Warning: DoT effect image not found: {path}")
                continue
            try:
                image = pygame.image.load(path).convert_alpha()
                # Maybe scale the effect image slightly smaller than grid size?
                # scaled_image = pygame.transform.smoothscale(image, (int(GRID_SIZE * 0.8), int(GRID_SIZE * 0.8)))
                self.dot_effect_visuals[effect_name] = image # Store original for now
                print(f"Loaded DoT effect visual for '{effect_name}': {filename}")
            except pygame.error as e:
                print(f"Error loading DoT effect image {filename}: {e}")

    # --- NEW: Load Status Effect Overlay Images --- 
    def load_status_overlay_images(self):
        """Load images used as overlays for status effects."""
        effects_dir = "assets/effects"
        # Map status effect name (key) to image filename (value)
        overlay_map = {
            "bonechill": "igloo_glacial_heart.png" 
            # Add other status overlays here, e.g.:
            # "burning": "fire_overlay.png"
        }

        print("Loading status effect overlay images...")
        for status_name, filename in overlay_map.items():
            path = os.path.join(effects_dir, filename)
            if not os.path.isfile(path):
                print(f"Warning: Status overlay image not found: {path}")
                continue
            try:
                image = pygame.image.load(path).convert_alpha()
                # Optional: Scale overlay image if needed (e.g., to match GRID_SIZE)
                scaled_image = pygame.transform.smoothscale(image, (GRID_SIZE, GRID_SIZE))
                self.status_overlay_images[status_name] = scaled_image # Store scaled image
                print(f"  Loaded and scaled overlay for '{status_name}': {filename}")
            except pygame.error as e:
                print(f"Error loading status overlay image {filename}: {e}")
    # --- End Status Overlay Loading ---

    def get_image(self, enemy_id):
        """Get the pre-loaded image for a specific enemy ID."""
        return self.images.get(enemy_id)

    # --- NEW: Get Status Overlay Image --- 
    def get_status_overlay_image(self, status_name):
        """Get the pre-loaded overlay image for a specific status effect."""
        return self.status_overlay_images.get(status_name)
    # --- End Get Overlay ---

    def draw_enemy(self, screen, enemy_id, x, y, width=None, height=None):
        """Draw a specific enemy image at the given coordinates."""
        image = self.get_image(enemy_id)
        if image:
            draw_width = width if width is not None else image.get_width()
            draw_height = height if height is not None else image.get_height()
            
            # If custom dimensions provided, scale the original image (might need optimization)
            if width is not None or height is not None:
                 # Re-fetch original if needed or store originals separately - for now, re-scale default
                 temp_image = pygame.transform.scale(image, (draw_width, draw_height)) 
            else:
                temp_image = image # Use the pre-scaled image

            # Calculate top-left corner for centering the image
            rect = temp_image.get_rect(center=(int(x), int(y)))
            screen.blit(temp_image, rect.topleft)
        else:
            # Fallback: Draw a simple circle if image not found
            pygame.draw.circle(screen, (255, 0, 0), (int(x), int(y)), GRID_SIZE // 2)
            print(f"Warning: Image not found for enemy_id '{enemy_id}'. Drawing fallback.") 