from __future__ import with_statement
from intermine.webservice import Service
from time import sleep
import random
import datetime
import threading
from contextlib import closing

STEP = datetime.timedelta(seconds = 10)

STRESS_LOCK = threading.Lock()

class Stressor(threading.Thread):
    def __init__(self, get_db, mine, title):
        threading.Thread.__init__(self)
        self.requests = 0
        s = Service("localhost/" + mine, "intermine-test-user", "intermine-test-user-password")
        with STRESS_LOCK:
            with closing(get_db()) as db:
                c = db.cursor()
                c.execute("insert into tests (mine, title) values (?, ?)", (mine, title))
                self.test_id = c.lastrowid
                db.commit()
        self.get_db = get_db
        self.title = title
        self.service = s
        self.last_tick = self.get_last_tick()
        self.empty_steps = 0

    def get_last_tick(self):
        with closing(self.get_db()) as db:
            c = db.cursor()
            c.execute("select dp.at from data_points as dp where dp.test = ? order by dp.at desc limit 1", (self.test_id,))
            dp = c.fetchone()
            if dp:
                return dp[0]
            return datetime.datetime.now()

    def store_step(self):
        print "storing data for %s, %s" % (self.service.root, self.title)
        with STRESS_LOCK:
            with closing(self.get_db()) as db:
                c = db.cursor()
                c.execute("insert into data_points (requests, seconds, test) values (?, ?, ?)",
                        (self.requests, (datetime.datetime.now() - self.last_tick).total_seconds(), self.test_id))
                db.commit()
                if self.requests == 0:
                    self.empty_steps += 1
                    self.active = self.active and self.empty_steps < 5
                self.requests = 0
                self.last_tick = datetime.datetime.now()

    @property
    def next_tick(self):
        if self.last_tick is None:
            self.last_tick = self.get_last_tick()
        return self.last_tick + STEP

    def run(self):
        self.active = True

        try:
            while self.active:
                if self.next_tick <= datetime.datetime.now():
                    self.store_step()
                self.do_step()
        finally:
            self.cleanup()
            self.close_test()

    def cleanup(self):
        pass

    def close_test(self):
        with STRESS_LOCK:
            with closing(self.get_db()) as db:
                c = db.cursor()
                c.execute("update tests set completed_at = ? where id = ?",
                        (datetime.datetime.now(), self.test_id))
                db.commit()


class DummyStressor(Stressor):

    def do_step(self):
        if not self.requests % 10:
            print "I am a dummy"
        self.requests += 1
        sleep(1)

    def cleanup(self):
        pass

class BagStressor(Stressor):

    def __init__(self, get_db, mine):
        Stressor.__init__(self, get_db, mine, "List Queries")

        self.q1 = self.service.select("Manager")
        self.q2 = self.service.select("Manager").where("department.name", "=", "Sales")
        self.requests += 2

    def do_step(self):
        bag1 = self.service.create_list(self.q1)
        self.requests += 2
        bag2 = self.service.create_list(self.q2)
        self.requests += 2
        bag3 = bag1 - bag2
        self.requests += 2
        assert(bag3.size == bag1.size - 3)
        bag3.add_tags("cause_of_stress", "agonist")
        self.requests += 1
        assert(len(bag3.tags) == 2)
        bag1.delete()
        self.requests += 2
        bag2.delete()
        self.requests += 2
        bag3.delete()
        self.requests += 2

    def cleanup(self):
        print "Cleaning up in %s" % self.__class__.__name__
        s = self.service
        for l in s.get_all_lists():
            if l.name.startwith("my_list_"):
                l.delete()


class QueryStressor(Stressor):

    def __init__(self, get_db, mine):
        Stressor.__init__(self, get_db, mine, "Random Queries")

        q = self.service.select("Manager").where("age", ">", 35).where("age", "<", 45)
        try:
            self.bag = self.service.create_list(q, name = "my_stressful_query_list")
        except:
            self.cleanup()
            raise
        self.requests += 3

    def do_step(self):
        # One of 5 * 5 * 1000 * 1000 (25,000,000) queries
        q = self.service.select("Manager")\
                .where("Manager", random.choice(["IN", "NOT IN"]), self.bag.name)\
                .where("age",
                        random.choice(["=", ">","<=", ">=", "<"]),
                        random.randrange(1000))\
                .where("department.employees.age",
                        random.choice(["=", ">",">=", "<=", "<"]), 
                        random.randrange(1000))
        assert(q.count() < 200)
        self.requests += 1
        assert(len(q.rows()) == q.count())
        self.requests += 2

    def cleanup(self):
        print "Cleaning up in %s" % self.__class__.__name__
        if hasattr(self, "bag"):
            self.bag.delete()
        else:
            self.service.get_list("my_stressful_query_list").delete()



