import datetime
import psycopg2
import sqlite3
import sys
sys.path.append("..")

from psycopg2.extras import DictCursor
from psycopg2.sql import Identifier, SQL
from typing import NoReturn

from load_data import BaseImportDataclass, UploadSettings, conn_context
from models import BaseImportDataclass
from models import Filmwork, Genre, Person, GenreFilmwork, PersonFilmwork


def check_tables(curs: sqlite3.Cursor,
                 pg_cur: psycopg2.extras.DictCursor,
                 model: BaseImportDataclass,
                 table_name: str,
                 db_name: str,
                 n: int) -> NoReturn:
    curs.execute(f"SELECT * FROM {table_name};")
    original_data = curs.fetchall();

    sql = SQL("SELECT * from {db_name}.{table_name};").format(
        db_name=Identifier(db_name),
        table_name=Identifier(table_name),
    )
    pg_cur.execute(sql)
    new_data = pg_cur.fetchall()
    assert (len(original_data) == len(new_data))

    id2item = {}
    for item in original_data:
        item_dict = dict(item)
        for key in item_dict.keys():
            if key in ['created_at', 'updated_at']:
                item_dict[key] = datetime.datetime.strptime(
                    item_dict[key], '%Y-%m-%d %H:%M:%S.%f+00'
                ).replace(tzinfo=datetime.timezone.utc)

        id2item[item['id']] = model(**item_dict)
    for item in new_data:
        item_dict = dict(item)
        for key in list(item_dict.keys())[::]:
            if key == 'created':
                item_dict['created_at'] = item_dict[key]
                del item_dict[key]
            elif key == 'modified':
                item_dict['updated_at'] = item_dict[key]
                del item_dict[key]

        new_model = model(**item_dict)
        assert (id2item[item_dict['id']] == new_model)


table2dataclass = {
    "genre": Genre,
    "genre_film_work": GenreFilmwork,
    "person_film_work": PersonFilmwork,
    "person": Person,
    "film_work": Filmwork,
}


def check_data(dsl: UploadSettings) -> NoReturn:
    """Check every table."""

    with conn_context(dsl) as (conn, pg_conn):
        cur = conn.cursor()
        pg_cur = pg_conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")

        for item in cur.fetchall():
            table_name = item['name']
            db_name = 'content'
            print(table_name)
            dataclass_ = table2dataclass[table_name]
            check_tables(cur, pg_cur, dataclass_, table_name, db_name, dsl.batch_size)


if __name__ == '__main__':
    dsl = UploadSettings(
        localdb='../db.sqlite',
        dbname='movies_database',
        output_dbname='content',
        user='app',
        password='123qwe',
        batch_size=100,
    )

    check_data(dsl)
