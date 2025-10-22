"""
Vehicle Rental System - Application Entry Point
"""
from app import app

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Server will be available at: http://localhost:5000")
    print("Press CTRL+C to stop the server")
    app.run(debug=True, port=5000)

