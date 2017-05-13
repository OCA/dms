odoo.define('muk_dms_widgets.form_widgets', function(require) {
	var core = require('web.core');
	var session = require('web.session');
	var framework = require('web.framework');
	var form_common = require('web.form_common');
	
	var Dialog = require('web.Dialog');
	var Model = require("web.Model");
	
	var Preview = require('muk_dms.preview');

	var _t = core._t;
	var QWeb = core.qweb;

	var Data = new Model('ir.model.data', session.user_context);
	var Directories = new Model('muk_dms.directory', session.user_context);
	var Files = new Model('muk_dms.file', session.user_context);
	
	var FieldPath = form_common.AbstractField.extend({
		template : 'DMSFieldPath',
		events : {
			'click a' : 'link_clicked',
		},
		init : function() {
			this._super.apply(this, arguments);
			
			if(this.options.seperator) {
				this.seperator = this.options.seperator;
			} else {
				this.seperator = '/';
			}
			if(this.options.last_seperator) {
				this.last_seperator = this.options.last_seperator;
			} else {
				this.last_seperator = false;
			}
			if(this.options.last_clickable) {
				this.last_clickable = this.options.last_clickable;
			} else {
				this.last_clickable = false;
			}
		},
		start : function() {
			this._super.apply(this, arguments);
			Preview.PreviewViewer.initPreview();
		},
		render_value : function() {
			this.path = JSON.parse(this.get('value'));
			var inner_html = "";
			_.each(this.path, function(element, index, list) {
				if (!this.last_clickable && index == list.length - 1) {
					inner_html += '<span class="oe_form_uri" data-model="' + element.model +
								  '" data-id="' + element.id + '">'
					inner_html += element.name
					inner_html += '</span>';
					if (index == list.length - 1) {
						if(this.last_seperator) {
							inner_html += '<span>' + this.seperator + '</span>';
						}
					} else {
						inner_html += '<span>' + this.seperator + '</span>';
					}
				} else {
					inner_html += '<a href="javascript:void(0);" class="oe_form_uri" data-model="' 
						          + element.model + '" data-id="' + element.id + '">'
					inner_html += element.name
					inner_html += '</a>';
					if (index == list.length - 1) {
						if(this.last_seperator) {
							inner_html += '<span>' + this.seperator + '</span>';
						}
					} else {
						inner_html += '<span>' + this.seperator + '</span>';
					}
				}
			}, this);
			this.$el.html(inner_html);
		},
		link_clicked : function(event) {
			this.do_action({
				type : 'ir.actions.act_window',
				res_model : $(event.currentTarget).data('model'),
				res_id : $(event.currentTarget).data('id'),
				views : [[ false, 'form' ]],
				target : 'current',
				context : {},
			});
		}
	});

	var PreviewFieldBinaryFile = core.form_widget_registry.get("binary").extend({
		template: 'PreviewFieldBinaryFile',
		initialize_content: function() {
	        var self = this;
	        this.$inputFile = this.$('.o_form_input_file');
	        this.$inputFile.change(this.on_file_change);
	        var self = this;
	        this.$('.o_select_file_button').click(function() {
	            self.$inputFile.click();
	        });
	        this.$('.o_clear_file_button').click(this.on_clear);
	        if (!this.get("effective_readonly")) {
	        	this.$input = this.$('.o_form_input').eq(0);
	            this.$input.on('click', function() {
	                self.$inputFile.click();
	            });
	        }
	    },
	    render_value: function() {
	    	var self = this;
	        if (!this.get("effective_readonly")) {
	        	self._super();
	        } else {
	        	self.$el.find('#link').text(_t("Download"));
	        	self.$el.find('#link').attr("href", self.view.datarecord.link_download);
	        	self.$el.find('.o_binary_preview').click(function() {
	        		Preview.PreviewViewer.handleClick(self, self.view.datarecord.id, self.view.datarecord.file_size,
	        				self.view.datarecord.filename, self.view.datarecord.file_extension,
	        				self.view.datarecord.mime_type, self.view.datarecord.link_preview, '.oe-binary-preview');
	        	});
	        }
	    },
	});
	
	var FinderDialog = Dialog.extend({
		init: function(parent, options) {
			var self = this;
			_.defaults(options || {}, {
	            title: _t('Finder'), 
	            subtitle: '',
	            size: 'large',
	            $content: QWeb.render("DirectoryDialog", {}),
	            buttons: [
	                {text: _t("Select"), classes: "btn-primary o_formdialog_save", click: function() {
	                	self.select();
	                }},
	            	{text: _t("Close"), classes: "btn-default o_form_button_cancel", close: true}
				],
	        });
			this.directories = false;
	    	this.selected_directory = false;
	        this._super(parent, options);
	    },
	    init_data: function() {
	        var self = this;
	        Directories.query(['name', 'parent_id']).all().then(function(directories) {
	        	var data = [];
	        	_.each(directories, function(value, key, list) {	        		
	        		data.push({
	        			id: value.id,
	        			parent: (value.parent_id ? value.parent_id[0] : "#"),
	        			text: value.name,
	        		});
	        	});
	        	self.directories = directories;
	        	self.$('.dir_tree').jstree({ 
		        	core: {
		        		animation: 150,
		        		multiple: false,
		        	    check_callback: true,
		        	    themes: { "stripes": true },
		        		data: data
		        	},
		        	plugins: [
		        	    "unique", "contextmenu", "search", "wholerow"
    	            ],
    	            contextmenu: {
    	                items: {
    	                	create: {
    	    					separator_before: false,
    	    					separator_after: false,
    	    					_disabled: false,
    	    					icon: "fa fa-plus-circle",
    	    					label: _t("Create"),
    	    					action: function (data) {
    	    						var inst = $.jstree.reference(data.reference);
    	    						var	obj = inst.get_node(data.reference);
    	    						inst.create_node(obj, {}, "last", function (new_node) {
	    								inst.edit(new_node, _t("New"), function(node) {
	    									Directories.call("create", [{name: node.text, parent_id: obj.id}])
	    				    				.done(function (result) {
    	    									self.$('.dir_tree').jstree(true).set_id(node, result);
	    				    				})
	    				    				.fail(function(xhr, status, text) {
	    				    					self.do_warn(_t("Create..."), _t("An error occurred during create!"));
	    				    				});
	    								});
    	    						});
    	    					}
    	    				},
    	                }
    	            },
		        }).bind('loaded.jstree', function (e, data) {
	        	    var depth = 3;
	        	    data.instance.get_container().find('li').each(function (i) {
	        	        if (data.instance.get_path($(this)).length <= depth) {
	        	        	data.instance.open_node($(this));
	        	        }
	        	    }); 
	        	});
	        	self.$('.dir_tree').on('changed.jstree', function (e, data) {
	        		self.selected_directory = [data.node.id, data.node.text];
	        	});
	        	var timeout = false;
	        	self.$('#dir_search').keyup(function() {
	        	    if(timeout) {
	        	    	clearTimeout(timeout); 
	        	    }
	        	    timeout = setTimeout(function() {
	        	    	var v = self.$('#dir_search').val();
	        	    	self.$('.dir_tree').jstree(true).search(v);
	        	    }, 250);
        	   });
    		});
	    },
	    open: function() {
	        this._super();
	        this.init_data();
	        return this;
	    },
	    renderElement: function() {
	        this._super();
	    },
	    select: function() {
        	this.trigger('directory_selected', this.selected_directory);
            this.close();
	    }
	});
	
	var directories = new Bloodhound({
		datumTokenizer: Bloodhound.tokenizers.obj.whitespace("value"),
		queryTokenizer: Bloodhound.tokenizers.whitespace,
		remote : {
			url : '/dms/query/directories?query=%QUERY',
			wildcard : '%QUERY',
			transform: function (response) {
				directories.suggestions = response;
	            return response;
        	}
		}
	});

	var DMSFieldBinaryFile = form_common.AbstractField.extend(form_common.ReinitializeFieldMixin, {
		template: 'DMSFieldBinary',
		events: {
	        "click a.oe_download_button": "download",
	        "click button.oe_info_button": "info",
	        "click button.oe_preview_button": "preview",
	        "click button.oe_checkout_button": "checkout",
	        "click button.oe_link_button": "link",
	        "click button.oe_checkin_button": "checkin",
	        "click i.oe_dir_cm_button": "open_finder",
	        "click button.oe_form_binary_file_clear": "clear",
	        "change input.field_binary_hidden": "fileselect",
	    },
		init: function(field_manager, node) {
			var self = this;
			this._super(field_manager, node);
			this.downloadOnly = !!this.node.attrs.downloadonly;
			this.hideinfo = !!this.node.attrs.hideinfo;
			this.hidepreview = !!this.node.attrs.hidepreview;
			this.hidecheckout = !!this.node.attrs.hidecheckout;
			this.hidelink = !!this.node.attrs.hidelink;
			this.max_upload_size = 50 * 1024 * 1024;
			this.file_base64 = false;
			this.delete_file = false;
	    },
	    initialize_content: function() {
	    	var self = this;
			Preview.PreviewViewer.initPreview();
	    	this.$('[data-toggle="tooltip"]').tooltip(); 
	    	if (this.get("effective_readonly")) {
	    		if(this.downloadOnly) {
	    			this.$el.find('.oe_info_button').hide();
	    			this.$el.find('.oe_checkout_button').hide();
	    			this.$el.find('.oe_link_button').hide();
	    		}
	    		if(this.hideinfo) {
	    			this.$el.find('.oe_info_button').hide();
	    		}
	    		if(this.hidepreview) {
	    			this.$el.find('.oe_preview_button').hide();
	    		}
	    		if(this.hidecheckout) {
	    			this.$el.find('.oe_checkout_button').hide();
	    		}
	    		if(this.hidelink) {
	    			this.$el.find('.oe_link_button').hide();
	    		}
	    	} else {
	    		if(this.downloadOnly) {
	    			this.$el.hide();
	    		} else {
			    	if(this.node.attrs.directory) {
			    		this.$el.find('.oe_m2o_cm_button').hide();
			    		this.$el.find('.oe_dms_form_input_many2one').attr("readonly", "readonly");
			    	} else {
			    		this.$el.find('.oe_dms_form_input_many2one').typeahead({
			    			limit: 10,
			    		}, 
			    		{
		    				name : 'directories',
		    				display: 'directory_name',
		    				source : directories
		    			}).bind('change blur', function (ev) {
		    				if (!!$(ev.target).val() && $(ev.target).data('originalValue') !== $(ev.target).val()){
		    					var found_id = false;
			    				_.each(directories.suggestions, function(value, key, list) {
			    					if($(ev.target).val() == value.directory_name) {
			    						found_id = value.directory_id;
			    					}
			    				});
			    				if(found_id) {
			    					self.$el.find('.oe_dms_form_input_many2one').data("id", found_id);
			    				} else {
			    					self.$el.find('.oe_dms_form_input_many2one').val("");
			    					self.$el.find('.oe_dms_form_input_many2one').removeData("id");
			    				}	
		    		        } else {
		    		        	$(ev.target).val($(ev.target).data('originalValue'));
		    		        }
		    			});
			    		this.$el.find('.oe_dms_form_input_many2one').on('focus', function (ev) {
			    			$(ev.target).data('originalValue', $(ev.target).val());
			    		});
		        	}
	    		}
	    	}
	    },
	    render_value: function() {
	    	var self = this;
	    	var value = self.get('value');
	    	if (this.get("effective_readonly")) {
	    		this.$el.toggle(!!value);
	    		if (value) {
	    			var link_value = _t("Download");
	    			this.$el.find('.oe_download_button').toggle(!!value);
	    			if(this.view && this.node.attrs.filename) {
	    				link_value += " " + this.view.datarecord[this.node.attrs.filename];
	    			} else {
	    				if(value instanceof Array){
	    					link_value += " " + value[1];
	    				}
		            }
					this.$el.find('.oe_download_button').text(link_value);
		    		Files.call("check_lock", [value[0]]).then(function (lock) {
		    			if(lock) {
		    				self.$el.find('.oe_checkout_button').hide();
		    				if(lock[1] == session.uid) {
		    					self.$el.find('.oe_checkin_button').show();
		    				}
		    			}
		 	        });
	    		}
	        } else {
	        	if(this.node.attrs.directory) {
	        		Data.call('get_object_reference', [this.view.dataset.model.split(".")[0], this.node.attrs.directory])
	        		.then(function (directory_ref) {
		        		Directories.query(["name"]).filter([['id', '=', directory_ref[1]]]).first().then(function(directory) {
		        			self.$el.find('.oe_dms_form_input_many2one').val(directory.name);
		        			self.$el.find('.oe_dms_form_input_many2one').data("id", directory.id);
		        			self.$el.find('.oe_dir_cm_button').hide();
			    		});
		        	});
	        	} else {
	        		self.$el.find('.oe_dir_cm_button').show();
	        	}
	        	if (value) {
	        		Files.call("check_lock", [value[0]]).then(function (lock) {
		    			if(!lock || lock && lock[1] == session.uid) {
		    				self.$el.find('.oe_form_lock_message').hide();
		    				self.$el.find('.oe_form_field_binary').show();
		    				if(self.view && self.node.attrs.filename) {	    				
		    					self.$el.find('.oe_dms_binary_input').val(self.view.datarecord[self.node.attrs.filename]);
			    			} else {
			    				if(value instanceof Array){
			    					self.$el.find('.oe_dms_binary_input').val(value[1]);
			    				} else {
			    					self.$el.find('.oe_dms_binary_input').val(_t("Data..."));
			    				}
				            }
			    			if(!self.node.attrs.directory) {
			    				Files.query([]).filter([['id', '=', value[0]]]).first().then(function(file) {
				        			self.$el.find('.oe_dms_form_input_many2one').val(file.directory[1]);
				        			self.$el.find('.oe_dms_form_input_many2one').data("id", file.directory[0]);
			        			}); 
			    			}
		    			} else {
		    				self.$el.find('.oe_form_lock_message').show();
		    				self.$el.find('.oe_form_field_binary').hide();
		    			}
		 	        });
	            } else {
	            	self.file_base64 = false;
	            	self.$el.find('.oe_dms_binary_input').val("");
					self.$el.find('.oe_dms_form_input_many2one').val("");
					self.$el.find('.oe_dms_form_input_many2one').removeData("id");
	            }
	        }
	    },
	    info: function(ev) {
	    	var self = this;
	    	var value = self.get('value');
	        if (!value) {
	        	this.do_warn(_t("Info..."), _t("The field is empty, there's nothing to show!"));
	        } else {
	        	Files.query([]).filter([['id', '=', value[0]]]).first()
		        .then(function(file) {
		        	new Dialog(this, {
		                size: 'medium',
		                title: _t("File Info!"),
		                $content: $('<div>').html(QWeb.render('DMSInfoDialog', {
		                	file: file
		                }))
		            }).open();
		        });
	        }
	    },
	    link: function(ev) {
	    	var value = this.get('value');
	        if (!value) {
	        	this.do_warn(_t("Link..."), _t("The field is empty!"));
	        } else {
	        	this.do_action({
	                type: 'ir.actions.act_window',
	                res_model: "muk_dms.file",
	                res_id: value[0],
	                views: [[false, 'form']],
	                target: 'current',
	                context: {},
	            });
	        }
	    },
	    preview: function(ev) {
	    	var self = this;
	    	var value = self.get('value');
	        if (!value) {
	        	this.do_warn(_t("Preview..."), _t("The field is empty, there's nothing to preview!"));
	        } else {
	        	Files.query([]).filter([['id', '=', value[0]]]).first()
		        .then(function(file) {
		        	Preview.PreviewViewer.handleClick(self, file.id, file.file_size, file.filename,
		        			file.file_extension, file.mime_type, file.link_preview, '.oe_preview_button');
		        });
	        }
	    },
	    download: function(ev) {
	    	var self = this;
	    	var value = self.get('value');
	        if (!value) {
	        	this.do_warn(_t("Download..."), _t("The field is empty, there's nothing to download!"));
	            ev.stopPropagation();
	        } else {
	        	Files.query([]).filter([['id', '=', value[0]]]).first()
		        .then(function(file) {
		        	$.ajax({
		        	    url: file.link_download,
		        	    type: "GET",
		        	    dataType: "binary",
		        	    processData: false,
		        	    beforeSend: function(xhr, settings) {
		        	    	framework.blockUI();
		        	    },
		        	    success: function(data, status, xhr){
		        		  	saveAs(data, file.filename);
		        	    },
		        	    error:function(xhr, status, text) {
		        	    	self.do_warn(_t("Download..."), _t("An error occurred during download!"));
			  			},
		        	    complete: function(xhr, status) {
		        	    	framework.unblockUI();
		        	    },
		        	});
	   			});
	            ev.stopPropagation();
	            return false; 
	        }
	    },
	    checkout: function(ev) {
	    	var self = this;
	    	var value = self.get('value');
	        if (!value) {
	        	this.do_warn(_t("Checkout..."), _t("The field is empty, there's nothing to download!"));
	            ev.stopPropagation();
	        } else {
	            Files.query([]).filter([['id', '=', value[0]]]).first()
		        .then(function(file) {
		        	$.ajax({
		        	    url: file.link_checkout,
		        	    type: "GET",
		        	    dataType: "binary",
		        	    processData: false,
		        	    beforeSend: function(xhr, settings) {
		        	    	framework.blockUI();
		        	    },
		        	    success: function(data, status, xhr){
							var file_id = xhr.getResponseHeader("File-ID");
							var file_token = xhr.getResponseHeader("File-Token");
		        	    	self.$el.find('.oe_checkout_button').hide();
							self.$el.find('.oe_checkin_button').show();
		        		  	saveAs(data, file.filename);
		        			self.do_notify(_t("Checkout Information"),
		        					QWeb.render("CheckOutNotification", {file_id: file_id, file_token: file_token}), true);
		        	    },
		        	    error:function(xhr, status, text) {
		        	    	self.do_warn(_t("Checkout..."), _t("An error occurred during checkout!"));
			  			},
		        	    complete: function(xhr, status) {
		        	    	framework.unblockUI();
		        	    },
		        	});
	   			});
	            ev.stopPropagation();
	            return false; 
	        }
	    },
	    checkin: function(ev) {
	    	var self = this;
	    	Files.call("user_unlock", [this.get('value')[0]])
	    	.done(function () {
				self.$el.find('.oe_checkout_button').show();
				self.$el.find('.oe_checkin_button').hide();
			})
			.fail(function(xhr, status, text) {
				self.do_warn(_t("Checkin..."), _t("An error occurred during checkin!"));
			});
	    	return false;
	    },
	    open_finder: function(ev) {
	    	var self = this;
	    	var finder = new FinderDialog(self, {}).open()
	    	.on('directory_selected', self, function(result){
		    	if(result) {
		    		var dir_id = parseInt(result[0]) || false;
		    		var dir_name = result[1];
		    		if(dir_id) {
			    		self.$el.find('.oe_dms_form_input_many2one').val(dir_name);
			    		self.$el.find('.oe_dms_form_input_many2one').data("id", dir_id);
		    		}
	    		}
            });
	    },
	    set_filename: function(filename) {
	    	this.$el.find('.oe_dms_binary_input').val(filename);
	      	if(this.node.attrs.filename) {	    				
	      		var field = this.field_manager.fields[this.node.attrs.filename];
	      		if (field) {
	                field.set_value(filename);
	                field._dirty_flag = true;
	            }
			}
	    },
	    fileselect: function(ev) {
	    	var self = this;
	    	var input = $(ev.target);
	    	var reader = new FileReader();
	    	reader.onload = function(e) {
	    		self.delete_file = false;
		      	self.file_base64 = reader.result.substr(reader.result.indexOf("base64,") + 7);
		      	self.set_filename(input.val().replace(/\\/g, '/').replace(/.*\//, ''));
		    }
	    	if(input.get(0).files[0]) {
	    		if(self.max_upload_size < input.get(0).files[0].size) {
	    			self.do_warn(_t("Upload..."), _t("The file is too big!"));
	    		} else {
	    			reader.readAsDataURL(input.get(0).files[0]);
	    		}
		    }
	    	return false;
	    },
	    clear: function(ev) {
	    	if (this.get('value')) {
	    		this.delete_file = true;
	    		this.$el.find('.oe_dms_binary_input').val("");
	        }
	        return false;
	    },
	    commit_value: function() {
	    	var self = this;
	    	var invalid = false;
	    	var value = this.get('value');
	    	var commited_value = $.Deferred();
	    	_.each(self.field_manager.fields, function (f) {
	    		if (!f.is_valid()) {
	    			invalid = true;
                }
            });
	    	if(self.commited || invalid) {
	    		commited_value.resolve();
	    	} else {
		    	if (value && value instanceof Array && this.delete_file) {
		    		Files.call("check_lock", [value[0]]).then(function (lock) {
		    	    	var unlocked = $.Deferred();
		    			if(lock && lock[1] == session.uid) {
		    				Files.call("user_unlock", [self.get('value')[0]]).then(function (lock) {
		    					unlocked.resolve();
		    				});
		    			} else {
		    				unlocked.resolve();
		    			}
		    			$.when(unlocked).done(function ( ) {
		    				Files.call("unlink", [value[0]])
		    		    	.done(function () {
		    		    		self.set({'value': false});
		    				})
		    				.fail(function(xhr, status, text) {
		    					self.do_warn(_t("Delete..."), _t("An error occurred during delete!"));
		    				})
		    				.always(function() {
		    					commited_value.resolve();
		    				});
		    			});
		    			
		    		});
		    	} else {
	    			var directory_id = self.$el.find('.oe_dms_form_input_many2one').data("id");
	    			var file_base64 = self.file_base64;
	    			var filename = self.$el.find('.oe_dms_binary_input').val();
	    			if(self.view && self.node.attrs.filename && self.view.fields[self.node.attrs.filename]) {	    				
	    				var filename_field_value = self.view.fields[self.node.attrs.filename].get('value');
	    				if(filename_field_value) {
	    					filename = filename_field_value;
	    				}
	    			}
		    		if (value && value instanceof Array) {
		    			var values = {};
		    			if(directory_id) values.directory = directory_id;
		    			if(filename) values.filename = filename;
		    			if(file_base64) values.file = file_base64;
		    			Files.call("write", [value[0], values])
	    				.fail(function(xhr, status, text) {
	    					self.do_warn(_t("Write..."), _t("An error occurred during write!"));
	    				})
	    				.always(function() {
	    					commited_value.resolve();
	    				});
		    		} else if(!value) {
		    			if(directory_id && filename && file_base64) {
		    				Files.call("create", [{directory: directory_id, filename: filename, file: file_base64}])
		    				.done(function (result) {
		    					self.internal_set_value(result);
		    				})
		    				.fail(function(xhr, status, text) {
		    					self.do_warn(_t("Create..."), _t("An error occurred during create!"));
		    				})
		    				.always(function() {
		    					commited_value.resolve();
		    				});
		    			} else if(!file_base64) {
		    				commited_value.resolve();
		    			} else {
		    				self.do_warn(_t("Save/Create..."), _t("Some fields are empty!"));
		    				commited_value.resolve();
		    			}
		    		} else {
		    			commited_value.resolve();
		    		}
		    	}
	    	}
	        return $.when(commited_value);
	    },
	});

	core.form_widget_registry.add('dms_path', FieldPath);
	core.form_widget_registry.add('preview_file', PreviewFieldBinaryFile);
	core.form_widget_registry.add('dms_file', DMSFieldBinaryFile);

	return {
		FieldPath : FieldPath,
		PreviewFieldBinaryFile: PreviewFieldBinaryFile,
		DMSFieldBinaryFile: DMSFieldBinaryFile,
	};
});
