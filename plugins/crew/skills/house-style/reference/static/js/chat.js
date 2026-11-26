/*
 * The assistant screen's layout: its drawers, a chat row's menu and the
 * starter cards. Loaded by chat.html after site.js. Sending, streaming and
 * building a turn are the project's own script.
 */
initDrawers();
initRowMenus();
initStarterCards();

// A [data-drawer] button opens its aria-controls panel as a drawer.
// data-drawer-wide: the width where the panel is a column instead.
// One open at a time.
function initDrawers() {
	const triggers = document.querySelectorAll("[data-drawer]");
	if (!triggers.length) return;

	const scrim = document.querySelector("[data-drawer-scrim]");
	const wide = new Map();
	let open = null; // { panel, trigger }

	// An open drawer is modal: everything beside it (and its ancestors) is
	// inert, so Tab and a screen reader stay inside. The scrim stays live
	// to take the closing click.
	let inertMade = [];
	const setBackgroundInert = (panel) => {
		inertMade.forEach((el) => { el.inert = false; });
		inertMade = [];
		for (let node = panel; node && node !== document.body; node = node.parentElement) {
			for (const sibling of node.parentElement?.children ?? []) {
				if (sibling !== node && sibling !== scrim && !sibling.inert) {
					sibling.inert = true;
					inertMade.push(sibling);
				}
			}
		}
	};

	const setOpen = (panel, trigger, shouldOpen) => {
		if (shouldOpen && open && open.panel !== panel) {
			setOpen(open.panel, open.trigger, false);
		}
		const hadFocus = panel.contains(document.activeElement);
		const isWide = wide.get(trigger).matches;
		open = shouldOpen ? { panel, trigger } : (open?.panel === panel ? null : open);

		panel.classList.toggle("is-open", shouldOpen);
		trigger.setAttribute("aria-expanded", String(shouldOpen));
		document.body.classList.toggle("drawer-open", Boolean(open));
		scrim?.classList.toggle("is-visible", Boolean(open));
		// Cleared before focus returns to the trigger, which sits behind it.
		setBackgroundInert(open && !isWide ? panel : null);

		if (shouldOpen && !isWide) {
			panel.focus();
		} else if (!shouldOpen && hadFocus && !isWide) {
			trigger.focus();
		}
	};

	const closeOpen = () => {
		if (!open) return;
		const { panel, trigger } = open;
		setOpen(panel, trigger, false);
		trigger.focus();
	};

	triggers.forEach((trigger) => {
		const panel = document.getElementById(trigger.getAttribute("aria-controls"));
		if (!panel) return;

		const query = window.matchMedia(trigger.dataset.drawerWide || "(min-width: 901px)");
		wide.set(trigger, query);
		// Wider than this the panel is a column: close its drawer.
		query.addEventListener("change", (event) => {
			if (event.matches && open?.trigger === trigger) setOpen(panel, trigger, false);
		});

		trigger.addEventListener("click", () => setOpen(panel, trigger, !panel.classList.contains("is-open")));
		panel.querySelector("[data-drawer-close]")?.addEventListener("click", () => setOpen(panel, trigger, false));
	});

	scrim?.addEventListener("click", closeOpen);
	window.addEventListener("keydown", (event) => {
		if (event.key === "Escape") closeOpen();
	});
}

// The ⋮ beside a chat: the stylesheet reads aria-expanded. Delegated, so
// rows loaded later work too. One open at a time.
function initRowMenus() {
	const closeAll = (except) => {
		document.querySelectorAll('.chat-row__menu[aria-expanded="true"]').forEach((button) => {
			if (button !== except) button.setAttribute("aria-expanded", "false");
		});
	};

	document.addEventListener("click", (event) => {
		const button = event.target.closest(".chat-row__menu");
		closeAll(button);
		if (!button) return;
		button.setAttribute("aria-expanded", String(button.getAttribute("aria-expanded") !== "true"));
		// Opens upwards when the scrolling list has no room below the row.
		const list = button.nextElementSibling;
		const scroller = button.closest(".chat-history");
		if (list && scroller) {
			list.classList.remove("chat-menu__list--up");
			list.classList.toggle(
				"chat-menu__list--up",
				list.getBoundingClientRect().bottom > scroller.getBoundingClientRect().bottom,
			);
		}
	});

	window.addEventListener("keydown", (event) => {
		if (event.key !== "Escape") return;
		const button = document.querySelector('.chat-row__menu[aria-expanded="true"]');
		if (button) {
			closeAll();
			button.focus();
		}
	});
}

// A starter card fills the box and never sends, and only fills an empty
// box, so it cannot replace something typed.
function initStarterCards() {
	const box = document.querySelector(".composer textarea");
	if (!box) return;

	document.addEventListener("click", (event) => {
		const card = event.target.closest("[data-starter]");
		if (!card || box.value.trim()) return;
		box.value = card.textContent.trim();
		box.dispatchEvent(new Event("input", { bubbles: true }));
		box.focus();
	});
}
