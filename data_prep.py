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

import os
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
        season_number = season[-2:]
        file_loc = "teams_" + season + ".csv"
        file_loc = os.path.join("input_data", "team_stats", file_loc)
        season_data = MyPyTable().load_from_file(file_loc)
        data = season_data.data
        # different month data columns for each season
        data = [[season_number] + row[:17] for row in data]
        team_data += data
    team_data = MyPyTable(["Season"] + season_data.column_names[:17], team_data)
    team_data.drop_column("Rk")
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
        season_number = season[-2:]
        file_loc = "players_" + season + ".csv"
        file_loc = os.path.join("input_data", "player_stats", file_loc)
        # can't use ascii because of european player names, must use utf-8
        season_data = MyPyTable().load_from_file(file_loc, ascii=False)
        data = season_data.data
        data = [[season_number] + row for row in data]
        player_data += data
    player_data = MyPyTable(["Season"] + season_data.column_names, player_data)
    player_data.drop_column("Rk")
    return player_data

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

def main():
    """Used to test validity of functions and to 
    call functions that store data in .csv files
    """
    teams = get_raw_team_data()
    players = get_raw_player_data()
    clean_player_data(players)

    cleaned_player_loc = os.path.join("input_data", "processed_data", "player_stats.csv")
    cleaned_team_loc = os.path.join("input_data", "processed_data", "team_info.csv")
    teams.save_to_file(cleaned_team_loc)
    players.save_to_file(cleaned_player_loc)
    

if __name__ == "__main__":
    main()