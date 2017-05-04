var original_Viewer = Viewer;

Viewer = function(plugin, parameters) {
    var matches = (/&title=([^&]+)&/).exec(window.location.hash);
    
    if(matches && matches.length > 1) {
        parameters.title = decodeURIComponent(matches[1]);
    }
    return original_Viewer(plugin, parameters);
}
