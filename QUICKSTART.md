# Quick Start Guide

This guide will help you get the Travel Recommendation System up and running in minutes.

## Prerequisites

- PHP 8.1+ installed
- MongoDB installed and running (see MONGODB_SETUP.md for installation)
- Composer installed

## Installation (5 minutes)

### Step 1: Get the Code

```bash
git clone https://github.com/phoebe497/Travel-Recommendation.git
cd Travel-Recommendation
```

### Step 2: Install Dependencies

```bash
composer install
```

### Step 3: Configure Environment

```bash
# Copy environment file
cp .env.example .env

# Generate application key
php artisan key:generate
```

### Step 4: Update Database Settings

Edit `.env` file and set your MongoDB connection:

```env
DB_CONNECTION=mongodb
DB_HOST=127.0.0.1
DB_PORT=27017
DB_DATABASE=travel_recommendation
DB_USERNAME=
DB_PASSWORD=
```

### Step 5: Seed Sample Data

```bash
php artisan db:seed
```

This will create:
- 2 sample users (john@example.com and jane@example.com, both password: password123)
- 10 sample tours in various categories

### Step 6: Start the Server

```bash
php artisan serve
```

The application will be available at `http://localhost:8000`

## Quick Test (2 minutes)

### 1. Create a User

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Wonder",
    "email": "alice@example.com",
    "password": "password123",
    "preferences": {
      "categories": ["adventure", "nature"],
      "tags": ["hiking", "photography"],
      "min_rating": 4.0
    }
  }'
```

**Response:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": "...",
    "name": "Alice Wonder",
    "email": "alice@example.com",
    "preferences": {...}
  }
}
```

Copy the `id` from the response for the next steps.

### 2. Generate Recommendations

Replace `{userId}` with the ID from step 1:

```bash
curl -X POST http://localhost:8000/api/recommendations/users/{userId}/generate \
  -H "Content-Type: application/json" \
  -d '{"date": "2024-01-20"}'
```

**Response:**
```json
{
  "message": "Recommendations generated successfully",
  "user_id": "...",
  "date": "2024-01-20",
  "schedule": [
    {
      "tour_id": "...",
      "tour_name": "Mountain Hiking Adventure",
      "start_time": "08:00",
      "end_time": "12:00",
      "duration": 240,
      "travel_time": 0,
      "score": 0.92
    },
    {
      "tour_id": "...",
      "tour_name": "Sunset Photography Tour",
      "start_time": "12:30",
      "end_time": "14:00",
      "duration": 90,
      "travel_time": 30,
      "score": 0.88
    }
  ],
  "score": 0.90
}
```

### 3. Get Tours

```bash
curl http://localhost:8000/api/tours
```

### 4. Filter Tours by Category

```bash
curl "http://localhost:8000/api/tours?category=adventure&min_rating=4.0"
```

## Using the Seeded Data

The database seeder creates two test users:

**User 1:**
- Email: `john@example.com`
- Password: `password123`
- Preferences: adventure, nature, cultural tours

**User 2:**
- Email: `jane@example.com`
- Password: `password123`
- Preferences: food, cultural, shopping tours

You can generate recommendations for these users after finding their IDs:

```bash
# List all users (you'll need to implement this endpoint or check MongoDB)
mongosh
use travel_recommendation
db.users.find({}, {_id: 1, name: 1, email: 1})
```

## Common Workflows

### Workflow 1: User Preference Updates

```bash
# Update preferences
curl -X PUT http://localhost:8000/api/users/{userId}/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "categories": ["food", "cultural"],
      "tags": ["food-tour", "local-cuisine"],
      "min_rating": 4.5,
      "max_price": 120
    }
  }'

# Generate new recommendations with updated preferences
curl -X POST http://localhost:8000/api/recommendations/users/{userId}/generate
```

### Workflow 2: Weekly Planning

```bash
# Get recommendations for a week
curl "http://localhost:8000/api/recommendations/users/{userId}/range?start_date=2024-01-20&end_date=2024-01-26"
```

### Workflow 3: Add New Tour

```bash
curl -X POST http://localhost:8000/api/tours \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Coffee Shop Tour",
    "description": "Visit the best coffee shops in the city",
    "location": "Downtown",
    "duration": 150,
    "category": "food",
    "tags": ["coffee", "food-tour", "urban"],
    "rating": 4.7,
    "price": 45,
    "capacity": 8,
    "coordinates": [40.7228, -74.0060]
  }'
```

## Configuration Options

### Change Optimization Algorithm

Edit `.env`:

```env
# Options: greedy, genetic, dynamic
RECOMMENDATION_OPTIMIZATION_ALGORITHM=greedy
```

- **greedy**: Fast, good for real-time requests
- **genetic**: Best quality, slower (good for batch processing)
- **dynamic**: Balanced approach

### Adjust Tour Limits

```env
# Maximum tours per day
RECOMMENDATION_MAX_TOURS_PER_DAY=5

# Time slot duration (minutes)
RECOMMENDATION_TIME_SLOT_DURATION=60
```

### Change Working Hours

Edit `config/recommendation.php`:

```php
'working_hours' => [
    'start' => '09:00',  // Start tours at 9 AM
    'end' => '18:00',    // End tours by 6 PM
],
```

## Viewing Data in MongoDB

```bash
# Connect to MongoDB
mongosh

# Switch to database
use travel_recommendation

# View users
db.users.find().pretty()

# View tours
db.tours.find().pretty()

# View recommendations
db.recommendations.find().pretty()

# Count documents
db.tours.countDocuments()

# Find tours by category
db.tours.find({ category: "adventure" }).pretty()
```

## Next Steps

1. **Read the full documentation**: See `README.md` for detailed features
2. **API Documentation**: Check `API_DOCUMENTATION.md` for all endpoints
3. **MongoDB Setup**: Review `MONGODB_SETUP.md` for advanced database configuration
4. **Deployment**: See `DEPLOYMENT.md` when ready to deploy to production

## Troubleshooting

### MongoDB Connection Error

```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod
```

### Composer Install Fails

```bash
# Update Composer
composer self-update

# Clear cache and retry
composer clear-cache
composer install
```

### Permission Errors

```bash
# Fix storage permissions
chmod -R 775 storage bootstrap/cache
```

### Port 8000 Already in Use

```bash
# Use a different port
php artisan serve --port=8080
```

## Getting Help

- Check the documentation files in the repository
- Review Laravel documentation: https://laravel.com/docs
- MongoDB PHP documentation: https://www.mongodb.com/docs/drivers/php/
- Open an issue on GitHub for bugs or questions

## Example Postman Collection

For easier testing, import this collection to Postman:

```json
{
  "info": {
    "name": "Travel Recommendation API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Create User",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\"name\":\"Test User\",\"email\":\"test@example.com\",\"password\":\"password123\",\"preferences\":{\"categories\":[\"adventure\"],\"tags\":[\"hiking\"]}}"
        },
        "url": "http://localhost:8000/api/users"
      }
    },
    {
      "name": "Generate Recommendations",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\"date\":\"2024-01-20\"}"
        },
        "url": "http://localhost:8000/api/recommendations/users/{{userId}}/generate"
      }
    },
    {
      "name": "Get Tours",
      "request": {
        "method": "GET",
        "url": "http://localhost:8000/api/tours"
      }
    }
  ]
}
```

Save this to a file and import in Postman for quick API testing!
