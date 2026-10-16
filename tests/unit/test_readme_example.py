def test_readme_import():
    from anchor import guard

    @guard(domain="finance")
    def f(x):
        return x

    assert f({"qty": 1}) == {"qty": 1}
