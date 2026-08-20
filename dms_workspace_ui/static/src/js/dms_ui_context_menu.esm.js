/** @odoo-module **/

import {useEffect, useExternalListener, useRef} from "@odoo/owl";
import {ColorList} from "@web/core/colorlist/colorlist";
import {registry} from "@web/core/registry";
import {
    isEnterKey,
    isSpaceKey,
    selectedFileIds,
    stopEvent,
} from "@dms_workspace_ui/js/dms_ui_core.esm";
import {DmsUiActions} from "@dms_workspace_ui/js/dms_ui_actions.esm";
import {
    DmsFocusTransaction,
    DmsWorkspaceCommand,
} from "@dms_workspace_ui/js/dms_ui_workspace_ui.esm";

const MENU_BUTTON_SELECTOR = "button.dropdown-item:not(:disabled)";
const COLOR_ITEM_SELECTOR =
    ".dms_ui_color_submenu button, " +
    ".dms_ui_color_submenu [role='button'], " +
    ".dms_ui_color_submenu .o_colorlist_item";
const COLOR_TRIGGER_SELECTOR = ".dms_ui_color_submenu_trigger";

export class DmsContextMenu extends DmsUiActions {
    static template = "dms_workspace_ui.ContextMenu";
    static components = {ColorList};

    setup() {
        super.setup();
        this.menuRef = useRef("menu");
        useExternalListener(
            document,
            "click",
            (event) => {
                if (!this.menu || event.target.closest?.(".dms_ui_context_menu")) {
                    return;
                }
                stopEvent(event);
                this.workspace.closeContextMenu({restoreFocus: false});
            },
            {capture: true}
        );
        useExternalListener(window, "resize", () => this.closeMenu());
        useExternalListener(
            window,
            "keydown",
            (event) => {
                if (this.menu && event.target.closest?.(".dms_ui_context_menu")) {
                    this.onMenuKeydown(event);
                }
            },
            {capture: true}
        );
        useEffect(
            () => {
                if (!this.menu) {
                    return;
                }
                this.menuTransaction = DmsFocusTransaction.forTarget(this, this.target);
                requestAnimationFrame(() => {
                    this.menuElement = this.menuRef.el;
                    this.adjustMenuPosition();
                    this.prepareColorItems();
                    this.hoveredMenuItem = false;
                    this.hoveredColorItem = false;
                    this.menuElement?.focus();
                });
            },
            () => [this.menu?.x, this.menu?.y]
        );
    }

    get menu() {
        return this.workspaceState.contextMenu;
    }

    get target() {
        return this.menu?.target;
    }

    get clipboard() {
        return this.workspaceState.clipboard;
    }

    get isMultiSelect() {
        return this.target?.items?.length > 1;
    }

    get menuStyle() {
        return `left:${this.menu.x}px;top:${this.menu.y}px;`;
    }

    adjustMenuPosition() {
        const menu = this.menuElement;
        if (!menu) {
            return;
        }
        const padding = 8;
        const rect = menu.getBoundingClientRect();
        const top = Math.max(
            padding,
            Math.min(rect.top, window.innerHeight - rect.height - padding)
        );
        const left = Math.max(
            padding,
            Math.min(rect.left, window.innerWidth - rect.width - padding)
        );
        menu.style.top = `${top}px`;
        menu.style.left = `${left}px`;
    }

    get colorIds() {
        return ColorList.COLORS.map((_label, color) => color);
    }

    get selectedColor() {
        const ids = new Set(selectedFileIds(this.target));
        const colors = this.workspaceState.selectedFiles
            .filter((file) => ids.has(file.id))
            .map((file) => file.color);
        if (!colors.length && this.target?.type === "file") {
            return this.target.color;
        }
        return colors.length && colors.every((color) => color === colors[0])
            ? colors[0]
            : undefined;
    }

    get colorSubmenuClass() {
        const x = this.workspaceState?.contextMenu?.x || 0;
        return {
            dms_ui_color_submenu: true,
            dms_ui_color_submenu_left: x > window.innerWidth - 360,
            "dropdown-menu": true,
            "p-2": true,
            show: true,
        };
    }

    closeMenu({restore = true} = {}) {
        const transaction = this.menuTransaction;
        this.workspace.closeContextMenu({restoreFocus: false});
        if (restore) {
            transaction?.restoreSoon();
        }
    }

    async runMenuAction(callback, {refresh = false} = {}) {
        const target = this.target;
        this.workspace.closeContextMenu({restoreFocus: false});
        const command = new DmsWorkspaceCommand(this, {
            transaction:
                this.menuTransaction || DmsFocusTransaction.forTarget(this, target),
        });
        return command.run(callback, {
            refresh,
            restore: "soon",
        });
    }

    menuButtons() {
        return this.menuElement
            ? [...this.menuElement.querySelectorAll(MENU_BUTTON_SELECTOR)]
            : [];
    }

    menuKeyboardAnchor() {
        return (
            document.activeElement?.closest?.("button.dropdown-item") ||
            this.hoveredMenuItem
        );
    }

    onMenuKeydown(event) {
        if (this.onColorMenuKeydown(event)) {
            return;
        }
        const focusable = this.menuButtons();
        const anchorItem = this.menuKeyboardAnchor();
        const currentIndex = focusable.indexOf(anchorItem);
        if (event.key === "Escape") {
            stopEvent(event);
            this.closeMenu();
            return;
        }
        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
            stopEvent(event);
            const delta = event.key === "ArrowDown" ? 1 : -1;
            const nextIndex =
                currentIndex < 0
                    ? 0
                    : (currentIndex + delta + focusable.length) % focusable.length;
            focusable[nextIndex]?.focus();
            this.hoveredMenuItem = false;
            return;
        }
        if (isEnterKey(event)) {
            stopEvent(event);
            const item = anchorItem || focusable[0];
            item?.click();
            return;
        }
        if (event.key === "Home" || event.key === "End") {
            stopEvent(event);
            (event.key === "Home"
                ? focusable[0]
                : focusable[focusable.length - 1]
            )?.focus();
            this.hoveredMenuItem = false;
            return;
        }
        if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
            stopEvent(event);
        }
    }

    onMenuMousemove(event) {
        const colorItem = event.target.closest?.(COLOR_ITEM_SELECTOR);
        const item = event.target.closest?.(MENU_BUTTON_SELECTOR);
        if (!colorItem && !item) {
            return;
        }
        for (const current of this.colorItems()) {
            current.classList.remove("dms_ui_keyboard_color_focus");
        }
        this.hoveredColorItem = colorItem || false;
        this.hoveredMenuItem = item || false;
        if (this.menuElement?.contains(document.activeElement)) {
            this.menuElement.focus();
        }
    }

    colorItems() {
        if (!this.menuElement) {
            return [];
        }
        return [
            ...new Set(
                [...this.menuElement.querySelectorAll(COLOR_ITEM_SELECTOR)].filter(
                    (item) => item.offsetParent
                )
            ),
        ];
    }

    prepareColorItems() {
        for (const item of this.colorItems()) {
            item.tabIndex = 0;
        }
    }

    focusColorItem(index) {
        const items = this.colorItems();
        const item = items[Math.max(0, Math.min(items.length - 1, index))];
        if (item) {
            item.tabIndex = 0;
            item.classList.add("dms_ui_keyboard_color_focus");
        }
        for (const other of items) {
            if (other !== item) {
                other.classList.remove("dms_ui_keyboard_color_focus");
            }
        }
        item?.focus();
        this.hoveredColorItem = false;
    }

    focusColorTrigger() {
        for (const item of this.colorItems()) {
            item.classList.remove("dms_ui_keyboard_color_focus");
        }
        this.menuElement?.querySelector(COLOR_TRIGGER_SELECTOR)?.focus();
    }

    onColorMenuKeydown(event) {
        const activeColorItem = document.activeElement?.closest?.(COLOR_ITEM_SELECTOR);
        const colorTrigger =
            document.activeElement?.closest?.(COLOR_TRIGGER_SELECTOR) ||
            this.hoveredMenuItem?.closest?.(COLOR_TRIGGER_SELECTOR);
        if (colorTrigger && event.key === "ArrowRight") {
            stopEvent(event);
            this.focusColorItem(0);
            return true;
        }
        if (!activeColorItem && !this.hoveredColorItem) {
            return false;
        }
        const items = this.colorItems();
        const index = items.indexOf(activeColorItem || this.hoveredColorItem);
        const columns = 4;
        if (event.key === "ArrowLeft" && index % columns === 0) {
            stopEvent(event);
            this.focusColorTrigger();
            return true;
        }
        const movements = {
            ArrowDown: columns,
            ArrowLeft: -1,
            ArrowRight: 1,
            ArrowUp: -columns,
        };
        if (event.key in movements) {
            stopEvent(event);
            this.focusColorItem(index + movements[event.key]);
            return true;
        }
        if (event.key === "Home" || event.key === "End") {
            stopEvent(event);
            this.focusColorItem(event.key === "Home" ? 0 : items.length - 1);
            return true;
        }
        if (isEnterKey(event) || isSpaceKey(event)) {
            stopEvent(event);
            (activeColorItem || this.hoveredColorItem)?.click();
            return true;
        }
        return false;
    }

    setColor(color) {
        const ids = selectedFileIds(this.target);
        return this.runMenuAction(() => this.orm.write("dms.file", ids, {color}), {
            refresh: {tree: false},
        });
    }
}

registry.category("main_components").add("DmsContextMenu", {
    Component: DmsContextMenu,
});
