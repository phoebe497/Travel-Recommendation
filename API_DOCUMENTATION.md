# API Documentation

## Base URL
```
http://localhost:8000/api
```

## Authentication
Currently, the API does not require authentication. This can be added in future versions.

## Response Format
All responses are in JSON format.

Success Response:
```json
{
  "data": {},
  "message": "Success message"
}
```

Error Response:
```json
{
  "error": "Error message"
}
```

---

## Users API

### Create User
**POST** `/users`

Create a new user account with preferences.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "password123",
  "preferences": {
    "categories": ["adventure", "nature"],
    "tags": ["hiking", "photography"],
    "min_rating": 4.0,
    "max_price": 100,
    "preferred_duration": 120
  }
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "user": {
    "id": "60d5ec49f1b2c8b5e8e4b1a1",
    "name": "John Doe",
    "email": "john@example.com",
    "preferences": {
      "categories": ["adventure", "nature"],
      "tags": ["hiking", "photography"],
      "min_rating": 4.0
    }
  }
}
```

### Get User
**GET** `/users/{id}`

Retrieve user profile information.

**Response:**
```json
{
  "id": "60d5ec49f1b2c8b5e8e4b1a1",
  "name": "John Doe",
  "email": "john@example.com",
  "preferences": {
    "categories": ["adventure", "nature"],
    "tags": ["hiking", "photography"]
  }
}
```

### Get User Preferences
**GET** `/users/{id}/preferences`

Get user's preferences.

**Response:**
```json
{
  "preferences": {
    "categories": ["adventure", "nature"],
    "tags": ["hiking", "photography"],
    "min_rating": 4.0,
    "max_price": 100
  }
}
```

### Update User Preferences
**PUT** `/users/{id}/preferences`

Update user's preferences.

**Request Body:**
```json
{
  "preferences": {
    "categories": ["food", "cultural"],
    "tags": ["food-tour", "museums"],
    "min_rating": 4.5,
    "max_price": 150
  }
}
```

**Response:**
```json
{
  "message": "Preferences updated successfully",
  "preferences": {
    "categories": ["food", "cultural"],
    "tags": ["food-tour", "museums"],
    "min_rating": 4.5
  }
}
```

---

## Tours API

### List Tours
**GET** `/tours`

Get all tours with optional filters.

**Query Parameters:**
- `category` (string): Filter by category
- `min_rating` (number): Minimum rating
- `tags` (string or array): Filter by tags

**Example:**
```
GET /tours?category=adventure&min_rating=4.0
```

**Response:**
```json
{
  "tours": [
    {
      "_id": "60d5ec49f1b2c8b5e8e4b1a2",
      "name": "Mountain Hiking Adventure",
      "description": "Challenging hike with breathtaking views",
      "location": "Blue Mountains",
      "duration": 240,
      "category": "adventure",
      "tags": ["hiking", "nature"],
      "rating": 4.8,
      "price": 75,
      "capacity": 10,
      "coordinates": [40.8128, -74.1060]
    }
  ],
  "total": 1
}
```

### Get Tour
**GET** `/tours/{id}`

Get details of a specific tour.

**Response:**
```json
{
  "_id": "60d5ec49f1b2c8b5e8e4b1a2",
  "name": "Mountain Hiking Adventure",
  "description": "Challenging hike with breathtaking views",
  "location": "Blue Mountains",
  "duration": 240,
  "category": "adventure",
  "tags": ["hiking", "nature"],
  "rating": 4.8,
  "price": 75,
  "capacity": 10,
  "coordinates": [40.8128, -74.1060]
}
```

### Create Tour
**POST** `/tours`

Create a new tour.

**Request Body:**
```json
{
  "name": "City Walking Tour",
  "description": "Explore the historic downtown",
  "location": "Downtown",
  "duration": 120,
  "category": "cultural",
  "tags": ["walking", "history"],
  "rating": 4.5,
  "price": 30,
  "capacity": 15,
  "coordinates": [40.7128, -74.0060]
}
```

**Response:**
```json
{
  "message": "Tour created successfully",
  "tour": {
    "_id": "60d5ec49f1b2c8b5e8e4b1a3",
    "name": "City Walking Tour",
    ...
  }
}
```

### Update Tour
**PUT** `/tours/{id}`

Update an existing tour.

**Request Body:**
```json
{
  "name": "Updated Tour Name",
  "price": 35,
  "rating": 4.6
}
```

**Response:**
```json
{
  "message": "Tour updated successfully",
  "tour": {
    "_id": "60d5ec49f1b2c8b5e8e4b1a3",
    "name": "Updated Tour Name",
    ...
  }
}
```

### Delete Tour
**DELETE** `/tours/{id}`

Delete a tour.

**Response:**
```json
{
  "message": "Tour deleted successfully"
}
```

---

## Recommendations API

### Get Daily Recommendations
**GET** `/recommendations/users/{userId}`

Get recommendations for a specific date.

**Query Parameters:**
- `date` (string, optional): Date in YYYY-MM-DD format. Defaults to today.

**Example:**
```
GET /recommendations/users/60d5ec49f1b2c8b5e8e4b1a1?date=2024-01-15
```

**Response:**
```json
{
  "user_id": "60d5ec49f1b2c8b5e8e4b1a1",
  "date": "2024-01-15",
  "schedule": [
    {
      "tour_id": "60d5ec49f1b2c8b5e8e4b1a2",
      "tour_name": "City Walking Tour",
      "start_time": "08:00",
      "end_time": "10:00",
      "duration": 120,
      "travel_time": 0,
      "score": 0.85
    },
    {
      "tour_id": "60d5ec49f1b2c8b5e8e4b1a3",
      "tour_name": "Mountain Hiking Adventure",
      "start_time": "10:30",
      "end_time": "14:30",
      "duration": 240,
      "travel_time": 30,
      "score": 0.92
    }
  ],
  "score": 0.88,
  "metadata": {
    "generated_at": "2024-01-14T10:30:00.000000Z",
    "algorithm": "genetic"
  }
}
```

### Generate Recommendations
**POST** `/recommendations/users/{userId}/generate`

Force generation of new recommendations (bypasses cache).

**Request Body:**
```json
{
  "date": "2024-01-15"
}
```

**Response:**
```json
{
  "message": "Recommendations generated successfully",
  "user_id": "60d5ec49f1b2c8b5e8e4b1a1",
  "date": "2024-01-15",
  "schedule": [...],
  "score": 0.88,
  "metadata": {...}
}
```

### Get Recommendations Range
**GET** `/recommendations/users/{userId}/range`

Get recommendations for a date range (up to 30 days).

**Query Parameters:**
- `start_date` (string): Start date in YYYY-MM-DD format
- `end_date` (string): End date in YYYY-MM-DD format

**Example:**
```
GET /recommendations/users/60d5ec49f1b2c8b5e8e4b1a1/range?start_date=2024-01-15&end_date=2024-01-22
```

**Response:**
```json
{
  "user_id": "60d5ec49f1b2c8b5e8e4b1a1",
  "start_date": "2024-01-15",
  "end_date": "2024-01-22",
  "recommendations": [
    {
      "date": "2024-01-15",
      "schedule": [...],
      "score": 0.88
    },
    {
      "date": "2024-01-16",
      "schedule": [...],
      "score": 0.91
    }
  ]
}
```

---

## Error Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Recommendation Scoring

The recommendation algorithm scores tours based on:

1. **User Preference Match (40%)**: How well the tour matches user's preferred categories and tags
2. **Rating (20%)**: The tour's rating (0-5 stars)
3. **Distance Efficiency (20%)**: Minimizes travel time between tours
4. **Time Optimization (20%)**: Maximizes useful tour time within working hours

## Optimization Algorithms

Three algorithms are available (configured in `.env`):

1. **Greedy (Default)**: Fast, selects highest-scoring tours that fit the schedule
2. **Genetic**: Uses evolutionary algorithm for optimal tour combinations
3. **Dynamic Programming**: Balances speed and quality for interval scheduling

## Rate Limiting

Currently not implemented. Can be added using Laravel's rate limiting middleware.

## Pagination

List endpoints support pagination (to be implemented):
- `page`: Page number
- `per_page`: Items per page (default: 20, max: 100)
