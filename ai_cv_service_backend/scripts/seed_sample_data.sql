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

-- Dedicated demo account with richer data for realistic user experience
INSERT INTO users (email, full_name, hashed_password, is_active, role_id, company_id)
SELECT
    'vuducanh039@gmail.com',
    'Vu Duc Anh',
    '$2b$12$5p7sbXi5S8RQ770N37KwkOTdVDCItoB.wn6B.qvZ60kNu2Ztt2jj2',
    TRUE,
    r.id,
    NULL
FROM roles r
WHERE r.name = 'user'
ON CONFLICT (email) DO NOTHING;

UPDATE users
SET
    full_name = 'Vu Duc Anh',
    date_of_birth = DATE '1998-09-03',
    phone = '0909123456',
    address = 'Cau Giay, Ha Noi',
    gender = 'male',
    education = 'Bachelor of Information Technology - PTIT',
    role_id = (SELECT id FROM roles WHERE name = 'hr'),
    company_id = (SELECT id FROM companies WHERE name = 'TechNova Solutions')
WHERE email = 'vuducanh039@gmail.com';

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

INSERT INTO jobs (title, description, status, required_skills, salary_min, salary_max, location, company_id, created_by_id)
SELECT
    seed.title,
    seed.description,
    seed.status,
    seed.required_skills::jsonb,
    seed.salary_min,
    seed.salary_max,
    seed.location,
    c.id,
    hr.id
FROM (
    VALUES
        ('TechNova Solutions', 'AI Engineer', 'open', 'Research and deploy ML models for candidate matching and scoring workflows.', '["python","pytorch","mlops","fastapi"]', 2200, 3400, 'Ha Noi', 'hr1@example.com'),
        ('TechNova Solutions', 'Technical Recruiter', 'open', 'Drive hiring pipeline for engineering and product teams.', '["recruitment","interview","communication","linkedin"]', 900, 1500, 'Ha Noi', 'hr1@example.com'),
        ('DigitalWave Labs', 'Business Analyst', 'open', 'Analyze HR SaaS metrics and align requirements with product roadmap.', '["analysis","sql","communication","product"]', 1300, 2100, 'Ho Chi Minh City', 'hr2@example.com'),
        ('DigitalWave Labs', 'Mobile Developer (React Native)', 'closed', 'Build and maintain candidate and recruiter mobile applications.', '["react-native","javascript","api","mobile"]', 1600, 2500, 'Ho Chi Minh City', 'hr2@example.com'),
        ('SkyBridge Systems', 'Site Reliability Engineer', 'open', 'Improve reliability, observability and incident response process.', '["sre","kubernetes","prometheus","linux"]', 2100, 3200, 'Da Nang', 'hr3@example.com'),
        ('SkyBridge Systems', 'Security Engineer', 'closed', 'Harden platform security and support audit/compliance requirements.', '["security","cloud","devsecops","siem"]', 2300, 3500, 'Da Nang', 'hr3@example.com')
) AS seed(company_name, title, status, description, required_skills, salary_min, salary_max, location, hr_email)
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

INSERT INTO cvs (file_name, file_path, mime_type, extracted_skills, extracted_experience, extracted_education, user_id)
SELECT
    seed.file_name,
    seed.file_path,
    seed.mime_type,
    seed.skills::jsonb,
    seed.experience::jsonb,
    seed.education::jsonb,
    u.id
FROM (
    VALUES
        (
            'vuducanh_backend_2026.pdf',
            'uploads/cvs/vuducanh_backend_2026.pdf',
            'application/pdf',
            '["python","fastapi","postgresql","redis","docker"]',
            '["4 years backend development","Built high-traffic recruitment APIs"]',
            '["Bachelor in Information Technology"]'
        ),
        (
            'vuducanh_fullstack_portfolio.pdf',
            'uploads/cvs/vuducanh_fullstack_portfolio.pdf',
            'application/pdf',
            '["react","typescript","nodejs","tailwindcss","rest-api"]',
            '["3 years fullstack web development","Led dashboard revamp for HR platform"]',
            '["Certified Frontend Professional"]'
        ),
        (
            'vuducanh_data_engineering_cv.pdf',
            'uploads/cvs/vuducanh_data_engineering_cv.pdf',
            'application/pdf',
            '["sql","airflow","dbt","python","data-warehouse"]',
            '["2 years data engineering","Designed ETL pipelines for recruitment analytics"]',
            '["Data Engineering Nanodegree"]'
        )
) AS seed(file_name, file_path, mime_type, skills, experience, education)
JOIN users u ON u.email = 'vuducanh039@gmail.com'
WHERE NOT EXISTS (
    SELECT 1
    FROM cvs c
    WHERE c.user_id = u.id
      AND c.file_name = seed.file_name
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

INSERT INTO applications (status, notes, job_id, candidate_id, cv_id, reviewed_by)
SELECT
    seed.status,
    seed.notes,
    j.id,
    u.id,
    cv.id,
    CASE WHEN seed.status IN ('accepted', 'rejected') THEN j.created_by_id ELSE NULL END
FROM (
    VALUES
        ('Senior Backend Engineer', 'accepted', 'Hồ sơ tốt, đã qua vòng CV. [MAIL_SENT]'),
        ('Frontend Engineer', 'pending', 'Đang đợi phản hồi từ team tuyển dụng.'),
        ('DevOps Engineer', 'rejected', 'Kinh nghiệm phù hợp một phần, chưa khớp yêu cầu cloud ở vòng này. [MAIL_SENT]')
) AS seed(job_title, status, notes)
JOIN users u ON u.email = 'vuducanh039@gmail.com'
JOIN jobs j ON j.title = seed.job_title AND j.deleted_at IS NULL
JOIN LATERAL (
    SELECT c.id
    FROM cvs c
    WHERE c.user_id = u.id
    ORDER BY c.created_at DESC
    LIMIT 1
) AS cv ON TRUE
ON CONFLICT (job_id, candidate_id)
DO UPDATE
SET
    status = EXCLUDED.status,
    notes = EXCLUDED.notes,
    cv_id = EXCLUDED.cv_id,
    reviewed_by = EXCLUDED.reviewed_by,
    updated_at = NOW();

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

INSERT INTO ai_scores (score, reasoning, application_id)
SELECT
    CASE
        WHEN a.status = 'accepted' THEN 92.40
        WHEN a.status = 'pending' THEN 81.15
        ELSE 68.75
    END,
    CASE
        WHEN a.status = 'accepted' THEN 'Strong backend depth and relevant project impact for the role'
        WHEN a.status = 'pending' THEN 'Good technical baseline; waiting for recruiter and hiring manager alignment'
        ELSE 'Solid profile but role requires stronger cloud-native production exposure'
    END,
    a.id
FROM applications a
JOIN users u ON u.id = a.candidate_id
WHERE u.email = 'vuducanh039@gmail.com'
ON CONFLICT (application_id)
DO UPDATE
SET
    score = EXCLUDED.score,
    reasoning = EXCLUDED.reasoning,
    updated_at = NOW();

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

INSERT INTO interviews (
    title,
    starts_at,
    ends_at,
    interview_mode,
    location,
    result_status,
    calendar_event_id,
    calendar_url,
    meeting_link,
    notes,
    application_id,
    candidate_id,
    hr_id
)
SELECT
    'Technical Interview - Senior Backend Engineer',
    NOW() + INTERVAL '3 days',
    NOW() + INTERVAL '3 days 1 hour',
    'online',
    NULL,
    'scheduled',
    format('vuducanh_interview_%s', a.id),
    'https://calendar.google.com/calendar/u/0/r/week',
    'https://meet.google.com/vda-tech-2026',
    'Phỏng vấn kỹ thuật vòng 2 với team backend và HR.',
    a.id,
    a.candidate_id,
    j.created_by_id
FROM applications a
JOIN users u ON u.id = a.candidate_id
JOIN jobs j ON j.id = a.job_id
WHERE u.email = 'vuducanh039@gmail.com'
  AND j.title = 'Senior Backend Engineer'
  AND a.status = 'accepted'
  AND NOT EXISTS (
      SELECT 1
      FROM interviews i
      WHERE i.application_id = a.id
  );

-- =============================================
-- Seed Departments
-- =============================================
INSERT INTO departments (name, description, company_id, manager_id)
SELECT seed.name, seed.description, c.id, mgr.id
FROM (
    VALUES
        ('TechNova Solutions', 'Phòng Công nghệ',      'Phát triển phần mềm, hạ tầng và AI',           'hr1@example.com'),
        ('TechNova Solutions', 'Phòng Nhân sự',         'Tuyển dụng, đào tạo và quản lý nhân viên',     'hr1@example.com'),
        ('TechNova Solutions', 'Phòng Marketing',       'Truyền thông, thương hiệu và quảng cáo',       NULL),
        ('TechNova Solutions', 'Phòng Kinh doanh',      'Phát triển khách hàng và doanh thu',            NULL),
        ('DigitalWave Labs',   'Phòng Sản phẩm',        'Quản lý sản phẩm và trải nghiệm người dùng',  'hr2@example.com'),
        ('DigitalWave Labs',   'Phòng Thiết kế',        'UI/UX và thiết kế đồ họa',                      NULL),
        ('DigitalWave Labs',   'Phòng Công nghệ',       'Frontend, backend và mobile development',       'hr2@example.com'),
        ('SkyBridge Systems',  'Phòng Hạ tầng',         'Cloud, DevOps và bảo mật hệ thống',            'hr3@example.com'),
        ('SkyBridge Systems',  'Phòng QA',              'Kiểm thử và đảm bảo chất lượng phần mềm',      NULL),
        ('SkyBridge Systems',  'Phòng Nhân sự',         'Quản lý nhân sự và hành chính',                 'hr3@example.com')
) AS seed(company_name, name, description, mgr_email)
JOIN companies c ON c.name = seed.company_name
LEFT JOIN users mgr ON mgr.email = seed.mgr_email
WHERE NOT EXISTS (
    SELECT 1 FROM departments d
    WHERE d.name = seed.name AND d.company_id = c.id AND d.deleted_at IS NULL
);

-- =============================================
-- Seed Employees (from existing candidate users)
-- =============================================
INSERT INTO employees (employee_code, position, status, contract_type, start_date, identity_number, user_id, department_id, company_id)
SELECT
    seed.emp_code,
    seed.position,
    seed.status,
    seed.contract_type,
    seed.start_date::date,
    seed.id_number,
    u.id,
    d.id,
    c.id
FROM (
    VALUES
        ('candidate01@example.com', 'TechNova Solutions', 'Phòng Công nghệ',  'NV001', 'Senior Backend Engineer',  'active',   'permanent',  '2022-03-15', '001099012345'),
        ('candidate02@example.com', 'TechNova Solutions', 'Phòng Công nghệ',  'NV002', 'Junior Backend Developer', 'active',   'probation',  '2025-11-01', '001099012346'),
        ('candidate03@example.com', 'TechNova Solutions', 'Phòng Nhân sự',    'NV003', 'Chuyên viên tuyển dụng',   'active',   'permanent',  '2023-06-10', '001099012347'),
        ('candidate04@example.com', 'TechNova Solutions', 'Phòng Marketing',  'NV004', 'Content Marketing',        'active',   'permanent',  '2023-01-05', '001099012348'),
        ('candidate05@example.com', 'TechNova Solutions', 'Phòng Kinh doanh', 'NV005', 'Sales Executive',          'active',   'temporary',  '2024-07-20', '001099012349'),
        ('candidate06@example.com', 'TechNova Solutions', 'Phòng Công nghệ',  'NV006', 'Data Engineer',            'on_leave', 'permanent',  '2022-09-01', '001099012350'),
        ('candidate07@example.com', 'DigitalWave Labs',   'Phòng Sản phẩm',   'NV007', 'Product Manager',          'active',   'permanent',  '2021-04-15', '001099012351'),
        ('candidate08@example.com', 'DigitalWave Labs',   'Phòng Thiết kế',   'NV008', 'UI/UX Designer',           'active',   'permanent',  '2022-08-20', '001099012352'),
        ('candidate09@example.com', 'DigitalWave Labs',   'Phòng Công nghệ',  'NV009', 'Frontend Developer',       'active',   'permanent',  '2023-02-10', '001099012353'),
        ('candidate10@example.com', 'DigitalWave Labs',   'Phòng Thiết kế',   'NV010', 'Graphic Designer',         'resigned', 'permanent',  '2021-11-01', '001099012354'),
        ('candidate11@example.com', 'SkyBridge Systems',  'Phòng Hạ tầng',    'NV011', 'DevOps Engineer',          'active',   'permanent',  '2022-05-10', '001099012355'),
        ('candidate12@example.com', 'SkyBridge Systems',  'Phòng QA',         'NV012', 'QA Engineer',              'active',   'permanent',  '2023-03-01', '001099012356'),
        ('candidate13@example.com', 'SkyBridge Systems',  'Phòng Hạ tầng',    'NV013', 'Cloud Architect',          'active',   'permanent',  '2021-01-15', '001099012357'),
        ('candidate14@example.com', 'SkyBridge Systems',  'Phòng Nhân sự',    'NV014', 'HR Coordinator',           'active',   'temporary',  '2024-09-01', '001099012358'),
        ('candidate15@example.com', 'SkyBridge Systems',  'Phòng QA',         'NV015', 'Automation Tester',        'on_leave', 'permanent',  '2022-12-01', '001099012359'),
        ('candidate16@example.com', 'TechNova Solutions', 'Phòng Công nghệ',  'NV016', 'Fullstack Developer',      'active',   'permanent',  '2024-01-08', '001099012360'),
        ('candidate17@example.com', 'TechNova Solutions', 'Phòng Nhân sự',    'NV017', 'Talent Acquisition',       'active',   'probation',  '2026-02-01', '001099012361'),
        ('candidate18@example.com', 'DigitalWave Labs',   'Phòng Công nghệ',  'NV018', 'QA Automation Engineer',   'active',   'permanent',  '2023-10-02', '001099012362'),
        ('candidate19@example.com', 'DigitalWave Labs',   'Phòng Sản phẩm',   'NV019', 'Product Owner',            'active',   'permanent',  '2022-06-20', '001099012363'),
        ('candidate20@example.com', 'SkyBridge Systems',  'Phòng Hạ tầng',    'NV020', 'Platform Engineer',        'active',   'permanent',  '2024-04-15', '001099012364'),
        ('candidate21@example.com', 'SkyBridge Systems',  'Phòng QA',         'NV021', 'Manual Tester',            'active',   'temporary',  '2025-07-01', '001099012365'),
        ('candidate22@example.com', 'SkyBridge Systems',  'Phòng Nhân sự',    'NV022', 'HR Specialist',            'active',   'probation',  '2026-01-15', '001099012366')
) AS seed(user_email, company_name, dept_name, emp_code, position, status, contract_type, start_date, id_number)
JOIN users u ON u.email = seed.user_email
JOIN companies c ON c.name = seed.company_name
JOIN departments d ON d.name = seed.dept_name AND d.company_id = c.id AND d.deleted_at IS NULL
WHERE NOT EXISTS (
    SELECT 1 FROM employees e WHERE e.employee_code = seed.emp_code AND e.deleted_at IS NULL
);

-- =============================================
-- Onboarding Templates & Tasks
-- =============================================

-- Template 1: Standard Onboarding (TechNova)
INSERT INTO onboarding_templates (name, description, company_id)
SELECT 'Onboarding Nhân viên mới', 'Quy trình tiếp nhận nhân viên mới tiêu chuẩn', c.id
FROM companies c WHERE c.name = 'TechNova Solutions'
AND NOT EXISTS (
    SELECT 1 FROM onboarding_templates t WHERE t.name = 'Onboarding Nhân viên mới'
      AND t.company_id = c.id AND t.deleted_at IS NULL
);

INSERT INTO onboarding_tasks (title, description, priority, "order", template_id)
SELECT seed.title, seed.description, seed.priority, seed.ord, t.id
FROM (VALUES
    ('Chuẩn bị bàn làm việc & thiết bị', 'Laptop, màn hình, bàn phím, chuột, tai nghe', 'high', 1),
    ('Tạo tài khoản email & công cụ nội bộ', 'Gmail, Slack, Jira, GitLab', 'high', 2),
    ('Gửi tài liệu nội quy công ty', 'Gồm handbook, chính sách bảo mật, quy định chấm công', 'medium', 3),
    ('Giới thiệu team & mentor', 'Sắp xếp buổi gặp mặt với đội nhóm và người hướng dẫn', 'high', 4),
    ('Đào tạo an toàn thông tin', 'Hoàn thành khóa học bảo mật nội bộ', 'medium', 5),
    ('Thiết lập VPN & môi trường dev', 'Cài đặt VPN, Docker, IDE, clone repository', 'high', 6),
    ('Review code conventions & workflow', 'Branching strategy, code review, CI/CD pipeline', 'medium', 7),
    ('Hoàn thành hồ sơ nhân sự', 'Nộp CMND/CCCD, ảnh 3x4, sổ hộ khẩu, bằng cấp', 'high', 8),
    ('Đăng ký BHXH & thuế TNCN', 'Cung cấp mã số thuế, đăng ký bảo hiểm', 'medium', 9),
    ('Đánh giá sau tuần đầu tiên', 'Mentor đánh giá và phản hồi sau 1 tuần', 'low', 10)
) AS seed(title, description, priority, ord)
CROSS JOIN onboarding_templates t
WHERE t.name = 'Onboarding Nhân viên mới'
  AND t.company_id = (SELECT id FROM companies WHERE name = 'TechNova Solutions')
  AND t.deleted_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM onboarding_tasks ot WHERE ot.template_id = t.id AND ot.title = seed.title
  );

-- Template 4: Cloud/Infra onboarding (SkyBridge)
INSERT INTO onboarding_templates (name, description, company_id)
SELECT 'Onboarding Cloud Ops', 'Quy trình onboarding cho đội hạ tầng và vận hành', c.id
FROM companies c WHERE c.name = 'SkyBridge Systems'
AND NOT EXISTS (
    SELECT 1 FROM onboarding_templates t WHERE t.name = 'Onboarding Cloud Ops'
      AND t.company_id = c.id AND t.deleted_at IS NULL
);

INSERT INTO onboarding_tasks (title, description, priority, "order", template_id)
SELECT seed.title, seed.description, seed.priority, seed.ord, t.id
FROM (VALUES
    ('Cấp quyền truy cập AWS/GCP', 'IAM account, MFA, phân quyền theo role', 'high', 1),
    ('Thiết lập monitoring stack', 'Cấu hình Prometheus, Grafana, Alertmanager', 'high', 2),
    ('Làm quen runbook & incident flow', 'Đọc tài liệu xử lý sự cố và escalation matrix', 'medium', 3),
    ('Diễn tập xử lý sự cố giả lập', 'Thực hành sự cố production với mentor', 'high', 4),
    ('Bàn giao checklist bảo mật', 'Review chính sách secret management và logging', 'medium', 5)
) AS seed(title, description, priority, ord)
CROSS JOIN onboarding_templates t
WHERE t.name = 'Onboarding Cloud Ops'
  AND t.company_id = (SELECT id FROM companies WHERE name = 'SkyBridge Systems')
  AND t.deleted_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM onboarding_tasks ot WHERE ot.template_id = t.id AND ot.title = seed.title
  );

-- Template 2: IT Onboarding (TechNova)
INSERT INTO onboarding_templates (name, description, company_id)
SELECT 'Onboarding IT/Dev', 'Quy trình dành riêng cho developer & kỹ sư phần mềm', c.id
FROM companies c WHERE c.name = 'TechNova Solutions'
AND NOT EXISTS (
    SELECT 1 FROM onboarding_templates t WHERE t.name = 'Onboarding IT/Dev'
      AND t.company_id = c.id AND t.deleted_at IS NULL
);

INSERT INTO onboarding_tasks (title, description, priority, "order", template_id)
SELECT seed.title, seed.description, seed.priority, seed.ord, t.id
FROM (VALUES
    ('Cấp quyền truy cập GitLab/GitHub', 'Thêm vào organization và các repo liên quan', 'high', 1),
    ('Cài đặt môi trường phát triển', 'IDE, Docker, Node.js, Python, database local', 'high', 2),
    ('Chạy project local lần đầu', 'Clone repo, cài dependencies, chạy migration, seed data', 'high', 3),
    ('Đọc tài liệu kiến trúc hệ thống', 'System design docs, API docs, database schema', 'medium', 4),
    ('Pair programming với senior', 'Ít nhất 2 buổi pair programming trong tuần đầu', 'medium', 5),
    ('Hoàn thành task onboarding đầu tiên', 'Fix 1 bug hoặc implement 1 feature nhỏ', 'low', 6)
) AS seed(title, description, priority, ord)
CROSS JOIN onboarding_templates t
WHERE t.name = 'Onboarding IT/Dev'
  AND t.company_id = (SELECT id FROM companies WHERE name = 'TechNova Solutions')
  AND t.deleted_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM onboarding_tasks ot WHERE ot.template_id = t.id AND ot.title = seed.title
  );

-- Template 3: Generic onboarding (DigitalWave)
INSERT INTO onboarding_templates (name, description, company_id)
SELECT 'Chương trình Hội nhập', 'Quy trình onboarding cơ bản cho nhân viên DigitalWave', c.id
FROM companies c WHERE c.name = 'DigitalWave Labs'
AND NOT EXISTS (
    SELECT 1 FROM onboarding_templates t WHERE t.name = 'Chương trình Hội nhập'
      AND t.company_id = c.id AND t.deleted_at IS NULL
);

INSERT INTO onboarding_tasks (title, description, priority, "order", template_id)
SELECT seed.title, seed.description, seed.priority, seed.ord, t.id
FROM (VALUES
    ('Ký hợp đồng lao động', 'Ký HĐ chính thức và các phụ lục', 'high', 1),
    ('Nhận thẻ nhân viên & vân tay chấm công', 'Đăng ký vân tay và phát thẻ từ', 'high', 2),
    ('Tham quan văn phòng', 'Tour giới thiệu các phòng ban, canteen, phòng họp', 'low', 3),
    ('Đào tạo văn hóa doanh nghiệp', 'Tham gia buổi giới thiệu về giá trị và tầm nhìn công ty', 'medium', 4),
    ('Setup email & chat nội bộ', 'Tạo tài khoản Outlook, Microsoft Teams', 'high', 5),
    ('Gặp mặt quản lý trực tiếp', 'Buổi 1-on-1 lần đầu với manager', 'medium', 6),
    ('Hoàn thành hồ sơ nhân sự', 'Nộp đầy đủ giấy tờ theo checklist HR', 'high', 7)
) AS seed(title, description, priority, ord)
CROSS JOIN onboarding_templates t
WHERE t.name = 'Chương trình Hội nhập'
  AND t.company_id = (SELECT id FROM companies WHERE name = 'DigitalWave Labs')
  AND t.deleted_at IS NULL
  AND NOT EXISTS (
      SELECT 1 FROM onboarding_tasks ot WHERE ot.template_id = t.id AND ot.title = seed.title
  );

-- =============================================
-- Onboarding Assignments (assign to some employees)
-- =============================================

-- Assign "Onboarding Nhân viên mới" to employee NV003 (new hire)
INSERT INTO onboarding_assignments (status, due_date, employee_id, template_id, assigned_by_id, company_id)
SELECT 'in_progress', CURRENT_DATE + INTERVAL '14 days',
       e.id, t.id,
    (SELECT u.id FROM users u WHERE u.email = 'hr1@example.com'),
       e.company_id
FROM employees e
JOIN onboarding_templates t ON t.name = 'Onboarding Nhân viên mới'
  AND t.company_id = e.company_id AND t.deleted_at IS NULL
WHERE e.employee_code = 'NV003' AND e.deleted_at IS NULL
AND NOT EXISTS (
    SELECT 1 FROM onboarding_assignments a
    WHERE a.employee_id = e.id AND a.template_id = t.id AND a.status != 'completed'
);

-- Create task progress for the assignment above
INSERT INTO onboarding_task_progress (is_completed, completed_at, assignment_id, task_id)
SELECT
    CASE WHEN ot."order" <= 4 THEN TRUE ELSE FALSE END,
    CASE WHEN ot."order" <= 4 THEN NOW() ELSE NULL END,
    a.id, ot.id
FROM onboarding_assignments a
JOIN onboarding_tasks ot ON ot.template_id = a.template_id
WHERE a.employee_id = (SELECT id FROM employees WHERE employee_code = 'NV003' AND deleted_at IS NULL)
  AND a.template_id = (
      SELECT id FROM onboarding_templates
      WHERE name = 'Onboarding Nhân viên mới'
        AND company_id = (SELECT id FROM companies WHERE name = 'TechNova Solutions')
        AND deleted_at IS NULL
  )
  AND NOT EXISTS (
      SELECT 1 FROM onboarding_task_progress tp WHERE tp.assignment_id = a.id AND tp.task_id = ot.id
  );

-- Assign "Onboarding IT/Dev" to employee NV005
INSERT INTO onboarding_assignments (status, due_date, employee_id, template_id, assigned_by_id, company_id)
SELECT 'not_started', CURRENT_DATE + INTERVAL '7 days',
       e.id, t.id,
    (SELECT u.id FROM users u WHERE u.email = 'hr1@example.com'),
       e.company_id
FROM employees e
JOIN onboarding_templates t ON t.name = 'Onboarding IT/Dev'
  AND t.company_id = e.company_id AND t.deleted_at IS NULL
WHERE e.employee_code = 'NV005' AND e.deleted_at IS NULL
AND NOT EXISTS (
    SELECT 1 FROM onboarding_assignments a
    WHERE a.employee_id = e.id AND a.template_id = t.id AND a.status != 'completed'
);

-- Create task progress for NV005
INSERT INTO onboarding_task_progress (is_completed, assignment_id, task_id)
SELECT FALSE, a.id, ot.id
FROM onboarding_assignments a
JOIN onboarding_tasks ot ON ot.template_id = a.template_id
WHERE a.employee_id = (SELECT id FROM employees WHERE employee_code = 'NV005' AND deleted_at IS NULL)
  AND a.template_id = (
      SELECT id FROM onboarding_templates
      WHERE name = 'Onboarding IT/Dev'
        AND company_id = (SELECT id FROM companies WHERE name = 'TechNova Solutions')
        AND deleted_at IS NULL
  )
  AND NOT EXISTS (
      SELECT 1 FROM onboarding_task_progress tp WHERE tp.assignment_id = a.id AND tp.task_id = ot.id
  );

-- Additional assignments for richer onboarding dashboard
INSERT INTO onboarding_assignments (status, due_date, employee_id, template_id, assigned_by_id, company_id)
SELECT seed.status, seed.due_date, e.id, t.id, hr.id, e.company_id
FROM (
    VALUES
        ('NV016', 'Onboarding IT/Dev', 'in_progress', CURRENT_DATE + INTERVAL '10 days', 'hr1@example.com'),
        ('NV017', 'Onboarding Nhân viên mới', 'not_started', CURRENT_DATE + INTERVAL '12 days', 'hr1@example.com'),
        ('NV018', 'Chương trình Hội nhập', 'in_progress', CURRENT_DATE + INTERVAL '9 days', 'hr2@example.com'),
        ('NV019', 'Chương trình Hội nhập', 'completed', CURRENT_DATE - INTERVAL '1 days', 'hr2@example.com'),
        ('NV020', 'Onboarding Cloud Ops', 'in_progress', CURRENT_DATE + INTERVAL '8 days', 'hr3@example.com')
) AS seed(emp_code, template_name, status, due_date, hr_email)
JOIN employees e ON e.employee_code = seed.emp_code AND e.deleted_at IS NULL
JOIN onboarding_templates t ON t.name = seed.template_name AND t.company_id = e.company_id AND t.deleted_at IS NULL
JOIN users hr ON hr.email = seed.hr_email
WHERE NOT EXISTS (
    SELECT 1 FROM onboarding_assignments a
    WHERE a.employee_id = e.id AND a.template_id = t.id AND a.status != 'completed'
);

INSERT INTO onboarding_task_progress (is_completed, completed_at, note, assignment_id, task_id)
SELECT
    CASE
        WHEN a.status = 'completed' THEN TRUE
        WHEN a.status = 'in_progress' AND ot."order" <= 3 THEN TRUE
        ELSE FALSE
    END,
    CASE
        WHEN a.status = 'completed' THEN NOW() - INTERVAL '2 hours'
        WHEN a.status = 'in_progress' AND ot."order" <= 3 THEN NOW() - INTERVAL '1 day'
        ELSE NULL
    END,
    CASE
        WHEN a.status = 'completed' THEN 'Đã hoàn thành đầy đủ checklist onboarding'
        WHEN a.status = 'in_progress' AND ot."order" <= 3 THEN 'Đã hoàn thành các bước khởi tạo ban đầu'
        ELSE NULL
    END,
    a.id,
    ot.id
FROM onboarding_assignments a
JOIN employees e ON e.id = a.employee_id
JOIN onboarding_tasks ot ON ot.template_id = a.template_id
WHERE e.employee_code IN ('NV016', 'NV017', 'NV018', 'NV019', 'NV020')
  AND NOT EXISTS (
      SELECT 1 FROM onboarding_task_progress tp WHERE tp.assignment_id = a.id AND tp.task_id = ot.id
  );

-- =============================================
-- Attendance (Chấm công) - last 5 working days for TechNova employees
-- =============================================
INSERT INTO attendances (date, check_in, check_out, status, work_hours, employee_id, company_id)
SELECT seed.att_date, seed.ci, seed.co, seed.st,
       EXTRACT(EPOCH FROM (seed.co - seed.ci)) / 3600.0,
       e.id, e.company_id
FROM (VALUES
    -- NV001
    ('NV001', CURRENT_DATE - 1, TIME '08:02', TIME '17:05', 'present'),
    ('NV001', CURRENT_DATE - 2, TIME '08:15', TIME '17:00', 'late'),
    ('NV001', CURRENT_DATE - 3, TIME '07:55', TIME '17:10', 'present'),
    ('NV001', CURRENT_DATE - 4, TIME '08:00', TIME '12:00', 'half_day'),
    ('NV001', CURRENT_DATE - 5, TIME '08:00', TIME '17:30', 'present'),
    -- NV002
    ('NV002', CURRENT_DATE - 1, TIME '08:00', TIME '17:00', 'present'),
    ('NV002', CURRENT_DATE - 2, TIME '09:10', TIME '17:00', 'late'),
    ('NV002', CURRENT_DATE - 3, NULL, NULL, 'absent'),
    ('NV002', CURRENT_DATE - 4, TIME '08:05', TIME '17:15', 'present'),
    ('NV002', CURRENT_DATE - 5, TIME '07:50', TIME '17:00', 'present'),
    -- NV003
    ('NV003', CURRENT_DATE - 1, TIME '08:00', TIME '17:00', 'present'),
    ('NV003', CURRENT_DATE - 2, TIME '08:00', TIME '17:30', 'present'),
    ('NV003', CURRENT_DATE - 3, TIME '08:30', TIME '17:00', 'late'),
    -- NV004
    ('NV004', CURRENT_DATE - 1, TIME '07:45', TIME '16:50', 'present'),
    ('NV004', CURRENT_DATE - 2, TIME '08:00', TIME '17:00', 'present'),
    -- NV005
    ('NV005', CURRENT_DATE - 1, NULL, NULL, 'absent'),
    ('NV005', CURRENT_DATE - 2, TIME '08:00', TIME '17:00', 'present')
) AS seed(emp_code, att_date, ci, co, st)
JOIN employees e ON e.employee_code = seed.emp_code AND e.deleted_at IS NULL
WHERE NOT EXISTS (
    SELECT 1 FROM attendances a WHERE a.employee_id = e.id AND a.date = seed.att_date
);

INSERT INTO attendances (date, check_in, check_out, status, work_hours, notes, employee_id, company_id)
SELECT
    seed.att_date,
    seed.ci,
    seed.co,
    seed.st,
    EXTRACT(EPOCH FROM (seed.co - seed.ci)) / 3600.0,
    seed.note,
    e.id,
    e.company_id
FROM (VALUES
    ('NV006', CURRENT_DATE - 1, TIME '08:12', TIME '17:20', 'late', 'Đi họp khách hàng buổi sáng'),
    ('NV006', CURRENT_DATE - 2, TIME '08:00', TIME '17:05', 'present', 'Làm việc bình thường'),
    ('NV007', CURRENT_DATE - 1, TIME '07:58', TIME '17:10', 'present', 'Tham gia daily đúng giờ'),
    ('NV007', CURRENT_DATE - 2, NULL, NULL, 'absent', 'Nghỉ phép cá nhân đã báo trước'),
    ('NV008', CURRENT_DATE - 1, TIME '08:45', TIME '17:15', 'late', 'Kẹt xe giờ cao điểm'),
    ('NV009', CURRENT_DATE - 1, TIME '08:03', TIME '17:30', 'present', 'Overtime hỗ trợ release'),
    ('NV010', CURRENT_DATE - 1, TIME '08:00', TIME '12:00', 'half_day', 'Làm nửa ngày do việc gia đình'),
    ('NV011', CURRENT_DATE - 1, TIME '07:40', TIME '17:50', 'present', 'On-call hạ tầng'),
    ('NV012', CURRENT_DATE - 1, TIME '08:25', TIME '17:00', 'late', 'Kiểm thử regression buổi chiều'),
    ('NV020', CURRENT_DATE - 1, TIME '08:00', TIME '17:40', 'present', 'Triển khai cải tiến CI/CD'),
    ('NV021', CURRENT_DATE - 1, NULL, NULL, 'absent', 'Nghỉ ốm có giấy xác nhận'),
    ('NV022', CURRENT_DATE - 1, TIME '08:10', TIME '17:00', 'late', 'Hỗ trợ onboarding nhân viên mới')
) AS seed(emp_code, att_date, ci, co, st, note)
JOIN employees e ON e.employee_code = seed.emp_code AND e.deleted_at IS NULL
WHERE NOT EXISTS (
    SELECT 1 FROM attendances a WHERE a.employee_id = e.id AND a.date = seed.att_date
);

-- =============================================
-- Leave Requests (Nghỉ phép)
-- =============================================
INSERT INTO leave_requests (leave_type, start_date, end_date, total_days, reason, status, approved_at, employee_id, approved_by_id, company_id)
SELECT seed.lt, seed.sd, seed.ed, seed.td, seed.reason, seed.st,
       CASE WHEN seed.st IN ('approved','rejected') THEN NOW() ELSE NULL END,
       e.id,
       CASE WHEN seed.st IN ('approved','rejected')
          THEN (SELECT u.id FROM users u WHERE u.email = 'hr1@example.com')
            ELSE NULL END,
       e.company_id
FROM (VALUES
    ('NV001', 'annual',    CURRENT_DATE + 5,  CURRENT_DATE + 7,  3, 'Nghỉ phép năm - du lịch gia đình', 'approved'),
    ('NV002', 'sick',      CURRENT_DATE - 3,  CURRENT_DATE - 3,  1, 'Ốm, cần nghỉ khám bệnh', 'approved'),
    ('NV003', 'personal',  CURRENT_DATE + 10, CURRENT_DATE + 11, 2, 'Việc cá nhân cần giải quyết', 'pending'),
    ('NV004', 'annual',    CURRENT_DATE + 14, CURRENT_DATE + 18, 5, 'Nghỉ phép dài ngày', 'pending'),
    ('NV005', 'sick',      CURRENT_DATE - 1,  CURRENT_DATE - 1,  1, 'Không khỏe', 'approved'),
    ('NV001', 'maternity', CURRENT_DATE + 30, CURRENT_DATE + 210, 180, 'Nghỉ thai sản', 'rejected'),
    ('NV006', 'annual',    CURRENT_DATE + 3,  CURRENT_DATE + 4,  2, 'Nghỉ phép cá nhân', 'pending'),
    ('NV007', 'unpaid',    CURRENT_DATE + 7,  CURRENT_DATE + 9,  3, 'Nghỉ không lương - việc gia đình', 'pending')
) AS seed(emp_code, lt, sd, ed, td, reason, st)
JOIN employees e ON e.employee_code = seed.emp_code AND e.deleted_at IS NULL
WHERE NOT EXISTS (
    SELECT 1 FROM leave_requests lr
    WHERE lr.employee_id = e.id AND lr.start_date = seed.sd AND lr.leave_type = seed.lt
);

COMMIT;
