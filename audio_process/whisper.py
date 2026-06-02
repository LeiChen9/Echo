import json
import os
import librosa
import soundfile as sf
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq
import tempfile

# Load from .env file in project root
env_file = Path(__file__).parent.parent / ".env"
load_dotenv(env_file)


def split_audio(audio_path: str, num_chunks: int = 8) -> list[tuple[str, float, float]]:
    """Split audio into chunks and return list of (chunk_path, start_time, end_time)"""
    audio, sr = librosa.load(audio_path, sr=16000, mono=True)
    total_duration = len(audio) / sr
    chunk_duration = total_duration / num_chunks
    
    chunk_paths = []
    temp_dir = Path(tempfile.gettempdir()) / "whisper_chunks"
    temp_dir.mkdir(exist_ok=True)
    
    for i in range(num_chunks):
        start_sec = i * chunk_duration
        end_sec = (i + 1) * chunk_duration
        start_sample = int(start_sec * sr)
        end_sample = int(end_sec * sr)
        
        chunk_audio = audio[start_sample:end_sample]
        chunk_path = temp_dir / f"chunk_{i:02d}.mp3"
        sf.write(str(chunk_path), chunk_audio, sr, format='MP3')
        
        chunk_paths.append((str(chunk_path), start_sec, end_sec))
    
    return chunk_paths


def transcribe_chunk(client: Groq, chunk_path: str) -> str:
    """Transcribe a single audio chunk"""
    with open(chunk_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            file=(Path(chunk_path).name, f.read()),
            model="whisper-large-v3-turbo",
            temperature=0,
            response_format="verbose_json",
        )
    return transcription.text


def main():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment variables or .env file")
    
    client = Groq(api_key=api_key)
    audio_file = "asset/ep6_bil.mp3"
    audio_name = audio_file.split("/")[-1]
    num_chunks = 10
    
    print(f"Splitting audio into {num_chunks} chunks...")
    chunks = split_audio(audio_file, num_chunks)
    
    print(f"Transcribing {num_chunks} chunks...")
    transcriptions = []
    for i, (chunk_path, start_time, end_time) in enumerate(chunks):
        print(f"  [{i+1}/{num_chunks}] Transcribing chunk {i+1}...")
        text = transcribe_chunk(client, chunk_path)
        transcriptions.append(text)
    
    # Combine transcriptions
    full_text = " ".join(transcriptions)
    
    # Save to output
    Path("output").mkdir(exist_ok=True)
    
    output_data = {
        "text": full_text,
        "chunks": [
            {"index": i, "start": start, "end": end, "text": text}
            for i, (_, start, end), text in zip(range(num_chunks), chunks, transcriptions)
        ]
    }
    
    with open(f"output/{audio_name}_transcription.json", "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print("\n=== Full Transcription ===")
    print(full_text)
    print(f"\n✓ Transcription saved to: output/{audio_name}_transcription.json")


if __name__ == "__main__":
    main()

