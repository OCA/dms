ALTER TABLE muk_dms_file RENAME COLUMN file_extension TO extension;
ALTER TABLE muk_dms_file RENAME COLUMN file_size TO size;
ALTER TABLE muk_dms_file RENAME COLUMN filename TO name;
ALTER TABLE muk_dms_file RENAME COLUMN mime_type TO mimetype;
ALTER TABLE muk_dms_file RENAME COLUMN file_ref TO reference;

ALTER TABLE muk_dms_file DROP COLUMN message_last_post;
 
ALTER TABLE muk_dms_file ADD COLUMN relational_path text;
ALTER TABLE muk_dms_file ADD COLUMN index_content text;
ALTER TABLE muk_dms_file ADD COLUMN custom_thumbnail bytea;
ALTER TABLE muk_dms_file ADD COLUMN path character varying;
ALTER TABLE muk_dms_file ADD COLUMN settings integer;

COMMENT ON TABLE muk_dms_file IS 'File';
COMMENT ON COLUMN muk_dms_file.relational_path IS 'Path';
COMMENT ON COLUMN muk_dms_file.reference IS 'Data Reference';
COMMENT ON COLUMN muk_dms_file.write_uid IS 'Last Updated by';
COMMENT ON COLUMN muk_dms_file.size IS 'Size';
COMMENT ON COLUMN muk_dms_file.create_uid IS 'Created by';
COMMENT ON COLUMN muk_dms_file.index_content IS 'Indexed Content';
COMMENT ON COLUMN muk_dms_file.custom_thumbnail IS 'Custom Thumbnail';
COMMENT ON COLUMN muk_dms_file.write_date IS 'Last Updated on';
COMMENT ON COLUMN muk_dms_file.path IS 'Path';
COMMENT ON COLUMN muk_dms_file.mimetype IS 'Type';
COMMENT ON COLUMN muk_dms_file.name IS 'Filename';
COMMENT ON COLUMN muk_dms_file.extension IS 'Extension';
COMMENT ON COLUMN muk_dms_file.settings IS 'Settings';
COMMENT ON COLUMN muk_dms_file.create_date IS 'Created on';
COMMENT ON COLUMN muk_dms_file.directory IS 'Directory';

-- UPDATE muk_dms_file SET reference = REPLACE(reference, 'muk_dms.', 'muk_dms.data_');
-- UPDATE muk_dms_file SET reference = REPLACE(reference, '_data', '');
UPDATE muk_dms_file SET reference = REPLACE(reference, 'muk_dms.database_data', 'muk_dms.data_database');
