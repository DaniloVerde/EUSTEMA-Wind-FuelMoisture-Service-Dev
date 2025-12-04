import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.mask import mask
import os


def bbox_to_geojson(bounds):
    # bounds: left, bottom, right, top
    left, bottom, right, top = bounds
    return [{
        "type": "Polygon",
        "coordinates": [[
            [left, bottom],
            [left, top],
            [right, top],
            [right, bottom],
            [left, bottom]
        ]]
    }]


def expand_bounds(bounds, buffer_m):
    left, bottom, right, top = bounds
    return (
        left - buffer_m,
        bottom - buffer_m,
        right + buffer_m,
        top + buffer_m
    )


def create_wind_magnitude_direction(tiff_path, u_band, v_band, magnitude_output_path, direction_output_path, elevation_file_path, buffer_km=10):
    # Open the U and V component files
    with rasterio.open(tiff_path) as src:
        u_data = src.read(u_band)  # u banda 1
        v_data = src.read(v_band)  # v banda 2
        profile = src.profile
        profile.update(count=1)
        # profile.update(nodata=-9999)

        wind_crs = src.crs

    # Calculate wind speed (magnitude)
    wind_speed = np.sqrt(u_data**2 + v_data**2)

    # Calculate wind direction (in degrees, from 0 to 360)
    # Note: atan2 returns the angle in radians from the positive x-axis
    # to the point (v, u), with values in [-π, π]
    # Meteorologically, wind direction is the direction FROM WHICH the wind comes,
    # so we need to add 180 degrees and make sure it's between 0 and 360
    wind_direction = (np.degrees(np.arctan2(v_data, u_data)) + 180) % 360

    profile.update(dtype=rasterio.float32)
    profile.update(nodata=0)  # Imposta nodata a 0

    # Open elevation file and get CRS and geometry
    with rasterio.open(elevation_file_path) as elev_src:
        elev_crs = elev_src.crs
        elev_bounds = elev_src.bounds

        # Determina il buffer in unità CRS
        if elev_crs.is_geographic:
            # CRS geografico: buffer in gradi (1 grado ≈ 111 km)
            buffer_crs = buffer_km / 111.0
        else:
            # CRS proiettato: buffer in metri
            buffer_crs = buffer_km * 1000

        expanded_bounds = expand_bounds(elev_bounds, buffer_crs)
        elev_geom = bbox_to_geojson(expanded_bounds)
        elev_transform = elev_src.transform
        elev_shape = elev_src.shape
        elev_profile = elev_src.profile
        # Get geometry for mask (full extent polygon) without shapely
        elev_geom = bbox_to_geojson(elev_bounds)

    if wind_crs != elev_crs:
        print(f"Reprojecting wind rasters to match elevation CRS: {elev_crs}")

        # Reproject wind speed
        with rasterio.open(magnitude_output_path, 'w', **profile) as dst:
            wind_speed_out = wind_speed.astype(rasterio.float32)
            wind_speed_out[np.isnan(wind_speed_out)] = 0  # Sostituisci NaN con 0
            dst.write(wind_speed_out, 1)
        with rasterio.open(magnitude_output_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, elev_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': elev_crs,
                'transform': transform,
                'width': width,
                'height': height,
                'nodata': 0  # Assicura nodata=0
            })
            reprojected_speed_path = magnitude_output_path.replace('.tif', '_reprojected.tif')
            with rasterio.open(reprojected_speed_path, 'w', **kwargs) as dst:
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=elev_crs,
                    resampling=Resampling.bilinear
                )

        # Reproject wind direction
        with rasterio.open(direction_output_path, 'w', **profile) as dst:
            wind_direction_out = wind_direction.astype(rasterio.float32)
            wind_direction_out[np.isnan(wind_direction_out)] = 0  # Sostituisci NaN con 0
            dst.write(wind_direction_out, 1)
        with rasterio.open(direction_output_path) as src:
            transform, width, height = calculate_default_transform(
                src.crs, elev_crs, src.width, src.height, *src.bounds)
            kwargs = src.meta.copy()
            kwargs.update({
                'crs': elev_crs,
                'transform': transform,
                'width': width,
                'height': height,
                'nodata': 0  # Assicura nodata=0
            })
            reprojected_direction_path = direction_output_path.replace('.tif', '_reprojected.tif')
            with rasterio.open(reprojected_direction_path, 'w', **kwargs) as dst:
                reproject(
                    source=rasterio.band(src, 1),
                    destination=rasterio.band(dst, 1),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=elev_crs,
                    resampling=Resampling.bilinear
                )
        # After reprojection, crop to DTM extent
        with rasterio.open(reprojected_speed_path) as src:
            out_image, out_transform = mask(src, elev_geom, crop=True, nodata=0)
            out_image[out_image == src.nodata] = 0  # Sostituisci nodata con 0
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "nodata": 0
            })
            cropped_speed_path = reprojected_speed_path.replace('.tif', '_cropped.tif')
            with rasterio.open(cropped_speed_path, "w", **out_meta) as dest:
                dest.write(out_image)
        with rasterio.open(reprojected_direction_path) as src:
            out_image, out_transform = mask(src, elev_geom, crop=True, nodata=0)
            out_image[out_image == src.nodata] = 0  # Sostituisci nodata con 0
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "nodata": 0
            })
            cropped_direction_path = reprojected_direction_path.replace('.tif', '_cropped.tif')
            with rasterio.open(cropped_direction_path, "w", **out_meta) as dest:
                dest.write(out_image)
        print(f"Reprojected and cropped files created: {cropped_speed_path} and {cropped_direction_path}")
        return cropped_speed_path, cropped_direction_path
    else:
        print("Wind rasters CRS matches elevation CRS, no reprojection needed.")
        with rasterio.open(magnitude_output_path, 'w', **profile) as dst:
            wind_speed_out = wind_speed.astype(rasterio.float32)
            wind_speed_out[np.isnan(wind_speed_out)] = 0  # Sostituisci NaN con 0
            dst.write(wind_speed_out, 1)
        with rasterio.open(direction_output_path, 'w', **profile) as dst:
            wind_direction_out = wind_direction.astype(rasterio.float32)
            wind_direction_out[np.isnan(wind_direction_out)] = 0  # Sostituisci NaN con 0
            dst.write(wind_direction_out, 1)
        # After writing, crop to DTM extent
        with rasterio.open(magnitude_output_path) as src:
            out_image, out_transform = mask(src, elev_geom, crop=True, nodata=0)
            out_image[out_image == src.nodata] = 0  # Sostituisci nodata con 0
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "nodata": 0
            })
            cropped_speed_path = magnitude_output_path.replace('.tif', '_cropped.tif')
            with rasterio.open(cropped_speed_path, "w", **out_meta) as dest:
                dest.write(out_image)
        with rasterio.open(direction_output_path) as src:
            out_image, out_transform = mask(src, elev_geom, crop=True, nodata=0)
            out_image[out_image == src.nodata] = 0  # Sostituisci nodata con 0
            out_meta = src.meta.copy()
            out_meta.update({
                "driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform,
                "nodata": 0
            })
            cropped_direction_path = direction_output_path.replace('.tif', '_cropped.tif')
            with rasterio.open(cropped_direction_path, "w", **out_meta) as dest:
                dest.write(out_image)
        print(f"Files created and cropped: {cropped_speed_path} and {cropped_direction_path}")
        return cropped_speed_path, cropped_direction_path