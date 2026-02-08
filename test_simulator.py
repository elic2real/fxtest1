#!/usr/bin/env python3
"""
Test script to validate error handling and edge cases.
"""

from simulator import MarketSimulator, PriceEvent
import sys


def test_invalid_csv():
    """Test with invalid CSV format."""
    print("Test 1: Invalid CSV format")
    sim = MarketSimulator()
    
    # Create invalid CSV
    with open('/tmp/invalid.csv', 'w') as f:
        f.write("2024-01-01T09:00:00,1.0800\n")  # Only 2 columns
    
    try:
        sim.replay_csv('/tmp/invalid.csv', lambda e, s: None)
        print("  FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"  PASSED: {e}")
        return True


def test_missing_csv():
    """Test with non-existent CSV."""
    print("\nTest 2: Missing CSV file")
    sim = MarketSimulator()
    
    try:
        sim.replay_csv('/tmp/nonexistent.csv', lambda e, s: None)
        print("  FAILED: Should have raised FileNotFoundError")
        return False
    except FileNotFoundError as e:
        print(f"  PASSED: {e}")
        return True


def test_invalid_prices():
    """Test with invalid prices."""
    print("\nTest 3: Invalid prices (bid > ask)")
    sim = MarketSimulator()
    
    # Create CSV with bid > ask
    with open('/tmp/invalid_prices.csv', 'w') as f:
        f.write("2024-01-01T09:00:00,1.0805,1.0800\n")  # bid > ask
    
    try:
        sim.replay_csv('/tmp/invalid_prices.csv', lambda e, s: None)
        print("  FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"  PASSED: {e}")
        return True


def test_invalid_fill_side():
    """Test recording fill with invalid side."""
    print("\nTest 4: Invalid fill side")
    sim = MarketSimulator()
    
    try:
        sim.record_fill("2024-01-01T09:00:00", "INVALID", 1.0800, 1000.0)
        print("  FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"  PASSED: {e}")
        return True


def test_exit_without_position():
    """Test exiting without position."""
    print("\nTest 5: Exit without position")
    sim = MarketSimulator()
    
    try:
        sim.record_exit("2024-01-01T09:00:00", 1.0800)
        print("  FAILED: Should have raised ValueError")
        return False
    except ValueError as e:
        print(f"  PASSED: {e}")
        return True


def test_position_tracking():
    """Test position tracking."""
    print("\nTest 6: Position tracking")
    sim = MarketSimulator()
    
    # No position initially
    if sim.get_position() is not None:
        print("  FAILED: Should have no position initially")
        return False
    
    # Record a fill
    sim.record_fill("2024-01-01T09:00:00", "BUY", 1.0800, 1000.0)
    
    pos = sim.get_position()
    if pos is None or pos['side'] != 'BUY' or pos['size'] != 1000.0:
        print(f"  FAILED: Wrong position: {pos}")
        return False
    
    # Exit position
    sim.record_exit("2024-01-01T09:00:01", 1.0810)
    
    if sim.get_position() is not None:
        print("  FAILED: Should have no position after exit")
        return False
    
    # Check PnL
    expected_pnl = (1.0810 - 1.0800) * 1000.0  # 10.0
    if abs(sim.get_total_pnl() - expected_pnl) > 0.01:
        print(f"  FAILED: Wrong PnL: {sim.get_total_pnl()}, expected {expected_pnl}")
        return False
    
    print("  PASSED: Position tracking and PnL calculation correct")
    return True


def test_partial_exit():
    """Test partial position exit."""
    print("\nTest 7: Partial position exit")
    sim = MarketSimulator()
    
    # Record a fill
    sim.record_fill("2024-01-01T09:00:00", "BUY", 1.0800, 1000.0)
    
    # Partial exit
    sim.record_exit("2024-01-01T09:00:01", 1.0810, size=500.0)
    
    pos = sim.get_position()
    if pos is None or pos['size'] != 500.0:
        print(f"  FAILED: Wrong position size after partial exit: {pos}")
        return False
    
    # Check PnL
    expected_pnl = (1.0810 - 1.0800) * 500.0  # 5.0
    if abs(sim.get_total_pnl() - expected_pnl) > 0.01:
        print(f"  FAILED: Wrong PnL: {sim.get_total_pnl()}, expected {expected_pnl}")
        return False
    
    print("  PASSED: Partial exit works correctly")
    return True


def test_sell_position():
    """Test SELL position and PnL."""
    print("\nTest 8: SELL position PnL calculation")
    sim = MarketSimulator()
    
    # Record a SELL fill
    sim.record_fill("2024-01-01T09:00:00", "SELL", 1.0800, 1000.0)
    
    # Exit at lower price (profit for SELL)
    sim.record_exit("2024-01-01T09:00:01", 1.0790)
    
    # PnL should be (1.0800 - 1.0790) * 1000.0 = 10.0
    expected_pnl = (1.0800 - 1.0790) * 1000.0
    if abs(sim.get_total_pnl() - expected_pnl) > 0.01:
        print(f"  FAILED: Wrong PnL: {sim.get_total_pnl()}, expected {expected_pnl}")
        return False
    
    print("  PASSED: SELL position PnL calculation correct")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Market Simulator - Test Suite")
    print("=" * 60)
    
    tests = [
        test_invalid_csv,
        test_missing_csv,
        test_invalid_prices,
        test_invalid_fill_side,
        test_exit_without_position,
        test_position_tracking,
        test_partial_exit,
        test_sell_position,
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"  ERROR: Unexpected exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
