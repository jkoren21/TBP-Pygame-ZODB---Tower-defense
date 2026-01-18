# levels/level3.py

def get_level_3():
    path_grid = [
        (0, 10), (12, 10),
        (12, 3), (15, 3)
    ]
    return {
        "id": 3,
        "name": "Level 3: Long Bridge",
        "path_grid": path_grid,
        "campaign_waves": 8,
        "duration_text": "Campaign: ~8 waves (5-8 min)",
        "difficulty_text": "Difficulty: Hard",
    }
