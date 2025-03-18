import pugsql
import time
import sys
import os

DB_FILE = os.path.expanduser("~/gasferm.db")

queries = None


def init():
    global queries
    queries = pugsql.module("queries/")
    queries.connect("sqlite:///" + DB_FILE)


def rebuild_db():
    print("Creating new database.", file=sys.stderr)
    queries.create_table_sensordata()
    queries.create_trigger_delete_oldest()
