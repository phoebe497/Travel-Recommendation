<?php

namespace App\Http\Controllers;

use App\Models\User;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Hash;

class UserController extends Controller
{
    /**
     * Get user profile
     */
    public function show(string $id): JsonResponse
    {
        $user = User::find($id);

        if (!$user) {
            return response()->json(['error' => 'User not found'], 404);
        }

        return response()->json([
            'id' => $user->_id,
            'name' => $user->name,
            'email' => $user->email,
            'preferences' => $user->preferences,
        ]);
    }

    /**
     * Create a new user
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'name' => 'required|string|max:255',
            'email' => 'required|email|unique:users,email',
            'password' => 'required|string|min:8',
            'preferences' => 'array',
        ]);

        $user = User::create([
            'name' => $validated['name'],
            'email' => $validated['email'],
            'password' => Hash::make($validated['password']),
            'preferences' => $validated['preferences'] ?? [],
        ]);

        return response()->json([
            'message' => 'User created successfully',
            'user' => [
                'id' => $user->_id,
                'name' => $user->name,
                'email' => $user->email,
                'preferences' => $user->preferences,
            ],
        ], 201);
    }

    /**
     * Update user preferences
     */
    public function updatePreferences(Request $request, string $id): JsonResponse
    {
        $user = User::find($id);

        if (!$user) {
            return response()->json(['error' => 'User not found'], 404);
        }

        $validated = $request->validate([
            'preferences' => 'required|array',
            'preferences.categories' => 'array',
            'preferences.tags' => 'array',
            'preferences.min_rating' => 'numeric|min:0|max:5',
            'preferences.max_price' => 'numeric|min:0',
            'preferences.preferred_duration' => 'integer|min:0',
        ]);

        $user->updatePreferences($validated['preferences']);

        return response()->json([
            'message' => 'Preferences updated successfully',
            'preferences' => $user->preferences,
        ]);
    }

    /**
     * Get user preferences
     */
    public function getPreferences(string $id): JsonResponse
    {
        $user = User::find($id);

        if (!$user) {
            return response()->json(['error' => 'User not found'], 404);
        }

        return response()->json([
            'preferences' => $user->getPreferences(),
        ]);
    }
}
