import streamlit as st
import pandas as pd
import functions as fn

# Read csv into dataframe and drop unnecessary columns
# df = pd.read_csv("nfl_projections.csv")
# df = df.drop(columns=['Opp.', 'Fum.', 'PaCom', 'PaAtt', 'PaYds', 'PaTD', 'PaINT', 'RuAtt', 'RuYds', 'RuTD', 'Tar', 'Rec', 'ReYds', 'ReTD', 'FPTS'])

# # Add Bye and Rank columns
# df.insert(3, 'Bye', df['Team'].map(fn.nfl_bye_weeks_2025))
# df.insert(0, 'Rank', range(1, len(df) + 1))

# --- Main app ---
st.set_page_config(page_title="Fantasy Draft", layout="wide")

with st.sidebar:
    st.subheader("Upload Custom Rankings")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"], key="csv_upload")

# Built-in default CSV
default_df = pd.read_csv("nfl_projections.csv")
drop_cols = [
    'Opp.', 'Fum.', 'PaCom', 'PaAtt', 'PaYds', 'PaTD', 'PaINT',
    'RuAtt', 'RuYds', 'RuTD', 'Tar', 'Rec', 'ReYds', 'ReTD', 'FPTS'
]
default_df = default_df.drop(columns=[c for c in drop_cols if c in default_df.columns], errors="ignore")
default_df.insert(3, 'Bye', default_df['Team'].map(fn.nfl_bye_weeks_2025))
default_df.insert(0, 'Rank', range(1, len(default_df) + 1))

# --- Handle user upload ---
if uploaded_file is not None:
    raw_df = pd.read_csv(uploaded_file)

    with st.expander("Customize Uploaded Rankings", expanded=True):
        st.write("Preview of uploaded file:", raw_df.head())

        # Let user map their CSV columns
        col_player = st.selectbox("Which column has player names?", raw_df.columns, key="map_player")
        col_team   = st.selectbox("Which column has team names?", raw_df.columns, key="map_team")
        col_pos    = st.selectbox("Which column has positions?", raw_df.columns, key="map_pos")

        if st.button("Use this file"):
            df = pd.DataFrame()
            df["Player"]   = raw_df[col_player]
            df["Team"]     = raw_df[col_team]
            df["Position"] = raw_df[col_pos]

            # Add Bye + Rank
            df.insert(3, "Bye", df["Team"].map(fn.nfl_bye_weeks_2025))
            df.insert(0, "Rank", range(1, len(df) + 1))

            st.session_state.custom_df = df
            st.success("✅ Custom rankings loaded! Restart draft to apply.")


# Decide which dataset to use
df = st.session_state.get("custom_df", default_df)

# Initialize session state first thing!
fn.init_state(df)

# Always ensure we aren't pointing at a keeper slot
fn.align_to_next_available_pick()

st.title("⚡Fantasy Football Draft Sheet⚡")

# Sidebar for settings & controls
with st.sidebar:
    st.header("Draft Settings & Controls")
    ds = st.session_state.draft_settings

    # Only allow changes before draft starts (no players drafted by picks yet)
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
            st.session_state.keepers = {f"Team {i+1}": [] for i in range(teams)}
            # Reload sample players or your own data here
            st.session_state.player_pool = df
            st.rerun()
    st.markdown("---")
    st.subheader("My Team")

    team_options = [f"Team {i+1}" for i in range(ds["teams"])]
    default_team = st.session_state.get("my_team", team_options[0])
    my_team = st.selectbox("Select Your Team", team_options, index=team_options.index(default_team))
    st.session_state.my_team = my_team


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

# Sidebar: Keeper setup (allowed any time before first *actual* pick)
with st.sidebar:
    st.markdown("---")
    st.header("Keeper Setup")
    ds = st.session_state.draft_settings
    if ds["current_pick"] == 1:  # allow keeper entry before the draft starts
        for i in range(ds["teams"]):
            team_name = f"Team {i+1}"
            with st.expander(f"{team_name} Keepers"):
                player_options = st.session_state.player_pool["Player"].tolist()
                if player_options:
                    keeper_player = st.selectbox(
                        f"Select keeper for {team_name}",
                        player_options,
                        key=f"keeper_player_{i}"
                    )
                    keeper_round = st.number_input(
                        f"Round for {team_name}",
                        min_value=1,
                        max_value=ds["rounds"],
                        step=1,
                        key=f"keeper_round_{i}"
                    )
                    if st.button(f"Add Keeper for {team_name}", key=f"add_keeper_btn_{i}"):
                        fn.add_keeper(team_name, keeper_player, keeper_round)
                        st.rerun()
                else:
                    st.info("No available players left to assign as keepers.")
    else:
        st.caption("Keepers can only be added before the draft begins (Pick 1).")


col1, col2 = st.columns([3,2])

with col1:
    st.subheader("Available Players")
    # Player Filters
    with st.expander("Filters", expanded=True):
        search = st.text_input("Search Player/Team")
        positions = st.multiselect("Positions", options=["QB","RB","WR","TE","K","DST"], default=[])
        

    # Apply filters
    filtered = st.session_state.player_pool.copy()
    
    if search:
        mask = filtered["Player"].str.contains(search, case=False, na=False) | filtered["Team"].str.contains(search, case=False, na=False)
        filtered = filtered[mask]
    if positions:
        filtered = filtered[filtered["Position"].isin(positions)]
    filtered = filtered.sort_values(by="Rank")
    
    st.subheader("Draft Player")
    player_options = filtered["Player"].tolist()
    if not player_options:
        st.info("No players available with current filters.")
    else:
        selected_player = st.selectbox(
            "Select player",
            player_options,
            index=player_options.index(st.session_state.get("selected_player"))
                if "selected_player" in st.session_state and st.session_state.selected_player in player_options
                else 0
                )
        
        col_pick, col_undo = st.columns(2)
        with col_pick:
            if st.button("Pick Player"):
                fn.pick_player(selected_player)
                st.rerun()
        with col_undo:
            if st.button("Undo Last Pick"):
                fn.remove_player_from_team()
                st.rerun()
    # st.dataframe(filtered, height=600)
    
    #Player Table with single-select via delta detection
    current_selected = st.session_state.get("selected_player")

    # Pre-check the currently selected player so only one row is True on render
    filtered_display = filtered.copy()
    filtered_display["Select"] = filtered_display["Player"] == current_selected

    clicked = st.data_editor(
        filtered_display,
        column_order=["Select", "Rank", "Player", "Team", "Position", "Bye"],
        hide_index=True,
        height=600,
        use_container_width=True,
        key="player_table"   # IMPORTANT: don't set disabled=True; checkboxes must be editable
    )

    # Figure out what changed: which player(s) were newly checked this run
    prev_selected = set(filtered_display.loc[filtered_display["Select"], "Player"])
    new_selected  = set(clicked.loc[clicked["Select"], "Player"])

    added = list(new_selected - prev_selected)     # the newly checked row(s)
    removed = list(prev_selected - new_selected)   # the previously-checked row that was unchecked

    if added:
        # User clicked a new row -> make that the single selection
        new_pick = added[0]
        if new_pick != current_selected:
            st.session_state.selected_player = new_pick
            st.rerun()
    elif removed and not new_selected:
        # User unchecked the only selected row; pick the top of the filtered table to stay consistent
        if not filtered.empty:
            st.session_state.selected_player = filtered.iloc[0]["Player"]
            st.rerun()

        
with col2:
    st.subheader("Teams & Rosters")
    ds = st.session_state.draft_settings
    my_team = st.session_state.get("my_team")
    if my_team:
        st.text_input('My Team Name', key='my_team_name', value=my_team)
        players = st.session_state.drafted_players.get(my_team, [])
        if players:
            df_roster = pd.DataFrame(players)
            st.table(df_roster[["Round","Pick","Player","Team","Position"]])
        else:
            st.write("_No players picked yet_")
        st.markdown("---")

    # Show all other teams
    for i in range(ds["teams"]):
        team_name = f"Team {i+1}"
        if team_name == my_team:
            continue  # already displayed
        st.text_input(f"{team_name} Name", key=f"team_name_{i+1}", value=team_name)
        players = st.session_state.drafted_players.get(team_name, [])
        if players:
            df_roster = pd.DataFrame(players)
            st.table(df_roster[["Round","Pick","Player","Team","Position"]])
        else:
            st.write("_No players picked yet_")

st.markdown("---")
