/** @odoo-module **/

import {useEffect, useExternalListener, useRef, useState} from "@odoo/owl";
import {_t} from "@web/core/l10n/translation";
import {DmsUiActions} from "@dms_workspace_ui/js/dms_ui_actions.esm";
import {dmsUiInspectorSections} from "@dms_workspace_ui/js/dms_ui_registries.esm";
import {
    directoryFileCountLabel,
    directoryFolderCountLabel,
    directoryFromSearchPanelValue,
    dmsUiDirectorySection,
} from "@dms_workspace_ui/js/dms_ui_directories.esm";
import {
    INSPECTOR_BREADCRUMB_MAX_LINES,
    INSPECTOR_WIDTH_KEY,
    errorMessage,
    focusContextTargetNow,
    focusTokenForContentItem,
    rememberWidth,
    stopEvent,
    storedWidth,
} from "@dms_workspace_ui/js/dms_ui_core.esm";

const INSPECTOR_SECTION_SELECTOR = ".dms_ui_inspector_section";

function inspectorSectionSelector(sectionId) {
    return `${INSPECTOR_SECTION_SELECTOR}[data-section-id="${sectionId}"]`;
}

async function loadInspectorSection(section, file, orm) {
    return {
        id: section.id,
        label: section.label,
        text: (await section.load({file, orm})) || "",
        draft: "",
        canEdit: Boolean(section.save),
    };
}

export class DmsInspector extends DmsUiActions {
    static template = "dms_workspace_ui.Inspector";

    setup() {
        super.setup();
        this.inspectorState = useState({sections: []});
        this.breadcrumbRef = useRef("breadcrumb");
        this.breadcrumbState = useState({hiddenCount: 0});
        this.resizeState = useState({
            width: storedWidth(INSPECTOR_WIDTH_KEY, 260, 220, 520),
        });
        this.sectionFocusRestoreToken = 0;
        this.sectionFocusRestoreTimers = [];
        useExternalListener(
            document,
            "pointerdown",
            (event) => this.onInspectorPointerdown(event),
            {capture: true}
        );
        useExternalListener(
            document,
            "keydown",
            (event) => this.onInspectorKeydown(event),
            {capture: true}
        );
        useEffect(
            () => {
                this.breadcrumbState.hiddenCount = 0;
            },
            () => [this.breadcrumbSignature, this.resizeState.width]
        );
        useEffect(
            () => {
                this.fitBreadcrumb();
            },
            () => [
                this.breadcrumbSignature,
                this.breadcrumbState.hiddenCount,
                this.resizeState.width,
            ]
        );
        useEffect(
            () => {
                this.loadSections(this.file);
            },
            () => [this.file?.id, this.workspaceState.revision]
        );
        useEffect(
            () => {
                this.applyPendingInspectorSectionEdit();
            },
            () => [
                this.workspaceState.pendingInspectorSectionEdit?.token,
                this.file?.id,
                this.inspectorSectionsSignature,
            ]
        );
    }

    get file() {
        const content = this.workspaceState.focusedContent;
        return content?.type === "file" ? content : false;
    }

    get folder() {
        const content = this.workspaceState.focusedContent;
        return content?.type === "directory" ? content : false;
    }

    get previewTarget() {
        return this.file || this.folder || false;
    }

    onFocusIn() {
        const target = this.previewTarget;
        if (!target) {
            return;
        }
        this.workspace.rememberFocus(focusTokenForContentItem(target), {
            scope: "content",
            order: [focusTokenForContentItem(target)],
            index: 0,
            fallback: {type: "content-root"},
        });
    }

    get rawLocationBreadcrumbs() {
        const file = this.file;
        if (file?.directoryId) {
            return this.directoryBreadcrumbs(file.directoryId, {
                fallbackName: file.location,
            });
        }
        const folder = this.folder;
        if (folder) {
            return this.directoryBreadcrumbs(folder.parentId, {includeAll: true});
        }
        return [];
    }

    get locationBreadcrumbs() {
        const crumbs = this.rawLocationBreadcrumbs;
        const hiddenCount = Math.min(
            this.breadcrumbState.hiddenCount,
            Math.max(crumbs.length - 1, 0)
        );
        return hiddenCount ? crumbs.slice(hiddenCount) : crumbs;
    }

    get hasHiddenBreadcrumbs() {
        return this.breadcrumbState.hiddenCount > 0;
    }

    get breadcrumbSignature() {
        return this.rawLocationBreadcrumbs
            .map((crumb) => `${crumb.key}:${crumb.name}`)
            .join("/");
    }

    directoryBreadcrumbs(directoryId, {fallbackName = "", includeAll = false} = {}) {
        const crumbs = includeAll
            ? [
                  {
                      key: "all",
                      id: false,
                      name: _t("All Documents"),
                      clickable: true,
                      virtualRoot: true,
                  },
              ]
            : [];
        if (!directoryId) {
            return crumbs;
        }
        const section = dmsUiDirectorySection(this.env);
        const values = section?.values;
        if (!values?.has(directoryId)) {
            return fallbackName
                ? [
                      ...crumbs,
                      {
                          key: `directory_${directoryId}`,
                          id: directoryId,
                          name: fallbackName,
                          clickable: false,
                      },
                  ]
                : crumbs;
        }
        const directoryCrumbs = [];
        let value = values.get(directoryId);
        while (value) {
            directoryCrumbs.unshift({
                key: `directory_${value.id}`,
                id: value.id,
                name: value.display_name,
                clickable: true,
            });
            value = value.parentId ? values.get(value.parentId) : false;
        }
        return [...crumbs, ...directoryCrumbs];
    }

    fitBreadcrumb() {
        const signature = this.breadcrumbSignature;
        requestAnimationFrame(() => {
            if (signature !== this.breadcrumbSignature) {
                return;
            }
            const breadcrumb = this.breadcrumbRef.el;
            if (!breadcrumb) {
                return;
            }
            const styles = getComputedStyle(breadcrumb);
            const lineHeight = parseFloat(styles.lineHeight) || 15;
            const rowGap = parseFloat(styles.rowGap || styles.gap) || 0;
            const maxHeight =
                lineHeight * INSPECTOR_BREADCRUMB_MAX_LINES +
                rowGap * (INSPECTOR_BREADCRUMB_MAX_LINES - 1) +
                1;
            if (
                breadcrumb.scrollHeight > maxHeight &&
                this.breadcrumbState.hiddenCount <
                    Math.max(this.rawLocationBreadcrumbs.length - 1, 0)
            ) {
                this.breadcrumbState.hiddenCount++;
            }
        });
    }

    fileCountLabel(count) {
        return directoryFileCountLabel(count);
    }

    folderCountLabel(count) {
        return directoryFolderCountLabel(count);
    }

    get inspectorStyle() {
        return `flex-basis: ${this.resizeState.width}px;`;
    }

    get inspectorSectionsSignature() {
        return this.inspectorState.sections
            .map((section) => `${section.id}:${section.canEdit ? 1 : 0}`)
            .join(",");
    }

    inspectorSectionDefinition(section) {
        return dmsUiInspectorSections
            .getAll()
            .find((definition) => definition.id === section.id);
    }

    inspectorSection(sectionId) {
        return this.inspectorState.sections.find((section) => section.id === sectionId);
    }

    isEditingSection(section) {
        return this.inspectorState.editingSectionId === section.id;
    }

    isSavingSection(section) {
        return this.inspectorState.savingSectionId === section.id;
    }

    focusSectionEditor(section) {
        const focusEditor = () => {
            const editor = document.querySelector(
                `${inspectorSectionSelector(section.id)} textarea`
            );
            if (!editor) {
                return false;
            }
            editor.focus();
            editor.setSelectionRange?.(editor.value.length, editor.value.length);
            return true;
        };
        window.requestAnimationFrame(() => {
            if (!focusEditor()) {
                window.setTimeout(focusEditor, 0);
            }
        });
    }

    startSectionEdit(section) {
        this.clearSectionFocusRestore();
        section.draft = section.text || "";
        this.inspectorState.editingSectionId = section.id;
        this.focusSectionEditor(section);
    }

    editSection(section, event) {
        event.preventDefault();
        event.stopPropagation();
        this.startSectionEdit(section);
    }

    updateSectionDraft(section, event) {
        section.draft = event.target.value;
    }

    clearSectionFocusRestore() {
        this.sectionFocusRestoreToken++;
        for (const timer of this.sectionFocusRestoreTimers) {
            window.clearTimeout(timer);
        }
        this.sectionFocusRestoreTimers = [];
    }

    focusEditedFile(file = this.file) {
        if (!file?.id) {
            return;
        }
        this.clearSectionFocusRestore();
        const restoreToken = this.sectionFocusRestoreToken;
        const target = {type: "file", id: file.id, localId: file.localId};
        const restore = () => {
            if (restoreToken !== this.sectionFocusRestoreToken) {
                return;
            }
            focusContextTargetNow(target);
        };
        window.requestAnimationFrame(restore);
        for (const delay of [40, 120, 300, 600]) {
            this.sectionFocusRestoreTimers.push(window.setTimeout(restore, delay));
        }
    }

    cancelSectionEdit(section, event, {restoreFocus = true} = {}) {
        event?.preventDefault?.();
        event?.stopPropagation?.();
        const file = this.file;
        section.draft = section.text || "";
        if (this.isEditingSection(section)) {
            this.inspectorState.editingSectionId = false;
        }
        if (restoreFocus) {
            this.focusEditedFile(file);
        }
    }

    async saveSectionEdit(section, event) {
        event?.preventDefault?.();
        event?.stopPropagation?.();
        const definition = this.inspectorSectionDefinition(section);
        if (!definition?.save || !this.file || this.isSavingSection(section)) {
            return;
        }
        const file = this.file;
        const value = section.draft || "";
        this.inspectorState.savingSectionId = section.id;
        try {
            const savedValue = await definition.save({
                file,
                orm: this.orm,
                value,
            });
            const nextText = savedValue === undefined ? value : savedValue || "";
            section.text = nextText;
            section.draft = nextText;
            this.inspectorState.editingSectionId = false;
            if (!nextText) {
                this.inspectorState.sections = this.inspectorState.sections.filter(
                    (candidate) => candidate.id !== section.id
                );
            }
            this.focusEditedFile(file);
        } catch (error) {
            this.notification.add(errorMessage(error), {type: "danger"});
        } finally {
            if (this.isSavingSection(section)) {
                this.inspectorState.savingSectionId = false;
            }
        }
    }

    onInspectorKeydown(event) {
        const editingSectionId = this.inspectorState.editingSectionId;
        if (!editingSectionId) {
            return;
        }
        const sectionEl = event.target.closest?.(INSPECTOR_SECTION_SELECTOR);
        if (sectionEl?.dataset.sectionId !== String(editingSectionId)) {
            return;
        }
        const section = this.inspectorSection(editingSectionId);
        if (!section || this.isSavingSection(section)) {
            return;
        }
        if (event.key === "Escape") {
            stopEvent(event);
            this.cancelSectionEdit(section);
            return;
        }
        if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            stopEvent(event);
            this.saveSectionEdit(section, event);
        }
    }

    onInspectorPointerdown(event) {
        const editingSectionId = this.inspectorState.editingSectionId;
        if (!editingSectionId) {
            return;
        }
        const sectionEl = event.target.closest?.(INSPECTOR_SECTION_SELECTOR);
        if (sectionEl?.dataset.sectionId === String(editingSectionId)) {
            return;
        }
        const section = this.inspectorSection(editingSectionId);
        if (section && !this.isSavingSection(section)) {
            this.cancelSectionEdit(section, undefined, {restoreFocus: false});
        }
    }

    applyPendingInspectorSectionEdit() {
        const request = this.workspaceState.pendingInspectorSectionEdit;
        if (!request || !this.file) {
            return;
        }
        const section = this.inspectorSection(request.sectionId);
        if (section && !section.canEdit) {
            return;
        }
        if (!section || !this.workspace.consumeInspectorSectionEdit(request)) {
            return;
        }
        this.startSectionEdit(section);
    }

    startResize(event) {
        if (event.button !== 0) {
            return;
        }
        const initialX = event.pageX;
        const initialWidth = this.resizeState.width;
        const resizeStoppingEvents = ["keydown", "pointerdown", "pointerup"];
        document.body.classList.add("dms_ui_resizing_inspector");
        const resizePanel = (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            const maxWidth = Math.max(0.5 * window.innerWidth, initialWidth);
            const delta = ev.pageX - initialX;
            const newWidth = Math.min(maxWidth, Math.max(220, initialWidth - delta));
            this.resizeState.width = newWidth;
        };
        const stopResize = (ev) => {
            if (ev.type === "pointerdown" && ev.button === 0) {
                return;
            }
            ev.preventDefault();
            ev.stopPropagation();
            document.removeEventListener("pointermove", resizePanel, true);
            for (const stoppingEvent of resizeStoppingEvents) {
                document.removeEventListener(stoppingEvent, stopResize, true);
            }
            document.body.classList.remove("dms_ui_resizing_inspector");
            rememberWidth(INSPECTOR_WIDTH_KEY, this.resizeState.width, 220, 520);
            document.activeElement?.blur?.();
        };
        document.addEventListener("pointermove", resizePanel, true);
        for (const stoppingEvent of resizeStoppingEvents) {
            document.addEventListener(stoppingEvent, stopResize, true);
        }
    }

    async openLocationBreadcrumb(crumb, event) {
        event.preventDefault();
        event.stopPropagation();
        if (!crumb.clickable) {
            return;
        }
        const section = dmsUiDirectorySection(this.env);
        if (!section) {
            return;
        }
        this.workspace.requestContentFocus();
        this.workspace.selectContentDirectory(false);
        this.workspace.clearMarkedFiles();
        if (crumb.virtualRoot) {
            this.workspace.selectDirectory(false);
            this.env.searchModel.clearSections([section.id]);
            await this.workspace.refresh({tree: false});
            return;
        }
        const value = section.values.get(crumb.id);
        if (!value) {
            return;
        }
        this.workspace.selectDirectory(directoryFromSearchPanelValue(value));
        if (section.activeValueId !== value.id) {
            await this.env.searchModel.toggleCategoryValue(section.id, value.id);
        }
        await this.workspace.refresh({tree: false});
    }

    async loadSections(file) {
        const definitions = dmsUiInspectorSections.getAll();
        this.inspectorState.sections = [];
        if (!file) {
            return [];
        }
        const sections = (
            await Promise.all(
                definitions.map((section) =>
                    loadInspectorSection(section, file, this.orm)
                )
            )
        ).filter((section) => section.text || section.canEdit);
        if (this.file?.id === file.id) {
            this.inspectorState.sections = sections;
        }
    }
}
