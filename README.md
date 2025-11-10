# Travel Recommendation System

A Laravel-based tour recommendation system that generates personalized daily tour schedules using MongoDB and advanced scheduling optimization algorithms.

## Features

- **MongoDB Integration**: Uses MongoDB for flexible data storage
- **User Preference Management**: Store and manage user preferences for personalized recommendations
- **Tour Management**: CRUD operations for tours with detailed information
- **Scheduling Optimization**: Three optimization algorithms:
  - Greedy Algorithm (fast, good results)
  - Genetic Algorithm (best results, slower)
  - Dynamic Programming (balanced approach)
- **Time-based Scheduling**: Optimizes tours based on time slots, travel time, and working hours
- **RESTful API**: Complete API for integration with frontend applications

## Requirements

- PHP >= 8.1
- MongoDB >= 4.0
- Composer
- Laravel 10.x

## Installation

1. Clone the repository:
```bash
git clone https://github.com/phoebe497/Travel-Recommendation.git
cd Travel-Recommendation
```

2. Install dependencies:
```bash
composer install
```

3. Configure environment:
```bash
cp .env.example .env
```

4. Update `.env` file with your MongoDB credentials:
```env
DB_CONNECTION=mongodb
DB_HOST=127.0.0.1
DB_PORT=27017
DB_DATABASE=travel_recommendation
DB_USERNAME=
DB_PASSWORD=
```

5. Generate application key:
```bash
php artisan key:generate
```

6. Seed the database with sample data:
```bash
php artisan db:seed
```

## Configuration

### Recommendation Settings

Edit `config/recommendation.php` to customize:

- `time_slot_duration`: Duration of time slots in minutes (default: 60)
- `max_tours_per_day`: Maximum tours per day (default: 5)
- `optimization_algorithm`: Algorithm to use (`genetic`, `greedy`, or `dynamic`)
- `scoring_weights`: Weights for different scoring factors
- `working_hours`: Start and end times for tour scheduling

### Environment Variables

```env
RECOMMENDATION_TIME_SLOT_DURATION=60
RECOMMENDATION_MAX_TOURS_PER_DAY=5
RECOMMENDATION_OPTIMIZATION_ALGORITHM=genetic
```

## API Endpoints

### Users

- `POST /api/users` - Create a new user
- `GET /api/users/{id}` - Get user profile
- `GET /api/users/{id}/preferences` - Get user preferences
- `PUT /api/users/{id}/preferences` - Update user preferences

### Tours

- `GET /api/tours` - List all tours (with filters)
- `POST /api/tours` - Create a new tour
- `GET /api/tours/{id}` - Get tour details
- `PUT /api/tours/{id}` - Update tour
- `DELETE /api/tours/{id}` - Delete tour

### Recommendations

- `GET /api/recommendations/users/{userId}` - Get daily recommendations
- `POST /api/recommendations/users/{userId}/generate` - Generate new recommendations
- `GET /api/recommendations/users/{userId}/range` - Get recommendations for date range

## Usage Examples

### Create a User with Preferences

```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123",
    "preferences": {
      "categories": ["adventure", "nature"],
      "tags": ["hiking", "photography"],
      "min_rating": 4.0,
      "max_price": 100
    }
  }'
```

### Get Daily Recommendations

```bash
curl -X GET "http://localhost:8000/api/recommendations/users/{userId}?date=2024-01-15"
```

### Generate New Recommendations

```bash
curl -X POST "http://localhost:8000/api/recommendations/users/{userId}/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2024-01-15"
  }'
```

### Get Recommendations for Date Range

```bash
curl -X GET "http://localhost:8000/api/recommendations/users/{userId}/range?start_date=2024-01-15&end_date=2024-01-22"
```

### Update User Preferences

```bash
curl -X PUT http://localhost:8000/api/users/{userId}/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "preferences": {
      "categories": ["food", "cultural"],
      "tags": ["food-tour", "museums"],
      "min_rating": 4.5
    }
  }'
```

## Recommendation Algorithm

The system uses a multi-step process to generate recommendations:

1. **Tour Scoring**: Each tour is scored based on:
   - User preference match (40%)
   - Tour rating (20%)
   - Distance efficiency (20%)
   - Time optimization (20%)

2. **Schedule Optimization**: Tours are arranged into an optimal daily schedule using one of three algorithms:
   - **Greedy**: Quick scheduling based on highest scores
   - **Genetic**: Evolutionary algorithm for optimal solutions
   - **Dynamic Programming**: Balanced approach for good results

3. **Time Management**: 
   - Considers tour duration
   - Calculates travel time between locations
   - Respects working hours (default: 8:00 AM - 8:00 PM)
   - Optimizes for minimal idle time

## Database Schema

### Users Collection
```javascript
{
  _id: ObjectId,
  name: String,
  email: String,
  password: String,
  preferences: {
    categories: Array,
    tags: Array,
    min_rating: Number,
    max_price: Number,
    preferred_duration: Number
  }
}
```

### Tours Collection
```javascript
{
  _id: ObjectId,
  name: String,
  description: String,
  location: String,
  duration: Number,
  category: String,
  tags: Array,
  rating: Number,
  price: Number,
  capacity: Number,
  coordinates: [Number, Number],
  images: Array
}
```

### Recommendations Collection
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  date: Date,
  schedule: [{
    tour_id: ObjectId,
    tour_name: String,
    start_time: String,
    end_time: String,
    duration: Number,
    travel_time: Number,
    score: Number
  }],
  score: Number,
  metadata: Object
}
```

## Development

### Running the Application

```bash
php artisan serve
```

The application will be available at `http://localhost:8000`

### Testing

```bash
php artisan test
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Architecture

### Service Layer
- `RecommendationService`: Core recommendation logic and optimization algorithms
- Handles scoring, scheduling, and caching of recommendations

### Models
- `User`: User management and preferences
- `Tour`: Tour information and utilities
- `Recommendation`: Stored recommendations with schedules

### Controllers
- `UserController`: User management endpoints
- `TourController`: Tour CRUD operations
- `RecommendationController`: Recommendation generation and retrieval

## Performance Considerations

- Recommendations are cached for 60 minutes by default
- Genetic algorithm may take longer for large tour datasets
- Consider using the greedy algorithm for real-time requests
- Use batch generation for multiple days

## Future Enhancements

- Real-time traffic data integration
- Weather-based recommendations
- Social features (group tours, reviews)
- Machine learning-based preference learning
- Mobile app integration
- Payment gateway integration