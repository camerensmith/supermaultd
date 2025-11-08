import pygame
import pygame_gui
from config import WIDTH, HEIGHT, GRID_SIZE
from pygame_gui.elements import UIButton, UILabel
from pygame_gui.elements import UIScrollingContainer # Import the scrolling container
import os

class TowerSelector:
    def __init__(self, available_towers, tower_assets, manager, initial_money, initial_lives, panel_rect, damage_type_data, click_sound):
        """
        Initialize the tower selection UI panel within the provided rect.
        
        :param available_towers: Dictionary of available towers for the selected race
        :param tower_assets: Instance of TowerAssets
        :param manager: pygame_gui UIManager instance
        :param initial_money: The starting money amount from the game scene
        :param initial_lives: The starting lives amount from the game scene
        :param panel_rect: The pygame.Rect defining the panel's position and size
        :param damage_type_data: Dictionary containing descriptions for damage types
        :param click_sound: Loaded pygame.mixer.Sound object for clicks
        """
        self.available_towers = available_towers
        self.tower_assets = tower_assets 
        self.manager = manager
        self.selected_tower = None
        self.tower_buttons = {} 
        self.tower_images = {}
        self.selected_highlights = {}  # Store highlight overlays for selected state
        self.money = initial_money
        self.lives = initial_lives
        self.damage_type_data = damage_type_data # Store damage type data
        self.click_sound = click_sound # Store sound effect
        self.tower_counts = {}  # Track number of each tower type built
        # Cache for expensive-to-generate tooltip HTML per tower
        self._tooltip_html_cache = {}
        
        # --- Load Cannot Select Sound ---
        self.cannot_select_sound = None
        try:
            cannot_select_path = os.path.join("assets", "sounds", "cannot_select.mp3") 
            if os.path.exists(cannot_select_path):
                self.cannot_select_sound = pygame.mixer.Sound(cannot_select_path)
                print(f"[TowerSelector Init] Loaded cannot select sound: {cannot_select_path}")
            else:
                print(f"[TowerSelector Init] Warning: Cannot select sound file not found: {cannot_select_path}")
        except pygame.error as e:
            print(f"[TowerSelector Init] Error loading cannot select sound: {e}")
        # --- End Cannot Select Sound Loading ---
        
        # Store panel dimensions from rect
        self.panel_rect = panel_rect
        self.panel_width = panel_rect.width
        self.panel_height = panel_rect.height
        
        # Drawer animation state
        self.is_open = True  # Panel starts open
        self.is_animating = False
        self.animation_progress = 1.0  # 1.0 = fully open, 0.0 = fully closed
        self.animation_speed = 8.0  # Animation speed (higher = faster)
        self.visible_x = panel_rect.x  # Visible position (when open)
        self.hidden_x = panel_rect.x + panel_rect.width  # Hidden position (off-screen to the right)
        self.toggle_button_screen_x = panel_rect.x  # Toggle button stays at left edge of panel area
        
        # Create the main panel using the provided rect
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=self.panel_rect,
            manager=self.manager
        )
        
        # Create toggle button (nib/arrow on left side)
        # Position it on the left edge of the panel area, centered vertically
        # Make it a small nib that extends slightly to the left of the panel
        # Position it as a top-level element (not in panel container) so it stays visible
        toggle_button_width = 25
        toggle_button_height = 80
        toggle_button_x = panel_rect.x - toggle_button_width  # Position on left edge, outside panel
        toggle_button_y = panel_rect.y + (panel_rect.height - toggle_button_height) // 2  # Center vertically
        self.toggle_button_screen_x = toggle_button_x  # Store screen position
        
        self.toggle_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(toggle_button_x, toggle_button_y, toggle_button_width, toggle_button_height),
            text=">",  # Will be updated by _update_toggle_button_text()
            manager=self.manager,
            object_id="#toggle_button"
        )
        
        # Update toggle button text based on initial state
        self._update_toggle_button_text()
        
        # --- Internal Layout (relative to panel) ---
        current_y = 10 # Start Y for internal elements

        # Add lives display (top of panel)
        lives_height = 28
        lives_rect = pygame.Rect(10, current_y, self.panel_width - 20, lives_height)
        self.lives_label = pygame_gui.elements.UILabel(
            relative_rect=lives_rect,
            text=f'Lives: {self.lives}',
            manager=self.manager,
            container=self.panel,
            object_id="#lives_label"
        )
        current_y += lives_height + 4
        
        # Add money display 
        money_height = 28
        money_rect = pygame.Rect(10, current_y, self.panel_width - 20, money_height)
        self.money_label = pygame_gui.elements.UILabel(
            relative_rect=money_rect,
            text=f'Money: ${self.money}',
            manager=self.manager,
            container=self.panel,
            object_id="#money_label"
        )
        current_y += money_height + 12
        
        # --- Split Panel into Two Sections ---
        # Top section: Icon buttons (scrollable)
        # Bottom section: Fixed info box
        
        # Calculate heights - Info box takes ~40% of remaining space, icons take ~60%
        remaining_height = self.panel_height - current_y - 10  # 10px bottom padding
        info_box_height = int(remaining_height * 0.4)
        icons_area_height = remaining_height - info_box_height - 10  # 10px gap between sections
        
        # Create scrolling container for icon buttons (top section)
        icon_container_rect = pygame.Rect(10, current_y, self.panel_width - 20, icons_area_height)
        self.icon_scroll_container = UIScrollingContainer(
            relative_rect=icon_container_rect,
            manager=self.manager,
            container=self.panel
        )
        
        # Create fixed info box (bottom section)
        info_box_y = current_y + icons_area_height + 10
        info_box_rect = pygame.Rect(10, info_box_y, self.panel_width - 20, info_box_height)
        self.info_box = pygame_gui.elements.UITextBox(
            html_text="<b>Select a tower to view details</b><br><i>Click on a tower icon above</i>",
            relative_rect=info_box_rect,
            manager=self.manager,
            container=self.panel,
            object_id='#tower_info_box'
        )
        
        # Precompute tooltip HTML once per tower for faster rebuilds
        for tower_id, tower_data in self.available_towers.items():
            if tower_id not in self._tooltip_html_cache:
                self._tooltip_html_cache[tower_id] = self._build_tooltip_html(tower_data)

        # Create icon buttons
        self.create_icon_buttons()
        
    def create_icon_buttons(self):
        """Create icon-only buttons in the scrolling container"""
        # Icon size - should be square
        icon_size = 64  # Size of each icon button
        padding = 8  # Padding between icons
        icons_per_row = max(2, (self.panel_width - 40) // (icon_size + padding))  # Calculate how many fit per row
        
        content_width = self.icon_scroll_container.get_container().get_rect().width
        
        current_x = padding
        current_y = padding
        
        for index, (tower_id, tower_data) in enumerate(self.available_towers.items()):
            # Start new row if needed
            if current_x + icon_size > content_width:
                current_x = padding
                current_y += icon_size + padding
            
            # Create button rect for icon
            button_rect = pygame.Rect(current_x, current_y, icon_size, icon_size)
            
            # Get tower image (use original, not preview, for better quality)
            tower_image = self.tower_assets.get_tower_image(tower_id)
            if tower_image:
                # Scale image to fit button size (with some padding)
                scaled_size = icon_size - 8  # Leave 4px padding on each side
                scaled_image = pygame.transform.scale(tower_image, (scaled_size, scaled_size))
                
                # Create button with empty text (will draw image on top)
                button = pygame_gui.elements.UIButton(
                    relative_rect=button_rect,
                    text="",  # Empty text - icon only
                    manager=self.manager,
                    container=self.icon_scroll_container.get_container(),
                    object_id="#tower_icon_button"
                )
                self.tower_buttons[tower_id] = button
                
                # Add image on top of button
                image_offset = 4  # 4px padding inside button
                image_rect = pygame.Rect(
                    current_x + image_offset,
                    current_y + image_offset,
                    scaled_size,
                    scaled_size
                )
                img_elem = pygame_gui.elements.UIImage(
                    relative_rect=image_rect,
                    image_surface=scaled_image,
                    manager=self.manager,
                    container=self.icon_scroll_container.get_container()
                )
                self.tower_images[tower_id] = img_elem
                
                # Create selection highlight overlay (initially hidden)
                # Create a bright border/highlight surface
                highlight_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                # Draw outer border (bright yellow/gold)
                pygame.draw.rect(highlight_surface, (255, 215, 0, 200), (0, 0, icon_size, icon_size), 4)
                # Draw inner glow
                pygame.draw.rect(highlight_surface, (255, 255, 100, 100), (2, 2, icon_size-4, icon_size-4), 3)
                
                highlight_rect = pygame.Rect(current_x, current_y, icon_size, icon_size)
                highlight_elem = pygame_gui.elements.UIImage(
                    relative_rect=highlight_rect,
                    image_surface=highlight_surface,
                    manager=self.manager,
                    container=self.icon_scroll_container.get_container()
                )
                # Initially hide highlight
                highlight_elem.hide()
                self.selected_highlights[tower_id] = highlight_elem
            else:
                # Fallback: create button with tower name if image missing
                button = pygame_gui.elements.UIButton(
                    relative_rect=button_rect,
                    text=tower_data.get('name', 'N/A')[:5],  # Truncated name
                    manager=self.manager,
                    container=self.icon_scroll_container.get_container(),
                    object_id="#tower_icon_button"
                )
                self.tower_buttons[tower_id] = button
                
                # Create selection highlight for fallback button too
                highlight_surface = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                pygame.draw.rect(highlight_surface, (255, 215, 0, 200), (0, 0, icon_size, icon_size), 4)
                pygame.draw.rect(highlight_surface, (255, 255, 100, 100), (2, 2, icon_size-4, icon_size-4), 3)
                highlight_rect = pygame.Rect(current_x, current_y, icon_size, icon_size)
                highlight_elem = pygame_gui.elements.UIImage(
                    relative_rect=highlight_rect,
                    image_surface=highlight_surface,
                    manager=self.manager,
                    container=self.icon_scroll_container.get_container()
                )
                highlight_elem.hide()
                self.selected_highlights[tower_id] = highlight_elem
            
            # Move to next position
            current_x += icon_size + padding
            
        # Set scrollable area size
        total_content_height = current_y + icon_size + padding
        self.icon_scroll_container.set_scrollable_area_dimensions((content_width, total_content_height))

    def handle_event(self, event):
        """Handle pygame_gui events"""
        # Handle right-click on tower icons
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:  # Right click
            mouse_pos = event.pos
            # Check if right-click is on any tower button
            for tower_id, button in self.tower_buttons.items():
                # Get the absolute screen position of the button
                button_rect = button.get_abs_rect()
                if button_rect.collidepoint(mouse_pos):
                    # Right-clicked on a tower icon
                    # If this tower is selected and cannot be placed, clear selection
                    if tower_id == self.selected_tower:
                        tower_data = self.available_towers.get(tower_id)
                        if tower_data:
                            can_afford = self.money >= tower_data['cost']
                            tower_limit = tower_data.get('limit')
                            current_count = self.tower_counts.get(tower_id, 0)
                            at_limit = tower_limit is not None and current_count >= tower_limit
                            
                            # If cannot be placed (can't afford or at limit), clear selection
                            if not can_afford or at_limit:
                                self.clear_selection()
                                return  # Don't process further
        
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            clicked_button = event.ui_element
            
            # Check if toggle button was clicked
            if clicked_button == self.toggle_button:
                self.toggle_panel()
                if self.click_sound:
                    self.click_sound.play()
                return
            
            clicked_tower_id = None
            
            # Find which tower button was clicked
            for tower_id, button in self.tower_buttons.items():
                if clicked_button == button:
                    clicked_tower_id = tower_id
                    break

            if clicked_tower_id:
                if self.click_sound: 
                    self.click_sound.play()
                
                tower_data = self.available_towers.get(clicked_tower_id)
                can_afford = tower_data and self.money >= tower_data['cost']
                tower_limit = tower_data.get('limit') if tower_data else None
                current_count = self.tower_counts.get(clicked_tower_id, 0)
                at_limit = tower_limit is not None and current_count >= tower_limit

                # Handle selection
                if clicked_tower_id == self.selected_tower:
                    # Clicked the already selected tower - Deselect it
                    self.selected_tower = None
                    self.update_info_box(None)
                    self.update_selection_highlights(None)
                elif can_afford and not at_limit:
                    # Clicked a new, affordable tower - Select it
                    self.selected_tower = clicked_tower_id
                    # Visually select the new one and deselect others
                    for t_id, btn in self.tower_buttons.items():
                        if t_id == clicked_tower_id:
                            btn.select()
                        else:
                            btn.unselect()
                    # Update highlights and info box
                    self.update_selection_highlights(clicked_tower_id)
                    self.update_info_box(clicked_tower_id)
                else:
                    # Clicked an unaffordable or at-limit tower - Play sound
                    if self.cannot_select_sound: 
                        self.cannot_select_sound.play()
                    # Still show info and highlight even if can't afford (for preview)
                    for t_id, btn in self.tower_buttons.items():
                        if t_id == clicked_tower_id:
                            btn.select()
                        else:
                            btn.unselect()
                    self.update_selection_highlights(clicked_tower_id)
                    self.update_info_box(clicked_tower_id)
        
        # Let the manager process the event regardless of our handling
        self.manager.process_events(event)

    def update_selection_highlights(self, selected_tower_id):
        """Update visual highlights for selected tower buttons"""
        for tower_id, highlight in self.selected_highlights.items():
            if tower_id == selected_tower_id:
                highlight.show()
            else:
                highlight.hide()

    def update_info_box(self, tower_id):
        """Update the info box with tower details or placeholder"""
        if tower_id is None:
            # Show placeholder
            placeholder_text = "<b>Select a tower to view details</b><br><i>Click on a tower icon above</i>"
            self.info_box.html_text = placeholder_text
            self.info_box.rebuild()
        else:
            # Show tower details
            tower_data = self.available_towers.get(tower_id)
            if tower_data:
                tooltip_html = self._tooltip_html_cache.get(tower_id)
                if tooltip_html is None:
                    tooltip_html = self._build_tooltip_html(tower_data)
                    self._tooltip_html_cache[tower_id] = tooltip_html
                
                # Check if affordable/at limit and add status
                can_afford = self.money >= tower_data['cost']
                tower_limit = tower_data.get('limit')
                current_count = self.tower_counts.get(tower_id, 0)
                at_limit = tower_limit is not None and current_count >= tower_limit
                
                status_html = ""
                if at_limit:
                    status_html = "<br><b style='color:#FF0000;'>LIMIT REACHED</b>"
                elif not can_afford:
                    status_html = f"<br><b style='color:#FFAA00;'>CANNOT AFFORD (Need ${tower_data['cost']})</b>"
                else:
                    status_html = "<br><b style='color:#00FF00;'>READY TO PLACE</b>"
                
                self.info_box.html_text = tooltip_html + status_html
                self.info_box.rebuild()

    def _update_toggle_button_text(self):
        """Update toggle button text to show current state"""
        if hasattr(self, 'toggle_button'):
            # Show ">" when open (panel visible, arrow points right to indicate it can close)
            # Show "<" when closed (panel hidden, arrow points left to indicate it can open)
            self.toggle_button.set_text(">" if self.is_open else "<")
    
    def toggle_panel(self):
        """Toggle panel visibility (show/hide)"""
        self.is_open = not self.is_open
        self.is_animating = True
        self._update_toggle_button_text()
    
    def update(self, time_delta):
        """Update the UI manager and handle drawer animation"""
        # Handle drawer animation
        if self.is_animating:
            # Calculate target progress (1.0 = open, 0.0 = closed)
            target_progress = 1.0 if self.is_open else 0.0
            # Animate towards target
            if self.is_open:
                # Opening: increase progress
                self.animation_progress += self.animation_speed * time_delta
                if self.animation_progress >= 1.0:
                    self.animation_progress = 1.0
                    self.is_animating = False
            else:
                # Closing: decrease progress
                self.animation_progress -= self.animation_speed * time_delta
                if self.animation_progress <= 0.0:
                    self.animation_progress = 0.0
                    self.is_animating = False
            
            # Calculate current panel X position (interpolate between hidden and visible)
            current_x = self.hidden_x + (self.visible_x - self.hidden_x) * self.animation_progress
            
            # Update panel position (pygame_gui uses set_position for absolute positioning)
            new_rect = pygame.Rect(current_x, self.panel_rect.y, self.panel_width, self.panel_height)
            self.panel.set_position((current_x, self.panel_rect.y))
            self.panel_rect = new_rect
            
            # Update toggle button position to follow panel (stays on left edge of panel)
            if hasattr(self, 'toggle_button'):
                toggle_button_x = current_x - self.toggle_button.rect.width
                toggle_button_y = self.panel_rect.y + (self.panel_height - self.toggle_button.rect.height) // 2
                self.toggle_button.set_position((toggle_button_x, toggle_button_y))
        
        self.manager.update(time_delta)
        
    def draw(self, surface):
        """Draw the UI elements"""
        self.manager.draw_ui(surface)
        
    def get_selected_tower(self):
        """Get the currently selected tower ID"""
        return self.selected_tower
    
    def select_tower_by_index(self, index):
        """Select a tower by its index in the available_towers dictionary"""
        # Get list of tower IDs in order (Python 3.7+ preserves insertion order)
        tower_ids = list(self.available_towers.keys())
        
        if 0 <= index < len(tower_ids):
            tower_id = tower_ids[index]
            tower_data = self.available_towers.get(tower_id)
            
            if tower_data:
                can_afford = self.money >= tower_data['cost']
                tower_limit = tower_data.get('limit')
                current_count = self.tower_counts.get(tower_id, 0)
                at_limit = tower_limit is not None and current_count >= tower_limit
                
                # Handle selection similar to button click
                if tower_id == self.selected_tower:
                    # Same tower - deselect it
                    self.selected_tower = None
                    self.update_info_box(None)
                    self.update_selection_highlights(None)
                    for btn in self.tower_buttons.values():
                        btn.unselect()
                elif can_afford and not at_limit:
                    # Select the new tower
                    self.selected_tower = tower_id
                    # Visually select the new one and deselect others
                    for t_id, btn in self.tower_buttons.items():
                        if t_id == tower_id:
                            btn.select()
                        else:
                            btn.unselect()
                    self.update_selection_highlights(tower_id)
                    self.update_info_box(tower_id)
                    if self.click_sound:
                        self.click_sound.play()
                else:
                    # Can't afford or at limit - still show info/highlight but play sound
                    if self.cannot_select_sound:
                        self.cannot_select_sound.play()
                    # Show info and highlight even if can't afford
                    for t_id, btn in self.tower_buttons.items():
                        if t_id == tower_id:
                            btn.select()
                        else:
                            btn.unselect()
                    self.update_selection_highlights(tower_id)
                    self.update_info_box(tower_id)
        
    def clear_selection(self):
        """Clear the current tower selection and visually deselect all buttons."""
        self.selected_tower = None
        self.update_info_box(None)
        self.update_selection_highlights(None)
        # Loop through buttons and call unselect()
        for button in self.tower_buttons.values():
            button.unselect()
    
    def is_point_in_ui(self, point):
        """Check if a point (x, y) is within the tower selector UI area (panel or toggle button)."""
        x, y = point
        # Check if point is in the panel (use current panel position)
        if hasattr(self, 'panel') and hasattr(self, 'panel_rect'):
            # Get current panel position (accounts for animation)
            try:
                current_panel_rect = self.panel.get_abs_rect()
                if current_panel_rect.collidepoint(x, y):
                    return True
            except Exception:
                # Fallback to stored panel_rect if get_abs_rect fails
                if self.panel_rect.collidepoint(x, y):
                    return True
        # Check if point is in the toggle button
        if hasattr(self, 'toggle_button'):
            try:
                toggle_rect = self.toggle_button.get_abs_rect()
                if toggle_rect.collidepoint(x, y):
                    return True
            except Exception:
                pass
        # Check if point is in any tower button
        for button in self.tower_buttons.values():
            try:
                button_rect = button.get_abs_rect()
                if button_rect.collidepoint(x, y):
                    return True
            except Exception:
                pass
        return False
        
    def update_money(self, new_amount):
        """Update the money display and refresh button states"""
        self.money = new_amount
        self.money_label.set_text(f'Money: ${self.money}')
        self.update_button_states()  # Refresh button states based on new money amount
        # Refresh info box if a tower is selected
        if self.selected_tower:
            self.update_info_box(self.selected_tower)

    def update_lives(self, new_lives):
        """Update the lives display label at the top of the panel."""
        self.lives = new_lives
        if hasattr(self, 'lives_label'):
            try:
                self.lives_label.set_text(f'Lives: {self.lives}')
            except Exception:
                pass

    def update_tower_counts(self, tower_counts):
        """Update the tower counts and refresh button states."""
        self.tower_counts = tower_counts
        self.update_button_states()
        # Refresh info box if a tower is selected
        if self.selected_tower:
            self.update_info_box(self.selected_tower)

    def _build_tooltip_html(self, tower_data):
        """Build and return HTML tooltip for a tower_data dict (cached by caller)."""
        tooltip_lines = []

        name = tower_data.get('name', 'N/A')
        cost = tower_data.get('cost', 0)
        tooltip_lines.append(f"<b>{name}</b>")

        description = tower_data.get('description')
        if description:
            tooltip_lines.append(f"<i>{description}</i>")
            tooltip_lines.append("")

        tooltip_lines.append(f"Cost: ${cost}")
        grid_w = tower_data.get('grid_width', 1)
        grid_h = tower_data.get('grid_height', 1)
        if grid_w > 1 or grid_h > 1:
            tooltip_lines.append(f"Size: {grid_w}x{grid_h}")

        tooltip_lines.append("")
        tooltip_lines.append("<b>Stats:</b>")

        # Check for special effect damage first
        special_damage = None
        special_damage_type = None
        special = tower_data.get('special', {})
        
        if special:
            effect = special.get('effect', '')
            if effect == 'orbiting_damager':
                special_damage = special.get('orb_damage', 0)
                special_damage_type = special.get('orb_damage_type', 'normal')
            elif effect == 'damage_pulse_aura':
                special_damage = special.get('pulse_damage', 0)
                special_damage_type = special.get('damage_type', tower_data.get('damage_type', 'normal'))
            elif effect == 'black_hole':
                special_damage = special.get('black_hole_damage', 0)
                special_damage_type = special.get('damage_type', tower_data.get('damage_type', 'normal'))

        # Use special damage if available, otherwise use regular damage
        if special_damage and special_damage > 0:
            damage_str = f"{special_damage}"
            damage_type = special_damage_type or tower_data.get('damage_type', 'normal')
        else:
            damage_min = tower_data.get('damage_min', 0)
            damage_max = tower_data.get('damage_max', damage_min)
            damage_str = f"{damage_min}-{damage_max}" if damage_min != damage_max else f"{damage_min}"
            damage_type = tower_data.get('damage_type', 'normal')
        
        tooltip_lines.append(f"- Damage: {damage_str}")

        damage_type_info = self.damage_type_data.get(damage_type, {})
        damage_desc = damage_type_info.get("description", "")
        tooltip_lines.append(f"- Type: {damage_type.capitalize()} ({damage_desc})")

        attack_interval = tower_data.get('attack_interval')
        attack_speed_stat = tower_data.get('attack_speed')
        if attack_speed_stat:
            tooltip_lines.append(f"- Attack Speed: {attack_speed_stat:.2f}/sec")
        elif attack_interval and attack_interval > 0 and attack_interval < 999:
            tooltip_lines.append(f"- Attack Speed: {(1.0 / attack_interval):.2f}/sec (Interval: {attack_interval:.2f}s)")

        range_val = tower_data.get('range', 0)
        range_min = tower_data.get('range_min', 0)
        range_str = f"{range_val}"
        if range_min > 0:
            range_str += f" (Min: {range_min})"
        tooltip_lines.append(f"- Range: {range_str}")

        targets = tower_data.get('targets', [])
        if targets:
            tooltip_lines.append(f"- Targets: {', '.join(t.capitalize() for t in targets)}")

        crit_chance = tower_data.get('critical_chance', 0.0)
        crit_multi = tower_data.get('critical_multiplier', 1.0)
        if crit_chance > 0:
            tooltip_lines.append(f"- Crit: {crit_chance*100:.0f}% chance for x{crit_multi:.1f} damage")

        tooltip_lines.append("")
        tooltip_lines.append("<b>Attack Modifiers:</b>")

        attack_type = tower_data.get('attack_type', 'none')
        tooltip_lines.append(f"- Attack Type: {attack_type.capitalize()}")

        proj_speed = tower_data.get('projectile_speed')
        if proj_speed is not None:
            tooltip_lines.append(f"- Projectile Speed: {proj_speed}")

        splash = tower_data.get('splash_radius')
        if splash is not None and splash > 0:
            tooltip_lines.append(f"- Splash Radius: {splash}")

        bounce = tower_data.get('bounce', 0)
        if bounce > 0:
            bounce_range = tower_data.get('bounce_range', 'N/A')
            bounce_falloff = tower_data.get('bounce_damage_falloff', 'N/A')
            falloff_str = f"{bounce_falloff*100:.0f}%" if isinstance(bounce_falloff, (int, float)) else str(bounce_falloff)
            tooltip_lines.append(f"- Bounces: {bounce} times (Range: {bounce_range}, Falloff: {falloff_str})")

        pierce = tower_data.get('pierce_adjacent', 0)
        if pierce > 0:
            tooltip_lines.append(f"- Pierces: {pierce} adjacent targets")

        special_data = tower_data.get('special')
        if special_data and isinstance(special_data, dict):
            tooltip_lines.append("")
            tooltip_lines.append("<b>Special Ability:</b>")
            special_desc = special_data.get('description')
            if special_desc:
                tooltip_lines.append(f"<i>{special_desc}</i>")
            else:
                effect_name = special_data.get('effect')
                if effect_name:
                    tooltip_lines.append(f"Effect: {effect_name}")

            known_params = {
                "duration": "Duration", "interval": "Interval", "slow_percentage": "Slow",
                "aura_radius": "Aura Radius", "pulse_damage": "Pulse Damage", "dot_damage": "DoT Damage",
                "stun_duration": "Stun Duration", "chance_percent": "Chance", "pellets": "Pellets", 
                "crit_splash_multiplier": "Crit Splash Mult", "chain_targets": "Chain Targets",
                "gold_amount": "Gold Amount", "reduction_amount": "Reduction", "max_stacks": "Max Stacks"
            }
            for key, label in known_params.items():
                if key in special_data:
                    value = special_data[key]
                    unit = "%" if "percent" in key or "slow" in key else ("s" if "duration" in key or "interval" in key else "")
                    tooltip_lines.append(f"- {label}: {value}{unit}")

        return "<br>".join(tooltip_lines)
        
    def refresh_selector(self):
        """Refresh the entire tower selector - useful for debugging or when issues occur."""
        # Recreate all buttons to ensure they're properly positioned and functional
        # Clear existing buttons
        for button in self.tower_buttons.values():
            button.kill()
        self.tower_buttons.clear()
        for img in self.tower_images.values():
            try:
                img.kill()
            except Exception:
                pass
        self.tower_images.clear()

        # Clear highlights too
        for highlight in self.selected_highlights.values():
            try:
                highlight.kill()
            except Exception:
                pass
        self.selected_highlights.clear()
        
        # Recreate buttons
        self.create_icon_buttons()
        
        # Update button states and restore selection highlight if needed
        self.update_button_states()
        if self.selected_tower:
            self.update_selection_highlights(self.selected_tower)
        
    def update_button_states(self):
        """Update button states based on money and tower limits."""
        for tower_id, button in self.tower_buttons.items():
            tower_data = self.available_towers.get(tower_id)
            if tower_data:
                can_afford = self.money >= tower_data['cost']
                tower_limit = tower_data.get('limit')
                current_count = self.tower_counts.get(tower_id, 0)
                at_limit = tower_limit is not None and current_count >= tower_limit
                
                # Update button state - ensure buttons are always enabled for hover/selection
                # Only disable if at tower limit, but keep enabled for money issues (sound will play)
                if at_limit:
                    button.disable()
                else:
                    button.enable()  # Always enable for hover/interaction, even if can't afford
