#!/usr/bin/env python3
"""
Example usage of the market simulator.
This example implements a simple strategy that:
1. Opens a BUY order on the 3rd tick
2. Closes it on the 10th tick
3. Opens a SELL order on the 12th tick
4. Closes it on the 18th tick
"""

from market_simulator import MarketSimulator, OrderSide, PriceEvent

# Track state across callbacks
state = {
    'tick_count': 0,
    'buy_order': None,
    'sell_order': None,
}


def trading_callback(event: PriceEvent, simulator: MarketSimulator):
    """
    Callback function called for each price event.
    
    Args:
        event: Current price event
        simulator: The market simulator instance
    """
    state['tick_count'] += 1
    tick = state['tick_count']
    
    print(f"Tick {tick}: {event}")
    
    # Open BUY order on tick 3
    if tick == 3:
        state['buy_order'] = simulator.open_order(OrderSide.BUY, size=1000, event=event)
        print(f"  -> Opened BUY order: {state['buy_order'].order_id}")
    
    # Close BUY order on tick 10
    elif tick == 10:
        if state['buy_order']:
            simulator.close_order(state['buy_order'], event)
            print(f"  -> Closed BUY order: {state['buy_order'].order_id}, PnL: {state['buy_order'].pnl:.2f}")
    
    # Open SELL order on tick 12
    elif tick == 12:
        state['sell_order'] = simulator.open_order(OrderSide.SELL, size=1000, event=event)
        print(f"  -> Opened SELL order: {state['sell_order'].order_id}")
    
    # Close SELL order on tick 18
    elif tick == 18:
        if state['sell_order']:
            simulator.close_order(state['sell_order'], event)
            print(f"  -> Closed SELL order: {state['sell_order'].order_id}, PnL: {state['sell_order'].pnl:.2f}")


def main():
    """Run the simulation."""
    print("=" * 60)
    print("Market Simulator Example")
    print("=" * 60)
    
    # Create simulator
    simulator = MarketSimulator(
        csv_path='sample_prices.csv',
        log_path='example.log'
    )
    
    # Run simulation
    print("\nRunning simulation...\n")
    total_pnl = simulator.run(trading_callback)
    
    print("\n" + "=" * 60)
    print(f"Final Total PnL: {total_pnl:.2f}")
    print(f"Check 'example.log' for detailed state transitions")
    print("=" * 60)


if __name__ == '__main__':
    main()
