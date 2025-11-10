<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Models\User;
use App\Models\Tour;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;

class RecommendationTest extends TestCase
{
    /**
     * Test that recommendations can be generated for a user.
     */
    public function test_recommendations_can_be_generated(): void
    {
        // Create a test user with preferences
        $user = User::create([
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => Hash::make('password'),
            'preferences' => [
                'categories' => ['adventure', 'nature'],
                'tags' => ['hiking', 'photography'],
                'min_rating' => 4.0,
            ],
        ]);

        // Create some test tours
        Tour::create([
            'name' => 'Test Tour 1',
            'description' => 'Test description',
            'location' => 'Test Location',
            'duration' => 120,
            'category' => 'adventure',
            'tags' => ['hiking'],
            'rating' => 4.5,
            'price' => 50,
            'capacity' => 10,
            'coordinates' => [40.7128, -74.0060],
        ]);

        // Make API request to generate recommendations
        $response = $this->postJson("/api/recommendations/users/{$user->_id}/generate", [
            'date' => '2024-01-15',
        ]);

        // Assert response is successful
        $response->assertStatus(200)
            ->assertJsonStructure([
                'message',
                'user_id',
                'date',
                'schedule',
                'score',
                'metadata',
            ]);

        // Clean up
        $user->delete();
        Tour::truncate();
    }

    /**
     * Test that recommendations can be retrieved.
     */
    public function test_recommendations_can_be_retrieved(): void
    {
        // Create a test user
        $user = User::create([
            'name' => 'Test User',
            'email' => 'test2@example.com',
            'password' => Hash::make('password'),
            'preferences' => [
                'categories' => ['cultural'],
                'tags' => ['museums'],
            ],
        ]);

        // Generate recommendations first
        $this->postJson("/api/recommendations/users/{$user->_id}/generate", [
            'date' => '2024-01-15',
        ]);

        // Retrieve recommendations
        $response = $this->getJson("/api/recommendations/users/{$user->_id}?date=2024-01-15");

        // Assert response is successful
        $response->assertStatus(200)
            ->assertJsonStructure([
                'user_id',
                'date',
                'schedule',
                'score',
            ]);

        // Clean up
        $user->delete();
    }
}
