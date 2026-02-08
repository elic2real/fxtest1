"""
Minimal, deterministic market simulator.
Replays price events from CSV and records trading activity.
"""

import csv
from datetime import datetime
from typing import Callable, List, Dict, Any, Optional
from enum import Enum


class OrderSide(Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    EXITED = "EXITED"


class PriceEvent:
    """Represents a single price tick."""
    
    def __init__(self, timestamp: str, bid: float, ask: float):
        self.timestamp = timestamp
        self.bid = bid
        self.ask = ask
    
    def __repr__(self):
        return f"PriceEvent(timestamp={self.timestamp}, bid={self.bid}, ask={self.ask})"


class Order:
    """Represents a trading order."""
    
    def __init__(self, order_id: int, side: OrderSide, size: float, entry_price: float, timestamp: str):
        self.order_id = order_id
        self.side = side
        self.size = size
        self.entry_price = entry_price
        self.entry_timestamp = timestamp
        self.exit_price: Optional[float] = None
        self.exit_timestamp: Optional[str] = None
        self.status = OrderStatus.FILLED
        self.pnl: float = 0.0
    
    def exit(self, exit_price: float, timestamp: str):
        """Close the order at the given price."""
        self.exit_price = exit_price
        self.exit_timestamp = timestamp
        self.status = OrderStatus.EXITED
        
        # Calculate PnL
        if self.side == OrderSide.BUY:
            self.pnl = (exit_price - self.entry_price) * self.size
        else:  # SELL
            self.pnl = (self.entry_price - exit_price) * self.size
    
    def __repr__(self):
        return (f"Order(id={self.order_id}, side={self.side.value}, size={self.size}, "
                f"entry={self.entry_price}, exit={self.exit_price}, status={self.status.value}, pnl={self.pnl:.2f})")


class MarketSimulator:
    """
    Deterministic market simulator that replays price events from CSV.
    """
    
    def __init__(self, csv_path: str, log_path: str = "simulator.log"):
        self.csv_path = csv_path
        self.log_path = log_path
        self.orders: List[Order] = []
        self.next_order_id = 1
        self.total_pnl = 0.0
        self.log_file = None
    
    def _log(self, message: str):
        """Write a message to the log file."""
        if self.log_file:
            timestamp = datetime.now().isoformat()
            self.log_file.write(f"[{timestamp}] {message}\n")
            self.log_file.flush()
    
    def _read_csv(self) -> List[PriceEvent]:
        """Read price events from CSV file."""
        events = []
        try:
            with open(self.csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Validate required fields
                    if 'timestamp' not in row or 'bid' not in row or 'ask' not in row:
                        raise ValueError(f"CSV must contain 'timestamp', 'bid', and 'ask' columns. Got: {row.keys()}")
                    
                    try:
                        bid = float(row['bid'])
                        ask = float(row['ask'])
                    except ValueError as e:
                        raise ValueError(f"Invalid numeric value in CSV: {e}")
                    
                    events.append(PriceEvent(row['timestamp'], bid, ask))
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
        except (ValueError, KeyError) as e:
            # Re-raise ValueError and KeyError directly
            raise
        except Exception as e:
            raise RuntimeError(f"Error reading CSV: {e}")
        
        if not events:
            raise ValueError("CSV file is empty or contains no valid events")
        
        return events
    
    def open_order(self, side: OrderSide, size: float, event: PriceEvent) -> Order:
        """
        Open a new order at the current market price.
        
        Args:
            side: BUY or SELL
            size: Order size
            event: Current price event
        
        Returns:
            The created order
        """
        # Use ask price for buy, bid price for sell (realistic market execution)
        entry_price = event.ask if side == OrderSide.BUY else event.bid
        
        order = Order(self.next_order_id, side, size, entry_price, event.timestamp)
        self.next_order_id += 1
        self.orders.append(order)
        
        self._log(f"ORDER_OPENED: {order}")
        return order
    
    def close_order(self, order: Order, event: PriceEvent):
        """
        Close an existing order at the current market price.
        
        Args:
            order: The order to close
            event: Current price event
        """
        if order.status != OrderStatus.FILLED:
            raise ValueError(f"Cannot close order {order.order_id}: status is {order.status.value}")
        
        # Use bid price for closing buy, ask price for closing sell
        exit_price = event.bid if order.side == OrderSide.BUY else event.ask
        
        order.exit(exit_price, event.timestamp)
        self.total_pnl += order.pnl
        
        self._log(f"ORDER_CLOSED: {order}")
        self._log(f"STATE: Total PnL = {self.total_pnl:.2f}")
    
    def run(self, callback: Callable[[PriceEvent, 'MarketSimulator'], None]):
        """
        Run the simulation by replaying all price events.
        
        Args:
            callback: Function called for each price event. Signature: callback(event, simulator)
        """
        # Open log file
        with open(self.log_path, 'w') as log_file:
            self.log_file = log_file
            
            self._log("=== SIMULATION START ===")
            self._log(f"CSV: {self.csv_path}")
            
            # Read all events
            events = self._read_csv()
            self._log(f"Loaded {len(events)} price events")
            
            # Process events sequentially
            for i, event in enumerate(events):
                self._log(f"EVENT_{i}: {event}")
                
                # Call the user callback
                try:
                    callback(event, self)
                except Exception as e:
                    self._log(f"ERROR in callback: {e}")
                    raise RuntimeError(f"Callback error at event {i}: {e}")
            
            # Final state
            self._log("=== SIMULATION END ===")
            self._log(f"Total orders: {len(self.orders)}")
            self._log(f"Total PnL: {self.total_pnl:.2f}")
            
            # Close any open orders
            open_orders = [o for o in self.orders if o.status == OrderStatus.FILLED]
            if open_orders:
                self._log(f"WARNING: {len(open_orders)} orders still open at end of simulation")
                for order in open_orders:
                    self._log(f"  OPEN: {order}")
            
            self.log_file = None
        
        print(f"Simulation complete. Log written to: {self.log_path}")
        print(f"Total PnL: {self.total_pnl:.2f}")
        return self.total_pnl
