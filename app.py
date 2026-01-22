import streamlit as st
import pandas as pd
import numpy as np
import time

# --- 1. NASTAVENÍ A PAMĚŤ ---
st.set_page_config(page_title="Investiční Průvodce", page_icon="📈", layout="wide") # Layout wide = využití celé šířky

if 'hledani_hotovo' not in st.session_state:
    st.session_state.hledani_hotovo = False

if 'moje_portfolio' not in st.session_state:
    st.session_state.moje_portfolio = []

KURZ_USD_CZK = 23.50

# --- 2. GENERÁTOR DAT (Demo Grafy & Loga) 🎨 ---
def ziskej_data_o_akcii(ticker):
    # Data: (Cena, Měna, Dividenda, URL Loga)
    # Používáme službu Clearbit pro loga zdarma
    demo_data = {
        "KO": (62.50, "USD", 0.031, "https://logo.clearbit.com/coca-cola.com"),
        "PEP": (169.00, "USD", 0.030, "https://logo.clearbit.com/pepsico.com"),
        "JNJ": (155.40, "USD", 0.029, "https://logo.clearbit.com/jnj.com"),
        "MCD": (290.10, "USD", 0.023, "https://logo.clearbit.com/mcdonalds.com"),
        "AAPL": (185.50, "USD", 0.005, "https://logo.clearbit.com/apple.com"),
        "MSFT": (420.00, "USD", 0.007, "https://logo.clearbit.com/microsoft.com"),
        "TSLA": (175.30, "USD", 0.000, "https://logo.clearbit.com/tesla.com"),
        "NVDA": (850.00, "USD", 0.001, "https://logo.clearbit.com/nvidia.com"),
        "O": (52.30, "USD", 0.055, "https://logo.clearbit.com/realtyincome.com"),
        "XOM": (110.20, "USD", 0.035, "https://logo.clearbit.com/exxonmobil.com")
    }
    return demo_data.get(ticker, (100.00, "USD", 0.02, ""))

def generuj_falesny_graf(ticker, styl):
    # Vytvoříme demo graf vývoje ceny za poslední rok
    # Pokud je styl "Růst", uděláme graf strmější
    np.random.seed(len(ticker)) # Aby graf vypadal pokaždé stejně pro stejnou firmu
    
    start_price = 100
    volatilita = 2 if styl == "Dividenda" else 5 # Růstové skáčou víc
    trend = 0.05 if styl == "Dividenda" else 0.15 # Růstové rostou rychleji
    
    zmeny = np.random.normal(trend, volatilita, 365)
    ceny = start_price + np.cumsum(zmeny)
    
    # Převedeme na Pandas DataFrame pro Streamlit chart
    chart_data = pd.DataFrame(ceny, columns=["Cena"])
    return chart_data

db_akcii = [
    {"ticker": "KO", "name": "Coca-Cola", "styl": "Dividenda", "riziko": "Nízké", "sektor": "Konzum", "duvod": "Legenda. Zvyšuje dividendu 62 let v kuse."},
    {"ticker": "PEP", "name": "PepsiCo", "styl": "Dividenda", "riziko": "Nízké", "sektor": "Konzum", "duvod": "Nejen limonády, ale i brambůrky Lays."},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "styl": "Dividenda", "riziko": "Nízké", "sektor": "Zdraví", "duvod": "Gigant ve zdravotnictví. AAA rating."},
    {"ticker": "MCD", "name": "McDonald's", "styl": "Dividenda", "riziko": "Střední", "sektor": "Gastro", "duvod": "Realitní firma, co prodává burgery."},
    {"ticker": "AAPL", "name": "Apple", "styl": "Růst", "riziko": "Střední", "sektor": "Tech", "duvod": "Ekosystém, ze kterého zákazníci neodchází."},
    {"ticker": "MSFT", "name": "Microsoft", "styl": "Růst", "riziko": "Střední", "sektor": "Tech", "duvod": "Vládce firemního softwaru a cloudu."},
    {"ticker": "TSLA", "name": "Tesla", "styl": "Růst", "riziko": "Vysoké", "sektor": "Tech / Auto", "duvod": "Lídr v EV a robotice. Extrémní volatilita."},
    {"ticker": "NVDA", "name": "Nvidia", "styl": "Růst", "riziko": "Vysoké", "sektor": "Tech", "duvod": "Lopaty pro zlatou horečku AI."},
    {"ticker": "O", "name": "Realty Income", "styl": "Dividenda", "riziko": "Střední", "sektor": "Nemovitosti", "duvod": "Měsíční dividenda! Vlastní tisíce obchodů."},
    {"ticker": "XOM", "name": "Exxon Mobil", "styl": "Dividenda", "riziko": "Střední", "sektor": "Energie", "duvod": "Ropný gigant. Cash cow."},
]

# --- 3. MODÁLNÍ OKNO 🛒 ---
@st.dialog("Potvrzení nákupu")
def nakupni_okno(firma, cena_usd, div_yield, logo_url):
    # Hlavička s logem
    cols = st.columns([1, 4])
    with cols[0]:
        st.image(logo_url, width=50)
    with cols[1]:
        st.subheader(f"{firma['name']}")
        st.caption(f"Cena: {cena_usd} USD")

    st.markdown("---")
    
    typ_nakupu = st.radio("Jak chceš nakupovat?", ["Podle částky (Kč)", "Podle počtu kusů (ks)"], horizontal=True)
    
    if typ_nakupu == "Podle částky (Kč)":
        investice_czk = st.number_input("Kolik chceš investovat (Kč)?", min_value=100, value=2000, step=100)
        investice_usd = investice_czk / KURZ_USD_CZK
        pocet_akcii = investice_usd / cena_usd
    else:
        pocet_akcii = st.number_input("Kolik akcií chceš?", min_value=0.1, value=1.0, step=0.1)
        investice_usd = pocet_akcii * cena_usd
        investice_czk = investice_usd * KURZ_USD_CZK
        st.info(f"Cena: **{int(investice_czk)} Kč**")

    # Výsledky
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Získáš podíl", f"{pocet_akcii:.4f} ks")
    with c2:
        div_czk = (pocet_akcii * cena_usd) * div_yield * KURZ_USD_CZK
        st.metric("Roční dividenda", f"{int(div_czk)} Kč")
    
    if abs(pocet_akcii - round(pocet_akcii)) > 0.001:
        st.info(f"ℹ️ Kupuješ část akcie ({pocet_akcii:.2f} ks).")
    
    if st.button(f"✅ Zaplatit {int(investice_czk)} Kč", type="primary"):
        st.session_state.moje_portfolio.append({
            "ticker": firma['ticker'],
            "name": firma['name'],
            "ks": pocet_akcii,
            "investice": investice_czk,
            "logo": logo_url # Ukládáme i logo
        })
        st.balloons()
        st.success("Koupeno!")
        time.sleep(2)
        st.rerun()

# --- 4. HLAVNÍ UI (LAYOUT) ---

# A) BOČNÍ PANEL (SIDEBAR) 👈
with st.sidebar:
    st.title("🧮 Nastavení")
    st.write("Tady si nastav, co hledáš.")
    
    cil = st.radio("🎯 Tvůj Cíl", ["Dividenda", "Růst"])
    st.markdown("---")
    riziko = st.select_slider("⚖️ Ochota riskovat", options=["Nízké", "Střední", "Vysoké"])
    st.markdown("---")
    vsechny_sektory = sorted(list(set([x['sektor'] for x in db_akcii])))
    oblibene_sektory = st.multiselect("🏭 Sektory", vsechny_sektory, default=vsechny_sektory)
    
    st.markdown("---")
    # Tlačítko hledání dáme sem
    if st.button("🔍 Hledat akcie", type="primary"):
        st.session_state.hledani_hotovo = True

# B) HLAVNÍ PLOCHA 👉
st.title("🦄 Petrův Investiční Průvodce")

# PORTFOLIO (Zobrazujeme jen pokud něco máme)
if len(st.session_state.moje_portfolio) > 0:
    st.info("💼 Tvoje aktivní portfolio")
    cols = st.columns(len(st.session_state.moje_portfolio))
    
    for i, polozka in enumerate(st.session_state.moje_portfolio):
        # Kartička portfolia
        with cols[i]:
            st.image(polozka['logo'], width=40)
            st.metric(polozka['name'], f"{polozka['ks']:.2f} ks")
            st.caption(f"Inv: {int(polozka['investice'])} Kč")
    st.markdown("---")

# VÝSLEDKY HLEDÁNÍ
if st.session_state.hledani_hotovo:
    # Filtrace
    nalezeno = [x for x in db_akcii if x['styl'] == cil and 
               (riziko == x['riziko'] or (riziko == "Střední" and x['riziko'] == "Nízké") or (riziko == "Vysoké")) and
               (not oblibene_sektory or x['sektor'] in oblibene_sektory)]

    if nalezeno:
        st.subheader(f"Nalezeno {len(nalezeno)} příležitostí")
        
        for firma in nalezeno:
            cena, mena, div_yield, logo = ziskej_data_o_akcii(firma['ticker'])
            
            # Karta firmy
            with st.container(border=True):
                # 1. Řádek: Logo + Název + Cena
                hlavicka_col1, hlavicka_col2, hlavicka_col3 = st.columns([1, 5, 2])
                with hlavicka_col1:
                    st.image(logo, width=60)
                with hlavicka_col2:
                    st.subheader(f"{firma['name']} ({firma['ticker']})")
                    st.caption(firma['sektor'])
                with hlavicka_col3:
                    st.metric("Cena", f"{cena} {mena}", delta="+1.2%") # Demo delta
                
                # 2. Řádek: Důvod + Graf
                obsah_col1, obsah_col2 = st.columns([3, 4])
                with obsah_col1:
                    st.info(f"**Proč Jarvis:** {firma['duvod']}")
                    
                    # Motivační text
                    if firma['styl'] == "Dividenda":
                        st.markdown(f"💰 Roční dividenda: **{div_yield*100:.1f} %**")
                    else:
                        st.markdown(f"🚀 Růstový potenciál: **Vysoký**")
                        
                with obsah_col2:
                    # Tady vykreslíme ten graf! 📈
                    chart_data = generuj_falesny_graf(firma['ticker'], firma['styl'])
                    st.line_chart(chart_data, height=150, color="#228B22" if cena > 150 else "#FF4500")

                # 3. Řádek: Akce
                akce_col1, akce_col2 = st.columns([4, 1])
                with akce_col2:
                    if st.button("🛒 Koupit", key=f"btn_{firma['ticker']}", type="primary", use_container_width=True):
                         nakupni_okno(firma, cena, div_yield, logo)
            
            st.write("") # Mezera mezi kartami

    else:
        st.warning("Nic nenalezeno. Zkus změnit filtry vlevo.")
else:
    st.write("👈 Začni tím, že si vlevo nastavíš filtry a klikneš na Hledat.")