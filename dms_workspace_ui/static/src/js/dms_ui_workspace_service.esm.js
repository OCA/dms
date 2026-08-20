/** @odoo-module **/

import {reactive} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {DmsUiFocusModel} from "@dms_workspace_ui/js/dms_ui_focus_model.esm";
import {DmsUiSelectionModel} from "@dms_workspace_ui/js/dms_ui_selection_model.esm";
import {focusContextTargetSoon} from "@dms_workspace_ui/js/dms_ui_core.esm";

const dmsUiWorkspaceService = {
    start() {
        const state = reactive({
            clipboard: false,
            contextMenu: false,
            focusedContent: false,
            focusSnapshot: false,
            lastWorkspaceFocus: false,
            selectedDirectory: false,
            selectedContentDirectory: false,
            selectedFile: false,
            selectedFiles: [],
            markedFileIds: [],
            visibleFiles: [],
            fileTypeahead: {query: "", updatedAt: 0},
            pendingContentFocus: 0,
            pendingInspectorSectionEdit: false,
            clearSelectionToken: 0,
            revision: 0,
        });
        let filePickerTransaction = false;
        let inspectorSectionEditCounter = 0;
        let refresh = async () => undefined;
        const focusModel = new DmsUiFocusModel(state);
        const selectionModel = new DmsUiSelectionModel(state, focusModel);
        return {
            state,
            closeContextMenu({restoreFocus = true} = {}) {
                const target = state.contextMenu?.target;
                state.contextMenu = false;
                if (restoreFocus) {
                    focusContextTargetSoon(target);
                }
            },
            openContextMenu(event, target) {
                event.preventDefault();
                event.stopPropagation();
                state.contextMenu = {
                    x: event.clientX,
                    y: event.clientY,
                    target,
                };
            },
            selectDirectory(directory) {
                if (state.selectedDirectory?.id !== directory?.id) {
                    selectionModel.clearContentSelection();
                    focusModel.clearContentFocus();
                }
                state.selectedDirectory = directory;
            },
            selectContentDirectory(directory) {
                focusModel.selectContentDirectory(directory);
            },
            selectFile(file) {
                focusModel.selectFile(file);
            },
            focusContent(content) {
                focusModel.focusContent(content);
            },
            selectFiles(files, focusedFile = false) {
                selectionModel.selectFiles(files, focusedFile);
            },
            setSelectedFiles(files) {
                selectionModel.setSelectedFiles(files);
            },
            setVisibleFiles(files) {
                selectionModel.setVisibleFiles(files);
            },
            setClipboard(mode, items) {
                state.clipboard = {mode, items};
            },
            clearClipboard() {
                state.clipboard = false;
            },
            clearMarkedFiles() {
                selectionModel.clearMarkedFiles();
            },
            clearContentSelection() {
                selectionModel.clearContentSelection();
            },
            retainMarkedFiles(ids) {
                selectionModel.retainMarkedFiles(ids);
            },
            setFileMarked(id, marked) {
                selectionModel.setFileMarked(id, marked);
            },
            rememberFocus(focus) {
                return focusModel.rememberFocus(focus, arguments[1] || {});
            },
            captureFocus(fallback = false) {
                return focusModel.captureFocus(fallback);
            },
            captureFocusSnapshot(fallback = false) {
                return focusModel.captureFocusSnapshot(fallback);
            },
            restoreCandidates(snapshot = false) {
                return focusModel.restoreCandidates(snapshot);
            },
            setFilePickerTransaction(transaction) {
                filePickerTransaction = transaction || false;
            },
            consumeFilePickerTransaction() {
                const transaction = filePickerTransaction;
                filePickerTransaction = false;
                return transaction;
            },
            requestContentFocus() {
                state.pendingContentFocus++;
            },
            consumePendingContentFocus() {
                const pending = state.pendingContentFocus;
                state.pendingContentFocus = 0;
                return pending;
            },
            requestInspectorSectionEdit(sectionId) {
                state.pendingInspectorSectionEdit = {
                    sectionId,
                    token: ++inspectorSectionEditCounter,
                };
            },
            consumeInspectorSectionEdit(request) {
                if (
                    !request ||
                    state.pendingInspectorSectionEdit?.token !== request.token
                ) {
                    return false;
                }
                state.pendingInspectorSectionEdit = false;
                return true;
            },
            bumpRevision() {
                state.revision++;
            },
            setRefresh(callback) {
                refresh = callback;
            },
            refresh(options) {
                return refresh(options);
            },
        };
    },
};

registry.category("services").add("dms_ui_workspace", dmsUiWorkspaceService);
