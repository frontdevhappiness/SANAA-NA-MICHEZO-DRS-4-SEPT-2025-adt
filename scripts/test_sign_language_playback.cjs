const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const handlers = {}, timers = new Map(); let timerId = 0;
function emit(type, target) {
  const event = {target, stopImmediatePropagation() {}, stopPropagation() {}};
  for (const fn of handlers[type] || []) fn(event);
  for (const fn of target.listeners[type] || []) fn(event);
}
class Media {
  constructor(src) { this.src = this.currentSrc = src; this.paused = true; this.listeners = {}; this.playbackRate = 1; }
  play() { this.paused = false; emit('play', this); return Promise.resolve(); }
  pause() { this.paused = true; emit('pause', this); }
  setAttribute() {}
  getAttribute(name) { return this[name]; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
}
class Audio extends Media {}
class Video extends Media {}
let panelOpen = true; let panelClicks = 0;
const video = new Video('/content/i18n/sw-TZ/video/test.mp4');
const audio = new Audio('/content/i18n/sw-TZ/audio/test.mp3');
const window = {HTMLMediaElement: Media, addEventListener(type, fn) { (handlers[type] ||= []).push(fn); },
 setTimeout(fn) { timers.set(++timerId, fn); return timerId; }, clearTimeout(id) { timers.delete(id); }};
const nativePause = Media.prototype.pause;
vm.runInNewContext(fs.readFileSync('assets/sign-language-sync.js', 'utf8'), {window, HTMLAudioElement:Audio, HTMLVideoElement:Video,
 document:{querySelectorAll:()=>panelOpen ? [video] : [], querySelector:()=>panelOpen ? null : {click(){panelOpen=true; panelClicks++;}}, documentElement:{}}, Element:class {}, MutationObserver:class {observe() {}}, Promise});
async function flush() { await Promise.resolve(); const pending=[...timers.values()]; timers.clear(); pending.forEach(fn=>fn()); await Promise.resolve(); }
(async()=>{
 await audio.play(); await flush(); assert.equal(video.paused,false,'joint startup');
 audio.pause(); assert.equal(video.paused,false,'TTS pause must leave video playing');
 await audio.play(); await flush();
 video.pause(); assert.equal(audio.paused,false,'video pause must leave TTS playing');
 await audio.play(); await flush(); assert.equal(video.paused,true,'next TTS clip must respect video pause');
 audio.pause(); await audio.play(); await flush();
 assert.equal(video.paused,false,'resuming TTS must restart a paused sign video');
 video.pause(); await video.play(); assert.equal(audio.paused,false,'video resume must leave TTS playing');
 audio.ended=true; emit('ended',audio); await flush(); assert.equal(video.paused,false,'TTS end must leave video playing');
 audio.ended=false; await audio.play(); nativePause.call(video); await flush();
 assert.equal(video.paused,true,'native video pause during startup must survive retry');
 await video.play(); emit('error',audio); assert.equal(video.paused,false,'TTS error must leave video playing');
 audio.pause(); panelOpen=false; nativePause.call(video);
 await audio.play(); await flush(); await flush();
 assert.equal(panelClicks,1,'TTS must open a closed sign panel once');
 assert.equal(video.paused,false,'newly opened video must start');
 console.log('Independent playback and automatic panel-opening checks passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
