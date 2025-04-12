import heapq
from config import *

class Node:
    def __init__(self, x, y, g_cost=float('inf'), h_cost=0, parent=None):
        self.x = x
        self.y = y
        self.g_cost = g_cost  # Cost from start to current node
        self.h_cost = h_cost  # Estimated cost from current node to end
        self.f_cost = g_cost + h_cost  # Total cost
        self.parent = parent
        
    def __lt__(self, other):
        return self.f_cost < other.f_cost

def manhattan_distance(x1, y1, x2, y2):
    """Calculate Manhattan distance between two points"""
    return abs(x1 - x2) + abs(y1 - y2)

def get_neighbors(node, grid, is_air_unit=False):
    """Get valid neighboring nodes, considering unit type."""
    neighbors = []
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up
    
    for dx, dy in directions:
        new_x, new_y = node.x + dx, node.y + dy
        
        # Check if the new position is within grid bounds
        if 0 <= new_x < len(grid[0]) and 0 <= new_y < len(grid):
            # Check cell walkability based on unit type
            is_walkable = False
            if is_air_unit:
                # Air units only care about bounds, ignore cell values (0, 1, 2)
                is_walkable = True
            else: # Ground unit
                # Ground units should ONLY walk on 0 (empty), not 1 (tower) or 2 (restricted)
                if grid[new_y][new_x] == 0:
                    is_walkable = True
                    
            if is_walkable:
                neighbors.append(Node(new_x, new_y))
            
    return neighbors

def find_path(start_x, start_y, end_x, end_y, grid, is_air_unit=False):
    """
    Find a path from start to end using A* algorithm.
    
    :param start_x: Starting x coordinate
    :param start_y: Starting y coordinate
    :param end_x: Ending x coordinate
    :param end_y: Ending y coordinate
    :param grid: 2D grid representing the map (0 = walkable, 1 = obstacle)
    :return: List of (x, y) coordinates representing the path
    """
    start_node = Node(start_x, start_y, g_cost=0)
    end_node = Node(end_x, end_y)
    
    open_set = []
    closed_set = set()
    node_dict = {}  # Keep track of nodes by their coordinates
    
    heapq.heappush(open_set, start_node)
    node_dict[(start_x, start_y)] = start_node
    
    while open_set:
        current = heapq.heappop(open_set)
        
        # Check if we've reached the end
        if current.x == end_x and current.y == end_y:
            path = []
            while current:
                path.append((current.x, current.y))
                current = current.parent
            return path[::-1]  # Reverse the path
            
        closed_set.add((current.x, current.y))
        
        # Check all neighbors
        for neighbor in get_neighbors(current, grid, is_air_unit):
            if (neighbor.x, neighbor.y) in closed_set:
                continue
                
            g_cost = current.g_cost + 1  # Cost to move to neighbor
            
            # Check if we've found a better path to this node
            if (neighbor.x, neighbor.y) in node_dict:
                if g_cost >= node_dict[(neighbor.x, neighbor.y)].g_cost:
                    continue
                node_dict[(neighbor.x, neighbor.y)].g_cost = g_cost
                node_dict[(neighbor.x, neighbor.y)].f_cost = g_cost + node_dict[(neighbor.x, neighbor.y)].h_cost
            else:
                neighbor.g_cost = g_cost
                neighbor.h_cost = manhattan_distance(neighbor.x, neighbor.y, end_x, end_y)
                neighbor.f_cost = g_cost + neighbor.h_cost
                neighbor.parent = current
                node_dict[(neighbor.x, neighbor.y)] = neighbor
                heapq.heappush(open_set, neighbor)
    
    return []  # No path found
