'use strict';

// Main
document.addEventListener("DOMContentLoaded", function(){
  
  // Admin password
  const adminPassword = document.querySelector("#admin-password");
  adminPassword.addEventListener("change", () => {
    setCookie("password", adminPassword.value);
  });
  const currentPassword = getCookie("password");
  if (currentPassword != null) {
    adminPassword.value = currentPassword;
  }

  // show-hide buttons
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
});

function getCookie(name) {
  const v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
  return v ? v[2] : null;
}

function setCookie(name, value) {
  const d = new Date;
  document.cookie = name + "=" + window.escape(value);
}
