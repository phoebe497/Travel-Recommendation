<?php

return [
    // Time slot duration in minutes for scheduling
    'time_slot_duration' => env('RECOMMENDATION_TIME_SLOT_DURATION', 60),
    
    // Maximum number of tours per day
    'max_tours_per_day' => env('RECOMMENDATION_MAX_TOURS_PER_DAY', 5),
    
    // Optimization algorithm: genetic, greedy, or dynamic
    'optimization_algorithm' => env('RECOMMENDATION_OPTIMIZATION_ALGORITHM', 'genetic'),
    
    // Weights for recommendation scoring
    'scoring_weights' => [
        'user_preference_match' => 0.4,
        'rating' => 0.2,
        'distance_efficiency' => 0.2,
        'time_optimization' => 0.2,
    ],
    
    // Working hours for tours
    'working_hours' => [
        'start' => '08:00',
        'end' => '20:00',
    ],
    
    // Cache duration for recommendations (in minutes)
    'cache_duration' => 60,
];
