/** @odoo-module **/

import {setFocusedContentState} from "@dms_workspace_ui/js/dms_ui_content_focus.esm";

export class DmsUiFocusModel {
    constructor(state) {
        this.state = state;
    }

    tokenKey(token) {
        return token ? `${token.type}:${token.id || ""}:${token.localId || ""}` : "";
    }

    sameToken(left, right) {
        return this.tokenKey(left) === this.tokenKey(right);
    }

    focusToken(focus) {
        return focus?.token || focus?.focusToken || focus || false;
    }

    focusSnapshot(focus, options = {}) {
        const token = this.focusToken(focus);
        if (!token) {
            return false;
        }
        const order = (options.order || focus?.order || [token])
            .map((candidate) => this.focusToken(candidate))
            .filter(Boolean);
        const index =
            Number.isInteger(options.index) && options.index >= 0
                ? options.index
                : Math.max(
                      0,
                      order.findIndex((candidate) => this.sameToken(candidate, token))
                  );
        return {
            token,
            scope: options.scope || focus?.scope || token.type,
            context: options.context || focus?.context || false,
            order: order.length ? order : [token],
            index,
            fallback: this.focusToken(options.fallback || focus?.fallback) || false,
        };
    }

    focusContent(content) {
        return setFocusedContentState(this.state, content || {type: "empty"});
    }

    selectContentDirectory(directory) {
        return setFocusedContentState(this.state, directory || {type: "empty"});
    }

    selectFile(file) {
        return setFocusedContentState(this.state, file || {type: "empty"});
    }

    clearContentFocus() {
        return setFocusedContentState(this.state, false);
    }

    rememberFocus(focus, options = {}) {
        const snapshot = this.focusSnapshot(focus, options);
        if (snapshot) {
            this.state.focusSnapshot = snapshot;
            this.state.lastWorkspaceFocus = snapshot.token;
        }
        return this.state.lastWorkspaceFocus;
    }

    captureFocus(fallback = false) {
        return (
            this.state.focusSnapshot?.token ||
            this.state.lastWorkspaceFocus ||
            fallback ||
            false
        );
    }

    captureFocusSnapshot(fallback = false) {
        return this.state.focusSnapshot || this.focusSnapshot(fallback) || false;
    }

    restoreCandidates(snapshot = false) {
        const current = this.focusSnapshot(snapshot || this.state.focusSnapshot);
        if (!current) {
            return [];
        }
        const tokens = [];
        const addToken = (token) => {
            if (
                token &&
                !tokens.some((candidate) => this.sameToken(candidate, token))
            ) {
                tokens.push(token);
            }
        };
        addToken(current.token);
        for (let index = current.index - 1; index >= 0; index--) {
            addToken(current.order[index]);
        }
        for (let index = current.index + 1; index < current.order.length; index++) {
            addToken(current.order[index]);
        }
        addToken(current.fallback);
        if (current.scope === "tree") {
            addToken({type: "tree-all"});
        } else {
            addToken({type: "content-root"});
        }
        return tokens;
    }
}
