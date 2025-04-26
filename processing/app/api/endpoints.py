from fastapi import APIRouter, BackgroundTasks, HTTPException, status
import asyncio
import logging
from datetime import datetime

from .models import WindNinjaRequest, ProcessingResponse
from .tasks import process_windninja_request

# Get module logger
logger = logging.getLogger(__name__)

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
        logger.info(f"Received processing request for model: {request.modelId}")
        
        # Convert Pydantic model to dict
        request_data = request.dict()
        
        # Add the task to the background queue
        background_tasks.add_task(process_windninja_request, request.modelId, request_data)
        
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