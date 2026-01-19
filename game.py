import streamlit as st
import random
import pandas as pd
import mysql.connector
from mysql.connector import Error

# --- Streamlit Config ---
st.set_page_config(page_title="Tambola Multiplayer", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #f4f9fd; }
    h1, h2, h3, h4 { color: #1d3557; }
    .winner { color: green; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("🎫 BingoBlitz : Play, Match & Win")

# --- Database Connection ---
def get_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="work28",
            database="tambola_game"
        )
        return conn
    except Error as e:
        st.error(f"Database connection failed ❌: {e}")
        return None

# --- Login & Signup ---
def login_signup_page():
    st.sidebar.title("🔐 User Login / Signup")
    choice = st.sidebar.radio("Select Option", ["Login", "Sign Up"])

    if choice == "Sign Up":
        fullname = st.text_input("Full Name")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Create Account"):
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("INSERT INTO users (username, password, fullname) VALUES (%s, %s, %s)",
                                   (username, password, fullname))
                    conn.commit()
                    st.success("🎉 Account created! Please log in.")
                except mysql.connector.IntegrityError:
                    st.error("Username already exists!")
                finally:
                    cursor.close()
                    conn.close()

    elif choice == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            conn = get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT fullname FROM users WHERE username=%s AND password=%s", (username, password))
                result = cursor.fetchone()
                if result:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.fullname = result[0]
                    st.success(f"Welcome {result[0]} 👋")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
                cursor.close()
                conn.close()

# --- Login Session ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_signup_page()
    st.stop()

st.sidebar.success(f"Logged in as {st.session_state.fullname}")

# --- Sidebar Controls ---
st.sidebar.header("🎮 Game Controls")
num_players = st.sidebar.number_input("👥 Number of Players", min_value=1, max_value=6, value=2)

# --- Player Names ---
if "player_names" not in st.session_state or len(st.session_state.player_names) != num_players:
    st.session_state.player_names = [f"Player {i+1}" for i in range(num_players)]

st.sidebar.subheader("✏️ Enter Player Names")
for i in range(num_players):
    name = st.sidebar.text_input(f"Name for Player {i+1}", st.session_state.player_names[i])
    st.session_state.player_names[i] = name.strip() if name.strip() else f"Player {i+1}"

# --- Create Ticket ---
def create_ticket():
    cols = {i: list(range(i*10+1, i*10+11)) if i > 0 else list(range(1,10)) for i in range(9)}
    ticket = [[0]*9 for _ in range(3)]
    chosen_cols = [random.sample(list(cols.keys()), 5) for _ in range(3)]
    for row in range(3):
        for col in chosen_cols[row]:
            num = random.choice(cols[col])
            cols[col].remove(num)
            ticket[row][col] = num
    for col in range(9):
        nums = [ticket[row][col] for row in range(3) if ticket[row][col] != 0]
        nums.sort()
        i = 0
        for row in range(3):
            if ticket[row][col] != 0:
                ticket[row][col] = nums[i]
                i += 1
    return ticket

# --- Initialize Game ---
defaults = {
    "tickets": [],
    "marks": [],
    "called_numbers": [],
    "available_numbers": list(range(1, 91)),
    "claims": {},
    "winners": [],
    "prizes": {
        "Top Line": None,
        "Middle Line": None,
        "Bottom Line": None,
        "Full House": None
    }
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# --- Generate Tickets ---
if st.sidebar.button("🎟️ Generate Tickets"):
    st.session_state.tickets = [create_ticket() for _ in range(num_players)]
    st.session_state.marks = [[[False]*9 for _ in range(3)] for _ in range(num_players)]
    st.session_state.called_numbers = []
    st.session_state.available_numbers = list(range(1, 91))
    st.session_state.claims = {
        st.session_state.player_names[i]: {"Top Line": False, "Middle Line": False, "Bottom Line": False, "Full House": False}
        for i in range(num_players)
    }
    st.session_state.winners = []
    for k in st.session_state.prizes.keys():
        st.session_state.prizes[k] = None
    st.success(f"{num_players} tickets generated successfully ✅")

# --- Call Next Number ---
if st.sidebar.button("🎲 Call Next Number"):
    if st.session_state.available_numbers:
        number = random.choice(st.session_state.available_numbers)
        st.session_state.available_numbers.remove(number)
        st.session_state.called_numbers.append(number)
        for p in range(num_players):
            for r in range(3):
                for c in range(9):
                    if st.session_state.tickets[p][r][c] == number:
                        st.session_state.marks[p][r][c] = True
        st.sidebar.success(f"📢 Number Called: {number}")
    else:
        st.sidebar.warning("All 90 numbers have been called.")

# --- Restart ---
if st.sidebar.button("🔄 Restart Game"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# --- Display Called Numbers ---
if st.session_state.called_numbers:
    last_num = st.session_state.called_numbers[-1]
    st.markdown(f"## 📢 Latest Number: **:blue[{last_num}]**")
    st.info("Numbers Called: " + ", ".join(map(str, sorted(st.session_state.called_numbers))))
    st.caption(f"Remaining Numbers: {len(st.session_state.available_numbers)}")

# --- Display Tickets ---
def display_ticket(ticket, marks):
    df = pd.DataFrame(ticket)
    df.replace(0, "", inplace=True)
    def highlight(val, row, col):
        if val == "":
            return ""
        return "background-color: lightgreen; font-weight:bold;" if marks[row][col] else "font-weight:bold;"
    styled = df.style.apply(lambda row: [highlight(v, row.name, i) for i,v in enumerate(row)], axis=1)
    st.table(styled)

st.subheader("🎟️ Player Tickets")
if not st.session_state.tickets:
    st.info("Please generate tickets first.")
else:
    avatars = ["🧑‍💻", "👩‍🎨", "🧔", "👩‍🏫", "🧑‍🚀", "👩‍💼"]
    for idx, name in enumerate(st.session_state.player_names):
        st.markdown(f"### {avatars[idx % len(avatars)]} {name}")
        display_ticket(st.session_state.tickets[idx], st.session_state.marks[idx])

# --- Helpers ---
def is_line_complete(row_marks, row_numbers):
    return sum([row_marks[c] for c in range(9) if row_numbers[c] != 0]) == 5

def is_full_house(mark_grid, ticket):
    total_nums = sum([1 for r in ticket for c in r if c != 0])
    marked = sum([1 for r in range(3) for c in range(9) if ticket[r][c] != 0 and mark_grid[r][c]])
    return marked == total_nums

def save_win(username, prize):
    conn = get_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO game_history (username, prize) VALUES (%s, %s)", (username, prize))
        conn.commit()
        cursor.close()
        conn.close()

# --- Claims ---
st.subheader("🏆 Claims")
for idx, name in enumerate(st.session_state.player_names):
    st.markdown(f"#### {name}")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.session_state.prizes["Top Line"] is None:
            if st.button(f"Top Line - {name}"):
                if is_line_complete(st.session_state.marks[idx][0], st.session_state.tickets[idx][0]):
                    st.success(f"🎉 {name} won Top Line!")
                    st.session_state.prizes["Top Line"] = name
                    st.session_state.winners.append((name, "Top Line"))
                    save_win(name, "Top Line")
                else:
                    st.error("❌ Invalid claim")
        else:
            st.info(f"🏆 Top Line: {st.session_state.prizes['Top Line']}")

    with col2:
        if st.session_state.prizes["Middle Line"] is None:
            if st.button(f"Middle Line - {name}"):
                if is_line_complete(st.session_state.marks[idx][1], st.session_state.tickets[idx][1]):
                    st.success(f"🎉 {name} won Middle Line!")
                    st.session_state.prizes["Middle Line"] = name
                    st.session_state.winners.append((name, "Middle Line"))
                    save_win(name, "Middle Line")
                else:
                    st.error("❌ Invalid claim")
        else:
            st.info(f"🏆 Middle Line: {st.session_state.prizes['Middle Line']}")

    with col3:
        if st.session_state.prizes["Bottom Line"] is None:
            if st.button(f"Bottom Line - {name}"):
                if is_line_complete(st.session_state.marks[idx][2], st.session_state.tickets[idx][2]):
                    st.success(f"🎉 {name} won Bottom Line!")
                    st.session_state.prizes["Bottom Line"] = name
                    st.session_state.winners.append((name, "Bottom Line"))
                    save_win(name, "Bottom Line")
                else:
                    st.error("❌ Invalid claim")
        else:
            st.info(f"🏆 Bottom Line: {st.session_state.prizes['Bottom Line']}")

    with col4:
        if st.session_state.prizes["Full House"] is None:
            if st.button(f"Full House - {name}"):
                if is_full_house(st.session_state.marks[idx], st.session_state.tickets[idx]):
                    st.balloons()
                    st.success(f"🏆 {name} won Full House!")
                    st.session_state.prizes["Full House"] = name
                    st.session_state.winners.append((name, "Full House"))
                    save_win(name, "Full House")
                else:
                    st.error("❌ Invalid claim")
        else:
            st.info(f"🏆 Full House: {st.session_state.prizes['Full House']}")

# --- Winners Board ---
st.subheader("🥇 Winners Board")
for prize, winner in st.session_state.prizes.items():
    if winner:
        st.markdown(f"✅ **{prize}** → <span class='winner'>{winner}</span>", unsafe_allow_html=True)
    else:
        st.write(f"⏳ **{prize}** → Not claimed yet")

# --- Game History ---
st.subheader("📜 Game History (All Players)")
conn = get_connection()
if conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(u.fullname, g.username) AS Player, g.prize, g.game_date
        FROM game_history g
        LEFT JOIN users u ON g.username = u.username
        ORDER BY g.game_date DESC
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    if rows:
        df = pd.DataFrame(rows, columns=["Player Name", "Prize Won", "Date & Time"])
        df.index = df.index + 1
        st.dataframe(df)
    else:
        st.info("No game history yet. Be the first to win!")

# --- Global Leaderboard ---
st.subheader("🏆 Global Leaderboard")
conn = get_connection()
if conn:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COALESCE(u.fullname, g.username) AS Player, COUNT(g.prize) AS Total_Wins
        FROM game_history g
        LEFT JOIN users u ON g.username = u.username
        GROUP BY Player
        ORDER BY Total_Wins DESC
        LIMIT 10
    """)
    leaderboard = cursor.fetchall()
    cursor.close()
    conn.close()

    if leaderboard:
        df_leaderboard = pd.DataFrame(leaderboard, columns=["Player Name", "Total Wins"])
        df_leaderboard.index = df_leaderboard.index + 1
        st.dataframe(df_leaderboard.style.highlight_max(axis=0, subset=["Total Wins"], color="#a8dadc"))
    else:
        st.info("No winners yet. Play and claim to appear on the leaderboard!")
