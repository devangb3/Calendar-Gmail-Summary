import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  IconButton,
  Slider,
  Typography,
  Paper,
  Tooltip,
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import VolumeOffIcon from '@mui/icons-material/VolumeOff';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import DownloadIcon from '@mui/icons-material/Download';
import PropTypes from 'prop-types';

// Create a static audio state to persist between component unmounts
const globalAudioState = {
  currentTime: 0,
  isPlaying: false,
  volume: 1,
  isMuted: false
};

function AudioSummary({ audioUrl, title = 'Daily Summary' }) {
  const [isPlaying, setIsPlaying] = useState(globalAudioState.isPlaying);
  const [isMuted, setIsMuted] = useState(globalAudioState.isMuted);
  const [currentTime, setCurrentTime] = useState(globalAudioState.currentTime);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(globalAudioState.volume);
  const [error, setError] = useState(null);
  const audioRef = useRef(null);

  useEffect(() => {
    if (!audioUrl) return;

    // Create new audio element when URL changes
    if (audioRef.current) {
      audioRef.current.pause();
      setIsPlaying(false);
      globalAudioState.isPlaying = false;
    }

    const audio = new Audio(audioUrl);
    audioRef.current = audio;

    // Set up initial state
    audio.currentTime = globalAudioState.currentTime;
    audio.volume = globalAudioState.isMuted ? 0 : globalAudioState.volume;

    // Add event listeners
    audio.addEventListener('loadedmetadata', handleLoadedMetadata);
    audio.addEventListener('timeupdate', handleTimeUpdate);
    audio.addEventListener('ended', () => {
      setIsPlaying(false);
      globalAudioState.isPlaying = false;
    });
    audio.addEventListener('error', (e) => {
      console.error('Audio error:', e);
      setError('Failed to load audio');
      setIsPlaying(false);
      globalAudioState.isPlaying = false;
    });

    return () => {
      if (audioRef.current) {
        // Save state before cleanup
        globalAudioState.currentTime = audioRef.current.currentTime;
        globalAudioState.isPlaying = !audioRef.current.paused;
        globalAudioState.volume = volume;
        globalAudioState.isMuted = isMuted;
        
        // Remove event listeners
        audio.removeEventListener('loadedmetadata', handleLoadedMetadata);
        audio.removeEventListener('timeupdate', handleTimeUpdate);
        audio.removeEventListener('ended', () => {});
        audio.removeEventListener('error', () => {});
        
        // Cleanup audio element
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [audioUrl]);

  const handlePlayPause = () => {
    if (!audioRef.current) return;

    if (audioRef.current.paused) {
      const playPromise = audioRef.current.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => {
            setIsPlaying(true);
            globalAudioState.isPlaying = true;
            setError(null);
          })
          .catch(error => {
            console.error('Error playing audio:', error);
            setIsPlaying(false);
            globalAudioState.isPlaying = false;
            setError('Failed to play audio');
          });
      }
    } else {
      audioRef.current.pause();
      setIsPlaying(false);
      globalAudioState.isPlaying = false;
    }
  };

  const handleTimeUpdate = () => {
    if (!audioRef.current) return;
    setCurrentTime(audioRef.current.currentTime);
    globalAudioState.currentTime = audioRef.current.currentTime;
  };

  const handleLoadedMetadata = () => {
    if (!audioRef.current) return;
    setDuration(audioRef.current.duration);
  };

  const handleSeek = (event, newValue) => {
    if (!audioRef.current) return;
    const time = newValue;
    audioRef.current.currentTime = time;
    setCurrentTime(time);
    globalAudioState.currentTime = time;
  };

  const handleVolumeChange = (event, newValue) => {
    if (!audioRef.current) return;
    const vol = newValue;
    audioRef.current.volume = vol;
    setVolume(vol);
    setIsMuted(vol === 0);
    globalAudioState.volume = vol;
    globalAudioState.isMuted = vol === 0;
  };

  const handleMuteToggle = () => {
    if (!audioRef.current) return;
    if (isMuted) {
      audioRef.current.volume = volume || 1;
      setIsMuted(false);
      globalAudioState.isMuted = false;
    } else {
      audioRef.current.volume = 0;
      setIsMuted(true);
      globalAudioState.isMuted = true;
    }
  };

  const handleRestart = () => {
    if (!audioRef.current) return;
    audioRef.current.currentTime = 0;
    setCurrentTime(0);
    globalAudioState.currentTime = 0;
    if (!isPlaying) {
      handlePlayPause();
    }
  };

  const formatTime = (timeInSeconds) => {
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = Math.floor(timeInSeconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // Check if audio URL is valid
  const isAudioAvailable = Boolean(audioUrl);

  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        borderRadius: 4,
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        backdropFilter: 'blur(20px)',
      }}
    >
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>

        {!isAudioAvailable ? (
          <Typography color="text.secondary" align="center">
            No audio summary available
          </Typography>
        ) : (
          <>
            {error && (
              <Typography color="error" align="center" sx={{ mb: 1 }}>
                {error}
              </Typography>
            )}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <IconButton
                onClick={handlePlayPause}
                disabled={!isAudioAvailable}
                sx={{
                  p: 1.5,
                  color: 'primary.main',
                  bgcolor: 'primary.light',
                  '&:hover': {
                    bgcolor: 'primary.main',
                    color: 'white',
                  },
                }}
              >
                {isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
              </IconButton>

              <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 40 }}>
                  {formatTime(currentTime)}
                </Typography>
                <Slider
                  value={currentTime}
                  max={duration || 100}
                  onChange={handleSeek}
                  disabled={!isAudioAvailable}
                  aria-label="audio progress"
                  sx={{
                    color: 'primary.main',
                    '& .MuiSlider-thumb': {
                      width: 12,
                      height: 12,
                      '&:hover, &.Mui-focusVisible': {
                        boxShadow: '0 0 0 8px rgba(63, 81, 181, 0.16)',
                      },
                    },
                  }}
                />
                <Typography variant="body2" color="text.secondary" sx={{ minWidth: 40 }}>
                  {formatTime(duration)}
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Tooltip title="Restart">
                  <IconButton 
                    size="small" 
                    onClick={handleRestart}
                    disabled={!isAudioAvailable}
                  >
                    <RestartAltIcon />
                  </IconButton>
                </Tooltip>
                <Box sx={{ display: 'flex', alignItems: 'center', width: 140 }}>
                  <IconButton 
                    size="small" 
                    onClick={handleMuteToggle}
                    disabled={!isAudioAvailable}
                  >
                    {isMuted ? <VolumeOffIcon /> : <VolumeUpIcon />}
                  </IconButton>
                  <Slider
                    size="small"
                    value={isMuted ? 0 : volume}
                    onChange={handleVolumeChange}
                    disabled={!isAudioAvailable}
                    max={1}
                    step={0.1}
                    aria-label="Volume"
                    sx={{
                      width: 80,
                      ml: 1,
                      color: 'primary.main',
                    }}
                  />
                </Box>
                {audioUrl && (
                  <Tooltip title="Download audio">
                    <IconButton
                      size="small"
                      component="a"
                      href={audioUrl}
                      download="summary.mp3"
                      sx={{ color: 'primary.main' }}
                    >
                      <DownloadIcon />
                    </IconButton>
                  </Tooltip>
                )}
              </Box>
            </Box>
          </>
        )}
      </Box>
    </Paper>
  );
}

AudioSummary.propTypes = {
  audioUrl: PropTypes.string,
  title: PropTypes.string,
};

export default AudioSummary;
