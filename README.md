# Market Simulator

A minimal, deterministic market simulator in Python. Replays price events from CSV files with no AI logic, no indicators, and no randomness.

## Features

- **Deterministic**: Replays price events from CSV files sequentially
- **Event-driven**: Emits events to user-provided callbacks
- **Comprehensive logging**: Records fills, exits, PnL, and state transitions
- **Terminal-based**: Runs entirely from the command line
- **Error handling**: Raises errors for invalid inputs instead of guessing
- **No dependencies**: Uses only Python standard library

## Installation

No installation required. Simply clone the repository:

```bash
git clone https://github.com/elic2real/fxtest1.git
cd fxtest1
```

## Quick Start

Run the included example:

```bash
python3 example.py
```

## CSV Format

The simulator expects CSV files with three columns (no header):

```
timestamp,bid,ask
```

Example:
```
2024-01-01T09:00:00,1.0800,1.0802
2024-01-01T09:00:01,1.0801,1.0803
2024-01-01T09:00:02,1.0802,1.0804
```

## Usage

### Basic Example

```python
from simulator import MarketSimulator, PriceEvent

def my_strategy(event: PriceEvent, sim: MarketSimulator):
    """Your strategy callback function."""
    # Check current position
    position = sim.get_position()
    
    # Example: Buy when no position
    if position is None:
        sim.record_fill(
            timestamp=event.timestamp,
            side='BUY',
            price=event.ask,
            size=10000.0
        )
    # Example: Exit when have position
    elif position['side'] == 'BUY':
        sim.record_exit(
            timestamp=event.timestamp,
            price=event.bid
        )

# Create simulator
simulator = MarketSimulator()

# Replay market data
simulator.replay_csv('market_data.csv', my_strategy)

# Get results
print(f"Total PnL: {simulator.total_pnl}")
```

## API Reference

### MarketSimulator

Main class for the market simulator.

#### Constructor
```python
MarketSimulator(log_file=sys.stdout)
```
- `log_file`: File-like object for logging (default: stdout)

#### Methods

**`replay_csv(csv_path: str, callback: Callable)`**
- Replays price events from a CSV file
- Calls `callback(event, simulator)` for each price event
- Raises `FileNotFoundError` if CSV doesn't exist
- Raises `ValueError` if CSV format is invalid

**`record_fill(timestamp: str, side: str, price: float, size: float)`**
- Records a trade fill
- `side`: Must be 'BUY' or 'SELL'
- `size`: Must be positive
- `price`: Must be positive
- Raises `ValueError` for invalid parameters

**`record_exit(timestamp: str, price: float, size: Optional[float] = None)`**
- Records an exit/close of current position
- `size`: Amount to exit (None = full position)
- Calculates and records PnL automatically
- Raises `ValueError` if no position exists

**`get_position()`**
- Returns current position as dict: `{'side': str, 'size': float, 'price': float}`
- Returns `None` if no position

**`get_total_pnl()`**
- Returns total realized PnL

### Data Classes

**PriceEvent**
```python
@dataclass
class PriceEvent:
    timestamp: str
    bid: float
    ask: float
```

**Fill**
```python
@dataclass
class Fill:
    timestamp: str
    side: str  # 'BUY' or 'SELL'
    price: float
    size: float
```

**Exit**
```python
@dataclass
class Exit:
    timestamp: str
    side: str  # 'BUY' or 'SELL'
    price: float
    size: float
    pnl: float
```

**StateTransition**
```python
@dataclass
class StateTransition:
    timestamp: str
    from_state: str
    to_state: str
    reason: str
```

## State Machine

The simulator maintains these states:
- `IDLE`: No replay in progress, no position
- `REPLAYING`: Actively replaying CSV data
- `IN_POSITION`: Holding an open position
- `COMPLETE`: Replay finished

State transitions are logged automatically.

## Error Handling

The simulator raises explicit errors instead of guessing:

- `ValueError`: Invalid parameters (negative prices, wrong side, etc.)
- `FileNotFoundError`: CSV file doesn't exist
- `ValueError`: CSV format errors (wrong number of columns, invalid data)

## Example Output

```
============================================================
Market Simulator - Example Run
============================================================

Starting replay from: market_data.csv
STATE: START IDLE->REPLAYING (begin CSV replay)
[2024-01-01T09:00:11] Signal: BUY (bid=1.0799 < 1.0800)
FILL: 2024-01-01T09:00:11 BUY 10000.0@1.0801
STATE: 2024-01-01T09:00:11 REPLAYING->IN_POSITION (opened BUY position)
[2024-01-01T09:00:22] Signal: EXIT (bid=1.0807 > 1.0805)
EXIT: 2024-01-01T09:00:22 SELL 10000.0@1.0807 PnL=6.00
STATE: 2024-01-01T09:00:22 IN_POSITION->IDLE (position closed)
STATE: END IDLE->COMPLETE (replay finished)
Replay complete. Total PnL: 6.00

============================================================
Summary
============================================================
Total Fills: 1
Total Exits: 1
Total PnL: 6.00
Final State: COMPLETE
Open Position: None
```

## Design Principles

1. **Deterministic**: Same CSV input always produces same output
2. **No randomness**: No random numbers or probabilistic logic
3. **No AI**: No machine learning or complex algorithms
4. **Explicit errors**: Raises errors for invalid inputs instead of guessing
5. **Sequential**: Processes events in order from CSV
6. **Minimal**: Uses only Python standard library

## License

MIT
