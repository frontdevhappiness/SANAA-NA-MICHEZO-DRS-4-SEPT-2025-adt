(function () {
  "use strict";

  if (window.__adtSignLanguageSyncInstalled) return;
  window.__adtSignLanguageSyncInstalled = true;

  var mediaPrototype = window.HTMLMediaElement && window.HTMLMediaElement.prototype;
  if (!mediaPrototype) return;

  var nativePlay = mediaPrototype.play;
  var nativePause = mediaPrototype.pause;
  var trackedAudio = new WeakSet();
  var ttsAudio = null;
  var ttsPlaying = false;
  var sessionStarted = false;
  var retryTimer = 0;
  var videoPausedByUser = false;
  var startingTts = false;
  var panelRequested = false;

  function mediaUrl(media) {
    return String(media.currentSrc || media.src || "");
  }

  function isTtsAudio(media) {
    return (
      media instanceof HTMLAudioElement &&
      /\/content\/i18n\/[^/]+\/audio\//.test(mediaUrl(media))
    );
  }

  function isSignVideo(media) {
    return (
      media instanceof HTMLVideoElement &&
      /\/content\/i18n\/[^/]+\/video\//.test(mediaUrl(media))
    );
  }

  function signVideo() {
    var videos = document.querySelectorAll("video");
    for (var i = 0; i < videos.length; i += 1) {
      if (isSignVideo(videos[i])) return videos[i];
    }
    return null;
  }

  function muteVideo(video) {
    video.defaultMuted = true;
    video.muted = true;
    video.volume = 0;
    video.setAttribute("muted", "");
    video.setAttribute("playsinline", "");
  }

  function setVideoSpeed(video) {
    if (!ttsAudio) return;
    var rate = Number(ttsAudio.playbackRate) || 1;
    video.playbackRate = Math.max(0.25, Math.min(4, rate));
  }

  function playSignVideo(video, reset) {
    if (!video || !ttsPlaying || videoPausedByUser) return;
    muteVideo(video);
    setVideoSpeed(video);
    if (reset && video.paused) {
      try {
        video.currentTime = 0;
      } catch (_error) {
        // Metadata may not be available yet; loadedmetadata retries below.
      }
    }
    var result = nativePlay.call(video);
    if (result && typeof result.catch === "function") result.catch(function () {});
  }

  function ensureSignVideo(reset, attempt) {
    window.clearTimeout(retryTimer);
    var video = signVideo();
    if (video) {
      playSignVideo(video, reset);
      return;
    }

    if (!panelRequested && ttsPlaying && !videoPausedByUser) {
      var toggle = document.querySelector(
        'button[aria-label="Lugha ya ishara"][aria-pressed="false"], ' +
        'button[aria-label="Sign language"][aria-pressed="false"]'
      );
      if (toggle) {
        panelRequested = true;
        toggle.click();
      }
    }

    if (attempt < 20 && ttsPlaying && !videoPausedByUser) {
      retryTimer = window.setTimeout(function () {
        ensureSignVideo(reset, attempt + 1);
      }, 50);
    }
  }

  function finishIfAudioStopped(audio) {
    window.setTimeout(function () {
      if (ttsAudio !== audio) return;
      if (!audio.ended && audio.getAttribute("src")) return;
      ttsPlaying = false;
      sessionStarted = false;
      window.clearTimeout(retryTimer);
    }, 120);
  }

  function trackAudio(audio) {
    if (trackedAudio.has(audio)) return;
    trackedAudio.add(audio);
    audio.addEventListener("ended", function () {
      finishIfAudioStopped(audio);
    });
    audio.addEventListener("error", function () {
      ttsPlaying = false;
      sessionStarted = false;
      window.clearTimeout(retryTimer);
    });
    audio.addEventListener("ratechange", function () {
      var video = signVideo();
      if (video) setVideoSpeed(video);
    });
  }

  mediaPrototype.play = function () {
    var media = this;
    var args = arguments;

    if (isSignVideo(media)) {
      videoPausedByUser = false;
      muteVideo(media);
      return nativePlay.apply(media, args);
    }

    var isTts = isTtsAudio(media);
    if (isTts) startingTts = true;
    var result = nativePlay.apply(media, args);
    if (!isTts) return result;

    trackAudio(media);
    var reset = !sessionStarted;
    var startTogether = !ttsPlaying;
    if (startTogether) {
      videoPausedByUser = false;
      panelRequested = false;
    }
    ttsAudio = media;
    ttsPlaying = true;
    sessionStarted = true;

    Promise.resolve(result).then(
      function () {
        if (startTogether) ensureSignVideo(reset, 0);
        // The ADT runtime updates its media state after play resolves. Retry
        // once after that update so its old exclusive-media effect cannot win.
        window.setTimeout(function () {
          startingTts = false;
          if (startTogether) ensureSignVideo(false, 0);
        }, 80);
      },
      function () {
        ttsPlaying = false;
        startingTts = false;
      }
    );
    return result;
  };

  mediaPrototype.pause = function () {
    // Ignore only the runtime's exclusive-media effect during TTS startup.
    // Native video controls still emit pause and are respected below.
    if (isSignVideo(this) && startingTts) return;
    if (isSignVideo(this)) videoPausedByUser = true;
    var result = nativePause.apply(this, arguments);
    if (isTtsAudio(this)) {
      ttsPlaying = false;
      startingTts = false;
      window.clearTimeout(retryTimer);
    }
    return result;
  };

  window.addEventListener("pause", function (event) {
    if (isSignVideo(event.target)) {
      videoPausedByUser = true;
      window.clearTimeout(retryTimer);
    }
  }, true);

  window.addEventListener(
    "play",
    function (event) {
      if (!isSignVideo(event.target)) return;
      videoPausedByUser = false;
      muteVideo(event.target);
      // React's current onPlay handler marks sign language as exclusive media,
      // which stops TTS. Keep the native playback but suppress that handler.
      event.stopImmediatePropagation();
      event.stopPropagation();
    },
    true
  );

  window.addEventListener(
    "volumechange",
    function (event) {
      if (isSignVideo(event.target)) muteVideo(event.target);
    },
    true
  );

  window.addEventListener(
    "loadedmetadata",
    function (event) {
      if (!isSignVideo(event.target)) return;
      muteVideo(event.target);
      if (ttsPlaying) playSignVideo(event.target, false);
    },
    true
  );

  new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (!(node instanceof Element)) return;
        var videos = node.matches("video")
          ? [node]
          : Array.from(node.querySelectorAll("video"));
        videos.forEach(function (video) {
          if (!isSignVideo(video)) return;
          muteVideo(video);
          if (ttsPlaying) playSignVideo(video, false);
          else nativePause.call(video);
        });
      });

      mutation.removedNodes.forEach(function (node) {
        if (!(node instanceof Element)) return;
        var videos = node.matches("video")
          ? [node]
          : Array.from(node.querySelectorAll("video"));
        videos.forEach(function (video) {
          if (isSignVideo(video)) nativePause.call(video);
        });
      });
    });
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
