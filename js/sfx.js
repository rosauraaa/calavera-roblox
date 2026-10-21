// Efectos de sonido sintetizados con Web Audio (sin archivos externos = sin problemas de licencia).
let ctx = null;

export function unlockAudio() {
  ctx ??= new (window.AudioContext || window.webkitAudioContext)();
  if (ctx.state === "suspended") ctx.resume();
}

function tone({ freq = 440, to = freq, type = "square", dur = 0.15, vol = 0.2, delay = 0 }) {
  if (!ctx) return;
  const t = ctx.currentTime + delay;
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, t);
  osc.frequency.exponentialRampToValueAtTime(Math.max(to, 1), t + dur);
  gain.gain.setValueAtTime(vol, t);
  gain.gain.exponentialRampToValueAtTime(0.001, t + dur);
  osc.connect(gain).connect(ctx.destination);
  osc.start(t);
  osc.stop(t + dur + 0.02);
}

function noise({ dur = 0.4, vol = 0.4, cutoff = 900 }) {
  if (!ctx) return;
  const t = ctx.currentTime;
  const buf = ctx.createBuffer(1, ctx.sampleRate * dur, ctx.sampleRate);
  const data = buf.getChannelData(0);
  for (let i = 0; i < data.length; i++) data[i] = (Math.random() * 2 - 1) * (1 - i / data.length);
  const src = ctx.createBufferSource();
  src.buffer = buf;
  const filter = ctx.createBiquadFilter();
  filter.type = "lowpass";
  filter.frequency.value = cutoff;
  const gain = ctx.createGain();
  gain.gain.value = vol;
  src.connect(filter).connect(gain).connect(ctx.destination);
  src.start(t);
}
// escala pentatonica tipo marimba
const NOTES = [523, 587, 659, 784, 880, 1047, 1175, 1319];

export const sfx = {
  marimba: () => NOTES.forEach((f, i) => tone({ freq: f, type: "triangle", dur: 0.25, vol: 0.14, delay: i * 0.06 })),
  chime: () => {
    [1047, 1319, 1568].forEach((f, i) => tone({ freq: f, type: "sine", dur: 0.6, vol: 0.12, delay: i * 0.05 }));
    noise({ dur: 0.3, vol: 0.08, cutoff: 6000 });
  },
};
