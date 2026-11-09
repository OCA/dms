/* Copyright 2025 Carlos Roca - Tecnativa
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {Component, onWillStart, useRef, useState} from "@odoo/owl";
import {KeepLast} from "@web/core/utils/concurrency";
import {SearchMedia} from "@web_editor/components/media_dialog/search_media";
import {_t} from "@web/core/l10n/translation";
import {useDebounced} from "@web/core/utils/timing";
import {useService} from "@web/core/utils/hooks";

export class DMSFile extends Component {}
DMSFile.template = "web_editor_media_dialog_dms.DMSFile";

export class DMSSelector extends Component {
    setup() {
        this.orm = useService("orm");
        this.keepLast = new KeepLast();
        this.loadMoreButtonRef = useRef("load-more-button");
        this.state = useState({
            dmsFiles: [],
            canLoadMoreFiles: true,
            isFetchingFiles: false,
            needle: "",
        });
        this.allowOpenPublic = false;
        this.NUMBER_OF_FILES_TO_DISPLAY = 30;
        this.searchPlaceholder = _t("Search a dms file");
        onWillStart(async () => {
            this.state.dmsFiles = await this.fetchFiles(
                this.NUMBER_OF_FILES_TO_DISPLAY,
                0
            );
        });
        this.debouncedScroll = useDebounced(this.scrollToLoadMoreButton, 500);
    }

    get canLoadMore() {
        return this.state.canLoadMoreFiles;
    }

    get hasContent() {
        return this.state.dmsFiles.length;
    }

    get isFetching() {
        return this.state.isFetchingFiles;
    }

    get selectedFileIds() {
        return this.props.selectedMedia[this.props.id]
            .filter((media) => media.mediaType === "dms")
            .map(({id}) => id);
    }

    async fetchFiles(limit, offset) {
        this.state.isFetchingFiles = true;
        let files = [];
        try {
            files = await this.orm.searchRead(
                "dms.file",
                [["name", "ilike", this.state.needle]],
                ["name", "mimetype"],
                {
                    order: "id desc",
                    limit,
                    offset,
                }
            );
        } catch (e) {
            if (e.exceptionName !== "odoo.exceptions.AccessError") {
                throw e;
            }
        }
        this.state.canLoadMoreFiles = files.length >= this.NUMBER_OF_FILES_TO_DISPLAY;
        this.state.isFetchingFiles = false;
        if (this.selectInitialMedia()) {
            for (const file of files) {
                if (
                    `/mail/view?model=dms.file&res_id=${file.id}` ===
                    this.props.media.getAttribute("href").replace(/[?].*/, "")
                ) {
                    this.selectFile(file);
                }
            }
        }
        for (const file of files) {
            file.allowOpenPublic = this.allowOpenPublic;
        }
        return files;
    }

    async handleLoadMore() {
        await this.loadMore();
        this.debouncedScroll();
    }

    async loadMore() {
        return this.keepLast
            .add(
                this.fetchFiles(
                    this.NUMBER_OF_FILES_TO_DISPLAY,
                    this.state.dmsFiles.length
                )
            )
            .then((newFiles) => {
                // This is never reached if another search or loadMore occurred.
                this.state.dmsFiles.push(...newFiles);
            });
    }

    async handleSearch(needle) {
        await this.search(needle);
        this.debouncedScroll();
    }

    search(needle) {
        this.state.dmsFiles = [];
        this.state.needle = needle;
        return this.keepLast
            .add(this.fetchFiles(this.NUMBER_OF_FILES_TO_DISPLAY, 0))
            .then((files) => {
                this.state.dmsFiles = files;
            });
    }

    scrollToLoadMoreButton() {
        if (
            this.state.needle ||
            this.state.dmsFiles.length > this.NUMBER_OF_FILES_TO_DISPLAY
        ) {
            this.loadMoreButtonRef.el.scrollIntoView({
                block: "end",
                inline: "nearest",
                behavior: "smooth",
            });
        }
    }

    async onClickFile(file) {
        this.props.selectMedia({...file, mediaType: "dms"});
        await this.props.save();
    }

    static async createElements(selectedMedia, {orm}) {
        return Promise.all(
            selectedMedia.map(async (file) => {
                const linkEl = document.createElement("a");
                let href = `/mail/view?model=dms.file&res_id=${encodeURIComponent(
                    file.id
                )}`;
                // Download svg images because are considered images but are not
                // visualized correctly on new tab. Other files than pdf or image are
                // downloaded by default
                if (file.mimetype === "image/svg+xml") {
                    href += "&download=true";
                }
                if (file.allowOpenPublic) {
                    const accessToken = await orm.call("dms.file", "get_access_token", [
                        file.id,
                    ]);
                    href += `&access_token=${encodeURIComponent(accessToken)}`;
                }
                linkEl.href = href;
                linkEl.title = file.name;
                linkEl.dataset.mimetype = file.mimetype;
                return linkEl;
            })
        );
    }

    selectFile(file) {
        this.props.selectMedia({...file, mediaType: "dms"});
    }

    selectInitialMedia() {
        return (
            this.props.media &&
            this.constructor.tagNames.includes(this.props.media.tagName) &&
            !this.selectedFileIds.length
        );
    }

    async handleChangeAllowOpenPublic() {
        await this.changeAllowOpenPublic();
        this.debouncedScroll();
    }

    changeAllowOpenPublic() {
        this.allowOpenPublic = !this.allowOpenPublic;
        return this.keepLast
            .add(this.fetchFiles(this.state.dmsFiles.length, 0))
            .then((files) => {
                this.state.dmsFiles = files;
            });
    }
}

DMSSelector.template = "web_editor_media_dialog_dms.DMSSelector";
DMSSelector.mediaSpecificClasses = ["o_image", "o_dms_file"];
DMSSelector.mediaSpecificStyles = [];
DMSSelector.mediaExtraClasses = [];
DMSSelector.tagNames = ["A"];
DMSSelector.components = {
    DMSFile,
    SearchMedia,
};
