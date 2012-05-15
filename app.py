from __future__ import with_statement
import sqlite3
import datetime
from contextlib import closing
import json
import itertools

from flask import Flask, request, session, g, redirect, url_for, render_template

from stressors import BagStressor, QueryStressor, DummyStressor

DATABASE = 'stresstest.db'
DEBUG = True
SECRET_KEY = 'dev-key'

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_envvar('STRESS_TEST_SETTINGS', silent=True)

@app.before_request
def setup():
    if not hasattr(g, "stressors"):
        g.stressors = {}

def connect_db():
    return sqlite3.connect(app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)

def init_db():
    """Create the db tables"""
    with closing(connect_db()) as db:
        with app.open_resource("schema.sql") as f:
            db.cursor().executescript(f.read())
        db.commit()

class DateHandlingEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return str(o)
        return JSONEncoder.default(self, o)

@app.route('/test/<mine>')
def run_test(mine):
    if "clean" in request.args:
        if mine in g.stressors:
            g.stressors[mine].active = false
            g.stressors[mine] = None
    if mine not in g.stressors or g.stressors[mine] is None:
        start_stress_tests(mine, request.args.get("type", "queries"))
    return render_template("test.html", mine = mine)

@app.route('/results/<mine>.json')
def get_results(mine):
    with closing(connect_db()) as db:
        cur = db.execute("""
                select dp.seconds, dp.requests, t.id, t.title, t.started_at
                from data_points as dp
                join tests t on dp.test = t.id
                where t.mine = ?
                order by t.id asc, dp.at asc
                """, (mine,))
        res = cur.fetchall()
    datasets = [list(rows) for test, rows in itertools.groupby(res, lambda r: r[2])]
    data = [dict(title = ds[0][3], start = ds[0][4], data = [(x[0], x[1]) for x in ds]) for ds in datasets]
    return json.dumps(data, cls = DateHandlingEncoder)

def start_stress_tests(mine, test_type = "queries"):

    if test_type == "lists":
        stressor = BagStressor(connect_db, mine)
    else:
        stressor = QueryStressor(connect_db, mine)

    stressor.start()
    g.stressors[mine] = stressor

if __name__ == "__main__":
    app.run(port = 5000)











