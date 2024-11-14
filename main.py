from flask import Flask, request, jsonify, send_from_directory
import threading
import requests
import os
from services import Logger, Translator, Transcriptor, Utils, DBManager
import gc

app = Flask(__name__)
UPLOAD_FOLDER = 'media'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FILE_SUFFIX'] = '.es.srt'

logger = Logger()
db = DBManager(logger=logger, db_file="./media/tasks.db")

# Envs
HOST = os.getenv('LLM_HOST', "0.0.0.0")
PORT = int(os.getenv('LLM_PORT', 4003))
NOTIFICATION_URL = str(os.getenv("LLM_NOTIFICATION_SERVICE_URL", "http://192.168.105.105:4000/"))

# Endpoint that process tasks
@app.route("/processTask", methods=["GET"])
def processTask():
    thread = threading.Thread(target=processTasks,)
    thread.start()
    return jsonify({"message":"ok"}), 200

# Endpoint to download str file
@app.route("/download", methods=["GET"])
def download_file():
    file_path = request.args.get("filename")
    logger.info(f"downloading file: {file_path}")
    
    if not file_path:
        return jsonify({"error": "filaname required."}, 400)
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], path=file_path, as_attachment=True)
    except Exception as e:
        logger.error(f"error downloading file: {e}")
        return jsonify({"error": f"error {e}"})

# Endpoint to translate from str to str
@app.route("/send_translate", methods=["POST"])
def translate():
    logger.info("request for translate received")
    
    if 'file' not in request.files:
        logger.error("missing srt source file.")
        return jsonify({"error": "missing srt source file."}), 400
    
    lang = request.form.get("lang")
    if lang == "":
        logger.error('missing output language from request.')
        return jsonify({"error": "output language is required."}), 400
    
    title = request.form.get("title")
    if title == "":
        logger.error("missing input title from request.")
        return jsonify({"error": "missing input title as required."}, 400)

    destinationPath = request.form.get("destinationPath")
    if destinationPath == "":
        logger.error("missing input destinationPath from request.")
        return jsonify({"error": "missing input destinationPath as required."}, 400)
    
    file = request.files['file']
    if file.filename == '':
        logger.error("missing srt source file.")
        return jsonify({"error": "missing srt source file."}), 400

    logger.info(f"processing translation file: {file.filename}, with title: {title} for lang: {lang}")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    db.insert_task(('translate', lang, title, file_path, destinationPath))
    return jsonify({"message": "file saved", "path": file_path, "task": "translation created"}), 200

@app.route("/send_transcript", methods=["POST"])
def transcribe():
    logger.info("request for transcript received")

    if 'file' not in request.files:
        logger.error("missing audio input file.")
        return jsonify({"error": "missing audio file."}), 400

    lang = request.form.get("lang")
    if lang == "":
        logger.error("missing output language from request.")
        return jsonify({"error": "missing output language from request."}), 400

    title = request.form.get("title")
    if title == "":
        logger.error("missing input title from request.")
        return jsonify({"error": "missing input title as required."}), 400

    destinationPath = request.form.get("destinationPath")
    if destinationPath == "":
        logger.error("missing input destinationPath from request.")
        return jsonify({"error": "missing input destinationPath as required."}, 400)

    file = request.files["file"]
    if file.filename == '':
        logger.error("missing audio input file.")
        return jsonify({"error": "missing audio input file."}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    db.insert_task(('transcript', lang, title, file_path, destinationPath))
    return jsonify({"message": "file saved", "path": file_path, "task": "transcription created"}), 200

def processTasks() -> None:
    tasks = db.getTasks(query="select id, operation, language, title, file, destinationPath, process from tasks where process = ?", params=(0,))
    for task in tasks:
        logger.info(f"processing task {task['id']} for {task['operation']}")
        if task['operation'] == 'transcript':
            db.update_task_status(taskId=task['id'])
            transcribeTask(task['file'], task['language'], task['title'], task['destinationPath'])
        elif task['operation'] == 'translate':
            db.update_task_status(taskId=task['id'])
            translateTask(task['file'], task['language'], task['title'], task['destinationPath'])
        else:
            logger.error(f"operation {task['operation']} not supported.")
        logger.info(f"end processing {task['operation']} task {task['id']}")
        db.delete_task(taskId=task['id'])

def translateTask(file_path: str, output_lang: str, title: str, destinationPath: str) -> None:
    # Detect source file language
    lang = Utils.detect_str_lang(file_path=file_path)
    logger.info(f"task initialized with {file_path} with lang: {lang} and output_lang: {output_lang}")
    # Validate if input lang and desired translation language are the same
    if lang == output_lang:
        logger.error("source language and output language are the same.")
        return
    
    output_path = os.path.splitext(file_path)[0] + app.config['OUTPUT_FILE_SUFFIX']
    # Setting Translation model
    model = f"Helsinki-NLP/opus-mt-{lang}-{output_lang}"
    translator = Translator(logger=logger, model_name=model, device="cuda")
    translator.translate_srt_file(srt_file=file_path, output_file=output_path)
    try:
        # Notify to service that translation is completed.
        requests.post(NOTIFICATION_URL, json={"status":"task completed", "title": title, "file": output_path,  "destinationPath": destinationPath}, timeout=0.001)
    except requests.exceptions.Timeout:
        logger.info("notification sent, no waiting for response.")
    logger.info(f"translation task completed for {file_path} as title {title} from {lang} to {output_lang} saved in {output_path}.")
    # garbage collect
    gc.collect()

def transcribeTask(file_path: str, output_lang:str, title: str, destinationPath: str) -> None:
    # detect source language
    audio_lang = Utils.detect_language(file_path)
    if audio_lang == "":
        logger.error("while detecting source audio language.")
        return
    if audio_lang == output_lang:
        logger.error("source language and output language are the same.")
        return 
    output_path = os.path.splitext(file_path)[0] + app.config['OUTPUT_FILE_SUFFIX']
    
    logger.info(f"language detected {audio_lang} for {file_path}")
    if not audio_lang or not output_lang:
        logger.error(f"no language detected {audio_lang} or {output_lang}")
        return
    # Setting Translation instance
    model = f"Helsinki-NLP/opus-mt-{audio_lang}-{output_lang}"
    translator = Translator(logger=logger, model_name=model, device="cuda")
    # Serting Transcriber instance
    transcriptor = Transcriptor(logger=logger, translator=translator, device="cuda")
    transcriptor.transcript(language=audio_lang, audio_file=file_path, output_file=output_path)
    try:
        # send notification back when task finishes
        requests.post(NOTIFICATION_URL, json={"status": "task completed", "title": title, "file": output_path, "destinationPath": destinationPath}, timeout=0.001)
    except requests.exceptions.Timeout:
        logger.info("notification sent, no waiting for response.")
    logger.info(f"transcription completed for {file_path} as title: {title} from {audio_lang} to {output_lang} saved in {output_path}.")
    # garbage collector
    gc.collect()
# init
if __name__ == '__main__':
    from waitress import serve
    logger.info(f"Server starting at: http://{HOST}:{PORT}")
    logger.info(f"Notification Service: {NOTIFICATION_URL}")
    serve(app, host=HOST, port=PORT)
