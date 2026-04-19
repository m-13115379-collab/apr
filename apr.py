import pandas as pd, streamlit as st, hashlib, time
from datetime import datetime, timedelta
import sqlite3
import os

# --- CONFIG & DATABASE ---
# 💳 MAKLUMAT BANK AWAK
BSN = "0100241100043399"
BSN_N = "MUHAMMAD MUAZ HADIF BIN MOHAMAD HIDIR"
CR_L1, CR_L2 = 0.10, 0.02

# Guna SQLite (Senang, tak payah password)
DB_FILE = "apr_data.db"

def get_conn():
    # Pastikan folder data wujud
    if not os.path.exists('data'):
        os.makedirs('data')
    return sqlite3.connect(f'data/{DB_FILE}')

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users(u TEXT PRIMARY KEY, p TEXT, ph TEXT, w REAL, pt INT, lv INT DEFAULT 1, ref TEXT, vrf INT DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS ads(id INTEGER PRIMARY KEY AUTOINCREMENT, u TEXT, txt TEXT, v TEXT, b REAL, r INT, ex TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS tops(id INTEGER PRIMARY KEY AUTOINCREMENT, u TEXT, a REAL, s TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chat(id INTEGER PRIMARY KEY AUTOINCREMENT, u TEXT, m TEXT, t TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS jobs(id INTEGER PRIMARY KEY AUTOINCREMENT, u TEXT, task TEXT, pay REAL, s TEXT, assigned_to TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS revenue(id INTEGER PRIMARY KEY AUTOINCREMENT, amt REAL, type TEXT, t TEXT)')
    conn.commit()
    conn.close()

def up_w(u, a, r):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET w = w + ?, pt = pt + ? WHERE u = ?", (a, abs(int(a)), u))
    if a < 0:
        c.execute("INSERT INTO revenue(amt, type, t) VALUES(?, ?, ?)", (abs(a), r, datetime.now().strftime("%Y-%m-%d")))
    
    # Sistem Referral
    c.execute("SELECT ref FROM users WHERE u = ?", (u,))
    res = c.fetchone()
    if res and res[0] and a > 0:
        l1 = res[0]
        c.execute("UPDATE users SET w = w + ? WHERE u = ?", (a * CR_L1, l1))
        c.execute("SELECT ref FROM users WHERE u = ?", (l1,))
        res2 = c.fetchone()
        if res2 and res2[0]:
            c.execute("UPDATE users SET w = w + ? WHERE u = ?", (a * CR_L2, res2[0]))
    conn.commit()
    conn.close()

# --- STREAMLIT SETUP ---
st.set_page_config(page_title="APR V20 ULTRA", layout="wide")
init_db()

# --- LOGIN SYSTEM ---
if 'u' not in st.session_state:
    t1, t2 = st.tabs(["🔑 LOGIN", "📝 JOIN"])
    with t1:
        u_in = st.text_input("Username")
        p_in = st.text_input("Password", type='password')
        if st.button("MASUK"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE u = ?", (u_in,))
            chk = c.fetchone()
            conn.close()
            if chk and chk[1] == hashlib.sha256(p_in.encode()).hexdigest():
                st.session_state.u = u_in
                st.rerun()
            else:
                st.error("User atau Password salah!")
    with t2:
        nu = st.text_input("Username Baru")
        np = st.text_input("Password Baru", type='password')
        nph = st.text_input("No Telefon")
        rf = st.query_params.get("ref", "")
        if st.button("DAFTAR"):
            if nu and np:
                try:
                    conn = get_conn()
                    c = conn.cursor()
                    c.execute("INSERT INTO users(u,p,ph,w,pt,lv,ref,vrf) VALUES(?,?,?,0,0,1,?,0)", 
                              (nu, hashlib.sha256(np.encode()).hexdigest(), nph, rf))
                    conn.commit()
                    conn.close()
                    st.success("Daftar Berjaya! Sila Login.")
                except Exception as e:
                    st.error(f"Username dah wujud atau error: {e}")
    st.stop()

# --- DASHBOARD ---
try:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE u = ?", (st.session_state.u,))
    ud_data = c.fetchone()
    
    if ud_data is None:
        st.error("Sila login semula!")
        del st.session_state.u
        st.rerun()
        
    c.execute("PRAGMA table_info(users)")
    cols = [col[1] for col in c.fetchall()]
    ud = dict(zip(cols, ud_data))
    conn.close()
except Exception as e:
    st.error(f"Error: {e}")
    if 'u' in st.session_state:
        del st.session_state.u
    st.rerun()

st.sidebar.title(f"💸 RM{ud['w']:.2f} {'✅' if ud['vrf'] else ''}")

menu = st.sidebar.radio("MENU UTAMA", 
    ["🔥 WARZONE", "🚀 POST", "🤝 GIGS", "🛡️ STORE", "💬 CHAT", "💰 TOPUP", "👥 REFERAL", "👨‍💻 ADMIN"])

# --- PAGE FUNCTIONS ---
if menu == "🔥 WARZONE":
    st.header("🔥 WARZONE")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM ads WHERE r < 5 ORDER BY b DESC LIMIT 1")
    ad = c.fetchone()
    conn.close()
    
    if ad:
        try:
            st.video(ad[3])
        except:
            st.write("📌 Iklan Aktif")
        st.info(f"**@{ad[1]}**: {ad[2]}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🏴‍☠️ HIJACK\n(RM100)") and ud['w'] >= 100:
                up_w(ud['u'], -100, "HIJACK")
                st.rerun()
        with col2:
            if st.button("🚀 BOOST\n(RM10)") and ud['w'] >= 10:
                conn = get_conn()
                c = conn.cursor()
                c.execute("UPDATE ads SET b = b + 50 WHERE id = ?", (ad[0],))
                conn.commit()
                conn.close()
                up_w(ud['u'], -10, "BOOST")
                st.rerun()
        with col3:
            if st.button("🔥 BURN\n(RM200)") and ud['w'] >= 200:
                conn = get_conn()
                c = conn.cursor()
                c.execute("UPDATE ads SET r = 99 WHERE id = ?", (ad[0],))
                conn.commit()
                conn.close()
                up_w(ud['u'], -200, "BURN")
                st.rerun()

elif menu == "🚀 POST":
    st.header("🚀 POST IKLAN")
    txt = st.text_area("Teks Iklan")
    vid = st.text_input("Link Video (YouTube/Embed)")
    if st.button("POST NOW (RM10)") and ud['w'] >= 10:
        up_w(ud['u'], -10, "POST")
        conn = get_conn()
        c = conn.cursor()
        expire = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d")
        c.execute("INSERT INTO ads(u,txt,v,b,r,ex) VALUES(?,?,?,0,0,?)", (ud['u'], txt, vid, expire))
        conn.commit()
        conn.close()
        st.success("Iklan Berjaya Dihantar!")
        st.rerun()

elif menu == "🤝 GIGS":
    st.header("🤝 TUGASAN / GIGS")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM jobs WHERE s = 'OPEN'")
    js = c.fetchall()
    conn.close()
    
    if not js:
        st.write("Tiada tugasan buat masa ini.")
    for j in js:
        if st.button(f"AMBIL | RM{j[3]} | {j[2]}"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("UPDATE jobs SET s = 'TAKEN', assigned_to = ? WHERE id = ?", (ud['u'], j[0]))
            conn.commit()
            conn.close()
            st.success("Tugasan Anda!")
            st.rerun()

elif menu == "🛡️ STORE":
    st.header("🛡️ STORE")
    if st.button("✅ VERIFIKASI AKAUN (RM100)") and ud['w'] >= 100:
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE users SET vrf = 1 WHERE u = ?", (ud['u'],))
        conn.commit()
        conn.close()
        up_w(ud['u'], -100, "VERIFY")
        st.success("Akaun Berjaya Diverifikasi!")
        st.rerun()

elif menu == "💬 CHAT":
    st.header("💬 GROUP CHAT")
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM chat ORDER BY id DESC LIMIT 30")
    msgs = c.fetchall()
    conn.close()
    
    for msg in reversed(msgs):
        st.write(f"**[{msg[3]}] {msg[1]}**: {msg[2]}")
    
    m_in = st.text_input("Taip mesej...")
    if st.button("HANTAR") and m_in:
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO chat(u,m,t) VALUES(?,?,?)", (ud['u'], m_in, datetime.now().strftime("%H:%M")))
        conn.commit()
        conn.close()
        st.rerun()

elif menu == "💰 TOPUP":
    st.header("💰 TOPUP BALANCE")
    st.info(f"🏦 **Akaun Bank:** {BSN}\n**Nama:** {BSN_N}")
    amt = st.number_input("Jumlah (RM)", min_value=10.0, step=10.0)
    if st.button("PROSES TOPUP"):
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO tops(u,a,s) VALUES(?,?,'PENDING')", (ud['u'], amt))
        conn.commit()
        conn.close()
        st.success("Berjaya! Sila buat pembayaran & tunggu admin sahkan.")

elif menu == "👥 REFERAL":
    st.header("👥 SISTEM REFERAL")
    link_ref = f"https://apr.streamlit.app/?ref={ud['u']}"
    st.code(link_ref, language="text")
    st.success("Link di atas untuk anda share!")
    st.write("---")
    st.metric("Komisen Level 1", f"{CR_L1*100}%")
    st.metric("Komisen Level 2", f"{CR_L2*100}%")

elif menu == "👨‍💻 ADMIN":
    st.header("👨‍💻 PANEL ADMIN")
    key = st.text_input("Masukkan Kunci Admin", type="password")
    
    if key == "Apexmuaz" and ud['u'] == "muazgud131@gmail.com":
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT SUM(amt) FROM revenue")
        rev = c.fetchone()[0] or 0
        st.metric("JUMLAH HASIL", f"RM{rev:.2f}")
        
        st.subheader("📥 SENARAI TOPUP PENDING")
        c.execute("SELECT * FROM tops WHERE s = 'PENDING'")
        ts = c.fetchall()
        if not ts:
            st.write("Tiada permohonan baru.")
        for t_ in ts:
            col1, col2 = st.columns([4,1])
            col1.write(f"**{t_[1]}** - RM{t_[2]}")
            if col2.button(f"LULUS #{t_[0]}"):
                up_w(t_[1], t_[2], "TOPUP_APPROVED")
                c.execute("UPDATE tops SET s = 'OK' WHERE id = ?", (t_[0],))
                conn.commit()
                st.success(f"RM{t_[2]} dah masuk!")
                st.rerun()
        
        st.subheader("📊 STATISTIK")
        c.execute("SELECT COUNT(*) FROM users")
        total_u = c.fetchone()[0]
        st.write(f"Jumlah Pengguna: **{total_u} orang**")
        conn.close()
        
        if st.button("🔴 LOGOUT ADMIN"):
            del st.session_state.u
            st.rerun()
    else:
        st.warning("Anda bukan admin atau kunci salah!")