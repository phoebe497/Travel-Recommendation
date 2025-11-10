<?php

namespace App\Models;

use MongoDB\Laravel\Eloquent\Model;

class User extends Model
{
    protected $connection = 'mongodb';
    protected $collection = 'users';

    protected $fillable = [
        'name',
        'email',
        'password',
        'preferences',
    ];

    protected $hidden = [
        'password',
        'remember_token',
    ];

    protected $casts = [
        'email_verified_at' => 'datetime',
        'preferences' => 'array',
    ];

    /**
     * Get user preferences
     */
    public function getPreferences()
    {
        return $this->preferences ?? [];
    }

    /**
     * Update user preferences
     */
    public function updatePreferences(array $preferences)
    {
        $this->preferences = array_merge($this->getPreferences(), $preferences);
        $this->save();
        return $this;
    }

    /**
     * Get recommendations for this user
     */
    public function recommendations()
    {
        return $this->hasMany(Recommendation::class);
    }
}
