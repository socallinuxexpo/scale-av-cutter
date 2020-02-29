'use strict';

function parseTimeInput(timeStr) {
  if (!timeStr) {
    return null;
  }
  const re = /^([0-9]?[0-9]):([0-5]?[0-9]):([0-5]?[0-9])$/;
  const match = timeStr.match(re);
  if (!match) {
    return null;
  }
  return parseInt(match[1]) * 3600 +
         parseInt(match[2]) * 60 +
         parseInt(match[3]);
}

function convertTimeInput(timestamp) {
  if (!timestamp) {
    timestamp = 0;
  }
  const hours = Math.floor(timestamp / 3600);
  const minutes = Math.floor((timestamp % 3600) / 60);
  const seconds = Math.floor(timestamp % 60);

  return String(hours) + ":" +
         String(minutes).padStart(2, '0') + ":" +
         String(seconds).padStart(2, '0');
}

function sendCutState(cut) {
  const cutId = cut.dataset.id;
  const start = parseTimeInput(cut.querySelector('.cut-time-start .cut-time-input').value);
  const end = parseTimeInput(cut.querySelector('.cut-time-end .cut-time-input').value);
  const cutStatus = cut.querySelector("input[name='cut-status-" + cutId + "']:checked").value;

  const formData = new FormData();
  formData.append("id", cutId);
  formData.append("start", start);
  formData.append("end", end);
  formData.append("status", cutStatus);
  console.log("Sending update for " + cutId);
  fetch('/edit', {
    method: "POST",
    body: formData
  })
    .then((response) => {
      return response.json();
    })
    .then((data) => {
      console.log(data);
    });
}

function updateCutColor(cut) {
  const cutId = cut.dataset.id;
  const header = cut.querySelector(".cut-header");
  const cutStatus = cut.querySelector("input[name='cut-status-" + cutId + "']:checked").value;
  header.classList.remove("btn-success", "btn-secondary", "btn-warning");

  if (cutStatus == "done") {
    header.classList.add("btn-success");
  } else if (cutStatus == "unusable") {
    header.classList.add("btn-warning");
  } else {
    header.classList.add("btn-secondary");
  }
}

// Initialize player
var player = null;
function onYouTubeIframeAPIReady() {
  const playerDiv = document.querySelector("#player");
  player = new YT.Player('player', {
    height: '360',
    width: '640',
    videoId: playerDiv.dataset.vid,
    host: 'https://www.youtube-nocookie.com',
  });
}

// Initialize each cut
const cuts = document.querySelectorAll(".cut");
for (const cut of cuts) {
  const cutId = cut.dataset.id;

  // Update its color
  updateCutColor(cut);

  // Header expand/collapse
  const header = cut.querySelector(".cut-header");
  const contents = cut.querySelector(".cut-contents");
  header.addEventListener("click", () => {
    header.classList.toggle("active");
    if (contents.style.display === "block") {
      contents.style.display = "none";
    } else {
      contents.style.display = "block";
    }
  });

  // Cut times
  const cutTimes = cut.querySelectorAll(".cut-time");
  for (const cutTime of cutTimes) {
    const timeInput = cutTime.querySelector('.cut-time-input');
    const timeSeek = cutTime.querySelector('.cut-time-seek');
    const timeSample = cutTime.querySelector('.cut-time-sample');
    timeSeek.addEventListener("click", () => {
      const timestamp = parseTimeInput(timeInput.value);
      if (timestamp === null) {
      } else {
        player.seekTo(timestamp, true);
      }
    });
    timeSample.addEventListener("click", () => {
      const origValue = timeInput.value;
      const timeStr = convertTimeInput(player.getCurrentTime());
      if (origValue != timeStr) {
        timeInput.value = timeStr;
        timeInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    timeInput.addEventListener("change", () => { sendCutState(cut); });
    timeInput.value = convertTimeInput(timeInput.dataset.initial);
  }

  // Cut edit status
  const cutStatuses = cut.querySelectorAll("input[name='cut-status-" + cutId + "']");
  for (const cutStatus of cutStatuses) {
    cutStatus.addEventListener("change", () => {
      sendCutState(cut);
      updateCutColor(cut);
    });
  }
}

