"""
End-to-end smoke test for all 8 SkillForge AI modules.
Run: .venv\Scripts\python.exe tmp_verify.py
"""
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)

def test_all():
    # 1) Register
    r = client.post('/api/register', json={
        'name': 'Rahul Sharma', 'email': 'rahul@demo.com',
        'password': 'abc123', 'target_role': 'Data Analyst',
        'current_skills': ['Excel'], 'learning_goals': []
    })
    assert r.status_code == 200, f'Register failed: {r.text[:300]}'
    token = r.json()['access_token']
    h = {'Authorization': f'Bearer {token}'}
    print('1. Register: OK')

    # 2) Start assessment
    r2 = client.get('/api/assessment/start', headers=h)
    assert r2.status_code == 200, f'Start failed: {r2.text[:300]}'
    qs = r2.json()['questions']
    skills_in_qs = list(set(q['skill'] for q in qs))
    print(f'2. Assessment Start: OK ({len(qs)} questions, skills: {skills_in_qs})')

    # 3) Submit legacy scores
    r3 = client.post('/api/assessment/submit', json={
        'scores': {'SQL': 45, 'Excel': 80, 'Python': 30, 'Data Visualization': 55, 'Statistics': 25}
    }, headers=h)
    assert r3.status_code == 200, f'Submit failed: {r3.text[:300]}'
    assert r3.json()['scores']['SQL'] == 45
    print('3. Assessment Submit: OK, SQL score =', r3.json()['scores']['SQL'])

    # 4) Get result
    r4 = client.get('/api/assessment/result', headers=h)
    assert r4.status_code == 200, f'Result failed: {r4.text[:300]}'
    assert r4.json()['scores']['SQL'] == 45
    print('4. Assessment Result: OK, skill_scores =', list(r4.json()['skill_scores'].keys()))

    # 5) Skill gap analysis with explainability
    r5 = client.get('/api/skill-gap/analyze', headers=h)
    assert r5.status_code == 200, f'Gap failed: {r5.text[:300]}'
    body = r5.json()
    assert body['target_role'] == 'Data Analyst'
    assert 'readiness_percent' in body
    g = body['skills'][0]
    assert 'reason' in g, f'Missing reason: {g}'
    assert 'evidence' in g, f'Missing evidence: {g}'
    assert 'priority' in g, f'Missing priority: {g}'
    print(f'5. Skill Gap: OK, readiness={body["readiness_percent"]}%')
    print(f'   Gap[0]: skill={g["skill"]}, priority={g["priority"]}, reason={g["reason"][:50]}...')

    # 6) Role mapper
    r6 = client.get('/api/roles')
    assert r6.status_code == 200
    companies = r6.json()['companies']
    print(f'6. Companies: OK ({len(companies)} companies: {companies[:3]}...)')

    r6b = client.get('/api/roles/TCS')
    assert r6b.status_code == 200
    print('6b. TCS roles:', r6b.json()['roles'])

    r6c = client.get('/api/roles/TCS/Data%20Analyst')
    assert r6c.status_code == 200
    print('6c. TCS/Data Analyst skills:', list(r6c.json()['skills'].keys()))

    # 7) Roadmap
    r7 = client.get('/api/roadmap', headers=h)
    assert r7.status_code == 200, f'Roadmap failed: {r7.text[:300]}'
    rm = r7.json()
    print(f'7. Roadmap: OK ({len(rm["roadmap"])} skill paths, ~{rm["estimated_total_weeks"]} weeks total)')
    if rm['roadmap']:
        s = rm['roadmap'][0]
        print(f'   First: {s["skill"]} ({s["priority"]}) | stages: {[st["stage"] for st in s["stages"]]}')
        if s['stages']:
            res = s['stages'][0].get('resources', [])
            print(f'   Resources[0]: {res[0]["name"] if res else "N/A"}')

    # 8) Progress tracking
    r8 = client.post('/api/progress/complete', json={'skill': 'SQL', 'stage': 'beginner'}, headers=h)
    assert r8.status_code == 200, f'Progress failed: {r8.text[:300]}'
    print('8. Progress: OK -', r8.json()['result'])

    r8b = client.get('/api/progress', headers=h)
    assert r8b.status_code == 200
    metrics = r8b.json()['metrics']
    print(f'   Metrics: completion={metrics["overall_completion_pct"]}%, gap_reduction={metrics["gap_reduction_pct"]}%')

    print('\n' + '='*50)
    print('ALL 8 MODULES VERIFIED SUCCESSFULLY')
    print('='*50)

if __name__ == '__main__':
    test_all()
