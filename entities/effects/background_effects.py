#!/usr/bin/env python3
"""
Background effects for SupermaulTD - Tessellation and other cool visual effects.
"""

import pygame
import math
import random
from typing import List, Tuple

class TessellationEffect:
    """Creates a rotating tessellation pattern background effect."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rotation_angle = 0
        self.rotation_speed = 0.005  # Much slower rotation - degrees per frame
        self.tile_size = 80  # Larger tiles for more visible pattern
        
        # Define color schemes for different game modes
        self.color_schemes = {
            "classic": [
                (100, 150, 200),  # Icy light blue
                (80, 130, 180),   # Medium icy blue
                (60, 110, 160),   # Darker icy blue
                (40, 90, 140),    # Dark blue
            ],
            "advanced": [
                (120, 40, 40),   # Dark red
                (150, 50, 50),   # Red
                (100, 30, 30),   # Darker red
                (180, 60, 60),   # Bright red
            ],
            "wild": [
                (120, 120, 40),  # Dark yellow
                (150, 150, 50),  # Yellow
                (100, 100, 30),  # Darker yellow
                (180, 180, 60),  # Bright yellow
            ]
        }
        
        # Start with classic colors
        self.colors = self.color_schemes["classic"]
    
    def set_color_scheme(self, scheme_name: str):
        """Change the color scheme based on game mode."""
        if scheme_name in self.color_schemes:
            self.colors = self.color_schemes[scheme_name]
            print(f"[TessellationEffect] Switched to {scheme_name} color scheme")
        else:
            print(f"[TessellationEffect] Unknown color scheme: {scheme_name}")
        
    def draw_triangle(self, surface: pygame.Surface, points: List[Tuple[int, int]], color: Tuple[int, int, int]):
        """Draw a triangle with the given points and color."""
        pygame.draw.polygon(surface, color, points)
        # Add a subtle border
        pygame.draw.polygon(surface, (color[0] + 20, color[1] + 20, color[2] + 20), points, 1)
    
    def draw_tessellation(self, surface: pygame.Surface):
        """Draw the tessellation pattern."""
        # Clear the surface
        surface.fill((10, 10, 25))  # Very dark background
        
        # Calculate how many tiles we need to cover the screen
        cols = int(self.screen_width / self.tile_size) + 2
        rows = int(self.screen_height / self.tile_size) + 2
        
        # Create a temporary surface for rotation
        temp_surface = pygame.Surface((self.screen_width + self.tile_size * 2, 
                                     self.screen_height + self.tile_size * 2))
        temp_surface.set_colorkey((0, 0, 0))  # Make black transparent
        
        # Draw tessellation pattern
        for row in range(rows):
            for col in range(cols):
                x = col * self.tile_size
                y = row * self.tile_size
                
                # Create triangular tessellation
                center_x = x + self.tile_size // 2
                center_y = y + self.tile_size // 2
                
                # Calculate rotated points
                angle_rad = math.radians(self.rotation_angle)
                cos_a = math.cos(angle_rad)
                sin_a = math.sin(angle_rad)
                
                # Triangle points (equilateral triangle)
                points = []
                for i in range(3):
                    angle = (i * 120 + self.rotation_angle) * math.pi / 180
                    px = center_x + self.tile_size * 0.4 * math.cos(angle)
                    py = center_y + self.tile_size * 0.4 * math.sin(angle)
                    points.append((int(px), int(py)))
                
                # Choose color based on position
                color_index = (row + col) % len(self.colors)
                self.draw_triangle(temp_surface, points, self.colors[color_index])
        
        # Rotate the entire pattern
        rotated_surface = pygame.transform.rotate(temp_surface, self.rotation_angle)
        
        # Blit to main surface, centered
        rect = rotated_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        surface.blit(rotated_surface, rect)
        
        # Update rotation
        self.rotation_angle += self.rotation_speed
        if self.rotation_angle >= 360:
            self.rotation_angle -= 360

class HexagonTessellation:
    """Creates a hexagonal tessellation pattern."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.rotation_angle = 80
        self.rotation_speed = 1  # Much slower rotation for hexagons
        self.hex_size = 40
        
        # Define color schemes for different game modes
        self.color_schemes = {
            "classic": [
                (25, 25, 45),   # Dark blue
                (35, 25, 55),   # Purple
                (45, 35, 65),   # Blue
                (55, 45, 75),   # Purple
            ],
            "advanced": [
                (45, 15, 15),   # Dark red
                (55, 20, 20),   # Red
                (35, 10, 10),   # Darker red
                (65, 25, 25),   # Bright red
            ],
            "wild": [
                (45, 45, 15),   # Dark yellow
                (55, 55, 20),   # Yellow
                (35, 35, 10),   # Darker yellow
                (65, 65, 25),   # Bright yellow
            ]
        }
        
        # Start with classic colors
        self.colors = self.color_schemes["classic"]
    
    def set_color_scheme(self, scheme_name: str):
        """Change the color scheme based on game mode."""
        if scheme_name in self.color_schemes:
            self.colors = self.color_schemes[scheme_name]
            print(f"[HexagonTessellation] Switched to {scheme_name} color scheme")
        else:
            print(f"[HexagonTessellation] Unknown color scheme: {scheme_name}")
    
    def draw_hexagon(self, surface: pygame.Surface, center: Tuple[int, int], size: int, color: Tuple[int, int, int]):
        """Draw a hexagon at the given center point."""
        points = []
        for i in range(6):
            angle = (i * 60 + self.rotation_angle) * math.pi / 180
            x = center[0] + size * math.cos(angle)
            y = center[1] + size * math.sin(angle)
            points.append((int(x), int(y)))
        
        pygame.draw.polygon(surface, color, points)
        # Add subtle border
        pygame.draw.polygon(surface, (color[0] + 15, color[1] + 15, color[2] + 15), points, 1)
    
    def draw_tessellation(self, surface: pygame.Surface):
        """Draw the hexagonal tessellation."""
        surface.fill((15, 15, 35))
        
        # Calculate hexagon spacing
        hex_width = int(self.hex_size * math.sqrt(3))
        hex_height = int(self.hex_size * 2)
        
        cols = int(self.screen_width / hex_width) + 2
        rows = int(self.screen_height / hex_height) + 2
        
        for row in range(rows):
            for col in range(cols):
                x = col * hex_width
                y = row * hex_height
                
                # Offset every other row
                if row % 2 == 1:
                    x += hex_width // 2
                
                center = (x, y)
                color_index = (row + col) % len(self.colors)
                self.draw_hexagon(surface, center, self.hex_size, self.colors[color_index])
        
        self.rotation_angle += self.rotation_speed
        if self.rotation_angle >= 360:
            self.rotation_angle -= 360

class ParticleField:
    """Creates a subtle particle field effect."""
    
    def __init__(self, screen_width: int, screen_height: int, num_particles: int = 100):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.particles = []
        
        # Define color schemes for different game modes
        self.color_schemes = {
            "classic": [
                (100, 100, 150),
                (120, 100, 160),
                (80, 120, 180),
                (140, 80, 200),
            ],
            "advanced": [
                (150, 80, 80),
                (180, 100, 100),
                (120, 60, 60),
                (200, 120, 120),
            ],
            "wild": [
                (150, 150, 80),
                (180, 180, 100),
                (120, 120, 60),
                (200, 200, 120),
            ]
        }
        
        # Start with classic colors
        self.current_scheme = "classic"
        
        # Create particles
        for _ in range(num_particles):
            particle = {
                'x': random.randint(0, screen_width),
                'y': random.randint(0, screen_height),
                'vx': random.uniform(-0.5, 0.5),
                'vy': random.uniform(-0.5, 0.5),
                'size': random.randint(1, 3),
                'alpha': random.randint(50, 150),
                'color': random.choice(self.color_schemes["classic"])
            }
            self.particles.append(particle)
    
    def set_color_scheme(self, scheme_name: str):
        """Change the color scheme based on game mode."""
        if scheme_name in self.color_schemes:
            self.current_scheme = scheme_name
            # Update all existing particles with new colors
            for particle in self.particles:
                particle['color'] = random.choice(self.color_schemes[scheme_name])
            print(f"[ParticleField] Switched to {scheme_name} color scheme")
        else:
            print(f"[ParticleField] Unknown color scheme: {scheme_name}")
    
    def draw_particles(self, surface: pygame.Surface):
        """Draw the particle field."""
        for particle in self.particles:
            # Create a surface for this particle with alpha
            particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2))
            particle_surface.set_alpha(particle['alpha'])
            particle_surface.fill(particle['color'])
            
            # Draw the particle
            surface.blit(particle_surface, 
                        (particle['x'] - particle['size'], 
                         particle['y'] - particle['size']))
            
            # Update position
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            
            # Wrap around screen
            if particle['x'] < 0:
                particle['x'] = self.screen_width
            elif particle['x'] > self.screen_width:
                particle['x'] = 0
                
            if particle['y'] < 0:
                particle['y'] = self.screen_height
            elif particle['y'] > self.screen_height:
                particle['y'] = 0

class BackgroundManager:
    """Manages different background effects."""
    
    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.current_effect = "tessellation"
        
        # Create effect instances
        self.effects = {
            "tessellation": TessellationEffect(screen_width, screen_height),
            "hexagon": HexagonTessellation(screen_width, screen_height),
            "particles": ParticleField(screen_width, screen_height),
        }
        
        # Create background surface
        self.background_surface = pygame.Surface((screen_width, screen_height))
    
    def set_effect(self, effect_name: str):
        """Switch to a different background effect."""
        if effect_name in self.effects:
            self.current_effect = effect_name
            print(f"[BackgroundManager] Switched to {effect_name} effect")
    
    def set_color_scheme(self, scheme_name: str):
        """Change the color scheme for all effects."""
        for effect_name, effect in self.effects.items():
            if hasattr(effect, 'set_color_scheme'):
                effect.set_color_scheme(scheme_name)
        print(f"[BackgroundManager] Updated color scheme to {scheme_name} for all effects")
    
    def update(self):
        """Update the background effect."""
        # Clear background
        self.background_surface.fill((20, 20, 40))
        
        # Draw current effect
        if self.current_effect == "tessellation":
            self.effects["tessellation"].draw_tessellation(self.background_surface)
        elif self.current_effect == "hexagon":
            self.effects["hexagon"].draw_tessellation(self.background_surface)
        elif self.current_effect == "particles":
            self.effects["particles"].draw_particles(self.background_surface)
    
    def draw(self, surface: pygame.Surface):
        """Draw the background to the main surface."""
        surface.blit(self.background_surface, (0, 0))
    
    def get_available_effects(self):
        """Get list of available effects."""
        return list(self.effects.keys())
