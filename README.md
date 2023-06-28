ExtendedBOLDQC PDF Reports
==========================
ExtQC Report allows you to save a PDF of ExtendedBOLDQC results and 
a PDF of the corresponding XNAT MR Session screen.

## Installation
Just use pip

```bash
pip install --upgrade pip
pip install git+https://github.com/harvard-nrg/extqc-report.git
```

### Playwright
ExtQC Report uses
[Playwright](https://playwright.dev/python/docs/library)
browser automation to do most of the work. However, in order to use Playwright, 
you need to run the following command to install a web browser backend

> **Note** 
> At this time, `chromium` is the only browser that supports saving web pages in PDF.

```bash
playwright install chromium
```

## Usage
The main command line tool is `extqc_report.py`

```bash
extqc_report.py -a xnatastic -l MRSESSION --scans 1
```

This command will output two PDF files, one of the ExtendedBOLDQC results, and 
the other a snapshot of the MR Session page.

For more options, run

```bash
extqc_report.py --help
```

## Customizations
The ExtendedBOLDQC PDF is not a simple snapshot of the ExtendedBOLDQC XNAT 
screen. The layout is defined using a
[Jinja](https://jinja.palletsprojects.com/)
templated HTML file. You can find the default template
[here](https://github.com/harvard-nrg/extqc-report/blob/main/extqcreport/templates/extqc_report.html).

You are free to copy this template, customize it, and pass in your customized 
template using the `extqc_report.py --template` argument. You can even embed 
JavaScript!

