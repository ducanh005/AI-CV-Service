CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    website VARCHAR(255),
    description TEXT,
    location VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name);
CREATE INDEX IF NOT EXISTS idx_companies_deleted_at ON companies(deleted_at);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(120) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    avatar_url VARCHAR(255),
    date_of_birth DATE,
    phone VARCHAR(20),
    address VARCHAR(255),
    gender VARCHAR(20),
    education VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    role_id INT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    company_id INT REFERENCES companies(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);
CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_users_deleted_at ON users(deleted_at);

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    required_skills JSONB NOT NULL DEFAULT '[]'::jsonb,
    salary_min INT,
    salary_max INT,
    location VARCHAR(255),
    company_id INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_by_id INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_company_id ON jobs(company_id);
CREATE INDEX IF NOT EXISTS idx_jobs_deleted_at ON jobs(deleted_at);
CREATE INDEX IF NOT EXISTS idx_jobs_required_skills_gin ON jobs USING GIN(required_skills);

CREATE TABLE IF NOT EXISTS cvs (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    extracted_skills JSONB,
    extracted_experience JSONB,
    extracted_education JSONB,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_cvs_user_id ON cvs(user_id);

CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    notes TEXT,
    job_id INT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    candidate_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cv_id INT REFERENCES cvs(id) ON DELETE SET NULL,
    reviewed_by INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_job_candidate_application UNIQUE (job_id, candidate_id)
);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_candidate_id ON applications(candidate_id);
CREATE INDEX IF NOT EXISTS idx_applications_reviewed_by ON applications(reviewed_by);

CREATE TABLE IF NOT EXISTS ai_scores (
    id SERIAL PRIMARY KEY,
    score FLOAT NOT NULL,
    reasoning TEXT,
    application_id INT NOT NULL UNIQUE REFERENCES applications(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_ai_scores_score ON ai_scores(score);

CREATE TABLE IF NOT EXISTS interviews (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL DEFAULT 'Interview',
    starts_at TIMESTAMPTZ NOT NULL,
    ends_at TIMESTAMPTZ NOT NULL,
    interview_mode VARCHAR(20) NOT NULL DEFAULT 'online',
    location VARCHAR(255),
    notes TEXT,
    result_status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    calendar_event_id VARCHAR(255),
    calendar_url VARCHAR(500),
    meeting_link VARCHAR(255),
    application_id INT NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    candidate_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    hr_id INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_interviews_application_id ON interviews(application_id);
CREATE INDEX IF NOT EXISTS idx_interviews_candidate_id ON interviews(candidate_id);
CREATE INDEX IF NOT EXISTS idx_interviews_hr_id ON interviews(hr_id);
CREATE INDEX IF NOT EXISTS idx_interviews_calendar_event_id ON interviews(calendar_event_id);

CREATE TABLE IF NOT EXISTS token_blacklist (
    id SERIAL PRIMARY KEY,
    jti VARCHAR(64) NOT NULL UNIQUE,
    token_type VARCHAR(20) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_token_blacklist_jti ON token_blacklist(jti);

ALTER TABLE interviews
ADD COLUMN IF NOT EXISTS title VARCHAR(255) NOT NULL DEFAULT 'Interview',
ADD COLUMN IF NOT EXISTS interview_mode VARCHAR(20) NOT NULL DEFAULT 'online',
ADD COLUMN IF NOT EXISTS location VARCHAR(255),
ADD COLUMN IF NOT EXISTS result_status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
ADD COLUMN IF NOT EXISTS calendar_url VARCHAR(500);

UPDATE interviews
SET title = 'Interview'
WHERE title IS NULL;

CREATE INDEX IF NOT EXISTS ix_interviews_interview_mode ON interviews (interview_mode);
CREATE INDEX IF NOT EXISTS ix_interviews_result_status ON interviews (result_status);

-- =============================================
-- Departments & Employees
-- =============================================
CREATE TABLE IF NOT EXISTS departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    company_id INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    manager_id INT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_departments_company_id ON departments(company_id);
CREATE INDEX IF NOT EXISTS idx_departments_name ON departments(name);
CREATE INDEX IF NOT EXISTS idx_departments_deleted_at ON departments(deleted_at);

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    employee_code VARCHAR(50) NOT NULL UNIQUE,
    position VARCHAR(150) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    contract_type VARCHAR(20) NOT NULL DEFAULT 'permanent',
    start_date DATE NOT NULL,
    end_date DATE,
    identity_number VARCHAR(20),
    notes TEXT,
    user_id INT NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    department_id INT NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    company_id INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_employees_employee_code ON employees(employee_code);
CREATE INDEX IF NOT EXISTS idx_employees_user_id ON employees(user_id);
CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_employees_company_id ON employees(company_id);
CREATE INDEX IF NOT EXISTS idx_employees_status ON employees(status);
CREATE INDEX IF NOT EXISTS idx_employees_deleted_at ON employees(deleted_at);

-- =============================================
-- Onboarding
-- =============================================
CREATE TABLE IF NOT EXISTS onboarding_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    company_id INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_onboarding_templates_company_id ON onboarding_templates(company_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_templates_deleted_at ON onboarding_templates(deleted_at);

CREATE TABLE IF NOT EXISTS onboarding_tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    "order" INT NOT NULL DEFAULT 0,
    template_id INT NOT NULL REFERENCES onboarding_templates(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_onboarding_tasks_template_id ON onboarding_tasks(template_id);

CREATE TABLE IF NOT EXISTS onboarding_assignments (
    id SERIAL PRIMARY KEY,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started',
    due_date DATE,
    completed_at TIMESTAMPTZ,
    notes TEXT,
    employee_id INT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    template_id INT NOT NULL REFERENCES onboarding_templates(id) ON DELETE RESTRICT,
    assigned_by_id INT REFERENCES users(id) ON DELETE SET NULL,
    company_id INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_onboarding_assignments_employee_id ON onboarding_assignments(employee_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_assignments_template_id ON onboarding_assignments(template_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_assignments_company_id ON onboarding_assignments(company_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_assignments_status ON onboarding_assignments(status);

CREATE TABLE IF NOT EXISTS onboarding_task_progress (
    id SERIAL PRIMARY KEY,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    note TEXT,
    assignment_id INT NOT NULL REFERENCES onboarding_assignments(id) ON DELETE CASCADE,
    task_id INT NOT NULL REFERENCES onboarding_tasks(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_onboarding_task_progress_assignment_id ON onboarding_task_progress(assignment_id);
CREATE INDEX IF NOT EXISTS idx_onboarding_task_progress_task_id ON onboarding_task_progress(task_id);

-- =============================================
-- Attendance (Chấm công)
-- =============================================
CREATE TABLE IF NOT EXISTS attendances (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    check_in TIME,
    check_out TIME,
    status VARCHAR(20) NOT NULL DEFAULT 'present',
    work_hours FLOAT,
    notes TEXT,
    employee_id INT NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    company_id INT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_attendance_employee_date UNIQUE (employee_id, date)
);
CREATE INDEX IF NOT EXISTS idx_attendances_employee_id ON attendances(employee_id);
CREATE INDEX IF NOT EXISTS idx_attendances_company_id ON attendances(company_id);
CREATE INDEX IF NOT EXISTS idx_attendances_date ON attendances(date);
CREATE INDEX IF NOT EXISTS idx_attendances_status ON attendances(status);

