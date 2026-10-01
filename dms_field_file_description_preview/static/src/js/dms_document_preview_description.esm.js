/** @odoo-module **/

import {registry} from "@web/core/registry";

const DESCRIPTION_BLOCK_CLASS = "o_dms_document_preview_description";
const DESCRIPTION_TEXT_CLASS = "o_dms_document_preview_description_text";

function parseFileIdFromPreview(previewEl) {
    const contentLink = previewEl.querySelector(
        'a[href*="/web/content"][href*="model=dms.file"], a[href*="/web/content?id="]'
    );
    const href = contentLink?.getAttribute("href") || "";
    if (href) {
        try {
            const url = new URL(href, window.location.origin);
            const id = url.searchParams.get("id");
            if (id && /^\d+$/.test(id)) {
                return Number.parseInt(id, 10);
            }
        } catch {
            const match = href.match(/[?&]id=(\d+)/);
            if (match) {
                return Number.parseInt(match[1], 10);
            }
        }
    }

    const image = previewEl.querySelector('img[src*="/web/image/dms.file/"]');
    const src = image?.getAttribute("src") || "";
    const imageMatch = src.match(/\/web\/image\/dms\.file\/(\d+)\//);
    if (imageMatch) {
        return Number.parseInt(imageMatch[1], 10);
    }

    return null;
}

function descriptionBlock(previewEl) {
    return previewEl.querySelector(`:scope > .${DESCRIPTION_BLOCK_CLASS}`);
}

function removeDescription(previewEl) {
    const existing = descriptionBlock(previewEl);
    if (existing) {
        existing.remove();
    }
}

function renderDescription(previewEl, description) {
    const normalized = (description || "").trim();
    if (!normalized) {
        removeDescription(previewEl);
        return;
    }

    let block = descriptionBlock(previewEl);
    if (!block) {
        block = document.createElement("div");
        block.className = DESCRIPTION_BLOCK_CLASS;

        const title = document.createElement("div");
        title.className = "o_dms_document_preview_description_title";
        title.textContent = "Description";

        const text = document.createElement("div");
        text.className = DESCRIPTION_TEXT_CLASS;

        block.append(title, text);

        const previewDirectory = previewEl.querySelector(
            ":scope > .o_preview_directory"
        );
        if (previewDirectory) {
            previewDirectory.insertAdjacentElement("afterend", block);
        } else {
            previewEl.append(block);
        }
    }

    const textEl = block.querySelector(`.${DESCRIPTION_TEXT_CLASS}`);
    if (textEl) {
        textEl.textContent = normalized;
    }
}

const dmsFileDescriptionPreviewService = {
    dependencies: ["orm"],
    start(env, {orm}) {
        const pending = new Map();
        const minPassiveRefreshMs = 10000;
        let scheduled = null;

        async function readDescription(fileId) {
            // Do not cache completed descriptions here. DMS preview panes can be reused
            // after editing a file in a dialog, and stale cached descriptions are very
            // confusing. We only deduplicate concurrent reads for the same file.
            if (pending.has(fileId)) {
                return pending.get(fileId);
            }

            const promise = orm
                .read("dms.file", [fileId], ["description"])
                .then((records) => {
                    pending.delete(fileId);
                    return records?.[0]?.description || "";
                })
                .catch((error) => {
                    pending.delete(fileId);
                    // Keep this non-fatal. The preview pane should still work even if
                    // permissions or transient DMS state prevent reading the description.
                    console.warn(
                        "Unable to load DMS file description for preview panel",
                        fileId,
                        error
                    );
                    return "";
                });

            pending.set(fileId, promise);
            return promise;
        }

        async function updatePreview(previewEl, {force = false} = {}) {
            const fileId = parseFileIdFromPreview(previewEl);
            if (!fileId) {
                removeDescription(previewEl);
                delete previewEl.dataset.dmsFileDescriptionId;
                delete previewEl.dataset.dmsFileDescriptionCheckedAt;
                return;
            }

            const now = Date.now();
            const idKey = String(fileId);
            const previousId = previewEl.dataset.dmsFileDescriptionId;
            const lastChecked = Number.parseInt(
                previewEl.dataset.dmsFileDescriptionCheckedAt || "0",
                10
            );

            // MutationObserver fires again when this service inserts/updates the block.
            // Avoid repeatedly reading the same preview just because our own DOM changed.
            if (
                !force &&
                previousId === idKey &&
                descriptionBlock(previewEl) &&
                now - lastChecked < minPassiveRefreshMs
            ) {
                return;
            }

            previewEl.dataset.dmsFileDescriptionId = idKey;
            previewEl.dataset.dmsFileDescriptionCheckedAt = String(now);

            const description = await readDescription(fileId);
            // The preview may have changed while the RPC was pending.
            if (parseFileIdFromPreview(previewEl) === fileId) {
                renderDescription(previewEl, description);
            }
        }

        function updateAllPreviews(options = {}) {
            for (const previewEl of document.querySelectorAll(
                ".dms_document_preview"
            )) {
                updatePreview(previewEl, options);
            }
        }

        function schedulePassiveUpdate() {
            if (scheduled) {
                window.clearTimeout(scheduled);
            }
            scheduled = window.setTimeout(() => {
                scheduled = null;
                updateAllPreviews({force: false});
            }, 80);
        }

        function scheduleForcedRefreshes() {
            // A form save may still be in-flight when the click happens. Refresh a few
            // times after likely save/close events so the preview catches the new
            // description without requiring a full browser refresh.
            for (const delay of [250, 900, 1800]) {
                window.setTimeout(() => updateAllPreviews({force: true}), delay);
            }
        }

        const observer = new MutationObserver(schedulePassiveUpdate);
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ["src", "href", "class"],
        });

        document.body.addEventListener(
            "click",
            (event) => {
                schedulePassiveUpdate();
                // Refresh after likely file-detail saves or dialog confirm actions.
                if (
                    event.target.closest(
                        ".o_form_button_save, .modal-footer .btn-primary, .o_dialog .btn-primary"
                    )
                ) {
                    scheduleForcedRefreshes();
                }
            },
            true
        );
        window.addEventListener("focus", scheduleForcedRefreshes);

        schedulePassiveUpdate();

        return {
            update() {
                updateAllPreviews({force: true});
            },
        };
    },
};

registry
    .category("services")
    .add(
        "dms_field_file_description_preview.preview_panel",
        dmsFileDescriptionPreviewService
    );
