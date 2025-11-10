<?php

namespace App\Services;

use App\Models\Tour;
use App\Models\User;
use App\Models\Recommendation;
use Illuminate\Support\Collection;
use Carbon\Carbon;

class RecommendationService
{
    protected array $config;

    public function __construct()
    {
        $this->config = config('recommendation');
    }

    /**
     * Generate daily recommendations for a user
     */
    public function generateDailyRecommendations(User $user, Carbon $date): Recommendation
    {
        // Get available tours
        $tours = Tour::all();
        
        // Score tours based on user preferences
        $scoredTours = $this->scoreTours($tours, $user);
        
        // Apply scheduling optimization
        $schedule = $this->optimizeSchedule($scoredTours, $date);
        
        // Calculate overall recommendation score
        $overallScore = $this->calculateOverallScore($schedule);
        
        // Create or update recommendation
        $recommendation = Recommendation::updateOrCreate(
            [
                'user_id' => $user->_id,
                'date' => $date->startOfDay(),
            ],
            [
                'schedule' => $schedule,
                'score' => $overallScore,
                'metadata' => [
                    'generated_at' => now(),
                    'algorithm' => $this->config['optimization_algorithm'],
                ],
            ]
        );

        return $recommendation;
    }

    /**
     * Score tours based on user preferences
     */
    protected function scoreTours(Collection $tours, User $user): Collection
    {
        $preferences = $user->getPreferences();
        $weights = $this->config['scoring_weights'];

        return $tours->map(function ($tour) use ($preferences, $weights) {
            $preferenceScore = $tour->matchesPreferences($preferences);
            $ratingScore = $tour->rating / 5.0;
            
            $totalScore = 
                $preferenceScore * $weights['user_preference_match'] +
                $ratingScore * $weights['rating'];

            return [
                'tour' => $tour,
                'score' => $totalScore,
            ];
        })->sortByDesc('score');
    }

    /**
     * Optimize schedule using selected algorithm
     */
    protected function optimizeSchedule(Collection $scoredTours, Carbon $date): array
    {
        $algorithm = $this->config['optimization_algorithm'];

        switch ($algorithm) {
            case 'genetic':
                return $this->geneticAlgorithmScheduling($scoredTours, $date);
            case 'greedy':
                return $this->greedyScheduling($scoredTours, $date);
            case 'dynamic':
                return $this->dynamicProgrammingScheduling($scoredTours, $date);
            default:
                return $this->greedyScheduling($scoredTours, $date);
        }
    }

    /**
     * Greedy scheduling algorithm
     */
    protected function greedyScheduling(Collection $scoredTours, Carbon $date): array
    {
        $schedule = [];
        $maxTours = $this->config['max_tours_per_day'];
        $workingHours = $this->config['working_hours'];
        
        $currentTime = Carbon::parse($date->format('Y-m-d') . ' ' . $workingHours['start']);
        $endTime = Carbon::parse($date->format('Y-m-d') . ' ' . $workingHours['end']);
        
        $lastLocation = null;
        
        foreach ($scoredTours->take($maxTours * 3) as $item) {
            if (count($schedule) >= $maxTours) {
                break;
            }
            
            $tour = $item['tour'];
            $tourDuration = $tour->duration;
            
            // Add travel time if there's a previous location
            $travelTime = 0;
            if ($lastLocation) {
                $distance = $tour->distanceTo($lastLocation);
                $travelTime = $this->estimateTravelTime($distance);
            }
            
            $startTime = $currentTime->copy()->addMinutes($travelTime);
            $proposedEndTime = $startTime->copy()->addMinutes($tourDuration);
            
            // Check if tour fits in the remaining time
            if ($proposedEndTime->lte($endTime)) {
                $schedule[] = [
                    'tour_id' => $tour->_id,
                    'tour_name' => $tour->name,
                    'start_time' => $startTime->format('H:i'),
                    'end_time' => $proposedEndTime->format('H:i'),
                    'duration' => $tourDuration,
                    'travel_time' => $travelTime,
                    'score' => $item['score'],
                ];
                
                $currentTime = $proposedEndTime;
                $lastLocation = $tour;
            }
        }
        
        return $schedule;
    }

    /**
     * Genetic algorithm for scheduling optimization
     */
    protected function geneticAlgorithmScheduling(Collection $scoredTours, Carbon $date): array
    {
        // For this implementation, we'll use a simplified genetic algorithm
        $populationSize = 20;
        $generations = 50;
        $maxTours = $this->config['max_tours_per_day'];
        
        // Create initial population
        $population = $this->createInitialPopulation($scoredTours, $date, $populationSize);
        
        // Evolve population
        for ($gen = 0; $gen < $generations; $gen++) {
            // Evaluate fitness
            $fitness = $this->evaluatePopulation($population);
            
            // Select parents
            $parents = $this->selectParents($population, $fitness);
            
            // Create new generation through crossover and mutation
            $population = $this->createNewGeneration($parents, $scoredTours, $date);
        }
        
        // Return best solution
        $fitness = $this->evaluatePopulation($population);
        $bestIndex = array_search(max($fitness), $fitness);
        
        return $population[$bestIndex];
    }

    /**
     * Dynamic programming scheduling
     */
    protected function dynamicProgrammingScheduling(Collection $scoredTours, Carbon $date): array
    {
        // Simplified DP approach for tour scheduling
        // This is a variant of the weighted interval scheduling problem
        
        $maxTours = $this->config['max_tours_per_day'];
        $workingHours = $this->config['working_hours'];
        
        $startOfDay = Carbon::parse($date->format('Y-m-d') . ' ' . $workingHours['start']);
        $endOfDay = Carbon::parse($date->format('Y-m-d') . ' ' . $workingHours['end']);
        $totalMinutes = $endOfDay->diffInMinutes($startOfDay);
        
        // Create time slots
        $slots = array_fill(0, $totalMinutes, null);
        $schedule = [];
        
        foreach ($scoredTours->take($maxTours * 2) as $item) {
            $tour = $item['tour'];
            $bestSlot = $this->findBestTimeSlot($tour, $slots, $startOfDay, $endOfDay, $schedule);
            
            if ($bestSlot !== null && count($schedule) < $maxTours) {
                $startTime = $startOfDay->copy()->addMinutes($bestSlot);
                $endTime = $startTime->copy()->addMinutes($tour->duration);
                
                $schedule[] = [
                    'tour_id' => $tour->_id,
                    'tour_name' => $tour->name,
                    'start_time' => $startTime->format('H:i'),
                    'end_time' => $endTime->format('H:i'),
                    'duration' => $tour->duration,
                    'score' => $item['score'],
                ];
                
                // Mark slots as occupied
                for ($i = $bestSlot; $i < $bestSlot + $tour->duration && $i < count($slots); $i++) {
                    $slots[$i] = true;
                }
            }
        }
        
        return $schedule;
    }

    /**
     * Helper methods for genetic algorithm
     */
    protected function createInitialPopulation(Collection $scoredTours, Carbon $date, int $size): array
    {
        $population = [];
        
        for ($i = 0; $i < $size; $i++) {
            // Shuffle tours and create random valid schedule
            $shuffled = $scoredTours->shuffle();
            $schedule = $this->greedyScheduling($shuffled, $date);
            $population[] = $schedule;
        }
        
        return $population;
    }

    protected function evaluatePopulation(array $population): array
    {
        return array_map(function ($schedule) {
            return $this->calculateOverallScore($schedule);
        }, $population);
    }

    protected function selectParents(array $population, array $fitness): array
    {
        // Tournament selection
        $parents = [];
        $tournamentSize = 3;
        
        for ($i = 0; $i < count($population); $i++) {
            $tournament = array_rand($fitness, min($tournamentSize, count($fitness)));
            $winner = is_array($tournament) ? $tournament[array_search(max(array_intersect_key($fitness, array_flip($tournament))), array_intersect_key($fitness, array_flip($tournament)))] : $tournament;
            $parents[] = $population[$winner];
        }
        
        return $parents;
    }

    protected function createNewGeneration(array $parents, Collection $scoredTours, Carbon $date): array
    {
        $newGeneration = [];
        $mutationRate = 0.1;
        
        for ($i = 0; $i < count($parents); $i += 2) {
            $parent1 = $parents[$i];
            $parent2 = $parents[min($i + 1, count($parents) - 1)];
            
            // Simple crossover: take first half from parent1, second from parent2
            $child = $this->crossover($parent1, $parent2);
            
            // Mutation: randomly swap tours
            if (rand(0, 100) / 100 < $mutationRate) {
                $child = $this->mutate($child, $scoredTours, $date);
            }
            
            $newGeneration[] = $child;
        }
        
        return $newGeneration;
    }

    protected function crossover(array $parent1, array $parent2): array
    {
        if (empty($parent1) || empty($parent2)) {
            return !empty($parent1) ? $parent1 : $parent2;
        }
        
        $midpoint = floor(count($parent1) / 2);
        return array_merge(
            array_slice($parent1, 0, $midpoint),
            array_slice($parent2, $midpoint)
        );
    }

    protected function mutate(array $schedule, Collection $scoredTours, Carbon $date): array
    {
        // Simple mutation: regenerate the schedule
        return $this->greedyScheduling($scoredTours->shuffle(), $date);
    }

    /**
     * Find best time slot for a tour
     */
    protected function findBestTimeSlot($tour, array $slots, Carbon $startOfDay, Carbon $endOfDay, array $currentSchedule): ?int
    {
        $duration = $tour->duration;
        $totalMinutes = $endOfDay->diffInMinutes($startOfDay);
        
        for ($slot = 0; $slot <= $totalMinutes - $duration; $slot++) {
            $available = true;
            for ($i = $slot; $i < $slot + $duration && $i < count($slots); $i++) {
                if ($slots[$i] !== null) {
                    $available = false;
                    break;
                }
            }
            
            if ($available) {
                return $slot;
            }
        }
        
        return null;
    }

    /**
     * Estimate travel time based on distance
     */
    protected function estimateTravelTime(float $distance): int
    {
        // Assume average speed of 40 km/h
        $hours = $distance / 40;
        return (int) ($hours * 60);
    }

    /**
     * Calculate overall score for a schedule
     */
    protected function calculateOverallScore(array $schedule): float
    {
        if (empty($schedule)) {
            return 0.0;
        }

        $totalScore = 0;
        $weights = $this->config['scoring_weights'];
        
        // Sum individual tour scores
        foreach ($schedule as $item) {
            $totalScore += $item['score'] ?? 0;
        }
        
        // Bonus for efficient scheduling (more tours = better)
        $efficiencyBonus = count($schedule) / $this->config['max_tours_per_day'];
        
        // Calculate time efficiency (less idle time = better)
        $timeEfficiency = $this->calculateTimeEfficiency($schedule);
        
        return ($totalScore / count($schedule)) * 0.6 + $efficiencyBonus * 0.2 + $timeEfficiency * 0.2;
    }

    /**
     * Calculate time efficiency of schedule
     */
    protected function calculateTimeEfficiency(array $schedule): float
    {
        if (empty($schedule)) {
            return 0;
        }

        $totalDuration = 0;
        $workingHours = $this->config['working_hours'];
        
        foreach ($schedule as $item) {
            $totalDuration += $item['duration'];
        }
        
        $startTime = Carbon::parse($workingHours['start']);
        $endTime = Carbon::parse($workingHours['end']);
        $availableTime = $endTime->diffInMinutes($startTime);
        
        return min($totalDuration / $availableTime, 1.0);
    }

    /**
     * Get recommendations for a user on a specific date
     */
    public function getRecommendations(User $user, Carbon $date): ?Recommendation
    {
        return Recommendation::where('user_id', $user->_id)
            ->where('date', $date->startOfDay())
            ->first();
    }

    /**
     * Regenerate recommendations if needed
     */
    public function getOrGenerateRecommendations(User $user, Carbon $date): Recommendation
    {
        $existing = $this->getRecommendations($user, $date);
        
        if ($existing && $existing->updated_at->diffInMinutes(now()) < $this->config['cache_duration']) {
            return $existing;
        }
        
        return $this->generateDailyRecommendations($user, $date);
    }
}
