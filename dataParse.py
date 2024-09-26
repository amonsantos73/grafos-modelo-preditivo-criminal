import pandas as pd

csv_file_path = 'Crime_Data_from_2020_to_Present.csv'

df = pd.read_csv(csv_file_path)

# filtro linhas com codigos 210, 220, 122, 121 ou 110 = codigos de robbery, murder, rape e suas variacoes
filtered_df = df[df['Crm Cd'].isin([210, 220, 122, 121, 110])]

output_csv_file = 'filtered_crime_data.csv'

filtered_df.to_csv(output_csv_file, index=False)

print(f"Novo arquivo CSV salvo em: {output_csv_file}")
