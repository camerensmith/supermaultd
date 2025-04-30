import pygame
import pygame_gui
import os
import json
# Remove direct WIDTH/HEIGHT import for layout
# from config import WIDTH, HEIGHT 

class RaceSelector:
    def __init__(self, game_data, manager, screen_width, screen_height, click_sound, initial_wave_mode):
        """
        Initialize the race selector UI.
        
        :param game_data: Dictionary containing all game definitions
        :param manager: pygame_gui UIManager instance
        :param screen_width: Actual width of the screen
        :param screen_height: Actual height of the screen
        :param click_sound: Loaded pygame.mixer.Sound object for clicks
        :param initial_wave_mode: 'classic' or 'advanced'
        """
        self.game_data = game_data
        self.manager = manager
        self.selected_races = []
        self.screen_width = screen_width   # Store dimensions
        self.screen_height = screen_height # Store dimensions
        self.click_sound = click_sound     # Store sound effect
        self.wave_mode = initial_wave_mode  # Store wave mode
        
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
            #print(f"Error loading title image: {e}")
            pass
        
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
            pass
            #print(f"Error creating placeholder image: {e}")
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
                    #print(f"Error loading image for race '{race_id}' at {image_path}: {e}")
                    pass
            
            if loaded_image:
                # Calculate scaled size preserving aspect ratio
                original_width, original_height = loaded_image.get_size()
                ratio = min(max_img_width / original_width, max_img_height / original_height)
                scaled_width = int(original_width * ratio)
                scaled_height = int(original_height * ratio)
                
                try:
                    scaled_image = pygame.transform.smoothscale(loaded_image, (scaled_width, scaled_height))
                    self.race_images[race_id] = scaled_image
                    #print(f"Loaded and scaled image for race '{race_id}'")
                except Exception as e:
                    #print(f"Error scaling image for race '{race_id}': {e}")
                    self.race_images[race_id] = None # Fallback if scaling fails
            else:
                #print(f"Image not found for race '{race_id}' at {image_path}")
                self.race_images[race_id] = None # Store None if not found/loaded
        
        # --- Load Combined Race Data --- 
        self.combined_race_lookup = {}
        self.combined_race_images = {}
        images_base_path = os.path.join("assets", "images")
        
        # <<< Robust Path Construction >>>
        # Get the directory where this race_selector.py file is located
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to the project root (supermaultd), then into data
        project_root = os.path.dirname(current_script_dir) # This should be supermaultd dir
        data_dir = os.path.join(project_root, 'data')
        combined_data_path = os.path.join(data_dir, "combined_races.json")
        # <<< End Robust Path Construction >>>
        
        try:
            with open(combined_data_path, 'r') as f:
                combined_data = json.load(f)
            #print(f"Loaded combined race data from: {combined_data_path}")
            
            for combo_info in combined_data:
                base_races = combo_info.get("races", [])
                if len(base_races) == 2: # Ensure it's a pair
                    # Create a consistent key by sorting race IDs
                    combo_key = tuple(sorted(base_races))
                    self.combined_race_lookup[combo_key] = combo_info
                    #print(f"  - Processed combination for: {combo_key}")
                    
                    # Load the combined image
                    img_filename = combo_info.get("combined_image")
                    if img_filename:
                        img_path = os.path.join(images_base_path, img_filename)
                        try:
                            loaded_image = pygame.image.load(img_path).convert_alpha()
                            # Reuse scaling logic from base images
                            max_img_width = 300
                            max_img_height = 300
                            original_width, original_height = loaded_image.get_size()
                            ratio = min(max_img_width / original_width, max_img_height / original_height)
                            scaled_width = int(original_width * ratio)
                            scaled_height = int(original_height * ratio)
                            scaled_image = pygame.transform.smoothscale(loaded_image, (scaled_width, scaled_height))
                            self.combined_race_images[combo_key] = scaled_image
                            #print(f"    - Loaded combined image: {img_filename}")
                        except Exception as e:
                            #print(f"    - Error loading/scaling combined image '{img_filename}' for {combo_key}: {e}")
                            self.combined_race_images[combo_key] = None # Store None on error
                    else:
                         self.combined_race_images[combo_key] = None # Store None if no image specified
        except FileNotFoundError:
            #print(f"Warning: Combined race data file not found: {combined_data_path}")
            pass
        except json.JSONDecodeError as e:
            #print(f"Error decoding JSON from {combined_data_path}: {e}")
            pass
        except Exception as e:
            #print(f"Error processing combined race data: {e}")
            pass
        # --- End Combined Race Data Loading --- 
        
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
        # Set initial title based on the mode
        if self.wave_mode == 'advanced':
            self.title_label.set_text('Select Two Races')
        else:
            self.title_label.set_text('Select Your Race') # Default for classic or other modes
        
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

    def set_selection_mode(self, new_mode):
        if new_mode in ['classic', 'advanced', 'wild'] and self.wave_mode != new_mode:
            #print(f"[RaceSelector] Mode changed to: {new_mode}")
            self.wave_mode = new_mode
            # Clear current selection when mode changes
            self.selected_races = []
            # Unselect all buttons visually
            for _, btn in self.race_buttons:
                btn.unselect()
            # Update description/image to default/placeholder
            self.description_text_box.set_text("Select a race...")
            display_image = self.placeholder_image
            if display_image:
                self.race_image_display.set_image(display_image)
            else:
                self.race_image_display.set_image(pygame.Surface((1,1)))
            
            # Update the title label based on the new mode
            if self.title_label: # Check if label exists
                if self.wave_mode == 'advanced' or self.wave_mode == 'wild':
                    self.title_label.set_text('Select Two Races')
                else:
                    self.title_label.set_text('Select Your Race')

    def handle_event(self, event):
        """Handle pygame_gui events, considering wave_mode"""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            button_pressed = event.ui_element
            clicked_race_id = None

            # Check if a race button was clicked
            for race_id, button in self.race_buttons:
                if button_pressed == button:
                    clicked_race_id = race_id
                    break

            if clicked_race_id:
                if self.click_sound: self.click_sound.play()
                print(f"Clicked race: {clicked_race_id}")

                # --- Mode-Dependent Selection Logic ---
                if self.wave_mode == 'classic':
                    # Classic mode: Select only one
                    if clicked_race_id not in self.selected_races:
                        self.selected_races = [clicked_race_id]
                        # Update visuals
                        for r_id, btn in self.race_buttons:
                            if r_id == clicked_race_id:
                                btn.select()
                            else:
                                btn.unselect()
                    # If already selected, do nothing (classic mode doesn't deselect)
                elif self.wave_mode == 'advanced' or self.wave_mode == 'wild':
                    # Advanced/Wild mode: Select up to two
                    if clicked_race_id in self.selected_races:
                        # Deselect if already selected
                        self.selected_races.remove(clicked_race_id)
                        button_pressed.unselect() # Unselect the clicked button
                    elif len(self.selected_races) < 2:
                        # Select if less than 2 are already selected
                        self.selected_races.append(clicked_race_id)
                        button_pressed.select() # Select the clicked button
                    else:
                        # Limit reached, maybe provide feedback (e.g., sound)
                        print("[RaceSelector] Cannot select more than 2 races in Advanced mode.")
                # --- End Mode-Dependent Logic ---

                # --- Update Description & Image (Check for Combination) ---
                description_to_show = "Select a race..."
                image_to_show = self.placeholder_image
                combination_found = False

                if (self.wave_mode == 'advanced' or self.wave_mode == 'wild') and len(self.selected_races) == 2:
                    # Try to find a combined entry
                    combo_key = tuple(sorted(self.selected_races))
                    combo_data = self.combined_race_lookup.get(combo_key)
                    if combo_data:
                        description_to_show = combo_data.get("combined_description", "Combined description missing.")
                        image_to_show = self.combined_race_images.get(combo_key) # Get pre-loaded image
                        combination_found = True
                        print(f"Displaying combined info for: {combo_key}")

                # Fallback if no combination found or not in advanced/2 selected mode
                if not combination_found and self.selected_races:
                    first_selected_race = self.selected_races[0]
                    description_to_show = self.race_descriptions.get(first_selected_race, "Description not found.")
                    image_to_show = self.race_images.get(first_selected_race)
                
                # Final update to UI elements
                self.description_text_box.set_text(description_to_show)
                if not image_to_show: image_to_show = self.placeholder_image # Ensure placeholder if needed
                if image_to_show: self.race_image_display.set_image(image_to_show)
                else: self.race_image_display.set_image(pygame.Surface((1,1))) # Ultimate fallback
                # --- END UPDATE --- 

            elif button_pressed == self.confirm_button:
                # Confirmation logic is handled in game.py
                pass 

        # Process other events AFTER our button logic
        self.manager.process_events(event)
        return False # Indicate event was handled locally
        
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
        
    def get_selected_races(self):
        """Get the currently selected list of race IDs"""
        return self.selected_races

    def update_button_visuals(self):
        """Updates the visual state of all race buttons based on current selections."""
        for race_id, button in self.race_buttons:
            if race_id in self.selected_races:
                button.select() # Use pygame_gui select/unselect for visual state
            else:
                button.unselect()
        # No need to rebuild here unless object_id changes drastically

    def kill(self):
        """Remove the race selector panel and its elements from the UI manager."""
        if self.panel:
            self.panel.kill()
            #print("RaceSelector panel killed.") 