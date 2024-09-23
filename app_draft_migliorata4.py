import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import hashlib
import pyautogui
import time
import os
import pywhatkit as kit

# Funzione per generare hash della password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Credenziali simulate
USERS = {
    'dottoressa': hash_password('dottoressa')
}

# Funzione per verificare le credenziali
def check_credentials(username, password):
    return username in USERS and USERS[username] == hash_password(password)

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
    if not phone_number.startswith('+'):
        phone_number = '+39' + phone_number
    return phone_number

# Funzione per inviare un messaggio WhatsApp
def send_whatsapp_message_instantly(numero, messaggio):
    try:
        numero = format_phone_number(numero)
        kit.sendwhatmsg_instantly(numero, messaggio)
        time.sleep(10)
        pyautogui.press('enter')
        st.success(f"Messaggio inviato correttamente a {numero}")
    except Exception as e:
        st.error(f"Errore durante l'invio del messaggio: {e}")

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
    
    for index, row in selected_patients.iterrows():
        col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1, 1, 2, 2, 2, 2, 1, 1])
        col1.write(row['Nome'])
        col2.write(row['Cognome'])
        col3.write(row['Cellulare'])
        col4.write(row['Tipo Visita'])
        col5.write(row['Giorno Visita'])
        col6.write(row['Ora Visita'])

        if col7.button('✏️', key=f"modifica_{index}"):
            st.session_state['editing_row'] = index

        if col8.button('❌', key=f"elimina_{index}"):
            df = df.drop(index)
            save_appointments(df, appointment_file)
            st.success(f"Appuntamento per {row['Nome']} {row['Cognome']} eliminato correttamente!")
            st.experimental_rerun()

    # Gestisci la modifica di un appuntamento
    if 'editing_row' in st.session_state:
        row = selected_patients.iloc[st.session_state['editing_row']]
        st.subheader("Modifica l'appuntamento")
        nome = st.text_input("Nome", value=row['Nome'])
        cognome = st.text_input("Cognome", value=row['Cognome'])
        cellulare = st.text_input("Cellulare", value=row['Cellulare'])
        tipo_visita = st.selectbox("Tipo di visita", ["Terapia", "Visita posturale", "Check-up Completo"], key=f"selectbox_{index}")
        giorno_visita = st.date_input("Giorno Visita", value=pd.to_datetime(row['Giorno Visita']))
        ora_visita = st.time_input("Ora Visita", value=datetime.strptime(row['Ora Visita'], '%H:%M').time())

        if st.button("Salva modifiche"):
            df.at[st.session_state['editing_row'], 'Nome'] = nome
            df.at[st.session_state['editing_row'], 'Cognome'] = cognome
            df.at[st.session_state['editing_row'], 'Cellulare'] = cellulare
            df.at[st.session_state['editing_row'], 'Tipo Visita'] = tipo_visita
            df.at[st.session_state['editing_row'], 'Giorno Visita'] = giorno_visita.strftime('%Y-%m-%d')
            df.at[st.session_state['editing_row'], 'Ora Visita'] = ora_visita.strftime('%H:%M')

            save_appointments(df, appointment_file)
            st.success("Modifiche salvate correttamente!")
            del st.session_state['editing_row']
            st.query_params (refresh=datetime.now().timestamp())

# Interfaccia utente con login
st.title("Portale Appuntamenti - Studio della Dott.ssa Pezzella")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
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
else:
    st.sidebar.title(f"Benvenuta, {st.session_state.username}")
    st.sidebar.write("[Logout](#)")

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
        ora_visita = st.time_input("Ora della visita", datetime.now().time())

        

        if st.button("Aggiungi Appuntamento"):
            nuovo_appuntamento = {
                "Nome": nome,
                "Cognome": cognome,
                "Cellulare": cellulare,
                "Tipo Visita": tipo_visita,
                "Giorno Visita": giorno_visita.strftime('%Y-%m-%d'),
                "Ora Visita": ora_visita.strftime('%H:%M')
            }
            df = pd.concat([df, pd.DataFrame([nuovo_appuntamento])], ignore_index=True)
            save_appointments(df, appointment_file)
            st.success(f"Appuntamento aggiunto per {nome} {cognome}")

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
