const startButton = document.getElementById('start-button');
const stopButton = document.getElementById('stop-button');

const status = document.getElementById('status');


let audioContext;
let source;
let processor;

// establish websockets connection
var ws = new WebSocket("wss://146.148.99.249:30036/api/v1/listen");

ws.addEventListener('message', event => {
    const data = JSON.parse(event.data);

    const duration = data.accum_duration;
    document.getElementById('duration-indicator').innerHTML = `Duration: ${Math.floor(duration)}`
    if (data.activity.start) {
        document.getElementById('status-indicator').innerHTML = "SPEAKING!";
    } else if (data.activity.end) {
        document.getElementById('status-indicator').innerHTML = "Not Speaking";
    }
})


startButton.addEventListener('click', async () => {
    console.log("STARTING")
    // Check if the browser supports the required APIs
    if (!window.AudioContext || 
        !window.MediaStreamAudioSourceNode || 
        !window.AudioWorkletNode) {
        alert('Your browser does not support the required APIs');
        return;
    }


    // Request access to the user's microphone
    const micStream = await navigator
        .mediaDevices
        .getUserMedia({ audio: true });
    const sampleRate = micStream.getAudioTracks()[0].getSettings().sampleRate;
    const sampleRateHeader = { sampleRate };
    console.log(`sample rate: ${sampleRate}`)

    // Send this sample rate over web sockets
    ws.send(JSON.stringify(sampleRateHeader))


    // Create the microphone stream
    audioContext = new AudioContext({ sampleRate });
    source = audioContext.createMediaStreamSource(micStream);
    console.log('Got source and audio context')

    // Create and connect AudioWorkletNode 
    // for processing the audio stream
    await audioContext.audioWorklet.addModule("/static/js/audio-processor.js");
    const processor = new AudioWorkletNode(audioContext, 'audio-processor');
    source.connect(processor);
    processor.connect(audioContext.destination)
    console.log('Connected')

    processor.port.onmessage = function(event) {
        // Get the raw audio data and convert it to a Float32Array
        buffer = event.data
        const data = new Float32Array(buffer.length);

        for (let i = 0; i < buffer.length; i++) {
            data[i] = buffer[i];
        }
        // Send the data over WebSocket
        ws.send(data);
    }
});


stopButton.addEventListener('click', () => {
    console.log('CLOSING')
    // Close audio stream
    console.log("Should disconnect audio recording")
    source.disconnect();
    audioContext.close();
    document.getElementById('status-indicator').innerHTML = "Stopped Listening";
});