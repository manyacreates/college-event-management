def test_student_can_register(client):
    response = client.post("/api/auth/register", json={
        "name": "Manya Sharma",
        "email": "manya@example.com",
        "password": "password123",
        "role": "student"
    })

    assert response.status_code == 201
    assert response.get_json() == {
        "success": True,
        "message": "Registration successful"
    }