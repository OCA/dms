ALTER TABLE muk_dms_directory ADD CONSTRAINT muk_dms_directory_settings_fkey FOREIGN KEY (settings) REFERENCES muk_dms_settings (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE RESTRICT;
ALTER TABLE muk_dms_file ADD CONSTRAINT muk_dms_file_settings_fkey FOREIGN KEY (settings) REFERENCES muk_dms_settings (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE RESTRICT;
