import numpy as np
import rasterio

def create_wind_magnitude_direction(u_tiff_path, v_tiff_path, magnitude_output_path, direction_output_path):
    # Apri i file delle componenti U e V
    with rasterio.open(u_tiff_path) as u_src:
        u_data = u_src.read(1)
        profile = u_src.profile
    
    with rasterio.open(v_tiff_path) as v_src:
        v_data = v_src.read(1)
        
    # Calcola la velocità (magnitude) del vento
    wind_speed = np.sqrt(u_data**2 + v_data**2)
    
    # Calcola la direzione del vento (in gradi, da 0 a 360)
    # Nota: atan2 restituisce l'angolo in radianti dalla direzione positiva dell'asse x
    # alla direzione del punto (v, u), con valori in [-π, π]
    # Meteorologicamente, la direzione del vento è la direzione DA CUI il vento proviene,
    # quindi dobbiamo aggiungere 180 gradi e assicurarci che sia tra 0 e 360
    wind_direction = (np.degrees(np.arctan2(v_data, u_data)) + 180) % 360
    
    # Crea il file di output per la velocità
    profile.update(dtype=rasterio.float32)
    with rasterio.open(magnitude_output_path, 'w', **profile) as dst:
        dst.write(wind_speed.astype(rasterio.float32), 1)
    
    # Crea il file di output per la direzione
    with rasterio.open(direction_output_path, 'w', **profile) as dst:
        dst.write(wind_direction.astype(rasterio.float32), 1)
    
    print(f"File creati: {magnitude_output_path} e {direction_output_path}")
