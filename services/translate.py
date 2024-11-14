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

    # cut long lines until max_length
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

    # translate text method
    def translate_text(self, text: str) -> str:
        clean_content = self.clean_text(text)
        # input text tokenizer
        inputs = self.tokenizer(clean_content.capitalize(), return_tensors="pt", add_special_tokens=True, padding=False, truncation=False).to(self.device)
        # translate
        translated_tokens = self.model.generate(**inputs)
        # decode output
        translated_text = self.tokenizer.batch_decode(translated_tokens, skip_special_tokens=True)
        return translated_text[0]

    # load str file
    def load_srt(self, file_path:str) -> List[str]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return list(srt.parse(f.read()))

    # translate function keeping time and str's structure
    def translate_srt_file(self, srt_file: str, output_file: str):
        if self.is_cli:
            print(f"translating file {srt_file} to output: {output_file}")
        
        self.logger.info(f"translating file {srt_file} to output: {output_file}")
        # load srt file
        subtitles = self.load_srt(srt_file)

        translated_subtitles = []

        # translate each line 
        for subtitle in subtitles:
            content = subtitle.content
            
            translated_text = self.translate_text(content)
            lines = self.split_lines(translated_text, max_length=42)
            # creating new str file
            translated_subtitle = srt.Subtitle(index=subtitle.index,
                                            start=subtitle.start,
                                            end=subtitle.end,
                                            content="\n".join(lines)+"\n")
            translated_subtitles.append(translated_subtitle)

        # save generated str file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(srt.compose(translated_subtitles))
        
        if self.is_cli:
            print("translation completed")
        self.logger.info("translation completed")

