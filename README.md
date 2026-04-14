# AI-Based Skill Gap Analyzer with TNP Admin Control Panel

This project now includes a fully functional Admin Control Panel for TNP Head usage without rebuilding the existing system. The implementation extends the existing FastAPI architecture and keeps compatibility with existing modules.

## Updated Architecture

### Existing modules preserved
- Auth and student profile
- Resume parser and resume generator
- Assessment engine (batch + adaptive)
- Skill gap analyzer
- Roadmap generator
- Progress tracker

### New admin extension
- backend/admin/admin_routes.py
- backend/admin/admin_controller.py
- backend/admin/admin_service.py

### Central control data source
Admin actions now update shared runtime state in backend/services/data_store.py:
- company_role_requirements
- career_paths
- question_bank
- admin_custom_tests and assignments
- admin_role_roadmap_overrides
- admin_student_roadmap_assignments

This ensures admin changes directly influence:
- Assessment engine behavior
- Skill gap analysis logic
- Roadmap generation
- Resume generation focus skills

## Admin Features Implemented

1. Admin authentication
- Secure admin login with token session
- Admin-only APIs protected using bearer token middleware
- Default demo credentials:
	- username: tnp_admin
	- password: admin123
	- override via env: ADMIN_USERNAME, ADMIN_PASSWORD

2. Student identity and login
- Each student account stores a unique college `student_id`
- `student_id` is also mapped as `username` for login
- Duplicate prevention on both `email` and `student_id`
- Personalization mappings (tests, roadmap assignments) are tied to student identity
- Login/user/session auth data is persisted in `backend/services/auth_data.json` and survives server restart
- Users can set or update `target_role` later from dashboard if skipped at registration

3. Role and company management
- Create, update, delete role requirements per company
- Skill requirement format:
	- skill
	- weight (High, Medium, Low)
	- minimum_score_required
- Auto-sync to career_paths for backward compatibility

4. Question bank control
- Add, update, delete questions
- Supports MCQ, MULTI, CASE
- Difficulty and weight controls
- Optional custom test creation and assignment to role or student
- Assessment start honors assigned custom tests first

5. Roadmap control and override
- Role-level roadmap override
- Student-level custom roadmap assignment
- Admin-defined custom steps and resources
- Optional role override per student

6. Student analytics dashboard
- Per student:
	- resume skills
	- assessment scores
	- skill gaps
	- roadmap progress
	- readiness score
- Aggregated:
	- average performance
	- most common weak skills
	- role-wise readiness

7. Intervention system
- Assign targeted roadmap
- Assign targeted test
- Recommend specific resources

## New Admin APIs

### Mandatory endpoints
- POST /api/admin/login
- POST /api/admin/role
- PUT /api/admin/role/{id}
- DELETE /api/admin/role/{id}
- POST /api/admin/question
- GET /api/admin/students
- POST /api/admin/assign-roadmap

### Additional admin endpoints
- GET /api/admin/snapshot
- PUT /api/admin/question/{question_id}
- DELETE /api/admin/question/{question_id}
- GET /api/admin/questions
- POST /api/admin/tests
- POST /api/admin/roadmap-override

All admin endpoints except login require:
- Authorization: Bearer <admin_token>

## Frontend Admin Panel

New page:
- frontend/admin.html

Panels included:
1. Role Management Panel
2. Question Bank Panel
3. Student Analytics Dashboard
4. Roadmap Editor
5. Custom Assignment Panel

UI capabilities:
- Forms + tables for CRUD
- Role-wise readiness chart using Chart.js
- Auth-gated admin workspace

Access routes:
- /admin
- /admin.html

## Sample Data Payloads

### Create role
POST /api/admin/role

{
	"company": "Infosys",
	"role": "Data Analyst",
	"skills": [
		{"skill": "SQL", "weight": "High", "minimum_score_required": 75},
		{"skill": "Python", "weight": "Medium", "minimum_score_required": 65},
		{"skill": "Statistics", "weight": "Medium", "minimum_score_required": 60}
	]
}

### Add question
POST /api/admin/question

{
	"question": "Which SQL clause filters grouped data?",
	"type": "MCQ",
	"skill": "SQL",
	"difficulty": "Easy",
	"weight": 3,
	"options": ["WHERE", "GROUP BY", "HAVING", "ORDER BY"],
	"correct_answers": [2]
}

### Assign custom roadmap
POST /api/admin/assign-roadmap

{
	"student_id": "<student-id>",
	"role": "Data Analyst",
	"timeline_weeks": 6,
	"custom_steps": [
		{
			"skill": "SQL",
			"priority": "High",
			"start_from_stage": "beginner",
			"stages": [
				{"stage": "beginner", "title": "SQL Basics", "time_weeks": 2, "tasks": ["Practice 50 queries"]}
			],
			"total_weeks": 2
		}
	],
	"custom_resources": [
		{"title": "SQL Full Course", "url": "https://www.youtube.com/results?search_query=sql+full+course"}
	],
	"recommended_resources": [
		{"title": "LeetCode SQL 50", "url": "https://leetcode.com/studyplan/top-sql-50/"}
	]
}

## Integration Instructions

1. Install dependencies

pip install -r requirements.txt

2. Start backend

uvicorn backend.api.main:app --reload

3. Open app pages
- Main app: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin
- Swagger docs: http://127.0.0.1:8000/docs

4. Test consistency flow
1. Login as admin
2. Create or update role skill requirements
3. Add or update question bank entries
4. Assign custom tests or roadmap to a student
5. Run student assessment and skill gap endpoints
6. Verify roadmap and resume outputs reflect admin changes

## Notes for Students

- Architecture is modular and extensible.
- No paid services are required.
- Data remains in-memory for MVP simplicity.
- Restart resets runtime state (users, sessions, admin edits).