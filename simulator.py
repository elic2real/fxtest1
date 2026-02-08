"""
Minimal, deterministic market simulator.
Replays price events from CSV and emits them to a callback.
Records fills, exits, PnL, and state transitions to a log.
"""

import csv
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Optional, TextIO
import sys


@dataclass
class PriceEvent:
    """A price event from the market."""
    timestamp: str
    bid: float
    ask: float


@dataclass
class Fill:
    """A trade fill record."""
    timestamp: str
    side: str  # 'BUY' or 'SELL'
    price: float
    size: float
    
    def __str__(self):
        return f"FILL: {self.timestamp} {self.side} {self.size}@{self.price}"


@dataclass
class Exit:
    """An exit/close record."""
    timestamp: str
    side: str  # 'BUY' or 'SELL' (opposite of entry)
    price: float
    size: float
    pnl: float
    
    def __str__(self):
        return f"EXIT: {self.timestamp} {self.side} {self.size}@{self.price} PnL={self.pnl:.2f}"


@dataclass
class StateTransition:
    """A state transition record."""
    timestamp: str
    from_state: str
    to_state: str
    reason: str
    
    def __str__(self):
        return f"STATE: {self.timestamp} {self.from_state}->{self.to_state} ({self.reason})"


class MarketSimulator:
    """
    Deterministic market simulator that replays price events from a CSV file.
    
    CSV format: timestamp,bid,ask
    No headers expected.
    
    The simulator emits price events sequentially to a provided callback function.
    It maintains a log of all fills, exits, PnL calculations, and state transitions.
    """
    
    def __init__(self, log_file: TextIO = sys.stdout):
        """
        Initialize the market simulator.
        
        Args:
            log_file: File-like object for logging (default: stdout)
        """
        self.log_file = log_file
        self.fills = []
        self.exits = []
        self.state_transitions = []
        self.current_state = "IDLE"
        self.position_size = 0.0
        self.position_price = 0.0
        self.position_side = None  # 'BUY' or 'SELL'
        self.total_pnl = 0.0
        
    def _log(self, message: str):
        """Write a message to the log."""
        self.log_file.write(f"{message}\n")
        self.log_file.flush()
        
    def _transition_state(self, timestamp: str, new_state: str, reason: str):
        """Record and log a state transition."""
        transition = StateTransition(
            timestamp=timestamp,
            from_state=self.current_state,
            to_state=new_state,
            reason=reason
        )
        self.state_transitions.append(transition)
        self._log(str(transition))
        self.current_state = new_state
        
    def record_fill(self, timestamp: str, side: str, price: float, size: float):
        """
        Record a trade fill.
        
        Args:
            timestamp: Event timestamp
            side: 'BUY' or 'SELL'
            price: Fill price
            size: Fill size (must be positive)
        
        Raises:
            ValueError: If parameters are invalid
        """
        if side not in ('BUY', 'SELL'):
            raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")
        if size <= 0:
            raise ValueError(f"Invalid size: {size}. Must be positive")
        if price <= 0:
            raise ValueError(f"Invalid price: {price}. Must be positive")
            
        fill = Fill(timestamp=timestamp, side=side, price=price, size=size)
        self.fills.append(fill)
        self._log(str(fill))
        
        # Update position
        if self.position_size == 0:
            # Opening new position
            self.position_side = side
            self.position_price = price
            self.position_size = size
            self._transition_state(timestamp, "IN_POSITION", f"opened {side} position")
        elif self.position_side == side:
            # Adding to existing position
            total_value = self.position_price * self.position_size + price * size
            self.position_size += size
            self.position_price = total_value / self.position_size
        else:
            # Position in opposite direction - this is an exit
            raise ValueError(f"Cannot fill {side} while holding {self.position_side} position. Use record_exit instead.")
    
    def record_exit(self, timestamp: str, price: float, size: Optional[float] = None):
        """
        Record an exit/close of current position.
        
        Args:
            timestamp: Event timestamp
            price: Exit price
            size: Size to exit (None = full position)
            
        Raises:
            ValueError: If no position exists or invalid parameters
        """
        if self.position_size == 0:
            raise ValueError("Cannot exit: no open position")
        if price <= 0:
            raise ValueError(f"Invalid price: {price}. Must be positive")
            
        exit_size = self.position_size if size is None else size
        
        if exit_size <= 0:
            raise ValueError(f"Invalid exit size: {exit_size}. Must be positive")
        if exit_size > self.position_size:
            raise ValueError(f"Exit size {exit_size} exceeds position size {self.position_size}")
        
        # Calculate PnL
        if self.position_side == 'BUY':
            pnl = (price - self.position_price) * exit_size
            exit_side = 'SELL'
        else:  # SELL position
            pnl = (self.position_price - price) * exit_size
            exit_side = 'BUY'
        
        exit_record = Exit(
            timestamp=timestamp,
            side=exit_side,
            price=price,
            size=exit_size,
            pnl=pnl
        )
        self.exits.append(exit_record)
        self.total_pnl += pnl
        self._log(str(exit_record))
        
        # Update position
        self.position_size -= exit_size
        if self.position_size == 0:
            self.position_side = None
            self.position_price = 0.0
            self._transition_state(timestamp, "IDLE", "position closed")
        
    def get_position(self):
        """
        Get current position information.
        
        Returns:
            dict with keys: side, size, price, or None if no position
        """
        if self.position_size == 0:
            return None
        return {
            'side': self.position_side,
            'size': self.position_size,
            'price': self.position_price
        }
    
    def get_total_pnl(self):
        """Get total realized PnL."""
        return self.total_pnl
    
    def replay_csv(self, csv_path: str, callback: Callable[[PriceEvent, 'MarketSimulator'], None]):
        """
        Replay price events from a CSV file.
        
        CSV format (no header):
            timestamp,bid,ask
        
        Args:
            csv_path: Path to CSV file
            callback: Function to call for each price event.
                     Signature: callback(event: PriceEvent, simulator: MarketSimulator)
        
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        self._log(f"Starting replay from: {csv_path}")
        self._transition_state("START", "REPLAYING", "begin CSV replay")
        
        try:
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                line_num = 0
                
                for row in reader:
                    line_num += 1
                    
                    if len(row) != 3:
                        raise ValueError(
                            f"Line {line_num}: Expected 3 columns (timestamp,bid,ask), got {len(row)}"
                        )
                    
                    try:
                        timestamp = row[0].strip()
                        bid = float(row[1].strip())
                        ask = float(row[2].strip())
                    except ValueError as e:
                        raise ValueError(
                            f"Line {line_num}: Failed to parse price data: {e}"
                        ) from e
                    
                    if bid <= 0 or ask <= 0:
                        raise ValueError(
                            f"Line {line_num}: Prices must be positive (bid={bid}, ask={ask})"
                        )
                    if bid > ask:
                        raise ValueError(
                            f"Line {line_num}: Bid ({bid}) cannot be greater than ask ({ask})"
                        )
                    
                    event = PriceEvent(timestamp=timestamp, bid=bid, ask=ask)
                    callback(event, self)
                    
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        self._transition_state("END", "COMPLETE", "replay finished")
        self._log(f"Replay complete. Total PnL: {self.total_pnl:.2f}")
