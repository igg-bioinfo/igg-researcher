import pandas as pd
import json
from datetime import datetime 
from utils import *

class Pubmed:
    st = None
    db = None
    pubs_cols_n = 7
    columns = [
        "pm_id",
        "doi",
        "journal",
        "issn",
        "title",
        "pub_date",
        "pmc_id",
        "author_orcid",
        "author_name",
        "is_person",
        "position",
        "corresponding",
        "affiliations"]
    excel_columns = [
        "PUBMED",
        "DOI",
        "Rivista",
        "ISSN",
        "Titolo",
        "Data",
        "PMC",
        "ORCID",
        "Autore",
        "Persona",
        "Posizione",
        "Corresponding",
        "Affiliazioni"]
    is_gaslini = None
    year = 0
    update_date = None
    update_days = None
    update_count_authors = None
    update_count_pubs = None


    def __init__(self, st, db, is_gaslini = True, year = None):
        self.st = st
        self.db = db
        self.is_gaslini = is_gaslini
        self.year = datetime.now().year if year == None else year


    def get_update_details(self):
        with self.st.spinner():
            sql = "SELECT update_date, COUNT(pub_authors) FROM pubmed_pubs WHERE "
            if self.is_gaslini:
                sql += "lower(affiliations::text) like '%%gaslini%%' and "
            sql += " EXTRACT('Year' from TO_DATE(pub_date,'YYYY-MM-DD')) = %s GROUP BY update_date, pm_id "
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
            cols_pub = self.columns[:self.pubs_cols_n]
            excel_cols_pub = self.excel_columns[:self.pubs_cols_n]
            cols = ""
            for col in cols_pub:
                cols += col + ", "
            cols = cols[:-2]
            sql = "SELECT DISTINCT " + cols + " FROM pubmed_pubs WHERE "
            if self.is_gaslini:
                sql += "lower(affiliations::text) like '%%gaslini%%' and "
            sql += " EXTRACT('Year' from TO_DATE(pub_date,'YYYY-MM-DD')) = %s ORDER BY pub_date DESC, pm_id "
            self.db.cur.execute(sql, [self.year])
            res = self.db.cur.fetchall()
            df = pd.DataFrame(res, columns=excel_cols_pub)
            download_excel(self.st, df, "pubmed_author_pubs_" + datetime.now().strftime("%Y-%m-%d_%H.%M"))
            show_df(self.st, df)


    def get_no_scopus_pubs_author_for_year(self, author, scopus_id):
        with self.st.spinner():
            cols_pub = self.columns[:self.pubs_cols_n]
            excel_cols_pub = self.excel_columns[:self.pubs_cols_n]
            cols = ""
            for col in cols_pub:
                cols += col + ", "
            cols = cols[:-2]
            sql = "SELECT DISTINCT " + cols + " FROM pubmed_pubs WHERE pm_id in ("
            sql += "select pm_id from pubs_not_in_scopus_per_author(%s, %s)" #pubs_not_in_scopus(%s)
            sql += ") and author_name like '%%" + author + "%%' and EXTRACT('Year' from TO_DATE(pub_date,'YYYY-MM-DD')) = %s "
            sql += "ORDER BY pub_date DESC, pm_id "
            self.db.cur.execute(sql, [self.year, scopus_id, self.year])
            res = self.db.cur.fetchall()
            df = pd.DataFrame(res, columns=excel_cols_pub)
            download_excel(self.st, df, "pubmed_author_pubs_" + datetime.now().strftime("%Y-%m-%d_%H.%M"), 'no_scopus_pubmed_pubs')
            show_df(self.st, df)

    def get_no_scopus_pubs_authors_for_year(self):
        with self.st.spinner():
            cols_pub = self.columns[:self.pubs_cols_n]
            excel_cols_pub = self.excel_columns[:self.pubs_cols_n]
            cols = ""
            for col in cols_pub:
                cols += col + ", "
            cols = cols[:-2]
            sql = "SELECT DISTINCT " + cols + " FROM pubmed_pubs WHERE pm_id in ("
            sql += "select pm_id from pubs_not_in_scopus(%s)"
            sql += ") and EXTRACT('Year' from TO_DATE(pub_date,'YYYY-MM-DD')) = %s "
            sql += "ORDER BY pub_date DESC, pm_id "
            self.db.cur.execute(sql, [self.year, self.year])
            res = self.db.cur.fetchall()
            df = pd.DataFrame(res, columns=excel_cols_pub)
            download_excel(self.st, df, "pubmed_author_pubs_" + datetime.now().strftime("%Y-%m-%d_%H.%M"), 'no_scopus_pubmed_pubs')
            show_df(self.st, df)
