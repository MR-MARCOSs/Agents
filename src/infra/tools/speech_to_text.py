import os
import yt_dlp
import whisper
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

def obter_transcricao_hibrida(url):
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        video_id = info['id']
        video_title = info['title']

    print(f"Processando: {video_title}")

    try:
        print("Tentando recuperar legendas existentes...")
        
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
        texto = " ".join([i['text'] for i in transcript_list])
        return f"[Fonte: Legendas do YouTube]\n{texto}"

    except (TranscriptsDisabled, NoTranscriptFound, Exception) as e:
        print(f"Legendas não encontradas ou desativadas. Erro: {e}")
        print("Iniciando transcrição via IA (Whisper)... Isso pode demorar.")
    
    audio_filename = f"audio_{video_id}.mp3"
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': audio_filename,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True
    }

    try:
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        model = whisper.load_model("base")
        result = model.transcribe(audio_filename)
        
        return f"[Fonte: Transcrição via IA Whisper]\n{result['text']}"

    except Exception as e:
        return f"Erro crítico: Não foi possível transcrever o vídeo. {e}"

    finally:
        
        if os.path.exists(audio_filename):
            os.remove(audio_filename)

url_video = "https://www.youtube.com/watch?v=NOME_DO_VIDEO"
resultado = obter_transcricao_hibrida(url_video)
print("\n--- RESULTADO ---\n")
print(resultado)