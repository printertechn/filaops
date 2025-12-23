        # Use optimized query with joins
        query = self.db.query(ProductionOrder).filter(
            ProductionOrder.status.in_(statuses)
        )
        
        # Date filtering
        if horizon_date:
            query = query.filter(
                or_(
                    ProductionOrder.due_date.is_(None),
                    ProductionOrder.due_date <= horizon_date
                )
            )
        
        # Eager load related data to reduce queries
        query = query.options(joinedload(ProductionOrder.product))
        
        return query.all()

    def explode_bom(self, *args, **kwargs):
        """Legacy wrapper for compatibility"""
        return self.explode_bom_optimized(*args, **kwargs)
        
    def calculate_net_requirements(self, requirements):
        """Legacy wrapper for compatibility"""
        return self._calculate_net_requirements_optimized(requirements)
        
    def generate_planned_orders(self, shortages, mrp_run_id, user_id=None, **kwargs):
        """Legacy wrapper for compatibility"""
        return self._generate_planned_orders_batch(shortages, mrp_run_id, user_id)
        
    # ========================================================================
    # Supply/Demand Timeline (simplified for stability)
    # ========================================================================

    def get_supply_demand_timeline(
        self,
        product_id: int,
        days_ahead: int = 30
    ) -> Dict:
        """Get simplified supply and demand timeline for a product"""
        try:
            product = self.db.query(Product).get(product_id)
            if not product:
                raise ValueError(f"Product {product_id} not found")

            # Get current inventory
            inv_total = self.db.query(
                func.sum(Inventory.on_hand_quantity),
                func.sum(Inventory.allocated_quantity)
            ).filter(Inventory.product_id == product_id).first()

            on_hand = Decimal(str(inv_total[0] or 0))
            allocated = Decimal(str(inv_total[1] or 0))
            available = on_hand - allocated

            entries = [{
                "date": date.today(),
                "entry_type": "on_hand",
                "source_type": "inventory",
                "source_id": None,
                "source_code": None,
                "quantity": available,
                "running_balance": available
            }]

            return {
                "product_id": product_id,
                "product_sku": product.sku,
                "product_name": product.name,
                "current_on_hand": on_hand,
                "current_available": available,
                "safety_stock": Decimal(str(product.safety_stock or 0)),
                "entries": entries,
                "projected_shortage_date": None,
                "days_of_supply": None
            }
            
        except Exception as e:
            logger.error(f"Error getting supply/demand timeline for product {product_id}: {e}", exc_info=True)
            raise
