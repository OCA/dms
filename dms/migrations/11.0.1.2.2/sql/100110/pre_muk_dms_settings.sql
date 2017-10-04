ALTER TABLE muk_dms_root RENAME TO muk_dms_settings;

ALTER TABLE muk_dms_settings DROP COLUMN message_last_post;
ALTER TABLE muk_dms_settings DROP COLUMN is_created;
ALTER TABLE muk_dms_settings DROP COLUMN root_directory;

ALTER TABLE muk_dms_settings ADD COLUMN index_files boolean;
ALTER TABLE muk_dms_settings ADD COLUMN system_locks boolean;

COMMENT ON TABLE muk_dms_settings IS 'MuK Documents Settings';
COMMENT ON COLUMN muk_dms_settings.create_uid IS 'Created by';
COMMENT ON COLUMN muk_dms_settings.name IS 'Name';
COMMENT ON COLUMN muk_dms_settings.index_files IS 'Index Files';
COMMENT ON COLUMN muk_dms_settings.system_locks IS 'System Locks';
COMMENT ON COLUMN muk_dms_settings.write_uid IS 'Last Updated by';
COMMENT ON COLUMN muk_dms_settings.write_date IS 'Last Updated on';
COMMENT ON COLUMN muk_dms_settings.create_date IS 'Created on';
COMMENT ON COLUMN muk_dms_settings.save_type IS 'Save Type';

UPDATE ir_model_data SET (model) = ('muk_dms.settings') WHERE model = 'muk_dms.root';

ALTER SEQUENCE muk_dms_root_id_seq RENAME TO muk_dms_settings_id_seq;