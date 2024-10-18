import torch
import whisper
import srt
import datetime
import os

class Transcriptor:

    def __init__(self, logger, translator, device="cuda", is_cli=False):
        self.basePath = "media/vad_chunks"
        self.logger = logger
        self.is_cli = is_cli
        if not os.path.exists(self.basePath):
            os.mkdir(self.basePath)
        self.translator = translator
        self.device = device
        self.model = whisper.load_model("large", device=device)
        self.VAD_SR=16000
        self.VAD_THRESHOLD = 0.4 # calculate percentaje of VAD (Voice Activity Detection) if exceeds 40% will detect as voice activity
        self.CHUNK_THRESHOLD = 3.0 # calculate silence between files


    def vad_run(self, audio_file: str):
        self.logger.info(f"running VAD...")
        model, utils = torch.hub.load(repo_or_dir="snakers4/silero-vad", model="silero_vad", onnx=False)
        (get_speech_timestamps, save_audio, read_audio, VADIterator, collect_chunks) = utils
        wav = read_audio(audio_file, sampling_rate=self.VAD_SR)
        t = get_speech_timestamps(wav, model, sampling_rate=self.VAD_SR, threshold=self.VAD_THRESHOLD)

        # Add a bit of padding, and remove small gaps
        for i in range(len(t)):
            t[i]["start"] = max(0, t[i]["start"] - 3200)  # 0.2s head
            t[i]["end"] = min(wav.shape[0] - 16, t[i]["end"] + 20800)  # 1.3s tail
            if i > 0 and t[i]["start"] < t[i - 1]["end"]:
                t[i]["start"] = t[i - 1]["end"]  # Remove overlap

        # If breaks are longer than chunk_threshold seconds, split into a new audio file
        # This'll effectively turn long transcriptions into many shorter ones
        u = [[]]
        for i in range(len(t)):
            if i > 0 and t[i]["start"] > t[i - 1]["end"] + (self.CHUNK_THRESHOLD * self.VAD_SR):
                u.append([])
            u[-1].append(t[i])

        # Merge speech chunks
        for i in range(len(u)):
            save_audio(
                self.basePath + "/" + str(i) + ".wav",
                collect_chunks(u[i], wav),
                sampling_rate=self.VAD_SR,
            )
        # Convert timestamps to seconds
        for i in range(len(u)):
            time = 0.0
            offset = 0.0
            for j in range(len(u[i])):
                u[i][j]["start"] /= self.VAD_SR
                u[i][j]["end"] /= self.VAD_SR
                u[i][j]["chunk_start"] = time
                time += u[i][j]["end"] - u[i][j]["start"]
                u[i][j]["chunk_end"] = time
                if j == 0:
                    offset += u[i][j]["start"]
                else:
                    offset += u[i][j]["start"] - u[i][j - 1]["end"]
                u[i][j]["offset"] = offset

        self.logger.info(f"VAD generated {len(u)} chunk files.")
        # remove source file
        os.remove(audio_file)
        return u
    
    def transcript(self, language, audio_file: str, output_file: str):
        u = self.vad_run(audio_file=audio_file)
        if len(u) == 0:
            self.logger.error("VAD generation failed!")
            return 
        subs = []
        sub_index = 1
        total_chunks = len(u)
        self.logger.info(f"got total chunks: {total_chunks}")
        for i in range(len(u)):
            audio_chunk_file = self.basePath + "/" + str(i) + ".wav"
            
            if self.is_cli:
                print(f"Processing : {i}/{total_chunks} file: {audio_chunk_file}")
            
            result = self.model.transcribe(audio_chunk_file, task="transcribe", language=language)
            # Si no hay segmentos en la transcripción, saltar
            if len(result['segments']) == 0:
                if self.is_cli:
                    print(f"No se encontraron segmentos en el fragmento {audio_chunk_file}")
                continue

            for r in result["segments"]:
                start = r["start"] + u[i][0]["offset"]
                for j in range(len(u[i])):
                    if (r["start"] >= u[i][j]["chunk_start"] and r["start"] <= u[i][j]["chunk_end"]):
                        start = r["start"] + u[i][j]["offset"]
                        break
                
                # Prevent overlapping subs
                if len(subs) > 0:
                    last_end = datetime.timedelta.total_seconds(subs[-1].end)
                    if last_end > start:
                        subs[-1].end = datetime.timedelta(seconds=start)

                # Set end timestamp
                end = u[i][-1]["end"] + 0.5
                for j in range(len(u[i])):
                    if r["end"] >= u[i][j]["chunk_start"] and r["end"] <= u[i][j]["chunk_end"]:
                        end = r["end"] + u[i][j]["offset"]
                        break
                # Translate
                clean_content = r['text'].strip()
                text = self.translator.translate_text(clean_content)
                # Add to SRT list
                subs.append(
                    srt.Subtitle(
                        index=sub_index,
                        start=datetime.timedelta(seconds=start),
                        end=datetime.timedelta(seconds=end),
                        content=text,
                    )
                )
                sub_index += 1
            # Eliminar archivo temporal
            os.remove(audio_chunk_file)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(srt.compose(subs))
        
        if self.is_cli:
            print(f"transcript completed")
        
        self.logger.info("transcript completed.")
