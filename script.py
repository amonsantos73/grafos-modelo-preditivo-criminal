import pandas as pd
import networkx as nx
from geopy.distance import geodesic
from datetime import datetime
import matplotlib.pyplot as plt

# função para calcular a distância geográfica entre duas coordenadas (latitude, longitude)
def calc_distance(coord1, coord2):
    print(f"Calculando distância entre {coord1} e {coord2}")
    try:
        return geodesic(coord1, coord2).kilometers
    except ValueError as e:
        print(f"Erro nas coordenadas: {e}")
        return float('inf') 

# função para calcular a diferença de tempo em horas
def calc_time_diff(time1, time2):
    diff = time2 - time1
    return diff.total_seconds() / 3600  # converte segundos para horas

# carregar os dados
csv_file_path = "Crime_Data_from_2020_to_Present.csv"

columns = ["DR_NO", "DATE OCC", "TIME OCC", "LAT", "LON"]

# leitura do arquivo CSV com apenas as colunas necessárias
df = pd.read_csv(csv_file_path, delimiter=',', usecols=columns, header=0)

# limpeza e processamento dos dados como antes

# limpar colunas de data e hora
df['DATE OCC'] = df['DATE OCC'].str.replace(r'( AM| PM|:00)', '', regex=True).str.strip()
df['DATE OCC'] = pd.to_datetime(df['DATE OCC'], errors='coerce')

# função para converter o horário de forma segura
def convert_time(time_str):
    try:
        return pd.to_datetime(time_str, format='%H%M', errors='coerce').time()
    except:
        return None  # retorna None se o formato for inválido

df['TIME OCC'] = df['TIME OCC'].apply(convert_time)

# garantir que LAT e LON sejam numéricos
df['LAT'] = pd.to_numeric(df['LAT'], errors='coerce')
df['LON'] = pd.to_numeric(df['LON'], errors='coerce')

# remover linhas com coordenadas inválidas
df = df.dropna(subset=['LAT', 'LON'])

# filtragem espacial e temporal
# criar uma janela temporal de +/- 48 horas e uma janela espacial de 1 km

# parâmetros
time_window_hours = 48  # janela temporal para filtragem
distance_threshold_km = 1.0  # limite de distância espacial em quilômetros

# ordenar por data para proximidade temporal
df = df.sort_values(by='DATE OCC').reset_index(drop=True)

# criar o grafo
G = nx.Graph()

# passo 1: adicionar nós
for index, row in df.iterrows():
    crime_id = row['DR_NO']
    location = (row['LAT'], row['LON'])
    date_occ = row['DATE OCC']
    time_occ = row['TIME OCC']
    G.add_node(crime_id, location=location, date_occ=date_occ, time_occ=time_occ)

# passo 2: adicionar arestas usando janelas temporais e espaciais
# agrupar em blocos para reduzir o número de comparações
chunk_size = 10000  # ajuste de acordo com a memória disponível

for i in range(0, len(df), chunk_size):
    chunk = df.iloc[i:i + chunk_size]

    for index1, row1 in chunk.iterrows():
        crime1 = row1['DR_NO']
        location1 = (row1['LAT'], row1['LON'])
        date1 = row1['DATE OCC']

        # definir uma janela temporal de +/- 48 horas
        min_time = date1 - pd.Timedelta(hours=time_window_hours)
        max_time = date1 + pd.Timedelta(hours=time_window_hours)

        # filtrar crimes que ocorreram dentro da janela temporal
        time_filtered_df = df[(df['DATE OCC'] >= min_time) & (df['DATE OCC'] <= max_time)]

        for index2, row2 in time_filtered_df.iterrows():
            if crime1 == row2['DR_NO']:
                continue

            crime2 = row2['DR_NO']
            location2 = (row2['LAT'], row2['LON'])
            date2 = row2['DATE OCC']

            # calcular distância
            distance = calc_distance(location1, location2)

            # só adicionar a aresta se estiver dentro do limite de distância
            if distance < distance_threshold_km:
                time_diff = calc_time_diff(date1, date2)
                G.add_edge(crime1, crime2, weight=distance)

# salvar o grafo para análise futura
nx.write_gml(G, "crime_relationships_optimized.gml")
