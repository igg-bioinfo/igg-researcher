import streamlit as st
from utils import set_title
from classes.db_psql import *
from classes.user import *
from classes.user_request import *

set_title(st, "Richiesta per un nuovo ricercatore")

db = DB(st)
db.connect()
st.markdown("E' possibile fare richiesta di aggiunta per un nuovo ricercatore non ancora presente in anagrafica.")
user_name = st.text_input("Email Gaslini / username:", value="")
first_name = st.text_input("Nome:", value="")
surname = st.text_input("Cognome:", value="")
contract = st.text_input("Contratto:", value="")
unit = st.text_input("Unità operativa:", value="")
scopus_id = st.text_input("SCOPUS ID:", value="")
orcid_id = st.text_input("ORCID ID:", value="")
researcher_id = st.text_input("Researcher ID:", value="")

user = User_request(st, db)
user.save_request(first_name, surname, user_name, contract, unit, scopus_id, orcid_id, researcher_id)

db.close()