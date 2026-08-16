from app.validators.budget_normalizer import normalize_budget_value


def test_plain_number():
    assert normalize_budget_value(20000) == 20000
    assert normalize_budget_value(20000.4) == 20000


def test_numeric_strings():
    assert normalize_budget_value("20000") == 20000
    assert normalize_budget_value("20000.00") == 20000


def test_k_shorthand():
    assert normalize_budget_value("20k") == 20000
    assert normalize_budget_value("20K") == 20000
    assert normalize_budget_value("20 k") == 20000
    assert normalize_budget_value("1.5k") == 1500


def test_rupee_formatting():
    assert normalize_budget_value("₹20,000") == 20000
    assert normalize_budget_value("20000 rupees") == 20000
    assert normalize_budget_value("Rs. 20000") == 20000
    assert normalize_budget_value("INR 20000") == 20000


def test_lakh_before_k():
    assert normalize_budget_value("1.5 lakh") == 150000
    assert normalize_budget_value("1.5l") == 150000
    assert normalize_budget_value("2 lakhs") == 200000


def test_unparseable():
    assert normalize_budget_value("idk maybe 20k?") is None
    assert normalize_budget_value("around twenty thousand") is None
    assert normalize_budget_value("") is None
    assert normalize_budget_value(0) is None
    assert normalize_budget_value(-5) is None
