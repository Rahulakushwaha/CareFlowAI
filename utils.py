import io, re, pandas as pd

def safe_text(value):
    return "" if value is None else str(value)

def validate_inquiry(name,email,message):
    if not safe_text(name).strip(): return "Please enter a patient name."
    if not safe_text(message).strip(): return "Please enter an inquiry message."
    email=safe_text(email).strip()
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$",email):
        return "Please enter a valid email address or leave the field blank."
    if len(name)>120: return "Patient name must be 120 characters or fewer."
    if len(message)>5000: return "Inquiry message must be 5,000 characters or fewer."
    return None

def export_csv(records):
    df=pd.DataFrame(records)
    # Prevent spreadsheet formula execution when opening exported text in spreadsheet software.
    for col in df.select_dtypes(include=["object"]).columns:
        df[col]=df[col].map(lambda x: "'"+x if isinstance(x,str) and x.startswith(("=","+","-","@")) else x)
    buffer=io.StringIO()
    df.to_csv(buffer,index=False)
    return buffer.getvalue()
