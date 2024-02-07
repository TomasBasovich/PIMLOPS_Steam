#Cargamos las bibliotecas que utilizaremos
from fastapi import FastAPI
import pandas as pd
from typing import List, Dict, Any
import pyarrow
import json

#Cargamos el archivo parquet en un dataframe
df_steam_games = pd.read_parquet('Data/Steam_Games.parquet')
#Seleccionamos las columnas que queremos utilizar del dataframe y las cargamos en un nuevo dataframe
steam_games = df_steam_games[["Developer", "Is Free To Play", "Release Date"]]

app=FastAPI()

#Definimos la ruta de API GET
@app.get("/Developer")
#Definimos una funcion llamada "Developer" que toma un argumento de tipo string
def Developer(Developer:str):
    #Filtramos el dataframe "steam_games" para obtener solo las filas donde el valor de la columna "Developer" es igual al argumento de la función.
    Developer = steam_games[steam_games['Developer']==Developer]
    #Sumamos todos los valores de la columna "Is Free To Play" en el dataframe filtrado. Esto nos da el total de juegos gratuitos del desarrollador.
    juegos_gratuitos = Developer["Is Free To Play"].sum()
    #Obtenemos el numero total de juegos del desarrollador contando el numero de filas en el dataframe filtrado
    total_juegos = len(Developer)
    #Calculamos el porcentaje de juegos gratuitos dividiendo el numero de juegos gratuitos entre el numero total de juegos y multiplicando por 100
    porcentaje_de_gratuitos = (juegos_gratuitos/total_juegos) * 100
    
    #Agrupamos el dataframe filtrado por la columna "Release Date" y contamos el numero de juegos por año
    juegos_por_año = Developer.groupby(Developer["Release Date"]).size()
    #Filtramos el dataframe para obtener solo los juegos gratuitos y luego agrupamos por la columna "Release Date" y contamos el numero de juegos gratuitos por año.
    juegos_gratuitos_por_año = Developer[Developer["Is Free To Play"]== True].groupby(Developer['Release Date']).size()
    #Reindexamos el dataframe de juegos gratuitos por año para que tenga el mismo indice que el dataframe de juegos por año, llenando los valores faltantes con 0.
    juegos_gratuitos_por_año = juegos_gratuitos_por_año.reindex(juegos_por_año.index, fill_value=0)
    #Calculamos el porcentaje de juegos gratuitos por año dividiendo el numero de juegos gratuitos por año entre el numero total de juegos por año y multiplicando por 100
    porcentaje_de_juegos_gratis_anual = (juegos_gratuitos_por_año/juegos_por_año) * 100
    
    #La función devuelve un diccionario con el porcentaje total de juegos gratuitos y el porcentaje de juegos gratuitos por año, ambos redondeados a dos decimales
    return{"Porcentaje Gratuito": (porcentaje_de_gratuitos).round(2),
           "Porcentaje Gratuito Anual" : (porcentaje_de_juegos_gratis_anual).round(2)}
    
    



#Definimos la ruta de API GET
@app.get("/Userdata")

#Definimos una función llamada "Userdata" que toma un argumento de tipo string
def User_Data(user_id: str):
    #Se inicializan 4 variables en 0 para almacenar datos
    cantidad = 0
    recommend_count = 0
    total_reviews = 0
    item_id = set()
    
    #Cargamos los dos conjuntos de datos desde archivos parquet
    user_reviews = pd.read_parquet('Data/User_Reviews.parquet')
    steam_games = pd.read_parquet('Data/Steam_Games.parquet')
    
    #Filtramos el dataframe "user_reviews" para obtener solo las filas donde el valor de la columna "User ID" es igual al argumento de la funcion
    user_reviews1 = user_reviews[user_reviews['User ID']==user_id]
    
    #Sumamos todos los valores de la columna "Price" en el dataframe resultante de la fusión de "user_reviews1" y "steam_games" en la columna "Item ID"
    #Esto nos da la cantidad de dinero gastado por el usuario
    cantidad += user_reviews1.merge(steam_games[['ID','Price']], left_on='Item ID', right_on='ID', how='inner')['Price'].sum()
    #Sumamos todos los valores de la columna "Recommend" en el dataframe "user_reviews1". Esto nos da el total de reseñas recomendadas por el usuario.
    recommend_count += user_reviews1['Recommend'].sum()
    #Contamos el numero total de reseñas del usuario contando el numero de filas en el dataframe "user_reviews1"
    total_reviews += len(user_reviews1)
    #Actualizamos el conjunto "item_id" con los identificadores únicos de los items que el usario ha reseñado
    item_id.update(user_reviews1['Item ID'].unique())
    
    #Si el total de reseñas es mayor que 0, calculamos el porcentaje de reseñas recomendadas. Si no hay reseñas, el porcentaje se establece en 0.
    if total_reviews > 0:
        porcentaje = (recommend_count/total_reviews) * 100
    else:
        porcentaje = 0
    
    #Contamos la cantidad de items únicos que el usario ha reseñado
    cantidad_de_items = len(item_id)
    
    #Creamos un diccionario que contiene la cantidad de dinero gastado, el porcentaje de reseñas recomendadas y el número de items únicos que el usuario ha reseñado
    user_data ={
        "Money Spent": cantidad,
        "Recommend Percentage": porcentaje,
        "Quantity of Items": cantidad_de_items
    }
    
    #La función devuelve el diccionario "user_data"
    return user_data



#Definimos la ruta de API GET
@app.get("/Best Developer of the Year")

def Best_developer_year(año: int):
    # Cargar los dataframes
    user_reviews = pd.read_parquet('Data/User_Reviews.parquet')
    steam_games = pd.read_parquet('Data/Steam_Games.parquet')

    # Fusionar los dataframes en el Item ID
    merged_df = pd.merge(user_reviews, steam_games, left_on='Item ID', right_on='ID')

    # Filtrar por año y reseñas positivas
    filtered_df = merged_df[(merged_df['Release Date'] == año) & (merged_df['Recommend'] == True)]

    # Contar las reseñas positivas por desarrollador
    developer_counts = filtered_df['Developer'].value_counts()

    # Obtener el top 3 de desarrolladores
    top_developers = developer_counts.nlargest(3).index.tolist()

    # Crear el diccionario de retorno
    if len(top_developers) >= 3:
        resultado = [{"Puesto 1": top_developers[0]}, {"Puesto 2": top_developers[1]}, {"Puesto 3": top_developers[2]}]
    elif len(top_developers) == 2:
        resultado = [{"Puesto 1": top_developers[0]}, {"Puesto 2": top_developers[1]}]
    elif len(top_developers) == 1:
        resultado = [{"Puesto 1": top_developers[0]}]
    else:
        resultado = []

    return resultado

@app.get("/Usuario por género")
def User_For_Genre(genre: str):
    
    #Cargar el archivo de Items
    user_items = pd.read_parquet('Data/User_Items.parquet')
    steam_games = pd.read_parquet('Data/Steam_Games.parquet')

    # Fusionar los DataFrames en el "ID del elemento"
    merged_data = pd.merge(steam_games, user_items, left_on='ID', right_on='Item ID')

    # Filtrar los datos por el género proporcionado
    genre_data = merged_data[merged_data['Genres'] == genre]

    # Encontrar el usuario con más tiempo de juego
    max_user = genre_data.groupby('User ID')['Play Time Forever'].sum().idxmax()

    # Agrupar por año de lanzamiento y calcular el tiempo total de juego para cada año
    year_playtime = genre_data.groupby('Release Date')['Play Time Forever'].sum().reset_index()

    # Crear la lista de horas jugadas por año
    hours_played: List[dict] = [{"Año": row['Release Date'], "Horas": row['Play Time Forever']} for _, row in year_playtime.iterrows()]

    # Crear el diccionario de retorno
    result = {"Usuario con más horas jugadas para Género X": max_user, "Horas jugadas": hours_played}

    return result

@app.get("/UserRecommend")
def User_Recommend(año: int):
    ruta = "Data/userRecommend.parquet"

    df_user_recommend = pd.read_parquet(ruta)
    games_year = df_user_recommend[df_user_recommend["Release Date"]== año]
    recommends = games_year[(games_year["Recommend"]== True) & (games_year["Sentiment Analysis"]== 2)]
    
    # Agrupamos por juego recomendados
    Games = recommends["App Name"].value_counts().reset_index()
    Games.columns = ["Games", "Recommend Count"]
    
    # Ordenamos y obtenemos el top3
    top_games = Games.nlargest(3, "Recommend Count")
    
    resultado = [{"Puesto {}: {}".format(i + 1, row['Games']): row['Recommend Count']} for i, row in top_games.iterrows()]
    
    return resultado

@app.get("/Sentiment Analysis")
def sentiment_analysis(desarrolladora: str):
    ruta_items = "Data/sentiment_analysis_items.parquet"
    ruta_sentiment = "Data/sentiment_analysis.parquet"

    # Abrimos los dataframe

    df_items = pd.read_parquet(ruta_items)
    df_combined = pd.read_parquet(ruta_sentiment)
    # filtra juego para desarrollador dado
    games_developer = df_combined[df_combined["Developer"]== desarrolladora]
    # obtiene el id de los juegos seleccionados
    game_id = games_developer["ID"]
    
    items_developer = df_items[df_items["Item ID"].isin(game_id)]
    
    # Obtenemos el id d los usuarios
    user_id = items_developer["User ID"]
    
    reviews_developer = df_combined[df_combined["User ID"].isin(user_id)]
    
    reviews_positive = reviews_developer[reviews_developer["Recommend"] == True].shape[0]
    reviews_negative = reviews_developer[reviews_developer["Recommend"]== False].shape[0]
    
    return {desarrolladora: {"Positive":reviews_positive, "Negative":reviews_negative}}