# levels/level1.py
def get_level_1():
    path_grid = [(0, 5), (3, 5), (3, 2), (8, 2), (8, 9), (13, 9), (13, 6), (15, 6)]
    return {
        "id": 1,
        "name": "Level 1: S-Curve",
        "path_grid": path_grid,
        "campaign_waves": 6,
        "duration_text": "Campaign: ~6 waves (3-6 min)",
        "difficulty_text": "Difficulty: Easy",
    }