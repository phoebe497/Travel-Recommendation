<?php

namespace Tests\Unit;

use Tests\TestCase;
use App\Models\Tour;
use App\Models\User;
use Illuminate\Support\Facades\Hash;

class TourTest extends TestCase
{
    /**
     * Test tour preference matching.
     */
    public function test_tour_matches_user_preferences(): void
    {
        $tour = new Tour([
            'name' => 'Test Tour',
            'category' => 'adventure',
            'tags' => ['hiking', 'nature'],
            'rating' => 4.5,
        ]);

        $preferences = [
            'categories' => ['adventure'],
            'tags' => ['hiking'],
            'min_rating' => 4.0,
        ];

        $score = $tour->matchesPreferences($preferences);

        $this->assertGreaterThan(0, $score);
        $this->assertLessThanOrEqual(1.0, $score);
    }

    /**
     * Test distance calculation between tours.
     */
    public function test_tour_distance_calculation(): void
    {
        $tour1 = new Tour([
            'coordinates' => [40.7128, -74.0060], // New York
        ]);

        $tour2 = new Tour([
            'coordinates' => [40.7589, -73.9851], // Times Square
        ]);

        $distance = $tour1->distanceTo($tour2);

        $this->assertGreaterThan(0, $distance);
        $this->assertLessThan(100, $distance); // Should be less than 100km for nearby locations
    }
}
