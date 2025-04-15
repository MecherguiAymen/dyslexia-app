import React, { useState } from 'react';
import Sound from 'react-sound'; 
import wav2 from './2.wav';

const PlaySound = ({
  handleSongLoading,
  handleSongPlaying,
  handleSongFinishedPlaying
}) => {
  const [isPlaying, setIsPlaying] = useState(false);

  return (
    <div>
      <button onClick={() => setIsPlaying(!isPlaying)} className="new-email-bx-button">
        {!isPlaying ? 'Play' : 'Stop'}
      </button>
      <Sound
        url={wav2}
        playStatus={
          isPlaying ? Sound.status.PLAYING : Sound.status.STOPPED
        }
        onLoading={handleSongLoading}
        onPlaying={handleSongPlaying}
        onFinishedPlaying={handleSongFinishedPlaying}
      />
    </div>
  );
};

export default PlaySound;