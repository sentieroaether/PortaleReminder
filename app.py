import pandas as pd
from datetime import datetime, timedelta
import hashlib
import time
import os
import streamlit as st
import json
import urllib.parse

# Funzione per generare hash della password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Carica le credenziali da un file JSON
def load_users(file='users.json'):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)  # Ritorna le credenziali come dizionario
    else:
        return {}  # Se il file non esiste, ritorna un dizionario vuoto

# Salva le credenziali in un file JSON
def save_users(users, file='users.json'):
    with open(file, 'w') as f:
        json.dump(users, f)


# Funzione per verificare le credenziali
def check_credentials(username, password):
    return username in USERS and USERS[username] == hash_password(password)

USERS = load_users()

def change_password(username):
    st.subheader("Cambia la tua password")

    # Campo per inserire la vecchia password
    old_password = st.text_input("Vecchia Password", type="password", key="old_password")

    # Campo per inserire la nuova password
    new_password = st.text_input("Nuova Password", type="password", key="new_password")

    # Campo per confermare la nuova password
    confirm_password = st.text_input("Conferma Nuova Password", type="password", key="confirm_password")

    # Bottone per confermare il cambio di password
    if st.button("Cambia Password", key="change_password_button"):
        users = load_users()  # Carica le credenziali esistenti
        if not check_credentials(username, old_password):
            st.error("La vecchia password non è corretta.")
        elif new_password != confirm_password:
            st.error("Le nuove password non corrispondono.")
        elif len(new_password) < 6:
            st.error("La nuova password deve essere lunga almeno 6 caratteri.")
        else:
            # Cambia la password
            users[username] = hash_password(new_password)  # Aggiorna l'hash della password
            save_users(users)  # Salva le credenziali aggiornate nel file JSON
            st.success("Password cambiata con successo!")
            
            # Effettua il logout e reindirizza alla schermata di login
            st.session_state.logged_in = False
            st.experimental_rerun()  # Reindirizza alla schermata di login


# File degli appuntamenti
appointment_file = 'appuntamenti.xlsx'

# Funzione per caricare gli appuntamenti
def load_appointments(file):
    if os.path.exists(file):
        return pd.read_excel(file)
    else:
        return pd.DataFrame(columns=["Nome", "Cognome", "Cellulare", "Tipo Visita", "Giorno Visita", "Ora Visita"])

# Funzione per salvare gli appuntamenti
def save_appointments(df, file):
    df.to_excel(file, index=False)

# Funzione per formattare i dati
def format_appointments(df):
    df['Cellulare'] = df['Cellulare'].apply(lambda x: str(x).replace(',', '').strip())
    df['Giorno Visita'] = pd.to_datetime(df['Giorno Visita']).dt.strftime('%Y-%m-%d')
    df['Ora Visita'] = df['Ora Visita'].apply(lambda x: x.strftime('%H:%M') if isinstance(x, datetime) else x)
    return df


# Funzione per formattare il numero di telefono con il prefisso internazionale
def format_phone_number(phone_number):
    phone_number = str(phone_number).strip().replace(' ', '').replace(',', '')
    if not phone_number.startswith('39'):  # Prefisso per l'Italia senza segno +
        phone_number = '39' + phone_number
    return phone_number

# Funzione per generare il link WhatsApp con messaggio precompilato
def generate_whatsapp_link(numero, messaggio):
    numero = format_phone_number(numero)
    encoded_message = urllib.parse.quote(messaggio, safe='')  # Codifica corretta del messaggio, safe='' codifica tutti i caratteri speciali
    whatsapp_link = f"https://wa.me/{numero}?text={encoded_message}"
    return whatsapp_link

# Funzione per inviare un messaggio WhatsApp tramite link
def send_whatsapp_message_instantly(numero, messaggio):
    try:
        link = generate_whatsapp_link(numero, messaggio)  # Genera il link per WhatsApp
        st.markdown(f'<a href="{link}" target="_blank">Clicca qui per inviare il messaggio a {numero}</a>', unsafe_allow_html=True)  # Forza apertura in nuova tab
        st.success("")
    except Exception as e:
        st.error(f"Errore durante la generazione del link WhatsApp: {e}")

# Funzione per creare il messaggio dinamico
def create_message(nome, cognome, tipo_visita, giorno_visita, ora_visita):
    giorno_visita_formattato = giorno_visita.strftime(f'%A %d %B %Y')  # Formatta la data nel formato desiderato
    messaggio = (f"Gentile {nome} {cognome}, ti ricordiamo il tuo appuntamento "
                 f"per {tipo_visita} il giorno {giorno_visita_formattato} alle ore {ora_visita} "
                 f"presso lo studio della dottoressa Pezzella.")
    return messaggio

# Mappatura dei giorni della settimana e mesi in italiano
giorni_settimana = ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica']
mesi = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre']

# Funzione per creare la vista settimanale con pulsanti interattivi
def create_weekly_view(df, start_date):
    df['Data e Ora Visita'] = pd.to_datetime(df['Giorno Visita'] + ' ' + df['Ora Visita'], format='%Y-%m-%d %H:%M', errors='coerce')
    df = df.dropna(subset=['Data e Ora Visita'])

    days_in_week = [start_date + timedelta(days=i) for i in range(7)]
    appointments_per_day = df.groupby(df['Data e Ora Visita'].dt.date).size().to_dict()

    weekly_data = []
    for i, day in enumerate(days_in_week):
        appointments = appointments_per_day.get(day.date(), 0)
        day_of_week = giorni_settimana[day.weekday()]
        day_display = f"<strong>{day_of_week}</strong><br>{day.day}<br>{appointments} app."
        if st.button(f"Vedi pazienti {day_of_week}", key=f"day_{i}"):
            st.session_state.selected_day = day.strftime('%Y-%m-%d')
        weekly_data.append(day_display)

    return weekly_data

# Funzione per mostrare i pazienti di un determinato giorno
def show_patients_for_day(df, selected_date):
    selected_patients = df[df['Giorno Visita'] == selected_date]
    st.subheader(f"Appuntamenti per il giorno {datetime.strptime(selected_date, '%Y-%m-%d').strftime('%d/%m/%Y')}")

    if selected_patients.empty:
        st.write("Nessun appuntamento per questo giorno.")

    else:

        for index, row in selected_patients.iterrows():
            col1, col2, col3, col4, col6, col7, col8 = st.columns([2, 2, 2, 2, 1, 1, 1])
            col1.write(row['Nome'])
            col2.write(row['Cognome'])
            col3.write(row['Cellulare'])
            col4.write(row['Tipo Visita'])
            col6.write(row['Ora Visita'])

            if col7.button('✏️', key=f"modifica_{index}"):
                st.session_state['editing_row'] = index

        if col8.button('❌', key=f"elimina_{index}"):
            if index in df.index:  # Check if the index is valid
                df = df.drop(index)
                save_appointments(df, appointment_file)
                st.success(f"Appuntamento per {row['Nome']} {row['Cognome']} eliminato correttamente!")
                st.experimental_set_query_params(refresh=datetime.now().timestamp())
            else:
                st.error("L'appuntamento non esiste più o è già stato eliminato.")

    # Gestisci la modifica di un appuntamento
    if 'editing_row' in st.session_state:
        # Verifica se l'indice è ancora valido
        if st.session_state['editing_row'] not in selected_patients.index:
            st.error("Indice non valido, probabilmente l'appuntamento è stato eliminato.")
            # Resetta lo stato solo in caso di errore per evitare altre operazioni
            del st.session_state['editing_row']
        else:
            # Usa il metodo .iloc per selezionare la riga basata sulla posizione
            row = selected_patients.iloc[st.session_state['editing_row']]
            st.subheader("Modifica l'appuntamento")
            
            # Input fields
            nome = st.text_input("Nome", value=row['Nome'])
            cognome = st.text_input("Cognome", value=row['Cognome'])
            cellulare = st.text_input("Cellulare", value=row['Cellulare'])
            tipo_visita = st.selectbox("Tipo di visita", ["Terapia", "Visita posturale", "Check-up Completo"], 
                                        key=f"selectbox_tipo_visita_{st.session_state['editing_row']}")
            giorno_visita = st.date_input("Giorno Visita", value=pd.to_datetime(row['Giorno Visita']))

            # Gestione dell'orario in modo sicuro
            try:
                ora_visita = st.time_input("Ora Visita", value=datetime.strptime(row['Ora Visita'], '%H:%M:%S').time())
            except ValueError:
                ora_visita = st.time_input("Ora Visita", value=datetime.strptime(row['Ora Visita'], '%H:%M').time())

            # Salvare le modifiche
            if st.button("Salva modifiche"):
                # Verifica di nuovo che l'indice esista ancora per evitare accessi invalidi
                if st.session_state['editing_row'] in selected_patients.index:
                    # Aggiorna il DataFrame con i nuovi valori
                    df.at[selected_patients.index[st.session_state['editing_row']], 'Nome'] = nome
                    df.at[selected_patients.index[st.session_state['editing_row']], 'Cognome'] = cognome
                    df.at[selected_patients.index[st.session_state['editing_row']], 'Cellulare'] = cellulare
                    df.at[selected_patients.index[st.session_state['editing_row']], 'Tipo Visita'] = tipo_visita
                    df.at[selected_patients.index[st.session_state['editing_row']], 'Giorno Visita'] = giorno_visita.strftime('%Y-%m-%d')
                    df.at[selected_patients.index[st.session_state['editing_row']], 'Ora Visita'] = ora_visita.strftime('%H:%M')

                    save_appointments(df, appointment_file)
                    st.success("Modifiche salvate correttamente!")

                else:
                    st.error("Non è possibile salvare. L'appuntamento è stato rimosso.")
                    del st.session_state['editing_row']

                    # Resetta lo stato solo dopo il salvataggio
                    del st.session_state['editing_row']

# Interfaccia utente con login
st.title("Portale Appuntamenti")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Aggiungiamo uno stato per gestire se si deve mostrare solo il form di cambio password
if "show_change_password" not in st.session_state:
    st.session_state.show_change_password = False

if not st.session_state.logged_in and not st.session_state.show_change_password:
    # Mostra la schermata di login
    st.subheader("Accedi al portale")
    username_input = st.text_input("Nome utente")
    password = st.text_input("Password", type="password")
    login_button = st.button("Login")

    if login_button:
        if check_credentials(username_input, password):
            st.session_state.logged_in = True
            st.session_state.username = username_input
            st.success("Login riuscito!")
        else:
            st.error("Credenziali non valide. Riprova.")
elif st.session_state.show_change_password:
    # Mostra solo il form di cambio password
    change_password(st.session_state.username)
else:
    # Se l'utente è loggato, mostra l'interfaccia con il calendario e altro
    st.sidebar.title(f"Benvenuta, Dott.ssa Pezzella")
    st.sidebar.write("[Logout](#)")

    # Aggiungi il pulsante per mostrare la sezione di cambio password
    if st.sidebar.button("Cambia Password"):
        st.session_state.show_change_password = True

    # Mostra le tabs solo se l'utente non sta cambiando la password
    df = load_appointments(appointment_file)
    df = format_appointments(df)

    tab1, tab2, tab3 = st.tabs(["Calendario Appuntamenti", "Nuovo Appuntamento", "Invia Messaggi WhatsApp"])

    with tab1:
        if 'current_week_start' not in st.session_state:
            st.session_state.current_week_start = datetime.now() - timedelta(days=datetime.now().weekday())

        col1, col2, col3 = st.columns([1, 0.05, 1])

        with col1:
            if st.button("←"):
                st.session_state.current_week_start -= timedelta(weeks=1)
        with col2:
            if st.button("→"):
                st.session_state.current_week_start += timedelta(weeks=1)

        df = load_appointments(appointment_file)
        df = format_appointments(df)

        days_in_week = [st.session_state.current_week_start + timedelta(days=i) for i in range(7)]
        st.markdown(f"**{days_in_week[0].strftime(f'{giorni_settimana[days_in_week[0].weekday()]} %d {mesi[days_in_week[0].month-1]} %Y')} - "
                    f"{days_in_week[6].strftime(f'{giorni_settimana[days_in_week[6].weekday()]} %d {mesi[days_in_week[6].month-1]} %Y')}**")

        cols = st.columns(7)
        for i, day in enumerate(days_in_week):
            day_str = day.strftime('%Y-%m-%d')
            appointments_count = df[df['Giorno Visita'] == day_str].shape[0]

            with cols[i]:
                st.markdown(f"**{giorni_settimana[day.weekday()]}**")
                st.markdown(f"{day.day}")

                if st.button(f"{appointments_count} app.", key=f"day_{i}"):
                    st.session_state.selected_day_index = i

        if 'selected_day_index' in st.session_state:
            selected_day = days_in_week[st.session_state.selected_day_index]
            selected_day_str = selected_day.strftime('%Y-%m-%d')
            show_patients_for_day(df, selected_day_str)

    with tab2:
        st.header("Aggiungi un nuovo appuntamento")
        nome = st.text_input("Nome del paziente")
        cognome = st.text_input("Cognome del paziente")
        cellulare = st.text_input("Numero di cellulare")
        tipo_visita = st.selectbox("Tipo di visita", ["Terapia", "Visita posturale", "Check-up Completo"])
        giorno_visita = st.date_input("Giorno della visita", datetime.now())
        
        # Inizializza il campo 'Ora della visita' senza impostare il valore corrente
        ora_visita = st.time_input("Ora della visita")  # Rimuovi l'inizializzazione con ora corrente

        if st.button("Aggiungi Appuntamento"):
            if nome and cognome and cellulare and tipo_visita and giorno_visita and ora_visita:
                # Crea una nuova riga nel DataFrame con i dati
                nuovo_appuntamento = pd.DataFrame({
                    "Nome": [nome],
                    "Cognome": [cognome],
                    "Cellulare": [cellulare],
                    "Tipo Visita": [tipo_visita],
                    "Giorno Visita": [giorno_visita.strftime('%Y-%m-%d')],
                    "Ora Visita": [ora_visita.strftime('%H:%M')]
                })
        
                # Aggiungi il nuovo appuntamento al DataFrame esistente e salvalo
                df = pd.concat([df, nuovo_appuntamento], ignore_index=True)
                save_appointments(df, appointment_file)
                st.success("Appuntamento aggiunto con successo!")
            else:
                st.error("Per favore, compila tutti i campi prima di aggiungere l'appuntamento.")

    with tab3:
        st.header("Invia Messaggi WhatsApp")
        giorno_selezionato = st.date_input("Seleziona la data")
        
        if st.button("Invia reminder a tutti i pazienti del giorno"):
            pazienti_giorno = df[df['Giorno Visita'] == giorno_selezionato.strftime('%Y-%m-%d')]

            if not pazienti_giorno.empty:
                for index, paziente in pazienti_giorno.iterrows():
                    numero = paziente['Cellulare']
                    nome = paziente['Nome']
                    cognome = paziente['Cognome']
                    tipo_visita = paziente['Tipo Visita']
                    giorno_visita = pd.to_datetime(paziente['Giorno Visita'])
                    ora_visita = paziente['Ora Visita']

                    giorno_visita_formattato = giorno_visita.strftime(f'{giorni_settimana[giorno_visita.weekday()]} %d {mesi[giorno_visita.month-1]} %Y')
                    messaggio = (f"Gentile {nome} {cognome}, ti ricordiamo il tuo appuntamento "
                                 f"per {tipo_visita} il giorno {giorno_visita_formattato} alle ore {ora_visita} "
                                 f"presso lo studio della dottoressa Pezzella.")
                    send_whatsapp_message_instantly(numero, messaggio)
            else:
                st.error(f"Nessun paziente trovato per il giorno {giorno_selezionato.strftime('%Y-%m-%d')}")
