import pygame
import pygame_gui
from config import WIDTH, HEIGHT, GRID_SIZE
from pygame_gui.elements import UIButton, UILabel
from pygame_gui.elements import UIScrollingContainer # Import the scrolling container
import os

class TowerSelector:
    def __init__(self, available_towers, tower_assets, manager, initial_money, panel_rect, damage_type_data, click_sound):
        """
        Initialize the tower selection UI panel within the provided rect.
        
        :param available_towers: Dictionary of available towers for the selected race
        :param tower_assets: Instance of TowerAssets
        :param manager: pygame_gui UIManager instance
        :param initial_money: The starting money amount from the game scene
        :param panel_rect: The pygame.Rect defining the panel's position and size
        :param damage_type_data: Dictionary containing descriptions for damage types
        :param click_sound: Loaded pygame.mixer.Sound object for clicks
        """
        self.available_towers = available_towers
        self.tower_assets = tower_assets 
        self.manager = manager
        self.selected_tower = None
        self.tower_buttons = {} 
        self.tower_info_boxes = {}
        self.tower_images = {}
        self.expanded_tower_id = None
        self.money = initial_money
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
        
        # Create the main panel using the provided rect
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=self.panel_rect,
            manager=self.manager
        )
        
        # --- Internal Layout (relative to panel) ---
        current_y = 10 # Start Y for internal elements

        # Add title 
        title_height = 30
        title_rect = pygame.Rect(10, current_y, self.panel_width - 20, title_height)
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=title_rect,
            text='Select Tower',
            manager=self.manager,
            container=self.panel
        )
        current_y += title_height + 5
        
        # Add money display 
        money_height = 30
        money_rect = pygame.Rect(10, current_y, self.panel_width - 20, money_height)
        self.money_label = pygame_gui.elements.UILabel(
            relative_rect=money_rect,
            text=f'Money: ${self.money}',
            manager=self.manager,
            container=self.panel,
            object_id="#money_label"
        )
        current_y += money_height + 15
        
        # --- Create Scrolling Container for Buttons ---
        # Calculate remaining height for the scroll container
        scroll_container_top = current_y
        scroll_container_height = self.panel_height - scroll_container_top - 10 # Add some bottom padding
        scroll_container_rect = pygame.Rect(10, scroll_container_top, self.panel_width - 20, scroll_container_height)
        
        self.button_scroll_container = UIScrollingContainer(
            relative_rect=scroll_container_rect,
            manager=self.manager,
            container=self.panel
        )
        # --- End Scrolling Container ---
        
        # Store starting Y for buttons
        self.button_start_y = current_y 

        # Precompute tooltip HTML once per tower for faster rebuilds
        for tower_id, tower_data in self.available_towers.items():
            if tower_id not in self._tooltip_html_cache:
                self._tooltip_html_cache[tower_id] = self._build_tooltip_html(tower_data)

        # Create buttons
        self.create_tower_buttons()
        
    def create_tower_buttons(self):
        """Create buttons inside the scrolling container"""
        # Use scroll container's width for calculations
        content_width = self.button_scroll_container.get_container().get_rect().width # Width of the scrollable area
        # Adjust button height for image + name only
        image_size = 60 # Slightly smaller image to fit better
        padding = 10 
        button_height = image_size + padding * 2 # Height based on image + padding 
        text_x_rel = image_size + 15 # Text starts after image + padding
        text_width = content_width - text_x_rel - 10 
        line_height = 20 # Approx height of the name label font
        
        # Start Y position relative to the scroll container
        current_y = padding 

        for index, (tower_id, tower_data) in enumerate(self.available_towers.items()):
            # --- DEBUG PRINT --- 
            #print(f"[TowerSelector Debug] ID: {tower_id}, Data: {tower_data}") 
            # --- END DEBUG --- 

            # Calculate top-left position for this tower entry
            entry_x = 10
            # Button covers the whole entry area, relative to panel
            #button_rect = pygame.Rect(entry_x, current_y, content_width, button_height)

            # --- Use cached tooltip HTML ---
            tooltip_text = self._tooltip_html_cache.get(tower_id)
            # Fallback safety: build on demand if missing
            if tooltip_text is None:
                tooltip_text = self._build_tooltip_html(tower_data)
                self._tooltip_html_cache[tower_id] = tooltip_text

            # Position button relative to the scroll container
            button_rect = pygame.Rect(0, current_y, content_width, button_height) # X=0 for scroll container
            # Button label uses tower name
            name = tower_data.get('name', 'N/A')
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=name,
                manager=self.manager,
                container=self.button_scroll_container.get_container(), # Get the actual container surface
                tool_tip_text=tooltip_text,
                object_id=f"#tower_button_{tower_id}"
            )
            self.tower_buttons[tower_id] = button

            # Image
            preview_image = self.tower_assets.get_tower_preview(tower_id)
            if preview_image:
                # Ensure opaque
                if preview_image.get_alpha() is None: preview_image = preview_image.convert_alpha()
                else: preview_image = preview_image.copy()
                preview_image.set_alpha(255)

                image_rel_x = 5 # Padding from left button edge (inside scroll area)
                image_rel_y = (button_height - image_size) // 2 # Center vertically within button area
                # Image position is relative to the scroll container
                image_rect = pygame.Rect(image_rel_x, button_rect.top + image_rel_y, image_size, image_size)
                img_elem = pygame_gui.elements.UIImage(
                    relative_rect=image_rect, 
                    image_surface=preview_image, 
                    manager=self.manager, 
                    container=self.button_scroll_container.get_container() # Add to scroll container
                )
                # Track image element for cleanup on rebuilds
                self.tower_images[tower_id] = img_elem

            # --- Expanded Info Box (accordion style) ---
            if self.expanded_tower_id == tower_id:
                inline_html = tooltip_text
                # Estimate height by line count with caps
                approx_lines = inline_html.count('<br>') + 1
                line_px = 18
                padding_px = 12
                max_height = 420
                info_height_local = min(max_height, padding_px + approx_lines * line_px)

                info_rect = pygame.Rect(0, button_rect.bottom + 4, content_width, info_height_local)
                info_box = pygame_gui.elements.UITextBox(
                    html_text=inline_html,
                    relative_rect=info_rect,
                    manager=self.manager,
                    container=self.button_scroll_container.get_container(),
                    object_id='#tower_info_inline'
                )
                self.tower_info_boxes[tower_id] = info_box
                current_y += button_height + padding + info_height_local + padding
            else:
                current_y += button_height + padding
            
        # --- Set Scrollable Area Size --- 
        # After loop, current_y holds the total height needed + final padding
        total_content_height = current_y
        # Set the virtual size of the scrollable area
        self.button_scroll_container.set_scrollable_area_dimensions((content_width, total_content_height))
        # --- End Set Size --- 

    def handle_event(self, event):
        """Handle pygame_gui events"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            clicked_button = event.ui_element
            clicked_tower_id = None
            
            # Find which tower button was clicked
            for tower_id, button in self.tower_buttons.items():
                if clicked_button == button:
                    clicked_tower_id = tower_id
                    break

            if clicked_tower_id:
                if self.click_sound: self.click_sound.play() # Play click sound
                
                tower_data = self.available_towers.get(clicked_tower_id)
                can_afford = tower_data and self.money >= tower_data['cost']

                # Toggle accordion expansion independent of affordability
                if self.expanded_tower_id == clicked_tower_id:
                    self.expanded_tower_id = None
                else:
                    self.expanded_tower_id = clicked_tower_id

                # Rebuild buttons and info boxes to reflect new layout
                for button in list(self.tower_buttons.values()):
                    try:
                        button.kill()
                    except Exception:
                        pass
                self.tower_buttons.clear()
                for info in list(self.tower_info_boxes.values()):
                    try:
                        info.kill()
                    except Exception:
                        pass
                self.tower_info_boxes.clear()
                for img in list(self.tower_images.values()):
                    try:
                        img.kill()
                    except Exception:
                        pass
                self.tower_images.clear()
                self.create_tower_buttons()

                if clicked_tower_id == self.selected_tower:
                    # Clicked the already selected tower - Deselect it
                    self.selected_tower = None
                    clicked_button.unselect() # Visually deselect
                elif can_afford:
                    # Clicked a new, affordable tower - Select it
                    self.selected_tower = clicked_tower_id
                    # Visually select the new one and deselect others
                    for t_id, btn in self.tower_buttons.items():
                        if t_id == clicked_tower_id:
                            btn.select()
                        else:
                            btn.unselect()
                else:
                    # Clicked an unaffordable tower - Play sound
                    if self.cannot_select_sound: 
                        self.cannot_select_sound.play()
                    # Ensure nothing is selected internally if can't afford
                    if self.selected_tower == clicked_tower_id:
                         self.selected_tower = None
                         clicked_button.unselect()
        
        # Let the manager process the event regardless of our handling
        self.manager.process_events(event)

    def update(self, time_delta):
        """Update the UI manager"""
        self.manager.update(time_delta)
        
    def draw(self, surface):
        """Draw the UI elements"""
        self.manager.draw_ui(surface)
        
    def get_selected_tower(self):
        """Get the currently selected tower ID"""
        return self.selected_tower
        
    def clear_selection(self):
        """Clear the current tower selection and visually deselect all buttons."""
        self.selected_tower = None
        # Loop through buttons and call unselect()
        for button in self.tower_buttons.values():
            button.unselect()
        print("Cleared tower selection")
        
    def update_money(self, new_amount):
        """Update the money display and refresh button states"""
        self.money = new_amount
        self.money_label.set_text(f'Money: ${self.money}')
        self.update_button_states()  # Refresh button states based on new money amount 

    def update_tower_counts(self, tower_counts):
        """Update the tower counts and refresh button states."""
        self.tower_counts = tower_counts
        self.update_button_states()

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

        damage_min = tower_data.get('damage_min', 0)
        damage_max = tower_data.get('damage_max', damage_min)
        damage_str = f"{damage_min}-{damage_max}" if damage_min != damage_max else f"{damage_min}"
        tooltip_lines.append(f"- Damage: {damage_str}")

        damage_type = tower_data.get('damage_type', 'normal')
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
        for info in self.tower_info_boxes.values():
            try:
                info.kill()
            except Exception:
                pass
        self.tower_info_boxes.clear()
        for img in self.tower_images.values():
            try:
                img.kill()
            except Exception:
                pass
        self.tower_images.clear()

        # Recreate buttons
        self.create_tower_buttons()
        
        # Update button states
        self.update_button_states()
        
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
                
                # Update button text to show limit if applicable
                if tower_limit is not None:
                    button.set_text(f"{tower_data['name']} ({current_count}/{tower_limit})")
                else:
                    button.set_text(tower_data['name']) 