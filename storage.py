from ZODB import DB
from ZODB.FileStorage import FileStorage
import transaction


def open_storage(path="game_data.fs"):
    storage = FileStorage(path)
    db = DB(storage)
    conn = db.open()
    root = conn.root()
    return db, conn, root


def commit():
    transaction.commit()
