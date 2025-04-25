import pygame
import pygame_gui
import os
# Remove direct WIDTH/HEIGHT import for layout
# from config import WIDTH, HEIGHT 

class RaceSelector:
    def __init__(self, game_data, manager, screen_width, screen_height, click_sound):
        """
        Initialize the race selector UI.
        
        :param game_data: Dictionary containing all game definitions
        :param manager: pygame_gui UIManager instance
        :param screen_width: Actual width of the screen
        :param screen_height: Actual height of the screen
        :param click_sound: Loaded pygame.mixer.Sound object for clicks
        """
        self.game_data = game_data
        self.manager = manager
        self.selected_race = None
        self.screen_width = screen_width   # Store dimensions
        self.screen_height = screen_height # Store dimensions
        self.click_sound = click_sound     # Store sound effect
        
        # Load and scale title image
        title_image_path = os.path.join("assets", "images", "supermaultd.png")
        self.title_image = None
        try:
            title_image = pygame.image.load(title_image_path).convert_alpha()
            # Scale title image to reasonable size (e.g., 400px wide)
            original_width, original_height = title_image.get_size()
            scale_factor = 400 / original_width
            scaled_height = int(original_height * scale_factor)
            self.title_image = pygame.transform.smoothscale(title_image, (400, scaled_height))
        except Exception as e:
            print(f"Error loading title image: {e}")
        
        # Get available races, load descriptions and images
        self.races = list(game_data.get("races", {}).keys())
        self.race_descriptions = {}
        self.race_images = {} # Store loaded & scaled images
        self.placeholder_image = None # Placeholder if race image missing
        max_img_width = 300
        max_img_height = 300
        images_base_path = os.path.join("assets", "images") 
        
        # Try to create a simple placeholder surface
        try:
            self.placeholder_image = pygame.Surface((max_img_width, max_img_height))
            self.placeholder_image.fill((50, 50, 50)) # Dark gray
            # Optional: Draw text on placeholder
            font = pygame.font.Font(None, 24)
            text_surf = font.render("No Image", True, (200, 200, 200))
            text_rect = text_surf.get_rect(center=self.placeholder_image.get_rect().center)
            self.placeholder_image.blit(text_surf, text_rect)
        except Exception as e:
            print(f"Error creating placeholder image: {e}")
            # self.placeholder_image remains None
            
        for race_id in self.races:
            race_info = self.game_data.get("races", {}).get(race_id, {})
            self.race_descriptions[race_id] = race_info.get("description", "No description available.")
            
            image_path = os.path.join(images_base_path, f"{race_id}.png")
            loaded_image = None
            if os.path.isfile(image_path):
                try:
                    loaded_image = pygame.image.load(image_path).convert_alpha()
                except Exception as e:
                    print(f"Error loading image for race '{race_id}' at {image_path}: {e}")
            
            if loaded_image:
                # Calculate scaled size preserving aspect ratio
                original_width, original_height = loaded_image.get_size()
                ratio = min(max_img_width / original_width, max_img_height / original_height)
                scaled_width = int(original_width * ratio)
                scaled_height = int(original_height * ratio)
                
                try:
                    scaled_image = pygame.transform.smoothscale(loaded_image, (scaled_width, scaled_height))
                    self.race_images[race_id] = scaled_image
                    print(f"Loaded and scaled image for race '{race_id}'")
                except Exception as e:
                    print(f"Error scaling image for race '{race_id}': {e}")
                    self.race_images[race_id] = None # Fallback if scaling fails
            else:
                print(f"Image not found for race '{race_id}' at {image_path}")
                self.race_images[race_id] = None # Store None if not found/loaded
        
        # --- Panel sizing and positioning based on screen size ---
        # Make panel wider to accommodate description panel
        left_section_width = 400 # Width for list side
        desc_panel_width = 350 # Width for description side
        h_padding = 10 # Horizontal padding between elements/sections
        v_padding = 10 # Vertical padding
        total_panel_width = left_section_width + (2 * h_padding) + desc_panel_width 
        panel_height = 450 # Increased height slightly more
        
        # Calculate total height including title image
        title_height = self.title_image.get_height() if self.title_image else 0
        total_height = title_height + panel_height + (2 * v_padding)
        
        # Center the entire UI vertically
        total_y = (self.screen_height - total_height) // 2
        
        # Create title image rect if we have a title image
        if self.title_image:
            title_rect = pygame.Rect(
                (self.screen_width - self.title_image.get_width()) // 2,
                total_y,
                self.title_image.get_width(),
                self.title_image.get_height()
            )
            self.title_rect = title_rect
            total_y += title_height + v_padding
        
        # Position main panel below title
        panel_x = (self.screen_width - total_panel_width) // 2
        panel_y = total_y
        panel_rect = pygame.Rect(panel_x, panel_y, total_panel_width, panel_height)
        # --- End Panel sizing --- 
        
        # Create the main panel
        self.panel = pygame_gui.elements.UIPanel(
            relative_rect=panel_rect,
            manager=self.manager,
            object_id='#race_selector_panel'
        )
        
        # --- Left Side Elements (Title, List, Confirm) ---
        
        # Add title (relative to panel, on the left side)
        title_width = left_section_width
        title_height = 30
        self.title_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(h_padding, v_padding, title_width, title_height),
            text='Select Your Race',
            manager=self.manager,
            container=self.panel
        )
        
        # Calculate space for scrolling container and confirm button on the left
        confirm_button_height = 40
        scroll_container_y = v_padding + title_height + v_padding
        available_height_for_scroll = panel_height - scroll_container_y - confirm_button_height - (2 * v_padding) # Below scroll, bottom padding
        scroll_container_rect = pygame.Rect(h_padding, scroll_container_y, 
                                            left_section_width, 
                                            available_height_for_scroll)
        confirm_y = scroll_container_y + available_height_for_scroll + v_padding

        # Create Scrolling Container for Race Buttons on the left
        self.button_scroll_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=scroll_container_rect,
            manager=self.manager,
            container=self.panel
        )

        # Create buttons for each race INSIDE the scrolling container
        self.race_buttons = []
        # Width slightly less than container for padding & scrollbar
        button_width = left_section_width - (2 * h_padding) - 20 
        button_height = 40
        current_scroll_y = h_padding # Start with padding inside scroll container
        
        for index, race_id in enumerate(self.races):
            # Rect is relative to the scroll container
            button_rect = pygame.Rect(h_padding, current_scroll_y, button_width, button_height)
            # Special case for "tac" to ensure it's displayed as "TAC"
            display_name = race_id.replace('_', ' ').title()
            if race_id == "tac":
                display_name = "TAC"
            button = pygame_gui.elements.UIButton(
                relative_rect=button_rect,
                text=display_name,
                manager=self.manager,
                container=self.button_scroll_container.get_container(), 
                object_id=f"#race_button_{race_id}"
            )
            self.race_buttons.append((race_id, button))
            current_scroll_y += button_height + h_padding 
            
        # Set the size of the scrollable area 
        self.button_scroll_container.set_scrollable_area_dimensions((left_section_width - (2*h_padding), current_scroll_y))
            
        # Add confirm button (relative to main panel, below scroll container on left)
        confirm_button_width = left_section_width
        self.confirm_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(h_padding, confirm_y, confirm_button_width, confirm_button_height),
            text='Confirm Selection',
            manager=self.manager,
            container=self.panel,
            object_id='#confirm_button'
        )
        # --- End Left Side Elements ---
        
        # --- Right Side Elements (Description Panel) ---
        desc_panel_x = left_section_width + (2 * h_padding) # Start after left section + padding
        desc_panel_width_actual = desc_panel_width # Use pre-calculated width
        desc_panel_total_height = panel_height - (2 * v_padding) # Available height in panel
        
        # Define Rect for the Image display (Top part)
        # Use max_img_width/height defined earlier, center horizontally
        image_display_width = max_img_width
        image_display_height = max_img_height
        image_rect = pygame.Rect(0, 0, image_display_width, image_display_height)
        image_rect.topleft = (desc_panel_x + (desc_panel_width_actual - image_display_width) // 2, v_padding)
        
        # Create the UIImage element
        initial_image = self.placeholder_image # Start with placeholder
        self.race_image_display = pygame_gui.elements.UIImage(
            relative_rect=image_rect,
            image_surface=initial_image if initial_image else pygame.Surface((1,1)), # Use placeholder or tiny surface
            manager=self.manager,
            container=self.panel
        )
        
        # Define Rect for the Text Box (Below image)
        text_box_y = image_rect.bottom + v_padding
        text_box_height = desc_panel_total_height - image_display_height - (2 * v_padding) # Fill remaining space
        text_box_rect = pygame.Rect(desc_panel_x, text_box_y, desc_panel_width_actual, text_box_height)
        
        # Using a UITextBox for potential multi-line descriptions and wrapping
        self.description_text_box = pygame_gui.elements.UITextBox(
            html_text="Select a race from the list...", 
            relative_rect=text_box_rect,
            manager=self.manager,
            container=self.panel,
            object_id='#description_box'
        )
        # --- End Right Side Elements ---

    def handle_event(self, event):
        """Handle pygame_gui events"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            button_pressed = event.ui_element
            # Check race buttons
            new_selection_made = False
            for race_id, button in self.race_buttons:
                if button_pressed == button:
                    if self.click_sound: self.click_sound.play()
                    self.selected_race = race_id
                    print(f"Selected race: {race_id}")
                    new_selection_made = True

                    # --- UPDATE DESCRIPTION & IMAGE --- 
                    description = self.race_descriptions.get(self.selected_race, "Description not found.")
                    self.description_text_box.set_text(description)

                    display_image = self.race_images.get(self.selected_race)
                    if not display_image:
                         display_image = self.placeholder_image # Fallback to placeholder

                    # Ensure we have something to display before setting
                    if display_image:
                         self.race_image_display.set_image(display_image)
                    else:
                        # Handle case where even placeholder failed (should be rare)
                        self.race_image_display.set_image(pygame.Surface((1,1))) 
                    # --- END UPDATE --- 
                    break # Stop checking race buttons once found

            # --- ADD BUTTON SELECTION VISUAL UPDATE --- 
            if new_selection_made:
                # Iterate through all race buttons again to set selected/unselected state
                for r_id, btn in self.race_buttons:
                    if r_id == self.selected_race:
                        btn.select() # Select the clicked button
                    else:
                        btn.unselect() # Unselect all others
            # --- END BUTTON SELECTION UPDATE ---

            # Check confirm button (No changes needed here)
            elif button_pressed == self.confirm_button:
                # Confirmation logic is handled in game.py based on get_selected_race()
                # We might play a sound here if desired, but state change is external
                pass
        # Process other UI events (needed for tooltips, etc.)
        self.manager.process_events(event)
        return False
        
    def update(self, time_delta):
        """Update the UI manager"""
        self.manager.update(time_delta)
        
    def draw(self, surface):
        """Draw the UI elements"""
        # Draw title image if it exists
        if self.title_image:
            surface.blit(self.title_image, self.title_rect)
        # Draw the UI manager elements
        self.manager.draw_ui(surface)
        
    def get_selected_race(self):
        """Get the currently selected race"""
        return self.selected_race 

    def kill(self):
        """Remove the race selector panel and its elements from the UI manager."""
        if self.panel:
            self.panel.kill()
            print("RaceSelector panel killed.") 