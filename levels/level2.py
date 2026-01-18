# levels/level2.py

def get_level_2():

    path_grid = [
        (0, 2), (4, 2),
        (4, 9), (7, 9),
        (7, 4), (10, 4),
        (10, 10), (15, 10)
    ]
    return {
        "id": 2,
        "name": "Level 2: Zig-Zag Canyon",
        "path_grid": path_grid,
        "campaign_waves": 7,
        "duration_text": "Campaign: ~7 waves (4-7 min)",
        "difficulty_text": "Difficulty: Medium",
    }
