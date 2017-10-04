ALTER TABLE muk_dms_lock ADD COLUMN operation character varying;

COMMENT ON COLUMN muk_dms_lock.operation IS 'Operation';

