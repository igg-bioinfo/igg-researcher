import pandas as pd
from datetime import datetime 
from utils import *

class User:
    st = None
    db = None
    id = 0
    name = ""
    user_name = ""
    user_type = ""
    is_inv = False 
    
    first_name = ""
    last_name = ""
    contract = ""
    unit = ""
    scopus_id = ""
    orcid_id = ""
    researcher_id = ""

    age = ""
    update_date = "Nessuna data"
    metrics_date = "Nessuna data"
    user_confirmed = False
    hindex = None
    n_pubs = None
    all_cited = None
    hindex5 = None
    n_pubs5 = None
    all_cited5 = None
    hindex10 = None
    n_pubs10 = None
    all_cited10 = None
    pucs_missing = None
    pucs = None
    pucs5 = None
    pucs10 = None


    #-----------------------------------GENERALI
    def __init__(self, st, db, name = ""):
        self.st = st
        self.db = db
        if name != "":
            self.name = name
            self.get_investigator()
            self.db.cur.execute("SELECT user_id, user_name, user_type, name FROM users WHERE name = %s ", [self.name])
            res = self.db.cur.fetchone()
            if res != None:
                self.id = res[0]
                if res[1] != None and res[1] != '':
                    self.user_name = res[1]
                self.user_type = res[2]
                self.name = res[3]
        elif "logged_user" in self.st.session_state and self.st.session_state["logged_user"] != None:
            user = self.st.session_state["logged_user"]
            self.id = user['id']
            self.name = user['name']
            self.user_name = user['user_name']
            self.user_type = user['user_type']
            self.get_investigator()
            self.set_logout()
    
    
    def get_investigator(self):
        sql = ""
        sql += "SELECT * FROM view_invs "
        sql += "WHERE inv_name = %s and update_year = %s "
        self.db.cur.execute(sql, [self.name, datetime.now().year])
        res = self.db.cur.fetchone()
        if res != None:
            self.age = int(res[0])
            self.first_name = res[2] 
            self.last_name = res[3] 
            self.unit = res[5] 
            self.contract = res[6] 
            self.scopus_id = res[7] 
            self.orcid_id = res[8] 
            self.researcher_id = res[9] 
            self.user_confirmed = res[10] == '1'
            self.update_date = res[11]
            self.is_inv = True 


    def login(self):
        def check_get_user():
            #self.st.success(self.st.session_state["username"])
            self.db.cur.execute("SELECT user_id, user_name, user_type, name FROM users WHERE user_name = %s and user_password = %s and is_enabled = true ",
                                [self.st.session_state["username"], self.st.session_state["password"]])
            res = self.db.cur.fetchone()
            if res != None:
                del self.st.session_state["username"]
                del self.st.session_state["password"]
                self.st.session_state["logged_user"] = {'id': res[0], 'name': res[3], 'user_name': res[1], 'user_type': res[2]}
                self.st.experimental_rerun()
            else:
                self.st.error("Credenziali errate")
                self.st.session_state["logged_user"] = None

        if "logged_user" not in self.st.session_state or self.st.session_state["logged_user"] == None:
            with self.st.form("login_form"):
                self.st.write("LOGIN")
                self.st.text_input("Utente", key="username")
                self.st.text_input("Password", type="password", key="password")
                if self.st.form_submit_button("Entra"):
                    with self.st.spinner():
                        check_get_user()
        else:
            return True
        return False


    def set_logout(self):
        with self.st.sidebar:
            self.st.markdown("Profilo: **" + self.name + "**")
            if self.st.button("Logout"):
                self.st.session_state["logged_user"] = None
                self.st.experimental_rerun()


    def is_logged(self, write_error = True):
        if "logged_user" not in self.st.session_state or self.st.session_state["logged_user"] == None:
            if write_error:
                self.st.error("Accesso negato")
            self.st.stop()


    def has_access(self, type):
        has_access = False
        if type in self.user_type:
            has_access = True 
        return has_access


    #-----------------------------------AGGIORNA I DATI
    def save_data(self, first_name, last_name, user_name, contract, unit, scopus_id, orcid_id, researcher_id):   
        bt_text = "Conferma i dati"
        if self.user_confirmed:
            self.st.success("I dati del ricercatore sono stati confermati manualmente")  
            bt_text = "Aggiorna i dati"
        else:
            self.st.warning("Controlla e conferma i dati")  
        if self.st.button(bt_text, key="save_data"):
            with self.st.spinner():
                update_date = datetime.date(datetime.now())
                sql = "UPDATE investigator_details SET first_name=%s, last_name=%s, contract=%s, unit=%s, scopus_id=%s, orcid_id=%s, researcher_id=%s, update_date=%s WHERE inv_name=%s "
                self.db.cur.execute(sql, [first_name, last_name, contract, unit, scopus_id, orcid_id, researcher_id, update_date, self.name])
                sql = "INSERT INTO investigator_details (inv_name, first_name, last_name, contract, unit, scopus_id, orcid_id, researcher_id, update_date) "
                sql += "SELECT %s, %s, %s, %s, %s, %s, %s, %s, %s "
                sql += "WHERE NOT EXISTS (SELECT 1 FROM investigator_details WHERE inv_name = %s)"
                self.db.cur.execute(sql, [self.name, first_name, last_name, contract, unit, scopus_id, orcid_id, researcher_id, update_date, self.name])
                self.db.conn.commit()
                if scopus_id != None and scopus_id != "" and scopus_id != self.scopus_id and self.scopus_id != None and self.scopus_id != "":
                    sql = "call  update_scopus_pucs(%s, %s) "
                    self.db.cur.execute(sql, [self.scopus_id, scopus_id])
                    self.db.conn.commit()
                if user_name != '' and user_name != self.user_name:
                    sql = "UPDATE user SET user_name=%s, WHERE name=%s "
                    self.db.cur.execute(sql, [user_name, self.name])
                    self.db.conn.commit()
                self.st.experimental_rerun()


    #-----------------------------------METRICHE BASE
    def get_metrics(self, year):
        with self.st.spinner():
            if self.scopus_id != None and self.scopus_id != "":
                sql = "select hindex, pubs, allcited, hindex5, pubs5, allcited5, hindex10, pubs10, allcited10, update_date from "
                if year == all_years:
                    year = datetime.now().year
                self.db.cur.execute(sql + "scopus_metrics where author_scopus = %s and update_year = %s ", [self.scopus_id, year])
                res = self.db.cur.fetchall()
                if res:
                    self.hindex = res[0][0]
                    self.n_pubs = res[0][1]
                    self.all_cited = res[0][2]
                    self.hindex5 = res[0][3]
                    self.n_pubs5 = res[0][4]
                    self.all_cited5 = res[0][5]
                    self.hindex10 = res[0][6]
                    self.n_pubs10 = res[0][7]
                    self.all_cited10 = res[0][8]
                    self.metrics_date = res[0][9]


    def get_pubs(self, year):
        with self.st.spinner():
            if self.scopus_id != None and self.scopus_id != "":
                params = [self.scopus_id, self.scopus_id, self.scopus_id, 
                          self.scopus_id, self.scopus_id, self.scopus_id, 
                          self.scopus_id, self.scopus_id, self.scopus_id, self.scopus_id, self.scopus_id,
                          self.scopus_id]
                sql = "select s.eid, s.doi, s.pm_id, s.title, s.pub_date, s.pub_type, s.cited, "
                sql += "CASE WHEN p.eid is not null THEN true ELSE false END as PUC, "
                sql += "CASE WHEN p.first1 = %s or p.first2 = %s or p.first3 = %s THEN true ELSE false END as Primo, "
                sql += "CASE WHEN p.last1 = %s or p.last2 = %s or p.last3 = %s THEN true ELSE false END as Ultimo, "
                sql += "CASE WHEN p.corr1 = %s or p.corr2 = %s or p.corr3 = %s or p.corr4 = %s or p.corr5 = %s THEN true ELSE false END as Corr "
                sql += "FROM scopus_pubs_all s "
                sql += "LEFT OUTER JOIN scopus_pucs p ON p.eid = s.eid "
                sql += "WHERE author_scopus = %s "
                if year != all_years:
                    sql += "and EXTRACT('Year' from TO_DATE(pub_date,'YYYY-MM-DD')) = %s "
                    params.append(year)
                sql += "ORDER BY pub_date DESC"
                self.db.cur.execute(sql, params)
                res = self.db.cur.fetchall()
                if len(res) > 0 and len(res) > 0 and res[0][0] != None:
                    df = pd.DataFrame(res, columns=["EID", "DOI", "PUBMED ID", "Titolo pubblicazione", "Data", "Tipo", "Cit.", "PUC", "Primo", "Ultimo", "Corr."])
                    df.set_index('EID', inplace=True)
                    download_excel(self.st, df, "scopus_pubs_" + self.scopus_id + "_" + str(year) + "_" + datetime.now().strftime("%Y-%m-%d_%H.%M"))
                    self.st.write(str(len(df)) + " Righe")
                    self.st.dataframe(df, height=row_height)


    #-----------------------------------PUC
    def check_pucs(self):
        params = [self.scopus_id]
        sql = "SELECT COUNT(eid) AS eids FROM scopus_pubs_all "
        sql += "WHERE author_scopus = %s "
        sql += "and eid NOT IN (SELECT DISTINCT eid FROM scopus_pucs) GROUP BY author_scopus "
        self.db.cur.execute(sql, params)
        res = self.db.cur.fetchall()
        if res and len(res) > 0: 
            if len(res[0]) > 0:
                self.pucs_missing = res[0][0]
                if self.pucs_missing == None or self.pucs_missing == 0:   
                    return True
                elif self.pucs_missing == self.n_pubs:
                    self.st.error("Mancano i PUC di tutte le pubblicazioni per stimare i PUC per l'autore")
                    return False
                else:
                    self.st.error("Mancano i PUC per " + str(self.pucs_missing) + " pubblicazioni per stimare i PUC per l'intera carriera")
                    return False
            else:
                self.st.error("Mancano i PUC di tutte le pubblicazioni per stimare i PUC per l'autore")
                return False
        else: 
            return True
        
    def check_fields_value(self, fields, value):
        for field in fields:
            if value[field] == self.scopus_id:
                return 1
        return 0
    

    def get_pucs(self, year):
        self.pucs = ""
        self.pucs5 = ""
        self.pucs10 = ""
        sql = ""
        sql += "SELECT pub_year, first1, first2, first3, last1, last2, last3, corr1, corr2, corr3, corr4, corr5  FROM scopus_pucs "
        sql += "WHERE eid IN ( "
        sql += "SELECT eid FROM scopus_pubs_all WHERE author_scopus = %s "
        sql += ") AND ( "
        sql += "first1 = %s OR first2 = %s OR first3 = %s "
        sql += "OR last1 = %s OR last2 = %s OR last3 = %s "
        sql += "OR corr1 = %s OR corr2 = %s OR corr3 = %s OR corr4 = %s OR corr5 = %s "
        sql += ") ORDER BY pub_year DESC "

        params = [self.scopus_id,
                  self.scopus_id, self.scopus_id, self.scopus_id,
                  self.scopus_id, self.scopus_id, self.scopus_id,
                  self.scopus_id, self.scopus_id, self.scopus_id, self.scopus_id, self.scopus_id
                  ]
        self.db.cur.execute(sql, params)
        res = self.db.cur.fetchall()
        firsts = 0
        lasts = 0
        corrs = 0
        firsts5 = 0
        lasts5 = 0
        corrs5 = 0
        firsts10 = 0
        lasts10 = 0
        corrs10 = 0
        for r in res:
            if check_year(self.st, year, r[0], 5):
                firsts5 += self.check_fields_value([1,2,3], r)
                lasts5 += self.check_fields_value([4,5,6], r)
                corrs5 += self.check_fields_value([7,8,9,10,11], r)
            if check_year(self.st, year, r[0], 10):
                firsts10 +=  self.check_fields_value([1,2,3], r)
                lasts10 += self.check_fields_value([4,5,6], r)
                corrs10 += self.check_fields_value([7,8,9,10,11], r)
            if check_year(self.st, year, r[0], 0):
                firsts += self.check_fields_value([1,2,3], r)
                lasts += self.check_fields_value([4,5,6], r)
                corrs += self.check_fields_value([7,8,9,10,11], r)
        self.pucs5 = str(firsts5) + " - " + str(lasts5) + " - " + str(corrs5)
        self.pucs10 = str(firsts10) + " - " + str(lasts10) + " - " + str(corrs10)
        self.pucs = str(firsts) + " - " + str(lasts) + " - " + str(corrs)


        