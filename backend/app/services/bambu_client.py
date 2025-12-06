"""
Bambu Print Suite API Client

This client handles all communication with the Bambu Print Suite API
for printer management, job scheduling, real-time status updates, and quote generation.
"""
import httpx
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pathlib import Path

logger = logging.getLogger(__name__)

class BambuSuiteClient:
    """Client for Bambu Print Suite API"""

    def __init__(self, api_url: str, api_key: Optional[str] = None):
        """
        Initialize Bambu Suite client

        Args:
            api_url: Base URL of Bambu Print Suite API
            api_key: Optional API key for authentication
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.headers = {}

        if api_key:
            self.headers['X-API-Key'] = api_key

        # Material costs per gram (fallback pricing)
        self.material_costs = {
            'PLA': Decimal('0.01699'),    # $0.01699/gram = $16.99/kg
            'PETG': Decimal('0.02039'),   # $0.02039/gram = $20.39/kg (1.2× PLA)
            'ABS': Decimal('0.01869'),    # $0.01869/gram = $18.69/kg (1.1× PLA)
            'ASA': Decimal('0.02209'),    # $0.02209/gram = $22.09/kg (1.3× PLA)
            'TPU': Decimal('0.03058'),    # $0.03058/gram = $30.58/kg (1.8× PLA)
        }

        # Labor rate per hour
        self.labor_rate = Decimal('1.50')  # $1.50/hour machine time

        # Base margin (covers overhead + profit)
        # Standard: 2.0x, Rush: 2.5x, Volume: 1.5x
        self.base_margin = Decimal('2.0')  # 100% markup (2x multiplier)

    async def test_connection(self) -> bool:
        """
        Test connection to Bambu Print Suite

        Returns:
            True if connection successful, False otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/health",
                    headers=self.headers,
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to connect to Bambu Suite: {str(e)}")
            return False

    async def create_print_job(
        self,
        production_order_id: int,
        product_sku: str,
        product_name: str,
        quantity: int,
        material_type: str,
        gcode_file: Optional[str] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Create a new print job in Bambu Suite

        Args:
            production_order_id: ERP production order ID
            product_sku: Product SKU
            product_name: Product name
            quantity: Quantity to print
            material_type: Material type (PLA, PETG, etc.)
            gcode_file: Path to GCODE file
            priority: Job priority (low, normal, high, urgent)

        Returns:
            Print job details including ID and assigned printer
        """
        try:
            job_data = {
                'production_order_id': production_order_id,
                'product_sku': product_sku,
                'product_name': product_name,
                'quantity': quantity,
                'material_type': material_type,
                'gcode_file': gcode_file,
                'priority': priority,
                'created_at': datetime.now().isoformat()
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/api/integration/print-jobs",
                    json=job_data,
                    headers=self.headers,
                    timeout=10.0
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error creating print job: {e.response.status_code}")
            raise Exception(f"Failed to create print job: {e.response.text}")
        except Exception as e:
            logger.error(f"Error creating print job: {str(e)}")
            raise

    async def get_print_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get status of a specific print job

        Args:
            job_id: Print job ID

        Returns:
            Job status details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/api/integration/print-jobs/{job_id}",
                    headers=self.headers,
                    timeout=5.0
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Error getting print job status: {str(e)}")
            raise

    async def get_all_printer_status(self) -> List[Dict[str, Any]]:
        """
        Get status of all printers

        Returns:
            List of printer status information
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/api/integration/printers/status",
                    headers=self.headers,
                    timeout=5.0
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Error getting printer status: {str(e)}")
            raise

    async def get_quote(self, quote_id: str) -> Dict[str, Any]:
        """
        Get quote details from Bambu Suite

        Args:
            quote_id: Quote ID

        Returns:
            Quote details
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/api/integration/quotes/{quote_id}",
                    headers=self.headers,
                    timeout=5.0
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Error getting quote: {str(e)}")
            raise

    async def generate_quote(
        self,
        file_path: str,
        material_type: str,
        quantity: int,
        finish: str = "standard",
        rush_level: str = "standard"
    ) -> Dict[str, Any]:
        """
        Generate quote for 3D print job

        Attempts to call Bambu Suite quote engine API. If unavailable,
        falls back to calculated pricing based on file size and material costs.

        Args:
            file_path: Path to .3mf or .stl file
            material_type: Material (PLA, PETG, ABS, ASA, TPU)
            quantity: Number of parts
            finish: Finish type (standard, smooth, painted)
            rush_level: Rush level (standard, rush, super_rush, urgent)

        Returns:
            Dictionary with quote data:
            {
                'success': bool,
                'material_grams': Decimal,
                'print_time_hours': Decimal,
                'material_cost': Decimal,
                'labor_cost': Decimal,
                'unit_price': Decimal,
                'total_price': Decimal,
                'dimensions_x': Decimal,
                'dimensions_y': Decimal,
                'dimensions_z': Decimal
            }
        """
        # Try to call Bambu Suite API
        try:
            response = await self._call_bambu_quote_api(
                file_path=file_path,
                material_type=material_type,
                quantity=quantity,
                finish=finish,
                rush_level=rush_level
            )
            logger.info(f"Bambu Suite quote successful for {file_path}")
            return response
        except Exception as e:
            logger.warning(f"Bambu Suite quote API unavailable, using fallback pricing: {e}")

        # Fallback: Use calculated pricing
        return await self._calculate_quote_fallback(
            file_path=file_path,
            material_type=material_type,
            quantity=quantity,
            finish=finish,
            rush_level=rush_level
        )

    async def _call_bambu_quote_api(
        self,
        file_path: str,
        material_type: str,
        quantity: int,
        finish: str,
        rush_level: str
    ) -> Dict[str, Any]:
        """
        Call Bambu Suite quote engine API

        Endpoint: POST /api/quotes/generate
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Upload file and get quote
            with open(file_path, 'rb') as f:
                files = {'file': (Path(file_path).name, f, 'application/octet-stream')}
                data = {
                    'material': material_type,
                    'quantity': quantity,
                    'finish': finish,
                    'rush_level': rush_level
                }

                response = await client.post(
                    f"{self.api_url}/api/quotes/generate",
                    files=files,
                    data=data,
                    headers=self.headers
                )

            response.raise_for_status()
            data = response.json()

            return {
                'success': True,
                'material_grams': Decimal(str(data['material_grams'])),
                'print_time_hours': Decimal(str(data['print_time_hours'])),
                'material_cost': Decimal(str(data['material_cost'])),
                'labor_cost': Decimal(str(data['labor_cost'])),
                'unit_price': Decimal(str(data['unit_price'])),
                'total_price': Decimal(str(data['total_price'])),
                'dimensions_x': Decimal(str(data['dimensions']['x'])),
                'dimensions_y': Decimal(str(data['dimensions']['y'])),
                'dimensions_z': Decimal(str(data['dimensions']['z'])),
            }

    async def _calculate_quote_fallback(
        self,
        file_path: str,
        material_type: str,
        quantity: int,
        finish: str,
        rush_level: str
    ) -> Dict[str, Any]:
        """
        Calculate quote using fallback pricing model

        Uses file size and material costs to estimate pricing when
        Bambu Suite API is unavailable.
        """
        # Get file stats
        file_path_obj = Path(file_path)
        file_size_mb = file_path_obj.stat().st_size / (1024 * 1024)

        # Estimate material usage based on file size
        # Rule of thumb: 1MB file ≈ 50g material (rough estimate)
        base_material_grams = max(20, file_size_mb * 50)  # Min 20g

        # Adjust for material density
        density_factors = {
            'PLA': 1.0,
            'PETG': 1.1,
            'ABS': 0.95,
            'ASA': 0.95,
            'TPU': 1.2
        }
        material_grams = Decimal(str(base_material_grams * density_factors.get(material_type, 1.0)))

        # Estimate print time (hours)
        # Rule of thumb: 1g material ≈ 3 minutes print time
        base_print_time = float(material_grams) * 3 / 60  # Convert to hours
        print_time_hours = Decimal(str(max(0.5, base_print_time)))  # Min 30 min

        # Adjust for finish
        finish_multipliers = {
            'standard': Decimal('1.0'),
            'smooth': Decimal('1.3'),    # Additional post-processing
            'painted': Decimal('1.5')    # Painting + prep
        }
        finish_multiplier = finish_multipliers.get(finish, Decimal('1.0'))

        # Adjust for rush level (additional multiplier ON TOP of base margin)
        rush_multipliers = {
            'standard': Decimal('1.0'),     # No rush premium
            'rush': Decimal('1.25'),        # +25% rush premium
            'super_rush': Decimal('1.5'),   # +50% rush premium
            'urgent': Decimal('1.75')       # +75% rush premium
        }
        rush_multiplier = rush_multipliers.get(rush_level, Decimal('1.0'))

        # Calculate costs
        material_cost_per_gram = self.material_costs.get(material_type, Decimal('0.03'))
        material_cost = material_grams * material_cost_per_gram
        labor_cost = print_time_hours * self.labor_rate

        # Base unit price (material + labor)
        base_unit_price = material_cost + labor_cost

        # Apply base margin (covers overhead + profit)
        unit_price = base_unit_price * self.base_margin

        # Apply finish multiplier
        unit_price = unit_price * finish_multiplier

        # Apply rush multiplier (additional charge on top of everything)
        unit_price = unit_price * rush_multiplier

        # Total price
        total_price = unit_price * quantity

        # Estimate dimensions (rough guess)
        dimensions_x = Decimal('100.0')
        dimensions_y = Decimal('100.0')
        dimensions_z = Decimal('50.0')

        logger.info(
            f"Fallback pricing: {material_grams}g, {print_time_hours}h, "
            f"${unit_price}/unit, ${total_price} total"
        )

        return {
            'success': True,
            'material_grams': material_grams,
            'print_time_hours': print_time_hours,
            'material_cost': material_cost,
            'labor_cost': labor_cost,
            'unit_price': unit_price,
            'total_price': total_price,
            'dimensions_x': dimensions_x,
            'dimensions_y': dimensions_y,
            'dimensions_z': dimensions_z,
        }

    async def update_print_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        current_layer: Optional[int] = None,
        remaining_time: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update print job status

        Args:
            job_id: Print job ID
            status: Job status
            progress: Progress percentage
            current_layer: Current layer number
            remaining_time: Remaining time in minutes

        Returns:
            Updated job details
        """
        try:
            update_data = {}
            if status:
                update_data['status'] = status
            if progress is not None:
                update_data['progress'] = progress
            if current_layer is not None:
                update_data['current_layer'] = current_layer
            if remaining_time is not None:
                update_data['remaining_time'] = remaining_time

            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_url}/api/integration/print-jobs/{job_id}",
                    json=update_data,
                    headers=self.headers,
                    timeout=5.0
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Error updating print job: {str(e)}")
            raise

    async def complete_print_job(
        self,
        job_id: str,
        actual_time: int,
        actual_material: float,
        actual_cost: float
    ) -> Dict[str, Any]:
        """
        Mark print job as complete with actual metrics

        Args:
            job_id: Print job ID
            actual_time: Actual print time in minutes
            actual_material: Actual material used in grams
            actual_cost: Actual cost

        Returns:
            Completed job details
        """
        try:
            completion_data = {
                'actual_time_minutes': actual_time,
                'actual_material_grams': actual_material,
                'actual_cost': actual_cost,
                'completed_at': datetime.now().isoformat()
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/api/integration/print-jobs/{job_id}/complete",
                    json=completion_data,
                    headers=self.headers,
                    timeout=5.0
                )
                response.raise_for_status()
                return response.json()

        except Exception as e:
            logger.error(f"Error completing print job: {str(e)}")
            raise
