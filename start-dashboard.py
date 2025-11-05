#!/usr/bin/env python3
"""
Start NBA Simulator Monitoring Dashboard

Usage:
    python start-dashboard.py
    python start-dashboard.py --port 8080
    python start-dashboard.py --debug
"""

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description='NBA Simulator - Monitoring Dashboard')
    parser.add_argument('--port', '-p', type=int, default=5000, help='Port (default: 5000)')
    parser.add_argument('--host', default='0.0.0.0', help='Host (default: 0.0.0.0)')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("🏀  NBA Simulator - Monitoring Dashboard")
    print("=" * 70)
    print(f"Dashboard URL:  http://{args.host}:{args.port}")
    print(f"Health Check:   http://{args.host}:{args.port}/health")
    print(f"API Status:     http://{args.host}:{args.port}/api/status")
    print("=" * 70)
    print(f"Debug Mode:     {'ENABLED' if args.debug else 'DISABLED'}")
    print("=" * 70)
    print("\nPress Ctrl+C to stop\n")
    
    try:
        from nba_simulator.monitoring.dashboard import app
        app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
    except ImportError:
        print("\n❌ Error: Could not import dashboard module")
        print("Make sure you're running from the project root")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped")
        sys.exit(0)

if __name__ == '__main__':
    main()
