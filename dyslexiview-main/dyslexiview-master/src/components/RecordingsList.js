import React, { useState, useEffect } from 'react';
import './RecordingsList.css';

const RecordingsList = () => {
    const [recordings, setRecordings] = useState([]);
    const [currentlyPlaying, setCurrentlyPlaying] = useState(null);

    const fetchRecordings = async () => {
        try {
            const response = await fetch('http://localhost:5000/api/recordings');
            const data = await response.json();
            setRecordings(data);
        } catch (error) {
            console.error('Error fetching recordings:', error);
        }
    };

    useEffect(() => {
        fetchRecordings();
        // Fetch recordings every 5 seconds to keep the list updated
        const interval = setInterval(fetchRecordings, 5000);
        return () => clearInterval(interval);
    }, []);

    const formatDate = (timestamp) => {
        return new Date(timestamp * 1000).toLocaleString();
    };

    const handlePlay = (recording, enhanced = false) => {
        const audioUrl = `http://localhost:5000/api/recordings/${enhanced ? recording.filename.replace('.wav', '_enhanced.wav') : recording.filename}`;
        
        if (currentlyPlaying) {
            currentlyPlaying.pause();
            currentlyPlaying.currentTime = 0;
        }

        const audio = new Audio(audioUrl);
        audio.play();
        setCurrentlyPlaying(audio);
        
        audio.onended = () => {
            setCurrentlyPlaying(null);
        };
    };

    return (
        <div className="recordings-list">
            <h4>Your Recordings</h4>
            {recordings.length === 0 ? (
                <p>No recordings yet. Start recording to see them here!</p>
            ) : (
                <div className="recordings-grid">
                    {recordings.map(recording => (
                        <div key={recording.id} className="recording-item">
                            <div className="recording-info">
                                <span className="recording-date">
                                    {formatDate(recording.timestamp)}
                                </span>
                            </div>
                            <div className="recording-controls">
                                <button
                                    className="play-button"
                                    onClick={() => handlePlay(recording)}
                                >
                                    Play Original
                                </button>
                                {recording.enhanced && (
                                    <button
                                        className="play-button enhanced"
                                        onClick={() => handlePlay(recording, true)}
                                    >
                                        Play Enhanced
                                    </button>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default RecordingsList;
