<?php

namespace Database\Seeders;

use App\Models\Tour;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class DatabaseSeeder extends Seeder
{
    /**
     * Seed the application's database.
     */
    public function run(): void
    {
        // Create sample users
        $user1 = User::create([
            'name' => 'John Doe',
            'email' => 'john@example.com',
            'password' => Hash::make('password123'),
            'preferences' => [
                'categories' => ['adventure', 'nature', 'cultural'],
                'tags' => ['hiking', 'museums', 'photography'],
                'min_rating' => 4.0,
                'max_price' => 100,
                'preferred_duration' => 120,
            ],
        ]);

        $user2 = User::create([
            'name' => 'Jane Smith',
            'email' => 'jane@example.com',
            'password' => Hash::make('password123'),
            'preferences' => [
                'categories' => ['food', 'cultural', 'shopping'],
                'tags' => ['food-tour', 'local-cuisine', 'markets'],
                'min_rating' => 3.5,
                'max_price' => 150,
            ],
        ]);

        // Create sample tours
        $tours = [
            [
                'name' => 'City Walking Tour',
                'description' => 'Explore the historic downtown area with a knowledgeable guide',
                'location' => 'Downtown',
                'duration' => 120,
                'category' => 'cultural',
                'tags' => ['walking', 'history', 'photography'],
                'rating' => 4.5,
                'price' => 30,
                'capacity' => 15,
                'coordinates' => [40.7128, -74.0060], // New York coordinates as example
            ],
            [
                'name' => 'Mountain Hiking Adventure',
                'description' => 'Challenging hike with breathtaking views',
                'location' => 'Blue Mountains',
                'duration' => 240,
                'category' => 'adventure',
                'tags' => ['hiking', 'nature', 'photography'],
                'rating' => 4.8,
                'price' => 75,
                'capacity' => 10,
                'coordinates' => [40.8128, -74.1060],
            ],
            [
                'name' => 'Local Food Tour',
                'description' => 'Taste the best local cuisine and street food',
                'location' => 'Food District',
                'duration' => 180,
                'category' => 'food',
                'tags' => ['food-tour', 'local-cuisine', 'tasting'],
                'rating' => 4.6,
                'price' => 60,
                'capacity' => 12,
                'coordinates' => [40.7228, -74.0160],
            ],
            [
                'name' => 'Museum and Art Gallery Tour',
                'description' => 'Visit the finest museums and galleries in the city',
                'location' => 'Museum District',
                'duration' => 150,
                'category' => 'cultural',
                'tags' => ['museums', 'art', 'history'],
                'rating' => 4.4,
                'price' => 45,
                'capacity' => 20,
                'coordinates' => [40.7328, -74.0260],
            ],
            [
                'name' => 'Beach and Water Sports',
                'description' => 'Enjoy water activities and beach relaxation',
                'location' => 'Coastal Area',
                'duration' => 180,
                'category' => 'adventure',
                'tags' => ['beach', 'water-sports', 'recreation'],
                'rating' => 4.7,
                'price' => 85,
                'capacity' => 8,
                'coordinates' => [40.6128, -74.0060],
            ],
            [
                'name' => 'Wine Tasting Tour',
                'description' => 'Visit local wineries and taste premium wines',
                'location' => 'Wine Country',
                'duration' => 240,
                'category' => 'food',
                'tags' => ['wine', 'tasting', 'relaxation'],
                'rating' => 4.9,
                'price' => 95,
                'capacity' => 10,
                'coordinates' => [40.9128, -74.2060],
            ],
            [
                'name' => 'Shopping and Markets Tour',
                'description' => 'Explore local markets and shopping districts',
                'location' => 'Shopping District',
                'duration' => 120,
                'category' => 'shopping',
                'tags' => ['markets', 'shopping', 'local-crafts'],
                'rating' => 4.2,
                'price' => 40,
                'capacity' => 15,
                'coordinates' => [40.7428, -74.0360],
            ],
            [
                'name' => 'Sunset Photography Tour',
                'description' => 'Capture stunning sunset photos at scenic locations',
                'location' => 'Scenic Overlook',
                'duration' => 90,
                'category' => 'nature',
                'tags' => ['photography', 'sunset', 'scenic'],
                'rating' => 4.8,
                'price' => 55,
                'capacity' => 8,
                'coordinates' => [40.7528, -74.0460],
            ],
            [
                'name' => 'Historical Landmarks Tour',
                'description' => 'Visit important historical sites and monuments',
                'location' => 'Historic District',
                'duration' => 180,
                'category' => 'cultural',
                'tags' => ['history', 'landmarks', 'education'],
                'rating' => 4.5,
                'price' => 50,
                'capacity' => 18,
                'coordinates' => [40.7628, -74.0560],
            ],
            [
                'name' => 'Bike Tour Through Parks',
                'description' => 'Cycle through beautiful parks and green spaces',
                'location' => 'City Parks',
                'duration' => 150,
                'category' => 'adventure',
                'tags' => ['biking', 'nature', 'recreation'],
                'rating' => 4.6,
                'price' => 45,
                'capacity' => 12,
                'coordinates' => [40.7728, -74.0660],
            ],
        ];

        foreach ($tours as $tourData) {
            Tour::create($tourData);
        }

        $this->command->info('Database seeded successfully!');
    }
}
