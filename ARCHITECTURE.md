# System Architecture

## Overview

The Travel Recommendation System is built using a layered architecture pattern with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│  (Web Apps, Mobile Apps, Third-party Integrations)              │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/JSON
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API Layer (Routes)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ User Routes  │  │ Tour Routes  │  │ Rec. Routes  │         │
│  │ /api/users   │  │ /api/tours   │  │/api/recommend│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Controller Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │    User      │  │    Tour      │  │Recommendation│         │
│  │ Controller   │  │ Controller   │  │  Controller  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Service Layer                                │
│  ┌─────────────────────────────────────────────────┐            │
│  │      RecommendationService                      │            │
│  │  ┌──────────────────────────────────────────┐  │            │
│  │  │  Scoring Engine                          │  │            │
│  │  │  - Preference matching                   │  │            │
│  │  │  - Rating calculation                    │  │            │
│  │  │  - Distance optimization                 │  │            │
│  │  └──────────────────────────────────────────┘  │            │
│  │  ┌──────────────────────────────────────────┐  │            │
│  │  │  Optimization Algorithms                 │  │            │
│  │  │  - Greedy Algorithm                      │  │            │
│  │  │  - Genetic Algorithm                     │  │            │
│  │  │  - Dynamic Programming                   │  │            │
│  │  └──────────────────────────────────────────┘  │            │
│  │  ┌──────────────────────────────────────────┐  │            │
│  │  │  Scheduling Engine                       │  │            │
│  │  │  - Time slot management                  │  │            │
│  │  │  - Travel time calculation               │  │            │
│  │  │  - Working hours constraints             │  │            │
│  │  └──────────────────────────────────────────┘  │            │
│  └─────────────────────────────────────────────────┘            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Model Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  User Model  │  │  Tour Model  │  │Recommendation│         │
│  │              │  │              │  │    Model     │         │
│  │ - Attributes │  │ - Attributes │  │ - Attributes │         │
│  │ - Methods    │  │ - Methods    │  │ - Methods    │         │
│  │ - Relations  │  │ - Relations  │  │ - Relations  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database Layer                                │
│  ┌─────────────────────────────────────────────────┐            │
│  │              MongoDB Database                   │            │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │            │
│  │  │  users   │  │  tours   │  │recommendations││            │
│  │  │collection│  │collection│  │  collection   ││            │
│  │  └──────────┘  └──────────┘  └──────────────┘ │            │
│  └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Client Layer
- Web applications (Laravel Blade, React, Vue)
- Mobile applications (iOS, Android)
- Third-party integrations
- API consumers

**Communication**: RESTful JSON API over HTTP/HTTPS

### 2. API Layer (Routes)
**Location**: `routes/api.php`

**Responsibilities**:
- Route definitions
- Request routing
- Middleware application

**Endpoints**:
- `/api/users/*` - User management
- `/api/tours/*` - Tour management
- `/api/recommendations/*` - Recommendation services

### 3. Controller Layer
**Location**: `app/Http/Controllers/`

**Components**:
- **UserController**: User CRUD and preference management
- **TourController**: Tour CRUD and filtering
- **RecommendationController**: Recommendation generation and retrieval

**Responsibilities**:
- Request validation
- Input processing
- Response formatting
- Error handling

### 4. Service Layer
**Location**: `app/Services/`

**Main Component**: `RecommendationService`

#### Scoring Engine
- Calculates tour scores based on user preferences
- Applies configurable weights
- Considers multiple factors

#### Optimization Algorithms

**Greedy Algorithm**:
```
Input: Scored tours, Date
Output: Optimized schedule

1. Sort tours by score (descending)
2. Initialize empty schedule
3. Set current time to working hours start
4. For each tour in sorted list:
   - Calculate travel time from last location
   - Check if tour fits in remaining time
   - If yes, add to schedule
   - Update current time
5. Return schedule
```

**Genetic Algorithm**:
```
Input: Scored tours, Date, Population size, Generations
Output: Best schedule

1. Create initial population of random schedules
2. For each generation:
   - Evaluate fitness of all schedules
   - Select parents using tournament selection
   - Create offspring through crossover
   - Apply mutation
   - Replace old population
3. Return best schedule from final population
```

**Dynamic Programming**:
```
Input: Scored tours, Date
Output: Optimized schedule

1. Create time slot array
2. For each tour:
   - Find best available time slot
   - Mark slots as occupied
3. Return schedule
```

#### Scheduling Engine
- Manages time slots
- Calculates travel times (Haversine formula)
- Enforces working hours
- Optimizes time efficiency

### 5. Model Layer
**Location**: `app/Models/`

**User Model**:
```
Attributes:
- _id: ObjectId
- name: String
- email: String (unique)
- password: String (hashed)
- preferences: Array

Methods:
- getPreferences()
- updatePreferences()
- recommendations()
```

**Tour Model**:
```
Attributes:
- _id: ObjectId
- name: String
- description: String
- location: String
- duration: Integer (minutes)
- category: String
- tags: Array
- rating: Float
- price: Float
- capacity: Integer
- coordinates: Array [lat, lng]

Methods:
- matchesPreferences(preferences): Float
- distanceTo(target): Float
```

**Recommendation Model**:
```
Attributes:
- _id: ObjectId
- user_id: ObjectId
- date: DateTime
- schedule: Array
- score: Float
- metadata: Object

Methods:
- user()
- getTours()
- addTour()
```

### 6. Database Layer
**Technology**: MongoDB

**Collections**:

**users**:
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
    max_price: Number
  }
}
```

**tours**:
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
  coordinates: [Number, Number]
}
```

**recommendations**:
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

## Data Flow

### Recommendation Generation Flow

```
1. Client Request
   POST /api/recommendations/users/{userId}/generate
   Body: { date: "2024-01-20" }
   
2. Route → Controller
   RecommendationController::generateRecommendations()
   
3. Controller → Service
   RecommendationService::generateDailyRecommendations(user, date)
   
4. Service Operations:
   a. Fetch all tours from database
   b. Score tours based on user preferences
   c. Select optimization algorithm
   d. Generate optimized schedule
   e. Calculate overall score
   f. Save recommendation to database
   
5. Service → Controller
   Return Recommendation object
   
6. Controller → Client
   JSON response with schedule
```

### Preference Update Flow

```
1. Client Request
   PUT /api/users/{userId}/preferences
   Body: { preferences: {...} }
   
2. Route → Controller
   UserController::updatePreferences()
   
3. Controller → Model
   User::updatePreferences(preferences)
   
4. Model → Database
   Save updated preferences
   
5. Database → Model → Controller → Client
   Success response
```

## Configuration

### Environment Variables
```
DB_CONNECTION=mongodb
DB_HOST=127.0.0.1
DB_PORT=27017
DB_DATABASE=travel_recommendation

RECOMMENDATION_TIME_SLOT_DURATION=60
RECOMMENDATION_MAX_TOURS_PER_DAY=5
RECOMMENDATION_OPTIMIZATION_ALGORITHM=genetic
```

### Config Files
- `config/database.php` - Database settings
- `config/app.php` - Application settings
- `config/recommendation.php` - Algorithm settings

## Scalability Considerations

### Horizontal Scaling
```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  App    │     │  App    │     │  App    │
│ Server 1│     │ Server 2│     │ Server 3│
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
     └───────────────┴───────────────┘
                     │
              ┌──────┴──────┐
              │Load Balancer│
              └──────┬──────┘
                     │
         ┌───────────┴───────────┐
         │                       │
    ┌────┴────┐           ┌─────┴─────┐
    │ MongoDB │           │   Redis   │
    │ Replica │           │   Cache   │
    │   Set   │           └───────────┘
    └─────────┘
```

### Caching Strategy
- Recommendation caching (60 minutes default)
- Tour data caching
- User preference caching
- Redis integration ready

### Performance Optimization
- Database indexing
- Query optimization
- Algorithm selection based on use case
- Asynchronous processing for batch operations

## Security Architecture

### Layers of Security
1. **Transport Layer**: HTTPS only in production
2. **Authentication**: Ready for JWT/Passport integration
3. **Authorization**: Role-based access (future)
4. **Input Validation**: Laravel validation rules
5. **Database**: MongoDB authentication
6. **Environment**: Sensitive data in .env

## Monitoring & Logging

### Application Logs
- Location: `storage/logs/laravel.log`
- Level: Configurable (debug, info, warning, error)

### Database Logs
- Location: `/var/log/mongodb/mongod.log`
- Monitoring: Connection, queries, performance

### Performance Metrics
- Request duration
- Algorithm execution time
- Database query time
- Cache hit/miss ratio

## Deployment Architecture

### Development
```
Developer Machine
├── PHP 8.1+
├── MongoDB (local)
└── Laravel Development Server
```

### Production
```
┌─────────────────────────────┐
│     Load Balancer (Nginx)   │
└──────────────┬──────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼───┐             ┌───▼───┐
│  App  │             │  App  │
│Server1│             │Server2│
└───┬───┘             └───┬───┘
    │                     │
    └──────────┬──────────┘
               │
         ┌─────▼─────┐
         │  MongoDB  │
         │ Replica   │
         │   Set     │
         └───────────┘
```

## Technology Stack

- **Framework**: Laravel 10.x
- **Language**: PHP 8.1+
- **Database**: MongoDB 4.0+
- **Package Manager**: Composer
- **Testing**: PHPUnit
- **Web Server**: Nginx/Apache
- **Cache**: File/Redis
- **Queue**: Sync/Redis (future)

## Integration Points

### Internal
- Models ↔ Services
- Services ↔ Controllers
- Controllers ↔ Routes

### External (Future)
- Weather APIs
- Traffic APIs
- Payment Gateways
- Email Services
- SMS Services
- Authentication Providers

## Best Practices Implemented

- ✅ Separation of Concerns
- ✅ Dependency Injection
- ✅ Repository Pattern (via Eloquent)
- ✅ Service Layer Pattern
- ✅ RESTful API Design
- ✅ Configuration Management
- ✅ Environment-based Settings
- ✅ Error Handling
- ✅ Input Validation
- ✅ Code Documentation
- ✅ Testing Infrastructure
