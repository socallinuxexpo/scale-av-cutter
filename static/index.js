'use strict';

// Main
document.addEventListener("DOMContentLoaded", function(){

  // Show-hide buttons
  const showHideButtons = document.querySelectorAll(".show-hide");
  for (const showHideButton of showHideButtons) {
    const field = showHideButton.previousElementSibling;
    const setVisible = showHideButton.querySelector(".show-hide-set-visible");
    const setHidden = showHideButton.querySelector(".show-hide-set-hidden");
    if (field != null && field.tagName == "INPUT") {
      showHideButton.addEventListener("click", () => {
        const type = field.getAttribute("type");
        if (type === "text") {
          field.setAttribute("type", "password");
          setVisible.hidden = false;
          setHidden.hidden = true;
        } else if (type === "password") {
          field.setAttribute("type", "text");
          setVisible.hidden = true;
          setHidden.hidden = false;
        }
      });
    }
  }

  
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
