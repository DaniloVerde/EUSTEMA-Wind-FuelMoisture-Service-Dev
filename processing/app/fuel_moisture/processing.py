import logging
from pathlib import Path
import pandas as pd

from .utils import (
    round_5_value,
    round_100_value,
    round_001_value,
    parse_label
)


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
            logger.info(
                f"Surface temperature value found: {surface_temperature}")
            return surface_temperature
        else:
            logger.error(
                f"Error: value not found in the table for temperature={rounded_temperature}, radiation={rounded_solar_radiation}")
            return None
    except Exception as e:
        logger.exception(f"Error calculating surface temperature: {str(e)}")
        return None


def get_equilibrium_moisture_content(surface_temperature, humidity):
    """
    Calculates the equilibrium moisture content based on surface temperature and humidity.

    Args:
        surface_temperature: Surface temperature in Celsius degrees
        humidity: Relative humidity percentage

    Returns:
        float: Equilibrium moisture content value or None in case of error
    """
    logger = logging.getLogger(__name__)

    logger.debug(
        f"Calculating equilibrium moisture with surface_temperature={surface_temperature}, humidity={humidity}")

    try:
        current_dir = Path(__file__).resolve().parent
        csv_path = current_dir / "tables" / "eqmc.csv"
        df = pd.read_csv(csv_path, delimiter=";", index_col=0)

        # Process humidity value
        if humidity <= 2.5:
            rounded_humidity = 2
            logger.debug(
                f"Humidity {humidity} <= 2.5, set to {rounded_humidity}")
        elif humidity >= 97.5:
            rounded_humidity = 99
            logger.debug(
                f"Humidity {humidity} >= 97.5, set to {rounded_humidity}")
        else:
            rounded_humidity = round_5_value(humidity)
            logger.debug(
                f"Humidity in valid range, rounded to {rounded_humidity}")

        # Process surface temperature
        if surface_temperature < 10:
            rounded_surface_temperature = 10
            logger.debug(
                f"Surface temperature {surface_temperature} < 10, set to {rounded_surface_temperature}")
        elif surface_temperature > 125:
            rounded_surface_temperature = 125
            logger.debug(
                f"Surface temperature {surface_temperature} > 125, set to {rounded_surface_temperature}")
        else:
            rounded_surface_temperature = round_5_value(surface_temperature)
            logger.debug(
                f"Surface temperature rounded to {rounded_surface_temperature}")

        # Get value from table
        if rounded_surface_temperature in df.index and str(rounded_humidity) in df.columns:
            eqmc = df.at[rounded_surface_temperature, str(rounded_humidity)]
            logger.info(f"Equilibrium moisture content calculated: {eqmc}")
            return eqmc
        else:
            logger.error(
                f"Error: row or column not found in the dataframe. Temperature={rounded_surface_temperature}, humidity={rounded_humidity}")
            return None
    except Exception as e:
        logger.exception(f"Error calculating equilibrium moisture: {str(e)}")
        return None


def get_rainfall_moisture_factor(precipitation):
    """
    Calculates the rainfall moisture factor based on hourly precipitation.

    Args:
        precipitation: Hourly precipitation value

    Returns:
        float: Rainfall moisture factor value or None in case of error
    """
    logger = logging.getLogger(__name__)

    logger.debug(
        f"Calculating rainfall moisture factor with precipitation={precipitation}")

    try:
        if precipitation <= 0:
            logger.debug(f"Precipitation {precipitation} <= 0, returning 0")
            return 0

        rounded_precipitation = round_001_value(precipitation)
        logger.debug(f"Precipitation rounded to {rounded_precipitation}")

        if rounded_precipitation > 0.33:
            logger.debug(
                f"Precipitation {rounded_precipitation} > 0.33, returning 31")
            return 31

        current_dir = Path(__file__).resolve().parent
        csv_path = current_dir / "tables" / "rainfall_moisture_factor.csv"
        df = pd.read_csv(csv_path, delimiter=";", index_col=0)

        if float(rounded_precipitation) in df.index:
            rmf = df.loc[float(rounded_precipitation), "rmf"]
            logger.info(f"Rainfall moisture factor calculated: {rmf}")
            return rmf
        else:
            logger.error(
                f"Error: value not found in the table for precipitation={rounded_precipitation}")
            return None
    except Exception as e:
        logger.exception(
            f"Error calculating rainfall moisture factor: {str(e)}")
        return None


def get_evaporation_correction_factor(surface_temperature, previous_fuel_moisture):
    """
    Calculates the evaporation correction factor based on surface temperature and previous fuel moisture.

    Args:
        surface_temperature: Surface temperature in Celsius degrees
        previous_fuel_moisture: Previous fuel moisture value

    Returns:
        float: Evaporation correction factor value or None in case of error
    """
    logger = logging.getLogger(__name__)

    logger.debug(
        f"Calculating evaporation correction factor with surface_temperature={surface_temperature}, previous_fuel_moisture={previous_fuel_moisture}")

    try:
        if previous_fuel_moisture <= 30:
            logger.debug(
                f"Previous fuel moisture {previous_fuel_moisture} <= 30, returning 0")
            return 0

        rounded_surface_temperature = round_5_value(surface_temperature)
        logger.debug(
            f"Surface temperature rounded to {rounded_surface_temperature}")

        if rounded_surface_temperature < 30:
            logger.debug(
                f"Surface temperature {rounded_surface_temperature} < 30, returning -2")
            return -2

        if rounded_surface_temperature > 145:
            logger.debug(
                f"Surface temperature {rounded_surface_temperature} > 145, returning -9")
            return -9

        current_dir = Path(__file__).resolve().parent
        csv_path = current_dir / "tables" / "ecf.csv"
        df = pd.read_csv(csv_path, delimiter=";", index_col=0)

        if rounded_surface_temperature in df.index:
            ecf = df.loc[rounded_surface_temperature, "ecf"]
            logger.info(f"Evaporation correction factor calculated: {ecf}")
            return ecf
        else:
            logger.error(
                f"Error: value not found in the table for surface temperature={rounded_surface_temperature}")
            return None
    except Exception as e:
        logger.exception(
            f"Error calculating evaporation correction factor: {str(e)}")
        return None


def get_moisture_correction_factor(surface_temperature, humidity, eqmc, previous_fuel_moisture, precipitation):
    """
    Calculates the moisture correction factor based on multiple inputs.
    
    Args:
        surface_temperature: Surface temperature in Celsius degrees
        humidity: Relative humidity percentage
        eqmc: Equilibrium moisture content value
        previous_fuel_moisture: Previous fuel moisture value
        precipitation: Precipitation value
        
    Returns:
        float: Moisture correction factor value or None in case of error
    """
    logger = logging.getLogger(__name__)
    
    logger.debug(f"Calculating moisture correction factor with surface_temperature={surface_temperature}, humidity={humidity}, eqmc={eqmc}, previous_fuel_moisture={previous_fuel_moisture}, precipitation={precipitation}")
    
    try:
        tables = {}
        current_dir = Path(__file__).resolve().parent
        
        for i in range(1, 31):
            tables[i] = current_dir / "tables" / "desorption" / f"DES_{i}P.csv"
            tables[-i] = current_dir / "tables" / "absorption" / f"ABS_{i}P.csv"
        
        if precipitation <= 0 and previous_fuel_moisture < 30:
            diff = previous_fuel_moisture - eqmc
            if diff >= 0:
                abs_des_value = previous_fuel_moisture
                logger.debug(f"Using desorption value: {abs_des_value}")
            else:
                abs_des_value = -previous_fuel_moisture
                logger.debug(f"Using absorption value: {abs_des_value}")
            
            if humidity < 0 or humidity > 100:
                logger.error(f"Error: The humidity value {humidity} is not valid")
                return None
            
            if abs_des_value not in tables:
                logger.error(f"Error: No table found for value {abs_des_value}")
                return None
                
            df = pd.read_csv(tables[abs_des_value], delimiter=';')
            
            df.iloc[:, 0] = df.iloc[:, 0].apply(parse_label)
            
            row_index = df.iloc[:, 0].apply(lambda x: x[0] <= surface_temperature <= x[1])
            
            if not row_index.any():
                logger.error(f"Error: No match found for temperature value {surface_temperature}")
                return None
            
            col_names = df.columns[1:]
            col_ranges = [parse_label(col) for col in col_names]
            
            col_index = [y[0] <= humidity <= y[1] for y in col_ranges]
            
            if not any(col_index):
                logger.error(f"Error: No match found for humidity value {humidity}")
                return None
            
            # Find the value corresponding to the temperature and humidity
            row = df[row_index].iloc[:, 1:].values[0]
            value = row[col_index.index(True)]
            logger.info(f"Moisture correction factor calculated: {value}")
            return value

        else:
            logger.debug("Precipitation > 0 or previous_fuel_moisture >= 30, returning 0")
            return 0
    except Exception as e:
        logger.exception(f"Error calculating moisture correction factor: {str(e)}")
        return None
