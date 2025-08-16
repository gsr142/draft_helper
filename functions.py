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