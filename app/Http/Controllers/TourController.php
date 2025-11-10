<?php

namespace App\Http\Controllers;

use App\Models\Tour;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class TourController extends Controller
{
    /**
     * Get all tours
     */
    public function index(Request $request): JsonResponse
    {
        $query = Tour::query();

        // Filter by category
        if ($request->has('category')) {
            $query->where('category', $request->input('category'));
        }

        // Filter by minimum rating
        if ($request->has('min_rating')) {
            $query->where('rating', '>=', (float) $request->input('min_rating'));
        }

        // Filter by tags
        if ($request->has('tags')) {
            $tags = is_array($request->input('tags')) 
                ? $request->input('tags') 
                : explode(',', $request->input('tags'));
            $query->whereIn('tags', $tags);
        }

        $tours = $query->get();

        return response()->json([
            'tours' => $tours,
            'total' => $tours->count(),
        ]);
    }

    /**
     * Get a specific tour
     */
    public function show(string $id): JsonResponse
    {
        $tour = Tour::find($id);

        if (!$tour) {
            return response()->json(['error' => 'Tour not found'], 404);
        }

        return response()->json($tour);
    }

    /**
     * Create a new tour
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'description' => 'required|string',
            'location' => 'required|string',
            'duration' => 'required|integer|min:1',
            'category' => 'required|string',
            'tags' => 'array',
            'rating' => 'numeric|min:0|max:5',
            'price' => 'numeric|min:0',
            'capacity' => 'integer|min:1',
            'coordinates' => 'array|size:2',
            'coordinates.*' => 'numeric',
        ]);

        $tour = Tour::create($validated);

        return response()->json([
            'message' => 'Tour created successfully',
            'tour' => $tour,
        ], 201);
    }

    /**
     * Update a tour
     */
    public function update(Request $request, string $id): JsonResponse
    {
        $tour = Tour::find($id);

        if (!$tour) {
            return response()->json(['error' => 'Tour not found'], 404);
        }

        $validated = $request->validate([
            'name' => 'string|max:255',
            'description' => 'string',
            'location' => 'string',
            'duration' => 'integer|min:1',
            'category' => 'string',
            'tags' => 'array',
            'rating' => 'numeric|min:0|max:5',
            'price' => 'numeric|min:0',
            'capacity' => 'integer|min:1',
            'coordinates' => 'array|size:2',
            'coordinates.*' => 'numeric',
        ]);

        $tour->update($validated);

        return response()->json([
            'message' => 'Tour updated successfully',
            'tour' => $tour,
        ]);
    }

    /**
     * Delete a tour
     */
    public function destroy(string $id): JsonResponse
    {
        $tour = Tour::find($id);

        if (!$tour) {
            return response()->json(['error' => 'Tour not found'], 404);
        }

        $tour->delete();

        return response()->json([
            'message' => 'Tour deleted successfully',
        ]);
    }
}
