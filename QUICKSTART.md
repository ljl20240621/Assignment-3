# Quick Start Guide

Get your Vehicle Rental System up and running in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Initialize Sample Data

```bash
python init_data.py
```

This creates:
- **7 Cars** (Toyota, Honda, Mazda, Ford)
- **5 Motorbikes** (Yamaha, Honda, Kawasaki, Harley-Davidson, Suzuki)
- **5 Trucks** (Ford, Chevrolet, RAM, Toyota)
- **6 Users** (1 staff, 2 corporate, 3 individual)

## Step 3: (Optional) Generate Placeholder Images

```bash
cd static/images
python generate_placeholders.py
cd ../..
```

Or manually add your own vehicle images as:
- `static/images/car.jpg`
- `static/images/motorbike.jpg`
- `static/images/truck.jpg`
- `static/images/default.jpg`

## Step 4: Run the Application

```bash
python run.py
```

Or directly:
```bash
python app.py
```

## Step 5: Access the System

Open your browser and go to: **http://localhost:5000**

## Demo Accounts

### Staff (Administrator)
- **Username**: `admin`
- **Password**: `admin123`
- **Can**: Manage users, manage vehicles, view analytics, view all rentals

### Corporate User (15% Discount)
- **Username**: `corp001` or `corp002`
- **Password**: `password123`
- **Can**: Browse and rent vehicles, view rental history
- **Benefit**: 15% discount on all rentals

### Individual User (10% for 7+ days)
- **Username**: `john001`, `jane002`, or `bob003`
- **Password**: `password123`
- **Can**: Browse and rent vehicles, view rental history
- **Benefit**: 10% discount for rentals of 7 days or more

## Quick Test Workflow

### As a Customer:
1. Login with `corp001` / `password123`
2. Click "Vehicles" in navigation
3. Select any vehicle
4. Click "Rent Now"
5. Choose dates (try different durations to see discount)
6. Confirm rental
7. View your rental in Dashboard
8. Return the vehicle from Dashboard

### As Staff:
1. Login with `admin` / `admin123`
2. View dashboard with system statistics
3. Click "Manage" → "Users" to manage users
4. Click "Manage" → "Vehicles" to manage vehicles
5. Click "Analytics" to view business metrics
6. Click "Activities" to see rental/return logs

## Common Tasks

### Add a New Vehicle (Staff Only)
1. Login as staff
2. Go to "Manage" → "Vehicles"
3. Click "Add New Vehicle"
4. Fill in details and submit

### Add a New User (Staff Only)
1. Login as staff
2. Go to "Manage" → "Users"
3. Click "Add New User"
4. Fill in details and submit

### Rent a Vehicle (Customer)
1. Login as customer
2. Browse vehicles
3. Select vehicle and dates
4. Confirm and get invoice

### Return a Vehicle (Customer)
1. Login as customer
2. Go to Dashboard
3. Find active rental
4. Click "Return" button

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_users.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=models
```

## Troubleshooting

### "No data found" error
Run: `python init_data.py`

### Port 5000 already in use
Edit `app.py` line 470 to use different port:
```python
app.run(debug=True, port=5001)
```

### Import errors
Ensure you're running from project root directory:
```bash
cd Assignment-3
python app.py
```

### Missing images
Either run the placeholder generator or add your own images to `static/images/`

## Need Help?

See the full documentation in `README.md` for:
- Complete feature list
- Architecture details
- Development guide
- Testing guide
- API documentation

## Next Steps

1. ✅ Explore the UI as different user types
2. ✅ Try renting and returning vehicles
3. ✅ Check analytics dashboard (as staff)
4. ✅ Run the test suite
5. ✅ Customize for your needs

Enjoy your Vehicle Rental System! 🚗🏍️🚚

