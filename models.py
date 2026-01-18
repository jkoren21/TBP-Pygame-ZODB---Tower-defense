from persistent import Persistent
from persistent.mapping import PersistentMapping
from persistent.list import PersistentList
from BTrees.OOBTree import OOBTree


def _to_persistent(obj):
    
    if isinstance(obj, PersistentMapping) or isinstance(obj, PersistentList):
        return obj
    if isinstance(obj, dict):
        pm = PersistentMapping()
        for k, v in obj.items():
            pm[k] = _to_persistent(v)
        return pm
    if isinstance(obj, list):
        pl = PersistentList()
        pl.extend([_to_persistent(x) for x in obj])
        return pl
    return obj


class PlayerProfile(Persistent):
    def __init__(self, username: str):
        self.username = username
        self.stats = PersistentMapping({
            "games_played": 0,
            "wins": 0,
            "total_kills": 0,
        })
        self.best_score_by_level = OOBTree()
        self.runs = PersistentList()

        
        self.saved_game = None

    def _ensure_saved_game_field(self):
        
        if not hasattr(self, "saved_game"):
            self.saved_game = None

    def has_saved_game(self) -> bool:
        return getattr(self, "saved_game", None) is not None

    def save_game(self, save_dict):
        self._ensure_saved_game_field()
        self.saved_game = save_dict  # presliikavanje save-a

    def clear_saved_game(self):
        self._ensure_saved_game_field()
        self.saved_game = None

    def record_run(self, ts_iso: str, level: int, score: int, kills: int, won: bool):
        self.stats["games_played"] += 1
        if won:
            self.stats["wins"] += 1
        self.stats["total_kills"] += kills

        prev = self.best_score_by_level.get(level, 0)
        if score > prev:
            self.best_score_by_level[level] = score

        self.runs.append(PersistentMapping({
            "ts": ts_iso,
            "level": int(level),
            "score": int(score),
            "kills": int(kills),
            "won": bool(won),
        }))


class GameState(Persistent):
    def __init__(self):
        self.profiles = OOBTree()

    def get_or_create_profile(self, username: str) -> PlayerProfile:
        p = self.profiles.get(username)
        if p is None:
            p = PlayerProfile(username)
            self.profiles[username] = p
        return p
