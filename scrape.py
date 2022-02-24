from data.monsters import monster_ref
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

BASE_URL = 'https://mhrise.kiranico.com/data/monsters/{}'
TABLE_REF = {
    'hitzones': 0,
    # 'ailments': 3,
    'drops': 7,
    'quest': 8,
}

def pull_monster_data(mid, skip=False):
    r = requests.get(BASE_URL.format(mid))
    soup = BeautifulSoup(r.text, 'html.parser')
    tables = soup.find_all('table')
    raw_tbls = {tblname: pd.read_html(str(tables[tblidx]))[0] for tblname, tblidx in TABLE_REF.items()}
    return raw_tbls

def format_hitzones(mname, df):
    cols = ['parts', 'state', 'sever', 'blunt', 'projectile', 'fire', 'water', 'ice', 'thunder', 'dragon', 'stun']
    df.columns = cols
    df['monster'] = mname
    return df

def format_drops(mname, df):
    df.columns = df.columns.str.lower()
    df['amount'] = df['amount'].str.replace('x', '').astype(int)
    df['rate'] = df['rate'].str.replace('%', '').astype(int)
    df['monster'] = mname
    return df

def format_quest(mname, df):
    new_data = []
    for raw_str in df[df['Players'] > 1]['Monster']:
        # quest level
        level = re.sub('[^0-9A-Za-z]', '', raw_str.split(' ')[0])
        # quest title
        start = re.search('\s', raw_str).start()
        end = re.search('Area', raw_str).start()
        name = raw_str[start + 1:end]
        # zone info
        for match in re.finditer('Area (\d+) \((\d+)%\)', raw_str):
            new_data.append((mname, level[0], int(level[1:]), name, int(match.group(1)), int(match.group(2))))
    df = pd.DataFrame(new_data, columns=['monster', 'qtype', 'qlevel', 'qname', 'zone', 'rate'])
    return df

def format_quest_row(raw_str):
    level = re.sub('[^0-9A-Za-z]', '', raw_str.split(' ')[0])
    zones = []


# def format_ailments(mname, raw):
#     raw[['base', 'increase', 'cap']] = raw['Buildup'].str.replace('[^\s0-9]', '').str.split(' ', expand=True).astype(int)
#     print(split_vals)

if __name__ == '__main__':
    raw_tbls = pull_monster_data(monster_ref['rathian'])
    hz = format_hitzones('rathian', raw_tbls['hitzones'])
    drp = format_drops('rathian', raw_tbls['drops'])
    qst = format_quest('rathian', raw_tbls['quest'])
    pass
