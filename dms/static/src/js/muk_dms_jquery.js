$.ajaxTransport("+binary", function(options, originalOptions, jqXHR) {
    if (window.FormData && (options.dataType && (options.dataType == 'binary')) ||
    		(options.data && ((window.ArrayBuffer && options.data instanceof ArrayBuffer) ||
    	    (window.Blob && options.data instanceof Blob)))) {
        return {
            send: function(headers, callback) {
                var xhr = new XMLHttpRequest(),
				
                url = options.url,
				type = options.type,
				async = options.async || true,
				dataType = options.responseType || "blob",
				data = options.data || null,
				username = options.username || null,
				password = options.password || null;
							
		        xhr.addEventListener('load', function() {
					var data = {};
					data[options.dataType] = xhr.response;
					callback(xhr.status, xhr.statusText, data, xhr.getAllResponseHeaders());
		        });
		 
		        xhr.open(type, url, async, username, password);

				for (var i in headers ) {
					xhr.setRequestHeader(i, headers[i] );
				}
						
                xhr.responseType = dataType;
                xhr.send(data);
            },
            abort: function(){
                jqXHR.abort();
            }
        };
    }
});