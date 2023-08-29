import pandas as pd
from datetime import datetime 
from utils import *

class User_request:
    first_name = ''
    surname = ''
    user_name = ''
    contract = ''
    unit = ''
    scopus_id = ''
    orcid_id = ''
    researcher_id = ''

    def __init__(self, st, db):
        self.st = st
        self.db = db

    def save_request(self, first_name, surname, user_name, contract, unit, scopus_id, orcid_id, researcher_id):
        bt_text = "Inoltra la richiesta di aggiunta di un nuovo ricercatore"
        if self.st.button(bt_text, key="save_request"):
            with self.st.spinner():
                pass