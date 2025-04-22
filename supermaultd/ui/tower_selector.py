import pygame
import pygame_gui
from config import WIDTH, HEIGHT, GRID_SIZE
from pygame_gui.elements import UIButton, UILabel
from pygame_gui.elements import UIScrollingContainer # Import the scrolling container

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
        self.money = initial_money
        self.damage_type_data = damage_type_data # Store damage type data
        self.click_sound = click_sound # Store sound effect
        
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
            print(f"[TowerSelector Debug] ID: {tower_id}, Data: {tower_data}") 
            # --- END DEBUG --- 

            # Calculate top-left position for this tower entry
            entry_x = 10
            # Button covers the whole entry area, relative to panel
            #button_rect = pygame.Rect(entry_x, current_y, content_width, button_height)

            # --- Generate Comprehensive Tooltip Text ---
            tooltip_lines = []

            # Basic Info
            name = tower_data.get('name', 'N/A')
            cost = tower_data.get('cost', 0)
            tooltip_lines.append(f"<b>{name}</b>")
            tooltip_lines.append(f"Cost: ${cost}")
            grid_w = tower_data.get('grid_width', 1)
            grid_h = tower_data.get('grid_height', 1)
            if grid_w > 1 or grid_h > 1:
                tooltip_lines.append(f"Size: {grid_w}x{grid_h}")

            tooltip_lines.append("") # Spacer
            tooltip_lines.append("<b>Stats:</b>")

            # Damage
            damage_min = tower_data.get('damage_min', 0)
            damage_max = tower_data.get('damage_max', damage_min)
            damage_str = f"{damage_min}-{damage_max}" if damage_min != damage_max else f"{damage_min}"
            tooltip_lines.append(f"- Damage: {damage_str}")

            # Damage Type
            damage_type = tower_data.get('damage_type', 'normal')
            damage_type_info = self.damage_type_data.get(damage_type, {})
            damage_desc = damage_type_info.get("description", "")
            tooltip_lines.append(f"- Type: {damage_type.capitalize()} ({damage_desc})")

            # Attack Speed
            attack_interval = tower_data.get('attack_interval')
            attack_speed_stat = tower_data.get('attack_speed') # Check for explicit speed first
            if attack_speed_stat:
                tooltip_lines.append(f"- Attack Speed: {attack_speed_stat:.2f}/sec")
            elif attack_interval and attack_interval > 0 and attack_interval < 999:
                tooltip_lines.append(f"- Attack Speed: {(1.0 / attack_interval):.2f}/sec (Interval: {attack_interval:.2f}s)")

            # Range
            range_val = tower_data.get('range', 0)
            range_min = tower_data.get('range_min', 0)
            range_str = f"{range_val}"
            if range_min > 0:
                range_str += f" (Min: {range_min})"
            tooltip_lines.append(f"- Range: {range_str}")

            # Targets
            targets = tower_data.get('targets', [])
            if targets:
                tooltip_lines.append(f"- Targets: {', '.join(t.capitalize() for t in targets)}")

            # Critical Strike
            crit_chance = tower_data.get('critical_chance', 0.0)
            crit_multi = tower_data.get('critical_multiplier', 1.0)
            if crit_chance > 0:
                tooltip_lines.append(f"- Crit: {crit_chance*100:.0f}% chance for x{crit_multi:.1f} damage")

            tooltip_lines.append("") # Spacer
            tooltip_lines.append("<b>Attack Modifiers:</b>")

            # Attack Type
            attack_type = tower_data.get('attack_type', 'none')
            tooltip_lines.append(f"- Attack Type: {attack_type.capitalize()}")

            # Projectile Speed
            proj_speed = tower_data.get('projectile_speed')
            if proj_speed is not None:
                tooltip_lines.append(f"- Projectile Speed: {proj_speed}")

            # Splash
            splash = tower_data.get('splash_radius')
            if splash is not None and splash > 0:
                tooltip_lines.append(f"- Splash Radius: {splash}")

            # Bounce
            bounce = tower_data.get('bounce', 0)
            if bounce > 0:
                bounce_range = tower_data.get('bounce_range', 'N/A')
                bounce_falloff = tower_data.get('bounce_damage_falloff', 'N/A')
                tooltip_lines.append(f"- Bounces: {bounce} times (Range: {bounce_range}, Falloff: {bounce_falloff*100:.0f}%) ")

            # Pierce
            pierce = tower_data.get('pierce_adjacent', 0)
            if pierce > 0:
                tooltip_lines.append(f"- Pierces: {pierce} adjacent targets")

            # Special Block
            special_data = tower_data.get('special')
            if special_data and isinstance(special_data, dict):
                tooltip_lines.append("") # Spacer
                tooltip_lines.append("<b>Special Ability:</b>")
                special_desc = special_data.get('description')
                if special_desc:
                    tooltip_lines.append(f"<i>{special_desc}</i>")
                else:
                    # Try to display effect name if no description
                    effect_name = special_data.get('effect')
                    if effect_name:
                        tooltip_lines.append(f"Effect: {effect_name}")
                
                # Add known parameters (add more as needed)
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

            # Join lines with HTML line breaks
            tooltip_text = "<br>".join(tooltip_lines)
            # --- End Comprehensive Tooltip --- 

            # Position button relative to the scroll container
            button_rect = pygame.Rect(0, current_y, content_width, button_height) # X=0 for scroll container
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
                pygame_gui.elements.UIImage(
                    relative_rect=image_rect, 
                    image_surface=preview_image, 
                    manager=self.manager, 
                    container=self.button_scroll_container.get_container() # Add to scroll container
                )

            # Update Y for next button (relative to scroll container)
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
            # Check which tower button container was pressed
            for tower_id, button in self.tower_buttons.items():
                if event.ui_element == button:
                    if self.click_sound: self.click_sound.play() # Play click sound
                    # Check if player can afford the tower
                    tower_data = self.available_towers.get(tower_id)
                    if tower_data and self.money >= tower_data['cost']:
                        if self.selected_tower == tower_id:
                            self.selected_tower = None
                            print("Deselected tower")
                        else:
                            self.selected_tower = tower_id
                            print(f"[TowerSelector handle_event] Assigned self.selected_tower = {self.selected_tower}") 
                            print(f"Selected tower: {tower_id}")
                    else:
                        # TODO: Add visual feedback (e.g., shake button, red flash?)
                        print("Not enough money to select this tower!")
                    # No return here, let manager process event fully
                    break # Found the button
                    
        self.manager.process_events(event) # Process all events
        
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
        """Clear the current tower selection"""
        self.selected_tower = None
        print("Cleared tower selection")
        
    def update_money(self, new_amount):
        """Update the money display"""
        self.money = new_amount
        self.money_label.set_text(f'Money: ${self.money}') 