import sqlite3
import os
import json
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger("personal-shopper-db")
logger.setLevel(logging.INFO)

class CustomerDatabase:
    def __init__(self, db_path: str = None):
        """Initialize the customer database."""
        if db_path is None:
            # Use a default path in the same directory as this file
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, 'customer_data.db')
        
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Create the database and tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create customers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create orders table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_details TEXT NOT NULL,
            order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers (id)
        )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def get_or_create_customer(self, first_name: str, last_name: str) -> int:
        """Get a customer by name or create if not exists. Returns customer ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if customer exists
        cursor.execute(
            "SELECT id FROM customers WHERE first_name = ? AND last_name = ?", 
            (first_name, last_name)
        )
        result = cursor.fetchone()
        
        if result:
            customer_id = result[0]
            logger.info(f"Found existing customer: {first_name} {last_name} (ID: {customer_id})")
        else:
            # Create new customer
            cursor.execute(
                "INSERT INTO customers (first_name, last_name) VALUES (?, ?)",
                (first_name, last_name)
            )
            customer_id = cursor.lastrowid
            logger.info(f"Created new customer: {first_name} {last_name} (ID: {customer_id})")
        
        conn.commit()
        conn.close()
        return customer_id
    
    def add_order(self, customer_id: int, order_details: Dict[str, Any]) -> int:
        """Add a new order for a customer. Returns order ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Convert order details to JSON string
        order_json = json.dumps(order_details)
        
        cursor.execute(
            "INSERT INTO orders (customer_id, order_details) VALUES (?, ?)",
            (customer_id, order_json)
        )
        
        order_id = cursor.lastrowid
        logger.info(f"Added new order (ID: {order_id}) for customer ID: {customer_id}")
        
        conn.commit()
        conn.close()
        return order_id
    
    def get_customer_orders(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get all orders for a customer."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, order_details, order_date FROM orders WHERE customer_id = ? ORDER BY order_date DESC",
            (customer_id,)
        )
        
        orders = []
        for row in cursor.fetchall():
            order_data = json.loads(row['order_details'])
            orders.append({
                'id': row['id'],
                'date': row['order_date'],
                'details': order_data
            })
        
        conn.close()
        return orders
    
    def get_customer_order_history(self, first_name: str, last_name: str) -> str:
        """Get a formatted string of customer order history for LLM consumption."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get customer ID
        cursor.execute(
            "SELECT id FROM customers WHERE first_name = ? AND last_name = ?", 
            (first_name, last_name)
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return "No order history found for this customer."
        
        customer_id = result[0]
        orders = self.get_customer_orders(customer_id)
        
        if not orders:
            return f"Customer {first_name} {last_name} has no previous orders."
        
        # Format order history for LLM
        history = f"Order history for {first_name} {last_name}:\n\n"
        
        for order in orders:
            history += f"Order #{order['id']} (Date: {order['date']}):\n"
            details = order['details']
            
            if 'items' in details:
                for item in details['items']:
                    history += f"- {item.get('quantity', 1)}x {item.get('name', 'Unknown Item')}"
                    if 'price' in item:
                        history += f" (${item['price']})"
                    history += "\n"
            else:
                # Handle case where order details might be in a different format
                history += f"- {json.dumps(details)}\n"
            
            history += "\n"
        
        conn.close()
        return history 