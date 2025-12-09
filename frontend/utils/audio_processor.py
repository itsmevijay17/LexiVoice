"""
Audio preprocessing utility for fixing sample rate issues.
Save as: frontend/utils/audio_processor.py
"""
import io
import wave
import numpy as np
from scipy import signal
import logging

logger = logging.getLogger(__name__)


def resample_audio(audio_bytes: bytes, target_sample_rate: int = 16000) -> bytes:
    """
    Resample audio to target sample rate (default: 16kHz for Whisper).
    
    This fixes the "slowed and elongated" audio issue caused by
    sample rate mismatch between recording (48kHz) and processing (16kHz).
    
    Args:
        audio_bytes: Original audio bytes (any sample rate)
        target_sample_rate: Target sample rate (default: 16000 Hz)
        
    Returns:
        Resampled audio bytes at target sample rate
    """
    try:
        # Read the audio data
        audio_stream = io.BytesIO(audio_bytes)
        
        with wave.open(audio_stream, 'rb') as wav_file:
            # Get audio parameters
            n_channels = wav_file.getnchannels()
            sampwidth = wav_file.getsampwidth()
            original_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            
            logger.info(f"🎵 Original audio: {original_rate}Hz, {n_channels}ch, {sampwidth}B")
            
            # If already at target rate, return as-is
            if original_rate == target_sample_rate:
                logger.info(f"✅ Audio already at {target_sample_rate}Hz")
                return audio_bytes
            
            # Read audio data
            audio_data = wav_file.readframes(n_frames)
            
            # Convert to numpy array
            if sampwidth == 1:
                dtype = np.uint8
            elif sampwidth == 2:
                dtype = np.int16
            elif sampwidth == 4:
                dtype = np.int32
            else:
                raise ValueError(f"Unsupported sample width: {sampwidth}")
            
            audio_array = np.frombuffer(audio_data, dtype=dtype)
            
            # Handle stereo -> mono conversion if needed
            if n_channels == 2:
                logger.info("🔄 Converting stereo to mono")
                audio_array = audio_array.reshape(-1, 2)
                audio_array = audio_array.mean(axis=1).astype(dtype)
                n_channels = 1
            
            # Resample using scipy
            logger.info(f"🔄 Resampling from {original_rate}Hz to {target_sample_rate}Hz")
            
            # Calculate number of samples after resampling
            num_samples = int(len(audio_array) * target_sample_rate / original_rate)
            
            # Perform resampling
            resampled_array = signal.resample(audio_array, num_samples)
            
            # Convert back to original dtype
            resampled_array = resampled_array.astype(dtype)
            
            # Create new WAV file in memory
            output_stream = io.BytesIO()
            
            with wave.open(output_stream, 'wb') as output_wav:
                output_wav.setnchannels(n_channels)
                output_wav.setsampwidth(sampwidth)
                output_wav.setframerate(target_sample_rate)
                output_wav.writeframes(resampled_array.tobytes())
            
            # Get resampled bytes
            resampled_bytes = output_stream.getvalue()
            
            logger.info(f"✅ Resampled: {target_sample_rate}Hz, {n_channels}ch, {sampwidth}B")
            logger.info(f"📊 Size: {len(audio_bytes)} → {len(resampled_bytes)} bytes")
            
            return resampled_bytes
            
    except Exception as e:
        logger.error(f"❌ Resampling failed: {e}")
        logger.warning("⚠️ Returning original audio (may cause quality issues)")
        return audio_bytes


def validate_audio_quality(audio_bytes: bytes) -> dict:
    """
    Validate audio quality and return metadata.
    
    Args:
        audio_bytes: Audio bytes to validate
        
    Returns:
        Dictionary with audio metadata and validation status
    """
    try:
        audio_stream = io.BytesIO(audio_bytes)
        
        with wave.open(audio_stream, 'rb') as wav_file:
            return {
                'valid': True,
                'sample_rate': wav_file.getframerate(),
                'channels': wav_file.getnchannels(),
                'sample_width': wav_file.getsampwidth(),
                'duration_seconds': wav_file.getnframes() / wav_file.getframerate(),
                'size_bytes': len(audio_bytes),
                'size_mb': len(audio_bytes) / (1024 * 1024)
            }
    except Exception as e:
        return {
            'valid': False,
            'error': str(e)
        }


def prepare_audio_for_whisper(audio_bytes: bytes) -> bytes:
    """
    Complete audio preparation for Whisper STT.
    
    Performs:
    1. Sample rate normalization to 16kHz
    2. Stereo to mono conversion
    3. Quality validation
    
    Args:
        audio_bytes: Raw audio bytes
        
    Returns:
        Preprocessed audio bytes optimized for Whisper
    """
    logger.info("🎤 Preparing audio for Whisper STT...")
    
    # Validate input
    metadata = validate_audio_quality(audio_bytes)
    
    if not metadata['valid']:
        logger.error(f"❌ Invalid audio: {metadata.get('error')}")
        return audio_bytes
    
    logger.info(f"📊 Input: {metadata['sample_rate']}Hz, {metadata['duration_seconds']:.2f}s")
    
    # Resample to 16kHz (Whisper's optimal rate)
    processed_bytes = resample_audio(audio_bytes, target_sample_rate=16000)
    
    # Validate output
    output_metadata = validate_audio_quality(processed_bytes)
    
    if output_metadata['valid']:
        logger.info(f"✅ Output: {output_metadata['sample_rate']}Hz, {output_metadata['duration_seconds']:.2f}s")
    
    return processed_bytes