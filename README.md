# Market Simulator

A minimal, deterministic market simulator in Python for replaying price events from CSV files.

## Features

- **Deterministic**: No AI logic, no indicators, no randomness
- **Event-driven**: Replays price events sequentially from CSV
- **Callback-based**: Provides event callbacks for custom trading logic
- **Complete logging**: Records all fills, exits, PnL, and state transitions
- **Error handling**: Raises clear errors instead of guessing
- **Terminal-ready**: Runs entirely from the command line

## Requirements

- Python 3.6+
- No external dependencies

## Usage

### Running the Example

```bash
python3 example.py
```

This will:
1. Load price data from `sample_prices.csv`
2. Execute a simple trading strategy
3. Print execution details to console
4. Write detailed logs to `example.log`

### CSV Format

Price data must be in CSV format with these columns:
- `timestamp`: Event timestamp (any string format)
- `bid`: Bid price (float)
- `ask`: Ask price (float)

Example:
```csv
timestamp,bid,ask
2024-01-01T09:00:00,1.0850,1.0852
2024-01-01T09:00:01,1.0851,1.0853
2024-01-01T09:00:02,1.0852,1.0854
```

### Writing a Custom Strategy

```python
from market_simulator import MarketSimulator, OrderSide

def my_strategy(event, simulator):
    """Called for each price event."""
    # Your trading logic here
    # Open orders: simulator.open_order(OrderSide.BUY, size=1000, event=event)
    # Close orders: simulator.close_order(order, event)
    pass

# Create and run simulator
simulator = MarketSimulator('prices.csv', 'my_log.log')
simulator.run(my_strategy)
```

## API Reference

### MarketSimulator

Main simulator class.

**Constructor:**
- `MarketSimulator(csv_path: str, log_path: str = "simulator.log")`

**Methods:**
- `run(callback)`: Run simulation with the provided callback function
- `open_order(side, size, event)`: Open a new order at current market price
- `close_order(order, event)`: Close an existing order at current market price

### OrderSide

Enum for order direction:
- `OrderSide.BUY`: Buy/long order
- `OrderSide.SELL`: Sell/short order

### Order

Order object with properties:
- `order_id`: Unique order ID
- `side`: OrderSide (BUY or SELL)
- `size`: Order size
- `entry_price`: Entry price
- `exit_price`: Exit price (None if not closed)
- `status`: Order status (FILLED or EXITED)
- `pnl`: Profit and loss (0 until closed)

### PriceEvent

Price event with properties:
- `timestamp`: Event timestamp
- `bid`: Bid price
- `ask`: Ask price

## Design Principles

1. **Minimal**: No unnecessary features or abstractions
2. **Deterministic**: Same input always produces same output
3. **Explicit**: No hidden state or implicit behavior
4. **Fail-fast**: Raises errors for invalid inputs instead of guessing
5. **Observable**: Complete logging of all state changes

## Log Format

The simulator creates a detailed log file with:
- Simulation start/end markers
- All price events
- Order openings with entry details
- Order closings with exit details and PnL
- Running total PnL after each close
- Final summary statistics

Example log entry:
```
[2024-01-01T09:00:02.123456] ORDER_OPENED: Order(id=1, side=BUY, size=1000, entry=1.0854, exit=None, status=FILLED, pnl=0.00)
[2024-01-01T09:00:09.123456] ORDER_CLOSED: Order(id=1, side=BUY, size=1000, entry=1.0854, exit=1.0859, status=EXITED, pnl=0.50)
[2024-01-01T09:00:09.123456] STATE: Total PnL = 0.50
```

## License

MIT
