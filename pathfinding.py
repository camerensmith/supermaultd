def find_path(start, end, obstacles):
    # Simple straight-line path for now
    path = [start]
    while start[1] < end[1]:
        start = (start[0], start[1] + 1)
        path.append(start)
    return path
