import pandas as pd
from datetime import datetime 
from classes.demo import *
from utils import *
import json

class Scopus:
    columns = ["eid", "doi", "pm_id", "issn", "title", "pub_date", "pub_type", "cited", "author_name", "author_scopus"]
    metrics_columns = ["pubs", "allcited", "hindex", "pubs5", "allcited5", "hindex5", "pubs10", "allcited10", "hindex10"]
    excel_columns = ["EID", "DOI", "PubMed", "ISSN", "Titolo", "Data", "Tipo", "Cit.", "Autore", "SCOPUS"]
    is_gaslini = None
    year = 0
    update_date = None
    update_days = None
    update_count_pubs = None
    update_count_authors = None
    metrics_update = []
    min_days = 0
    max_pucs = 100


    #-----------------------------------GENERALI
    def __init__(self, st, db, year = None):
        self.st = st
        self.db = db
        self.year = datetime.now().year if year == None else year


    #-----------------------------------PUBBLICAZIONI PER ANNO
    def get_update_details(self):
        with self.st.spinner():
            sql = "SELECT update_date, COUNT(pub_authors) FROM scopus_pubs_all WHERE "
            sql += "EXTRACT('Year' from TO_DATE(pub_date,'YYYY-MM-DD')) = %s "
            sql += "GROUP BY update_date, doi "
            self.db.cur.execute(sql, [self.year])
            res = self.db.cur.fetchall()
            df = pd.DataFrame(res, columns=["update", "authors"])
            if len(df) > 0:
                self.update_date = df["update"][0]
                self.update_count_pubs = len(df)
                self.update_count_authors = df["authors"].sum()
                dt = datetime.date(datetime.now()) - self.update_date
                self.update_days = dt.days
                return True
        return False


    def get_pubs_authors_for_year(self):
        with self.st.spinner():
            cols = ""
            for col in self.columns:
                cols += col + ", "
            cols = cols[:-2]
            sql = "SELECT " + cols + " FROM scopus_pubs_all  "
            sql += "WHERE EXTRACT('Year' from TO_DATE(pub_date,'YYYY-MM-DD')) = %s "
            if self.is_gaslini:
                sql += "AND is_gaslini = true "
            sql += "ORDER BY doi, pm_id "
            self.db.cur.execute(sql, [self.year])
            res = self.db.cur.fetchall()
            df = pd.DataFrame(res, columns=self.excel_columns)
            df.set_index('Autore', inplace=True)
            download_excel(self.st, df, "scopus_pubs_" + str(self.year) + "_" + datetime.now().strftime("%Y-%m-%d_%H.%M"))
            self.st.write(str(len(df)) + " Righe")
            self.st.dataframe(df, height=row_height)


    #-----------------------------------METRICHE
    def get_metrics_update_details(self):
        with self.st.spinner():
            sql = "SELECT update_date, COUNT(metric_id) FROM scopus_metrics "
            sql += "WHERE update_year = %s GROUP BY update_date ORDER BY update_date DESC"
            self.db.cur.execute(sql, [self.year])
            res = self.db.cur.fetchall()
            df = pd.DataFrame(res, columns=["update", "metrics"])
            self.metrics_update = []
            for i, row in df.iterrows():
                self.metrics_update.append({"update": row["update"], "metrics": row["metrics"]})
            if len(df) > 0:
                self.update_date = df["update"][0]
                dt = datetime.date(datetime.now()) - self.update_date
                self.update_days = dt.days
                return True
        return False


    #-----------------------------------AUTORI
    def get_authors_update_details(self):
        with self.st.spinner():
            sql = "SELECT update_date, COUNT(scopus_inv_id) FROM scopus_invs "
            sql += "GROUP BY update_date "
            self.db.cur.execute(sql, [self.year])
            res = self.db.cur.fetchall()
            df = pd.DataFrame(res, columns=["update", "authors"])
            if len(df) > 0:
                self.update_date = df["update"][0]
                self.update_count_authors = df["authors"][0]
                dt = datetime.date(datetime.now()) - self.update_date
                self.update_days = dt.days
                return True
        return False