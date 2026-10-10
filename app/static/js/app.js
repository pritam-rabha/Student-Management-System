/* Shared behaviour: mobile sidebar, delete confirmation, client-side form validation. */
(function () {
  "use strict";

  var body = document.body;
  var toggle = document.getElementById("sidebar-toggle");
  var sidebar = document.getElementById("sidebar");

  function setSidebar(open) {
    body.classList.toggle("sidebar-open", open);
    if (toggle) {
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    }
    if (open && sidebar) {
      var first = sidebar.querySelector("a");
      if (first) { first.focus(); }
    } else if (!open && toggle && document.activeElement && sidebar && sidebar.contains(document.activeElement)) {
      toggle.focus();
    }
  }

  if (toggle) {
    toggle.addEventListener("click", function () {
      setSidebar(!body.classList.contains("sidebar-open"));
    });
  }
  document.querySelectorAll("[data-sidebar-close]").forEach(function (el) {
    el.addEventListener("click", function () { setSidebar(false); });
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && body.classList.contains("sidebar-open")) {
      setSidebar(false);
    }
  });

  /* Delete confirmation: one shared modal, filled in from the clicked button. */
  var deleteModal = document.getElementById("deleteModal");
  if (deleteModal) {
    deleteModal.addEventListener("show.bs.modal", function (event) {
      var trigger = event.relatedTarget;
      if (!trigger) { return; }
      document.getElementById("delete-form").setAttribute("action", trigger.getAttribute("data-delete-url"));
      document.getElementById("delete-student-name").textContent = trigger.getAttribute("data-student-name");
    });
  }

  /* Client-side validation. The server validates everything again. */
  document.querySelectorAll("form.needs-validation").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (form.checkValidity()) { return; }
      event.preventDefault();
      event.stopPropagation();
      form.classList.add("was-validated");

      var firstInvalid = null;
      form.querySelectorAll(":invalid").forEach(function (field) {
        var feedback = field.parentElement.querySelector(".invalid-feedback");
        if (feedback) {
          feedback.textContent = field.getAttribute("data-error-message") || field.validationMessage;
        }
        field.setAttribute("aria-invalid", "true");
        if (!firstInvalid) { firstInvalid = field; }
      });
      if (firstInvalid) { firstInvalid.focus(); }
    });

    form.addEventListener("input", function (event) {
      var field = event.target;
      if (field.classList && field.classList.contains("is-invalid")) {
        field.classList.remove("is-invalid");
      }
      if (field.validity && field.validity.valid) {
        field.removeAttribute("aria-invalid");
      }
    });
  });
})();
