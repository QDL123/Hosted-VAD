from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
import torch
import resampy

vad_model, utils = torch.hub.load(
    repo_or_dir="snakers4/silero-vad",
    model="silero_vad",
    onnx=True,
)
get_speech_ts, _, _, VADIterator, _ = utils

VAD_SAMPLING_RATE = 8000
VAD_WINDOW_SIZE_EXAMPLES = 512

app = FastAPI()


duration = 0

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def get():
    fname = "static/index.html"
    html_file = open(fname, 'r', encoding='utf-8') 
    return HTMLResponse(html_file.read())


@app.websocket("/api/v1/listen")
async def websocket_endpoint(websocket: WebSocket):
    print("REACHED WEBSOCKET ENDPOINT!")
    vad_iterator = VADIterator(vad_model, threshold=0.9, sampling_rate=VAD_SAMPLING_RATE)
    accum_buffer = np.array([])
    duration = 0

    await websocket.accept()

    # Read the sample rate
    data = await websocket.receive_json()
    sample_rate = data.get("sampleRate", None)
    if (sample_rate == None):
        raise ValueError("No sample rate found in streamed audio")
    
    while True:
        buffer = np.array([], dtype=np.float32)
        # Accumulate enough data to resample if necessary
        while buffer.size < 512:
            chunk = await websocket.receive_bytes()
            # convert byte array to numpy array
            data = np.frombuffer(chunk, dtype=np.float32)
            buffer = np.concatenate((buffer, data))

        # Resample to VAD input sampling rate
        if sample_rate != VAD_SAMPLING_RATE:
            # Resample the data
            try:
                buffer = resampy.resample(buffer, sample_rate, VAD_SAMPLING_RATE)
            except ValueError as e:
                print("Error resampling data: ", e)
                print("Data: ", buffer)

        accum_buffer = np.concatenate((accum_buffer, buffer))
        # Process the buffer
        processed_windows_count = 0
        activities = {}
        for i in range(0, len(accum_buffer), VAD_WINDOW_SIZE_EXAMPLES):
            if i + VAD_WINDOW_SIZE_EXAMPLES > len(accum_buffer):
                break

            processed_windows_count += 1
            speech_dict = vad_iterator(accum_buffer[i: i + VAD_WINDOW_SIZE_EXAMPLES], return_seconds=True)
            if speech_dict:
                if "start" in speech_dict:
                    activities["start"] = speech_dict["start"]
                else:
                    activities["end"] = speech_dict["end"]
        
        # Remove processed audio from buffer
        accum_buffer = accum_buffer[processed_windows_count * VAD_WINDOW_SIZE_EXAMPLES:]
        # Send activities to websocket
        duration += (processed_windows_count * (VAD_WINDOW_SIZE_EXAMPLES)) / VAD_SAMPLING_RATE
        await websocket.send_json({ "activity": activities, "accum_duration": duration })