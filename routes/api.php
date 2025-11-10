<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\RecommendationController;
use App\Http\Controllers\TourController;
use App\Http\Controllers\UserController;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
*/

// User routes
Route::prefix('users')->group(function () {
    Route::post('/', [UserController::class, 'store']);
    Route::get('/{id}', [UserController::class, 'show']);
    Route::get('/{id}/preferences', [UserController::class, 'getPreferences']);
    Route::put('/{id}/preferences', [UserController::class, 'updatePreferences']);
});

// Tour routes
Route::prefix('tours')->group(function () {
    Route::get('/', [TourController::class, 'index']);
    Route::post('/', [TourController::class, 'store']);
    Route::get('/{id}', [TourController::class, 'show']);
    Route::put('/{id}', [TourController::class, 'update']);
    Route::delete('/{id}', [TourController::class, 'destroy']);
});

// Recommendation routes
Route::prefix('recommendations')->group(function () {
    Route::get('/users/{userId}', [RecommendationController::class, 'getDailyRecommendations']);
    Route::post('/users/{userId}/generate', [RecommendationController::class, 'generateRecommendations']);
    Route::get('/users/{userId}/range', [RecommendationController::class, 'getRecommendationsRange']);
});
