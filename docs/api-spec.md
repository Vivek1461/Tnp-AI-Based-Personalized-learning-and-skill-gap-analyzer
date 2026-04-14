# API Specification (MVP)

Base URL: `http://127.0.0.1:8000`

## Feature 1: User Authentication and Profile

### POST `/api/register`
Register a user and return an access token.

Request body:

```json
{
	"name": "Alice",
	"email": "alice@example.com",
	"password": "secure123",
	"education_level": "Undergraduate",
	"current_skills": ["Python", "Basic Math"],
	"target_role": "AI Engineer",
	"learning_goals": ["Become ML Engineer"]
}
```

### POST `/api/login`
Login and return bearer token.

### GET `/api/profile`
Return current user profile.

Headers:

`Authorization: Bearer <token>`

### PUT `/api/update-profile`
Update selected profile fields.

### GET `/api/career-paths`
Return available career roles and required skill levels.

## Feature 2: Skill Assessment Engine

### GET `/api/assessment/start`
Start assessment for user's selected target role and fetch role-based questions.

### POST `/api/assessment/submit`
Submit skill scores (0-100).

Request body:

```json
{
	"scores": {
		"Python": 80,
		"Statistics": 25,
		"Linear Algebra": 15,
		"Machine Learning": 10
	}
}
```

### GET `/api/assessment/result`
Get latest submitted scores.

## Feature 3: AI Skill Gap Analyzer

### GET `/api/skill-gap/analyze`
Compare assessment scores against required role skill levels and compute readiness.

Sample response:

```json
{
	"target_role": "AI Engineer",
	"readiness_percent": 35,
	"summary": "You are 35% ready for AI Engineer role",
	"skills": [
		{
			"skill": "Python",
			"required_level": 85,
			"current_level": 80,
			"gap": 5,
			"status": "Good"
		}
	]
}
```

