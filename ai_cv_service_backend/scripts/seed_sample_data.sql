BEGIN;

INSERT INTO companies (name, website, description, location)
VALUES
    ('TechNova Solutions', 'https://technova.example', 'Software and AI consulting', 'Ha Noi'),
    ('DigitalWave Labs', 'https://digitalwave.example', 'Product engineering studio', 'Ho Chi Minh City'),
    ('SkyBridge Systems', 'https://skybridge.example', 'Cloud and data platform company', 'Da Nang')
ON CONFLICT (name) DO NOTHING;

INSERT INTO users (email, full_name, hashed_password, is_active, role_id, company_id)
SELECT
    'admin@example.com',
    'System Admin',
    '$2b$12$5p7sbXi5S8RQ770N37KwkOTdVDCItoB.wn6B.qvZ60kNu2Ztt2jj2',
    TRUE,
    r.id,
    NULL
FROM roles r
WHERE r.name = 'admin'
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (email, full_name, hashed_password, is_active, role_id, company_id)
SELECT
    seed.email,
    seed.full_name,
    '$2b$12$5p7sbXi5S8RQ770N37KwkOTdVDCItoB.wn6B.qvZ60kNu2Ztt2jj2',
    TRUE,
    r.id,
    c.id
FROM (
    VALUES
        ('hr1@example.com', 'HR Le Minh', 'TechNova Solutions'),
        ('hr2@example.com', 'HR Tran Anh', 'DigitalWave Labs'),
        ('hr3@example.com', 'HR Nguyen Hoa', 'SkyBridge Systems')
) AS seed(email, full_name, company_name)
JOIN roles r ON r.name = 'hr'
JOIN companies c ON c.name = seed.company_name
ON CONFLICT (email) DO NOTHING;

INSERT INTO users (email, full_name, hashed_password, is_active, role_id, company_id)
SELECT
    format('candidate%s@example.com', lpad(g::text, 2, '0')),
    format('Candidate %s', g),
    '$2b$12$5p7sbXi5S8RQ770N37KwkOTdVDCItoB.wn6B.qvZ60kNu2Ztt2jj2',
    TRUE,
    r.id,
    NULL
FROM generate_series(1, 30) AS g
JOIN roles r ON r.name = 'user'
ON CONFLICT (email) DO NOTHING;

INSERT INTO jobs (title, description, status, required_skills, salary_min, salary_max, location, company_id, created_by_id)
SELECT
    seed.title,
    seed.description,
    'open',
    seed.required_skills::jsonb,
    seed.salary_min,
    seed.salary_max,
    seed.location,
    c.id,
    hr.id
FROM (
    VALUES
        ('TechNova Solutions', 'Senior Backend Engineer', 'Build APIs and microservices with FastAPI and PostgreSQL.', '["python","fastapi","postgresql","docker"]', 1800, 2800, 'Ha Noi', 'hr1@example.com'),
        ('TechNova Solutions', 'Data Engineer', 'Develop data pipelines and warehouse models for recruitment analytics.', '["python","sql","airflow","postgresql"]', 1500, 2400, 'Ha Noi', 'hr1@example.com'),
        ('DigitalWave Labs', 'Frontend Engineer', 'Build modern React interfaces for HR and recruitment platforms.', '["javascript","react","typescript","css"]', 1400, 2200, 'Ho Chi Minh City', 'hr2@example.com'),
        ('DigitalWave Labs', 'Product Manager', 'Lead roadmap and cross-functional execution for HR SaaS modules.', '["communication","analytics","product"]', 1700, 2600, 'Ho Chi Minh City', 'hr2@example.com'),
        ('SkyBridge Systems', 'DevOps Engineer', 'Design CI/CD and cloud infrastructure for scaling services.', '["docker","kubernetes","aws","linux"]', 1900, 2900, 'Da Nang', 'hr3@example.com'),
        ('SkyBridge Systems', 'QA Engineer', 'Automate test plans and quality gates in CI workflows.', '["testing","automation","api","sql"]', 1200, 1900, 'Da Nang', 'hr3@example.com')
) AS seed(company_name, title, description, required_skills, salary_min, salary_max, location, hr_email)
JOIN companies c ON c.name = seed.company_name
JOIN users hr ON hr.email = seed.hr_email
WHERE NOT EXISTS (
    SELECT 1
    FROM jobs j
    WHERE j.title = seed.title
      AND j.company_id = c.id
      AND j.deleted_at IS NULL
);

INSERT INTO cvs (file_name, file_path, mime_type, extracted_skills, extracted_experience, extracted_education, user_id)
SELECT
    format('seed_candidate_%s.txt', idx.num),
    format('uploads/cvs/seed_candidate_%s.txt', idx.num),
    'text/plain',
    '["python","fastapi","sql","docker","react"]'::jsonb,
    format('["%s years experience in software engineering"]', ((idx.num % 8) + 1))::jsonb,
    '["Bachelor in Computer Science"]'::jsonb,
    u.id
FROM users u
JOIN LATERAL (
    SELECT CAST(substring(u.email FROM 'candidate0*([0-9]+)') AS INT) AS num
) AS idx ON TRUE
WHERE u.email LIKE 'candidate%@example.com'
  AND idx.num IS NOT NULL
  AND NOT EXISTS (
      SELECT 1
      FROM cvs c
      WHERE c.user_id = u.id
        AND c.file_name = format('seed_candidate_%s.txt', idx.num)
  );

INSERT INTO applications (status, notes, job_id, candidate_id, cv_id, reviewed_by)
SELECT
    CASE
        WHEN ((u.id + j.id) % 7) IN (0, 1) THEN 'accepted'
        WHEN ((u.id + j.id) % 7) = 2 THEN 'rejected'
        ELSE 'pending'
    END,
    CASE
        WHEN ((u.id + j.id) % 7) IN (0, 1) THEN 'Strong profile for this role'
        WHEN ((u.id + j.id) % 7) = 2 THEN 'Needs stronger matching skills'
        ELSE 'Waiting for HR review'
    END,
    j.id,
    u.id,
    cv.id,
    CASE
        WHEN ((u.id + j.id) % 7) IN (0, 1, 2) THEN j.created_by_id
        ELSE NULL
    END
FROM users u
JOIN jobs j ON j.deleted_at IS NULL
JOIN LATERAL (
    SELECT c.id
    FROM cvs c
    WHERE c.user_id = u.id
    ORDER BY c.created_at DESC
    LIMIT 1
) AS cv ON TRUE
WHERE u.email LIKE 'candidate%@example.com'
  AND ((u.id + j.id) % 3 = 0)
ON CONFLICT (job_id, candidate_id) DO NOTHING;

INSERT INTO ai_scores (score, reasoning, application_id)
SELECT
    ROUND((50 + random() * 50)::numeric, 2),
    'Seeded AI score based on CV and role matching',
    a.id
FROM applications a
WHERE NOT EXISTS (
    SELECT 1
    FROM ai_scores s
    WHERE s.application_id = a.id
);

INSERT INTO interviews (starts_at, ends_at, calendar_event_id, meeting_link, notes, application_id, candidate_id, hr_id)
SELECT
    NOW() + (ROW_NUMBER() OVER (ORDER BY a.id) || ' days')::interval,
    NOW() + ((ROW_NUMBER() OVER (ORDER BY a.id) || ' days')::interval) + interval '1 hour',
    format('seed_event_%s', a.id),
    format('https://meet.example.com/seed-%s', a.id),
    'Auto-seeded interview slot',
    a.id,
    a.candidate_id,
    j.created_by_id
FROM applications a
JOIN jobs j ON j.id = a.job_id
WHERE a.status = 'accepted'
  AND NOT EXISTS (
      SELECT 1
      FROM interviews i
      WHERE i.application_id = a.id
  )
LIMIT 12;

COMMIT;
