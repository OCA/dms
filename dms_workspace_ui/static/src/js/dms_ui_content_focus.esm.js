/** @odoo-module **/

export function setFocusedContentState(state, content = false) {
    state.focusedContent = content || false;
    if (!content || content.type === "empty" || content.type === "parent-directory") {
        state.selectedFile = false;
        state.selectedContentDirectory = false;
        return state.focusedContent;
    }
    if (content.type === "file") {
        state.selectedFile = content;
        state.selectedContentDirectory = false;
        return state.focusedContent;
    }
    if (content.type === "directory") {
        state.selectedFile = false;
        state.selectedContentDirectory = content;
    }
    return state.focusedContent;
}
