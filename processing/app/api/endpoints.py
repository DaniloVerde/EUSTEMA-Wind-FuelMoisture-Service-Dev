from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi import Query
from fastapi.responses import FileResponse, PlainTextResponse
import logging
from datetime import datetime
from collections import deque
import os

from .models import (
    WindNinjaRequest,
    ProcessingResponse,
    FuelMoistureRequest,
    FuelMoistureResponse,
    FuelMoistureStationResult,
    WindNinjaForecastRequest,
)
from .tasks import process_windninja_request, process_windninja_forecast_request
from ..cleanup.cleanup_simulations_data import CleanupSimulationsData
from ..fuel_moisture.runner import process_fuel_moisture_data
from ..config import settings

# Get module logger
logger = logging.getLogger(__name__)

# Initialize cleanup utility
cleanup_util = CleanupSimulationsData(
    output_dir=settings.DATA_DIR, keep_recent=3)

router = APIRouter(tags=["Processing"])


@router.post("/process", status_code=status.HTTP_202_ACCEPTED, response_model=ProcessingResponse)
async def process_windninja(request: WindNinjaRequest, background_tasks: BackgroundTasks):
    """
    Start a WindNinja processing job.

    - **Request body**: JSON with meteorological stations data and configuration (station_list.json format)
    - **Returns**: 202 Accepted with processing details

    The processing will run in the background. The results will be uploaded to MinIO.
    A Kafka message will be published when processing is complete or if an error occurs.
    """
    try:
        # Log the request
        logger.info(
            f"Received processing request for model: {request.modelId} resourceProvider: {request.resource_provider}")

        # Convert Pydantic model to dict
        request_data = request.dict()

        # Add the task to the background queue
        background_tasks.add_task(
            process_windninja_request, request.modelId, request_data, request.resource_provider.value)

        # Return accepted response
        return ProcessingResponse(
            modelId=request.modelId,
            status="accepted",
            message="Processing started, you will be notified via Kafka when complete",
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error starting WindNinja processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start processing: {str(e)}"
        )
    finally:
        try:
            cleanup_util.remove_old_simulations()
        except Exception as cleanup_err:
            logger.error(f"Cleanup error: {cleanup_err}")


@router.post("/fuel-moisture", response_model=FuelMoistureResponse)
async def calculate_fuel_moisture(request: FuelMoistureRequest):
    """
    Calculate fuel moisture content for meteorological stations.

    - **Request body**: JSON with meteorological stations data in the same format as fuel_moisture_station_list.json
    - **Returns**: JSON with fuel moisture values calculated for each station

    The calculation is performed synchronously and the results are returned immediately.
    """
    try:
        # Log the request
        logger.info(
            f"Received fuel moisture calculation request for model: {request.modelId}")

        # Convert Pydantic model to dict for processing
        request_data = request.dict()

        # Process the fuel moisture data
        fuel_moisture_results = process_fuel_moisture_data(request_data)

        # Create response with original data + calculated moisture values
        result_stations = []
        for station in request.meteorological_stations:
            # Create a copy of the station with calculated moisture
            station_result = FuelMoistureStationResult(
                station_name=station.station_name,
                lat=station.lat,
                lon=station.lon,
                observations=station.observations,
                fuel_moisture=fuel_moisture_results.get(station.station_name)
            )
            result_stations.append(station_result)

        # Return the response
        return FuelMoistureResponse(
            modelId=request.modelId,
            meteorological_stations=result_stations
        )

    except Exception as e:
        logger.error(f"Error calculating fuel moisture: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate fuel moisture: {str(e)}"
        )
    finally:
        try:
            cleanup_util.remove_old_simulations()
        except Exception as cleanup_err:
            logger.error(f"Cleanup error: {cleanup_err}")


@router.post("/forecast", status_code=status.HTTP_202_ACCEPTED, response_model=ProcessingResponse)
async def process_windninja_forecast(request: WindNinjaForecastRequest, background_tasks: BackgroundTasks):
    """
    Start a WindNinja forecast processing job.

    - **Request body**: JSON with forecast data and configuration
    - **Returns**: 202 Accepted with processing details

    The processing will run in the background. The results will be uploaded to MinIO.
    A Kafka message will be published when processing is complete or if an error occurs.
    """
    try:
        # Log the request
        logger.info(
            f"Received processing request for model: {request.modelId} resourceProvider: {request.resource_provider}")

        # Convert Pydantic model to dict
        request_data = request.dict()

        # Add the task to the background queue
        background_tasks.add_task(
            process_windninja_forecast_request, request.modelId, request_data, request.resource_provider.value)

        # Return accepted response
        return ProcessingResponse(
            modelId=request.modelId,
            status="accepted",
            message="Processing started, you will be notified via Kafka when complete",
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error starting WindNinja processing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start processing: {str(e)}"
        )
    finally:
        try:
            cleanup_util.remove_old_simulations()
        except Exception as cleanup_err:
            logger.error(f"Cleanup error: {cleanup_err}")


@router.get("/logs/windninja", tags=["Logs"])
async def windninja_log(
    download: bool = Query(False, description="If true, download the full windninja.log file"),
    lines: int = Query(
        default=settings.LOG_TAIL_DEFAULT_LINES,
        ge=1,
        description="Number of last lines to return when download=false",
    ),
):
    """Return last N lines of windninja.log (default from .env) or download the full file."""

    log_file_path = settings.LOG_FILE

    if not log_file_path or not os.path.exists(log_file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Log file not found: {log_file_path}",
        )

    if download:
        return FileResponse(
            path=log_file_path,
            media_type="text/plain",
            filename=os.path.basename(log_file_path) or "windninja.log",
        )

    try:
        with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
            last_lines = deque(f, maxlen=lines)
        return PlainTextResponse("".join(last_lines), media_type="text/plain")
    except Exception as e:
        logger.error(f"Error reading log file {log_file_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read log file",
        )
