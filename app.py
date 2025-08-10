import streamlit as st
import pandas as pd
df = pd.read_csv("nfl_projections.csv")
df = df.drop(columns=['Opp.', 'Fum.'])
nfl_bye_weeks_2025 = {
    "ATL": 5,
    "CIN": 10,
    "PHI": 9,
    "DET": 8,
    "BUF": 7,
    "SF": 14,
    "MIN": 6,
    "BAL": 7,
    "LV": 8,
    "DAL": 10,
    "MIA": 12,
    "ARZ": 8,   # Arizona Cardinals — typically abbreviated as ARI, but matched to your provided list
    "IND": 11,
    "LAR": 8,
    "NYG": 14,
    "WAS": 12,
    "TB": 9,
    "GB": 5,
    "HOU": 6,
    "JAX": 8,
    "SEA": 8,
    "NYJ": 9,
    "LAC": 12,
    "KC": 10,
    "CAR": 14,
    "NO": 11,
    "NE": 14,
    "CHI": 5,
    "PIT": 5,
    "CLE": 9,
    "DEN": 12,
    "TEN": 10
}

df.insert(3, 'Bye', df['Team'].map(nfl_bye_weeks_2025))
df.insert(4, 'Rank', range(1, len(df) + 1))

# --- Initialize session state ---
def init_state():
    if "draft_settings" not in st.session_state:
        st.session_state.draft_settings = {
            "teams": 10,
            "rounds": 16,
            "current_pick": 1,
            "current_round": 1,
            "current_team": 1,
        }
    if "player_pool" not in st.session_state:
        # Load sample data here or replace with your data loading logic
        
        st.session_state.player_pool = df.copy()
    if "drafted_players" not in st.session_state:
        st.session_state.drafted_players = {f"Team {i+1}": [] for i in range(st.session_state.draft_settings["teams"])}

# --- Draft logic helpers ---
def get_team_for_pick(pick_number, teams):
    round_number = (pick_number - 1) // teams + 1
    index_in_round = (pick_number - 1) % teams
    if round_number % 2 == 1:  # odd rounds left to right
        team_index = index_in_round
    else:  # even rounds right to left
        team_index = teams - 1 - index_in_round
    return f"Team {team_index+1}", round_number, index_in_round + 1

def advance_pick():
    ds = st.session_state.draft_settings
    total_picks = ds["teams"] * ds["rounds"]
    if ds["current_pick"] >= total_picks:
        return
    ds["current_pick"] += 1
    ds["current_round"] = ((ds["current_pick"] - 1) // ds["teams"]) + 1
    pick_pos_in_round = ((ds["current_pick"] - 1) % ds["teams"]) + 1
    if ds["current_round"] % 2 == 1:
        ds["current_team"] = pick_pos_in_round
    else:
        ds["current_team"] = ds["teams"] - pick_pos_in_round + 1

def pick_player(player_name):
    ds = st.session_state.draft_settings
    team_name, round_num, pick_in_round = get_team_for_pick(ds["current_pick"], ds["teams"])

    # Add player to drafted_players for this team
    st.session_state.drafted_players.setdefault(team_name, []).append({
        "Player": player_name,
        "Round": round_num,
        "Pick": pick_in_round,
    })

    # Remove player from player_pool
    st.session_state.player_pool = st.session_state.player_pool[
        st.session_state.player_pool["Player"] != player_name
    ].reset_index(drop=True)

    advance_pick()



# --- Style helper ---
def df_style_by_tier(df):
    palette = {
        1: "#ffd700",  # gold
        2: "#c0c0c0",  # silver
        3: "#cd7f32",  # bronze
        4: "#e6f7ff",  # light blue
        5: "#f2f2f2",  # light gray
    }
    def bg_tier(val):
        return f"background-color: {palette.get(val, '')}"
    sty = df.style.format(na_rep="").hide_index()
    if "Tier" in df.columns:
        sty = sty.applymap(bg_tier, subset=pd.IndexSlice[:, ["Tier"]])
    return sty

# --- Main app ---
st.set_page_config(page_title="Fantasy Draft Sheet with Snake Draft", layout="wide")

# Initialize session state first thing!
init_state()

st.title("⚡ Fantasy Football Draft Sheet with Snake Draft Tracker & Auto-Assign Teams")

# Sidebar for settings & controls
with st.sidebar:
    st.header("Draft Settings & Controls")
    ds = st.session_state.draft_settings

    # Only allow changes before draft starts
    if ds["current_pick"] == 1 and all(len(v) == 0 for v in st.session_state.drafted_players.values()):
        teams = st.number_input("Number of Teams", min_value=2, max_value=20, value=ds["teams"], step=1)
        rounds = st.number_input("Number of Rounds", min_value=1, max_value=30, value=ds["rounds"], step=1)
        if st.button("Start/Reset Draft"):
            ds["teams"] = teams
            ds["rounds"] = rounds
            ds["current_pick"] = 1
            ds["current_round"] = 1
            ds["current_team"] = 1
            st.session_state.drafted_players = {f"Team {i+1}": [] for i in range(teams)}
            # Reload sample players or your own data here
            st.session_state.player_pool = df
            st.rerun()

    st.markdown("---")
    total_picks = ds["teams"] * ds["rounds"]
    picks_left = total_picks - ds["current_pick"] + 1
    st.write(f"**Current Pick:** {ds['current_pick']} (Round {ds['current_round']}, Team {ds['current_team']})")
    st.write(f"Picks left: {picks_left}")

    st.subheader("Upcoming Picks")
    upcoming = []
    temp_ds = ds.copy()
    for _ in range(5):
        if temp_ds["current_pick"] >= total_picks:
            break
        sim = temp_ds.copy()
        sim["current_pick"] += 1
        sim["current_round"] = ((sim["current_pick"] - 1) // sim["teams"]) + 1
        pick_pos_in_round = ((sim["current_pick"] - 1) % sim["teams"]) + 1
        if sim["current_round"] % 2 == 1:
            sim["current_team"] = pick_pos_in_round
        else:
            sim["current_team"] = sim["teams"] - pick_pos_in_round + 1
        upcoming.append(sim.copy())
        temp_ds = sim.copy()
    for up in upcoming:
        st.write(f"Pick {up['current_pick']}: Round {up['current_round']} — Team {up['current_team']}")

# Sidebar filters for player pool
st.sidebar.markdown("---")
st.sidebar.header("Filters")
search = st.sidebar.text_input("Search Player/Team")
positions = st.sidebar.multiselect("Positions", options=["QB","RB","WR","TE","K","DST"], default=[])
bye_range = st.sidebar.slider("Bye Week", 0, 17, (0, 17))
pts_min, pts_max = st.sidebar.slider("Projected Points", 0, 500, (0, 500))


# Filter player pool based on inputs
filtered = st.session_state.player_pool.copy()

if search:
    mask = filtered["Player"].str.contains(search, case=False, na=False) | filtered["Team"].str.contains(search, case=False, na=False)
    filtered = filtered[mask]
if positions:
    filtered = filtered[filtered["Position"].isin(positions)]
filtered = filtered[(filtered["Bye"] >= bye_range[0]) & (filtered["Bye"] <= bye_range[1])]
filtered = filtered[(filtered["FPTS"] >= pts_min) & (filtered["FPTS"] <= pts_max)]


filtered = filtered.sort_values(by="Rank")

# Main layout
col1, col2 = st.columns([3,2])

with col1:
    st.subheader("Available Players")
    try:
        st.dataframe(df_style_by_tier(filtered), height=600)
    except:
        st.dataframe(filtered, height=600)

    st.markdown("---")
    st.subheader("Draft Player")
    player_options = filtered["Player"].tolist()
    if not player_options:
        st.info("No players available with current filters.")
    else:
        selected_player = st.selectbox("Select player", player_options)
        if st.button("Pick Player"):
            pick_player(selected_player)
            st.rerun()
        

with col2:
    st.subheader("Teams & Rosters")
    ds = st.session_state.draft_settings
    for t in [f"Team {i+1}" for i in range(ds["teams"])]:
        st.markdown(f"### {t}")
        players = st.session_state.drafted_players.get(t, [])
        if players:
            df_roster = pd.DataFrame(players)
            st.table(df_roster[["Round","Pick","Player"]])
            csv = df_roster.to_csv(index=False).encode("utf-8")
            st.download_button(f"Download {t} roster CSV", data=csv, file_name=f"{t}_roster.csv", mime="text/csv")
        else:
            st.write("_No players picked yet_")

st.markdown("---")
st.caption("Modify sample data or add your own CSV load in init_state()")
