/*
 * Site-wide behaviour (the CSP blocks inline script). Loaded at the end of
 * body.
 */
// data-confirm asks first, so no delete submits unconfirmed.
// Registered before anything here can throw.
document.addEventListener("submit", (e) => {
	const message = e.target.dataset.confirm;
	if (message && !confirm(message)) {
		e.preventDefault();
	}
});

initDisclosure(document.querySelector(".topbar__toggle"), {
	labels: { open: "Close menu", closed: "Open menu" },
	// 768px is also in components.css; keep the two in step.
	closeAbove: "(min-width: 768px)",
});
initDisclosure(document.querySelector(".topbar__avatar"));

// Toggles its aria-controls panel; the stylesheet reads aria-expanded.
function initDisclosure(button, { labels, closeAbove } = {}) {
	const panel = button && document.getElementById(button.getAttribute("aria-controls"));
	if (!panel) return;

	const isOpen = () => button.getAttribute("aria-expanded") === "true";
	const setOpen = (open) => {
		button.setAttribute("aria-expanded", String(open));
		if (labels) {
			button.setAttribute("aria-label", open ? labels.open : labels.closed);
		}
	};

	button.addEventListener("click", () => setOpen(!isOpen()));

	document.addEventListener("click", (event) => {
		if (isOpen() && !button.contains(event.target) && !panel.contains(event.target)) {
			setOpen(false);
		}
	});

	window.addEventListener("keydown", (event) => {
		if (event.key === "Escape" && isOpen()) {
			setOpen(false);
			button.focus();
		}
	});

	// The button is hidden above this width; do not leave it saying "open".
	if (closeAbove) {
		window.matchMedia(closeAbove).addEventListener("change", (event) => {
			if (event.matches) setOpen(false);
		});
	}
}
