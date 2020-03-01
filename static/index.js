'use strict';

// Main
document.addEventListener("DOMContentLoaded", function(){
  
  // Room day stuff
  const roomdays = document.querySelectorAll(".roomday");
  for (const roomday of roomdays) {
    const vidButton = roomday.querySelector(".roomday-vid");
    const description = roomday.querySelector(".roomday-description").textContent;
    if (vidButton != null) {
      vidButton.addEventListener("click", () => {
        const vid = window.prompt("Enter the VID for " + description, roomday.dataset.vid);
        if (vid != null) {
          roomday.dataset.vid = vid;
          sendVid(roomday, vid);
        }
      });
    }
  }
});

function sendVid(roomday, vid) {
  const roomday_id = roomday.dataset.id;

  const formData = new FormData();
  formData.append("id", roomday_id);
  formData.append("vid", vid);

  fetch('/vid', {
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
        if (vid != "") {
          roomday.querySelector(".roomday-no-vid").hidden = true;
          roomday.querySelector(".roomday-status").hidden = false;
        } else {
          roomday.querySelector(".roomday-no-vid").hidden = false;
          roomday.querySelector(".roomday-status").hidden = true;
        }
      }
    });
}
