import streamlit as st
import pandas as pd
import numpy as np
import time
from fpdf import FPDF
from datetime import datetime

# --- 1. NASTAVENÍ A BUSINESS LOGIKA ---
st.set_page_config(page_title="Investiční Průvodce", page_icon="📈", layout="wide")

# Session State pro uchování stavu
if 'hledani_hotovo' not in st.session_state:
    st.session_state.hledani_hotovo = False
if 'moje_portfolio' not in st.session_state:
    st.session_state.moje_portfolio = []
if 'lead_captured' not in st.session_state:
    st.session_state.lead_captured = False # Zda už nám dal email

KURZ_USD_CZK = 23.50

# --- 2. PDF GENERÁTOR ---
def generuj_pdf(portfolio, jmeno_uzivatele):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Investicni Plan pro: {jmeno_uzivatele}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Vygenerovano: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    
    # Tabulka
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, "Spolecnost", 1)
    pdf.cell(40, 10, "Pocet ks", 1)
    pdf.cell(50, 10, "Investice (CZK)", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=12)
    celkem_kc = 0
    for p in portfolio:
        safe_name = p['name'].encode('latin-1', 'ignore').decode('latin-1')
        pdf.cell(60, 10, safe_name, 1)
        pdf.cell(40, 10, f"{p['ks']:.2f}", 1)
        pdf.cell(50, 10, f"{int(p['investice']):,} CZK", 1)
        pdf.ln()
        celkem_kc += p['investice']
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Celkova hodnota: {int(celkem_kc):,} CZK", ln=True)
    
    pdf.set_font("Arial", 'I', 8)
    pdf.ln(20)
    pdf.multi_cell(0, 5, "UPOZORNENI: Tento dokument je pouze vzdelavaci material. Nejedna se o investicni doporuceni dle zakona o podnikani na kapitalovem trhu. Minule vynosy nejsou zarukou budoucich.")
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. DATA SIMULÁTOR (STABILNÍ) ---
def ziskej_data_simulace(ticker, styl):
    seed = sum(ord(c) for c in ticker)
    np.random.seed(seed)
    
    base_price = np.random.randint(50, 400)
    trend = np.linspace(0, 50 if styl == "Růst" else 10, 100)
    volatilita = np.random.normal(0, 5 if styl == "Růst" else 2, 100)
    
    krivka = base_price + trend + volatilita
    graf_data = pd.DataFrame(krivka, columns=['Close'])
    cena = float(krivka[-1])
    div_yield = 0.03 if styl == "Dividenda" else 0.005
    logo_url = f"https://financialmodelingprep.com/image-stock/{ticker}.png"
    
    return round(cena, 2), "USD", div_yield, logo_url, graf_data

db_akcii = [
    {"ticker": "KO", "name": "Coca-Cola", "styl": "Dividenda", "riziko": "Nízké", "sektor": "Konzum", "duvod": "Legenda."},
    {"ticker": "PEP", "name": "PepsiCo", "styl": "Dividenda", "riziko": "Nízké", "sektor": "Konzum", "duvod": "Lays."},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "styl": "Dividenda", "riziko": "Nízké", "sektor": "Zdraví", "duvod": "AAA rating."},
    {"ticker": "MCD", "name": "McDonald's", "styl": "Dividenda", "riziko": "Střední", "sektor": "Gastro", "duvod": "Realitní firma."},
    {"ticker": "AAPL", "name": "Apple", "styl": "Růst", "riziko": "Střední", "sektor": "Tech", "duvod": "Ekosystém."},
    {"ticker": "MSFT", "name": "Microsoft", "styl": "Růst", "riziko": "Střední", "sektor": "Tech", "duvod": "Cloud."},
    {"ticker": "TSLA", "name": "Tesla", "styl": "Růst", "riziko": "Vysoké", "sektor": "Tech / Auto", "duvod": "Volatilita."},
    {"ticker": "NVDA", "name": "Nvidia", "styl": "Růst", "riziko": "Vysoké", "sektor": "Tech", "duvod": "AI čipy."},
    {"ticker": "O", "name": "Realty Income", "styl": "Dividenda", "riziko": "Střední", "sektor": "Nemovitosti", "duvod": "Měsíční dividenda."},
    {"ticker": "XOM", "name": "Exxon Mobil", "styl": "Dividenda", "riziko": "Střední", "sektor": "Energie", "duvod": "Ropa."},
]

# --- 4. MODÁL NÁKUPU ---
@st.dialog("Potvrzení nákupu")
def nakupni_okno(firma, cena_usd, div_yield, logo_url):
    c1, c2 = st.columns([1, 4])
    with c1:
        if logo_url: st.image(logo_url, width=50)
    with c2:
        st.subheader(firma['name'])
        st.caption(f"Cena: {cena_usd} USD")
    st.markdown("---")
    typ_nakupu = st.radio("Režim:", ["Podle částky (Kč)", "Podle kusů (ks)"], horizontal=True)
    if typ_nakupu == "Podle částky (Kč)":
        investice_czk = st.number_input("Částka v Kč:", min_value=100, value=2000, step=100)
        investice_usd = investice_czk / KURZ_USD_CZK
        pocet_akcii = investice_usd / cena_usd if cena_usd > 0 else 0
    else:
        pocet_akcii = st.number_input("Počet akcií:", min_value=0.1, value=1.0, step=0.1)
        investice_usd = pocet_akcii * cena_usd
        investice_czk = investice_usd * KURZ_USD_CZK
        st.info(f"Cena: **{int(investice_czk)} Kč**")
    
    if st.button(f"✅ Přidat do plánu", type="primary"):
        st.session_state.moje_portfolio.append({
            "ticker": firma['ticker'], "name": firma['name'], "ks": pocet_akcii, "investice": investice_czk, "logo": logo_url
        })
        st.toast("Přidáno! Pokračuj ve výběru nebo stáhni plán.")
        time.sleep(1)
        st.rerun()

# --- 5. HLAVNÍ UI ---
with st.sidebar:
    st.header("🧮 Filtr")
    cil = st.radio("Cíl", ["Dividenda", "Růst"])
    riziko = st.select_slider("Riziko", options=["Nízké", "Střední", "Vysoké"])
    vsechny_sektory = sorted(list(set([x['sektor'] for x in db_akcii])))
    oblibene_sektory = st.multiselect("Sektory", vsechny_sektory, default=vsechny_sektory)
    if st.button("🔍 Najít", type="primary"):
        st.session_state.hledani_hotovo = True

st.title("🦄 Petrův Investiční Průvodce")

# --- SEKCE PORTFOLIO & LEAD MAGNET 🧲 ---
if st.session_state.moje_portfolio:
    with st.container(border=True):
        st.info("💼 Tvoje portfolio (Návrh)")
        
        # Výpis položek
        cols = st.columns(len(st.session_state.moje_portfolio))
        for i, p in enumerate(st.session_state.moje_portfolio):
            with cols[i]:
                if p['logo']: st.image(p['logo'], width=30)
                st.caption(f"{p['ks']:.2f} ks")
        
        st.markdown("---")
        
        # LOGIKA SBĚRU EMAILU (LEAD GATE)
        if not st.session_state.lead_captured:
            st.write("### 🔒 Odemknout Investiční Plán")
            st.write("Zadej email, kam ti máme poslat tvůj personalizovaný plán a přístup do aplikace.")
            
            c1, c2 = st.columns(2)
            with c1:
                jmeno = st.text_input("Tvé jméno")
            with c2:
                email = st.text_input("Tvůj email")
            
            if st.button("🚀 Odeslat a Stáhnout PDF", type="primary"):
                if "@" in email and len(jmeno) > 0:
                    st.session_state.lead_captured = True
                    st.session_state.user_name = jmeno
                    st.success("Plán vygenerován!")
                    st.rerun()
                else:
                    st.error("Prosím vyplň jméno a platný email.")
        else:
            # Uživatel už dal email -> Vidí tlačítko
            st.success(f"Díky, {st.session_state.user_name}! Tady je tvůj plán.")
            pdf_bytes = generuj_pdf(st.session_state.moje_portfolio, st.session_state.user_name)
            
            c_down, c_broker = st.columns(2)
            with c_down:
                st.download_button("📄 Stáhnout PDF", pdf_bytes, "investicni_plan.pdf", "application/pdf", type="primary")
            with c_broker:
                # Simulace odkazu na brokera
                st.link_button("🏦 Otevřít účet u Brokera (Demo)", "https://www.xtb.com/cz")

# --- VÝPIS AKCIÍ ---
if st.session_state.hledani_hotovo:
    nalezeno = [x for x in db_akcii if x['styl'] == cil and 
               (riziko == x['riziko'] or (riziko == "Střední" and x['riziko'] == "Nízké") or (riziko == "Vysoké")) and
               (not oblibene_sektory or x['sektor'] in oblibene_sektory)]

    if nalezeno:
        st.subheader(f"Nalezeno {len(nalezeno)} příležitostí")
        with st.spinner('Analyzuji trh...'):
            time.sleep(0.3)
            for firma in nalezeno:
                cena, mena, div_yield, logo, graf_data = ziskej_data_simulace(firma['ticker'], firma['styl'])
                
                with st.container(border=True):
                    h1, h2, h3 = st.columns([1, 4, 2])
                    with h1: 
                        if logo: st.image(logo, width=50)
                        else: st.write("📷")
                    with h2:
                        st.subheader(f"{firma['name']}")
                        st.caption(f"{firma['sektor']}")
                    with h3:
                        st.metric("Cena", f"{cena} {mena}")
                    
                    c_graf, c_akce = st.columns([3, 1])
                    with c_graf:
                        st.area_chart(graf_data, height=120)
                    with c_akce:
                        st.write("")
                        st.write("")
                        if st.button("Do plánu", key=f"btn_{firma['ticker']}", type="primary", use_container_width=True):
                            nakupni_okno(firma, cena, div_yield, logo)
    else:
        st.warning("Zkus změnit filtry.")
else:
    st.info("👈 Nastav filtry a jdeme najít tvou první investici.")

# --- PRÁVNÍ PATIČKA (DISCLAIMER) ---
st.markdown("---")
st.caption("⚠️ **Upozornění:** Tato aplikace slouží pouze k edukativním účelům. Nejedná se o investiční doporučení. Investování na kapitálových trzích nese riziko ztráty. Minulé výnosy nejsou zárukou budoucích.")
