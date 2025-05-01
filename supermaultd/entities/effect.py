import pygame
from math import sin, pi # Import sin and pi for fade-in/out
import random # Needed for particle randomization
from config import * # Import everything from config, including color constants like ORANGE
import config # Explicitly import config module

class Effect:
    """A simple class for displaying temporary effects with alpha fading and fixed size."""
    def __init__(self, x, y, base_image, duration, target_size, fade_type='fade_out', hold_duration=0.0):
        """
        Initialize the effect.

        :param x: Center X position for the effect (absolute screen coordinates).
        :param y: Center Y position for the effect (absolute screen coordinates).
        :param base_image: The Pygame surface to display and fade.
        :param duration: Total duration (in seconds) the effect should last (includes hold + fade).
        :param target_size: Tuple (width, height) for the desired effect display size.
        :param fade_type: 'fade_out' or 'fade_in_out'
        :param hold_duration: Duration (in seconds) to keep the effect fully visible before starting fade.
        """
        if not base_image:
            print("Warning: Effect created with no base image.")
            self.finished = True
            self.image = None
            self.rect = None
            return
            
        # Scale the base image to the target size for this effect instance
        try:
            # Use smoothscale for better quality if scaling down significantly
            self.image = pygame.transform.smoothscale(base_image, target_size).convert_alpha()
        except ValueError: # Handle potential zero dimensions in target_size
             print(f"Warning: Invalid target_size {target_size} for Effect. Using original size.")
             self.image = base_image.copy().convert_alpha()

        # --- DEBUG START ---
        # if self.image:
        #     print(f"DEBUG Effect init [Post-Scale]: Scaled image size={self.image.get_size()}, alpha enabled? {self.image.get_alpha() is not None}")
        # else:
        #     print("DEBUG Effect init [Post-Scale]: self.image is None")
        # --- DEBUG END ---

        # self.base_image = base_image # Store original (Optional, no longer strictly needed unless we reuse)
        # self.image = self.base_image.copy() # Work with a copy (Now happens during scaling)
        self.rect = self.image.get_rect(center=(int(x), int(y)))
        self.duration = max(0.01, duration)
        self.hold_duration = max(0, hold_duration)
        # Ensure total duration is at least the hold duration
        self.duration = max(self.duration, self.hold_duration)
        self.fade_duration = self.duration - self.hold_duration
        self.timer = 0.0
        self.fade_type = fade_type
        self.finished = False
        self.current_alpha = 255 if fade_type == 'fade_out' else 0
        self.image.set_alpha(self.current_alpha)
        
        # --- DEBUG START ---
        # print(f"DEBUG Effect init [End]: Rect={self.rect}, Initial Alpha={self.current_alpha}, Duration={self.duration}")
        # --- DEBUG END ---

    def update(self, time_delta):
        """
        Update the effect's timer and alpha based on time.

        :param time_delta: Time elapsed since the last frame in seconds.
        :return: True if the effect has finished, False otherwise.
        """
        if self.finished:
            return True
            
        self.timer += time_delta
        
        if self.timer >= self.duration:
            self.finished = True
            self.current_alpha = 0
        else:
            # --- Hold Phase --- 
            if self.timer < self.hold_duration:
                self.current_alpha = 255
            # --- Fade Phase --- 
            else:
                # Calculate progress within the fade duration only
                fade_progress = (self.timer - self.hold_duration) / max(0.01, self.fade_duration) # Avoid div by zero

                if self.fade_type == 'fade_in_out':
                    # Sine fade in/out adjusted for hold time (Might need rethinking if fade_in_out needed)
                    # For now, let's assume fade_in_out also just fades out after hold
                    alpha_multiplier = 1.0 - fade_progress
                    # alpha_multiplier = sin(fade_progress * pi) # This would fade in THEN out after hold
                    self.current_alpha = int(255 * alpha_multiplier)
                else: # Default to fade_out
                    # Linear fade out (1 -> 0)
                    alpha_multiplier = 1.0 - fade_progress
                    self.current_alpha = int(255 * alpha_multiplier)

            # Clamp alpha just in case
            self.current_alpha = max(0, min(255, self.current_alpha))
                
        # Apply alpha to the image copy
        self.image.set_alpha(self.current_alpha)
                
        return self.finished

    def draw(self, screen):
        """Draw the current animation frame."""
        if not self.finished and self.image:
            screen.blit(self.image, self.rect)

class ChainLightningVisual(Effect):
    """Visual effect for chain lightning, drawing lines between points."""
    def __init__(self, path_coords, duration=0.3, color=None, thickness=3, line_type='standard'):
        """
        Initialize the chain lightning visual.
        
        :param path_coords: List of (x, y) tuples representing the chain path (absolute screen coords).
        :param duration: How long the visual effect lasts in seconds.
        :param color: The color of the lightning bolts. If None, uses default based on type.
        :param thickness: The thickness of the lightning lines.
        :param line_type: 'standard' (enemy bounce) or 'tower_link' (tower chain connection).
        """
        self.path_coords = path_coords
        self.duration = max(0.01, duration)
        self.timer = 0.0
        self.finished = False
        self.line_type = line_type

        # Determine default color/thickness based on type if not provided
        if color is None:
            if self.line_type == 'tower_link':
                self.color = (200, 220, 255) # Light blue/white for tower links
                self.thickness = 2 # Thinner for tower links
            else: # Default standard enemy chain/bounce
                self.color = (0, 220, 255) # Cyan default
                self.thickness = 3 # Standard thickness
        else:
            self.color = color # Use provided color
            self.thickness = thickness # Use provided thickness
        
        # Base Effect attributes needed for loop compatibility
        self.image = None 
        self.rect = None 
        
        #print(f"ChainLightningVisual created ({self.line_type}). Path has {len(path_coords)} points.")

    def update(self, time_delta):
        """Update the effect timer. Returns True if finished."""
        if self.finished:
            return True
            
        self.timer += time_delta
        if self.timer >= self.duration:
            self.finished = True
            
        return self.finished

    def draw(self, screen):
        """Draw the lightning segments."""
        if self.finished or len(self.path_coords) < 2:
            return
            
        alpha_multiplier = max(0, 1.0 - (self.timer / self.duration))
        current_alpha = int(255 * alpha_multiplier)
        current_color = (*self.color[:3], current_alpha) # Use self.color

        try:
            for i in range(len(self.path_coords) - 1):
                start_pos = self.path_coords[i]
                end_pos = self.path_coords[i+1]
                pygame.draw.aaline(screen, current_color, start_pos, end_pos, self.thickness) # Use self.thickness
        except Exception as e:
             print(f"Error drawing chain lightning ({self.line_type}): {e}")

class WhipVisual(Effect):
    """Visual effect for whip attacks, drawing lines between points."""
    def __init__(self, path_coords, duration=0.3, color=None, thickness=3, line_type='whip'):
        """
        Initialize the whip visual.
        
        :param path_coords: List of (x, y) tuples representing the whip path (absolute screen coords).
        :param duration: How long the visual effect lasts in seconds.
        :param color: The color of the whip lines. If None, uses default based on type.
        :param thickness: The thickness of the whip lines.
        :param line_type: Used to determine default color/thickness if not provided.
        """
        self.path_coords = path_coords
        self.duration = max(0.01, duration)
        self.timer = 0.0
        self.finished = False
        self.line_type = line_type

        # Determine default color/thickness based on type if not provided
        if color is None:
            if self.line_type == 'whip':
                self.color = SADDLE_BROWN 
                self.thickness = 3 
            else: # Fallback 
                self.color = (255, 255, 255) 
                self.thickness = 3
        else:
            self.color = color # Use provided color
            self.thickness = thickness # Use provided thickness
        
        # Base Effect attributes needed for loop compatibility
        self.image = None 
        self.rect = None 
        
        #print(f"WhipVisual created. Path has {len(path_coords)} points.")

    def update(self, time_delta):
        """Update the effect timer. Returns True if finished."""
        if self.finished:
            return True
            
        self.timer += time_delta
        if self.timer >= self.duration:
            self.finished = True
            
        return self.finished

    def draw(self, screen):
        """Draw the whip segments."""
        if self.finished or len(self.path_coords) < 2:
            return
            
        alpha_multiplier = max(0, 1.0 - (self.timer / self.duration))
        current_alpha = int(255 * alpha_multiplier)
        current_color = (*self.color[:3], current_alpha) # Use self.color

        try:
            for i in range(len(self.path_coords) - 1):
                start_pos = self.path_coords[i]
                end_pos = self.path_coords[i+1]
                # Use standard line for whip for now, can customize later
                pygame.draw.aaline(screen, current_color, start_pos, end_pos, self.thickness) # Use self.thickness 
        except Exception as e:
             print(f"Error drawing whip visual: {e}")

class FloatingTextEffect(Effect):
    """Displays text that floats upwards and fades out."""
    def __init__(self, x, y, text, duration=1.5, color=(255, 215, 0), font_size=33, rise_speed=20):
        """
        Initialize the floating text effect.

        :param x: Center X position (absolute screen coordinates).
        :param y: Initial Center Y position (absolute screen coordinates).
        :param text: The string to display.
        :param duration: How long the effect lasts in seconds.
        :param color: RGB tuple for the text color.
        :param font_size: Size of the font.
        :param rise_speed: Pixels per second the text moves upwards.
        """
        self.x = x
        self.initial_y = y
        self.current_y = y
        self.text = text
        self.duration = max(0.1, duration)
        self.color = color
        self.rise_speed = rise_speed
        self.timer = 0.0
        self.finished = False

        # Load font (Consider loading fonts centrally in GameScene/main later)
        try:
            self.font = pygame.font.Font(None, font_size)
        except Exception as e:
            print(f"Error loading font for FloatingTextEffect: {e}")
            self.font = pygame.font.Font(pygame.font.get_default_font(), font_size)
        
        self.text_surf = None # Will be rendered in draw
        self.text_rect = None
        
        # Base Effect attributes needed for loop compatibility
        self.image = None 
        self.rect = None # Will be updated in draw
        
        print(f"FloatingTextEffect created: '{text}' at ({x},{y})")

    def update(self, time_delta):
        """Update timer, position, and alpha. Returns True if finished."""
        if self.finished:
            return True
            
        self.timer += time_delta
        if self.timer >= self.duration:
            self.finished = True
            return True
            
        # Update position
        self.current_y = self.initial_y - (self.timer * self.rise_speed)
        
        return False

    def draw(self, screen):
        """Draw the floating text with fade."""
        if self.finished:
            return

        # Calculate alpha (linear fade out)
        alpha_multiplier = max(0, 1.0 - (self.timer / self.duration))
        current_alpha = int(255 * alpha_multiplier)
        
        # Render text surface with current alpha
        # Creating surface each frame might be inefficient, but handles alpha easily
        try:
             current_color_with_alpha = (*self.color[:3], current_alpha)
             self.text_surf = self.font.render(self.text, True, self.color) # Render without alpha first
             self.text_surf.set_alpha(current_alpha) # Apply alpha to the surface
             self.rect = self.text_surf.get_rect(center=(int(self.x), int(self.current_y)))
             screen.blit(self.text_surf, self.rect)
        except Exception as e:
            print(f"Error rendering/drawing FloatingTextEffect: {e}") 

# --- New Effect: Orbiting Orbs --- 
import math
import random

class OrbitingOrbsEffect(Effect):
    """Visual effect showing orbs orbiting a target enemy."""
    def __init__(self, target_enemy, duration=2.0, num_orbs=4, color=(150, 0, 200), orbit_radius=25, orbit_speed=2 * math.pi):
        """
        Initialize the orbiting orbs effect.

        :param target_enemy: The Enemy instance to orbit.
        :param duration: How long the effect lasts in seconds.
        :param num_orbs: Number of orbs (3 or 4 recommended).
        :param color: RGB tuple for the orb color (default purple).
        :param orbit_radius: Pixel radius of the orbit.
        :param orbit_speed: Radians per second the orbs travel.
        """
        self.target_enemy = target_enemy
        self.duration = max(0.1, duration)
        self.num_orbs = num_orbs
        self.color = color
        self.orbit_radius = orbit_radius
        self.orbit_speed = orbit_speed
        self.timer = 0.0
        self.finished = False
        self.orb_radius = 3 # Small radius for the orbs themselves
        
        # Initialize orb angles spread evenly
        self.orb_angles = [(i * 2 * math.pi / self.num_orbs) + random.uniform(-0.1, 0.1) for i in range(self.num_orbs)]
        
        # Base Effect attributes needed for loop compatibility
        self.image = None
        self.rect = None
        
        print(f"OrbitingOrbsEffect created for enemy {target_enemy.enemy_id}")

    def update(self, time_delta):
        """Update timer and orb angles. Returns True if finished."""
        if self.finished or self.target_enemy.health <= 0: # Stop if target dies
            self.finished = True
            return True
            
        self.timer += time_delta
        if self.timer >= self.duration:
            self.finished = True
            return True
            
        # Update angles
        for i in range(self.num_orbs):
            self.orb_angles[i] += self.orbit_speed * time_delta
            self.orb_angles[i] %= (2 * math.pi) # Keep angle within 0-2pi
        
        return False

    def draw(self, screen):
        """Draw the orbiting orbs around the target enemy."""
        if self.finished:
            return

        # Calculate alpha (fade out over the last 30% of duration)
        fade_start_time = self.duration * 0.7
        alpha_multiplier = 1.0
        if self.timer > fade_start_time:
            fade_duration = self.duration - fade_start_time
            alpha_multiplier = max(0, 1.0 - (self.timer - fade_start_time) / max(0.01, fade_duration))
        
        current_alpha = int(255 * alpha_multiplier)
        current_color_with_alpha = (*self.color[:3], current_alpha)
        

        try:
            grid_offset_x = pygame.display.get_surface().get_rect().width * 0.01 # Crude guess for padding
            grid_offset_y = pygame.display.get_surface().get_rect().height * 0.01 # Crude guess
        except AttributeError:
            grid_offset_x = 10 # Fallback
            grid_offset_y = 10
            
        center_x = self.target_enemy.x + grid_offset_x 
        center_y = self.target_enemy.y + grid_offset_y

        # Draw each orb
        temp_surface = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        for angle in self.orb_angles:
            orb_x = center_x + self.orbit_radius * math.cos(angle)
            orb_y = center_y + self.orbit_radius * math.sin(angle)
            try:
                pygame.draw.circle(temp_surface, current_color_with_alpha, (int(orb_x), int(orb_y)), self.orb_radius)
            except TypeError: # Handle cases where color might be invalid briefly
                pygame.draw.circle(temp_surface, self.color, (int(orb_x), int(orb_y)), self.orb_radius)
                
        screen.blit(temp_surface, (0, 0)) 

class DrainParticleEffect:
    """Visual effect simulating life force being drained from an enemy to a tower."""
    def __init__(self, source_tower, target_enemy, 
                 particle_rate=30, # particles per second
                 particle_life_base=0.8, # Base lifetime, will be adjusted by distance
                 particle_speed=120, 
                 start_color=(180, 0, 255), # Start color (at enemy) - Bright Purple
                 end_color=(80, 0, 120),   # End color (fade towards tower) - Dark Purple
                 start_size=4, 
                 end_size=1):
        
        self.source_tower = source_tower
        self.target_enemy = target_enemy
        self.particle_rate = particle_rate
        self.particle_life_base = particle_life_base
        self.particle_speed = particle_speed
        self.start_color = start_color
        self.end_color = end_color
        self.start_size = start_size
        self.end_size = end_size
        
        self.particles = []
        self.spawn_accumulator = 0.0
        self.is_spawning = True # Controls if new particles are generated
        self.finished = False # For removal from GameScene effects list

    def stop_spawning(self):
        """Signal the effect to stop creating new particles."""
        self.is_spawning = False

    def update(self, time_delta):
        """Update particle positions, lifetimes, and spawn new ones."""
        if self.finished:
            return True # Already finished

        # Check if target is still valid for spawning more particles
        if not self.target_enemy or self.target_enemy.health <= 0:
            self.stop_spawning() # Stop spawning if target is gone

        # --- Spawn New Particles --- 
        if self.is_spawning:
            self.spawn_accumulator += self.particle_rate * time_delta
            num_new_particles = int(self.spawn_accumulator)
            if num_new_particles > 0:
                self.spawn_accumulator -= num_new_particles
                
                # Spawn Origin: Target Enemy's position
                start_x = self.target_enemy.x
                start_y = self.target_enemy.y
                # Destination: Source Tower's position
                target_x = self.source_tower.x
                target_y = self.source_tower.y
                
                dx = target_x - start_x
                dy = target_y - start_y
                distance = max(1, math.hypot(dx, dy))
                
                # Calculate base velocity vector TOWARDS the tower
                base_vx = (dx / distance) * self.particle_speed
                base_vy = (dy / distance) * self.particle_speed
                
                # Estimate lifetime based on distance and speed
                estimated_travel_time = distance / self.particle_speed if self.particle_speed > 0 else self.particle_life_base
                particle_life = max(0.1, estimated_travel_time) # Ensure a minimum lifetime

                for _ in range(num_new_particles):
                    # Optional: Slight randomization around spawn position
                    px = start_x + random.uniform(-5, 5)
                    py = start_y + random.uniform(-5, 5)
                    
                    # Optional: Slight randomization in speed/direction (could make it look less uniform)
                    speed_mult = random.uniform(0.9, 1.1)
                    vx = base_vx * speed_mult
                    vy = base_vy * speed_mult
                    
                    # Individual particle lifetime variation
                    life = particle_life * random.uniform(0.8, 1.2)
                    
                    self.particles.append({
                        'x': px,
                        'y': py,
                        'vx': vx,
                        'vy': vy,
                        'life': life,
                        'max_life': life 
                    })
        
        # --- Update Existing Particles --- 
        active_particles = []
        for p in self.particles:
            p['x'] += p['vx'] * time_delta
            p['y'] += p['vy'] * time_delta
            p['life'] -= time_delta
            
            if p['life'] > 0:
                active_particles.append(p)
                
        self.particles = active_particles
        
        # Check if effect is finished (no more spawning AND no particles left)
        if not self.is_spawning and not self.particles:
            self.finished = True
            return True # Signal finished
            
        return False # Effect still active

    def draw(self, screen, grid_offset_x, grid_offset_y):
        """Draw all active particles."""
        if self.finished:
            return
            
        for p in self.particles:
            # Life ratio: 0 when dead, 1 when full life. We want color/size to go from start->end as life decreases.
            life_ratio = max(0, p['life'] / p['max_life']) 
            
            # Interpolate color (starts purple, fades darker)
            r = int(self.start_color[0] + (self.end_color[0] - self.start_color[0]) * (1 - life_ratio))
            g = int(self.start_color[1] + (self.end_color[1] - self.start_color[1]) * (1 - life_ratio))
            b = int(self.start_color[2] + (self.end_color[2] - self.start_color[2]) * (1 - life_ratio))
            
            # Interpolate size (starts larger, shrinks)
            current_size = int(self.start_size + (self.end_size - self.start_size) * (1 - life_ratio))
            current_alpha = int(255 * life_ratio**0.5) # Fade out slightly slower than linearly
            
            if current_alpha > 0 and current_size > 0:
                try:
                    # Draw simple circles for particles
                    pos_x = int(p['x'] + grid_offset_x)
                    pos_y = int(p['y'] + grid_offset_y)
                    
                    # Use SRCALPHA surface for better alpha blending
                    particle_surf = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
                    # Clamp color components to valid range [0, 255]
                    color = (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)), current_alpha)
                    pygame.draw.circle(particle_surf, color, (current_size, current_size), current_size)
                    screen.blit(particle_surf, (pos_x - current_size, pos_y - current_size))
                except Exception as e:
                    #print(f"Error drawing drain particle: {e}")
                    pass

class RisingFadeEffect:
    """An effect where an image scales up and fades out simultaneously."""
    def __init__(self, x, y, image, duration, start_scale=0.1, end_scale=1.0):
        self.x = x
        self.y = y
        self.original_image = image
        self.duration = max(0.01, duration) # Avoid division by zero
        self.start_scale = start_scale
        self.end_scale = end_scale
        
        self.life_remaining = self.duration
        self.original_width, self.original_height = self.original_image.get_size()

    def update(self, time_delta):
        self.life_remaining -= time_delta
        return self.life_remaining <= 0 # Return True when effect is done

    def draw(self, screen):
        if self.life_remaining <= 0:
            return

        # Calculate progress (0.0 to 1.0)
        progress = 1.0 - (self.life_remaining / self.duration)
        
        # Calculate current scale (linear interpolation)
        current_scale = self.start_scale + (self.end_scale - self.start_scale) * progress
        current_width = int(self.original_width * current_scale)
        current_height = int(self.original_height * current_scale)
        
        # Calculate current alpha (fades out linearly)
        current_alpha = int(255 * (1.0 - progress))
        
        if current_width > 0 and current_height > 0 and current_alpha > 0:
            try:
                # Scale the original image
                scaled_image = pygame.transform.smoothscale(self.original_image, (current_width, current_height))
                # Set alpha
                scaled_image.set_alpha(current_alpha)
                
                # Calculate draw position (centered)
                draw_rect = scaled_image.get_rect(center=(int(self.x), int(self.y)))
                
                # Draw
                screen.blit(scaled_image, draw_rect)
            except ValueError: # Handle potential zero size during scaling
                pass 
            except Exception as e:
                #print(f"Error drawing RisingFadeEffect: {e}") 
                pass

class GroundEffectZone:
    """A persistent circular area on the ground that applies effects to enemies within it."""
    def __init__(self, x, y, radius_units, duration, dot_damage, dot_interval, damage_type, valid_targets):
        self.x = x # Center pixel X
        self.y = y # Center pixel Y
        self.radius_pixels = radius_units * (GRID_SIZE / 200.0)
        self.radius_pixels_sq = self.radius_pixels ** 2
        self.duration = duration
        self.dot_damage = dot_damage
        self.dot_interval = max(0.01, dot_interval) # Avoid division by zero
        self.damage_type = damage_type
        self.valid_targets = valid_targets # List of target types (e.g., ["ground"])
        
        self.life_remaining = duration
        self.time_since_last_dot = 0.0
        self.effect_color = (255, 165, 0, 120) # Orange with alpha for fallout

        #print(f"[DEBUG] GroundEffectZone created at ({x}, {y}) with:")
        #print(f"  - radius: {radius_units} units = {self.radius_pixels} pixels")
        #print(f"  - duration: {duration}s")
        #print(f"  - damage: {dot_damage} {damage_type} every {dot_interval}s")
        #print(f"  - valid targets: {valid_targets}")

    def update(self, time_delta, enemies):
        """Update zone duration and apply DoT to enemies inside."""
        self.life_remaining -= time_delta
        if self.life_remaining <= 0:
            #print("[DEBUG] GroundEffectZone expired")
            return True # Effect is finished

        self.time_since_last_dot += time_delta
        apply_dot_this_frame = False
        damage_to_apply = 0

        # Check if it's time to apply damage ticks
        while self.time_since_last_dot >= self.dot_interval:
            apply_dot_this_frame = True
            damage_to_apply += self.dot_damage
            self.time_since_last_dot -= self.dot_interval

        if apply_dot_this_frame and damage_to_apply > 0:
            enemies_hit = 0
            for enemy in enemies:
                # Check if enemy is a valid target type, alive, and within radius
                if enemy.type in self.valid_targets and enemy.health > 0:
                    dist_sq = (enemy.x - self.x)**2 + (enemy.y - self.y)**2
                    if dist_sq <= self.radius_pixels_sq:
                        enemy.take_damage(damage_to_apply, self.damage_type)
                        enemies_hit += 1
                        print(f"[DEBUG] Fallout zone hit enemy at ({enemy.x}, {enemy.y}) - distance: {math.sqrt(dist_sq):.1f}px, radius: {self.radius_pixels:.1f}px")
            if enemies_hit > 0:
                #print(f"[DEBUG] Fallout zone hit {enemies_hit} enemies for {damage_to_apply} {self.damage_type} damage")
                pass
            
        return False # Effect is still active

    def draw(self, screen, grid_offset_x, grid_offset_y):
        """Draw the semi-transparent effect zone."""
        if self.life_remaining <= 0:
            return
        
        # Calculate screen position
        draw_x = int(self.x + grid_offset_x)
        draw_y = int(self.y + grid_offset_y)
        radius = int(self.radius_pixels)
        
        if radius > 0:
            try:
                # Create a temporary surface for transparency
                temp_surface = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
                # Draw a filled circle
                pygame.draw.circle(temp_surface, self.effect_color, (radius + 2, radius + 2), radius)
                # Draw an outline
                pygame.draw.circle(temp_surface, (255, 165, 0, 255), (radius + 2, radius + 2), radius, 3)
                # Blit the temporary surface to the screen
                screen.blit(temp_surface, (draw_x - radius - 2, draw_y - radius - 2))
                
                if self.life_remaining % 1.0 < 0.1:  # Print debug once per second
                    print(f"[DEBUG] Drawing fallout zone at ({draw_x}, {draw_y}) with radius {radius}px, life: {self.life_remaining:.1f}s")
            except Exception as e:
                print(f"Error drawing fallout zone: {e}")
                print(f"  - draw_x: {draw_x}, draw_y: {draw_y}")
                print(f"  - radius: {radius}")
                print(f"  - grid_offset: ({grid_offset_x}, {grid_offset_y})")

class FlamethrowerParticleEffect:
    """Continuous stream of particles from a source tower to a target enemy."""
    def __init__(self, source_tower, target_enemy, 
                 particle_rate=50, # particles per second
                 particle_life=0.6, 
                 particle_speed=150, 
                 start_color=(255, 150, 0), 
                 end_color=(100, 50, 50), 
                 start_size=5, 
                 end_size=1, 
                 spread_angle=20): # degrees
        
        self.source_tower = source_tower
        self.target_enemy = target_enemy
        self.particle_rate = particle_rate
        self.particle_life = particle_life
        self.particle_speed = particle_speed
        self.start_color = start_color
        self.end_color = end_color
        self.start_size = start_size
        self.end_size = end_size
        self.spread_angle_rad = math.radians(spread_angle)
        
        self.particles = []
        self.spawn_accumulator = 0.0
        self.is_spawning = True # Controls if new particles are generated
        self.finished = False # For removal from GameScene effects list

    def stop_spawning(self):
        """Signal the effect to stop creating new particles."""
        self.is_spawning = False

    def update(self, time_delta):
        """Update particle positions, lifetimes, and spawn new ones."""
        if self.finished:
            return True

        # Check if target is still valid
        if not self.target_enemy or self.target_enemy.health <= 0:
            self.stop_spawning() # Stop spawning if target is gone

        # --- Spawn New Particles --- 
        if self.is_spawning:
            self.spawn_accumulator += self.particle_rate * time_delta
            num_new_particles = int(self.spawn_accumulator)
            if num_new_particles > 0:
                self.spawn_accumulator -= num_new_particles
                
                start_x = self.source_tower.x
                start_y = self.source_tower.y
                target_x = self.target_enemy.x
                target_y = self.target_enemy.y
                
                dx = target_x - start_x
                dy = target_y - start_y
                distance = max(1, math.hypot(dx, dy))
                base_angle = math.atan2(dy, dx)
                base_vx = (dx / distance) * self.particle_speed
                base_vy = (dy / distance) * self.particle_speed
                
                for _ in range(num_new_particles):
                    # Apply spread
                    angle_offset = random.uniform(-self.spread_angle_rad / 2, self.spread_angle_rad / 2)
                    current_angle = base_angle + angle_offset
                    speed_multiplier = random.uniform(0.8, 1.2)
                    vx = math.cos(current_angle) * self.particle_speed * speed_multiplier
                    vy = math.sin(current_angle) * self.particle_speed * speed_multiplier
                    
                    life = self.particle_life * random.uniform(0.7, 1.1)
                    
                    self.particles.append({
                        'x': start_x + random.uniform(-5, 5), # Slight origin jitter
                        'y': start_y + random.uniform(-5, 5),
                        'vx': vx,
                        'vy': vy,
                        'life': life,
                        'max_life': life
                    })
        
        # --- Update Existing Particles --- 
        active_particles = []
        for p in self.particles:
            p['x'] += p['vx'] * time_delta
            p['y'] += p['vy'] * time_delta
            p['life'] -= time_delta
            
            if p['life'] > 0:
                active_particles.append(p)
                
        self.particles = active_particles
        
        # Check if effect is finished (no more spawning AND no particles left)
        if not self.is_spawning and not self.particles:
            self.finished = True
            return True
            
        return False # Effect still active

    def draw(self, screen, grid_offset_x, grid_offset_y):
        """Draw all active particles."""
        if self.finished:
            return
            
        for p in self.particles:
            life_ratio = max(0, p['life'] / p['max_life'])
            
            # Interpolate color
            r = int(self.start_color[0] + (self.end_color[0] - self.start_color[0]) * (1 - life_ratio))
            g = int(self.start_color[1] + (self.end_color[1] - self.start_color[1]) * (1 - life_ratio))
            b = int(self.start_color[2] + (self.end_color[2] - self.start_color[2]) * (1 - life_ratio))
            
            # Interpolate size
            current_size = int(self.start_size + (self.end_size - self.start_size) * (1 - life_ratio))
            current_alpha = int(255 * life_ratio) # Fade out
            
            if current_alpha > 0 and current_size > 0:
                try:
                    # Draw simple circles for particles
                    pos_x = int(p['x'] + grid_offset_x)
                    pos_y = int(p['y'] + grid_offset_y)
                    
                    # Use SRCALPHA surface for better alpha blending
                    particle_surf = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
                    pygame.draw.circle(particle_surf, (r, g, b, current_alpha), (current_size, current_size), current_size)
                    screen.blit(particle_surf, (pos_x - current_size, pos_y - current_size))
                except Exception as e:
                    #print(f"Error drawing flamethrower particle: {e}") 
                    pass

class SuperchargedZapEffect(Effect):
    """Visual effect for the final high-damage zap from a tower chain."""
    def __init__(self, start_pos, end_pos, duration=0.2, color=(255, 255, 150), thickness=6):
        """
        Initialize the zap visual.
        
        :param start_pos: Tuple (x, y) of the starting tower (absolute screen coords).
        :param end_pos: Tuple (x, y) of the target enemy (absolute screen coords).
        :param duration: How long the visual effect lasts in seconds (should be short).
        :param color: The color of the zap.
        :param thickness: The thickness of the zap line.
        """
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.duration = max(0.01, duration)
        self.timer = 0.0
        self.finished = False
        self.color = color
        self.thickness = thickness
        
        # Base Effect attributes needed for loop compatibility
        self.image = None 
        self.rect = None 
        
        # print(f"SuperchargedZapEffect created from {start_pos} to {end_pos}") # Debug

    def update(self, time_delta):
        """Update the effect timer. Returns True if finished."""
        if self.finished:
            return True
            
        self.timer += time_delta
        if self.timer >= self.duration:
            self.finished = True
            
        return self.finished

    def draw(self, screen):
        """Draw the zap line with fade."""
        if self.finished:
            return
            
        # Calculate alpha based on remaining duration (linear fade)
        alpha_multiplier = max(0, 1.0 - (self.timer / self.duration))
        current_alpha = int(255 * alpha_multiplier)
        current_color = (*self.color[:3], current_alpha) 

        try:
            # Draw a single thick anti-aliased line
            pygame.draw.aaline(screen, current_color, self.start_pos, self.end_pos, self.thickness)
            # Optional: Draw a slightly thinner inner line of brighter color?
            # pygame.draw.aaline(screen, (255,255,255,current_alpha), self.start_pos, self.end_pos, max(1, self.thickness - 2))
        except Exception as e:
            #print(f"Error drawing SuperchargedZapEffect: {e}") 
            pass

# --- New Particle Effect for Acid Spew --- 
class AcidSpewParticleEffect:
    def __init__(self, source_tower, target_enemy, 
                 particle_rate=60, # particles per second
                 particle_life=0.5, 
                 particle_speed=170, 
                 start_color=(50, 205, 50), # Lime Green start
                 end_color=(34, 139, 34),   # Forest Green end
                 start_size=5, 
                 end_size=1, 
                 spread_angle=18): # degrees
        
        self.source_tower = source_tower
        self.target_enemy = target_enemy
        self.particle_rate = particle_rate
        self.particle_life = particle_life
        self.particle_speed = particle_speed
        self.start_color = start_color
        self.end_color = end_color
        self.start_size = start_size
        self.end_size = end_size
        self.spread_angle_rad = math.radians(spread_angle)
        
        self.particles = []
        self.spawn_timer = 0.0
        self.finished = False # Effect itself isn't finished until particles fade
        self.spawning_active = True # Controls if new particles are created

    def stop_spawning(self):
        """Stop creating new particles (e.g., when target is lost)."""
        self.spawning_active = False

    def update(self, time_delta):
        """Update particle positions, life, and spawn new ones."""
        # Update existing particles
        particles_to_remove = []
        for particle in self.particles:
            particle['life'] -= time_delta
            if particle['life'] <= 0:
                particles_to_remove.append(particle)
            else:
                # Move particle along its velocity vector
                particle['pos'][0] += particle['vel'][0] * time_delta
                particle['pos'][1] += particle['vel'][1] * time_delta
        
        # Remove dead particles
        for particle in particles_to_remove:
            self.particles.remove(particle)
            
        # Check if effect is truly finished (no more spawning AND no particles left)
        if not self.spawning_active and not self.particles:
             self.finished = True
             return # Skip spawning if done

        # Spawn new particles if spawning is active
        if self.spawning_active:
            self.spawn_timer += time_delta
            spawn_interval = 1.0 / self.particle_rate
            while self.spawn_timer >= spawn_interval:
                self.spawn_timer -= spawn_interval
                
                # Recalculate direction ONLY when spawning
                if self.target_enemy and self.target_enemy.health > 0:
                    # Target is valid, calculate direction
                    start_x = self.source_tower.x 
                    start_y = self.source_tower.y
                    target_x = self.target_enemy.x
                    target_y = self.target_enemy.y
                    
                    dx = target_x - start_x
                    dy = target_y - start_y
                    distance = math.hypot(dx, dy)
                    
                    if distance > 0:
                        # Base direction vector (normalized)
                        base_vx = dx / distance
                        base_vy = dy / distance
                        base_angle = math.atan2(base_vy, base_vx)
                        
                        # Apply random spread
                        angle_offset = random.uniform(-self.spread_angle_rad / 2, self.spread_angle_rad / 2)
                        final_angle = base_angle + angle_offset
                        
                        # Calculate velocity components
                        final_vx = math.cos(final_angle) * self.particle_speed
                        final_vy = math.sin(final_angle) * self.particle_speed
                        
                        # Create particle
                        self.particles.append({
                            'pos': [start_x, start_y], 
                            'vel': [final_vx, final_vy],
                            'life': self.particle_life
                        })
                else:
                    # Target lost or dead while spawning, stop spawning immediately
                    self.stop_spawning()
                    break # Exit the spawn loop for this frame
                    
    def draw(self, screen, grid_offset_x, grid_offset_y):
        """Draw all active particles."""
        for particle in self.particles:
            life_ratio = max(0, particle['life'] / self.particle_life)
            
            # Interpolate size and color based on life ratio
            current_size = int(self.start_size + (self.end_size - self.start_size) * (1 - life_ratio))
            if current_size <= 0: continue # Don't draw invisible particles
            
            current_color = [
                int(self.start_color[i] + (self.end_color[i] - self.start_color[i]) * (1 - life_ratio))
                for i in range(3)
            ]
            current_color = tuple(max(0, min(255, c)) for c in current_color) # Clamp color values
            
            # Calculate screen position
            draw_x = int(particle['pos'][0] + grid_offset_x)
            draw_y = int(particle['pos'][1] + grid_offset_y)
            
            try:
                pygame.draw.circle(screen, current_color, (draw_x, draw_y), current_size)
            except Exception as e:
                 #print(f"Error drawing AcidSpew particle: {e}")
                 pass

# --- End Acid Spew --- 

# --- NEW Pulse Image Effect ---
import pygame
import config # Use direct import

class PulseImageEffect:
    def __init__(self, x, y, image, duration=0.5, start_scale=0.8, end_scale=1.5):
        """
        Creates an effect that scales and fades an image outwards from a point.

        Args:
            x (float): Center x position (game grid coordinates).
            y (float): Center y position (game grid coordinates).
            image (pygame.Surface): The image surface to display.
            duration (float): Duration of the effect in seconds.
            start_scale (float): Initial scale factor of the image.
            end_scale (float): Final scale factor of the image.
        """
        self.x = x
        self.y = y
        self.image = image
        self.duration_ms = duration * 1000 # Convert to milliseconds
        self.start_scale = start_scale
        self.end_scale = end_scale
        self.elapsed_time_ms = 0
        self.finished = False
        self.current_scale = start_scale
        self.current_alpha = 255

    def update(self, time_delta):
        """
        Updates the effect's animation state.

        Args:
            time_delta (float): Time elapsed since the last frame in seconds.

        Returns:
            bool: True if the effect is finished, False otherwise.
        """
        if self.finished:
            return True

        self.elapsed_time_ms += time_delta * 1000

        if self.elapsed_time_ms >= self.duration_ms:
            self.finished = True
            return True

        # Interpolate scale and alpha based on progress
        progress = min(1.0, self.elapsed_time_ms / self.duration_ms)
        self.current_scale = self.start_scale + (self.end_scale - self.start_scale) * progress
        self.current_alpha = max(0, int(255 * (1.0 - progress))) # Fade out

        return False # Not finished yet

    def draw(self, screen):
        """
        Draws the effect on the screen.

        Args:
            screen (pygame.Surface): The surface to draw on.
        """
        if self.finished or not self.image:
            return

        try:
            # Use rotozoom for smooth scaling, 0 angle for no rotation
            scaled_image = pygame.transform.rotozoom(self.image, 0, self.current_scale)

            # Set alpha for fading
            # Create a copy to avoid modifying the original if it's cached/shared
            image_copy = scaled_image.copy()
            image_copy.set_alpha(self.current_alpha)

            # Calculate draw position (top-left) based on the effect's center (x, y)
            # and accounting for the grid's offset from the screen edge.
            draw_x = (self.x + config.UI_PANEL_PADDING) - image_copy.get_width() // 2
            draw_y = (self.y + config.UI_PANEL_PADDING) - image_copy.get_height() // 2

            screen.blit(image_copy, (draw_x, draw_y))
        except Exception as e:
            #print(f"Error drawing PulseImageEffect: {e}")
            # Handle potential errors, e.g., if image becomes invalid
            self.finished = True # Stop trying to draw if error occurs

# --- End Pulse Image Effect --- 

# --- NEW: Expanding Circle Effect --- 
class ExpandingCircleEffect:
    def __init__(self, x, y, max_radius, duration, color, thickness=2, filled=False):
        self.x = x
        self.y = y
        self.max_radius = max_radius
        self.duration = max(0.01, duration) # Avoid division by zero
        self.color = color # Should be RGBA tuple like (R, G, B, Alpha)
        self.thickness = thickness
        self.filled = filled  # Whether to draw a filled circle
        self.start_time = pygame.time.get_ticks() / 1000.0
        self.current_radius = 0
        self.finished = False

    def update(self, time_delta):
        if self.finished:
            return True
            
        current_time = pygame.time.get_ticks() / 1000.0
        elapsed_time = current_time - self.start_time

        if elapsed_time >= self.duration:
            self.finished = True
            return True
        else:
            # Linear expansion
            self.current_radius = self.max_radius * (elapsed_time / self.duration)
            return False

    def draw(self, screen, offset_x=0, offset_y=0):
        if not self.finished and self.current_radius > 0:
            draw_x = int(self.x + offset_x)
            draw_y = int(self.y + offset_y)
            
            # Draw filled or outlined circle based on the filled parameter
            thickness = 0 if self.filled else self.thickness  # pygame uses 0 for filled circles
            pygame.draw.circle(screen, self.color, (draw_x, draw_y), int(self.current_radius), thickness)
# --- End Expanding Circle Effect ---

class FloatingTextEffect:
    def __init__(self, x, y, text, color=(255, 255, 255), duration=1.0, rise_speed=30, font_size=24):
        self.x = x
        self.initial_y = y
        self.current_y = y
        self.text = text
        self.duration = max(0.1, duration)
        self.color = color
        self.rise_speed = rise_speed
        self.timer = 0.0
        self.finished = False

        # Load font (Consider loading fonts centrally in GameScene/main later)
        try:
            self.font = pygame.font.Font(None, font_size)
        except Exception as e:
            print(f"Error loading font for FloatingTextEffect: {e}")
            self.font = pygame.font.Font(pygame.font.get_default_font(), font_size)
        
        self.text_surf = None # Will be rendered in draw
        self.text_rect = None
        
        # Base Effect attributes needed for loop compatibility
        self.image = None 
        self.rect = None # Will be updated in draw
        
        print(f"FloatingTextEffect created: '{text}' at ({x},{y})")

    def update(self, time_delta):
        """Update timer, position, and alpha. Returns True if finished."""
        if self.finished:
            return True
            
        self.timer += time_delta
        if self.timer >= self.duration:
            self.finished = True
            return True
            
        # Update position
        self.current_y = self.initial_y - (self.timer * self.rise_speed)
        
        return False

    def draw(self, screen):
        """Draw the floating text with fade."""
        if self.finished:
            return

        # Calculate alpha (linear fade out)
        alpha_multiplier = max(0, 1.0 - (self.timer / self.duration))
        current_alpha = int(255 * alpha_multiplier)
        
        # Render text surface with current alpha
        # Creating surface each frame might be inefficient, but handles alpha easily
        try:
             current_color_with_alpha = (*self.color[:3], current_alpha)
             self.text_surf = self.font.render(self.text, True, self.color) # Render without alpha first
             self.text_surf.set_alpha(current_alpha) # Apply alpha to the surface
             self.rect = self.text_surf.get_rect(center=(int(self.x), int(self.current_y)))
             screen.blit(self.text_surf, self.rect)
        except Exception as e:
            print(f"Error rendering/drawing FloatingTextEffect: {e}") 

class FrostPulseEffect:
    """Visual effect for the Frost Pulse tower's slow aura."""
    def __init__(self, x, y, radius, duration):
        self.x = x
        self.y = y
        self.radius = radius
        self.duration = duration
        self.life_remaining = duration
        self.finished = False
        
    def update(self, time_delta):
        """Update the effect's lifetime."""
        self.life_remaining -= time_delta
        if self.life_remaining <= 0:
            self.finished = True
            return True
        return False
        
    def draw(self, screen, offset_x=0, offset_y=0):
        """Draw the expanding frost pulse effect."""
        if self.finished:
            return
            
        # Calculate current radius based on lifetime
        progress = 1.0 - (self.life_remaining / self.duration)
        current_radius = self.radius * progress
        
        # Calculate alpha based on lifetime
        alpha = int(255 * (1.0 - progress))
        
        # Create a surface for the pulse
        pulse_surface = pygame.Surface((int(current_radius * 2), int(current_radius * 2)), pygame.SRCALPHA)
        
        # Draw the pulse circle
        pygame.draw.circle(pulse_surface, (0, 200, 255, alpha), 
                         (int(current_radius), int(current_radius)), 
                         int(current_radius), 2)
        
        # Blit the pulse surface to the screen
        screen.blit(pulse_surface, 
                   (self.x - current_radius + offset_x, 
                    self.y - current_radius + offset_y)) 