import streamlit as st
from utils import set_title, select_year
from classes.db_psql import *
from classes.user import *
from classes.demo import *
from classes.scopus import *

set_title(st, "IGG Ricercatore")

db = DB(st)
db.connect()
investigator = User(st, db)
if investigator.login() == False:
    investigator.is_logged(False)
investigator.get_investigator()
if investigator.is_inv == False:
    investigator.is_logged(False)

st.markdown("#### Dati del ricercatore")
if investigator.update_date:
    st.write("Ultimo aggiornamento dei dati: **" + str(investigator.update_date) + "**")
user_name = st.text_input("Email Gaslini / username:", value=investigator.user_name if investigator.user_name else "")
first_name = st.text_input("Nome:", value=investigator.first_name if investigator.first_name else "")
surname = st.text_input("Cognome:", value=investigator.last_name if investigator.last_name else "")
set_prop(st, "Età", investigator.age)
contract = st.text_input("Contratto:", value=investigator.contract if investigator.contract else "")
unit = st.text_input("Unità operativa:", value=investigator.unit if investigator.unit else "")
#set_prop(st, "Contratto", investigator.contract)
scopus_id = st.text_input("SCOPUS ID:", value=investigator.scopus_id if investigator.scopus_id else "")
orcid_id = st.text_input("ORCID ID:", value=investigator.orcid_id if investigator.orcid_id else "")
researcher_id = st.text_input("Researcher ID:", value=investigator.researcher_id if investigator.researcher_id else "")
investigator.save_ids(first_name, surname, user_name, contract, scopus_id, orcid_id, researcher_id)
st.markdown("---")

st.markdown("#### Metriche da Scopus")
year_current = datetime.now().year
investigator.get_metrics(year_current)
st.write("Ultimo aggiornamento: **" + str(investigator.metrics_date) + "**")
has_all_pucs = investigator.check_pucs(year_current)
if has_all_pucs:
    investigator.get_pucs(year_current)
col_5years, col_10years, col_all = st.columns([1,1,1])
with col_5years:
    st.write("**Ultimi 5 anni**")
    set_prop(st, "H-index", investigator.hindex5)
    set_prop(st, "Pubblicazioni", investigator.n_pubs5)
    set_prop(st, "Citazioni", investigator.all_cited5)
    set_prop(st, "PUC", investigator.pucs5 if has_all_pucs else None)
with col_10years:
    st.write("**Ultimi 10 anni**")
    set_prop(st, "H-index", investigator.hindex10)
    set_prop(st, "Pubblicazioni", investigator.n_pubs10)
    set_prop(st, "Citazioni", investigator.all_cited10)
    set_prop(st, "PUC", investigator.pucs10 if has_all_pucs else None)
with col_all:
    st.write("**Totale**")
    set_prop(st, "H-index", investigator.hindex)
    set_prop(st, "Pubblicazioni", investigator.n_pubs)
    set_prop(st, "Citazioni", investigator.all_cited)
    set_prop(st, "PUC", investigator.pucs if has_all_pucs else None)
st.markdown("---")

st.markdown("#### Pubblicazioni di Scopus")
st.write("Pubblicazioni ricavate unicamente dalla banca dati Scopus (se registrato su Scopus viene riportato anche l'identificativo di PubMed PMID)")
year_pubs = select_year(st, True)
investigator.get_pubs(year_pubs)

db.close()
#   conda activate streamlit
#   streamlit run 0_Home.py
#   sudo systemctl start researcher.service
#   sudo systemctl stop researcher.service