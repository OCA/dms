/** @odoo-module **/

export class DmsContentSelectionModel {
    constructor(browser) {
        this.browser = browser;
    }

    get keys() {
        return this.browser.browserState.selectedKeys;
    }

    set keys(keys) {
        this.browser.browserState.selectedKeys = keys;
    }

    isSelectable(item) {
        return item && !this.browser.isParentDirectoryItem(item);
    }

    isSelected(item) {
        return this.isSelectable(item) && this.keys.includes(item.key);
    }

    selectedItems(items = this.browser.items) {
        const selected = new Set(this.keys);
        return items.filter(
            (item) => this.isSelectable(item) && selected.has(item.key)
        );
    }

    clear() {
        this.keys = [];
    }

    retain(items = this.browser.items) {
        const available = new Set(
            items.filter((item) => this.isSelectable(item)).map((item) => item.key)
        );
        this.keys = this.keys.filter((key) => available.has(key));
    }

    toggle(item) {
        if (!this.isSelectable(item)) {
            return this.keys;
        }
        const keys = new Set(this.keys);
        if (keys.has(item.key)) {
            keys.delete(item.key);
        } else {
            keys.add(item.key);
        }
        this.keys = [...keys];
        return this.keys;
    }

    addPair(currentItem, targetItem) {
        const keys = new Set(this.keys);
        if (this.isSelectable(currentItem)) {
            keys.add(currentItem.key);
        }
        if (this.isSelectable(targetItem)) {
            keys.add(targetItem.key);
        }
        this.keys = [...keys];
        return this.keys;
    }
}
