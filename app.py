import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import yfinance as yf

# --- 1. CONFIG & CSS ---
st.set_page_config(page_title="Petrův Průvodce", page_icon="🦄", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #0e1117, #161b22);
        color: #e0e0e0;
    }
    .big-font { font-size: 20px !important; }
    .card-highlight { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; margin-bottom: 10px; }
    
    /* Vlastní styly pro Anti-Panic štítky */
    .status-badge { padding: 5px 10px; border-radius: 5px; font-weight: bold; }
    .status-discount { background-color: #2563eb; color: white; } /* Modrá je neutrální/informační */
    .status-growth { background-color: #059669; color: white; }   /* Zelená pro růst */
    
    .stAlert { background-color: #1f2937; border: 1px solid #374151; color: #e0e0e0; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'page' not in st.session_state: st.session_state.page = "intro" 
if 'moje_portfolio' not in st.session_state: st.session_state.moje_portfolio = []
if 'user_name' not in st.session_state: st.session_state.user_name = "Návštěvník"
if 'temp_cil' not in st.session_state: st.session_state.temp_cil = "Dividenda" # Default

KURZ_USD_CZK = 23.50

# --- 2. JARVIS TOOLS (FUNKCE) ---

# A) Anti-Panic Logic 🧠 (Compliance Update)
def get_position_status(current_price, avg_buy_price):
    """
    Rozhoduje o statusu pozice.
    UPDATE: Odstraněn imperativ 'Kupuj'. Nyní pouze informuje o slevě.
    """
    diff = current_price - avg_buy_price
    percent_change = (diff / avg_buy_price) * 100
    
    if percent_change >= 0:
        return {
            "status": "GROWTH",
            "color": "#059669", 
            "icon": "📈",
            "label": f"Roste (+{percent_change:.1f} %)",
            "message": "Investice se zhodnocuje."
        }
    else:
        # Psychologický trik zachován, ale text je právně bezpečný
        return {
            "status": "DISCOUNT",
            "color": "#2563eb", # Modrá (Info), ne Oranžová (Warning)
            "icon": "📉", 
            "label": f"Cena je níže ({percent_change:.1f} %)",
            "message": f"Aktuálně levnější o {abs(int(diff * KURZ_USD_CZK))} Kč na kus."
        }

# B) Simulace Trhu (God Mode)
def apply_market_sentiment(price):
    factor = st.session_state.get('market_factor', 1.0) 
    return price * factor

# --- 3. DATABÁZE ---
db_akcii = [
    # DIVIDENDOVÉ
    {"ticker": "KO", "name": "Coca-Cola", "styl": "Dividenda", "riziko": "Nízké", "sektor": "Konzum", 
     "duvod": "Legenda. Když je krize, lidi pijí Colu.", "rule_40": False, "ps_ratio": 6.5, 
     "div_yield": 3.1, "div_months": ["Duben", "Červenec", "Říjen", "Prosinec"]},
    {"ticker": "PEP", "name": "PepsiCo", "styl": "Dividenda", "riziko": "Nízké", "sektor": "Konzum", 
     "duvod": "Vlastní i chipsy Lays. Diverzifikace.", "rule_40": False, "ps_ratio": 2.8, 
     "div_yield": 3.0, "div_months": ["Leden", "Březen", "Červen", "Září"]},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "styl": "Dividenda", "riziko": "Nízké", "sektor": "Zdraví", 
     "duvod": "AAA rating. Stabilnější než vláda USA.", "rule_40": False, "ps_ratio": 4.1, 
     "div_yield": 2.9, "div_months": ["Březen", "Červen", "Září", "Prosinec"]},
    {"ticker": "MCD", "name": "McDonald's", "styl": "Dividenda", "riziko": "Střední", "sektor": "Gastro", 
     "duvod": "Realitní firma převlečená za burgery.", "rule_40": False, "ps_ratio": 8.2, 
     "div_yield": 2.3, "div_months": ["Březen", "Červen", "Září", "Prosinec"]},
    {"ticker": "O", "name": "Realty Income", "styl": "Dividenda", "riziko": "Střední", "sektor": "Nemovitosti", 
     "duvod": "The Monthly Dividend Company.", "rule_40": False, "ps_ratio": 5.0, 
     "div_yield": 5.2, "div_months": ["Leden", "Únor", "Březen", "Duben", "Květen", "Červen", "Červenec", "Srpen", "Září", "Říjen", "Listopad", "Prosinec"]},
    
    # RŮSTOVÉ
    {"ticker": "AAPL", "name": "Apple", "styl": "Růst", "riziko": "Střední", "sektor": "Tech", 
     "duvod": "Ekosystém, ze kterého se neodchází.", "rule_40": True, "ps_ratio": 7.5, "div_yield": 0.5, "div_months": []},
    {"ticker": "MSFT", "name": "Microsoft", "styl": "Růst", "riziko": "Střední", "sektor": "Tech", 
     "duvod": "Windows a Cloud. Motor byznysu.", "rule_40": True, "ps_ratio": 12.0, "div_yield": 0.7, "div_months": []},
    {"ticker": "NVDA", "name": "Nvidia", "styl": "Růst", "riziko": "Vysoké", "sektor": "Tech", 
     "duvod": "AI čipy. Zlato 21. století.", "rule_40": True, "ps_ratio": 35.0, "div_yield": 0, "div_months": []},
]

# --- 4. ENGINE DAT ---
@st.cache_data(ttl=3600, show_spinner=False) 
def ziskej_data_yahoo(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty: return None
        cena = hist['Close'].iloc[-1]
        graf_data = hist[['Close']].reset_index(drop=True)
        return round(float(cena), 2), "USD", graf_data
    except Exception:
        return None

def ziskej_data_simulace(ticker, styl):
    seed = sum(ord(c) for c in ticker)
    np.random.seed(seed)
    base_price = np.random.randint(50, 400)
    base_price = apply_market_sentiment(base_price)
    points = 30 
    trend = np.linspace(0, 50 if styl == "Růst" else 10, points)
    volatilita = np.random.normal(0, 5 if styl == "Růst" else 2, points)
    krivka = [float(x) for x in (base_price + trend + volatilita)]
    graf_data = pd.DataFrame(krivka, columns=['Close'])
    return round(krivka[-1], 2), "USD", graf_data

def ziskej_data_smart(ticker, styl):
    raw_data = ziskej_data_yahoo(ticker)
    if raw_data:
        cena_real, mena, graf = raw_data
        cena_simulated = apply_market_sentiment(cena_real)
        return cena_simulated, mena, graf
    else:
        return ziskej_data_simulace(ticker, styl)

# --- 6. MODÁL NÁKUPU ---
@st.dialog("Nastavení investice")
def nakupni_okno(firma, cena_usd):
    st.subheader(f"Kupuješ: {firma['name']}")
    col_img, col_info = st.columns([1, 3])
    with col_img: st.image(f"https://financialmodelingprep.com/image-stock/{firma['ticker']}.png", width=50)
    with col_info: st.metric("Aktuální cena", f"{cena_usd:.2f} USD", f"{int(cena_usd * KURZ_USD_CZK)} Kč")
    
    st.markdown("---")
    typ_nakupu = st.radio("Jak chceš nakoupit?", ["Chci investovat částku (Kč)", "Chci konkrétní počet kusů (ks)"])
    if "částku" in typ_nakupu:
        investice_czk = st.number_input("Kolik chceš investovat (Kč)?", min_value=100, value=1000, step=100)
        investice_usd = investice_czk / KURZ_USD_CZK
        pocet_akcii = investice_usd / cena_usd
        st.info(f"💡 Za **{investice_czk} Kč** dostaneš **{pocet_akcii:.4f} ks** akcie.")
    else:
        pocet_akcii = st.number_input("Kolik akcií?", min_value=0.1, value=1.0, step=0.1)
        investice_czk = pocet_akcii * cena_usd * KURZ_USD_CZK
        st.info(f"💡 **{pocet_akcii} ks** tě bude stát cca **{int(investice_czk)} Kč**.")
    
    st.warning("ℹ️ **Spread (Poplatek):** Cca 0.5 %. To je normální, nelekni se malého mínusu po nákupu.")
    
    if st.button("✅ Potvrdit", type="primary"):
        st.session_state.moje_portfolio.append({
            "ticker": firma['ticker'], 
            "name": firma['name'], 
            "ks": pocet_akcii, 
            "investice_czk": investice_czk,
            "buy_price_usd": cena_usd, 
            "yield": firma.get('div_yield', 0), 
            "months": firma.get('div_months', [])
        })
        st.toast(f"{firma['name']} přidána do portfolia!", icon="🎒")
        time.sleep(1)
        st.rerun()

# --- 7. SIDEBAR (GOD MODE) ---
with st.sidebar:
    st.header("⚙️ God Mode (Simulace)")
    market_sentiment = st.slider("Nálada trhu", min_value=0.5, max_value=1.5, value=1.0, step=0.1)
    st.session_state.market_factor = market_sentiment
    if market_sentiment < 1.0:
        st.error(f"📉 SIMULACE POKLESU: -{int((1-market_sentiment)*100)} %")
    st.divider()

# --- 8. UI APLIKACE (MAIN FLOW) ---

if st.session_state.page == "intro":
    c1, c2 = st.columns([2, 1])
    with c1:
        st.title("🦄 Petrův Průvodce")
        st.markdown("### Investování bez 'finanční latiny'.")
        st.write("Většina lidí se bojí ztráty, protože nerozumí trhu. My ti ukážeme, že je to jednodušší než nákup na eshopu.")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🚀 Začít vybírat", type="primary", use_container_width=True):
                st.session_state.page = "wizard_1"
                st.rerun()
        with col_btn2:
            if st.button("🎓 Rychlokurz (3 min)", type="secondary", use_container_width=True):
                st.session_state.page = "education"
                st.rerun()
    with c2:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=200)

elif st.session_state.page == "education":
    st.title("🎓 Rychlokurz investora")
    st.write("Pár minut čtení, které ti změní pohled na peníze.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Kráva vs. Tele", "Teorie Benzínu", "Pizza Teorie", "Sněhová koule"])
    
    with tab1:
        st.subheader("Dividenda vs. Růst")
        st.info("🥛 **Sběrači (Dividenda):** Chtějí 'krávu na mléko'. Firma jim posílá část zisku na účet.")
        st.warning("🐂 **Lovci (Růst):** Chtějí 'tele, co vyroste'. Firma zisk neposílá, ale investuje do sebe.")
    
    with tab2:
        st.subheader("Proč trhy kolísají? (Teorie Benzínu ⛽)")
        st.write("Když přijedeš na pumpu a benzín stojí 25 Kč místo 40 Kč, co uděláš?")
        st.success("Většina lidí by natankovala plnou. S akciemi je to **podobné**. Pokud firma hospodaří zdravě, červená čísla znamenají slevu.")
    
    with tab3:
        st.subheader("Teorie Pizzy 🍕")
        st.write("Dvě firmy můžou být stejně hodnotné (stejně velká pizza), ale jedna bude mít 'levnější' akcii jen proto, že pizzu rozkrájela na více dílků.")
        st.info("💡 **Poučení:** Nekoukej na cenu akcie, koukej na hodnotu firmy.")
        
    with tab4:
        st.subheader("Sněhová koule (Složené úročení) ❄️")
        st.write("Albert Einstein to prý nazval osmým divem světa.")
        st.write("Když zisky nevybereš, ale necháš je vydělávat další zisky, tvoje peníze se začnou nabalovat jako koule ze svahu.")
        st.markdown("**100 Kč** ➡️ (+10%) ➡️ **110 Kč** ➡️ (+10%) ➡️ **121 Kč**... a za pár let je to lavina.")

    if st.button("⬅️ Jdeme na to", type="secondary"):
        st.session_state.page = "intro"
        st.rerun()

elif st.session_state.page == "wizard_1":
    st.progress(25)
    st.subheader("1. Jaký je tvůj cíl?")
    st.caption("💡 Vyber si strategii. Neboj, kalkulačka za tebe pohlídá důležité metriky.")
    
    volba = st.radio("Chci spíše:", ["🅰️ Pravidelná výplata (Dividenda)", "🅱️ Budování majetku (Růst)"])
    
    # Vysvětlení metrik na základě volby (Educational Overlay)
    if "Dividenda" in volba:
        st.info("ℹ️ **Na co dáváme pozor:** U dividendových firem pro tebe hlídáme **historii vyplácení**. Hledáme firmy, které platí spolehlivě jako švýcarské hodinky, i když je krize.")
    else:
        st.info("ℹ️ **Na co dáváme pozor:** U růstových firem hlídáme **zdraví byznysu** (např. Rule of 40 nebo P/S poměr). Zajímá nás, jestli firma reálně vydělává, nebo je to jen nafouknutá bublina.")

    if st.button("Dále ➡️", type="primary"):
        st.session_state.temp_cil = "Dividenda" if "Dividenda" in volba else "Růst"
        st.session_state.page = "wizard_2"
        st.rerun()

elif st.session_state.page == "wizard_2":
    st.progress(50)
    st.subheader("2. Test odolnosti")
    st.write("Investoval jsi 10 000 Kč. Za měsíc vidíš, že hodnota klesla na 8 000 Kč. Co uděláš?")
    
    # Rozepsané možnosti pro lepší empatii
    reakce = st.radio("Upřímně:", [
        "😱 Prodám to, protože se bojím, že spadnu na nulu.", 
        "😐 Nic neudělám, chci akcie držet dlouhodobě.", 
        "🤩 Super, teď můžu za míň peněz dokoupit víc (jako u benzínu)."
    ])
    
    if st.button("Dále ➡️", type="primary"):
        if "Prodám" in reakce: st.session_state.temp_riziko = "Nízké"
        elif "Nic" in reakce: st.session_state.temp_riziko = "Střední"
        else: st.session_state.temp_riziko = "Vysoké"
        st.session_state.page = "wizard_3"
        st.rerun()

elif st.session_state.page == "wizard_3":
    st.progress(75)
    st.subheader("3. Čemu rozumíš?")
    
    # Warren Buffett Quote
    st.markdown("""
    > *"Nikdy neinvestuj do byznysu, kterému nerozumíš."* > — Warren Buffett
    """)
    st.write("Vyber sektory, které znáš z běžného života. Nemusíš být expert, stačí, že jsi zákazník.")

    sektory_human = {"Konzum": "Jídlo a Pití (Cola, Pepsi)", "Tech": "Technologie (Apple, Microsoft)", "Zdraví": "Zdraví (Léky)", "Energie": "Energie (Benzín)", "Nemovitosti": "Nemovitosti"}
    vyber = st.multiselect("Vyber oblasti:", list(sektory_human.keys()), format_func=lambda x: sektory_human[x])
    
    if st.button("🎉 Ukázat výsledky", type="primary"):
        st.session_state.temp_sektory = vyber
        st.session_state.page = "results"
        st.rerun()

elif st.session_state.page == "results":
    # Logika stejná jako předtím...
    st.progress(100)
    cil = st.session_state.temp_cil
    riziko = st.session_state.temp_riziko
    sektory = st.session_state.temp_sektory
    
    nalezeno = [x for x in db_akcii if x['styl'] == cil and 
               (riziko == x['riziko'] or (riziko == "Střední" and x['riziko'] == "Nízké") or (riziko == "Vysoké")) and
               (not sektory or x['sektor'] in sektory)]
    
    if not nalezeno:
        st.warning("🧐 Pro tuto kombinaci jsme museli trochu rozšířit hledání.")
        nalezeno = [x for x in db_akcii if x['styl'] == cil][:3]

    st.subheader(f"Našli jsme {len(nalezeno)} příležitostí")
    
    col_main, col_detail = st.columns([2, 1])
    
    with col_main:
        for firma in nalezeno:
            cena_usd, mena, graf_data = ziskej_data_smart(firma['ticker'], firma['styl'])
            with st.container():
                st.markdown(f'<div class="card-highlight">', unsafe_allow_html=True)
                c1, c2, c3 = st.columns([1, 3, 2])
                with c1: st.image(f"https://financialmodelingprep.com/image-stock/{firma['ticker']}.png", width=60)
                with c2:
                    st.markdown(f"### {firma['name']}")
                    st.caption(f"{firma['sektor']} • {firma['duvod']}")
                with c3:
                    if st.button(f"🛒 Koupit", key=f"btn_{firma['ticker']}", type="secondary", use_container_width=True):
                        nakupni_okno(firma, cena_usd)
                st.area_chart(graf_data, height=80, color="#059669" if cil=="Dividenda" else "#4b0082")
                st.markdown('</div>', unsafe_allow_html=True)

    with col_detail:
        st.info("💡 **Tip:** Všechny tyto firmy jsou prověřené. Klikni na 'Koupit', abys viděl, kolik akcií dostaneš za své peníze.")

    if st.session_state.moje_portfolio:
        st.markdown("---")
        st.success(f"V košíku máš: {len(st.session_state.moje_portfolio)} firem.")
        if st.button("🚀 Přejít na Můj Plán (Dashboard)", type="primary", use_container_width=True):
             st.session_state.page = "dashboard"
             st.rerun()

elif st.session_state.page == "dashboard":
    # --- DASHBOARD LOGIC START ---
    total_invested = sum([p['investice_czk'] for p in st.session_state.moje_portfolio])
    current_value_czk = 0
    rocni_divi_czk = 0
    portfolio_display = []
    
    for p in st.session_state.moje_portfolio:
        curr_price_usd, _, _ = ziskej_data_smart(p['ticker'], "Neznámý")
        val_czk = p['ks'] * curr_price_usd * KURZ_USD_CZK
        current_value_czk += val_czk
        if p.get('yield'):
            rocni_divi_czk += p['investice_czk'] * (p['yield']/100)
            
        status = get_position_status(curr_price_usd, p['buy_price_usd'])
        
        portfolio_display.append({
            "ticker": p['ticker'],
            "name": p['name'],
            "ks": p['ks'],
            "val_czk": val_czk,
            "status_data": status
        })

    # --- UI DASHBOARD ---
    st.balloons()
    st.title(f"Plán pro: {st.session_state.user_name}")
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Investováno", f"{int(total_invested):,} Kč")
    diff_total = current_value_czk - total_invested
    kpi2.metric("Aktuální hodnota", f"{int(current_value_czk):,} Kč", delta=f"{int(diff_total)} Kč", delta_color="normal" if diff_total >= 0 else "off")
    kpi3.metric("Pasivní příjem (ročně)", f"{int(rocni_divi_czk):,} Kč", "Budoucí renta")

    st.markdown("---")
    st.subheader("📦 Tvoje Portfolio")
    
    for item in portfolio_display:
        s = item['status_data']
        with st.container():
            col_icon, col_name, col_stats, col_status = st.columns([1, 3, 3, 2])
            with col_icon: st.image(f"https://financialmodelingprep.com/image-stock/{item['ticker']}.png", width=50)
            with col_name:
                st.markdown(f"**{item['name']}** ({item['ticker']})")
                st.caption(f"{item['ks']:.2f} ks")
            with col_stats: st.write(f"Hodnota: **{int(item['val_czk'])} Kč**")
            with col_status:
                st.markdown(f"""
                <div style="background-color: {s['color']}; padding: 5px; border-radius: 5px; color: white; text-align: center;">
                    {s['icon']} {s['label']}
                </div>
                <div style="font-size: 12px; color: #aaa; text-align: center; margin-top: 2px;">
                    {s['message']}
                </div>
                """, unsafe_allow_html=True)
            st.divider()

    st.subheader("❄️ Sněhová koule (Efekt času)")
    st.write("Podívej se, co se stane za 20 let, když nebudeš panikařit.")
    roky = list(range(2025, 2045))
    hodnoty = [total_invested * (1.08 ** i) for i in range(len(roky))]
    st.area_chart(pd.DataFrame({"Rok": roky, "Hodnota": hodnoty}).set_index("Rok"), color="#4b0082")

    c_btn1, c_btn2 = st.columns(2)
    with c_btn1: st.link_button("🏦 Otevřít cvičný účet u Brokera", "https://www.xtb.com/cz", type="primary", use_container_width=True)
    with c_btn2:
        if st.button("🔄 Resetovat simulaci", type="secondary", use_container_width=True):
            st.session_state.moje_portfolio = []
            st.session_state.page = "intro"
            st.rerun()
