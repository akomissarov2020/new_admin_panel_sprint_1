# -*- coding: utf-8 -*-
#
# @created: 10.04.2022
# @author: Aleksey Komissarov
# @contact: ad3002@gmail.com
"""Testing data constituency after import."""
import datetime
import sqlite3
import sys
from dataclasses import dataclass
from typing import NoReturn

import psycopg2

sys.path.append("..")
from load_data import UploadSettings, conn_context, table2dataclass


def check_tables(
        curs: sqlite3.Cursor,
        pg_cur: psycopg2.extras.DictCursor,
        model: dataclass,
        table_name: str,
        db_name: str,
    ) -> NoReturn:
    """Check table consistency."""
    curs.execute("SELECT * FROM {table_name};".format(table_name=table_name))
    original_data = curs.fetchall()

    sql = psycopg2.sql.SQL("SELECT * from {db_name}.{table_name};").format(
        db_name=psycopg2.sql.Identifier(db_name),
        table_name=psycopg2.sql.Identifier(table_name),
    )
    pg_cur.execute(sql)
    new_data = pg_cur.fetchall()
    assert len(original_data) == len(new_data)

    id2item = {}
    for item in original_data:
        item_dict = dict(item)
        for key in item_dict.keys():
            if key in ("created_at", "updated_at"):
                item_dict[key] = datetime.datetime.strptime(
                    item_dict[key],
                    "%Y-%m-%d %H:%M:%S.%f+00",
                ).replace(tzinfo=datetime.timezone.utc)

        id2item[item["id"]] = model(**item_dict)
    for item in new_data:
        item_dict = dict(item)
        for key in list(item_dict.keys())[::]:
            if key == "created":
                item_dict["created_at"] = item_dict[key]
                del item_dict[key]
            elif key == "modified":
                item_dict["updated_at"] = item_dict[key]
                del item_dict[key]

        new_model = model(**item_dict)
        assert id2item[item_dict["id"]] == new_model


def check_data(dsl: UploadSettings) -> NoReturn:
    """Check every table."""
    with conn_context(dsl) as (conn, pg_conn):
        cur = conn.cursor()
        pg_cur = pg_conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for item in cur.fetchall():
            table_name = item["name"]
            db_name = "content"
            print(table_name)
            model = table2dataclass[table_name]
            check_tables(cur, pg_cur, model, table_name, db_name)


if __name__ == "__main__":
    dsl = UploadSettings(
        localdb="../db.sqlite",
        dbname="movies_database",
        output_dbname="content",
        user="app",
        password="123qwe",
    )

    check_data(dsl)
