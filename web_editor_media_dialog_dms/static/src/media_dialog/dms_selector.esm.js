/* Copyright 2025 Carlos Roca - Tecnativa
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {Component, onWillStart, proxy, signal, t, useProps} from "@odoo/owl";
import {KeepLast} from "@web/core/utils/concurrency";
import {SearchMedia} from "@html_editor/main/media/media_dialog/search_media";
import {_t} from "@web/core/l10n/translation";
import {renderToElement} from "@web/core/utils/render";
import {useDebounced} from "@web/core/utils/timing";
import {useService} from "@web/core/utils/hooks";

export class DMSFile extends Component {
    static template = "web_editor_media_dialog_dms.DMSFile";

    props = useProps({
        id: t.number(),
        name: t.string(),
        mimetype: t.or([t.string(), t.literal(false)]).optional(),
        selected: t.boolean().optional(),
        selectFile: t.function(),
    });
}

export class DMSSelector extends Component {
    static template = "web_editor_media_dialog_dms.DMSSelector";
    static mediaSpecificClasses = ["o_file_box", "o_dms_file"];
    static mediaSpecificStyles = [];
    static mediaExtraClasses = [];
    static tagNames = ["SPAN"];
    static components = {
        DMSFile,
        SearchMedia,
    };

    props = useProps({
        id: t.string(),
        media: t.any().optional(),
        save: t.function(),
        selectedMedia: t.object(),
        selectMedia: t.function(),
    });

    loadMoreButtonRef = signal.ref();

    setup() {
        this.orm = useService("orm");
        this.keepLast = new KeepLast();
        this.state = proxy({
            dmsFiles: [],
            canLoadMoreFiles: true,
            isFetchingFiles: false,
            needle: "",
            allowOpenPublic: false,
        });
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
            const initialFileId = Number(this.props.media.dataset.dmsFileId);
            const initialFile = files.find((file) => file.id === initialFileId);
            if (initialFile) {
                this.selectFile(initialFile);
            }
        }
        for (const file of files) {
            file.allowOpenPublic = this.state.allowOpenPublic;
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
        const loadMoreButtonEl = this.loadMoreButtonRef();
        if (
            loadMoreButtonEl &&
            (this.state.needle ||
                this.state.dmsFiles.length > this.NUMBER_OF_FILES_TO_DISPLAY)
        ) {
            loadMoreButtonEl.scrollIntoView({
                block: "end",
                inline: "nearest",
                behavior: "smooth",
            });
        }
    }

    async onClickFile(file) {
        this.selectFile(file);
        await this.props.save();
    }

    /**
     * Utility method used by the MediaDialog component.
     */
    static async createElements(selectedMedia, {orm, document = window.document}) {
        return Promise.all(
            selectedMedia.map(async (file) => {
                let url = `/mail/view?model=dms.file&res_id=${encodeURIComponent(
                    file.id
                )}`;
                // Download svg images because are considered images but are not
                // visualized correctly on new tab. Other files than pdf or image are
                // downloaded by default
                if (file.mimetype === "image/svg+xml") {
                    url += "&download=true";
                }
                if (file.allowOpenPublic) {
                    const accessToken = await orm.call("dms.file", "get_access_token", [
                        file.id,
                    ]);
                    url += `&access_token=${encodeURIComponent(accessToken)}`;
                }
                return this.renderFileElement(file, url, document);
            })
        );
    }

    /**
     * Render the file the same way the core renders the documents
     * (see renderStaticFileBox), so that the editor handles it as a media.
     */
    static renderFileElement(file, url, document) {
        const rootSpan = document.createElement("span");
        rootSpan.classList.add("o_file_box", "o_dms_file", "o-contenteditable-false");
        rootSpan.contentEditable = false;
        rootSpan.dataset.dmsFileId = file.id;
        const parts = file.name.split(".");
        rootSpan.dataset.extension = parts.length > 1 ? parts.pop() : "";
        const bannerElement = renderToElement(
            "web_editor_media_dialog_dms.DMSFileBox",
            {
                fileModel: {
                    filename: file.name,
                    mimetype: file.mimetype,
                    url,
                },
            }
        );
        rootSpan.append(document.importNode(bannerElement, true));
        return rootSpan;
    }

    selectFile(file) {
        this.props.selectMedia({...file, mediaType: "dms"});
    }

    selectInitialMedia() {
        return (
            this.props.media &&
            this.constructor.tagNames.includes(this.props.media.tagName) &&
            this.props.media.classList.contains("o_dms_file") &&
            !this.selectedFileIds.length
        );
    }

    async handleChangeAllowOpenPublic() {
        await this.changeAllowOpenPublic();
        this.debouncedScroll();
    }

    changeAllowOpenPublic() {
        this.state.allowOpenPublic = !this.state.allowOpenPublic;
        return this.keepLast
            .add(
                this.fetchFiles(
                    Math.max(
                        this.state.dmsFiles.length,
                        this.NUMBER_OF_FILES_TO_DISPLAY
                    ),
                    0
                )
            )
            .then((files) => {
                this.state.dmsFiles = files;
            });
    }
}
