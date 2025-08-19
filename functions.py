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
    # Base draft settings
    if "draft_settings" not in st.session_state:
        st.session_state.draft_settings = {
            "teams": 10,
            "rounds": 16,
            "current_pick": 1,
            "current_round": 1,
            "current_team": 1,
        }
    ds = st.session_state.draft_settings

    # Player pool
    if "player_pool" not in st.session_state:
        st.session_state.player_pool = df.copy()

    # Drafted players per team
    if "drafted_players" not in st.session_state:
        st.session_state.drafted_players = {f"Team {i+1}": [] for i in range(ds["teams"])}

    # Keepers storage (per team)
    if "keepers" not in st.session_state:
        st.session_state.keepers = {f"Team {i+1}": [] for i in range(ds["teams"])}
    else:
        # Ensure keys exist for current team count
        for i in range(ds["teams"]):
            st.session_state.keepers.setdefault(f"Team {i+1}", [])

# --- Draft logic helpers ---
def get_team_for_pick(pick_number, teams):
    round_number = (pick_number - 1) // teams + 1
    index_in_round = (pick_number - 1) % teams
    if round_number % 2 == 1:  # odd rounds left to right
        team_index = index_in_round
    else:  # even rounds right to left
        team_index = teams - 1 - index_in_round
    return f"Team {team_index+1}", round_number, index_in_round + 1

def is_keeper_slot(pick_number: int) -> bool:
    ds = st.session_state.draft_settings
    team_name, round_num, _ = get_team_for_pick(pick_number, ds["teams"])
    keepers_for_team = st.session_state.keepers.get(team_name, [])
    return any(p.get("Round") == round_num for p in keepers_for_team)

def _set_pick_for_matching_keeper(pick_number: int):
    # If a keeper occupies this pick, set its displayed Pick number for the roster table.
    ds = st.session_state.draft_settings
    team_name, round_num, pick_in_round = get_team_for_pick(pick_number, ds["teams"])
    for p in st.session_state.drafted_players.get(team_name, []):
        if p.get("Keeper") and p.get("Round") == round_num and p.get("Pick") in (None, ""):
            p["Pick"] = pick_in_round

def align_to_next_available_pick():
    # If the current pick is a keeper slot, advance until the next non-keeper slot.
    ds = st.session_state.draft_settings
    total_picks = ds["teams"] * ds["rounds"]
    while ds["current_pick"] <= total_picks and is_keeper_slot(ds["current_pick"]):
        _set_pick_for_matching_keeper(ds["current_pick"])
        if ds["current_pick"] >= total_picks:
            return
        ds["current_pick"] += 1
        ds["current_round"] = ((ds["current_pick"] - 1) // ds["teams"]) + 1
        pick_pos_in_round = ((ds["current_pick"] - 1) % ds["teams"]) + 1
        if ds["current_round"] % 2 == 1:
            ds["current_team"] = pick_pos_in_round
        else:
            ds["current_team"] = ds["teams"] - pick_pos_in_round + 1

def advance_pick():
    ds = st.session_state.draft_settings
    total_picks = ds["teams"] * ds["rounds"]
    if ds["current_pick"] >= total_picks:
        return

    # move to next pick
    ds["current_pick"] += 1
    ds["current_round"] = ((ds["current_pick"] - 1) // ds["teams"]) + 1
    pick_pos_in_round = ((ds["current_pick"] - 1) % ds["teams"]) + 1
    if ds["current_round"] % 2 == 1:
        ds["current_team"] = pick_pos_in_round
    else:
        ds["current_team"] = ds["teams"] - pick_pos_in_round + 1

    # Skip over keeper-occupied slots
    total_picks = ds["teams"] * ds["rounds"]
    while ds["current_pick"] <= total_picks and is_keeper_slot(ds["current_pick"]):
        _set_pick_for_matching_keeper(ds["current_pick"])
        if ds["current_pick"] >= total_picks:
            break
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

    while ds["current_pick"] > 1:
        # Roll back one pick
        reverse_pick()
        team_name, round_num, _ = get_team_for_pick(ds["current_pick"], ds["teams"])

        if not st.session_state.drafted_players[team_name]:
            continue  # nothing drafted here, keep going

        # Peek at last drafted player
        player = st.session_state.drafted_players[team_name][-1]

        if player.get("Keeper"):
            # Skip over keepers — don't remove them
            continue

        # ✅ Found a non-keeper, undo it
        st.session_state.drafted_players[team_name].pop()
        st.session_state.player_pool = pd.concat(
            [st.session_state.player_pool, pd.DataFrame([player])],
            ignore_index=True
        )
        break

def add_keeper(team_name: str, player_name: str, round_num: int):
    ds = st.session_state.draft_settings

    # Ensure keepers structure
    if "keepers" not in st.session_state:
        st.session_state.keepers = {f"Team {i+1}": [] for i in range(ds['teams'])}
    st.session_state.keepers.setdefault(team_name, [])

    # 🚫 Prevent more than one keeper per team
    if len(st.session_state.keepers[team_name]) >= 1:
        st.warning(f"{team_name} already has a keeper assigned.")
        return

    # Lookup player in pool
    player_row = st.session_state.player_pool[st.session_state.player_pool["Player"] == player_name]
    if player_row.empty:
        st.warning("Selected player not found in the player pool.")
        return

    # Build player dict marked as keeper
    player = {
        "Round": int(round_num),
        "Pick": None,
        "Rank": int(player_row["Rank"].iloc[0]),
        "Player": str(player_row["Player"].iloc[0]),
        "Position": str(player_row["Position"].iloc[0]),
        "Team": str(player_row["Team"].iloc[0]),
        "Bye": int(player_row["Bye"].iloc[0]),
        "Keeper": True
    }

    # Save on roster and in keepers ledger
    st.session_state.drafted_players.setdefault(team_name, []).append(player)
    st.session_state.keepers[team_name].append({"Player": player["Player"], "Round": player["Round"]})

    # Remove from player pool
    st.session_state.player_pool = st.session_state.player_pool[
        st.session_state.player_pool["Player"] != player_name
    ].reset_index(drop=True)

    # If this keeper occupies the current pick slot, ensure we jump to next available
    team_for_pick, round_for_pick, _ = get_team_for_pick(ds["current_pick"], ds["teams"])
    if team_for_pick == team_name and round_for_pick == round_num:
        align_to_next_available_pick()
