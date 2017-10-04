ALTER TABLE muk_dms_database_data RENAME TO muk_dms_data_database;

ALTER TABLE muk_dms_data_database RENAME COLUMN file TO data;

COMMENT ON TABLE muk_dms_data_database IS 'Database Data Model';
COMMENT ON COLUMN muk_dms_data_database.create_uid IS 'Created by';
COMMENT ON COLUMN muk_dms_data_database.create_date IS 'Created on';
COMMENT ON COLUMN muk_dms_data_database.write_uid IS 'Last Updated by';
COMMENT ON COLUMN muk_dms_data_database.write_date IS 'Last Updated on';
COMMENT ON COLUMN muk_dms_data_database.data IS 'Content';

ALTER SEQUENCE muk_dms_database_data_id_seq RENAME TO muk_dms_data_database_id_seq;
