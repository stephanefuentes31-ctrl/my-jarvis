const transcript = document.querySelector('#transcript');
const form = document.querySelector('#chat-form');
const promptInput = document.querySelector('#prompt');
const mic = document.querySelector('#mic');
const voiceLabel = document.querySelector('#voice-label');
const status = document.querySelector('#status');
const history = [];
let recognition;
let activeAudio;

function addMessage(content, role) {
  const message = document.createElement('p');
  message.className = `${role}-message`;
  message.textContent = content;
  transcript.append(message);
  transcript.scrollTop = transcript.scrollHeight;
  return message;
}

async function speak(text) {
  if (!text) return;
  activeAudio?.pause();
  try {
    const response = await fetch('/api/speech', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text }) });
    if (!response.ok) throw new Error('Speech unavailable');
    activeAudio = new Audio(URL.createObjectURL(await response.blob()));
    await activeAudio.play();
  } catch {
    // Text remains available if the optional voice service is unavailable.
  }
}

async function sendMessage(message) {
  if (!message.trim()) return;
  activeAudio?.pause();
  addMessage(message, 'user');
  history.push({ role: 'user', content: message });
  const responseNode = addMessage('', 'assistant');
  status.textContent = 'Processing request.';
  promptInput.disabled = true;
  try {
    const response = await fetch('/api/chat/stream', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, history: history.slice(0, -1) }) });
    if (!response.ok || !response.body) throw new Error('Request failed');
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = ''; let answer = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n'); buffer = lines.pop();
      for (const line of lines) { if (!line) continue; const event = JSON.parse(line); if (event.type === 'delta') { answer += event.content; responseNode.textContent = answer; transcript.scrollTop = transcript.scrollHeight; } }
    }
    history.push({ role: 'assistant', content: answer });
    if (history.length > 30) history.splice(0, history.length - 30);
    status.textContent = 'J.A.R.V.I.S. is ready.';
    speak(answer);
  } catch {
    responseNode.textContent = 'The operation could not be completed. Please try again.';
    status.textContent = 'Connection unavailable.';
  } finally { promptInput.disabled = false; promptInput.focus(); }
}

form.addEventListener('submit', (event) => { event.preventDefault(); const message = promptInput.value; promptInput.value = ''; sendMessage(message); });

if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  recognition = new Recognition(); recognition.continuous = false; recognition.interimResults = true;
  recognition.onstart = () => { mic.classList.add('listening'); voiceLabel.textContent = 'Listening...'; status.textContent = 'Listening for your command.'; };
  recognition.onresult = (event) => { const text = [...event.results].map(result => result[0].transcript).join(''); voiceLabel.textContent = text; if (event.results[event.results.length - 1].isFinal) sendMessage(text); };
  recognition.onend = () => { mic.classList.remove('listening'); voiceLabel.textContent = 'Speak to J.A.R.V.I.S.'; };
  recognition.onerror = () => { status.textContent = 'Voice input unavailable. You may type instead.'; };
  mic.addEventListener('click', () => { activeAudio?.pause(); recognition.start(); });
} else { mic.disabled = true; voiceLabel.textContent = 'Voice input is not supported by this browser'; }

function updateClock() { const now = new Date(); document.querySelector('#time').textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }); document.querySelector('#date').textContent = now.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' }).toUpperCase(); }
updateClock(); setInterval(updateClock, 1000);
