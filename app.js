/**
 * Nguyễn Phát Tài — Minimalist Portfolio Logic
 * Focused: The Weeknd Audio Player with Real Vocals, Time Clock, Clipboard
 */

document.addEventListener('DOMContentLoaded', () => {
  initMusicPlayer();
  initCopyEmail();
  initTimeClock();
});

// =============================================================================
// 1. THE WEEKND MUSIC PLAYER (REAL VOCALS VIA APPLE MUSIC CDN)
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
  audio.volume = 0.70;

  const playBtn = document.getElementById('playBtn');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const trackEl = document.getElementById('musicTrack');
  const artistEl = document.getElementById('musicArtist');
  const visualizer = document.getElementById('visualizer');
  const vinylDisc = document.getElementById('vinylDisc');

  function loadTrack(index) {
    currentTrackIdx = (index + tracks.length) % tracks.length;
    const t = tracks[currentTrackIdx];
    audio.src = t.url;
    if (trackEl) trackEl.textContent = t.title;
    if (artistEl) artistEl.textContent = t.artist;
  }

  function togglePlay() {
    if (isPlaying) {
      audio.pause();
      isPlaying = false;
      if (playBtn) playBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>';
      if (visualizer) visualizer.classList.remove('playing');
      if (vinylDisc) vinylDisc.classList.remove('playing');
    } else {
      loadTrack(currentTrackIdx);
      audio.play().then(() => {
        isPlaying = true;
        if (visualizer) visualizer.classList.add('playing');
        if (vinylDisc) vinylDisc.classList.add('playing');
        if (playBtn) playBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>';
      }).catch(err => {
        console.warn("Audio playback issue:", err);
      });
    }
  }

  if (playBtn) playBtn.addEventListener('click', togglePlay);
  
  if (prevBtn) prevBtn.addEventListener('click', () => {
    loadTrack(currentTrackIdx - 1);
    if (isPlaying) { audio.play(); }
  });

  if (nextBtn) nextBtn.addEventListener('click', () => {
    loadTrack(currentTrackIdx + 1);
    if (isPlaying) { audio.play(); }
  });

  audio.addEventListener('ended', () => {
    loadTrack(currentTrackIdx + 1);
    audio.play();
  });

  loadTrack(0);
}

// =============================================================================
// 2. COPY EMAIL ACTION
// =============================================================================
function initCopyEmail() {
  const copyBtns = document.querySelectorAll('.copy-email-btn');
  const email = 'ngtaiphat1501@gmail.com';

  copyBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      navigator.clipboard.writeText(email).then(() => {
        showToast('✓ Đã sao chép email: ' + email);
      }).catch(() => {
        showToast('Email: ' + email);
      });
    });
  });
}

// =============================================================================
// 3. REAL-TIME CẦN THƠ CLOCK
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
// 4. TOAST NOTIFICATION
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
  }, 2800);
}
