// Request microphone access when the iframe loads
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    // Stop tracks so the mic indicator doesn't stay on
    stream.getTracks().forEach(t => t.stop());
  })
  .catch(err => {
    console.error('Microphone permission error', err);
  });