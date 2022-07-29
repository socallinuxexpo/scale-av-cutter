'use strict';

// Will be set by onYouTubeIframeAPIReady
var player = null;

// Main
document.addEventListener("DOMContentLoaded", function(){
  // Initialize each talk
  const talks = document.querySelectorAll(".talk");
  for (const talk of talks) {
    const talkId = talk.dataset.id;

    // Update its color
    updateTalkColor(talk);

    // Header expand/collapse
    const header = talk.querySelector(".talk-header");
    const contents = talk.querySelector(".talk-contents");
    header.addEventListener("click", () => {
      header.classList.toggle("active");
      if (contents.style.display === "block") {
        contents.style.display = "none";
      } else {
        contents.style.display = "block";
      }
    });

    // Talk times
    const talkTimes = talk.querySelectorAll(".talk-time");
    for (const talkTime of talkTimes) {
      const timeInput = talkTime.querySelector(".talk-time-input");
      const timeSeek = talkTime.querySelector(".talk-time-seek");
      const timeSample = talkTime.querySelector(".talk-time-sample");
      timeSeek.addEventListener("click", () => {
        if (player == null) {
          return;
        }
        const timestamp = parseTimeInput(timeInput.value);
        if (timestamp != null) {
          player.seekTo(timestamp, true);
        }
      });
      timeSample.addEventListener("click", () => {
        if (player == null) {
          return;
        }
        const origValue = timeInput.value;
        const timeStr = convertTimeInput(player.getCurrentTime());
        if (origValue != timeStr) {
          timeInput.value = timeStr;
          timeInput.dispatchEvent(new Event("change", { bubbles: true }));
        }
      });
      timeInput.addEventListener("change", () => { sendTalkState(talk); });
      timeInput.value = convertTimeInput(timeInput.dataset.initial);
    }

    // Edit status
    const editStatuses = talk.querySelectorAll("input[name='edit-status-" + talkId + "']");
    for (const editStatus of editStatuses) {
      editStatus.addEventListener("change", () => {
        sendTalkState(talk);
        updateTalkColor(talk);
      });
    }

    // Review status
    const reviewStatuses = talk.querySelectorAll("input[name='review-status-" + talkId + "']");
    for (const reviewStatus of reviewStatuses) {
      if (!reviewStatus.disabled) {
        reviewStatus.addEventListener("change", () => {
          sendReview(talk);
        });
      }
    }

    // Notes initialized to their textcontent
    const notes = talk.querySelector(".notes");
    notes.value = notes.textContent;

    // Notes save button
    const notesSaveButton = talk.querySelector(".notes-save");
    notesSaveButton.addEventListener("click", (e) => {
      saveNotes(talk, notes, notesSaveButton);
      e.preventDefault();
    });
    // Disabled by default
    disableNotesSaveButton(notesSaveButton);
    // Enables save button on any input
    notes.addEventListener("input", () => {
      enableNotesSaveButton(notesSaveButton);
    });
    // Small QoL that re-disables button if content is same. We're abusing
    // textContent to store the "saved" version.
    notes.addEventListener("blur", () => {
      if (notes.value == notes.textContent) {
        disableNotesSaveButton(notesSaveButton);
      }
    });
  }
});

function onYouTubeIframeAPIReady() {
  const playerDiv = document.querySelector("#player");
  const vid = playerDiv.dataset.vid;

  if (vid == "") {
    document.querySelector("#no-vid").hidden = false;
    for (let ele of document.querySelectorAll(".talk-contents input")) {
        ele.disabled = true;
    }
    for (let ele of document.querySelectorAll(".talk-time button")) {
        ele.disabled = true;
    }

  } else {
    player = new YT.Player("player", {
      height: "360",
      width: "640",
      videoId: playerDiv.dataset.vid,
      host: "https://www.youtube-nocookie.com",
    });
  }
}

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
         String(minutes).padStart(2, "0") + ":" +
         String(seconds).padStart(2, "0");
}

function sendTalkState(talk) {
  const talkId = talk.dataset.id;
  const start = parseTimeInput(talk.querySelector(".talk-time-start .talk-time-input").value);
  const end = parseTimeInput(talk.querySelector(".talk-time-end .talk-time-input").value);
  const editStatus = talk.querySelector("input[name='edit-status-" + talkId + "']:checked").value;

  const formData = new FormData();
  formData.append("id", talkId);
  formData.append("start", start);
  formData.append("end", end);
  formData.append("status", editStatus);
  console.log("Sending update for " + talkId);
  fetch("/edit", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      return response.json();
    })
    .then((data) => {
      if (data.error != null) {
        window.alert("ERROR: " + data.error);
      }
    });
}

function sendReview(talk) {
  const talkId = talk.dataset.id;
  const reviewStatus = talk.querySelector("input[name='review-status-" + talkId + "']:checked").value;

  const formData = new FormData();
  formData.append("id", talkId);
  formData.append("status", reviewStatus);
  console.log("Sending review for " + talkId);
  fetch("/review", {
    method: "POST",
    body: formData,
    credentials: "same-origin",
  })
    .then((response) => {
      return response.json();
    })
    .then((data) => {
      if (data.error != null) {
        window.alert("ERROR: " + data.error);
      } else {
        setTalkEdits(talk, (reviewStatus == "approved"));
      }
    });
}

function updateTalkColor(talk) {
  const talkId = talk.dataset.id;
  const header = talk.querySelector(".talk-header");
  const editStatus = talk.querySelector("input[name='edit-status-" + talkId + "']:checked").value;
  header.classList.remove("btn-success", "btn-secondary", "btn-warning");

  if (editStatus == "done") {
    header.classList.add("btn-success");
  } else if (editStatus == "unusable") {
    header.classList.add("btn-warning");
  } else {
    header.classList.add("btn-secondary");
  }
}

function setTalkEdits(talk, disabled) {
  for (let ele of talk.querySelectorAll(".edit-status input")) {
    ele.disabled = disabled;
  }
  for (let ele of talk.querySelectorAll("button.talk-time-sample")) {
    ele.disabled = disabled;
  }
}

function saveNotes(talk, notes, notesSaveButton) {
  const talkId = talk.dataset.id;
  const value = notes.value;

  const formData = new FormData();
  formData.append("id", talkId);
  formData.append("notes", value);
  console.log("Saving notes for " + talkId);
  fetch("/save_notes", {
    method: "POST",
    body: formData,
  })
    .then((response) => {
      return response.json();
    })
    .then((data) => {
      if (data.error != null) {
        window.alert("ERROR: " + data.error);
      }
      else {
        notes.textContent = value;
        disableNotesSaveButton(notesSaveButton);
      }
    });
}

function disableNotesSaveButton(button)
{
  if (!button.disabled) {
    button.disabled = true;
    button.classList.remove("btn-primary");
    button.classList.add("btn-secondary");
  }
}

function enableNotesSaveButton(button)
{
  if (button.disabled) {
    button.disabled = false;
    button.classList.add("btn-primary");
    button.classList.remove("btn-secondary");
  }
}
