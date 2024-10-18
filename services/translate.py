import torch
from transformers import MarianMTModel, MarianTokenizer
import srt
from bs4 import BeautifulSoup
from typing import List

class Translator:

    def __init__(self, logger, model_name: str, device: str, is_cli: bool = False):
        self.logger = logger
        self.is_cli = is_cli
        self.tokenizer = MarianTokenizer.from_pretrained(model_name)
        self.model = MarianMTModel.from_pretrained(model_name)
        self.device = device
        self.model.to(device)

    # Cortar lineas largas hasta max_length
    def split_lines(self, text:str, max_length:int = 80) -> List[str]:
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            if len(current_line) + len(word) + 1 <= max_length:
                current_line += (word + " ")
            else:
                lines.append(current_line.strip())
                current_line = word + " "

        lines.append(current_line.strip())
        return lines

    def clean_text(self, text:str) -> str:
        return BeautifulSoup(text, "html.parser").get_text()

    # Función para traducir texto usando llm model
    def translate_text(self, text: str) -> str:
        clean_content = self.clean_text(text)
        # Tokenizar el texto de entrada
        inputs = self.tokenizer(clean_content.capitalize(), return_tensors="pt", add_special_tokens=True, padding=False, truncation=False).to(self.device)
        # Generar la traducción
        translated_tokens = self.model.generate(**inputs)
        # Decodificar la salida
        translated_text = self.tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
        return translated_text[0]

    # Función para cargar subtítulos desde un archivo SRT
    def load_srt(self, file_path:str) -> List[str]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return list(srt.parse(f.read()))

    # Función para traducir los subtítulos manteniendo tiempos y estructura
    def translate_srt_file(self, srt_file: str, output_file: str):
        if self.is_cli:
            print(f"translating file {srt_file} to output: {output_file}")
        
        self.logger.info(f"translating file {srt_file} to output: {output_file}")
        # Cargar los subtítulos
        subtitles = self.load_srt(srt_file)

        # Crear una lista para los subtítulos traducidos
        translated_subtitles = []

        # Traducir cada línea del subtítulo respetando el contexto
        for subtitle in subtitles:
            content = subtitle.content
            
            translated_text = self.translate_text(content)
            lines = self.split_lines(translated_text, max_length=42)
            # Crear un nuevo subtítulo con el texto traducido y los mismos tiempos
            translated_subtitle = srt.Subtitle(index=subtitle.index,
                                            start=subtitle.start,
                                            end=subtitle.end,
                                            content="\n".join(lines)+"\n")
            translated_subtitles.append(translated_subtitle)

        # Guardar los subtítulos traducidos en un nuevo archivo SRT
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(srt.compose(translated_subtitles))
        
        if self.is_cli:
            print("translation completed")
        self.logger.info("translation completed")
