

import streamlit as st
import random

# --- Page Configuration ---
st.set_page_config(page_title="Tambola Multiplayer", layout="centered")
st.title("🎫 Multiplayer Tambola (Housie)")

# --- User Input: Number of Players ---
num_players = st.sidebar.number_input("👥 Number of Players", min_value=1, max_value=6, value=2)

# --- Helper: Generate a single valid Tambola ticket ---
def create_ticket():
    ticket = [[0] * 9 for _ in range(3)]
    col_ranges = {i: list(range(i*10+1, i*10+11)) if i > 0 else list(range(1, 10)) for i in range(9)}
    
    for row in ticket:
        cols = random.sample(range(9), 5)
        for col in cols:
            if col_ranges[col]:
                num = random.choice(col_ranges[col])
                while any(num in r for r in ticket):
                    num = random.choice(col_ranges[col])
                row[col] = num
                col_ranges[col].remove(num)
    return ticket

# --- Session Initialization ---
if "tickets" not in st.session_state:
    st.session_state.tickets = []
if "marks" not in st.session_state:
    st.session_state.marks = []
if "called_numbers" not in st.session_state:
    st.session_state.called_numbers = []
if "available_numbers" not in st.session_state:
    st.session_state.available_numbers = list(range(1, 91))
if "claims" not in st.session_state:
    st.session_state.claims = {}

# --- Generate Player Tickets ---
if st.sidebar.button("🎟️ Generate Tickets"):
    st.session_state.tickets = [create_ticket() for _ in range(num_players)]
    st.session_state.marks = [[[False]*9 for _ in range(3)] for _ in range(num_players)]
    st.session_state.called_numbers = []
    st.session_state.available_numbers = list(range(1, 91))
    st.session_state.claims = {
        f"Player {i+1}": {"Top Line": False, "Middle Line": False, "Bottom Line": False, "Full House": False}
        for i in range(num_players)
    }
    st.success(f"{num_players} tickets generated successfully, Enjoy!")

# --- Number Calling ---
if st.sidebar.button("🎲 Call Next Number"):
    if st.session_state.available_numbers:
        number = random.choice(st.session_state.available_numbers)
        st.session_state.available_numbers.remove(number)
        st.session_state.called_numbers.append(number)
        # Mark number in all tickets
        for p in range(num_players):
            for r in range(3):
                for c in range(9):
                    if st.session_state.tickets[p][r][c] == number:
                        st.session_state.marks[p][r][c] = True
        st.sidebar.success(f"📢 Number Called: {number}")
    else:
        st.sidebar.warning("All 90 numbers have been called.")

# --- Restart Game ---
if st.sidebar.button("🔄 Restart Game"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.experimental_rerun()

# --- Show Called Numbers ---
if st.session_state.called_numbers:
    st.subheader("🔢 Numbers Called")
    st.info(", ".join(map(str, sorted(st.session_state.called_numbers))))
    st.write(f"Remaining Numbers: {len(st.session_state.available_numbers)}")

## --- Display Tickets ---
st.subheader("🎟️ Player Tickets")

if not st.session_state.tickets or len(st.session_state.tickets) < num_players:
    st.info("Please generate tickets first using the sidebar button.")
else:
    for idx in range(num_players):
        player = f"Player {idx+1}"
        st.markdown(f"### {player}")
        for row in range(3):
            row_display = []
            for col in range(9):
                try:
                    num = st.session_state.tickets[idx][row][col]
                    if num == 0:
                        row_display.append("   ")
                    elif st.session_state.marks[idx][row][col]:
                        row_display.append(f":green[{num:02}]")
                    else:
                        row_display.append(f"**{num:02}**")
                except IndexError:
                    row_display.append("??")  # fallback to avoid crashes
            st.write(" | ".join(row_display))


# --- Claim Checkers ---
def is_line_complete(row_marks):
    return sum(row_marks) == 5

def is_full_house(mark_grid):
    return sum([sum(row) for row in mark_grid]) == 15

# --- Claim Buttons ---
st.subheader("🏆 Claims")

if "claims" not in st.session_state or not st.session_state.claims:
    st.info("Please generate tickets first to make any claims.")
else:
    for idx in range(num_players):
        player = f"Player {idx+1}"
        st.markdown(f"#### {player}")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if not st.session_state.claims[player]["Top Line"] and st.button(f"Top Line - {player}"):
                if is_line_complete(st.session_state.marks[idx][0]):
                    st.success(f"🎉 {player} won Top Line!")
                    st.session_state.claims[player]["Top Line"] = True
                else:
                    st.error("❌ Invalid claim")

        with col2:
            if not st.session_state.claims[player]["Middle Line"] and st.button(f"Middle Line - {player}"):
                if is_line_complete(st.session_state.marks[idx][1]):
                    st.success(f"🎉 {player} won Middle Line!")
                    st.session_state.claims[player]["Middle Line"] = True
                else:
                    st.error("❌ Invalid claim")

        with col3:
            if not st.session_state.claims[player]["Bottom Line"] and st.button(f"Bottom Line - {player}"):
                if is_line_complete(st.session_state.marks[idx][2]):
                    st.success(f"🎉 {player} won Bottom Line!")
                    st.session_state.claims[player]["Bottom Line"] = True
                else:
                    st.error("❌ Invalid claim")

        with col4:
            if not st.session_state.claims[player]["Full House"] and st.button(f"Full House - {player}"):
                if is_full_house(st.session_state.marks[idx]):
                    st.balloons()
                    st.success(f"🏆 {player} won Full House!")
                    st.session_state.claims[player]["Full House"] = True
                else:
                    st.error("❌ Invalid claim")



