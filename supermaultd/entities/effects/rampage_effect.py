import math

class RampageEffect:
    """Manages the state and logic for a rampage/stacking damage effect."""

    def __init__(self, tower, special_data):
        """
        Initialize the RampageEffect handler.

        :param tower: The Tower instance this effect belongs to.
        :param special_data: The dictionary containing the effect parameters 
                             (e.g., damage_per_stack, max_stacks, decay_duration).
        """
        self.tower = tower # Keep a reference if needed, e.g., for tower ID in logs
        self.damage_per_stack = special_data.get("damage_per_stack", 0)
        self.max_stacks = special_data.get("max_stacks", 1) # Default to 1 if missing?
        self.decay_duration = special_data.get("decay_duration", 5.0) # Default decay time
        
        self.stacks = 0
        self.last_attack_time = 0.0 # Time the tower last successfully attacked
        
        # print(f"DEBUG: RampageEffect initialized for tower {getattr(tower, 'tower_id', '?')} - Dmg/Stack: {self.damage_per_stack}, Max: {self.max_stacks}, Decay: {self.decay_duration}s")

    def update(self, current_time):
        """
        Checks for stack decay based on time since the last attack.
        Should be called every frame.
        """
        # Check decay only if there are active stacks
        if self.stacks > 0:
            time_since_last_attack = current_time - self.last_attack_time
            if time_since_last_attack > self.decay_duration:
                # Decay time exceeded, reset stacks to 0
                # print(f"DEBUG: Rampage stacks decayed to 0 (Time since last: {time_since_last_attack:.2f}s > Decay: {self.decay_duration}s)")
                self.stacks = 0

    def record_attack(self, current_time):
        """
        Records that an attack occurred, incrementing stacks.
        Handles the initial stack gain.
        Should be called *after* a successful attack hits.
        
        :param current_time: The current game time in seconds.
        """
        if self.stacks == 0:
            # If stacks were 0 (either initial state or after decay), start at 1
            self.stacks = 1
            # print(f"DEBUG: Rampage stacks started at 1")
        else:
            # Otherwise, increment stacks up to the max
            self.stacks = min(self.stacks + 1, self.max_stacks)
            # print(f"DEBUG: Rampage stacks incremented to {self.stacks}")

        # Always update the last attack time when an attack is recorded
        self.last_attack_time = current_time

    def get_bonus_damage(self):
        """Calculate the current bonus damage based on active stacks."""
        return self.stacks * self.damage_per_stack

    def get_current_stacks(self):
        """Return the current number of active stacks."""
        return self.stacks 