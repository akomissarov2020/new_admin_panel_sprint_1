# -*- coding: utf-8 -*-
#
# @created: 10.04.2022
# @author: Aleksey Komissarov
# @contact: ad3002@gmail.com
"""Loadind data from sqlite3 to postgres."""
import os
import sqlite3
import sys
import traceback
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator, NoReturn, Tuple

import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor
from psycopg2.sql import SQL, Identifier, Placeholder

from models import Filmwork, Genre, GenreFilmwork, Person, PersonFilmwork

table2dataclass = {
    'genre': Genre,
    'genre_film_work': GenreFilmwork,
    'person_film_work': PersonFilmwork,
    'person': Person,
    'film_work': Filmwork,
}

@dataclass
class UploadSettings:
    localdb: os.PathLike
    dbname: str
    output_dbname: str
    user: str
    password: str
    host: str = '127.0.0.1'
    port: int = 5432
    batch_size: int = 100
    
    def get_psycopg_dict(self) -> dict:
        return {
            'dbname': self.dbname,
            'user': self.user,
            'password': self.password,
            'host': self.host,
            'port': self.port,
        }


def handle_sqlite3_errors(err):
    print('SQLite error: %s' % (' '.join(err.args)))
    print("Exception class is: ", err.__class__)
    print('SQLite traceback: ')
    exc_type, exc_value, exc_tb = sys.exc_info()
    print(traceback.format_exception(exc_type, exc_value, exc_tb))
    sys.exit(10)


def handle_psycopg2_errors(err):
    print('psycopg2 error: %s' % (' '.join(err.args)))
    print("Exception class is: ", err.__class__)
    print('psycopg2 traceback: ')
    exc_type, exc_value, exc_tb = sys.exc_info()
    print(traceback.format_exception(exc_type, exc_value, exc_tb))
    sys.exit(11)


@contextmanager
def conn_context(dsl: UploadSettings) -> Iterator[Tuple[sqlite3.Row, _connection]]:
    
    try:
        conn = sqlite3.connect(dsl.localdb)
    except sqlite3.Error as err:
        handle_sqlite3_errors(err)

    conn.row_factory = sqlite3.Row

    pg_conn = None
    try:
        pg_conn = psycopg2.connect(**dsl.get_psycopg_dict(), cursor_factory=DictCursor)
    except psycopg2.OperationalError as err:
        handle_psycopg2_errors(err)

    yield conn, pg_conn
    
    conn.close()
    pg_conn.close()


def upload_table(curs: sqlite3.Cursor, 
                 pg_cur: psycopg2.extras.DictCursor, 
                 model: dataclass,
                 table_name: str, 
                 db_name: str,
                 n: int) -> NoReturn:

    try:
        curs.execute(f"SELECT * FROM {table_name};")
    except sqlite3.Error as err:
        handle_sqlite3_errors(err)

    batch = []
    fields_ = model.get_fields()
    col_names = SQL(', ').join(Identifier(name) for name in fields_)
    place_holders = SQL(', ').join(Placeholder() * len(fields_ ))
    sql = SQL("INSERT INTO {db_name}.{table_name} ({col_names}) VALUES ({values}) ON CONFLICT DO NOTHING;").format(
            db_name=Identifier(db_name),
            table_name=Identifier(table_name),
            col_names=col_names,
            values=place_holders,
            )
    for item in curs.fetchall():
        batch.append(model(**dict(item)).get_data())
        if len(batch) == n:    
            try:
                pg_cur.executemany(sql, batch)
            except Exception as err:
                handle_psycopg2_errors(err)
            batch = []
    if batch:
        try:
            pg_cur.executemany(sql, batch)
        except Exception as err:
            handle_psycopg2_errors(err)


def load_from_sqlite(dsl: UploadSettings) -> NoReturn:
    """Основной метод загрузки данных из SQLite в Postgres"""

    with conn_context(dsl) as (conn, pg_conn):
        cur = conn.cursor()
        pg_cur = pg_conn.cursor()
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        except sqlite3.Error as err:
            handle_sqlite3_errors(err)

        for item in cur.fetchall():
            table_name = item['name']
            db_name = dsl.output_dbname
            print(table_name)
            dataclass_ = table2dataclass[table_name]
            upload_table(cur, pg_cur, dataclass_, table_name, db_name, dsl.batch_size)
        try:
            pg_conn.commit()
        except Exception as err:
            handle_psycopg2_errors(err)


if __name__ == '__main__':
    
    dsl = UploadSettings(
                    localdb='db.sqlite',
                    dbname='movies_database',
                    output_dbname='content',
                    user='app',
                    password='123qwe',
                    batch_size=100,
                    )

    load_from_sqlite(dsl)
