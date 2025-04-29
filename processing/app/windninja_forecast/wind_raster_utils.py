import numpy as np
import rasterio

def create_wind_magnitude_direction(u_tiff_path, v_tiff_path, magnitude_output_path, direction_output_path):
    # Open the U and V component files
    with rasterio.open(u_tiff_path) as u_src:
        u_data = u_src.read(1)
        profile = u_src.profile
    
    with rasterio.open(v_tiff_path) as v_src:
        v_data = v_src.read(1)
        
    # Calculate wind speed (magnitude)
    wind_speed = np.sqrt(u_data**2 + v_data**2)
    
    # Calculate wind direction (in degrees, from 0 to 360)
    # Note: atan2 returns the angle in radians from the positive x-axis
    # to the point (v, u), with values in [-π, π]
    # Meteorologically, wind direction is the direction FROM WHICH the wind comes,
    # so we need to add 180 degrees and make sure it's between 0 and 360
    wind_direction = (np.degrees(np.arctan2(v_data, u_data)) + 180) % 360
    
    # Create output file for speed
    profile.update(dtype=rasterio.float32)
    with rasterio.open(magnitude_output_path, 'w', **profile) as dst:
        dst.write(wind_speed.astype(rasterio.float32), 1)
    
    # Create output file for direction
    with rasterio.open(direction_output_path, 'w', **profile) as dst:
        dst.write(wind_direction.astype(rasterio.float32), 1)
    
    print(f"Files created: {magnitude_output_path} and {direction_output_path}")
