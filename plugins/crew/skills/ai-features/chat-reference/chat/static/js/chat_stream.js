/*
 * Sending, streaming and drawing a chat (chat/chat.html). The layout's own
 * behaviour is the house style's chat.js. Everything is bound here: the
 * CSP blocks inline handlers.
 *
 * Three rules this file keeps:
 * - What anyone wrote reaches the page as text, or as markdown rendered
 *   from ESCAPED text. Never innerHTML of raw model or user text.
 * - A typed message is never lost: it is back in the box unless the
 *   server saved it.
 * - Images never load and links are not clickable unless their host is in
 *   LINK_HOSTS: a link can carry what was typed off the page.
 */
(function () {
    const page = document.querySelector("[data-chat]");
    const messages = document.getElementById("messages");
    const input = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    if (!page || !messages || !input || !sendBtn) return;

    const config = page.dataset;
    // Hosts whose links stay clickable, with their subdomains. Https only.
    const LINK_HOSTS = ["gov.uk"];
    const STATUS = /\x1e([^\x1e]*)\x1e/g;       // a whole status frame
    const STATUS_OR_OPEN = /\x1e[^\x1e]*(\x1e|$)/g; // or one split across reads

    function csrfToken() {
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : "";
    }

    function escapeHtml(text) {
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    function allowedLink(href) {
        try {
            const url = new URL(href);
            return url.protocol === "https:"
                && LINK_HOSTS.some((host) => url.hostname === host || url.hostname.endsWith("." + host));
        } catch (_) {
            return false;
        }
    }

    const FIGURE = /^[+\-−–]?£?\d[\d,]*(\.\d+)?\s*(%|pp)?$/;

    if (typeof marked !== "undefined") {
        marked.use({
            renderer: {
                link(token) {
                    if (allowedLink(token.href)) {
                        token.title = null;
                        return false; // marked's own <a>
                    }
                    const text = this.parser.parseInline(token.tokens);
                    const href = (token.href || "").replace(/[<>"]/g, "");
                    return text === href || !href ? text : `${text} (${href})`;
                },
                image(token) {
                    return token.text || "";
                },
                // Headings start at h3, under the page's own.
                heading(token) {
                    const level = Math.min(6, Math.max(3, token.depth + 1));
                    return `<h${level}>${this.parser.parseInline(token.tokens)}</h${level}>\n`;
                },
                // The house style's table: in its scroller, figures right-aligned.
                table(token) {
                    const right = token.header.map((_, i) => token.rows.length > 0
                        && token.rows.every((row) => FIGURE.test((row[i]?.text || "").trim())));
                    const cell = (c, i, tag) =>
                        `<${tag}${right[i] ? ' class="cell--right"' : ""}>${this.parser.parseInline(c.tokens)}</${tag}>`;
                    const head = token.header.map((c, i) => cell(c, i, "th")).join("");
                    const body = token.rows.map((row) =>
                        `<tr>${row.map((c, i) => cell(c, i, "td")).join("")}</tr>`).join("");
                    return '<div class="table-scroll" tabindex="0" role="region" aria-label="Table">'
                        + `<table class="table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>\n`;
                },
            },
            // No reference definitions: "[Name]: word" would vanish and
            // link every later "[Name]".
            tokenizer: { def() { return undefined; } },
        });
    }

    function setPlainText(el, text) {
        el.replaceChildren();
        for (const paragraph of text.split(/\n+/)) {
            const p = document.createElement("p");
            p.textContent = paragraph;
            el.appendChild(p);
        }
    }

    function setReply(el, text) {
        if (typeof marked === "undefined") {
            setPlainText(el, text);
        } else {
            // Escaped first: marked has no sanitizer, so raw HTML from the
            // model never survives.
            el.innerHTML = marked.parse(escapeHtml(text), { gfm: true });
        }
    }

    function scrollToEnd() {
        messages.scrollTop = messages.scrollHeight;
    }

    // Every turn, live or stored, with the markup styleguide_chat.html shows.
    function addTurn(role) {
        const div = document.createElement("div");
        div.className = `message message--${role}`;
        if (role === "assistant") {
            const head = document.createElement("div");
            head.className = "message__head";
            const mark = document.createElement("span");
            mark.className = "assistant-mark";
            mark.setAttribute("aria-hidden", "true");
            mark.textContent = (config.assistantName || "A").slice(0, 1).toUpperCase();
            const name = document.createElement("span");
            name.className = "message__name";
            name.textContent = config.assistantName || "Assistant";
            head.append(mark, name);
            div.appendChild(head);
        } else {
            const who = document.createElement("span");
            who.className = "visually-hidden";
            who.textContent = "You said: ";
            div.appendChild(who);
        }
        const body = document.createElement("div");
        body.className = "message__body";
        div.appendChild(body);
        messages.appendChild(div);
        return { div, body };
    }

    function addCopy(turn, text) {
        const actions = document.createElement("div");
        actions.className = "message__actions";
        const button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn--small";
        button.textContent = "Copy";
        const said = document.createElement("span");
        said.setAttribute("role", "status");
        button.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(text);
                said.textContent = "Copied";
            } catch (_) {
                said.textContent = "Could not copy: select the text instead.";
            }
        });
        actions.append(button, said);
        turn.appendChild(actions);
    }

    function addNotice(text) {
        const p = document.createElement("p");
        p.className = "notice notice--warn";
        p.setAttribute("role", "alert");
        p.textContent = text;
        messages.appendChild(p);
        scrollToEnd();
    }

    // The one progress line, updated in place, gone when the reply starts.
    function showStatus(label) {
        let line = document.getElementById("chat-status");
        if (!line) {
            line = document.createElement("div");
            line.id = "chat-status";
            line.className = "message message--status";
            const dots = document.createElement("span");
            dots.className = "message__dots";
            dots.setAttribute("aria-hidden", "true");
            line.append(dots, document.createElement("span"));
            messages.appendChild(line);
        }
        line.lastChild.textContent = label || "Thinking…";
        scrollToEnd();
    }

    function hideStatus() {
        document.getElementById("chat-status")?.remove();
    }

    function autoGrow() {
        input.style.height = "";
        input.style.height = input.scrollHeight + "px";
    }

    // Stored turns, from the page's JSON island.
    const stored = document.getElementById("chat-turns");
    for (const turn of stored ? JSON.parse(stored.textContent) : []) {
        const { div, body } = addTurn(turn.role);
        if (turn.role === "assistant") {
            setReply(body, turn.content);
            addCopy(div, turn.content);
        } else {
            setPlainText(body, turn.content);
        }
    }
    scrollToEnd();

    // After a reply: the sidebar, the title and the sources, from the server.
    async function refresh() {
        try {
            const url = `${config.historyUrl}?session_id=${encodeURIComponent(config.sessionKey)}`;
            const response = await fetch(url, { headers: { Accept: "application/json" } });
            if (!response.ok) return;
            const data = await response.json();
            // Our own templates' markup, auto-escaped on the server.
            document.getElementById("chat-history").innerHTML = data.history;
            document.getElementById("chat-sources-body").innerHTML = data.sources;
            if (data.title) {
                document.querySelector(".chat-header__title").textContent = data.title;
                document.querySelector("[data-chat-export]")?.removeAttribute("hidden");
            }
        } catch (_) {
            // The reply is saved; a stale sidebar is not worth an error.
        }
    }

    // One send at a time: a second stream would interleave the saved turns.
    let sending = false;

    async function send() {
        const text = input.value.trim();
        if (sending || !text) return;
        sending = true;
        sendBtn.setAttribute("aria-disabled", "true");

        // Shown before it is sent; taken back if nothing was saved.
        const mine = addTurn("user");
        setPlainText(mine.body, text);
        input.value = "";
        autoGrow();
        showStatus();

        const putBack = () => {
            if (!input.value) {
                input.value = text;
                autoGrow();
            }
            return input.value === text;
        };

        // Only a reply stream means the message was saved.
        let streaming = false;
        try {
            const response = await fetch(config.streamUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
                body: JSON.stringify({ message: text, session_key: config.sessionKey }),
            });

            const isStream = (response.headers.get("Content-Type") || "").startsWith("text/plain");
            if (!response.ok || !response.body || !isStream) {
                hideStatus();
                let problem = "That could not be sent. Your message is still in the box.";
                try {
                    const data = await response.json();
                    if (data && data.error) problem = data.error;
                } catch (_) {
                    // An error page: signed out elsewhere, or a page open too long.
                    if (response.status === 403 || response.status === 404) {
                        problem = "This page is out of date. Copy your message first: it has not been sent. Then start a new chat and send it there.";
                    }
                }
                if (putBack()) mine.div.remove();
                addNotice(problem);
                return;
            }

            streaming = true;
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");
            let all = "";
            let reply = null;
            let replyText = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                all += decoder.decode(value, { stream: true });
                replyText = all.replace(STATUS_OR_OPEN, "");

                // The latest status shows until words follow it.
                const frames = [...all.matchAll(STATUS)];
                const last = frames[frames.length - 1];
                const since = last ? all.slice(last.index + last[0].length) : all;
                if (last && !since.trim()) showStatus(last[1]);
                else hideStatus();

                if (replyText) {
                    // Made on the first word, so no empty turn flashes up.
                    if (!reply) reply = addTurn("assistant");
                    setReply(reply.body, replyText);
                }
                scrollToEnd();
            }

            hideStatus();
            if (reply) addCopy(reply.div, replyText);
            refresh();
        } catch (_) {
            hideStatus();
            if (streaming) {
                addNotice("The connection dropped, but your message was saved. Reload the page to see what was kept before you send it again.");
            } else {
                putBack();
                addNotice("Network error: your message may not have been sent. Copy it, then reload the page to check before you send it again.");
            }
        } finally {
            sending = false;
            sendBtn.removeAttribute("aria-disabled");
        }
    }

    // Enter sends; Shift+Enter is a new line. A held Enter sends once.
    input.addEventListener("input", autoGrow);
    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            if (!event.repeat) send();
        }
    });
    sendBtn.addEventListener("click", send);

    // Rename, from a chat's menu. Delegated: the list is replaced after a reply.
    document.addEventListener("click", async (event) => {
        const item = event.target.closest("[data-rename-url]");
        if (!item) return;
        const title = (window.prompt("A new name for this chat:") || "").trim();
        if (!title) return;
        const response = await fetch(item.dataset.renameUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken() },
            body: JSON.stringify({ title }),
        });
        if (response.ok) refresh();
        else addNotice("That chat could not be renamed. Try again.");
    });
})();
