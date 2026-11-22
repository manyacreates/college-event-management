def test_login_page_loads(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert "Welcome back" in response.get_data(as_text=True)


def test_register_page_loads(client):
    response = client.get("/register")

    assert response.status_code == 200
    assert "Create your account" in response.get_data(as_text=True)


def test_admin_login_page_loads(client):
    response = client.get("/admin/login")

    assert response.status_code == 200
    assert "Admin" in response.get_data(as_text=True)


def test_register_page_has_name_email_password_fields(client):
    html = client.get("/register").get_data(as_text=True)

    assert 'name="name"' in html
    assert 'name="email"' in html
    assert 'name="password"' in html


def test_login_page_has_no_name_field(client):
    html = client.get("/login").get_data(as_text=True)

    assert 'name="name"' not in html
    assert 'name="email"' in html


def test_auth_script_is_served(client):
    assert client.get("/static/js/auth.js").status_code == 200