"""RPC handlers for drive-thru agent communication."""

import json
import logging

from livekit.rtc import RpcInvocationData


logger = logging.getLogger("drive-thru-agent")


def create_get_order_state_handler(userdata):
    """Create the get_order_state RPC handler with access to userdata."""
    async def get_order_state(_: RpcInvocationData) -> str:
        """Get current order state"""
        try:
            order_items = userdata.order.get_formatted_order()
            total_price = sum(item["price"] for item in order_items)
            
            response = {
                "success": True,
                "data": {
                    "items": order_items,
                    "total_price": total_price,
                    "item_count": len(order_items)
                }
            }
            
            return json.dumps(response)
        except Exception as e:
            logger.error(f"Error in get_order_state RPC: {e}")
            return json.dumps({"success": False, "error": str(e)})
    
    return get_order_state


def register_rpc_handlers(room, userdata):
    """Register all RPC handlers for the drive-thru agent."""
    room.local_participant.register_rpc_method(
        "get_order_state", 
        create_get_order_state_handler(userdata)
    )
    logger.info("RPC methods registered: get_order_state")