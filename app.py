import streamlit as st
import pandas as pd
import numpy as np # Přidali jsme Numpy na generování čísel
import time
from fpdf import FPDF
from datetime import datetime

# --- 1. NASTAVENÍ ---
st.set_page_config(page_title="Investiční Průvodce", page_icon="📈", layout="wide")

if 'hledani_hotovo' not in st.session_state:
    st.session_state.hledani_hotovo = False

if 'moje_portfolio' not in st.session_state:
    st.session_state.moje_portfolio = []

KURZ_USD_CZK = 23.50

# --- 2. PDF FUNKCE (Bezpečná) ---
def generuj_pdf(portfolio):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Petruv Investicni Plan", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Vygenerovano: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
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
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. DATA (SIMULÁTOR 🎮) ---
# Toto nahrazuje yfinance. Generujeme data matematicky.
# Je to 1000x rychlejší a nepadá to.
def ziskej_data_simulace(ticker, styl):
    # Unikátní "náhoda" pro každou firmu (aby graf vypadal vždy stejně pro stejnou firmu)
    seed = sum(ord(c) for c in ticker)
    np.random.seed(seed)
    
    # Cena podle stylu
    base_price = np.random.randint(50, 400)
    if styl == "Růst":
        trend = np.linspace(0, 50, 100) # Roste rychle
        volatilita = np.random.normal(0, 5, 100)
    else:
        trend = np.linspace(0, 10, 100) # Roste pomalu
        volatilita = np.random.normal(0, 2, 100)
        
    # Vytvoření grafu
    krivka = base_price + trend + volatilita
    graf_data = pd.DataFrame(krivka, columns=['Close'])
    
    # Aktuální cena je poslední bod grafu
    cena = float(krivka[-1])
    
    # Dividenda
    div_yield = 0.03 if styl == "Dividenda" else 0.005
    
    # Logo (použijeme online, to většinou nevadí)
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

# --- 4. MODÁL ---
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

    c1, c2 = st.columns(2)
    with c1: st.metric("Kupuješ", f"{pocet_akcii:.4f} ks")
    with c2: 
        div_czk = (pocet_akcii * cena_usd) * div_yield * KURZ_USD_CZK
        st.metric("Roční dividenda", f"{int(div_czk)} Kč")
    
    if st.button(f"✅ Koupit", type="primary"):
        st.session_state.moje_portfolio.append({
            "ticker": firma['ticker'], "name": firma['name'], "ks": pocet_akcii, "investice": investice_czk, "logo": logo_url
        })
        st.balloons()
        st.success("Hotovo!")
        time.sleep(1)
        st.rerun()

# --- 5. UI ---
with st.sidebar:
    st.header("🧮 Filtr")
    cil = st.radio("Cíl", ["Dividenda", "Růst"])
    st.markdown("---")
    riziko = st.select_slider("Riziko", options=["Nízké", "Střední", "Vysoké"])
    st.markdown("---")
    vsechny_sektory = sorted(list(set([x['sektor'] for x in db_akcii])))
    oblibene_sektory = st.multiselect("Sektory", vsechny_sektory, default=vsechny_sektory)
    st.markdown("---")
    if st.button("🔍 Najít", type="primary"):
        st.session_state.hledani_hotovo = True

st.title("🦄 Petrův Investiční Průvodce")

if st.session_state.moje_portfolio:
    st.info("💼 Tvoje portfolio")
    col_port, col_export = st.columns([3, 1])
    with col_port:
        cols = st.columns(len(st.session_state.moje_portfolio))
        for i, p in enumerate(st.session_state.moje_portfolio):
            with cols[i]:
                if p['logo']: st.image(p['logo'], width=30)
                st.caption(f"{p['ticker']}: {p['ks']:.2f} ks")
    with col_export:
        pdf_bytes = generuj_pdf(st.session_state.moje_portfolio)
        st.download_button("📄 Stáhnout Plán", pdf_bytes, "investicni_plan.pdf", "application/pdf", type="secondary")
    st.markdown("---")

if st.session_state.hledani_hotovo:
    nalezeno = [x for x in db_akcii if x['styl'] == cil and 
               (riziko == x['riziko'] or (riziko == "Střední" and x['riziko'] == "Nízké") or (riziko == "Vysoké")) and
               (not oblibene_sektory or x['sektor'] in oblibene_sektory)]

    if nalezeno:
        st.subheader(f"Nalezeno {len(nalezeno)} akcií")
        # Simulace chvilkového načítání pro efekt
        with st.spinner('Analyzuji trh...'):
            time.sleep(0.5) 
            
        for firma in nalezeno:
            # POUŽÍVÁME SIMULÁTOR MÍSTO YFINANCE
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
                    st.area_chart(graf_data, height=120) # Tady už barvu neřešíme, ať je to safe
                        
                with c_akce:
                    st.write("")
                    st.write("")
                    if st.button("🛒", key=f"btn_{firma['ticker']}", type="primary", use_container_width=True):
                        nakupni_okno(firma, cena, div_yield, logo)

    else:
        st.warning("Zkus změnit filtry.")
else:
    st.write("👈 Nastav filtry a jdeme na to.")
