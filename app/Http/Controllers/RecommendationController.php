<?php

namespace App\Http\Controllers;

use App\Models\User;
use App\Services\RecommendationService;
use Carbon\Carbon;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class RecommendationController extends Controller
{
    protected RecommendationService $recommendationService;

    public function __construct(RecommendationService $recommendationService)
    {
        $this->recommendationService = $recommendationService;
    }

    /**
     * Get daily recommendations for a user
     */
    public function getDailyRecommendations(Request $request, string $userId): JsonResponse
    {
        $user = User::find($userId);
        
        if (!$user) {
            return response()->json(['error' => 'User not found'], 404);
        }

        $date = $request->has('date') 
            ? Carbon::parse($request->input('date'))
            : Carbon::today();

        $recommendation = $this->recommendationService->getOrGenerateRecommendations($user, $date);

        return response()->json([
            'user_id' => $user->_id,
            'date' => $date->format('Y-m-d'),
            'schedule' => $recommendation->schedule,
            'score' => $recommendation->score,
            'metadata' => $recommendation->metadata,
        ]);
    }

    /**
     * Generate new recommendations for a user
     */
    public function generateRecommendations(Request $request, string $userId): JsonResponse
    {
        $user = User::find($userId);
        
        if (!$user) {
            return response()->json(['error' => 'User not found'], 404);
        }

        $date = $request->has('date')
            ? Carbon::parse($request->input('date'))
            : Carbon::today();

        $recommendation = $this->recommendationService->generateDailyRecommendations($user, $date);

        return response()->json([
            'message' => 'Recommendations generated successfully',
            'user_id' => $user->_id,
            'date' => $date->format('Y-m-d'),
            'schedule' => $recommendation->schedule,
            'score' => $recommendation->score,
            'metadata' => $recommendation->metadata,
        ]);
    }

    /**
     * Get recommendations for a date range
     */
    public function getRecommendationsRange(Request $request, string $userId): JsonResponse
    {
        $user = User::find($userId);
        
        if (!$user) {
            return response()->json(['error' => 'User not found'], 404);
        }

        $startDate = Carbon::parse($request->input('start_date', Carbon::today()));
        $endDate = Carbon::parse($request->input('end_date', Carbon::today()->addDays(7)));

        $recommendations = [];
        $currentDate = $startDate->copy();

        while ($currentDate->lte($endDate)) {
            $recommendation = $this->recommendationService->getOrGenerateRecommendations($user, $currentDate);
            
            $recommendations[] = [
                'date' => $currentDate->format('Y-m-d'),
                'schedule' => $recommendation->schedule,
                'score' => $recommendation->score,
            ];

            $currentDate->addDay();
        }

        return response()->json([
            'user_id' => $user->_id,
            'start_date' => $startDate->format('Y-m-d'),
            'end_date' => $endDate->format('Y-m-d'),
            'recommendations' => $recommendations,
        ]);
    }
}
