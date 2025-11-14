#!/usr/bin/env python3
import os
import sys
import logging
from database import CustomerDatabase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test-orders")

def add_test_orders():
    """Add test orders for Shayne Parlo."""
    # Initialize the database
    db = CustomerDatabase()
    
    # Create or get Shayne Parlo
    first_name = "Shayne"
    last_name = "Parlo"
    customer_id = db.get_or_create_customer(first_name, last_name)
    logger.info(f"Customer ID for {first_name} {last_name}: {customer_id}")
    
    # Add test orders
    
    # Order 1: Electronics
    order1 = {
        "items": [
            {
                "name": "Smartphone XS Pro",
                "quantity": 1,
                "price": 999.99
            },
            {
                "name": "Wireless Earbuds",
                "quantity": 1,
                "price": 149.99
            },
            {
                "name": "Phone Case (Black)",
                "quantity": 1,
                "price": 29.99
            }
        ],
        "total": 1179.97,
        "payment_method": "Credit Card",
        "shipping_address": "123 Main St, Anytown, USA"
    }
    
    # Order 2: Clothing
    order2 = {
        "items": [
            {
                "name": "Men's Casual Shirt (Blue)",
                "quantity": 2,
                "price": 39.99
            },
            {
                "name": "Jeans (Dark Wash)",
                "quantity": 1,
                "price": 59.99
            },
            {
                "name": "Leather Belt",
                "quantity": 1,
                "price": 34.99
            }
        ],
        "total": 174.96,
        "payment_method": "PayPal",
        "shipping_address": "123 Main St, Anytown, USA"
    }
    
    # Order 3: Home Goods
    order3 = {
        "items": [
            {
                "name": "Coffee Maker",
                "quantity": 1,
                "price": 89.99
            },
            {
                "name": "Towel Set",
                "quantity": 1,
                "price": 49.99
            },
            {
                "name": "Decorative Pillows",
                "quantity": 2,
                "price": 24.99
            }
        ],
        "total": 189.96,
        "payment_method": "Credit Card",
        "shipping_address": "123 Main St, Anytown, USA"
    }
    
    # Add orders to database
    order1_id = db.add_order(customer_id, order1)
    logger.info(f"Added Order #{order1_id}: Electronics - Total: ${order1['total']}")
    
    order2_id = db.add_order(customer_id, order2)
    logger.info(f"Added Order #{order2_id}: Clothing - Total: ${order2['total']}")
    
    order3_id = db.add_order(customer_id, order3)
    logger.info(f"Added Order #{order3_id}: Home Goods - Total: ${order3['total']}")
    
    # Verify orders were added
    order_history = db.get_customer_order_history(first_name, last_name)
    logger.info(f"Order history for {first_name} {last_name}:\n{order_history}")
    
    return order1_id, order2_id, order3_id

if __name__ == "__main__":
    order_ids = add_test_orders()
    print(f"Added test orders with IDs: {order_ids}")
    print("Test orders have been added successfully for Shayne Parlo.") 