import pandas as pd
import networkx as nx
from sklearn.neighbors import BallTree
import numpy as np

# carregar os dados
csv_file_path = "filtered_crime_data.csv"
columns = ["DR_NO", "DATE OCC", "TIME OCC", "LAT", "LON", "Crm Cd"]

# leitura de um subconjunto menor de dados
df = pd.read_csv(csv_file_path, delimiter=',', usecols=columns, header=0)

# limitar os dados a um intervalo de tempo menor (por exemplo, 30 dias) no caso foi um ano
# Ajuste de formato para 'DATE OCC'
df['DATE OCC'] = pd.to_datetime(df['DATE OCC'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
# Filtrar por um ano inteiro (2023)
start_date = pd.to_datetime('2023-01-01 00:00:00')
end_date = pd.to_datetime('2024-01-01 00:00:00')

df = df[(df['DATE OCC'] >= start_date) & (df['DATE OCC'] < end_date)]


# limitar os dados a uma região geográfica específica (exemplo: Los Angeles)
df['LAT'] = pd.to_numeric(df['LAT'], errors='coerce')
df['LON'] = pd.to_numeric(df['LON'], errors='coerce')
df = df.dropna(subset=['LAT', 'LON'])
df = df[(df['LAT'] > 33.5) & (df['LAT'] < 34.5) & (df['LON'] > -118.5) & (df['LON'] < -118)]

# parâmetros reduzidos
time_window_hours = 24  # janela temporal 24hrs
distance_threshold_km = 0.5  # limite espacial 0.5km

# converter coordenadas para radianos
coordinates_radians = np.deg2rad(df[['LAT', 'LON']].values)
tree = BallTree(coordinates_radians, metric='haversine')

# Criar grafo simplificado
G = nx.Graph()

# Adicionar vértices
for index, row in df.iterrows():
    crime_id = row['DR_NO']
    G.add_node(crime_id, date_occ=row['DATE OCC'].strftime('%Y-%m-%d %H:%M:%S'), lat=row['LAT'], lon=row['LON'], crm_cd=row['Crm Cd'])

# distância para radianos (0.5 km = 0.5 / 6371 radianos)
distance_threshold_radians = distance_threshold_km / 6371.0

# Criar arestas entre crimes próximos espacial e temporalmente
for index1, row1 in df.iterrows():
    crime1 = row1['DR_NO']
    date1 = row1['DATE OCC']
    
    # definir janela temporal de +/- 24 horas
    min_time = date1 - pd.Timedelta(hours=time_window_hours)
    max_time = date1 + pd.Timedelta(hours=time_window_hours)

    # encontrar vizinhos espaciais usando BallTree
    query_point = np.deg2rad([[row1['LAT'], row1['LON']]])
    indices = tree.query_radius(query_point, r=distance_threshold_radians)[0]

    for index2 in indices:
        if index1 == index2:
            continue
        row2 = df.iloc[index2]
        crime2 = row2['DR_NO']
        date2 = row2['DATE OCC']
        
        # verificar se o crime está dentro da janela temporal
        if min_time <= date2 <= max_time:
            # adicionar aresta entre crimes próximos
            G.add_edge(crime1, crime2)

# salvar o grafo para futuras análises
nx.write_gml(G, "modelo_relacionamento_crimes.gml")