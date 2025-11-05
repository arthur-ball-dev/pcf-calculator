"""
Async Task Service
TASK-BE-004: Background task processing for long-running calculations

This service provides:
- Async task submission (non-blocking)
- Task status tracking (pending → running → completed/failed)
- Background execution using asyncio
- Database persistence of task state

Usage:
    service = TaskService(db_session)
    task_id = await service.submit_calculation_task(product_id, calculation_type)
    status = await service.get_task_status(task_id)
"""

import asyncio
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from backend.models import Product, PCFCalculation, generate_uuid

# Configure logging
logger = logging.getLogger(__name__)


class TaskService:
    """
    Service for managing async background tasks

    Handles:
    - Task submission and ID generation
    - Status tracking through task lifecycle
    - Error handling and logging
    - Database persistence
    """

    def __init__(self, db: Session):
        """
        Initialize TaskService with database session

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self._background_tasks = set()  # Track running tasks for cleanup
        self._failed_tasks = {}  # In-memory store for failed tasks (invalid product IDs)

    async def submit_calculation_task(
        self,
        product_id: str,
        calculation_type: str = "cradle_to_gate",
        **kwargs
    ) -> str:
        """
        Submit a PCF calculation task for background processing

        This method returns immediately with a task_id, allowing the client
        to poll for results using get_task_status().

        Args:
            product_id: ID of product to calculate PCF for
            calculation_type: Type of calculation (default: "cradle_to_gate")
            **kwargs: Additional calculation parameters

        Returns:
            task_id: Unique identifier for tracking task status

        Example:
            task_id = await service.submit_calculation_task("product-001")
            # Returns immediately, calculation runs in background
        """
        # Generate unique task ID
        task_id = generate_uuid()

        # Verify product exists before creating calculation record
        # This prevents foreign key constraint errors
        product = self.db.query(Product).filter_by(id=product_id).first()

        if not product:
            # Store failed task info in memory (can't store in DB without valid FK)
            self._failed_tasks[task_id] = {
                "calculation_id": task_id,
                "status": "failed",
                "product_id": None,
                "error_message": f"Product {product_id} not found",
                "created_at": datetime.now(UTC).isoformat()
            }
            logger.warning(f"Task {task_id} failed: product {product_id} not found")
            return task_id

        # Create initial calculation record in database with status='pending'
        try:
            calculation = PCFCalculation(
                id=task_id,
                product_id=product_id,
                calculation_type=calculation_type,
                status="pending",
                total_co2e_kg=0.0,  # Placeholder until calculation completes
                created_at=datetime.now(UTC)
            )

            self.db.add(calculation)
            self.db.commit()

            logger.info(f"Task {task_id} created for product {product_id}")

        except (SQLAlchemyError, IntegrityError) as e:
            self.db.rollback()
            logger.error(f"Failed to create task {task_id}: {e}")

            # Store in memory as failed
            self._failed_tasks[task_id] = {
                "calculation_id": task_id,
                "status": "failed",
                "product_id": product_id,
                "error_message": f"Database error: {str(e)}",
                "created_at": datetime.now(UTC).isoformat()
            }
            return task_id

        # Start background task (non-blocking)
        task = asyncio.create_task(
            self._execute_calculation_task(task_id, product_id, calculation_type, **kwargs)
        )

        # Track task for cleanup
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        return task_id

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a calculation task

        Args:
            task_id: Task identifier returned from submit_calculation_task

        Returns:
            Status dict with fields:
                - calculation_id: Task ID
                - status: Current status (pending, running, completed, failed)
                - product_id: Product being calculated (None if product not found)
                - total_co2e_kg: Result (when completed)
                - error_message: Error details (when failed)
                - created_at: Task creation time
                - calculation_time_ms: Execution time (when completed)

            Returns None if task doesn't exist

        Example:
            status = await service.get_task_status(task_id)
            if status["status"] == "completed":
                print(f"Result: {status['total_co2e_kg']} kg CO2e")
        """
        # Check in-memory failed tasks first
        if task_id in self._failed_tasks:
            return self._failed_tasks[task_id]

        # Check database
        try:
            calculation = self.db.query(PCFCalculation).filter_by(id=task_id).first()

            if not calculation:
                return None

            # Build status response
            status_dict = {
                "calculation_id": calculation.id,
                "status": calculation.status,
                "product_id": calculation.product_id,
                "created_at": calculation.created_at.isoformat() if calculation.created_at else None
            }

            # Add result fields if completed
            if calculation.status == "completed":
                status_dict.update({
                    "total_co2e_kg": float(calculation.total_co2e_kg) if calculation.total_co2e_kg else 0.0,
                    "calculation_time_ms": calculation.calculation_time_ms,
                    "materials_co2e": float(calculation.materials_co2e) if calculation.materials_co2e else None,
                    "energy_co2e": float(calculation.energy_co2e) if calculation.energy_co2e else None,
                    "transport_co2e": float(calculation.transport_co2e) if calculation.transport_co2e else None,
                })

            # Add error details if failed
            if calculation.status == "failed":
                # Error message stored in metadata or input_data JSON field
                error_msg = None
                if calculation.calculation_metadata:
                    error_msg = calculation.calculation_metadata.get("error_message")
                if not error_msg and calculation.input_data:
                    error_msg = calculation.input_data.get("error_message")

                status_dict["error_message"] = error_msg or "Calculation failed"

            return status_dict

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving status for task {task_id}: {e}")
            return None

    async def _execute_calculation_task(
        self,
        task_id: str,
        product_id: str,
        calculation_type: str,
        **kwargs
    ):
        """
        Internal method: Execute calculation in background

        This method runs asynchronously and updates the database with progress.

        Lifecycle:
        1. Update status to 'running'
        2. Verify product exists
        3. Perform calculation (placeholder for now)
        4. Update status to 'completed' with results
        5. Handle errors and update status to 'failed'

        Args:
            task_id: Task identifier
            product_id: Product to calculate
            calculation_type: Calculation type
            **kwargs: Additional parameters
        """
        start_time = time.time()

        try:
            # Update status to 'running'
            await self._update_task_status(task_id, "running")

            logger.info(f"Task {task_id}: Starting calculation for product {product_id}")

            # Verify product exists
            product = self.db.query(Product).filter_by(id=product_id).first()

            if not product:
                raise ValueError(f"Product {product_id} not found")

            # Simulate calculation (placeholder)
            # In TASK-API-002, this will call the actual Brightway2 calculator
            await asyncio.sleep(0.01)  # Simulate brief calculation

            # For now, return a placeholder result
            # TODO: Replace with actual calculation in TASK-API-002
            result = {
                "total_co2e_kg": 0.0,
                "materials_co2e": 0.0,
                "energy_co2e": 0.0,
                "transport_co2e": 0.0,
            }

            # Calculate execution time
            elapsed_ms = int((time.time() - start_time) * 1000)

            # Update database with completed results
            calculation = self.db.query(PCFCalculation).filter_by(id=task_id).first()

            if calculation:
                calculation.status = "completed"
                calculation.total_co2e_kg = result["total_co2e_kg"]
                calculation.materials_co2e = result["materials_co2e"]
                calculation.energy_co2e = result["energy_co2e"]
                calculation.transport_co2e = result["transport_co2e"]
                calculation.calculation_time_ms = elapsed_ms
                calculation.calculation_method = "MVP_Placeholder"

                self.db.commit()

                logger.info(f"Task {task_id}: Completed in {elapsed_ms}ms")

        except ValueError as e:
            # Product not found or validation error
            logger.error(f"Task {task_id}: Validation error - {e}")
            await self._update_task_status(
                task_id,
                "failed",
                error_message=str(e)
            )

        except Exception as e:
            # Unexpected error
            logger.error(f"Task {task_id}: Unexpected error - {e}", exc_info=True)
            await self._update_task_status(
                task_id,
                "failed",
                error_message=f"Calculation failed: {str(e)}"
            )

    async def _update_task_status(
        self,
        task_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Internal method: Update task status in database

        Args:
            task_id: Task identifier
            status: New status (pending, running, completed, failed)
            error_message: Error message for failed tasks
        """
        try:
            calculation = self.db.query(PCFCalculation).filter_by(id=task_id).first()

            if calculation:
                calculation.status = status

                # Store error message in metadata JSON field
                if error_message:
                    if not calculation.calculation_metadata:
                        calculation.calculation_metadata = {}
                    calculation.calculation_metadata["error_message"] = error_message

                self.db.commit()

                logger.debug(f"Task {task_id}: Status updated to '{status}'")

        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Failed to update status for task {task_id}: {e}")

    async def cancel_all_tasks(self):
        """
        Cancel all running background tasks (for graceful shutdown)

        This should be called when the application shuts down to ensure
        all background tasks are properly cancelled.
        """
        logger.info(f"Cancelling {len(self._background_tasks)} background tasks")

        for task in self._background_tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete cancellation
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        self._background_tasks.clear()

        logger.info("All background tasks cancelled")


# Module-level convenience functions for FastAPI integration

async def submit_task(
    db: Session,
    product_id: str,
    calculation_type: str = "cradle_to_gate",
    **kwargs
) -> str:
    """
    Convenience function for submitting tasks from FastAPI endpoints

    Args:
        db: Database session (from Depends(get_db))
        product_id: Product to calculate
        calculation_type: Calculation type
        **kwargs: Additional parameters

    Returns:
        task_id: Task identifier

    Example:
        @app.post("/calculate")
        async def calculate(product_id: str, db: Session = Depends(get_db)):
            task_id = await submit_task(db, product_id)
            return {"calculation_id": task_id, "status": "processing"}
    """
    service = TaskService(db)
    return await service.submit_calculation_task(product_id, calculation_type, **kwargs)


async def get_status(db: Session, task_id: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function for checking task status from FastAPI endpoints

    Args:
        db: Database session (from Depends(get_db))
        task_id: Task identifier

    Returns:
        Status dict or None if not found

    Example:
        @app.get("/calculations/{task_id}")
        async def get_calculation(task_id: str, db: Session = Depends(get_db)):
            status = await get_status(db, task_id)
            if not status:
                raise HTTPException(404, "Calculation not found")
            return status
    """
    service = TaskService(db)
    return await service.get_task_status(task_id)
