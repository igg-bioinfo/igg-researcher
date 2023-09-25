import pandas as pd
from datetime import datetime 
from utils import *

class User_request:
    user_name = ''
    first_name = ''
    last_name = ''
    contract = ''
    unit = ''
    scopus_id = ''
    orcid_id = ''
    researcher_id = ''
    year = 0

    def __init__(self, st, db):
        self.st = st
        self.db = db
        self.year = datetime.now().year 

    def check_request(self):
        sql = "SELECT status FROM investigator_requests WHERE email = %s"
        self.db.cur.execute(sql, [self.user_name])
        return self.db.cur.fetchall()

    def check_username(self):
        sql = "SELECT * FROM view_invs WHERE update_year = %s AND user_name = %s"
        self.db.cur.execute(sql, [self.year, self.user_name])
        return self.db.cur.fetchall()

    def check_name(self):
        sql = "SELECT * FROM view_invs WHERE update_year = %s AND lower(inv_name) = %s"
        self.db.cur.execute(sql, [self.year, str(self.last_name + ' ' + self.first_name).lower()])
        return self.db.cur.fetchall()

    def insert(self):
        try:
            sql = "INSERT INTO investigator_requests ("
            sql += "email, first_name, last_name, contract, unit, scopus_id, orcid_id, researcher_id, update_date, status"
            sql += ") VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
            params = [self.user_name, self.first_name, self.last_name, self.contract, 
                    self.unit, self.scopus_id, self.orcid_id, self.researcher_id,
                    datetime.date(datetime.now()), 0]
            self.db.cur.execute(sql, params)
            self.db.conn.commit()
        except:
            return False
        return True

    def save_request(self, user_name, first_name, last_name, contract, unit, scopus_id, orcid_id, researcher_id):
        bt_text = "Inoltra la richiesta di aggiunta di un nuovo ricercatore"
        if self.st.button(bt_text, key="save_request"):
            with self.st.spinner():
                if '@' in user_name and first_name != '' and first_name != '' and unit != '':
                    self.user_name = user_name
                    self.first_name = first_name
                    self.last_name = last_name
                    self.contract = contract
                    self.unit = unit
                    self.scopus_id = scopus_id
                    self.orcid_id = orcid_id
                    self.researcher_id = researcher_id
                    req = self.check_request()
                    if len(req) > 0:
                        msg = 'Una richiesta per l\'utente ' + user_name + ' è già stata inoltrata'
                        status = req[0][0]
                        if status == 0:
                            msg += ' ed è in attesa di conferma da parte degli amministratori'
                        elif status == 1:
                            msg += ' e accettata'
                        elif status == 2:
                            msg += ' e rifiutata da parte degli amministratori'
                        self.st.error(msg)
                        return
                    usr_email = self.check_username()
                    if len(usr_email) > 0:
                        self.st.error('Un utente con l\'email ' + user_name + ' è già presente nel sistema')
                        return
                    usr_name = self.check_name()
                    if len(usr_name) > 0:
                        self.st.error('Un utente per ' + last_name + ' ' + first_name + ' è già presente nel sistema')
                        return
                    if self.insert():
                        self.st.success('La richiesta per il nuovo ricercatore è stata inoltrata correttamente')
                    else:
                        self.st.error('La richiesta per il nuovo ricercatore ha prodotto un errore interno')
                else:
                    self.st.error('Compila correttamente almeno i seguenti campi: email, nome, cognome, unità operativa e Scopus ID')