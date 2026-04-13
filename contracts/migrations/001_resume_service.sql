CREATE TABLE resumes (
  resume_id  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID        NOT NULL,
  tenant_id  UUID        NOT NULL,
  name       TEXT,
  email      TEXT,
  raw_text   TEXT        NOT NULL,
  parsed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_resumes_user_tenant ON resumes (user_id, tenant_id);
CREATE INDEX idx_resumes_tenant      ON resumes (tenant_id);

ALTER TABLE resumes ADD COLUMN parsed_data JSONB;  -- stores full ResumeData structured fields
