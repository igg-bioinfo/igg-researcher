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
last_name = st.text_input("Cognome:", value=investigator.last_name if investigator.last_name else "")
if first_name == "" or last_name == "":
    st.error("Compila il tuo nome e cognome correttamente")
set_prop(st, "Età", investigator.age)
contract = st.text_input("Contratto:", value=investigator.contract if investigator.contract else "")
unit = st.text_input("Unità operativa:", value=investigator.unit if investigator.unit else "")
scopus_id = st.text_input("SCOPUS ID:", value=investigator.scopus_id if investigator.scopus_id else "")

orcid_id = st.text_input("ORCID ID:", value=investigator.orcid_id if investigator.orcid_id else "")
researcher_id = st.text_input("Researcher ID:", value=investigator.researcher_id if investigator.researcher_id else "")
investigator.save_data(first_name, last_name, user_name, contract, unit, scopus_id, orcid_id, researcher_id)

if investigator.first_name != "" or investigator.last_name != "":
    st.markdown("---")
    st.markdown("**Controlla su Scopus di non avere identificativi doppi a tuo nome al seguente link:**")
    html = ""
    html += "<a href='https://www.scopus.com/results/authorNamesList.uri?name=name&st1="
    names = first_name.split(" ")
    name_initials = []
    for n in names:
        name_initials.append(n[0])
    html += last_name.replace(" ", "+") + "&st2=" + "+".join(name_initials) + "&origin=searchauthorlookup'>"
    html += "Link a Scopus</a>"
    st.markdown(html, unsafe_allow_html=True)
    st.markdown("**In caso di identificativi multipli:**")
    st.markdown("* Loggati a Scopus con le tue credenziali")
    st.markdown("* Seleziona gli identificativi multipli")
    st.markdown("* Clicca sull'opzione 'Request to merge authors'")
    st.markdown("* Segui le istruzioni della banca dati")
else:
    st.markdown("**Una volta inseriti nome e cognome, comparirà un link che ti reindirizzerà a Scopus per controllare eventuali duplicati.**")
st.markdown("---")

st.markdown("#### Metriche da Scopus")
year_current = datetime.now().year
investigator.get_metrics(year_current)
st.write("Ultimo aggiornamento: **" + str(investigator.metrics_date) + "**")
has_all_pucs = investigator.check_pucs()
if has_all_pucs:
    investigator.get_pucs(year_current)
col_5years, col_10years, col_all = st.columns([1,1,1])
with col_5years:
    st.write("**Ultimi 5 anni (escluso anno corrente)**")
    set_prop(st, "H-index", investigator.hindex5)
    set_prop(st, "Pubblicazioni", investigator.n_pubs5)
    set_prop(st, "Citazioni", investigator.all_cited5)
    set_prop(st, "PUC", investigator.pucs5 if has_all_pucs else None)
with col_10years:
    st.write("**Ultimi 10 anni (escluso anno corrente)**")
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
st.write("Pubblicazioni ricavate unicamente dalla banca dati Scopus")
year_pubs = select_year(st, True)
investigator.get_pubs(year_pubs)

db.close()
#   conda activate streamlit
#   streamlit run 0_Home.py
#   sudo systemctl start researcher.service
#   sudo systemctl stop researcher.service