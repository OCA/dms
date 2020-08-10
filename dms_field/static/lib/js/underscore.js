_.mixin({
    memoizeDebounce: function(func, wait, options) {
        wait = typeof wait !== "undefined" ? wait : 0;
        options = typeof options !== "undefined" ? options : {};
        var mem = _.memoize(function() {
            return _.debounce(func, wait, options);
        }, options.resolver);
        return function() {
            mem.apply(this, arguments).apply(this, arguments);
        };
    },
});

_.mixin({
    memoizeThrottle: function(func, wait, options) {
        wait = typeof wait !== "undefined" ? wait : 0;
        options = typeof options !== "undefined" ? options : {};
        var mem = _.memoize(function() {
            return _.throttle(func, wait, options);
        }, options.resolver);
        return function() {
            mem.apply(this, arguments).apply(this, arguments);
        };
    },
});
