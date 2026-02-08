#!/usr/bin/env python3
"""
Example usage of the market simulator.

This example demonstrates:
1. Loading price data from CSV
2. Implementing a simple callback strategy
3. Recording fills and exits
4. Tracking PnL and state transitions

The strategy used here is a simple mean reversion:
- Buy when price drops below 1.0800
- Sell when price rises above 1.0805
"""

from simulator import MarketSimulator, PriceEvent


def simple_strategy(event: PriceEvent, sim: MarketSimulator):
    """
    A simple deterministic strategy callback.
    
    Logic:
    - If no position and bid < 1.0800: buy at ask
    - If holding BUY position and bid > 1.0805: exit at bid
    """
    position = sim.get_position()
    
    # Entry logic: buy when bid drops below threshold
    if position is None and event.bid < 1.0800:
        print(f"[{event.timestamp}] Signal: BUY (bid={event.bid} < 1.0800)")
        sim.record_fill(
            timestamp=event.timestamp,
            side='BUY',
            price=event.ask,  # Buy at ask price
            size=10000.0      # Fixed position size
        )
    
    # Exit logic: sell when bid rises above threshold
    elif position is not None and position['side'] == 'BUY' and event.bid > 1.0805:
        print(f"[{event.timestamp}] Signal: EXIT (bid={event.bid} > 1.0805)")
        sim.record_exit(
            timestamp=event.timestamp,
            price=event.bid  # Exit at bid price
        )


def main():
    """Run the example."""
    print("=" * 60)
    print("Market Simulator - Example Run")
    print("=" * 60)
    print()
    
    # Create simulator (logs to stdout by default)
    simulator = MarketSimulator()
    
    # Replay market data with our strategy
    csv_file = "market_data.csv"
    
    try:
        simulator.replay_csv(csv_file, simple_strategy)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print("Make sure market_data.csv exists in the current directory.")
        return 1
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1
    
    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total Fills: {len(simulator.fills)}")
    print(f"Total Exits: {len(simulator.exits)}")
    print(f"Total PnL: {simulator.total_pnl:.2f}")
    print(f"Final State: {simulator.current_state}")
    
    current_pos = simulator.get_position()
    if current_pos:
        print(f"Open Position: {current_pos['side']} {current_pos['size']} @ {current_pos['price']:.4f}")
    else:
        print("Open Position: None")
    
    return 0


if __name__ == "__main__":
    exit(main())
