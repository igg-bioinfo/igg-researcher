import pandas as pd
from datetime import datetime 
from utils import *

class Demo:
    st = None
    db = None
    id = 0
    name = ""
    user_name = ""
    user_type = ""
    year = 0
    update_date = None
    update_count = None
    update_days = None
    min_days = 3


    def __init__(self, st, db, year = None):
        self.st = st
        self.db = db
        self.year = datetime.now().year if year == None else year

    def get_description(self):
        pass

    def get_update_details(self):
        with self.st.spinner():
            sql = "SELECT update_date, COUNT(inv_name) FROM view_invs WHERE "
            sql += "update_year = %s GROUP BY update_date "
            self.db.cur.execute(sql,  [self.year])
            res = self.db.cur.fetchall()
            df = pd.DataFrame(res, columns=["update", "id"])
            if len(df) > 0:
                self.update_date = df["update"][0]
                self.update_count = df["id"][0]
                dt = datetime.date(datetime.now()) - self.update_date
                self.update_days = dt.days
                return True
        return False