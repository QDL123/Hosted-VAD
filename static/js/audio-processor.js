class AudioProcessor extends AudioWorkletProcessor {
    process(inputs, outputs, parameters) {
        const input = inputs[0];
        const output = outputs[0];

        input.forEach((channel, i) => {
            const outputChannel = output[i];
            for (let j = 0; j < channel.length; j++) {
                outputChannel[j] = channel[j];
            }
        });

        // Post the first channel of audio data to the main thread
        this.port.postMessage(output[0]);

        return true;
    }
}

registerProcessor('audio-processor', AudioProcessor)