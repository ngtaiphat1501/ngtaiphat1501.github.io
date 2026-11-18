/**
 * Nguyễn Phát Tài - Developer Portfolio
 * App Logic: Typewriter, Music Player, CV Modal, Time Clock
 */

document.addEventListener('DOMContentLoaded', () => {
  initTypingBanner();
  initMusicPlayer();
  initModals();
  initTimeClock();
});

// =============================================================================
// 1. TYPING BANNER (Đồng bộ với Readme Typing SVG trên GitHub)
// =============================================================================
function initTypingBanner() {
  const el = document.getElementById('typingOutput');
  if (!el) return;

  const lines = [
    "Java Backend & Systems Architect",
    "Turning Coffee & Lo-Fi into Clean Code ☕",
    "Building Scalable Software 🚀",
    "Exploring Applied AI & Distributed Systems ✨"
  ];

  let lineIdx = 0;
  let charIdx = 0;
  let isDeleting = false;
  let typingSpeed = 80;

  function type() {
    const current = lines[lineIdx % lines.length];

    if (isDeleting) {
      charIdx--;
      el.textContent = current.substring(0, charIdx);
      typingSpeed = 35;
    } else {
      charIdx++;
      el.textContent = current.substring(0, charIdx);
      typingSpeed = 75;
    }

    if (!isDeleting && charIdx === current.length) {
      typingSpeed = 2200; // Hold at full text
      isDeleting = true;
    } else if (isDeleting && charIdx === 0) {
      isDeleting = false;
      lineIdx++;
      typingSpeed = 400; // Pause before next line
    }

    setTimeout(type, typingSpeed);
  }

  type();
}

// =============================================================================
// 2. CODING VIBES & MUSIC PLAYER
// =============================================================================
function initMusicPlayer() {
  const tracks = [
    {
      title: "Blinding Lights",
      artist: "The Weeknd • After Hours",
      url: "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/19/d6/60/19d660ff-e3a9-8377-15a3-ce4b28e89cac/mzaf_18422426156481158187.plus.aac.p.m4a"
    },
    {
      title: "Starboy (ft. Daft Punk)",
      artist: "The Weeknd • Starboy",
      url: "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/11/71/d6/1171d6ad-3c96-e027-2af6-58028426588c/mzaf_15137631797407745471.plus.aac.p.m4a"
    },
    {
      title: "Save Your Tears",
      artist: "The Weeknd • After Hours",
      url: "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/8b/38/17/8b3817e4-c0e9-7e02-2654-3e2ecee93603/mzaf_18415642125637540903.plus.aac.p.m4a"
    },
    {
      title: "Die For You",
      artist: "The Weeknd • Starboy",
      url: "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview221/v4/50/50/1a/50501a86-bd74-e90d-8a56-68c9b5e6e7d6/mzaf_4588197682084244913.plus.aac.p.m4a"
    },
    {
      title: "Call Out My Name",
      artist: "The Weeknd • My Dear Melancholy,",
      url: "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/d5/0a/ca/d50aca46-f871-b774-077a-22cbb42df336/mzaf_7520446500958405524.plus.aac.p.m4a"
    },
    {
      title: "Out of Time",
      artist: "The Weeknd • Dawn FM",
      url: "https://audio-ssl.itunes.apple.com/itunes-assets/AudioPreview211/v4/79/b8/43/79b84369-15c3-5a5a-fb72-2334b00826e6/mzaf_4381874253449656759.plus.aac.p.m4a"
    }
  ];

  let currentTrackIdx = 0;
  let isPlaying = false;
  const audio = new Audio();
  audio.volume = 0.65;

  const playBtn = document.getElementById('playBtn');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const trackEl = document.getElementById('musicTrack');
  const artistEl = document.getElementById('musicArtist');
  const visualizer = document.getElementById('visualizer');

  function loadTrack(index) {
    currentTrackIdx = (index + tracks.length) % tracks.length;
    const t = tracks[currentTrackIdx];
    audio.src = t.url;
    if (trackEl) trackEl.textContent = t.title;
    if (artistEl) artistEl.textContent = t.artist;
  }

  let audioCtx = null;
  let synthInterval = null;

  function playSynthChordProgression() {
    if (!audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioContext();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }

    // 80s Synthwave / The Weeknd Mood: Dm - C - Bb - F progression
    const chords = [
      [146.83, 220.00, 293.66, 349.23], // Dm
      [130.81, 196.00, 261.63, 329.63], // C
      [116.54, 174.61, 233.08, 293.66], // Bb
      [174.61, 220.00, 261.63, 349.23]  // F
    ];

    let chordIdx = 0;
    function playChord() {
      if (!isPlaying) return;
      const notes = chords[chordIdx % chords.length];
      chordIdx++;

      notes.forEach((freq) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        const filter = audioCtx.createBiquadFilter();

        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(800, audioCtx.currentTime);

        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);

        gain.gain.setValueAtTime(0, audioCtx.currentTime);
        gain.gain.linearRampToValueAtTime(0.035, audioCtx.currentTime + 0.2);
        gain.gain.exponentialRampToValueAtTime(0.0001, audioCtx.currentTime + 3.6);

        osc.connect(filter);
        filter.connect(gain);
        gain.connect(audioCtx.destination);

        osc.start();
        osc.stop(audioCtx.currentTime + 3.8);
      });
    }

    playChord();
    synthInterval = setInterval(playChord, 3600);
  }

  function stopSynthProgression() {
    if (synthInterval) {
      clearInterval(synthInterval);
      synthInterval = null;
    }
  }

  function togglePlay() {
    if (isPlaying) {
      audio.pause();
      stopSynthProgression();
      isPlaying = false;
      if (playBtn) playBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>';
      if (visualizer) visualizer.classList.remove('playing');
    } else {
      loadTrack(currentTrackIdx);
      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise.then(() => {
          isPlaying = true;
          if (visualizer) visualizer.classList.add('playing');
          if (playBtn) playBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>';
        }).catch(() => {
          // Fallback to procedural synth chord progression
          isPlaying = true;
          playSynthChordProgression();
          if (visualizer) visualizer.classList.add('playing');
          if (playBtn) playBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>';
        });
      }
    }
  }

  if (playBtn) playBtn.addEventListener('click', togglePlay);
  if (prevBtn) prevBtn.addEventListener('click', () => {
    loadTrack(currentTrackIdx - 1);
    if (isPlaying) { audio.play().catch(playSynthChordProgression); }
  });
  if (nextBtn) nextBtn.addEventListener('click', () => {
    loadTrack(currentTrackIdx + 1);
    if (isPlaying) { audio.play().catch(playSynthChordProgression); }
  });
  audio.addEventListener('ended', () => {
    loadTrack(currentTrackIdx + 1);
    audio.play().catch(playSynthChordProgression);
  });

  loadTrack(0);
}

// =============================================================================
// 3. CV MODAL & COPY ACTIONS
// =============================================================================
function initModals() {
  const cvModal = document.getElementById('cvModal');
  const openCvBtns = document.querySelectorAll('.open-cv-btn');
  const closeCvBtn = document.getElementById('closeCvBtn');
  const copyEmailBtns = document.querySelectorAll('.copy-email-btn');

  openCvBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (cvModal) {
        cvModal.classList.add('open');
        document.body.style.overflow = 'hidden';
      }
    });
  });

  if (closeCvBtn && cvModal) {
    closeCvBtn.addEventListener('click', () => {
      cvModal.classList.remove('open');
      document.body.style.overflow = '';
    });

    cvModal.addEventListener('click', (e) => {
      if (e.target === cvModal) {
        cvModal.classList.remove('open');
        document.body.style.overflow = '';
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && cvModal.classList.contains('open')) {
        cvModal.classList.remove('open');
        document.body.style.overflow = '';
      }
    });
  }

  copyEmailBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const email = 'ngtaiphat1501@gmail.com';
      navigator.clipboard.writeText(email).then(() => {
        showToast('✓ Đã sao chép email: ' + email);
      }).catch(() => {
        showToast('Email: ' + email);
      });
    });
  });
}

// =============================================================================
// 4. REAL-TIME CẦN THƠ CLOCK
// =============================================================================
function initTimeClock() {
  const clockEl = document.getElementById('canthoTime');
  if (!clockEl) return;

  function update() {
    const now = new Date();
    const options = {
      timeZone: 'Asia/Ho_Chi_Minh',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    };
    clockEl.textContent = new Intl.DateTimeFormat('vi-VN', options).format(now);
  }

  update();
  setInterval(update, 1000);
}

// =============================================================================
// 5. TOAST NOTIFICATION
// =============================================================================
function showToast(msg) {
  let toast = document.querySelector('.toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast';
    document.body.appendChild(toast);
  }

  toast.textContent = msg;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 3000);
}
