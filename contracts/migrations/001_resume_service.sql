CREATE TABLE resumes (
  resume_id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        UUID        NOT NULL,
  tenant_id      UUID        NOT NULL,
  storage_object TEXT        NOT NULL,
  name           TEXT,
  email          TEXT,
  raw_text       TEXT        NOT NULL,
  parsed_data    JSONB       NOT NULL DEFAULT '{}',
  parsed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Efficient GetLatestResume: filter by (user_id, tenant_id) + sort by created_at DESC
CREATE INDEX idx_resumes_user_tenant_created ON resumes (user_id, tenant_id, created_at DESC);
-- Efficient tenant-scoped queries (e.g. admin audit, data purge)
CREATE INDEX idx_resumes_tenant ON resumes (tenant_id);
