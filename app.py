import streamlit as st
import pandas as pd
import functions as fn

# Read csv into dataframe and drop unnecessary columns
df = pd.read_csv("nfl_projections.csv")
df = df.drop(columns=['Opp.', 'Fum.', 'PaCom', 'PaAtt', 'PaYds', 'PaTD', 'PaINT', 'RuAtt', 'RuYds', 'RuTD', 'Tar', 'Rec', 'ReYds', 'ReTD'])

# Add Bye and Rank columns
df.insert(3, 'Bye', df['Team'].map(fn.nfl_bye_weeks_2025))
df.insert(0, 'Rank', range(1, len(df) + 1))


# --- Main app ---
st.set_page_config(page_title="Fantasy Draft", layout="wide")

# Initialize session state first thing!
fn.init_state(df)

st.title("⚡Fantasy Football Draft Sheet⚡")

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
    st.dataframe(filtered, height=600)

    st.markdown("---")
    st.subheader("Draft Player")
    player_options = filtered["Player"].tolist()
    if not player_options:
        st.info("No players available with current filters.")
    else:
        selected_player = st.selectbox("Select player", player_options)
        if st.button("Pick Player"):
            fn.pick_player(selected_player)
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
