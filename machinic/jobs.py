# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import jinja2
import consul
import subprocess
import requests
import json
import textwrap
import argparse
import sys
import os
import logging
import logzero
from logzero import logger
import logzero
logzero.logfile("/tmp/{}.log".format(os.path.basename(sys.argv[0])))
#add logs option calling stderr
#./nomad logs -stderr -address=http://192.168.0.155:4646 343beff9

#nomad does not accept underscores in job names

def nomad_address():
    c = consul.Consul()
    nomad_details = c.agent.services()['_nomad-server-nomad-http']
    nomad_port = nomad_details['Port']
    nomad_ip = nomad_details['Address']
    return nomad_ip,nomad_port

def get_scheduler_jobs(nomad_location=None):
    nomad_ip,nomad_port = nomad_address()
    print(nomad_ip,nomad_port)
    print(subprocess.check_output('{} status -address=http://{}:{}'.format(nomad_location,nomad_ip,nomad_port).split()).decode())


def get_scheduler_services():
    c = consul.Consul()
    services = {k:v for (k,v) in c.agent.services().items() if k.startswith("_nomad")}
    logger.info("retrieving service details from consul")
    print("{}\t\t{}\t\t{}".format("Service","Ip","Port"))
    for k in services.keys():
        print("{}\t{}\t{}".format(services[k]['Service'].ljust(15),services[k]['Address'],services[k]['Port']))

def get_job_raw(name,path=".jobs",file=None):
    if not os.path.exists(os.path.abspath(path)):
        os.makedirs(path)

    nomad_ip,nomad_port = nomad_address()
    gs = 'http://{}:{}/v1/job/{}'.format(nomad_ip,nomad_port,name)
    r = requests.get(gs)
    logger.info(r.text)

    if file is not False:
        if file is None:
            fname = '{}.json'.format(name)
        else:
            fname = file
        with open(os.path.join(path,fname),'w+') as f:
            f.write(json.dumps(r.json(), indent=4))

    return r.json()

def stop_job(name,purge=False,nomad_location=None):
    logger.info("stopping {}".format(name))

    nomad_ip,nomad_port = nomad_address()
    if purge:
        purge = '-purge'
    else:
        purge=''

    print(subprocess.check_output('{} stop -address=http://{}:{} {} {}'.format(nomad_location,nomad_ip,nomad_port,purge,name).split()).decode())

def run_job(name,command,args,path=".jobs",tags=None,external_file=None,checks=None,scheduler_wireup_host_port=None):
    #pass in checks as list of textfiles with path
    args = list(filter(None, args)) 

    if external_file is not None and not os.path.isfile(external_file):
        logger.error("no file to load: {}".format(external_file))
        return

    if not os.path.exists(os.path.abspath(path)):
        logger.info("creating: {}".format(os.path.abspath(path)))
        os.makedirs(path)

    logger.info("job path: {}".format(os.path.abspath(path)))

    logger.info("preparing to run job: {}".format(name))
    nomad_ip,nomad_port = nomad_address()
    logger.info("nomad address: http://{}:{}".format(nomad_ip,nomad_port))

    config = {}
    config['name'] = name
    if tags:
        config['tags'] = tags

    config['args'] = args
    config['command'] = command
    config['scheduler_wireup_host_port'] = scheduler_wireup_host_port

    #TODO modularize checks
    check_gphoto2 = textwrap.dedent('''
        check {
          type = "script"
          #id = "interfering-gphoto"
          name = "Interfering os gphoto processes"
          command = "/usr/local/bin/check_gphoto"
          interval = "10s"
          timeout = "1s"
          }
        ''')

    if checks == 'gphoto2':
        config['checks'] = [check_gphoto2]

    job_template = textwrap.dedent('''
    job "{{ name }}" {
      datacenters = ["dc1"]
      
      group "example" {
      count = 1
        task "{{ name }}" {
          driver = "raw_exec"
          service {
            name = "{{ name }}"
            tags = [{% for tag in tags %} "{{ tag }}",{% endfor %}]
            port = "service_port"
            {% for check in checks %}
            {{ check }}
            {% endfor %}

            }

          config {
            command = "{{ command }}"
            args = [
              {% for arg in args -%}
              "{{arg}}"{{ "," }}
              {%- endfor %}
              {% if scheduler_wireup_host_port != true %}
              "--host","${NOMAD_IP_service_port}",
              "--port","${NOMAD_PORT_service_port}",
              {% endif%}
            ]
          }

          resources {
            network {
              #mbits = 10
              port "service_port" {}
            }
          }
        }
      }
    }
    ''')

    logger.info("rendering hcl from args dict: {}".format(config))
    job_hcl = jinja2.Environment().from_string(job_template).render(config)
    
    #do not overwrite if using external kwarg
    #in case of reload
    if not external_file:
        logger.info("writing job .hcl file: {}".format(os.path.join(path,'{}.hcl'.format(name))))
        with open(os.path.join(path,'{}.hcl'.format(name)),'w+') as f:
            f.write(job_hcl)

        logger.info("converting .hcl to .json for submission")
        job_json = subprocess.check_output('{} run -output {}.hcl'.format(nomad,os.path.join(path,name)).split()) 
        job_json=job_json.decode()

        logger.info("loading json")
        j = json.loads(job_json)

    if external_file:
        #external_file = os.path.join(path,external_file)
        logger.info("loading job file: {}".format(external_file))

        if external_file.endswith('.hcl'):
            logger.info("converting .hcl to .json for submission")
            job_json = subprocess.check_output('{} run -output {}'.format(nomad,external_file).split()) 
            job_json=job_json.decode()
            logger.info("loading json")
            j = json.loads(job_json)

        elif external_file.endswith('.json'):
            logger.info("loading json from file {}".format(external_file))
            with open(external_file) as json_data:
                j = json.load(json_data)

    job_submit_endpoint = 'http://{}:{}/v1/job/{}'.format(nomad_ip,nomad_port,name)
    logger.info("submitting(PUT) job json to: {}".format(job_submit_endpoint))
    r = requests.put(job_submit_endpoint, json=j)
    logger.info("{}".format(r))
    logger.info(j)

    json_file = '{}.json'.format(name)

    logger.info("writing job .json file: {}".format(os.path.join(path,json_file)))
    with open(os.path.join(path,json_file),'w+') as f:
        f.write(json.dumps(j, indent=4))

def job_name_needed(args):
    if 'status' in args or 'status-raw' in args:
        return False
    else:
        return True

def command_needed(argv):
    #parser.add_argument("--command",required='run' in argv , help="full path of command to call")
    logger.info("args: {}".format(argv))
    job_name = ""
    for i,arg in enumerate(argv):
        if arg == "--name":
            try:
                job_name = argv[i+1]
            except:
                return True
    job = os.path.join(os.path.expanduser('~/.local/jobs'),job_name)
    #sys.exit()
    if 'run' in argv and '--existing-file' in argv:
        return False
    elif 'run' in argv and os.path.isfile(job):
        return True
    elif 'run' in argv:
        return True
    else:
        return False

def main(argv):
    """Nomad jobs cli. Allow creation of jobs 
    via templates. 
    """
    log_levels = {
        "info":logging.INFO,
        "debug":logging.DEBUG,
        "warn":logging.WARN,
        "error":logging.ERROR,
    }

    jobs_path = os.path.expanduser('~/.local/jobs')

    tutorial_string = """
    Job files will be stored at(override with -j):
        {}

    Actions:

        jobs.py [action]

            status:       prints scheduler jobs
            status-raw:   prints scheduler jobs with ip address and port(useful for debugging)

        jobs.py [action] --name [job_name]

            run:          run job with args from --command
            stop:         stop job
            run-file:     run a job from file
            reload:       reload a job
            purge:        stop job and delete job file
            get:          get raw job json from scheduler

    """.format(jobs_path)

    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser = argparse.ArgumentParser(epilog=tutorial_string,formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("action", help="stop|run|run-file|reload|status|status-raw|get|purge", choices=['run','run-file','stop','reload','status','status-raw','get','purge'])
    parser.add_argument("--name",required=job_name_needed(argv) , help="job name/id")
    parser.add_argument("--command",required=command_needed(argv), help="full path of command to call",default=None)
    parser.add_argument("--args", help="Args,kwargs and flags to be used by command. A string separated by space, quoted at beginning and end to avoid parsing. Example: \"--foo bar.baz --another-flag\" ",default=[])
    parser.add_argument("--nomad-location", help="nomad binary location",default="nomad")
    parser.add_argument("--existing-file", help="",default=False)
    parser.add_argument("-c","--checks",help="checks ie gphoto2")
    parser.add_argument("--log-level", choices=['debug','info','warn','error'],default="info",help="checks ie gphoto2")
    parser.add_argument("-j","--jobs-path", help="directory to story job output and generated files default: ~/.local/jobs" ,default=jobs_path)
    parser.add_argument("-t","--tags", help="store in tags",nargs='+',default=None)
    parser.add_argument("--scheduler-wireup", action='store_true',default=False)

    #TODO tutorial string on error with no arguments
    args = parser.parse_args()  

    logzero.loglevel(log_levels[args.log_level])
    
    try:
        args.args=args.args.strip().split(" ")
    except AttributeError as ex:
        pass

    if args.action == 'run':
        run_job(args.name,args.command,args.args,path=args.jobs_path,tags=args.tags,checks=args.checks,external_file=args.existing_file,scheduler_wireup_host_port=args.scheduler_wireup)
    elif args.action =='stop':
        stop_job(args.name,False,args.nomad_location)
    elif args.action == 'reload':
        reload_file = '{}.json'.format(args.name)
        stop_job(args.name,False,args.nomad_location)
        run_job(args.name,'',[],external_file=reload_file)
    elif args.action == 'run-file':
        run_job(args.name,'',args.args,external_file=args.existing_file)
    elif args.action =='purge':
        stop_job(args.name,True,args.nomad_location)
    elif args.action == 'status':
        get_scheduler_jobs(args.nomad_location)
    elif args.action == 'status-raw':
        get_scheduler_services()
    elif args.action == 'get':
        get_job_raw(args.name,path=args.jobs_path)

if __name__ == "__main__":
    main(sys.argv)


