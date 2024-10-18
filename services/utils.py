from langdetect import detect
import whisper
import srt
import random
from collections import defaultdict

class Utils:
    @staticmethod
    def detect_str_lang(file_path: str) -> str:
        try:
            lines = Utils.read_file(file_path=file_path)
            return detect(lines)
        except:
            return ""
    
    @staticmethod
    def read_file(file_path: str) -> str:
        lines = ''
        with open(file_path, "r") as f:
            content = f.read()
        subs = list(srt.parse(content))
        for i, sub in enumerate(subs):
            if i >= 50:
                break
            lines += sub.content
        return lines

    @staticmethod
    def detect_language(audio_file_path: str, samples_number=5):
        # Cargar el audio
        audio = whisper.load_audio(audio_file_path)

        # Cargar el modelo de Whisper "base" (porque sólo queremos detectar el idioma del audio)
        model = whisper.load_model("base", download_root="models", device="cuda")

        # Optimización: si la longitud del audio es <= que el tamaño de chunk de Whisper, solo tomaremos 1 muestra
        if len(audio) <= whisper.audio.CHUNK_LENGTH * whisper.audio.SAMPLE_RATE:
            samples_number = 1

        probabilities_map = defaultdict(list)

        for i in range(samples_number):
            # Seleccionar un fragmento de audio al azar
            random_center = random.randint(0, len(audio) - 1)
            start = random_center - (whisper.audio.CHUNK_LENGTH // 2) * whisper.audio.SAMPLE_RATE
            end = random_center + (whisper.audio.CHUNK_LENGTH // 2) * whisper.audio.SAMPLE_RATE

            # Asegurarse de que el rango de audio esté dentro de los límites
            start = max(0, start)
            start = min(start, len(audio) - 1)
            end = max(0, end)
            end = min(end, len(audio) - 1)

            # Extraer el fragmento de audio
            audio_fragment = audio[start:end]

            # Asegurarse de que el fragmento tenga el tamaño adecuado para Whisper
            audio_fragment = whisper.pad_or_trim(audio_fragment)

            # Extraer el espectrograma Mel
            mel = whisper.log_mel_spectrogram(audio_fragment)

            # Mover el espectrograma Mel a la GPU
            mel = mel.to("cuda")

            # Detectar el idioma del fragmento
            _, _probs = model.detect_language(mel)

            # Almacenar las probabilidades de cada idioma
            for lang_key in _probs:
                probabilities_map[lang_key].append(_probs[lang_key])

        # Calcular la probabilidad promedio para cada idioma
        for lang_key in probabilities_map:
            probabilities_map[lang_key] = sum(probabilities_map[lang_key]) / len(probabilities_map[lang_key])

        # Devolver el idioma con la probabilidad más alta
        detected_lang = max(probabilities_map, key=probabilities_map.get)
        return detected_lang
