/** @odoo-module **/

import {Component} from "@odoo/owl";
import {useFileViewer} from "@web/core/file_viewer/file_viewer_hook";
import {useService} from "@web/core/utils/hooks";
import {
    TREE_HEADER_SELECTOR,
    WORKSPACE_SELECTOR,
    errorMessage,
    focusWorkspaceTokenNow,
} from "@dms_workspace_ui/js/dms_ui_core.esm";

export class DmsWorkspaceWidget extends Component {
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.store = useService("mail.store");
        this.ui = useService("ui");
        this.workspace = useService("dms_ui_workspace");
        this.fileViewer = useFileViewer();
    }
}

export class DmsFocusTransaction {
    constructor(owner, {snapshot = false, fallback = false} = {}) {
        this.owner = owner;
        this.workspace = owner.workspace || owner.dmsUiWorkspace;
        this.snapshot = snapshot || this.workspace.captureFocusSnapshot(fallback);
        this.restored = false;
        this.waitingForOverlayClose = false;
        this.observer = null;
        this.fallbackTimer = null;
        this.restoreTimers = [];
        this.cancelRestoreListeners = null;
        this.userMovedAfterRestore = false;
    }

    focusBestCandidate() {
        for (const token of this.workspace.restoreCandidates(this.snapshot)) {
            if (focusWorkspaceTokenNow(token)) {
                return true;
            }
        }
        return false;
    }

    hasWorkspaceFocus() {
        const active = document.activeElement;
        return Boolean(
            active?.closest?.(
                [
                    `${WORKSPACE_SELECTOR} .dms_ui_custom_browser`,
                    `${WORKSPACE_SELECTOR} .dms_ui_custom_item`,
                    `${WORKSPACE_SELECTOR} .dms_ui_inspector`,
                    TREE_HEADER_SELECTOR,
                ].join(", ")
            )
        );
    }

    restoreNow() {
        if (this.restored) {
            return false;
        }
        this.restored = true;
        this.cleanup();
        return this.focusBestCandidate();
    }

    restoreSoon() {
        if (this.restored) {
            return false;
        }
        this.restored = true;
        this.cleanup();
        let restoredFocus = false;
        const attempt = () => {
            if (this.userMovedAfterRestore) {
                this.clearRestoreTimers();
                return;
            }
            if (restoredFocus && this.hasWorkspaceFocus()) {
                this.clearRestoreTimers();
                return;
            }
            if (this.focusBestCandidate()) {
                restoredFocus = true;
                this.cancelOnUserMove();
            }
        };
        requestAnimationFrame(attempt);
        for (const delay of [40, 120, 300]) {
            this.restoreTimers.push(window.setTimeout(attempt, delay));
        }
        return true;
    }

    restoreAfterOverlayClose({waitForOpen = false} = {}) {
        if (this.restored || this.waitingForOverlayClose) {
            return;
        }
        this.waitingForOverlayClose = true;
        const restoreWhenClosed = this.makeOverlayCloseRestoreHandler({waitForOpen});
        requestAnimationFrame(restoreWhenClosed);
        this.observer = new MutationObserver(restoreWhenClosed);
        this.observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ["class"],
        });
        this.fallbackTimer = window.setTimeout(() => this.restoreSoon(), 1500);
    }

    makeOverlayCloseRestoreHandler({waitForOpen = false} = {}) {
        const overlaySelector = ".modal.show, .o_dialog, .o-FileViewer";
        let sawOverlay = false;
        return () => {
            const overlay = document.querySelector(overlaySelector);
            sawOverlay = sawOverlay || Boolean(overlay);
            if (!overlay && (sawOverlay || !waitForOpen)) {
                this.restoreSoon();
            }
        };
    }

    dialogRestoreHooks({waitForOpen = false, cancel = false, dismiss = false} = {}) {
        const restore = this.makeRestoreAfterOverlayCloseHook({waitForOpen});
        return {
            props: {
                ...(cancel ? {cancel: restore} : {}),
                ...(dismiss ? {dismiss: restore} : {}),
            },
            options: {
                onClose: restore,
            },
        };
    }

    makeRestoreAfterOverlayCloseHook({waitForOpen = false} = {}) {
        return () => this.restoreAfterOverlayClose({waitForOpen});
    }

    async refresh(options = false) {
        if (options) {
            await this.workspace.refresh(options);
        }
    }

    cleanup() {
        this.observer?.disconnect();
        this.observer = null;
        this.waitingForOverlayClose = false;
        if (this.fallbackTimer) {
            window.clearTimeout(this.fallbackTimer);
            this.fallbackTimer = null;
        }
        this.clearRestoreTimers();
        this.cancelRestoreListeners?.();
        this.cancelRestoreListeners = null;
    }

    clearRestoreTimers() {
        for (const timer of this.restoreTimers) {
            window.clearTimeout(timer);
        }
        this.restoreTimers = [];
    }

    cancelOnUserMove() {
        if (this.cancelRestoreListeners) {
            return;
        }
        const cancel = () => {
            this.userMovedAfterRestore = true;
            this.clearRestoreTimers();
            this.cancelRestoreListeners?.();
            this.cancelRestoreListeners = null;
        };
        window.addEventListener("keydown", cancel, {capture: true, once: true});
        window.addEventListener("pointerdown", cancel, {capture: true, once: true});
        this.cancelRestoreListeners = () => {
            window.removeEventListener("keydown", cancel, {capture: true});
            window.removeEventListener("pointerdown", cancel, {capture: true});
        };
    }

    static forTarget(owner, target, options = {}) {
        return new this(owner, {
            ...options,
            fallback:
                options.fallback !== undefined
                    ? options.fallback
                    : target?.focusToken || target,
        });
    }
}

export class DmsWorkspaceCommand {
    constructor(owner, options = {}) {
        this.owner = owner;
        this.transaction =
            options.transaction || new DmsFocusTransaction(owner, options);
    }

    async run(callback, {refresh = false, restore = "soon"} = {}) {
        try {
            const result = await callback(this.transaction);
            await this.transaction.refresh(refresh);
            if (result instanceof DmsFocusTransaction) {
                return result;
            }
            if (restore === "now") {
                this.transaction.restoreNow();
            } else if (restore !== false && restore !== "manual") {
                this.transaction.restoreSoon();
            }
            return result;
        } catch (error) {
            (this.owner.notification || this.owner.dmsUiNotification).add(
                errorMessage(error),
                {
                    type: "danger",
                }
            );
            this.transaction.restoreSoon();
        }
    }
}

export class DmsWorkspaceDialog extends DmsWorkspaceWidget {
    static show(owner, props = {}, options = {}) {
        const transaction =
            options.transaction || new DmsFocusTransaction(owner, options);
        const dialog = owner.dialog || owner.dmsUiDialog;
        const restoreHooks = transaction.dialogRestoreHooks();
        dialog.add(
            this,
            {
                ...props,
                transaction,
                refresh: options.refresh || false,
            },
            restoreHooks.options
        );
        return transaction;
    }

    payload() {
        return {};
    }

    validate() {
        return true;
    }

    async save() {
        const payload = this.payload();
        if (!this.validate(payload)) {
            return;
        }
        await this.props.confirm(payload);
        await this.props.transaction.refresh(this.props.refresh);
        this.props.close();
    }

    cancel() {
        this.props.close();
    }
}
