"""CPSC 322 Final Project: NBA Team Success Predictor
@author L. Martin
@author E. Johnson
@date April 18, 2022

data_prep.py
Description:
    This python file contains the functions
    used to clean the player and team data and prepare
    it for classification tasks in the success predictor
    project.
"""

from audioop import reverse
import os
import operator
from sre_constants import SUCCESS
import matplotlib.pyplot as plt
from math import sqrt
from unidecode import unidecode
from mysklearn.mypytable import MyPyTable

"""Globals (Change as data is added or removed)
    first_season(int): earliest season we have data for
        (i.e. 91 for 1990-1991 season)
    last_season(int): most recent season we have data for
        (i.e. 91 for 1990-1991 season)
    season_anomolies(dict of int, int pairs): keeps track of 
        seasons without the standard 82 games
        Note: in 2019-2020, non-bubble teams played around 63 games, 
            while bubble teams played 75
"""
first_season = 91
last_season = 21
season_anomolies = {21: 72, 20: 75, 12: 66, 99: 50}

def get_season_strings():
    """Creates a list of valid strings for the seasons we have in the format
    required for loading in the raw data from our input_data folder

    Returns:
        season_strings(list of strs): season strings in format 'XX_XX'
    """
    seasons = list(range(first_season, 100)) + list(range(0, last_season + 1))
    season_strings = []

    for season in seasons:
        begin = (season - 1) % 100
        if begin < 10:
            begin = "0" + str(begin)
        else:
            begin = str(begin)
        if season < 10:
            end = "0" + str(season)
        else:
            end = str(season)
        season_strings.append(begin + "_" + end)

    return season_strings

def get_raw_team_data():
    """Load all of the raw team data into a MyPyTable object
    Adds a column for season (i.e. 99 for 1998 - 1999 season)

    Returns:
        team_data(MyPyTable): table object containing the team information
    """
    seasons = get_season_strings()
    team_data = []
    for season in seasons:
        season_number = int(season[-2:])
        file_loc = "teams_" + season + ".csv"
        file_loc = os.path.join("input_data", "team_stats", file_loc)
        season_data = MyPyTable().load_from_file(file_loc, ascii=False)
        data = season_data.data
        # different month data columns for each season
        data = [[season_number] + row[:17] for row in data]
        team_data += data
    team_data = MyPyTable(["Season"] + season_data.column_names[:17], team_data)
    return team_data

def get_raw_player_data():
    """Load all of the raw player data into a MyPyTable object
    Adds a column for season (i.e. 99 for 1998 - 1999 season)

    Returns:
        player_data(MyPyTable): table object containing the player data
    """
    seasons = get_season_strings()
    player_data = []
    for season in seasons:
        season_number = int(season[-2:])
        file_loc = "players_" + season + ".csv"
        file_loc = os.path.join("input_data", "player_stats", file_loc)
        # can't use ascii because of european player names, must use utf-8
        season_data = MyPyTable().load_from_file(file_loc, ascii=False)
        data = season_data.data
        data = [[season_number] + row for row in data]
        player_data += data
    player_data = MyPyTable(["Season"] + season_data.column_names, player_data)
    return player_data

def clean_team_data(data):
    """Clean MyPyTable object containing the player data for later use

    Args:
        data(MyPyTable): table object containing the team data

    Cleaning Steps:
        1. Dropping columns
            Only keeping team name, season, and overall record
            Win percentage (later discretized) is the class we are
            trying to predict, and the rest of the labels are just
            win descriptions (i.e record by month, etc.)
        2. Extracting wins, losses, games played, and win percent from 'Overall' attribute
    """
    cols_to_keep = ["Team", "Season", "Overall"]
    col_indices = [data.column_names.index(col) for col in cols_to_keep]
    for i in range(len(data.data)):
        data.data[i] = [data.data[i][j] for j in col_indices]
    data.column_names = cols_to_keep

    record_index = data.column_names.index("Overall")
    for i in range(len(data.data)):
        record_str = data.data[i][record_index]
        record = record_str.split("-")
        wins = int(record[0])
        loses = int(record[1])
        games_played = wins + loses
        win_percent = wins / games_played
        success_rate = discretize_win_percent(win_percent)
        data.data[i] += [games_played, win_percent, wins, loses, success_rate]
    data.column_names += ["GP", "Win Percentage", "W", "L", "Success"]


def clean_player_data(data):
    """Clean MyPyTable object containing the player data for later use

    Args:
        data(MyPyTable): table object containing the player data

    Cleaning Steps:
        1. decode the team abbreviation column so it can be joined with team data
        2. fix the player name column by 
            * getting rid of basketball reference code for players
            * getting rid of asterisks denoting hall of famers
            * getting rid of special accented characters in names
        3. Dropping columns
            * Rk: just a numbering of players for that season, irrelevant when combined
    """
    teams = {"ATL":	"Atlanta Hawks", "BRK":	"Brooklyn Nets", "BOS": "Boston Celtics",
             "CHO":	"Charlotte Hornets", "CHI":	"Chicago Bulls", "CLE": "Cleveland Cavaliers",
             "DAL":	"Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
             "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
             "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
             "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
             "NOP":	"New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
             "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHO": "Phoenix Suns",
             "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
             "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards",
             # old, non-current teams
             "WSB": "Washington Bullets", "NJN": "New Jersey Nets", "SEA": "Seattle SuperSonics", 
             "CHH": "Charlotte Hornets", "VAN": "Vancouver Grizzlies", "NOH": "New Orleans Hornets",
             "CHA": "Charlotte Bobcats", "NOK": "New Orleans/Oklahoma City Hornets",  
             # used to keep track of players stats for whole year if traded, signed, etc.
             "TOT": "Total"}

    team_index = data.column_names.index("Tm")
    name_index = data.column_names.index("Player")
    for row in data.data:
        # cleaning team column
        row[team_index] = teams[row[team_index]]
        # cleaning player column
        player_name = row[name_index]
        player_name = unidecode(player_name)
        player_name = player_name.split("\\")[0]
        if player_name[-1] == "*":
            player_name = player_name[:-1]
        row[name_index] = player_name
    data.drop_column("Rk")
    data.column_names[data.column_names.index("Tm")] = "Team"

    pts_index = data.column_names.index("PTS")
    min_index = data.column_names.index("MP")
    for i in range(len(data.data)):
        ppg = data.data[i][pts_index]
        mpg = data.data[i][min_index]
        data.data[i] = data.data[i] + [jortin_per_36(ppg, mpg)]
    data.column_names += ["JPPG"]

def jortin_per_36(stat_per_game, minutes_per_game):
    """TODO:
    """
    return -1 * sqrt(9 * minutes_per_game) + stat_per_game + 18

def discretize_jppg(jppg):
    if jppg < 85:
        return 1
    elif jppg < 90:
        return 2
    elif jppg < 95:
        return 3
    elif jppg < 100:
        return 4
    elif jppg < 105:
        return 5
    elif jppg < 110:
        return 6
    elif jppg < 115:
        return 7
    elif jppg < 120:
        return 8
    elif jppg < 125:
        return 9
    elif jppg < 130:
        return 10
    elif jppg < 135:
        return 11
    else:
        return 12

def discretize_win_percent(percent): # games won if 82 game season
    if percent < 0.25: # <20 games won
        return 1
    elif percent < 0.43: # <35 games won
        return 2
    elif percent < 0.60: # <50 games won
        return 3
    elif percent < 0.75: # <65 games won
        return 4
    else:                # >= 65 games won
        return 5

def discretize_trb(rebounds):
    if rebounds < 35:
        return 1
    elif rebounds < 40:
        return 2
    elif rebounds < 45:
        return 3
    elif rebounds < 50:
        return 4
    else:
        return 5

def discretize_ast(assists):
    if assists < 20:
        return 1
    elif assists < 25:
        return 2
    elif assists < 30:
        return 3
    elif assists < 35:
        return 4
    else:
        return 5


def create_team_data(data):
    """TODO:
    """
    rows = []
    column_names = ["Team", "Season", "JPPG", "TRB", "AST", "Success"]
    top_n = 7 # Number of players

    for team_name, season_dict in data.items():
        for season, table in season_dict.items():
            team_games = table.data[0][table.column_names.index("GP")]
            team_success = table.data[0][table.column_names.index("Success")]

            jppg = table.get_column("JPPG") # Jortin PPG Creation
            games_played = table.get_column("G")
            jppg = [round(jppg[i] * (games_played[i] / team_games), 2) for i in range(len(jppg))]
            jppg.sort(reverse=True)
            jppg = jppg[0:top_n]
            jppg = sum(jppg)
            jppg = discretize_jppg(jppg) 

            trb = table.get_column("TRB") # Total Rebounds
            trb.sort(reverse=True)
            trb = trb[0:top_n]
            trb = sum(trb)
            trb = discretize_trb(trb)

            ast = table.get_column("AST") # Total Assists
            ast.sort(reverse=True)
            ast = ast[0:top_n]
            ast = sum(ast)
            ast = discretize_ast(ast)

            rows.append([team_name, season, jppg, trb, ast, team_success]) # Adds stat row to table

    return MyPyTable(column_names, rows)


def main():
    """Used to test validity of functions and to 
    call functions that store data in .csv files
    """
    teams = get_raw_team_data()
    players = get_raw_player_data()
    clean_player_data(players)
    clean_team_data(teams)

    cleaned_player_loc = os.path.join("input_data", "processed_data", "player_stats.csv")
    cleaned_team_loc = os.path.join("input_data", "processed_data", "team_info.csv")
    cleaned_joined_loc = os.path.join("input_data", "processed_data", "team_player_stats.csv")

    teams.save_to_file(cleaned_team_loc)
    players.save_to_file(cleaned_player_loc)
    player_season_stats = teams.perform_inner_join(players, ["Season", "Team"])
    player_season_stats.save_to_file(cleaned_joined_loc)

    teams_stats = player_season_stats.groupby("Team", "Season")
    team_data = create_team_data(teams_stats)
    data_loc = os.path.join("input_data", "processed_data", "team_stats.csv")
    team_data.save_to_file(data_loc)

    data = team_data.data
    data.sort(key=operator.itemgetter(5)) # Sorts by attribute
    print(data)
    

if __name__ == "__main__":
    main()