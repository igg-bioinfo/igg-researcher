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


    def sort_by_cited(self, e):
        return e["cited"]
    
    def get_hindex(self, pubs, years_range):
        hindex = 0
        index = 1
        for p in pubs:
            if index > p["cited"]:
                break
            pub_year = datetime.strptime(p["pub_date"], '%Y-%m-%d').year
            if check_year(self.st, self.year, pub_year, years_range):
                hindex = index
                index += 1
        return hindex
    
    def get_allcited(self, pubs, years_range):
        allcited = 0
        for p in pubs:
            pub_year = datetime.strptime(p["pub_date"], '%Y-%m-%d').year
            if check_year(self.st, self.year, pub_year, years_range):
                allcited += p["cited"]
        return allcited
    
    def get_n_pubs(self, pubs, years_range):
        n_pubs = 0
        for p in pubs:
            pub_year = datetime.strptime(p["pub_date"], '%Y-%m-%d').year
            if check_year(self.st, self.year, pub_year, years_range):
                n_pubs += 1
        return n_pubs

    def set_metrics(self, author_scopus, pubs: list, update_date):
        pubs.sort(key=self.sort_by_cited, reverse=True)

        hindex = self.get_hindex(pubs, 0)
        n_pubs = self.get_n_pubs(pubs, 0)
        allcited = self.get_allcited(pubs, 0)

        hindex5 = self.get_hindex(pubs, 5)
        n_pubs5 = self.get_n_pubs(pubs, 5)
        allcited5 = self.get_allcited(pubs, 5)

        hindex10 = self.get_hindex(pubs, 10)
        n_pubs10 = self.get_n_pubs(pubs, 10)
        allcited10 = self.get_allcited(pubs, 10)

        sql = "UPDATE scopus_metrics SET hindex=%s, pubs=%s, allcited=%s, hindex5=%s, pubs5=%s, allcited5=%s, hindex10=%s, pubs10=%s, allcited10=%s, "
        sql += "update_date=%s WHERE author_scopus=%s and update_year = %s"
        self.db.cur.execute(sql, [hindex, n_pubs, allcited, hindex5, n_pubs5, allcited5, hindex10, n_pubs10, allcited10, update_date, author_scopus, self.year])
        sql = "INSERT INTO scopus_metrics (author_scopus, hindex, pubs, allcited, hindex5, pubs5, allcited5, hindex10, pubs10, allcited10, update_date, update_year) "
        sql += "SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s "
        sql += "WHERE NOT EXISTS (SELECT 1 FROM scopus_metrics WHERE author_scopus = %s and update_year = %s)"
        self.db.cur.execute(sql, [author_scopus, hindex, n_pubs, allcited, hindex5, n_pubs5, allcited5, hindex10, n_pubs10, allcited10, 
                                  update_date, self.year, author_scopus, self.year])


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