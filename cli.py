#!/bin/env python
import argparse, sys, os.path
from services import Logger, Translator, Transcriptor, Utils
import torch

def print_ops(operation: str, device: str, lang_from: str, lang_to: str, input_file:str, output_file:str):
    print(f"Device: {device}")
    print(f"Operation: {operation}")
    print(f"Language from: {lang_from}")
    print(f"Langugage to: {lang_to}")
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")

def main():
    logger = Logger()
    parser = argparse.ArgumentParser(prog="Transcriber", description='Transcribe audio files and generate subtitles')
    parser.add_argument('-t', '--transcript', help="transcript", type=bool)
    parser.add_argument('-tr', '--translate', help="translate", type=bool)
    parser.add_argument('--fr', help="translate from language")
    parser.add_argument('--to', help="translate to language")
    parser.add_argument('-i', '--input-file', help="input audio file or srt file with -tr option", required=True)
    parser.add_argument('-o', '--output-file', help="output srt file", default="subtitle.srt", required=True)
    args = parser.parse_args()
    
    device = "cuda" if torch.cuda.is_available() else "cpu"

    if not os.path.isfile(args.input_file):
        print("file doesn't exist.")
        sys.exit(1)
    
    if args.transcript:
        print_ops(operation="transcript", device=device, lang_from=args.fr, lang_to=args.to, input_file=args.input_file, output_file=args.output_file)
        audio_lang = Utils.detect_language(args.input_file)
        # Setting Translation instance
        model = f"Helsinki-NLP/opus-mt-{audio_lang}-{args.to}"
        translator = Translator(logger=logger, model_name=model, device=device)
        # Serting Transcriber instance
        transcriptor = Transcriptor(logger=logger, translator=translator, device=device, is_cli=True)
        transcriptor.transcript(language=audio_lang, audio_file=args.input_file, output_file=args.output_file)
    elif args.translate:
        print_ops(operation="translate", device=device, lang_from=args.fr, lang_to=args.to, input_file=args.input_file, output_file=args.output_file)
        if args.fr and args.to and args.input_file and args.output_file:
            # Setting Translation model
            model = f"Helsinki-NLP/opus-mt-{args.fr}-{args.to}"
            translator = Translator(logger=logger, model_name=model, device=device, is_cli=True)
            translator.translate_srt_file(srt_file=args.input_file, output_file=args.output_file)


if __name__ == "__main__":
    main()
