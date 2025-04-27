import logging
from pathlib import Path
import pandas as pd

from .utils import round_5_value, round_100_value


def get_surface_temperature(temperature, solar_radiation):
    """
    Calculates the surface temperature based on temperature and solar radiation.

    Args:
        temperature: Temperature in Celsius degrees
        solar_radiation: Solar radiation

    Returns:
        float: Surface temperature value or None in case of error
    """
    logger = logging.getLogger(__name__)

    logger.debug(
        f"Calculating surface temperature with temperature={temperature}, solar_radiation={solar_radiation}")

    try:
        current_dir = Path(__file__).resolve().parent
        csv_path = current_dir / "tables" / "surface_temperature.csv"
        df = pd.read_csv(csv_path, delimiter=";", index_col=0)

        # Round input values
        rounded_temperature = round_5_value(temperature)
        rounded_solar_radiation = round_100_value(solar_radiation)
        logger.debug(
            f"Rounded values: temp={rounded_temperature}, solar={rounded_solar_radiation}")

        if rounded_temperature < 15:
            logger.debug(f"Temperature {rounded_temperature} < 15")
            rounded_temperature = 0
            logger.debug(f"Set to {rounded_temperature}")
        elif rounded_temperature > 120:
            logger.debug(f"Temperature {rounded_temperature} > 120")
            rounded_temperature = 999
            logger.debug(f"Set to {rounded_temperature}")
        else:
            logger.debug(f"Temperature in valid range: {rounded_temperature}")

        if rounded_solar_radiation < 100:
            logger.debug(f"Solar radiation {rounded_solar_radiation} < 100")
            rounded_solar_radiation = 0
            logger.debug(f"Set to {rounded_solar_radiation}")
        elif rounded_solar_radiation > 1300:
            logger.debug(f"Solar radiation {rounded_solar_radiation} > 1300")
            rounded_solar_radiation = 9999
            logger.debug(f"Set to {rounded_solar_radiation}")
        else:
            logger.debug(
                f"Solar radiation in valid range: {rounded_solar_radiation}")

        if str(rounded_solar_radiation) in df.columns and rounded_temperature in df.index:
            surface_temperature = df.at[rounded_temperature, str(
                rounded_solar_radiation)]
            logger.info(f"Surface temperature value found: {surface_temperature}")
            return surface_temperature
        else:
            logger.error(
                f"Error: value not found in the table for temperature={rounded_temperature}, radiation={rounded_solar_radiation}")
            return None
    except Exception as e:
        logger.exception(f"Error calculating surface temperature: {str(e)}")
        return None


def get_eqmc(surface_temperature, humidity):
    """
    Calculates the equilibrium moisture content based on surface temperature and humidity.
    
    Args:
        surface_temperature: Surface temperature in Celsius degrees
        humidity: Relative humidity percentage
        
    Returns:
        float: Equilibrium moisture content value or None in case of error
    """
    logger = logging.getLogger(__name__)
    
    logger.debug(f"Calculating equilibrium moisture with surface_temperature={surface_temperature}, humidity={humidity}")
    
    try:
        current_dir = Path(__file__).resolve().parent
        csv_path = current_dir / "tables" / "eqmc.csv"
        df = pd.read_csv(csv_path, delimiter=";", index_col=0)
        
        # Process humidity value
        if humidity <= 2.5:
            rounded_humidity = 2
            logger.debug(f"Humidity {humidity} <= 2.5, set to {rounded_humidity}")
        elif humidity >= 97.5:
            rounded_humidity = 99
            logger.debug(f"Humidity {humidity} >= 97.5, set to {rounded_humidity}")
        else:
            rounded_humidity = round_5_value(humidity)
            logger.debug(f"Humidity in valid range, rounded to {rounded_humidity}")
        
        # Process surface temperature
        rounded_surface_temperature = round_5_value(surface_temperature)
        logger.debug(f"Surface temperature rounded to {rounded_surface_temperature}")
        
        # Get value from table
        if rounded_surface_temperature in df.index and str(rounded_humidity) in df.columns:
            eqmc = df.at[rounded_surface_temperature, str(rounded_humidity)]
            logger.info(f"Equilibrium moisture content calculated: {eqmc}")
            return eqmc
        else:
            logger.error(f"Error: row or column not found in the dataframe. Temperature={rounded_surface_temperature}, humidity={rounded_humidity}")
            return None
    except Exception as e:
        logger.exception(f"Error calculating equilibrium moisture: {str(e)}")
        return None
