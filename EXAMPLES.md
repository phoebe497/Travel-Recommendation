# Example Usage Scenarios

This document provides real-world examples of using the Travel Recommendation System.

## Scenario 1: Travel Agency Integration

A travel agency wants to provide personalized daily tour recommendations for their customers.

### Step 1: Register Customers

```php
// Using PHP
$ch = curl_init('http://localhost:8000/api/users');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode([
    'name' => 'Sarah Johnson',
    'email' => 'sarah.j@example.com',
    'password' => 'secure_password',
    'preferences' => [
        'categories' => ['nature', 'adventure', 'photography'],
        'tags' => ['hiking', 'wildlife', 'scenic-views'],
        'min_rating' => 4.5,
        'max_price' => 150,
        'preferred_duration' => 180
    ]
]));

$response = curl_exec($ch);
$userData = json_decode($response, true);
$userId = $userData['user']['id'];
```

### Step 2: Generate Weekly Itinerary

```php
// Generate recommendations for the next 7 days
$startDate = date('Y-m-d');
$endDate = date('Y-m-d', strtotime('+7 days'));

$ch = curl_init("http://localhost:8000/api/recommendations/users/{$userId}/range?start_date={$startDate}&end_date={$endDate}");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$response = curl_exec($ch);
$weeklyPlan = json_decode($response, true);

// Display the itinerary
foreach ($weeklyPlan['recommendations'] as $day) {
    echo "Date: " . $day['date'] . "\n";
    echo "Tours planned: " . count($day['schedule']) . "\n";
    
    foreach ($day['schedule'] as $tour) {
        echo "  - {$tour['tour_name']}: {$tour['start_time']} - {$tour['end_time']}\n";
    }
    echo "\n";
}
```

## Scenario 2: Mobile App Integration

A mobile app wants to show today's recommended tours.

### JavaScript/React Example

```javascript
// API Service
class TravelRecommendationAPI {
  constructor(baseURL = 'http://localhost:8000/api') {
    this.baseURL = baseURL;
  }

  async createUser(userData) {
    const response = await fetch(`${this.baseURL}/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    return response.json();
  }

  async getDailyRecommendations(userId, date = null) {
    const dateParam = date ? `?date=${date}` : '';
    const response = await fetch(
      `${this.baseURL}/recommendations/users/${userId}${dateParam}`
    );
    return response.json();
  }

  async updatePreferences(userId, preferences) {
    const response = await fetch(
      `${this.baseURL}/users/${userId}/preferences`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preferences })
      }
    );
    return response.json();
  }

  async getTours(filters = {}) {
    const params = new URLSearchParams(filters);
    const response = await fetch(`${this.baseURL}/tours?${params}`);
    return response.json();
  }
}

// React Component Example
function TodaysTours({ userId }) {
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const api = new TravelRecommendationAPI();

  useEffect(() => {
    async function fetchRecommendations() {
      try {
        const data = await api.getDailyRecommendations(userId);
        setRecommendations(data);
      } catch (error) {
        console.error('Failed to fetch recommendations:', error);
      } finally {
        setLoading(false);
      }
    }
    
    fetchRecommendations();
  }, [userId]);

  if (loading) return <div>Loading your personalized tours...</div>;

  return (
    <div className="recommendations">
      <h2>Your Tours for {recommendations.date}</h2>
      <div className="score">
        Optimization Score: {(recommendations.score * 100).toFixed(0)}%
      </div>
      
      <div className="tour-schedule">
        {recommendations.schedule.map((tour, index) => (
          <div key={index} className="tour-card">
            <h3>{tour.tour_name}</h3>
            <p>⏰ {tour.start_time} - {tour.end_time}</p>
            <p>⏱️ Duration: {tour.duration} minutes</p>
            {tour.travel_time > 0 && (
              <p>🚗 Travel time: {tour.travel_time} minutes</p>
            )}
            <p>⭐ Match Score: {(tour.score * 100).toFixed(0)}%</p>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Scenario 3: Tour Operator Dashboard

Tour operators want to add new tours and see which users they match.

### Add New Tour

```python
import requests
import json

API_BASE = 'http://localhost:8000/api'

def add_tour(tour_data):
    """Add a new tour to the system"""
    response = requests.post(
        f'{API_BASE}/tours',
        headers={'Content-Type': 'application/json'},
        json=tour_data
    )
    return response.json()

# Example: Add a wine tasting tour
new_tour = {
    'name': 'Vineyard Wine Tasting Experience',
    'description': 'Visit three premium vineyards and taste award-winning wines',
    'location': 'Napa Valley',
    'duration': 240,  # 4 hours
    'category': 'food',
    'tags': ['wine', 'tasting', 'gourmet', 'relaxation'],
    'rating': 4.9,
    'price': 125,
    'capacity': 12,
    'coordinates': [38.2975, -122.2869],  # Napa Valley coordinates
    'images': [
        'https://example.com/vineyard1.jpg',
        'https://example.com/winery.jpg'
    ],
    'available_time_slots': ['10:00', '14:00']
}

result = add_tour(new_tour)
print(f"Tour created with ID: {result['tour']['_id']}")
```

### Update Tour Information

```python
def update_tour(tour_id, updates):
    """Update tour details"""
    response = requests.put(
        f'{API_BASE}/tours/{tour_id}',
        headers={'Content-Type': 'application/json'},
        json=updates
    )
    return response.json()

# Update tour rating and price
updates = {
    'rating': 5.0,
    'price': 135
}

result = update_tour(tour_id, updates)
print(f"Tour updated: {result['message']}")
```

## Scenario 4: Batch Processing for Hotels

A hotel wants to generate recommendations for all guests checking in tomorrow.

### Python Batch Script

```python
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

API_BASE = 'http://localhost:8000/api'

def generate_recommendation(user_id, date):
    """Generate recommendation for a single user"""
    try:
        response = requests.post(
            f'{API_BASE}/recommendations/users/{user_id}/generate',
            headers={'Content-Type': 'application/json'},
            json={'date': date}
        )
        return {
            'user_id': user_id,
            'success': response.status_code == 200,
            'data': response.json()
        }
    except Exception as e:
        return {
            'user_id': user_id,
            'success': False,
            'error': str(e)
        }

def batch_generate_recommendations(user_ids, date):
    """Generate recommendations for multiple users in parallel"""
    results = []
    
    # Use thread pool for parallel processing
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user = {
            executor.submit(generate_recommendation, uid, date): uid 
            for uid in user_ids
        }
        
        for future in as_completed(future_to_user):
            result = future.result()
            results.append(result)
            
            if result['success']:
                print(f"✓ Generated for user {result['user_id']}")
            else:
                print(f"✗ Failed for user {result['user_id']}: {result.get('error')}")
    
    return results

# Example: Generate for tomorrow
tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
guest_user_ids = ['user_id_1', 'user_id_2', 'user_id_3', ...]  # From hotel system

results = batch_generate_recommendations(guest_user_ids, tomorrow)

# Summary
success_count = sum(1 for r in results if r['success'])
print(f"\nProcessed {len(results)} guests")
print(f"Successful: {success_count}")
print(f"Failed: {len(results) - success_count}")
```

## Scenario 5: Preference Learning System

Analyze user behavior and update preferences automatically.

```python
def analyze_and_update_preferences(user_id):
    """
    Analyze user's past tours and update preferences
    This is a simplified example - in production, use ML
    """
    # Get user's past recommendations
    # (Note: You'd need to implement a history endpoint for this)
    
    # Simulated analysis
    preferred_categories = ['adventure', 'nature']
    preferred_tags = ['hiking', 'wildlife', 'photography']
    
    # Update preferences
    response = requests.put(
        f'{API_BASE}/users/{user_id}/preferences',
        headers={'Content-Type': 'application/json'},
        json={
            'preferences': {
                'categories': preferred_categories,
                'tags': preferred_tags,
                'min_rating': 4.5
            }
        }
    )
    
    return response.json()
```

## Scenario 6: Frontend Laravel Integration

Integrate with Laravel Blade templates.

```php
// app/Http/Controllers/WebRecommendationController.php
namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Models\User;
use App\Services\RecommendationService;
use Carbon\Carbon;

class WebRecommendationController extends Controller
{
    protected $recommendationService;

    public function __construct(RecommendationService $recommendationService)
    {
        $this->recommendationService = $recommendationService;
    }

    public function showDashboard(Request $request)
    {
        // Assuming user is authenticated
        $user = auth()->user();
        $date = $request->get('date', Carbon::today());
        
        $recommendations = $this->recommendationService
            ->getOrGenerateRecommendations($user, $date);
        
        return view('dashboard', [
            'recommendations' => $recommendations,
            'date' => $date,
            'user' => $user
        ]);
    }
}
```

```blade
{{-- resources/views/dashboard.blade.php --}}
@extends('layouts.app')

@section('content')
<div class="container">
    <h1>Your Tour Recommendations</h1>
    <h2>{{ $date->format('l, F j, Y') }}</h2>
    
    <div class="recommendation-score">
        <strong>Optimization Score:</strong> 
        {{ number_format($recommendations->score * 100, 0) }}%
    </div>

    <div class="tour-timeline">
        @foreach($recommendations->schedule as $tour)
        <div class="tour-item">
            <div class="tour-time">
                <span class="start">{{ $tour['start_time'] }}</span>
                <span class="separator">-</span>
                <span class="end">{{ $tour['end_time'] }}</span>
            </div>
            <div class="tour-details">
                <h3>{{ $tour['tour_name'] }}</h3>
                <p class="duration">Duration: {{ $tour['duration'] }} minutes</p>
                @if($tour['travel_time'] > 0)
                    <p class="travel">Travel time: {{ $tour['travel_time'] }} minutes</p>
                @endif
                <div class="score-badge">
                    Match: {{ number_format($tour['score'] * 100, 0) }}%
                </div>
            </div>
        </div>
        @endforeach
    </div>

    <div class="actions">
        <a href="{{ route('recommendations.refresh') }}" class="btn btn-primary">
            Regenerate Recommendations
        </a>
        <a href="{{ route('preferences.edit') }}" class="btn btn-secondary">
            Update Preferences
        </a>
    </div>
</div>
@endsection
```

## Scenario 7: CLI Tool for Administrators

Create an artisan command for managing the system.

```php
// app/Console/Commands/GenerateDailyRecommendations.php
namespace App\Console\Commands;

use Illuminate\Console\Command;
use App\Models\User;
use App\Services\RecommendationService;
use Carbon\Carbon;

class GenerateDailyRecommendations extends Command
{
    protected $signature = 'recommendations:generate 
                            {--date= : The date to generate recommendations for}
                            {--user= : Specific user ID}
                            {--all : Generate for all users}';

    protected $description = 'Generate tour recommendations for users';

    protected $recommendationService;

    public function __construct(RecommendationService $recommendationService)
    {
        parent::__construct();
        $this->recommendationService = $recommendationService;
    }

    public function handle()
    {
        $date = $this->option('date') 
            ? Carbon::parse($this->option('date'))
            : Carbon::tomorrow();

        if ($this->option('all')) {
            $users = User::all();
            $this->info("Generating recommendations for {$users->count()} users...");
            
            $bar = $this->output->createProgressBar($users->count());
            
            foreach ($users as $user) {
                $this->recommendationService->generateDailyRecommendations($user, $date);
                $bar->advance();
            }
            
            $bar->finish();
            $this->info("\nCompleted!");
            
        } elseif ($userId = $this->option('user')) {
            $user = User::find($userId);
            
            if (!$user) {
                $this->error("User not found!");
                return 1;
            }
            
            $recommendation = $this->recommendationService
                ->generateDailyRecommendations($user, $date);
            
            $this->info("Generated recommendations for {$user->name}");
            $this->table(
                ['Time', 'Tour', 'Duration', 'Score'],
                collect($recommendation->schedule)->map(fn($t) => [
                    $t['start_time'] . ' - ' . $t['end_time'],
                    $t['tour_name'],
                    $t['duration'] . ' min',
                    number_format($t['score'] * 100, 0) . '%'
                ])
            );
        } else {
            $this->error("Please specify --all or --user=ID");
            return 1;
        }

        return 0;
    }
}
```

Usage:
```bash
# Generate for all users for tomorrow
php artisan recommendations:generate --all

# Generate for specific user
php artisan recommendations:generate --user=60d5ec49f1b2c8b5e8e4b1a1

# Generate for specific date
php artisan recommendations:generate --all --date=2024-02-14
```

## Best Practices

1. **Caching**: Recommendations are cached. Use `generate` endpoint to force refresh.
2. **Batch Processing**: Use parallel processing for multiple users.
3. **Error Handling**: Always handle API errors gracefully.
4. **Rate Limiting**: Implement rate limiting in production.
5. **Preference Updates**: Regenerate recommendations after updating preferences.
6. **Algorithm Selection**: Use greedy for real-time, genetic for batch jobs.

## Performance Tips

- Use the greedy algorithm for real-time requests
- Cache recommendations for frequently accessed dates
- Generate recommendations in advance (e.g., nightly batch job)
- Index MongoDB collections properly
- Use database connection pooling for high traffic
