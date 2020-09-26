import numpy as np
import pandas as pd

import data_calculation as data_calculation
import data_handler as data_handler
from api_handler import Api_handler
from logger import log
from team import Team
from utils import apply_weight_sum_model
from dateutil.relativedelta import relativedelta
import requests
from datetime import datetime

STEAM_URL = 'http://api.steampowered.com/IDOTA2Match_570/GetLiveLeagueGames/V001/?format=json&key=122661F7EE442A064BD2DA08484274DE'


class Live_watcher(Api_handler):
    def __init__(self):
        super().__init__('live')
        self.stratz_api = 'https://api.stratz.com/api/v1/'

    def get_json(self):
        return pd.read_json(self.exec_query(to_json=False))

    def parse_steam(self):
        df = pd.DataFrame(requests.get(STEAM_URL).json())

        ready_for_dataset = self.process_live_batch_for_steam(
            df)
        # ready_for_dataset['winner'] = 'na'
        # ready_for_dataset['version'] = 0
        ready_for_dataset = ready_for_dataset.dropna()
        dataset = data_handler.make_dataset(ready_for_dataset, is_prediction=True, additional_values=[
            'league_id', 'last_update_time'])
        return dataset

    def process_live_batch_for_steam(self, df):
        df = pd.DataFrame(df['result']['games'])
        matches = pd.DataFrame()
        for game in df.itertuples():
            if not pd.isna(game.radiant_team) and not pd.isna(game.dire_team) and not pd.isna(game.scoreboard):
                try:
                    data = pd.Series()
                    data['match_id'] = game.match_id
                    data['league_id'] = game.league_id
                    radiant_team = {}
                    radiant_team['team_name'] = (
                        str(game.radiant_team['team_name']).strip("'")).replace("'", "")
                    radiant_team['team_id'] = game.radiant_team['team_id']
                    radiant_team['players'] = pd.DataFrame(
                        game.scoreboard['radiant']['players'])

                    dire_team = {}
                    dire_team['team_name'] = (
                        str(game.dire_team['team_name']).strip("'")).replace("'", "")
                    dire_team['team_id'] = game.dire_team['team_id']
                    dire_team['players'] = pd.DataFrame(
                        game.scoreboard['dire']['players'])

                    # ? Fill teams
                    data['radiant_team'] = Team(radiant_team,
                                                radiant_team['players'])
                    data['dire_team'] = Team(dire_team,
                                             dire_team['players'])
                    # ? ===================

                    # ? Synergy scores
                    log('DEBUG', 'Compute players heroes synergy')
                    data['radiant_team'].synergy_score, data['radiant_team'].synergy_wsm_score = data_calculation.players_heroes_synergy(
                        data['radiant_team'].players.account_id, data['radiant_team'].players.hero_id)
                    data['dire_team'].synergy_score, data['dire_team'].synergy_wsm_score = data_calculation.players_heroes_synergy(
                        data['dire_team'].players.account_id, data['dire_team'].players.hero_id)
                    # ? ===================

                    # ? Matchup scores
                    log('DEBUG', 'Compute heroes matchup scores')
                    data['radiant_team'].matchup_score, data['radiant_team'].matchup_wsm_score, data['dire_team'].matchup_score, data['dire_team'].matchup_wsm_score = data_calculation.heroes_matchup(
                        (data['radiant_team'].players.hero_id), (data['dire_team'].players.hero_id))
                    # ? ===================

                    # ? Matchup scores stratz
                    log('DEBUG', 'Compute heroes matchup scores')
                    data['radiant_team'].synergy_against, data['radiant_team'].winrate_against, data['radiant_team'].synergy_with, data['radiant_team'].winrate_with, data['dire_team'].synergy_against, data['dire_team'].winrate_against, data['dire_team'].synergy_with, data['dire_team'].winrate_with, = data_calculation.heroes_matchup_stratz(
                        (data['radiant_team'].players.hero_id), (data['dire_team'].players.hero_id))
                    # ? ===================

                    # ? Players peers scores
                    log('DEBUG', 'Compute players heroes synergy')
                    data['radiant_team'].peers_score, data['radiant_team'].peers_wsm_score = data_calculation.players_peers(
                        data['radiant_team'].players.account_id)
                    data['dire_team'].peers_score, data['dire_team'].peers_wsm_score = data_calculation.players_peers(
                        data['dire_team'].players.account_id)
                    # ? ===================

                    data['last_update_time'] = str(datetime.utcnow())
                    if radiant_team['team_id'] > 0 and dire_team['team_id'] > 0 and (len(data['radiant_team'].players) + len(data['dire_team'].players)) == 10:
                        matches = matches.append(data, ignore_index=True)
                    else:
                        log('INFO',
                            f'Game not ready {data.game_time} {data.scraped_time} {data.match_id} {data.team_name_dire} vs {data.team_name_radiant} / nb players = {(len(data["radiant_team"].players) + len(data["dire_team"].players))}')
                except:
                    pass
        return matches

    def get_live_data_stratz(self, ids):
        df = pd.DataFrame()
        for id in ids:
            log('DEBUG', f'request {self.stratz_api}match/{id}/live')
            r = requests.get(self.stratz_api + f'match/{id}/live')
            if r.status_code == 200:
                df = df.append(pd.Series(r.json()), ignore_index=True)
            else:
                log('INFO', f'match id {id} not ready')
        return df

    def get_current_games_stats_stratz(self):
        df = self.get_json()
        if 'team_id_radiant' not in df.columns.values and 'team_id_dire' not in df.columns.values:
            return pd.DataFrame()
        incoming_games = df[(df.team_id_radiant.notnull()) & (
            df.team_id_dire.notnull()) & (df.deactivate_time == 0)]
        if len(incoming_games) > 0:
            incoming_games = self.get_live_data_stratz(incoming_games.match_id)
            ready_for_dataset = self.process_live_batch_stratz(
                incoming_games)
            ready_for_dataset['winner'] = 'na'
            ready_for_dataset['version'] = 0
            ready_for_dataset = ready_for_dataset.dropna()
            dataset = data_handler.make_dataset(ready_for_dataset, is_prediction=True, additional_values=[
                'gameTime', 'gameMode', 'leagueId', 'last_update_time'])
            return dataset
        else:
            log('INFO', 'No games currently in live stratz with enough data')
            return pd.DataFrame()

    def get_current_games_stats(self, append=True):
        df = self.get_json()
        if 'team_id_radiant' not in df.columns.values and 'team_id_dire' not in df.columns.values:
            return pd.DataFrame()
        incoming_games = df[(df.team_id_radiant.notnull())
                            & (df.team_id_dire.notnull())]
        nb_games = len(incoming_games)
        # incoming_games.to_csv('data/incoming_games_raw.csv', index=False)
        if nb_games > 0:
            ready_for_dataset = self.process_live_batch(
                incoming_games)
            ready_for_dataset['winner'] = 'na'
            ready_for_dataset['version'] = 0
            ready_for_dataset = ready_for_dataset.dropna()
            dataset = data_handler.make_dataset(ready_for_dataset, is_prediction=True, additional_values=[
                'game_time',  'average_mmr', 'game_mode', 'league_id', 'last_update_time'])
            return dataset
        else:
            return pd.DataFrame()

    def process_live_batch_stratz(self, games_data):
        matches = pd.DataFrame()
        for game_data in games_data.itertuples():
            try:
                data = {}
                radiant_team = {}
                radiant_team['team_id'] = game_data.radiantTeamId
                radiant_team['team_name'] = (
                    str(game_data.radiantTeam['name']).strip("'")).replace("'", "")

                dire_team = {}
                dire_team['team_id'] = game_data.direTeamId
                dire_team['team_name'] = (
                    str(game_data.direTeam['name']).strip("'")).replace("'", "")
                players = pd.DataFrame(
                    filter(lambda x: 'isRadiant' in x, game_data.players))
                if len(players) >= 5:
                    # ? If 5 players has isRadiant variable
                    players = pd.DataFrame(game_data.players)[
                        ['steamId', 'heroId', 'isRadiant', 'name']]
                    players['hero_id'] = players['heroId']
                    players['account_id'] = players['steamId']

                    players.loc[players.isRadiant,
                                'team_id'] = game_data.radiantTeamId
                    players.loc[players.isRadiant == False,
                                'team_id'] = game_data.direTeamId
                # ? Fill teams
                data['radiant_team'] = Team(radiant_team,
                                            players[players['isRadiant']])
                data['dire_team'] = Team(dire_team,
                                         players[players['isRadiant'] == False])
                # ? ===================

                # ? Synergy scores
                log('DEBUG', 'Compute players heroes synergy')
                data['radiant_team'].synergy_score, data['radiant_team'].synergy_wsm_score = data_calculation.players_heroes_synergy(
                    data['radiant_team'].players.account_id, data['radiant_team'].players.hero_id)
                data['dire_team'].synergy_score, data['dire_team'].synergy_wsm_score = data_calculation.players_heroes_synergy(
                    data['dire_team'].players.account_id, data['dire_team'].players.hero_id)
                # ? ===================

                # ? Matchup scores
                log('DEBUG', 'Compute heroes matchup scores')
                data['radiant_team'].matchup_score, data['radiant_team'].matchup_wsm_score, data['dire_team'].matchup_score, data['dire_team'].matchup_wsm_score = data_calculation.heroes_matchup(
                    (data['radiant_team'].players.hero_id), (data['dire_team'].players.hero_id))
                # ? ===================

                # ? Matchup scores stratz
                log('DEBUG', 'Compute heroes matchup scores')
                data['radiant_team'].synergy_against, data['radiant_team'].winrate_against, data['radiant_team'].synergy_with, data['radiant_team'].winrate_with, data['dire_team'].synergy_against, data['dire_team'].winrate_against, data['dire_team'].synergy_with, data['dire_team'].winrate_with, = data_calculation.heroes_matchup_stratz(
                    (data['radiant_team'].players.hero_id), (data['dire_team'].players.hero_id))
                # ? ===================

                # ? Players peers scores
                log('DEBUG', 'Compute players heroes synergy')
                data['radiant_team'].peers_score, data['radiant_team'].peers_wsm_score = data_calculation.players_peers(
                    data['radiant_team'].players.account_id)
                data['dire_team'].peers_score, data['dire_team'].peers_wsm_score = data_calculation.players_peers(
                    data['dire_team'].players.account_id)
                # ? ===================

                data['match_id'] = game_data.matchId
                data['winner'] = pd.NA
                data['version'] = pd.NA
                data['game_time'] = game_data.gameTime
                # data['average_mmr'] = game_data.average_mmr
                data['game_mode'] = game_data.gameMode
                data['league_id'] = game_data.leagueId
                # ? To timestamp FR
                data['last_update_time'] = datetime.utcnow().strftime("%Y-%m-%d")

                if radiant_team['team_id'] > 0 and dire_team['team_id'] > 0 and (len(data['radiant_team'].players) + len(data['dire_team'].players)) == 10:
                    matches = matches.append(data, ignore_index=True)
                else:
                    log('INFO',
                        f'Game not ready  {game_data.last_update_time} {game_data.match_id} {game_data.team_name_dire} vs {game_data.team_name_radiant} / nb players = {len(players)}')
            except:
                pass
        return matches

    def process_live_batch(self, games_data):
        matches = pd.DataFrame()
        for game_data in games_data.itertuples():
            try:
                data = {}
                radiant_team = {}
                radiant_team['team_id'] = game_data.team_id_radiant
                radiant_team['team_name'] = str(
                    game_data.team_name_radiant).strip("'").replace("'", "")

                dire_team = {}
                dire_team['team_id'] = game_data.team_id_dire
                dire_team['team_name'] = str(
                    game_data.team_name_dire).strip("'").replace("'", "")
                players = pd.DataFrame(
                    filter(lambda x: 'team_id' in x, game_data.players))
                if len(players) == 10:
                    # ? If everybody has a team_id
                    players = pd.DataFrame(game_data.players)[
                        ['account_id', 'hero_id', 'team_id', 'name', 'is_pro']]
                    players['isRadiant'] = players['team_id'] == game_data.team_id_radiant
                elif len(players) >= 5:
                    # ? If at least 5 players have a team_id , we can deduce the 5 other's team.
                    players['isRadiant'] = players['team_id'] == game_data.team_id_radiant
                    players['team_name'] = np.where(
                        players.isRadiant, game_data.team_name_radiant, game_data.team_name_dire)

                # ? Fill teams
                data['radiant_team'] = Team(radiant_team,
                                            players[players['isRadiant']])
                data['dire_team'] = Team(dire_team,
                                         players[players['isRadiant'] == False])
                # ? ===================

                # ? Synergy scores
                log('DEBUG', 'Compute players heroes synergy')
                data['radiant_team'].synergy_score, data['radiant_team'].synergy_wsm_score = data_calculation.players_heroes_synergy(
                    data['radiant_team'].players.account_id, data['radiant_team'].players.hero_id)
                data['dire_team'].synergy_score, data['dire_team'].synergy_wsm_score = data_calculation.players_heroes_synergy(
                    data['dire_team'].players.account_id, data['dire_team'].players.hero_id)
                # ? ===================

                # ? Matchup scores
                log('DEBUG', 'Compute heroes matchup scores')
                data['radiant_team'].matchup_score, data['radiant_team'].matchup_wsm_score, data['dire_team'].matchup_score, data['dire_team'].matchup_wsm_score = data_calculation.heroes_matchup(
                    (data['radiant_team'].players.hero_id), (data['dire_team'].players.hero_id))
                # ? ===================

                # ? Matchup scores stratz
                log('DEBUG', 'Compute heroes matchup scores')
                data['radiant_team'].synergy_against, data['radiant_team'].winrate_against, data['radiant_team'].synergy_with, data['radiant_team'].winrate_with, data['dire_team'].synergy_against, data['dire_team'].winrate_against, data['dire_team'].synergy_with, data['dire_team'].winrate_with, = data_calculation.heroes_matchup_stratz(
                    (data['radiant_team'].players.hero_id), (data['dire_team'].players.hero_id))
                # ? ===================

                # ? Players peers scores
                log('DEBUG', 'Compute players heroes synergy')
                data['radiant_team'].peers_score, data['radiant_team'].peers_wsm_score = data_calculation.players_peers(
                    data['radiant_team'].players.account_id)
                data['dire_team'].peers_score, data['dire_team'].peers_wsm_score = data_calculation.players_peers(
                    data['dire_team'].players.account_id)
                # ? ===================

                data['match_id'] = game_data.match_id
                data['winner'] = pd.NA
                data['version'] = pd.NA
                data['game_time'] = game_data.game_time
                data['average_mmr'] = game_data.average_mmr
                data['game_mode'] = game_data.game_mode
                data['league_id'] = game_data.league_id
                # ? To timestamp FR
                data['last_update_time'] = (
                    game_data.last_update_time + relativedelta(hours=1)).strftime("%Y-%m-%d")

                if radiant_team['team_id'] > 0 and dire_team['team_id'] > 0 and (len(data['radiant_team'].players) + len(data['dire_team'].players)) == 10:
                    matches = matches.append(data, ignore_index=True)
                else:
                    log('INFO',
                        f'Game not ready  {game_data.last_update_time} {game_data.match_id} {game_data.team_name_dire} vs {game_data.team_name_radiant} / nb players = {len(players)}')
            except:
                pass
        return matches



def get_live():
    l = Live_watcher()
    to_predict = pd.DataFrame()
    to_predict3 = l.get_current_games_stats_stratz()
    to_predict3['source'] = 'stratz'
    to_predict = l.parse_steam()
    to_predict['source'] = 'steam'
    to_predict = pd.DataFrame()
    to_predict2 = l.get_current_games_stats()
    to_predict2['source'] = 'openDota'
    log('SUCCESS',
        f'Found OpenDota : {len(to_predict2)} , stratz : {len(to_predict3)} , steam : {len(to_predict)} on live')
    
    df = pd.concat([to_predict, to_predict2, to_predict3]).drop_duplicates(subset="match_id")
    df.to_csv('./data/incoming_games_dataset.csv', index=False)
    return df


if __name__ == "__main__":
    get_live()