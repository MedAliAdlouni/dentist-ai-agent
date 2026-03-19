"""Voice I/O : enregistrement micro, transcription faster-whisper, TTS Gemini."""

import io
import wave

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from google import genai
from google.genai import types

from src.config import (
    BLOCK_SIZE,
    CHANNELS,
    MAX_RECORD_DURATION,
    SAMPLE_RATE,
    SILENCE_DURATION,
    SILENCE_THRESHOLD,
    TTS_MODEL,
    TTS_SAMPLE_RATE,
    TTS_VOICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_MODEL,
)

# Modele Whisper charge une seule fois (lazy)
_whisper_model: WhisperModel | None = None


def _get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        print("  [Chargement du modele Whisper...]", flush=True)
        _whisper_model = WhisperModel(WHISPER_MODEL, compute_type=WHISPER_COMPUTE_TYPE)
    return _whisper_model


def record_audio() -> bytes:
    """Enregistre depuis le micro avec detection automatique du silence.

    Attend que la parole commence (RMS > seuil), puis enregistre jusqu'a
    SILENCE_DURATION secondes de silence ou MAX_DURATION atteint.

    Returns:
        Audio encode en WAV, ou bytes vides si aucune parole detectee.
    """
    print("  [Parlez...]", flush=True)

    frames: list[np.ndarray] = []
    started = False
    silence_blocks = 0
    silence_limit = int(SILENCE_DURATION * SAMPLE_RATE / BLOCK_SIZE)

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
        blocksize=BLOCK_SIZE,
    ) as stream:
        while True:
            data, _ = stream.read(BLOCK_SIZE)
            frames.append(data.copy())

            rms = np.sqrt(np.mean(data.astype(np.float32) ** 2))

            if rms > SILENCE_THRESHOLD:
                started = True
                silence_blocks = 0
            elif started:
                silence_blocks += 1

            if started and silence_blocks >= silence_limit:
                break
            if len(frames) * BLOCK_SIZE / SAMPLE_RATE >= MAX_RECORD_DURATION:
                break

    if not started:
        return b""

    audio_data = np.concatenate(frames)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_data.tobytes())

    return buf.getvalue()


def transcribe(audio_bytes: bytes) -> str:
    """Transcrit l'audio WAV en texte via faster-whisper (local)."""
    model = _get_whisper_model()

    buf = io.BytesIO(audio_bytes)
    segments, _ = model.transcribe(buf, language="fr")

    return " ".join(seg.text.strip() for seg in segments).strip()


def synthesize(client: genai.Client, text: str) -> bytes:
    """Synthetise le texte en francais via Gemini TTS et retourne des bytes WAV."""
    response = client.models.generate_content(
        model=TTS_MODEL,
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=TTS_VOICE)
                )
            ),
        ),
    )

    # Concatenate all audio parts (response may be split across multiple parts)
    chunks = [
        part.inline_data.data
        for part in response.candidates[0].content.parts
        if part.inline_data
    ]
    pcm_data = b"".join(chunks)

    # Encode raw PCM as WAV
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(TTS_SAMPLE_RATE)
        wf.writeframes(pcm_data)
    return buf.getvalue()


def speak(client: genai.Client, text: str) -> None:
    """Synthetise et joue le texte en francais via Gemini TTS."""
    wav_bytes = synthesize(client, text)

    # Decode WAV back to PCM for sounddevice playback
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        pcm_data = wf.readframes(wf.getnframes())

    pcm = np.frombuffer(pcm_data, dtype=np.int16)
    # Pad with 300ms of silence to prevent sounddevice cutting off the end
    silence = np.zeros(int(TTS_SAMPLE_RATE * 0.3), dtype=np.int16)
    pcm = np.concatenate([pcm, silence])
    sd.play(pcm, samplerate=TTS_SAMPLE_RATE)
    sd.wait()
