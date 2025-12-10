# 🔗 Integration Guide for Web Developers

This guide helps you integrate the Smart Travel Recommendation API into your web application.

---

## Quick Start (5 minutes)

### 1. API Endpoint
```
POST http://your-api-server.com/api/v1/generate-itinerary
```

### 2. Minimal Example (Python Backend)
```python
import requests

def generate_itinerary(city, num_days, start_date):
    response = requests.post(
        "http://localhost:8000/api/v1/generate-itinerary",
        json={
            "city": city,
            "num_days": num_days,
            "start_date": start_date,
            "interests": ["culture", "food"],
            "budget": "medium"
        },
        timeout=60
    )
    return response.json()

# Usage
itinerary = generate_itinerary("Singapore", 3, "2025-12-20")
print(f"Total cost: ${itinerary['total_cost_usd']}")
```

---

## Integration Patterns

### Pattern 1: Replace Gemini API (Direct Replacement)

**Old Code (Gemini):**
```python
import google.generativeai as genai

def generate_itinerary_gemini(city, days):
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"Generate {days}-day itinerary for {city}"
    response = model.generate_content(prompt)
    return response.text  # Unstructured text
```

**New Code (ML API):**
```python
import requests

def generate_itinerary_ml(city, days, start_date):
    response = requests.post(
        "http://api-server/api/v1/generate-itinerary",
        json={
            "city": city,
            "num_days": days,
            "start_date": start_date
        },
        timeout=60
    )
    return response.json()  # Structured JSON
```

**Benefits:**
- ✅ Structured output (JSON instead of text)
- ✅ Consistent format (no parsing needed)
- ✅ Faster response (5-10s vs Gemini's variable time)
- ✅ Cost: Free (self-hosted) vs Gemini API pricing

---

### Pattern 2: Hybrid Approach (Fallback Strategy)

Use ML API as primary, Gemini as backup:

```python
def generate_itinerary_with_fallback(city, days, start_date):
    try:
        # Try ML API first
        response = requests.post(
            "http://api-server/api/v1/generate-itinerary",
            json={"city": city, "num_days": days, "start_date": start_date},
            timeout=60
        )
        response.raise_for_status()
        return {"source": "ml", "data": response.json()}
    
    except requests.exceptions.Timeout:
        # Fallback to Gemini if ML API is slow
        print("ML API timeout, falling back to Gemini")
        return {"source": "gemini", "data": generate_gemini_fallback(city, days)}
    
    except Exception as e:
        print(f"ML API error: {e}, using Gemini")
        return {"source": "gemini", "data": generate_gemini_fallback(city, days)}
```

---

## Full Integration Example (Flask Backend)

```python
# backend/services/itinerary_service.py
import requests
from typing import Dict, List
from datetime import date

class ItineraryService:
    def __init__(self, api_url: str, api_key: str = None):
        self.api_url = api_url
        self.api_key = api_key
    
    def generate_itinerary(
        self,
        city: str,
        num_days: int,
        start_date: date,
        interests: List[str] = None,
        budget: str = "medium",
        travel_party: str = "solo"
    ) -> Dict:
        """
        Generate itinerary using ML API
        
        Returns:
            Dict with complete itinerary including:
            - daily_itineraries: List of days with scheduled places
            - total_cost_usd: Estimated total cost
            - processing_time_ms: API response time
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        payload = {
            "city": city,
            "num_days": num_days,
            "start_date": str(start_date),
            "interests": interests or ["culture", "food"],
            "budget": budget,
            "travel_party": travel_party
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/api/v1/generate-itinerary",
                json=payload,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(f"City '{city}' not found in database")
            elif e.response.status_code == 400:
                raise ValueError(f"Invalid request: {e.response.json()}")
            else:
                raise Exception(f"API error: {e}")
        
        except requests.exceptions.Timeout:
            raise Exception("API timeout - try again or contact support")
        
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to ML API - check if server is running")
    
    def get_recommendations(
        self,
        city: str,
        interests: List[str],
        num_recommendations: int = 20
    ) -> Dict:
        """Get place recommendations without scheduling"""
        payload = {
            "city": city,
            "interests": interests,
            "num_recommendations": num_recommendations
        }
        
        response = requests.post(
            f"{self.api_url}/api/v1/recommendations",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()


# Usage in Flask route
from flask import Flask, request, jsonify
app = Flask(__name__)

# Initialize service
itinerary_service = ItineraryService(
    api_url="http://localhost:8000",  # Or production URL
    api_key=None  # Optional
)

@app.route('/api/itinerary/generate', methods=['POST'])
def generate_itinerary():
    data = request.json
    
    try:
        result = itinerary_service.generate_itinerary(
            city=data['city'],
            num_days=data['num_days'],
            start_date=data['start_date'],
            interests=data.get('interests'),
            budget=data.get('budget', 'medium')
        )
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
```

---

## Frontend Integration (JavaScript/TypeScript)

### React Example
```typescript
// services/itineraryService.ts
interface ItineraryRequest {
  city: string;
  num_days: number;
  start_date: string;
  interests?: string[];
  budget?: string;
  travel_party?: string;
}

interface ItineraryResponse {
  destination: string;
  duration_days: number;
  daily_itineraries: DayItinerary[];
  total_cost_usd: number;
  processing_time_ms: number;
}

export async function generateItinerary(
  request: ItineraryRequest
): Promise<ItineraryResponse> {
  const response = await fetch('http://api-server/api/v1/generate-itinerary', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.message || 'Failed to generate itinerary');
  }

  return response.json();
}

// React Component
import { useState } from 'react';
import { generateItinerary } from './services/itineraryService';

function ItineraryGenerator() {
  const [loading, setLoading] = useState(false);
  const [itinerary, setItinerary] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const result = await generateItinerary({
        city: 'Singapore',
        num_days: 3,
        start_date: '2025-12-20',
        interests: ['landmarks', 'food'],
        budget: 'medium',
      });
      setItinerary(result);
    } catch (error) {
      console.error('Error:', error);
      alert(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={handleGenerate} disabled={loading}>
        {loading ? 'Generating...' : 'Generate Itinerary'}
      </button>
      
      {loading && <p>Please wait 5-10 seconds...</p>}
      
      {itinerary && (
        <div>
          <h2>{itinerary.destination} - {itinerary.duration_days} days</h2>
          <p>Total Cost: ${itinerary.total_cost_usd}</p>
          {itinerary.daily_itineraries.map(day => (
            <div key={day.day}>
              <h3>Day {day.day} - {day.date}</h3>
              <ul>
                {day.places.map(place => (
                  <li key={place.place_id}>
                    {place.name} ({place.arrival_time} - {place.departure_time})
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

---

## Error Handling Best Practices

```python
def generate_itinerary_safe(city, days, start_date):
    try:
        response = requests.post(
            "http://api-server/api/v1/generate-itinerary",
            json={"city": city, "num_days": days, "start_date": start_date},
            timeout=60
        )
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "timeout",
            "message": "Request took too long. Try again or reduce number of days."
        }
    
    except requests.exceptions.HTTPError as e:
        error_data = e.response.json()
        return {
            "success": False,
            "error": "api_error",
            "message": error_data.get("message", "API error"),
            "status_code": e.response.status_code
        }
    
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "error": "connection",
            "message": "Cannot connect to API server. Check if it's running."
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": "unknown",
            "message": str(e)
        }
```

---

## Performance Optimization

### 1. Loading States
```python
# Show loading message based on cache status
if is_first_request:
    show_message("Generating itinerary (40-50 seconds)...")
else:
    show_message("Generating itinerary (5-10 seconds)...")
```

### 2. Caching on Your Side
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=100)
def get_cached_itinerary(city, days, start_date):
    """Cache itineraries for same requests"""
    return generate_itinerary(city, days, start_date)
```

### 3. Async Requests
```python
import asyncio
import aiohttp

async def generate_itinerary_async(city, days, start_date):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://api-server/api/v1/generate-itinerary",
            json={"city": city, "num_days": days, "start_date": start_date}
        ) as response:
            return await response.json()
```

---

## Testing

### Unit Test Example
```python
import unittest
from unittest.mock import patch, Mock

class TestItineraryService(unittest.TestCase):
    def setUp(self):
        self.service = ItineraryService("http://test-api")
    
    @patch('requests.post')
    def test_generate_itinerary_success(self, mock_post):
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "destination": "Singapore",
            "duration_days": 3,
            "total_cost_usd": 500.0
        }
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Test
        result = self.service.generate_itinerary("Singapore", 3, "2025-12-20")
        
        # Assert
        self.assertEqual(result["destination"], "Singapore")
        self.assertEqual(result["duration_days"], 3)
        mock_post.assert_called_once()
```

---

## Deployment Checklist

- [ ] API server deployed and accessible
- [ ] MongoDB populated with place data
- [ ] `.env` configured with production settings
- [ ] CORS configured for your frontend domain
- [ ] Health check endpoint responding
- [ ] Error handling implemented
- [ ] Loading states in UI
- [ ] Timeout handling (60s recommended)
- [ ] Fallback strategy (optional)
- [ ] Monitoring/logging setup
- [ ] API documentation shared with team

---

## Common Issues & Solutions

### Issue: "City not found"
**Solution:** Check city name spelling. Must match exactly what's in database.
```python
# Query available cities first
response = requests.get("http://api-server/api/v1/cities")
available_cities = response.json()
```

### Issue: "Request timeout"
**Solution:** Increase timeout to 60s. First request takes longer.
```python
requests.post(..., timeout=60)  # Not 30
```

### Issue: "CORS error from browser"
**Solution:** Add your frontend URL to API's `CORS_ORIGINS` in `.env`
```env
CORS_ORIGINS=https://your-frontend.com,http://localhost:3000
```

### Issue: "Inconsistent results"
**Solution:** ML API is deterministic (same input = same output). If results vary, check if input parameters are changing.

---

## Support & Contact

- **API Documentation:** http://your-api-server/docs
- **Health Check:** http://your-api-server/health
- **GitHub Issues:** (your repo link)
- **Email:** your-team@email.com

---

## Migration Timeline (Gemini → ML API)

**Week 1:** 
- Deploy API in staging
- Test with sample data
- Verify response format matches your needs

**Week 2:**
- Integrate in development environment
- Replace Gemini calls
- Test error handling

**Week 3:**
- Deploy to production
- Monitor performance
- Keep Gemini as fallback (optional)

**Week 4:**
- Remove Gemini dependency
- Optimize based on usage patterns
