# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Fantasy Draft Sheet", layout="wide")

# --- Helpers ---
def sample_df():
    return pd.DataFrame([
        {"Rank": 1, "Player": "Justin Jefferson", "Team": "MIN", "Position": "WR", "Bye": 6, "ProjPts": 280, "Tier": 1},
        {"Rank": 2, "Player": "Christian McCaffrey", "Team": "SF", "Position": "RB", "Bye": 9, "ProjPts": 320, "Tier": 1},
        {"Rank": 3, "Player": "Ja'Marr Chase", "Team": "CIN", "Position": "WR", "Bye": 7, "ProjPts": 250, "Tier": 1},
        {"Rank": 10, "Player": "Travis Kelce", "Team": "KC", "Position": "TE", "Bye": 10, "ProjPts": 170, "Tier": 2},
        {"Rank": 40, "Player": "Darren Waller", "Team": "NYG", "Position": "TE", "Bye": 8, "ProjPts": 110, "Tier": 4},
        {"Rank": 25, "Player": "Najee Harris", "Team": "PIT", "Position": "RB", "Bye": 9, "ProjPts": 160, "Tier": 3},
    ])

def init_state():
    if "roster" not in st.session_state:
        st.session_state.roster = []
    if "draft_picks" not in st.session_state:
        st.session_state.draft_picks = []
    if "draft_settings" not in st.session_state:
        st.session_state.draft_settings = {
            "teams": 10,
            "rounds": 16,
            "current_pick": 1,
            "current_round": 1,
            "current_team": 1
        }

def advance_pick():
    ds = st.session_state.draft_settings
    total_picks = ds["teams"] * ds["rounds"]

    if ds["current_pick"] >= total_picks:
        return  # Draft complete

    ds["current_pick"] += 1
    ds["current_round"] = ((ds["current_pick"] - 1) // ds["teams"]) + 1

    pick_pos_in_round = ((ds["current_pick"] - 1) % ds["teams"]) + 1
    if ds["current_round"] % 2 == 1:
        ds["current_team"] = pick_pos_in_round
    else:
        ds["current_team"] = ds["teams"] - pick_pos_in_round + 1

def add_to_roster(player_row):
    st.session_state.roster.append(player_row.to_dict())
    advance_pick()

def remove_from_roster(idx):
    st.session_state.roster.pop(idx)

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

# --- App Layout ---
init_state()

st.title("⚡ Fantasy Football — Live Draft Sheet with Snake Draft Tracker")

# Sidebar
with st.sidebar:
    st.header("Load Data")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    use_sample = st.button("Use example data")

    st.markdown("---")
    st.header("Filters")
    search = st.text_input("Search (name/team)")
    positions = st.multiselect("Position", options=["QB","RB","WR","TE","K","DEF"], default=[])
    teams_filter = st.multiselect("Team", options=[], default=[])
    bye_range = st.slider("Bye Week", 0, 17, (0, 17))
    pts_min, pts_max = st.slider("Projected Points", 0, 500, (0, 500))
    tier_sel = st.multiselect("Tier", options=[], default=[])
    sort_by = st.selectbox("Sort by", options=["Rank","ProjPts","Player","Tier"], index=0)
    ascending = st.checkbox("Ascending", value=False)

    st.markdown("---")
    st.header("Roster Controls")
    max_roster = st.number_input("Max roster size", min_value=1, max_value=30, value=15)
    if st.button("Clear roster"):
        st.session_state.roster = []

    st.markdown("---")
    st.header("Snake Draft Tracker")

    ds = st.session_state.draft_settings
    if ds["current_pick"] == 1 and not st.session_state.roster:
        teams = st.number_input("Number of teams", min_value=2, max_value=20, value=10, step=1)
        rounds = st.number_input("Number of rounds", min_value=1, max_value=30, value=16, step=1)
        if st.button("Start Draft"):
            ds["teams"] = teams
            ds["rounds"] = rounds
            ds["current_pick"] = 1
            ds["current_round"] = 1
            ds["current_team"] = 1

    st.write(f"**Current Pick:** {ds['current_pick']} (Round {ds['current_round']}, Team {ds['current_team']})")
    total_picks = ds["teams"] * ds["rounds"]
    picks_left = total_picks - ds["current_pick"] + 1
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

# Load DataFrame
if uploaded is not None:
    df = pd.read_csv(uploaded)
elif use_sample:
    df = sample_df()
else:
    df = sample_df()

# Normalize column names
col_map = {}
for c in df.columns:
    lc = c.lower()
    if lc in ("player","name"): col_map[c] = "Player"
    if lc in ("team","tm"): col_map[c] = "Team"
    if lc in ("position","pos"): col_map[c] = "Position"
    if lc in ("bye","bye_week"): col_map[c] = "Bye"
    if lc in ("projpts","projected points","projected_points","points"): col_map[c] = "ProjPts"
    if lc in ("rank","rk"): col_map[c] = "Rank"
    if lc in ("tier",): col_map[c] = "Tier"
if col_map:
    df = df.rename(columns=col_map)
for required in ["Player","Team","Position","Bye","ProjPts","Rank","Tier"]:
    if required not in df.columns:
        df[required] = "" if required not in ("Bye","Rank","Tier","ProjPts") else 0

# Apply filters
filtered = df.copy()
if search:
    mask = filtered["Player"].astype(str).str.contains(search, case=False, na=False) | \
           filtered["Team"].astype(str).str.contains(search, case=False, na=False)
    filtered = filtered[mask]
if positions:
    filtered = filtered[filtered["Position"].isin(positions)]
if teams_filter:
    filtered = filtered[filtered["Team"].isin(teams_filter)]
filtered = filtered[(filtered["Bye"].fillna(0) >= bye_range[0]) & (filtered["Bye"].fillna(0) <= bye_range[1])]
filtered = filtered[(filtered["ProjPts"].fillna(0) >= pts_min) & (filtered["ProjPts"].fillna(0) <= pts_max)]
if tier_sel:
    filtered = filtered[filtered["Tier"].isin(tier_sel)]
if sort_by in filtered.columns:
    filtered = filtered.sort_values(by=sort_by, ascending=ascending)

# Main content
col1, col2 = st.columns((2, 1))

with col1:
    st.subheader("Players")
    st.caption(f"Showing {len(filtered)} players (from {len(df)} total).")
    try:
        st.dataframe(df_style_by_tier(filtered), height=500)
    except Exception:
        st.dataframe(filtered, height=500)

    st.markdown("---")
    st.subheader("Select players to add to roster")
    player_options = filtered["Player"].astype(str).tolist()
    sel_players = st.multiselect("Pick one or more players", options=player_options)
    if st.button("Add selected players to roster"):
        for p in sel_players:
            row = filtered[filtered["Player"].astype(str) == p].iloc[0]
            existing_names = [r["Player"] for r in st.session_state.roster]
            if row["Player"] not in existing_names and len(st.session_state.roster) < max_roster:
                add_to_roster(row)
        st.success("Players added.")

    st.markdown("Or add players one-by-one:")
    for i, row in filtered.reset_index(drop=True).iterrows():
        cols = st.columns([4,1])
        cols[0].write(f"**{row['Player']}** — {row['Position']} — {row['Team']} — Bye: {row['Bye']} — {row.get('ProjPts','')}")
        if cols[1].button("Add", key=f"add_{row['Player']}_{i}"):
            existing_names = [r["Player"] for r in st.session_state.roster]
            if row["Player"] not in existing_names and len(st.session_state.roster) < max_roster:
                add_to_roster(row)
                st.experimental_rerun()

with col2:
    st.subheader("My Roster")
    roster_df = pd.DataFrame(st.session_state.roster)
    if roster_df.empty:
        st.info("Roster is empty — add players from the left.")
    else:
        st.table(roster_df[["Player","Position","Team","Bye","ProjPts","Tier"]])
        if st.button("Export roster CSV"):
            csv = roster_df.to_csv(index=False).encode("utf-8")
            st.download_button("Download roster.csv", data=csv, file_name="roster.csv", mime="text/csv")
        remove_names = [f"{r['Player']} — {r.get('Position','')}" for r in st.session_state.roster]
        to_remove = st.selectbox("Remove player", options=["(none)"] + remove_names)
        if st.button("Remove selected"):
            if to_remove != "(none)":
                idx = remove_names.index(to_remove)
                remove_from_roster(idx)
                st.experimental_rerun()
    st.markdown("---")
    st.subheader("Roster summary")
    if not roster_df.empty:
        pos_counts = roster_df["Position"].value_counts().reset_index()
        pos_counts.columns = ["Position", "Count"]
        st.table(pos_counts)
