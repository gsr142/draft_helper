import streamlit as st
import pandas as pd

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
    "ARZ": 8,
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



# Initialize session state
def init_state(df):
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

    while ds["current_pick"] < total_picks:
        ds["current_pick"] += 1
        ds["current_round"] = ((ds["current_pick"] - 1) // ds["teams"]) + 1
        pick_pos_in_round = ((ds["current_pick"] - 1) % ds["teams"]) + 1
        if ds["current_round"] % 2 == 1:
            ds["current_team"] = pick_pos_in_round
        else:
            ds["current_team"] = ds["teams"] - pick_pos_in_round + 1

        team_name = f"Team {ds['current_team']}"
        # If this round is already occupied by a keeper for this team, skip it
        if any(p["Round"] == ds["current_round"] for p in st.session_state.keepers[team_name]):
            continue  # skip this pick
        break

def pick_player(player_name):
    ds = st.session_state.draft_settings
    team_name, round_num, pick_in_round = get_team_for_pick(ds["current_pick"], ds["teams"])

    # Add player to drafted_players for this team
    st.session_state.drafted_players.setdefault(team_name, []).append({
        "Round": round_num,
        "Pick": pick_in_round,
        "Rank": st.session_state.player_pool["Rank"][st.session_state.player_pool["Player"] == player_name].iloc[0],
        "Player": player_name,
        "Position": st.session_state.player_pool["Position"][st.session_state.player_pool["Player"] == player_name].iloc[0],
        "Team": st.session_state.player_pool["Team"][st.session_state.player_pool["Player"] == player_name].iloc[0],
        "Bye": st.session_state.player_pool["Bye"][st.session_state.player_pool["Player"] == player_name].iloc[0]
    })
    
    # Remove player from player_pool
    st.session_state.player_pool = st.session_state.player_pool[
        st.session_state.player_pool["Player"] != player_name
    ].reset_index(drop=True)

    advance_pick()

def reverse_pick():
    ds = st.session_state.draft_settings
    
    if ds["current_pick"] <= 1:
        return
    ds["current_pick"] -= 1
    ds["current_round"] = ((ds["current_pick"] - 1) // ds["teams"]) + 1
    pick_pos_in_round = ((ds["current_pick"] - 1) % ds["teams"]) + 1
    if ds["current_round"] % 2 == 1:
        ds["current_team"] = pick_pos_in_round
    else:
        ds["current_team"] = ds["teams"] - pick_pos_in_round + 1

def remove_player_from_team():
    ds = st.session_state.draft_settings

    # Roll back the draft pick first
    reverse_pick()
    team_name, _, _ = get_team_for_pick(ds["current_pick"], ds["teams"])

    if not st.session_state.drafted_players[team_name]:
        return  # Nothing to undo for this team

    # Get the last drafted player for this team
    player = st.session_state.drafted_players[team_name].pop()

    # Add player back into player_pool
    st.session_state.player_pool = pd.concat(
        [st.session_state.player_pool, pd.DataFrame([player])],
        ignore_index=True
    )

def add_keeper(team_name, player_name, round_num):
    # Get player info from player_pool
    player_row = st.session_state.player_pool[st.session_state.player_pool["Player"] == player_name]
    if player_row.empty:
        return
    
    player = {
        "Round": round_num,
        "Pick": None,  # no specific pick number, it's a keeper
        "Rank": player_row["Rank"].iloc[0],
        "Player": player_row["Player"].iloc[0],
        "Position": player_row["Position"].iloc[0],
        "Team": player_row["Team"].iloc[0],
        "Bye": player_row["Bye"].iloc[0],
        "Keeper": True
    }
    
    # Add keeper to drafted_players + keepers record
    st.session_state.drafted_players[team_name].append(player)
    st.session_state.keepers[team_name].append(player)
    
    # Remove from player_pool
    st.session_state.player_pool = st.session_state.player_pool[
        st.session_state.player_pool["Player"] != player_name
    ].reset_index(drop=True)
