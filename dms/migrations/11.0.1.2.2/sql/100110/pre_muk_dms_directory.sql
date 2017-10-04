ALTER TABLE muk_dms_directory DROP CONSTRAINT muk_dms_directory_parent_id_fkey;

DROP INDEX muk_dms_directory_parent_id_index;

ALTER TABLE muk_dms_directory RENAME COLUMN parent_id TO parent_directory;

ALTER TABLE muk_dms_directory DROP COLUMN message_last_post;

ALTER TABLE muk_dms_directory ADD COLUMN relational_path text;
ALTER TABLE muk_dms_directory ADD COLUMN size integer;
ALTER TABLE muk_dms_directory ADD COLUMN custom_thumbnail bytea;
ALTER TABLE muk_dms_directory ADD COLUMN path character varying;
ALTER TABLE muk_dms_directory ADD COLUMN is_root_directory boolean;
ALTER TABLE muk_dms_directory ADD COLUMN settings integer;

COMMENT ON TABLE muk_dms_directory IS 'MuK Documents  Directory';
COMMENT ON COLUMN muk_dms_directory.create_date IS 'Created on';
COMMENT ON COLUMN muk_dms_directory.write_uid IS 'Last Updated by';
COMMENT ON COLUMN muk_dms_directory.relational_path IS 'Path';
COMMENT ON COLUMN muk_dms_directory.size IS 'Size';
COMMENT ON COLUMN muk_dms_directory.create_uid IS 'Created by';
COMMENT ON COLUMN muk_dms_directory.custom_thumbnail IS 'Custom Thumbnail';
COMMENT ON COLUMN muk_dms_directory.write_date IS 'Last Updated on';
COMMENT ON COLUMN muk_dms_directory.path IS 'Path';
COMMENT ON COLUMN muk_dms_directory.name IS 'Name';
COMMENT ON COLUMN muk_dms_directory.is_root_directory IS 'Root Directory';
COMMENT ON COLUMN muk_dms_directory.settings IS 'Settings';
COMMENT ON COLUMN muk_dms_directory.parent_directory IS 'Parent Directory';

ALTER TABLE muk_dms_directory ADD CONSTRAINT muk_dms_directory_parent_directory_fkey FOREIGN KEY (parent_directory) REFERENCES muk_dms_directory (id) MATCH SIMPLE ON UPDATE NO ACTION ON DELETE RESTRICT;

CREATE INDEX muk_dms_directory_parent_id_index ON muk_dms_directory USING btree (parent_directory);

UPDATE muk_dms_directory SET (is_root_directory, settings) = (SELECT TRUE, id FROM muk_dms_root WHERE muk_dms_root.root_directory = muk_dms_directory.id);
     

