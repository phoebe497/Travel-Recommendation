<?php

namespace App\Models;

use MongoDB\Laravel\Eloquent\Model;

class Tour extends Model
{
    protected $connection = 'mongodb';
    protected $collection = 'tours';

    protected $fillable = [
        'name',
        'description',
        'location',
        'duration', // in minutes
        'category',
        'tags',
        'rating',
        'price',
        'capacity',
        'coordinates', // [latitude, longitude]
        'available_time_slots',
        'images',
    ];

    protected $casts = [
        'tags' => 'array',
        'coordinates' => 'array',
        'available_time_slots' => 'array',
        'images' => 'array',
        'duration' => 'integer',
        'rating' => 'float',
        'price' => 'float',
        'capacity' => 'integer',
    ];

    /**
     * Check if tour matches user preferences
     */
    public function matchesPreferences(array $preferences): float
    {
        $score = 0.0;
        $totalWeight = 0;

        // Category match
        if (isset($preferences['categories']) && in_array($this->category, $preferences['categories'])) {
            $score += 0.4;
        }
        $totalWeight += 0.4;

        // Tag match
        if (isset($preferences['tags']) && !empty($this->tags)) {
            $matchingTags = array_intersect($preferences['tags'], $this->tags);
            $tagScore = count($matchingTags) / max(count($preferences['tags']), 1);
            $score += $tagScore * 0.3;
        }
        $totalWeight += 0.3;

        // Rating preference
        if (isset($preferences['min_rating'])) {
            $score += ($this->rating >= $preferences['min_rating']) ? 0.3 : 0;
        } else {
            $score += ($this->rating / 5.0) * 0.3;
        }
        $totalWeight += 0.3;

        return $totalWeight > 0 ? $score / $totalWeight : 0;
    }

    /**
     * Calculate distance to another tour or coordinates
     */
    public function distanceTo($target): float
    {
        $targetCoords = $target instanceof Tour ? $target->coordinates : $target;
        
        if (empty($this->coordinates) || empty($targetCoords)) {
            return 0;
        }

        // Haversine formula
        $lat1 = deg2rad($this->coordinates[0]);
        $lon1 = deg2rad($this->coordinates[1]);
        $lat2 = deg2rad($targetCoords[0]);
        $lon2 = deg2rad($targetCoords[1]);

        $dlat = $lat2 - $lat1;
        $dlon = $lon2 - $lon1;

        $a = sin($dlat / 2) ** 2 + cos($lat1) * cos($lat2) * sin($dlon / 2) ** 2;
        $c = 2 * atan2(sqrt($a), sqrt(1 - $a));

        // Earth radius in kilometers
        return 6371 * $c;
    }
}
