import React, { useState, useEffect } from 'react';
import { 
  Box,
  IconButton,
  LinearProgress,
  Alert 
} from '@mui/material';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import PauseIcon from '@mui/icons-material/Pause';
import VolumeUpIcon from '@mui/icons-material/VolumeUp';
import { summary } from '../../utils/api';
import logger from '../../utils/logger';

const AudioSummary = () => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [audio, setAudio] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [audioUrl, setAudioUrl] = useState(null);

  useEffect(() => {
    return () => {
      // Cleanup function to revoke object URL and stop audio
      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
      }
      if (audio) {
        audio.pause();
        audio.currentTime = 0;
      }
    };
  }, [audio, audioUrl]);

  const fetchAudioSummary = async () => {
    try {
      setLoading(true);
      setError(null);
      logger.info('Fetching audio summary');
      
      const response = await summary.getAudioSummary();
      if (!response.ok) {
        throw new Error('Failed to fetch audio summary');
      }
      
      const blob = await response.blob();
      if (!blob || blob.size === 0) {
        throw new Error('Received empty audio data');
      }
      
      const url = URL.createObjectURL(blob);
      
      // Create new audio object
      const newAudio = new Audio(url);
      
      // Set up event listeners
      newAudio.addEventListener('timeupdate', () => {
        const percent = (newAudio.currentTime / newAudio.duration) * 100;
        setProgress(percent);
      });

      newAudio.addEventListener('ended', () => {
        setIsPlaying(false);
        setProgress(0);
      });

      newAudio.addEventListener('error', (e) => {
        logger.error('Audio playback error:', e);
        setError('Failed to play audio. Please try again.');
        setIsPlaying(false);
      });

      // Update state
      setAudioUrl(url);
      setAudio(newAudio);
      setLoading(false);
      
      // Start playing automatically
      try {
        await newAudio.play();
        setIsPlaying(true);
      } catch (err) {
        logger.error('Failed to start audio playback:', err);
        setError('Failed to start audio playback. Please try again.');
      }
      
    } catch (err) {
      logger.error('Failed to fetch audio summary:', err);
      setError('Failed to load audio summary. Please try again.');
      setLoading(false);
    }
  };

  const togglePlay = async () => {
    if (!audio) {
      await fetchAudioSummary();
      return;
    }

    if (isPlaying) {
      audio.pause();
      setIsPlaying(false);
    } else {
      try {
        await audio.play();
        setIsPlaying(true);
      } catch (err) {
        logger.error('Failed to play audio:', err);
        setError('Failed to play audio. Please try again.');
      }
    }
  };

  if (error) {
    return (
      <Alert severity="error" onClose={() => setError(null)}>
        {error}
      </Alert>
    );
  }

  return (
    <Box sx={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: 2, 
      p: 2, 
      borderRadius: 2,
      bgcolor: 'background.paper',
      boxShadow: 1
    }}>
      <IconButton 
        onClick={togglePlay} 
        color="primary"
        size="large"
        disabled={loading}
      >
        {isPlaying ? <PauseIcon /> : <PlayArrowIcon />}
      </IconButton>
      
      <Box sx={{ flexGrow: 1 }}>
        {loading ? (
          <LinearProgress />
        ) : (
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{ height: 8, borderRadius: 4 }}
          />
        )}
      </Box>
      
      <VolumeUpIcon color="primary" />
    </Box>
  );
};

export default AudioSummary;
