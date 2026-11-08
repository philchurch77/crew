// Saves the observation body while the teacher types on the edit page, so a
// closed tab never loses a long note. Warns before leaving with unsaved text.
(function () {
  const form = document.querySelector("form[data-autosave-url]");
  if (!form) return;
  const body = form.querySelector("[name=body]");
  const status = document.getElementById("autosave-status");
  const csrf = form.querySelector("[name=csrfmiddlewaretoken]").value;
  let saved = body.value;
  let timer = null;

  function postBody(text) {
    return fetch(form.dataset.autosaveUrl, {
      method: "POST",
      headers: { "X-CSRFToken": csrf },
      body: new URLSearchParams({ body: text }),
    }).then((r) =>
      r.json().catch(() => ({})).then((data) => {
        if (!r.ok) throw Object.assign(new Error("save failed"), { status: r.status, data });
        return data;
      })
    );
  }

  function save() {
    const text = body.value;
    if (text === saved) return;
    status.textContent = "Saving…";
    postBody(text)
      .then(() => {
        saved = text;
        status.textContent = "Saved";
      })
      .catch((err) => {
        status.textContent =
          err.status === 401 || err.status === 403
            ? "You have been signed out. Copy your text before you reload."
            : "Not saved yet. Keep this tab open.";
      });
  }

  body.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(save, 1000);
  });
  window.addEventListener("beforeunload", (e) => {
    if (body.value !== saved) {
      e.preventDefault();
      e.returnValue = "";
    }
  });
})();
