odoo.define('muk_dms.preview', function(require) {
	var core = require('web.core');
	var session = require('web.session');
	var framework = require('web.framework');
	
	var _t = core._t;
	var QWeb = core.qweb;
	
	var ViewerJSFrame = {
		checkExtension: function(extension) {
			return ['.odt', '.odp', '.ods', '.fodt', '.pdf', '.ott', '.fodp', '.otp', '.fods', '.ots'].includes(extension);
	    },
		createFrame: function(url, title, extension) {
			var frame = _.template('<iframe allowfullscreen="allowfullscreen" \
											webkitallowfullscreen="webkitallowfullscreen" \
											src="/muk_dms/static/lib/ViewerJS/index.html#<%= url_preview %>&title=<%= title_url %>&ext=<%= ext_url %>" \
											class="oe_iframe_viewer" \
									</iframe>');
			return frame({url_preview: url, title_url: encodeURIComponent(title),ext_url: encodeURIComponent(extension)});
		}
	};
	
	var ImageViewer = {
		checkExtension: function(extension) {
			return ['.cod', '.ras', '.fif', '.gif', '.ief', '.jpeg', '.jpg', '.jpe', '.png', '.tiff',
			        '.tif', '.mcf', '.wbmp', '.fh4', '.fh5', '.fhc', '.ico', '.pnm', '.pbm', '.pgm',
			        '.ppm', '.rgb', '.xwd', '.xbm', '.xpm'].includes(extension);
	    },
		createImageTag: function(url, file_size) {
			if(file_size > 1 * 1024 * 1024) {
				var tag = _.template('<span><strong><%= error %></strong><span>');
				return tag({error: _t("The image is too big! No preview can be provided!")});
			} else {
				var tag = _.template('<img src=<%= url_preview %> class="oe_preview_image img-responsive" />');
				return tag({url_preview: url});
			}
		}
	};
	
	var TextViewer = {
		checkType: function(type) {
			return ['text/plain', 'text/html', 'text/javascript', 'application/javascript'].includes(type);
	    },
		createTextTag: function(data) {
			return $('<pre/>').append($('<code class="oe_preview_text"/>').text(data));
		}
	}

	var EmailViewer = {
		checkExtension: function(extension) {
			return extension == '.eml';
	    },
		createPreview: function(mail) {
			mail.body = mail.body.replace(/cid:(\w|\d)+.\w+/g, function(cid) {
				var attachments = $.grep(mail.attachments, function(attachment) {
					return attachment.cid && attachment.cid.includes(cid.substring(4, cid.length));
				});
				return attachments[0].url;
			});
			return QWeb.render("MailViewDialog", {
					reply: mail.InReplyTo ? mail.InReplyTo : "",
					date: mail.Date ? mail.Date : "",
					from: mail.From ? mail.From : "",
					to: mail.To ? mail.To : "",
					cc: mail.CC ? mail.CC : "",
					subject: mail.subject ? mail.subject : "",
					body: mail.body,
					attachments: mail.attachments
			});
								   
		}
	};
	
	var MicrosoftWordViewer = {
		checkExtension: function(extension) {
			return extension == '.docx';
	    },
	    createTextTag: function(data) {
			return $('<div class="oe_preview_msword"/>').html(data.result);
		}
	};
	
	var PreviewViewer = {
		initPreview: function() {
			$('body').append($(QWeb.render("DMSModal", {})));
		},
		handleClick: function(self, id, file_size, filename, file_extension, mime_type, link_preview, popover_id) {
        	var showModal = false;
        	
			if(ViewerJSFrame.checkExtension(file_extension)) {
    			$('#oe_modal_viewer .oe_modal_viewer_title').text(_t("Document Viewer"));
    			$('#oe_modal_viewer .oe_modal_viewer_body').html(ViewerJSFrame.createFrame(link_preview,
    					filename, file_extension));
    			showModal = true;
    		} else if(ImageViewer.checkExtension(file_extension)) {
    			$('#oe_modal_viewer .oe_modal_viewer_title').text(_t("Image Viewer"));
    			$('#oe_modal_viewer .oe_modal_viewer_body').html(ImageViewer.createImageTag(link_preview, file_size));
    			showModal = true;
    		} else if(TextViewer.checkType(mime_type)) {
    			$.get(link_preview, function(data) {
    				$('#oe_modal_viewer .oe_modal_viewer_title').text(_t("Text Viewer"));
        			$('#oe_modal_viewer .oe_modal_viewer_body').html(TextViewer.createTextTag(data));
        			hljs.highlightBlock($('#oe_modal_viewer .oe_preview_text')[0]);
    			    hljs.lineNumbersBlock($('#oe_modal_viewer .oe_preview_text')[0]);
				});
    			showModal = true;
    		} else if(EmailViewer.checkExtension(file_extension)) {
    			$.get('/dms/parse/mail?id='+id, function(data) {
    				$('#oe_modal_viewer .oe_modal_viewer_title').text(_t("Mail Viewer"));
        			$('#oe_modal_viewer .oe_modal_viewer_body').html(EmailViewer.createPreview(data));
        			$('#oe_modal_viewer .oe_attachment_tab').on('shown.bs.tab', function(event){
        			    var active_tab = $(event.target).attr("href");
        			    if(!$.trim(self.$el.find(active_tab).html())) {
        			    	var data = self.$el.find(active_tab).data();
        			    	if(ViewerJSFrame.checkExtension(data.ext)) {
            			    	self.$el.find(active_tab).html(ViewerJSFrame.createFrame(data.url, data.filename, data.ext));
        	        		} else if(ImageViewer.checkExtension(data.ext)) {
        	        			self.$el.find(active_tab).html(ImageViewer.createImageTag(data.url));
        	        		} else if(TextViewer.checkType(data.mimetype)) {
        	        			$.get(data.url, function(data) {
        	        				self.$el.find(active_tab).html(TextViewer.createTextTag(data));
        	    				});
        	        		}
        			    }
        			});

				});
    			showModal = true;
	        } else if(MicrosoftWordViewer.checkExtension(file_extension)) {
    			$.get('/dms/parse/msword?id='+id, function(data) {
    				$('#oe_modal_viewer .oe_modal_viewer_title').text(_t("MSOffice Viewer"));
        			$('#oe_modal_viewer .oe_modal_viewer_body').html(MicrosoftWordViewer.createTextTag(data));
				});
    			showModal = true;
	        }
    		
    		if(showModal) {
    			$('#oe_modal_viewer').on('shown.bs.modal', function () {
    				$(this).find('.modal-content').css({
    					height:'100%'
    			    });
    				$(this).find('.modal-body').css({
    			        height:'100%'
    			    });
    			});
    			$('#oe_modal_viewer .modal-content').resizable({
    				ghost: true
    			});
    			$('#oe_modal_viewer .modal-dialog').draggable();
    			$('#oe_modal_viewer').modal('show');
    		} else {
    			self.$el.find(popover_id).popover({
                    placement: 'right',
                    trigger: 'manual',
                    html: true,
                    title:  _t("Viewer!") + ' <a class="close" href="#">&times;</a>',
                    content: _t("The file type is currently not supported!")
                }).on('shown.bs.popover', function(e) {
                    var current_popover = '#' + $(e.target).attr('aria-describedby');
                    var $cur_pop = $(current_popover);
                    $cur_pop.find('.close').click(function(){
                    	self.$el.find(popover_id).popover('hide');
                    });
                    setTimeout(function() {
                    	self.$('.popover').fadeOut('slow', function() {}); 
                    }, 2000);
                });
    			self.$el.find(popover_id).popover('show');
    		}
	    },
	};
	
	var PreviewHTML = {
			getPreviewHTML: function(id, file_size, filename, file_extension, mime_type, link_preview) {
	        	var result = $.Deferred();
				if(ViewerJSFrame.checkExtension(file_extension)) {
					result.resolve(ViewerJSFrame.createFrame(link_preview,filename, file_extension));
	    		} else if(ImageViewer.checkExtension(file_extension)) {
	    			result.resolve(ImageViewer.createImageTag(link_preview, file_size));
	    		} else if(TextViewer.checkType(mime_type)) {
	    			$.get(link_preview, function(data) {
	    				var container = $('<div>')
	        			container.html(TextViewer.createTextTag(data));
	        			hljs.highlightBlock($(container).find('.oe_preview_text')[0]);
	    			    hljs.lineNumbersBlock($(container).find('.oe_preview_text')[0]);
	    			    result.resolve(container);
					});
	    		} else if(EmailViewer.checkExtension(file_extension)) {
	    			$.get('/dms/parse/mail?id='+id, function(data) {
	    				var container = $('<div>')
	        			container.html(EmailViewer.createPreview(data));
	    				container.$('.oe_attachment_tab').on('shown.bs.tab', function(event){
	        			    var active_tab = $(event.target).attr("href");
	        			    if(!$.trim(self.$el.find(active_tab).html())) {
	        			    	var data = self.$el.find(active_tab).data();
	        			    	if(ViewerJSFrame.checkExtension(data.ext)) {
	            			    	self.$el.find(active_tab).html(ViewerJSFrame.createFrame(data.url, data.filename, data.ext));
	        	        		} else if(ImageViewer.checkExtension(data.ext)) {
	        	        			self.$el.find(active_tab).html(ImageViewer.createImageTag(data.url));
	        	        		} else if(TextViewer.checkType(data.mimetype)) {
	        	        			$.get(data.url, function(data) {
	        	        				self.$el.find(active_tab).html(TextViewer.createTextTag(data));
	        	    				});
	        	        		}
	        			    }
	        			});
	    				result.resolve(container);
					});
		        } else if(MicrosoftWordViewer.checkExtension(file_extension)) {
		        	$.get('/dms/parse/msword?id='+id, function(data) {
	    				var container = $('<div>')
	        			container.html(MicrosoftWordViewer.createTextTag(data));
	    				result.resolve(container);
					});
		        } else {
		        	result.resolve("<span>" + _t("The file type is currently not supported!") + "</span>");
		        }
				return result;
		    },
		};

	return {
		PreviewViewer : PreviewViewer,
		PreviewHTML : PreviewHTML,
	};
});