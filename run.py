"""
Vehicle Rental System - Application Entry Point
"""
import os
import sys

# Check if data has been initialized
data_dir = os.path.join(os.path.dirname(__file__), 'data')
if not os.path.exists(data_dir) or not os.listdir(data_dir):
    print("=" * 60)
    print("⚠️  Warning: No data found!")
    print("=" * 60)
    print("\nIt looks like this is your first time running the application.")
    print("Please initialize the system with sample data first:\n")
    print("  python init_data.py")
    print("\nThis will create sample users and vehicles for testing.")
    print("=" * 60)
    
    response = input("\nWould you like to initialize data now? (y/n): ").strip().lower()
    if response == 'y':
        print("\nInitializing data...\n")
        import init_data
        init_data.init_data()
        print("\nStarting application...\n")
    else:
        print("\nPlease run 'python init_data.py' before starting the application.")
        sys.exit(0)

# Import and run the Flask app
from app import app

if __name__ == '__main__':
    print("=" * 60)
    print("🚗 Vehicle Rental System")
    print("=" * 60)
    print("\nStarting Flask server...")
    print("Server will be available at: http://localhost:5000")
    print("Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    app.run(debug=True, port=5000)

