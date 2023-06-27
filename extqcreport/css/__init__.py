import os

__dir__ = os.path.dirname(__file__)

def extqc_report():
    css = os.path.join(
        __dir__,
        'extqc_report.css'
    )
    return css
