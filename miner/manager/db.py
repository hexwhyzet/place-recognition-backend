import datetime
import time
from sqlite3 import connect
from typing import Optional

from miner.manager.models import Pano, PanoType

DATABASE_PATH = "manager.sqlite"

TASK_EXPIRATION = datetime.timedelta(seconds=60)


def db_connect(func):
    def _db_connect(*args, **kwargs):
        conn = connect(DATABASE_PATH)
        curs = conn.cursor()
        result = func(curs, *args, **kwargs)
        conn.commit()
        conn.close()
        return result

    return _db_connect


@db_connect
def create_table(curs):
    curs.execute("""
        CREATE TABLE IF NOT EXISTS Pano
        (
          id CHAR PRIMARY KEY,
          type CHAR NOT NULL,
          downloaded INTEGER DEFAULT 0
        );
    """)
    curs.execute("""
        CREATE TABLE IF NOT EXISTS Task
        (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ip CHAR NOT NULL,
          issueTime INTEGER,
          panoId CHAR NOT NULL,
          FOREIGN KEY(panoId) REFERENCES Pano(id)
        );
    """)


@db_connect
def add_pano(curs, pano_id: str, pano_type: str):
    curs.execute(
        f"INSERT OR IGNORE INTO Pano(id, type) VALUES ('{pano_id}', '{pano_type}')"
    )


@db_connect
def get_pano(curs, pano_id: str) -> Optional[Pano]:
    result = curs.execute(f"""
        SELECT id, type
        FROM Pano
        WHERE Pano.id = '{pano_id}'
    """).fetchone()
    return result and Pano(id=result[0], type=PanoType(result[1]))


@db_connect
def get_not_downloaded_pano(curs) -> str:
    expiration = int((datetime.datetime.now() - TASK_EXPIRATION).timestamp())

    result = curs.execute(f"""
        SELECT id, type
        FROM Pano
        WHERE NOT EXISTS(
            SELECT 1
            FROM Task
            WHERE Task.panoId = Pano.id and Task.issueTime >= {expiration}
        ) AND Pano.downloaded = 0
        LIMIT 1;
    """).fetchone()
    return result and Pano(id=result[0], type=PanoType(result[1]))


@db_connect
def issue_task(curs, ip: str) -> Optional[Pano]:
    pano = get_not_downloaded_pano()
    if pano:
        curs.execute(f"""
            INSERT OR IGNORE INTO Task(ip, issueTime, panoId)
            VALUES ('{ip}', '{int(datetime.datetime.now().timestamp())}', '{pano.id}')
        """)
        return pano
    return None


@db_connect
def finish_task(curs, pano_id: str):
    curs.execute(f"""
        UPDATE Pano
        SET downloaded=TRUE
        WHERE Pano.id = '{pano_id}'
    """)


create_table()

if __name__ == '__main__':
    pano_id = "TEST_PANO"
    add_pano(pano_id, "google_pano")
    print(issue_task("TEST_IP"))
    time.sleep(7)
    finish_task(pano_id)
