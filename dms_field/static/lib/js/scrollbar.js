$.fn.renderScrollBar = function() {
    this.each(function() {
        new SimpleBar(this);
    });
};
