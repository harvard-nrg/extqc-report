#!/n/sw/ncf/venv/extqc_report/main/bin/python3

import os
import sys
import json
import yaxil
import asyncio
import logging
import requests
import importlib
import requests_cache
import argparse as ap
import tempfile as tf
import jinja2 as jinja
import subprocess as sp
import extqcreport.css as css
import extqcreport.browser as browser
import extqcreport.templates as templates

logger = logging.getLogger(os.path.basename(__file__))
logging.basicConfig(level=logging.INFO)

name = os.path.basename(__file__)

async def main():
    parser = ap.ArgumentParser(description='ExtendedBOLDQC report generator')
    parser.add_argument('--alias', '-a', required=True, 
        help='XNAT deployment alias')
    parser.add_argument('--label', '-l', required=True, 
        help='MR Session label')
    parser.add_argument('--project', '-p',
        help='MR Session project')
    parser.add_argument('--scan', '-s', nargs='+', default=[], required=True, 
        help="Scans")
    parser.add_argument('--template', "-t", default=templates.boldqc_report(),
        help="Jinja2 template to generate BOLDQC PDF")
    parser.add_argument('--orientation', choices=['portrait', 'landscape'],
        default='landscape', help='Orient report in portrait or landscape')
    parser.add_argument('--stylesheet', '-S', default=css.extqc_report(),
        help='CSS Stylesheet')
    parser.add_argument('--preserve-html', action='store_true', 
        help='Preserve the rendered HTML template')
    parser.add_argument('--output-dir', default='.', 
        help='Output PDF file directory')
    parser.add_argument('--cache', action='store_true',
        help='Cache XNAT responses to speed up debugging a little')
    parser.add_argument('--boldqc-version', choices=['default', 'legacy'],
        default='default', help='Request BOLDQC data from specific version')
    parser.add_argument('-v', '--verbose', action='store_true',
        help='Enable verbose mode')
    args = parser.parse_args()

    if args.boldqc_version == 'legacy':
        logger.info('loading legacy extendedboldqc assessment api and html template')
        neuroinfo = importlib.import_module('yaxil.assessments.neuroinfo.legacy')
        args.template = templates.extqc_report()
    else:
        neuroinfo = importlib.import_module('yaxil.assessments.neuroinfo')

    if args.verbose:
        logging.getLogger('extqc_report.py').setLevel(logging.DEBUG)
        logging.getLogger('extqcreport.browser').setLevel(logging.DEBUG)

    # need an output directory for multiple scans
    if len(args.scan) > 1 and not args.output_dir:
        parser.print_usage()
        print(f'{name}: error: please specify --output-dir when specifying multiple --scans')
        sys.exit(1)
    
    add_to_no_proxy(['127.0.0.1', 'localhost'])

    # setup xnat requests cache
    if args.cache:    
        requests_cache.install_cache(
            os.path.expanduser('~/.requests_xnat')
        )

    # get the eqc experiment id and file urls
    auth = yaxil.auth(args.alias)
    experiments = list(yaxil.experiments(auth, args.label, args.project))
    if not experiments:
        logger.info(f'no experiments found for {args.label}')
        sys.exit(0)    
    experiment = experiments[0]

    # generate a PDF of the MR Session report page
    args.output_dir = os.path.expanduser(args.output_dir)
    baseurl = auth.url.rstrip('/')
    url = f'{baseurl}/data/experiments/{experiment.id}?format=html'
    saveto = os.path.join(args.output_dir, "{0}.pdf".format(experiment.label))
    logger.info(f'rendering {saveto}')
    await browser.snapshot(
        auth,
        url,
        saveto,
        scale=.8
    )

    # iterate over scans and snapshot extendedboldqc pages
    for scanid in args.scan:
        logger.info(f'processing scan {scanid}')
        # get scan details
        scans = yaxil.scans(
            auth,
            project=experiment.project,
            label=experiment.label,
            scan_ids=[scanid]
        )
        scan = next(scans)
        # query assessor and get file urls
        assessors = neuroinfo.boldqc(
            auth,
            project=experiment.project,
            label=experiment.label,
            scan_ids=[scanid]
        )
        assessor = next(assessors)
        files = file_urls(auth.url, assessor)

        # build arguments for populating jinja template
        values = {
            'url': auth.url,
            'experiment': experiment,
            'scan': ap.Namespace(**scan),
            'assessor': ap.Namespace(**assessor),
            'stylesheet': f'file://{args.stylesheet}',
            'files': files
        }

        # read in the jinja template
        args.template = os.path.expanduser(args.template)
        with open(args.template, 'r') as fo:
            logger.info('reading template file')
            template = jinja.Template(fo.read())
        logger.info('rendering template')
        rendered = template.render(**values)
 
        # write the rendered html to a temporary file
        with tf.NamedTemporaryFile(
            dir=args.output_dir,
            prefix=f'{assessor["id"]}_',
            suffix='.html',
            delete=False) as fo: 
            fo.write(rendered.encode())

        # generate a PDF of the rendered html
        saveto = os.path.join(args.output_dir, f'{assessor["id"]}.pdf')
        logger.info(f'rendering {saveto}')
        await browser.snapshot(
            auth,
            f'file://{fo.name}',
            saveto,
            landscape=True,
            scale=1.5
        )
        
        # remove populated template
        if not args.preserve_html:
            os.remove(fo.name)

def file_urls(baseurl, assessor):
    baseurl = baseurl.rstrip('/')
    urls = dict()
    for key,value in iter(assessor['files'].items()):
        key = key.lower().replace(' ', '_')
        path = value['URI'].lstrip('/')
        url = f'{baseurl}/{path}'
        urls[key] = url
    return urls

def add_to_no_proxy(entries):
    no_proxy = os.environ.get('no_proxy', '').strip()
    if not no_proxy:
        no_proxy = set()
    else:
        no_proxy = set(no_proxy.split(','))
    no_proxy = no_proxy | set(entries)
    os.environ['no_proxy'] = ','.join(no_proxy)
    logger.debug(f'env no_proxy={os.environ["no_proxy"]}')
    logger.debug(f'env http_proxy={os.environ["http_proxy"]}')
    logger.debug(f'env https_proxy={os.environ["https_proxy"]}')

if __name__ == '__main__':
    asyncio.run(main())

