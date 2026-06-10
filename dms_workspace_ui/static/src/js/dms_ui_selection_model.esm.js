/** @odoo-module **/

export class DmsUiSelectionModel {
    constructor(state, focusModel) {
        this.state = state;
        this.focusModel = focusModel;
    }

    selectFiles(files, focusedFile = false) {
        this.state.selectedFiles = files;
        if (focusedFile) {
            this.focusModel.focusContent(focusedFile);
        } else if (files.length === 1) {
            this.focusModel.focusContent(files[0]);
        } else if (!files.length) {
            this.focusModel.focusContent({type: "empty"});
        }
    }

    setSelectedFiles(files) {
        this.state.selectedFiles = files;
    }

    setVisibleFiles(files) {
        this.state.visibleFiles = files;
    }

    clearMarkedFiles() {
        this.state.markedFileIds = [];
    }

    clearContentSelection() {
        this.state.selectedFiles = [];
        this.state.markedFileIds = [];
        this.state.clearSelectionToken++;
    }

    retainMarkedFiles(ids) {
        const retainedIds = new Set(ids);
        this.state.markedFileIds = this.state.markedFileIds.filter((id) =>
            retainedIds.has(id)
        );
    }

    setFileMarked(id, marked) {
        const ids = new Set(this.state.markedFileIds);
        if (marked) {
            ids.add(id);
        } else {
            ids.delete(id);
        }
        this.state.markedFileIds = [...ids];
    }
}
