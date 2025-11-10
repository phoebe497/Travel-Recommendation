<?php

namespace App\Models;

use MongoDB\Laravel\Eloquent\Model;

class Recommendation extends Model
{
    protected $connection = 'mongodb';
    protected $collection = 'recommendations';

    protected $fillable = [
        'user_id',
        'date',
        'schedule', // Array of scheduled tours with time slots
        'score',
        'metadata',
    ];

    protected $casts = [
        'date' => 'datetime',
        'schedule' => 'array',
        'metadata' => 'array',
        'score' => 'float',
    ];

    /**
     * Get the user that owns the recommendation
     */
    public function user()
    {
        return $this->belongsTo(User::class);
    }

    /**
     * Get tours in this recommendation
     */
    public function getTours()
    {
        $tourIds = array_column($this->schedule, 'tour_id');
        return Tour::whereIn('_id', $tourIds)->get();
    }

    /**
     * Add a tour to the schedule
     */
    public function addTour($tourId, string $startTime, string $endTime, array $metadata = [])
    {
        $schedule = $this->schedule ?? [];
        $schedule[] = [
            'tour_id' => $tourId,
            'start_time' => $startTime,
            'end_time' => $endTime,
            'metadata' => $metadata,
        ];
        $this->schedule = $schedule;
        $this->save();
        return $this;
    }
}
