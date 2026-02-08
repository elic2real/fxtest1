#!/usr/bin/env python3
"""
Advanced example: Log to file and demonstrate multiple trades.
"""

from simulator import MarketSimulator, PriceEvent


def advanced_strategy(event: PriceEvent, sim: MarketSimulator):
    """
    A more complex strategy with multiple entry/exit conditions.
    
    Logic:
    - Buy when bid drops to 1.0795 or below
    - Add to position when bid drops to 1.0793 or below
    - Exit 50% when bid rises above 1.0805
    - Exit remaining when bid rises above 1.0809
    """
    position = sim.get_position()
    
    # Entry logic
    if position is None:
        if event.bid <= 1.0795:
            print(f"[{event.timestamp}] Entry signal: bid={event.bid}")
            sim.record_fill(
                timestamp=event.timestamp,
                side='BUY',
                price=event.ask,
                size=5000.0
            )
    # Add to position
    elif position['side'] == 'BUY' and position['size'] == 5000.0 and event.bid <= 1.0793:
        print(f"[{event.timestamp}] Add to position: bid={event.bid}")
        sim.record_fill(
            timestamp=event.timestamp,
            side='BUY',
            price=event.ask,
            size=5000.0
        )
    # Partial exit
    elif position is not None and position['side'] == 'BUY' and position['size'] > 5000.0 and event.bid >= 1.0805:
        print(f"[{event.timestamp}] Partial exit signal: bid={event.bid}")
        sim.record_exit(
            timestamp=event.timestamp,
            price=event.bid,
            size=5000.0
        )
    # Full exit
    elif position is not None and position['side'] == 'BUY' and event.bid >= 1.0809:
        print(f"[{event.timestamp}] Full exit signal: bid={event.bid}")
        sim.record_exit(
            timestamp=event.timestamp,
            price=event.bid
        )


def main():
    """Run the advanced example."""
    print("=" * 60)
    print("Market Simulator - Advanced Example (with file logging)")
    print("=" * 60)
    print()
    
    # Create simulator with file logging
    with open('trading_log.txt', 'w') as log_file:
        simulator = MarketSimulator(log_file=log_file)
        
        # Replay market data
        csv_file = "market_data.csv"
        
        try:
            simulator.replay_csv(csv_file, advanced_strategy)
        except FileNotFoundError as e:
            print(f"ERROR: {e}")
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
        
        print()
        print("Detailed log written to: trading_log.txt")
        
    # Show log contents
    print("\n" + "=" * 60)
    print("Log File Contents:")
    print("=" * 60)
    with open('trading_log.txt', 'r') as f:
        print(f.read())
    
    return 0


if __name__ == "__main__":
    exit(main())
