import os

__dirname__ = os.path.dirname(__file__)

def extqc_report():
    html = os.path.join(
        __dirname__,
        'extqc_report.html'
    )
    return html

def boldqc_report():
    html = os.path.join(
        __dirname__,
        'boldqc_report.html'
    )
    return html
