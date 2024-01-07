'use strict';

// Globals inherited from HTML:
// - displayName
// - accessLevel

// Will be set by onYouTubeIframeAPIReady
var player = null;

/*
 * Main initialization procedure
 */
document.addEventListener("DOMContentLoaded", function()
{

  // Save access level
  const main = document.querySelector(".main");

  // Display no-vid message if no vid
  if (getVid() == "") {
    document.querySelector("#no-vid").hidden = false;
  }

  // Initialize each talk (event listeners, control state)
  const talks = document.querySelectorAll(".talk");
  for (const talk of talks) {

    // Header expand/collapse
    const header = talk.querySelector(".talk-header");
    header.addEventListener("click", () => { talk.classList.toggle("active"); });

    // Talk times
    const talkTimes = talk.querySelectorAll(".talk-time");
    for (const talkTime of talkTimes) {
      const timeInput = talkTime.querySelector(".talk-time-input");
      const timeSeek = talkTime.querySelector(".talk-time-seek");
      const timeSample = talkTime.querySelector(".talk-time-sample");
      const timeThumbnail = talkTime.querySelector(".talk-time-thumbnail");
      console.log("fwefwef");

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
      if (timeThumbnail) {
        timeThumbnail.addEventListener("click", () => {
          console.log("qwerty");
          if (player == null) {
            return;
          }
          const timeStr = convertTimeInput(player.getCurrentTime()); // need to save this current time into a variable
          sendThumbnail(timeStr, talk);
        })
      }
      
      timeInput.addEventListener("change", () => { sendTalkState(talk); });
      timeInput.value = convertTimeInput(timeInput.dataset.initial);
    }

    // Edit status
    const editStatuses = talk.querySelectorAll(".edit-status input");
    console.log("FHIEOWFJIOE");
    for (const editStatus of editStatuses) {
      editStatus.addEventListener("change", () => {
        sendTalkState(talk);
        updateTalkColor(talk);
      });
    }

    // Review status
    const reviewStatuses = talk.querySelectorAll(".review-status input");
    console.log("FHIEOWFJIOE");
    for (const reviewStatus of reviewStatuses) {
      reviewStatus.addEventListener("change", () => {
        sendReview(talk);
        updateTalkColor(talk);
      });
    }

    // Notes initialized to their textcontent (from backend)
    const notes = talk.querySelector(".notes");
    notes.value = notes.textContent;

    // Notes save button
    const notesSaveButton = talk.querySelector(".notes-save");
    notesSaveButton.addEventListener("click", (e) => {
      sendNotes(talk, notes, notesSaveButton);
      e.preventDefault();
    });
    // Enable save button on any input
    notes.addEventListener("input", () => { notesSaveButton.disabled = false; });
    // Do full reevaluation upon losing focus
    notes.addEventListener("blur", () => { updateNotesSaveButton(talk); });

    // Update header color
    updateTalkColor(talk);

    // Update state of the controls
    updateTalkControls(talk);
  }
});

function getVid() {
  return document.querySelector("#player").dataset.vid;
}

function onYouTubeIframeAPIReady() {
  const vid = getVid();
  if (vid != "") {

    let width = 640;

    // Attempt at responsiveness. 480px is threshold for single column.
    if (window.screen.width <= 480) {
      // In single-column, make video width ~= 90% of screen width
      width = Math.round(window.screen.width * 0.9);
    } else {
      // In double-column, give the talk side at least 480 px
      let allowance = window.screen.width - 480;
      allowance *= 0.9;
      width = Math.min(width, allowance);
    }
    let height = Math.round(width * 0.5625);
    console.log(height, width);

    player = new YT.Player("player", {
      height: height.toString(),
      width: width.toString(),
      videoId: vid,
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
  console.log("FJOIEWJFOEWJFOWEFjOW")
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
      } else {
        updateTalkControls(talk);
        updateLastEditedBy(talk, displayName);
      }
    });
}

function sendThumbnail(time, talk) {
  const talkId = talk.dataset.id;
  const thumbnail = time;

  const formData = new FormData();
  formData.append("id", talkId);
  formData.append("thumbnail", thumbnail);
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
      } else {
        updateTalkControls(talk);
        updateLastEditedBy(talk, displayName);
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
        updateTalkControls(talk);
      }
    });
}

/*
 * Assert color of the talk header
 *
 * Based on combination of edit and review status
 */
function updateTalkColor(talk) {
  console.log("FHIEOWFJIOE");
  const talkId = talk.dataset.id;
  const editStatus = talk.querySelector("input[name='edit-status-" + talkId + "']:checked").value;
  const reviewStatus = talk.querySelector("input[name='review-status-" + talkId + "']:checked").value;
  const header = talk.querySelector(".talk-header");
  header.classList.remove(
    "header-incomplete",
    "header-done",
    "header-unusable",
    "header-done-reviewing",
    "header-unusable-reviewing",
  );

  // Talk header color depends on the combination of edit and review status
  let talkClass = "header-incomplete";

  if (reviewStatus == "reviewing") {

    if (editStatus == "done") {
      talkClass = "header-done-reviewing";
    } else if (editStatus == "unusable") {
      talkClass = "header-unusable-reviewing";
    }

  } else if (reviewStatus == "done") {
    talkClass = "header-done";

  } else if (reviewStatus == "unusable") {
    talkClass = "header-unusable";
  }

  header.classList.add(talkClass);
}

/*
 * Set all of a talk controls' disabled state
 */
function disableTalkControls(talk, disabled) {
  talk.querySelectorAll(".talk-contents input").forEach((e) => { e.disabled = disabled; });
  talk.querySelectorAll(".talk-contents button").forEach((e) => { e.disabled = disabled; });
  talk.querySelectorAll(".talk-contents textarea").forEach((e) => { e.disabled = disabled; });
  if (!disabled) {
    updateNotesSaveButton(talk);
  }
}

/*
 * Assert what talk controls are enabled, based on:
 *
 * - Existence of VID
 * - User's access level
 * - Talk's edit status
 * - Talk's review status
 *
 * The backend does its own enforcement, but this implementation on the
 * frontend makes it more obvious what's allowed and what's not.
 */
function updateTalkControls(talk) {
  const talkId = talk.dataset.id;

  // If no VID, all edits disabled. We don't condition on the validity of VID
  // because we can't guarantee the Youtube iframe API works - the video might
  // be valid and can be viewed externally. In that case, allow edits anyway
  // instead of throwing out everything.
  if (getVid() == "") {
    disableTalkControls(talk, true);
  }

  // Editors: More controls are restricted
  else if (accessLevel == 1) {
    const reviewStatus = talk.querySelector("input[name='review-status-" + talkId + "']:checked").value;

    // If review status is reviewed, disable almost everything. Except the play buttons. :)
    if (reviewStatus != "reviewing") {
      disableTalkControls(talk, true);
      talk.querySelectorAll("button.talk-time-seek").forEach((e) => { e.disabled = false; });
    }

    // Otherwise, enable almost everything, except reviewing
    else {
      disableTalkControls(talk, false);
      talk.querySelectorAll(".review-status input").forEach((e) => { e.disabled = true; });
    }

  }

  // Reviewers/admins: Controls only mildly restricted in specific cases
  else if (accessLevel >= 2) {
    const editStatus = talk.querySelector("input[name='edit-status-" + talkId + "']:checked").value;
    const reviewStatus = talk.querySelector("input[name='review-status-" + talkId + "']:checked").value;

    // If review status is reviewed, disable most edit controls. Force reviewers to
    // unreview before editing. Not disabled:
    // - play button
    // - notes
    // - review status
    if (reviewStatus != "reviewing") {
      disableTalkControls(talk, true);
      talk.querySelectorAll("button.talk-time-seek").forEach((e) => { e.disabled = false; });
      talk.querySelectorAll("button.talk-time-thumbnail").forEach((e) => { e.disabled = false; });
      talk.querySelector(".notes").disabled = false;
      updateNotesSaveButton(talk);
      talk.querySelectorAll(".review-status input").forEach((e) => { e.disabled = false; });
    }

    // Otherwise, enable everything
    else {
      disableTalkControls(talk, false);
    }
  }
}

/*
 * Sets last edited by to current given name
 */
function updateLastEditedBy(talk, name) {
  const nameEle = talk.querySelector(".last-edited-by");
  nameEle.textContent = name;
}

function sendNotes(talk, notes, notesSaveButton) {
  const talkId = talk.dataset.id;
  const value = notes.value;

  const formData = new FormData();
  formData.append("id", talkId);
  formData.append("notes", value);
  console.log("Saving notes for " + talkId);
  fetch("/notes", {
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
        updateNotesSaveButton(talk);
      }
    });
}

/*
 * Assert state of the notes save button.
 *
 * If the notes area is disabled, the button should be too. If not, it may or
 * may not be - depending on if there are unsaved edits.
 */
function updateNotesSaveButton(talk)
{
  const notes = talk.querySelector(".notes");
  const notesSaveButton = talk.querySelector(".notes-save");

  if (notes.disabled) {
    notesSaveButton.disabled = true;
  }

  else {
    notesSaveButton.disabled = (notes.value == notes.textContent);
  }
}
