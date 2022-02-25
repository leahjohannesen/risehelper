from data.monsters import monster_ref
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time

BASE_URL = 'https://mhrise.kiranico.com/data/monsters/{}'
CSV_PATH = 'data/{}.csv'
TABLE_REF = {
    'hitzones': (0, ['monster', 'parts', 'state', 'sever', 'blunt', 'projectile', 'fire', 'water', 'ice', 'thunder', 'dragon', 'stun']),
    # 'ailments': 3,
    # 'drops': (7, ['monster', 'item', 'rank', 'method', 'amount', 'rate']),
    # 'quests': (8, ['monster', 'qtype', 'qlevel', 'qname', 'zone', 'rate']),
}

# pulls only monsters missing from any of the tables, force to re-pull all
# if a monster is missing in any table, it'll repull since all come from one request
def update_data(force=False):
    dfs, to_pull = load_dfs(force)
    if not to_pull:
        print('no monsters to pull, bailing')
        return
    i = 0
    for mname, mid in monster_ref.items():
        # skip if it's already present in all 3
        if mname not in to_pull:
            continue
        raw_monster_dfs = pull_monster_data(mid)
        formatted_monster_dfs = format_dfs(mname, raw_monster_dfs)
        dfs = append_dfs(dfs, mname, formatted_monster_dfs)
        # increment counter, save every 5
        i += 1
        if not i % 5:
            serialize_dfs(dfs)
        time.sleep(2)
    # final serialize
    serialize_dfs(dfs)
    return

## managing dfs

def load_dfs(force=False):
    output = {}
    all_monsters = set(monster_ref.keys())
    missing = set()
    for tbln, (_, cols) in TABLE_REF.items():
        try:
            df = pd.read_csv(CSV_PATH.format(tbln), index_col=0)
        except:
            df = pd.DataFrame([], columns=cols)
        output[tbln] = df
        missing |= all_monsters - set(df['monster'].unique())
    # a little extra compute but whatevs
    if force:
        missing = all_monsters
    print('dfs loaded, missing monsters')
    print(missing)
    return output, missing

def format_dfs(mname, raw_dfs):
    return {
        'hitzones': format_hitzones(mname, raw_dfs['hitzones']),
        # 'drops': format_drops(mname, raw_dfs['drops']),
        # 'quests': format_quests(mname, raw_dfs['quests']),
    }

def append_dfs(dfs, mname, monster_dfs):
    output = {}
    for tbln, df in dfs.items():
        # drop any w/ mname just in case
        dropped_df = df.drop((df[df['monster'] == mname]).index)
        output[tbln] = dropped_df.append(monster_dfs[tbln], ignore_index=True)
    return output

def serialize_dfs(dfs):
    for tbln, df in dfs.items():
        df.to_csv(CSV_PATH.format(tbln))
    return

## pull/formatting stuff

def pull_monster_data(mid):
    r = requests.get(BASE_URL.format(mid))
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.find_all('table')
    return {tblname: pd.read_html(str(tables[tblidx]))[0] for tblname, (tblidx, _) in TABLE_REF.items()}

def format_hitzones(mname, df):
    df.columns = TABLE_REF['hitzones'][1][1:]
    df = df.apply(lambda x: x.str.lower() if x.dtype == 'object' else x)
    df['monster'] = mname
    return df.loc[:, TABLE_REF['hitzones'][1]]

# might need to suppliment these with manual locations/%s, but for now this will suffice
# def format_drops(mname, df):
#     df.columns = TABLE_REF['drops'][1][1:]
#     df = df.apply(lambda x: x.str.lower() if x.dtype == 'object' else x)
#     rank_dict = {
#         'low rank': 'low',
#         'high rank': 'high',
#     }
#     method_dict = {
#         'target rewards': 'target',
#         'carves': 'carve',
#         'capture rewards': 'capture',
#         'broken part rewards': 'break',
#         'dropped materials': 'drop',
#         'items obtained by palico': 'palico',
#     }
#     df.replace({'rank': rank_dict, 'method': method_dict}, inplace=True)
#     df['amount'] = df['amount'].str.replace('x', '').astype(int)
#     df['rate'] = df['rate'].str.replace('%', '').astype(int)
#     df['monster'] = mname
#     return df.loc[:, TABLE_REF['drops'][1]]

# def format_quests(mname, df):
#     new_data = []
#     for raw_str in df[df['Players'] > 1]['Monster']:
#         # quest level
#         level = re.sub('[^0-9A-Za-z]', '', raw_str.split(' ')[0])
#         # quest title
#         start = re.search('\s', raw_str).start()
#         end = re.search('Area', raw_str).start()
#         name = raw_str[start + 1:end].lower()
#         # zone info
#         for match in re.finditer('Area (\d+) \((\d+)%\)', raw_str):
#             new_data.append((mname, level[0], int(level[1:]), name, int(match.group(1)), int(match.group(2))))
#     return pd.DataFrame(new_data, columns=['monster', 'qtype', 'qlevel', 'qname', 'zone', 'rate'])

# def format_ailments(mname, raw):
#     raw[['base', 'increase', 'cap']] = raw['Buildup'].str.replace('[^\s0-9]', '').str.split(' ', expand=True).astype(int)
#     print(split_vals)

if __name__ == '__main__':
    update_data()
