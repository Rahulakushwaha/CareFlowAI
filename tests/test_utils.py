from utils import validate_inquiry, export_csv

def test_validation():
    assert validate_inquiry("","x@y.com","Message")
    assert validate_inquiry("A","invalid","Message")
    assert validate_inquiry("A","a@b.com","Message") is None

def test_csv_formula_safety():
    csv=export_csv([{"patient_name":"=HYPERLINK('x')","status":"Open"}])
    assert "'=HYPERLINK" in csv
