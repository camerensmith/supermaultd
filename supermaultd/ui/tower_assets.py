import os
import pygame
from config import GRID_SIZE

class TowerAssets:
    def __init__(self):
        """Initialize the tower assets manager"""
        self.original_images = {}
        self.previews = {}
        self.aura_visuals = {}
        self.overlay_visuals = {}
        self.default_image = self._create_default_image()
        # Add dictionary for general effect images
        self.effect_images = {}
        self.load_tower_images()
        self.load_aura_visuals()
        self.load_overlay_visuals()
        # Call the new loader
        self.load_effect_images()
        
    def _create_default_image(self):
        """Create a reusable default image."""
        image = pygame.Surface((GRID_SIZE, GRID_SIZE))
        image.fill((100, 100, 100))  # Gray color for default
        return image

    def load_tower_images(self):
        """Load all tower images from the assets directory"""
        assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'towers')
        if not os.path.exists(assets_dir):
            print(f"Warning: Assets directory not found: {assets_dir}")
            return
            
        for filename in os.listdir(assets_dir):
            if filename.lower().endswith(('.png', '.jpg')):
                tower_id = os.path.splitext(filename)[0]
                try:
                    image_path = os.path.join(assets_dir, filename)
                    # Load original image
                    original_image = pygame.image.load(image_path).convert_alpha()
                    self.original_images[tower_id] = original_image
                    
                    # Create preview (scaled to single grid size, transparent)
                    preview_scaled = pygame.transform.scale(original_image, (GRID_SIZE, GRID_SIZE))
                    preview_scaled.set_alpha(128) # 50% transparency
                    self.previews[tower_id] = preview_scaled
                    
                    print(f"Loaded tower image: {tower_id}")
                except Exception as e:
                    print(f"Error loading tower image {filename}: {e}")
                    self.original_images[tower_id] = self.default_image
                    # Make default preview transparent
                    default_preview = self.default_image.copy()
                    default_preview.set_alpha(128)
                    self.previews[tower_id] = default_preview
                    
    def load_aura_visuals(self):
        """Load images used for persistent aura visual effects."""
        effects_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'effects')
        aura_map = {
            "alchemist_miasma_pillar": "miasma.png", # Tower ID maps to effect image
            "spark_storm_generator": "storm_effect.png", # Add mapping for storm generator
            # Add other towers/aura visuals here
        }

        for tower_id, filename in aura_map.items():
            path = os.path.join(effects_dir, filename)
            if not os.path.isfile(path):
                print(f"Warning: Aura visual image not found: {path}")
                continue
            try:
                image = pygame.image.load(path).convert_alpha()
                self.aura_visuals[tower_id] = image
                print(f"Loaded aura visual for '{tower_id}': {filename}")
            except Exception as e:
                print(f"Error loading aura visual image {filename}: {e}")

    def load_overlay_visuals(self):
        """Load images used for persistent overlay visual effects."""
        effects_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'effects')
        overlay_map = {
            "alien_black_hole_generator": "black_hole.png", # Update Tower ID
            "pyro_flame_dancer": "flame_ring.png", # Added flame dancer mapping
            "goblin_shredder": "buzzsaw.png", # Added shredder mapping
            # Add other towers/overlay visuals here
        }

        for tower_id, filename in overlay_map.items():
            path = os.path.join(effects_dir, filename)
            if not os.path.isfile(path):
                print(f"Warning: Overlay visual image not found: {path}")
                continue
            try:
                image = pygame.image.load(path).convert_alpha()
                self.overlay_visuals[tower_id] = image
                print(f"Loaded overlay visual for '{tower_id}': {filename}")
            except Exception as e:
                print(f"Error loading overlay visual image {filename}: {e}")

    def load_effect_images(self):
        """Load general effect images from the assets/effects directory."""
        effects_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'effects')
        if not os.path.exists(effects_dir):
            print(f"Warning: Effects directory not found: {effects_dir}")
            return
            
        print(f"Loading general effect images from: {effects_dir}")
        loaded_count = 0
        for filename in os.listdir(effects_dir):
            if filename.lower().endswith(('.png', '.jpg')):
                effect_name = os.path.splitext(filename)[0]
                # Skip images already loaded as aura/overlay visuals to avoid duplication if needed?
                # Or maybe allow overlap? For now, load all.
                try:
                    image_path = os.path.join(effects_dir, filename)
                    image = pygame.image.load(image_path).convert_alpha()
                    self.effect_images[effect_name] = image
                    loaded_count += 1
                    # print(f"  Loaded effect: {effect_name}") # Optional: Verbose logging
                except Exception as e:
                    print(f"Error loading effect image {filename}: {e}")
        print(f"Finished loading {loaded_count} general effect images.")

    def get_tower_image(self, tower_id):
        """Get the ORIGINAL (unscaled) image for a specific tower."""
        return self.original_images.get(tower_id, self.default_image)
        
    def get_tower_preview(self, tower_id):
        """Get the preview image (scaled to GRID_SIZE, transparent)."""
        return self.previews.get(tower_id)
        
    def get_aura_visual(self, tower_id):
        """Get the pre-loaded visual for a tower's aura effect."""
        return self.aura_visuals.get(tower_id)

    def get_overlay_visual(self, tower_id):
        """Get the pre-loaded visual for a tower's overlay effect."""
        return self.overlay_visuals.get(tower_id)

    # --- New Getter for General Effect Images ---
    def get_effect_image(self, effect_name):
        """Get a pre-loaded general effect image by its filename (without extension)."""
        return self.effect_images.get(effect_name)
    # --- End New Getter ---

    def draw_tower(self, surface, tower_id, x, y, width=None, height=None, is_preview=False):
        """Draw a tower at the specified pixel position, optionally scaling it."""
        if is_preview:
            image = self.get_tower_preview(tower_id)
            # Preview is already scaled to GRID_SIZE and transparent
            if image:
                surface.blit(image, (x, y))
        else:
            image = self.get_tower_image(tower_id)
            if image:
                # Scale the original image if width/height are provided
                draw_width = width if width is not None else image.get_width()
                draw_height = height if height is not None else image.get_height()
                if draw_width != image.get_width() or draw_height != image.get_height():
                    scaled_image = pygame.transform.scale(image, (draw_width, draw_height))
                    surface.blit(scaled_image, (x, y))
                else:
                    surface.blit(image, (x, y)) # Blit original if no scaling needed 