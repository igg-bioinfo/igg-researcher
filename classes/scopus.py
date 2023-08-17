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


    #-----------------------------------ALBO
    def get_albo(self, only_scopus: bool = True):
        with self.st.spinner():
            sql = ""
            sql += "SELECT l.*, COUNT(c.eid) as corrs FROM ( "
            sql += "SELECT f.*, COUNT(l.eid) as lasts FROM ( "
            sql += "SELECT s.*, COUNT(f.eid) as firsts FROM ( "
            sql += "SELECT i.inv_name, i.contract, " + age_field + " as age, CASE WHEN d.scopus_id IS NULL THEN i.scopus_id ELSE d.scopus_id END as scopus, "
            sql += (", ".join(self.metrics_columns)) + ", "
            sql += "(CASE WHEN pubs - (CASE WHEN pubs_puc IS NULL THEN 0 ELSE pubs_puc END) > 0 THEN (CASE WHEN pubs_puc IS NULL THEN 0 ELSE pubs_puc END)::text ELSE (CASE WHEN pubs IS NULL OR pubs = 0 THEN 'Nessun dato' ELSE 'OK' END) END) as puc "
            sql += "FROM investigators i "
            sql += "LEFT OUTER JOIN investigator_details d ON d.inv_name = i.inv_name "
            sql += "LEFT OUTER JOIN scopus_metrics m ON (d.scopus_id IS NULL and m.author_scopus = i.scopus_id) or (d.scopus_id IS NOT NULL and m.author_scopus = d.scopus_id) "
            sql += "LEFT OUTER JOIN (select author_scopus, count(eid) as pubs_puc from scopus_pubs_all WHERE EXTRACT('Year' from TO_DATE(pub_date,'YYYY-MM-DD')) = %s and eid IN (SELECT DISTINCT eid FROM scopus_pucs) group by author_scopus) p "
            sql += "ON (d.scopus_id IS NULL and p.author_scopus = i.scopus_id) or (d.scopus_id IS NOT NULL and p.author_scopus = d.scopus_id) "
            sql += "WHERE i.update_year = %s "
            if only_scopus:
                sql += " and (i.scopus_id IS NOT NULL or d.scopus_id IS NOT NULL) "
            sql += ") s "
            sql += "LEFT OUTER JOIN scopus_pucs f on (s.scopus = f.first1 or s.scopus = f.first2 or s.scopus = f.first3) "
            sql += "GROUP BY inv_name, contract, age, scopus, " + (", ".join(self.metrics_columns)) + ", puc "
            sql += ") f "
            sql += "LEFT OUTER JOIN scopus_pucs l on (f.scopus = l.last1 or f.scopus = l.last2 or f.scopus = l.last3) "
            sql += "GROUP BY inv_name, contract, age, scopus, " + (", ".join(self.metrics_columns)) + ", puc, firsts "
            sql += ") l "
            sql += "LEFT OUTER JOIN scopus_pucs c on (l.scopus = c.corr1 or l.scopus = c.corr2 or l.scopus = c.corr3 or l.scopus = c.corr4 or l.scopus = c.corr5) "
            sql += "GROUP BY inv_name, contract, age, scopus, " + (", ".join(self.metrics_columns)) + ", puc, firsts, lasts "
            sql += "ORDER BY hindex is null, hindex DESC, age ASC, inv_name ASC "
            #self.st.success(sql)
            self.db.cur.execute(sql, [self.year, self.year])
            res = self.db.cur.fetchall()
            albo_columns = ["Autore", "Contratto", "Età", "SCOPUS ID", "Pubs", "Cit.", "H-Index", "Pubs 5 anni", "Cit. 5 anni", "H-Index 5 anni", "Pubs con PUC", "Primi", "Ultimi", "Corr."]
            df = pd.DataFrame(res, columns=albo_columns)
            df["Email"] = ""
            for i, row in df.iterrows():
                df.loc[i, "Email"] = calculate_email(row["Autore"])

            download_excel(self.st, df, "albo_" + datetime.now().strftime("%Y-%m-%d_%H.%M"))
            self.st.dataframe(df, height=row_height)