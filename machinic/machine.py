# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2017, Galen Curwen-McAdams

import argparse
import sys
import os
import stat
from ruamel.yaml import YAML
import pathlib
import textwrap
import jinja2
import glob
#env var for nomad path?
import local_tools
import uuid
from logzero import logger
#external .hcl files do not take tags
#TODO add granularity to start stop scripts
#stop.sh <-- stops all
#stop.sh ap <-- stops service ap
#start.sh and stop.sh in directory?
#gitignore for generated files & .jobs

def status(machine_file='machine.yaml'):
    #how to call nonlocally?
    #should have same configuration on all nodes...
    #store name in tags
    #machine,machine_name
    import consul
    c = consul.Consul()
    current = c.agent.services()
    active_machines = {}
    for k,v in current.items():
        if 'machine' in v['Tags']:
            for tag in v['Tags']:
                if tag != "machine":
                    if not tag in active_machines:
                        active_machines[tag] = []
                    active_machines[tag].append(v['Service'])

    #list all yamls?
    # print("Machine\t\tStatus\t\tPath")
    # for f in glob.glob("*"):
    #     if os.path.isdir(f):
    #         if os.path.isfile(os.path.join(f,machine_file)):
    #             print(f+"\t"+"available"+"\t"+os.path.abspath(f))
    # print()
    print("Machine\t\tComponents")
    for k,v in active_machines.items():
        print(k+"\t"+'\n\t\t'.join(v))        

def list_to_file(name,list_name,path,list_items):
    file = os.path.join(path,"{}-{}.txt".format(list_name,name))
    logger.info("writing {} to {}".format(list_name,file))
    with open(file,'w+') as f:
        for r in list_items:
            f.write("{}\n".format(r))

def start_machine(name,clear_before_start,machine_file='machine.yaml'):

    if os.path.isdir(name):
        if os.path.isfile(os.path.join(name,machine_file)):
            doc = pathlib.Path(os.path.join(name,machine_file))
            yaml=YAML(typ='safe')
            machine_outline = yaml.load(doc)
            logger.info("loaded yaml: {}".format(machine_outline))
            machine_path = name
    elif os.path.isfile(machine_file):
        logger.info("{} found".format(machine_file))
        doc = pathlib.Path(machine_file)
        yaml=YAML(typ='safe')
        machine_outline = yaml.load(doc)
        logger.info("loaded yaml: {}".format(machine_outline))
        machine_path = os.path.dirname(machine_file)
    else:
        logger.info("returning",machine_file)
        return
    try:
        #import routeling
        #import pipeling
        if clear_before_start is True:
            #routeling.remove_routes()
            #pipeling.remove_pipes(name="*")
            #do via script
            pass
        logger.info("Routes:")
        try:
            for route in machine_outline['routes']:
            #     routeling.add_route(route)
                logger.info(route)
            list_to_file(name,"routes",os.path.abspath(machine_path),machine_outline['routes'])
        except TypeError:
            pass

        logger.info("Pipes:")
        try:
            for pipe in machine_outline['pipes']:
            #     pipeling.add_pipe(pipe)
                logger.info(pipe)
            list_to_file(name,"pipes",os.path.abspath(machine_path),machine_outline['pipes'])
        except TypeError:
            pass

        logger.info("Rules:")
        try:
            for rule in machine_outline['rules']:
                logger.info(rule)
            list_to_file(name,"rules",os.path.abspath(machine_path),machine_outline['rules'])
        except TypeError:
            pass

    except Exception as ex:
        logger.warn(ex)
    generate_control_scripts(os.path.abspath(machine_path),machine_outline['includes'],machine_outline['set'],name)

def generate_control_scripts(path,files,states,machine_name):
    #check for name collisions
    #if collision append -1,2etc..
    #difficult, may not want always want duplicates
    #filename:multiple|single
    #hash wrapped contents?
    #zerorpc in tags
    template_vars = {}

    template_vars['machine_path'] = path
    template_vars['states'] = states
    if not template_vars['machine_path'].endswith("/"):
        template_vars['machine_path']+="/"

    #assume that both are in same location as machine.py
    template_vars['job_path'] = os.path.abspath(os.path.dirname(sys.argv[0])) 
    template_vars['core_path'] = os.path.abspath(os.path.dirname(sys.argv[0]))
    # for path in ['job_path','core_path']:
    #     if not template_vars[path].endswith("/"):
    #         template_vars[path]+="/"

    template_vars['prefix'] = "zerorpc"
    named_files = []
    make_executable = []
    #connector wrapped .py
    #unwrapped .py
    #.hcl
    for file in files:
        #serve with zerorpc
        rpc = True
        #--host --port supplied by nomad
        default_connectivity = True
        args = []
        location = False
        for filename,params in file.items():
            if filename.endswith(".hcl"):
                rpc = False
            try:
                if params['rpc'] is False:
                    rpc = False
            except Exception as ex:
                pass

            try:
                if params['args']:
                    args = params['args']
            except Exception as ex:
                pass

            try:
                if params['location']:
                    location = params['location']
            except Exception as ex:
                location = False

            try:
                if params['connect_args'] is False:
                    default_connectivity = False

                if params['duplicates'] is True:
                    job_name = os.path.splitext(os.path.basename(filename))[0]
                    job_name+="-"+str(uuid.uuid4())[:8]
                    #this will fail due to incorrect arguments?
                    named_files.append((filename,job_name,rpc,args))
            except Exception as ex:
                try:
                    job_name = params['name']
                except Exception as ex:
                    job_name = os.path.splitext(os.path.basename(filename))[0]
                named_files.append((filename,job_name,rpc,args,default_connectivity,location))

    template_vars['files'] = named_files
    template_vars['machine_name'] = machine_name

    #--command $CORE_PATH"connector.py" --args "server --service-file ${MACHINE_PATH}"{{ f }}" --checks gphoto2
    #python3 ${JOB_PATH}jobs.py run --name {{prefix}}-{{job}} --command $MACHINE_PATH"{{ f }}"

    #TODO 
    #add check for arg
    #./stop.sh foo 
    #would stop job foo only
    #if [[ -z $1 && -z $2 ]]; then

    start_template = textwrap.dedent('''
    #!/bin/bash
    ### THIS FILE IS AUTOMATICALLY GENERATED BY machine.py ###

    MACHINE_PATH="{{machine_path}}"
    JOB_PATH="{{job_path}}/"
    CORE_PATH="{{core_path}}/"
        
    # prepare machine environment
    #(check & install if necessary)
    
    # add flag --no-env
    ./environment.sh

    {% for f,job,rpc,args,default_connectivity,location in files -%}
    {%- if rpc == True and not f.endswith(".hcl") -%}
    python3 ${JOB_PATH}jobs.py run --name {{prefix}}-{{job}} --tags machine {{machine_name}} --command $CORE_PATH"connector.py" --args "server --service-file {% if location == False %}${MACHINE_PATH}{%elif location == "path" %}{% else %}{{location}}{%- endif -%}
{{ f }}" {% if default_connectivity == False %} --no-default-args {% endif %}
    {%- elif rpc == False and not f.endswith(".hcl") -%}
    python3 ${JOB_PATH}jobs.py run --name {{job}} --tags machine {{machine_name}} --command "{% if location == False %}${MACHINE_PATH}{%- elif location == "path" -%}{%- else -%}{{location}}{%- endif -%}
{{ f }}" --args "{% for arg in args %} {{ arg }} {% endfor %}" {% if default_connectivity == False %} --no-default-args {% endif %} 
    {% else %}
    python3 ${JOB_PATH}jobs.py run --name {{job}} --tags machine {{machine_name}} --existing-file {{ f }} {% if default_connectivity == False %} --no-default-args {%- endif -%} 
    {% endif %}
    {% endfor %}
    python3 ${JOB_PATH}routes-add --file ${MACHINE_PATH}routes-{{machine_name}}.txt
    python3 ${JOB_PATH}pipes-add --file ${MACHINE_PATH}pipes-{{machine_name}}.txt
    python3 ${JOB_PATH}rules-add --file ${MACHINE_PATH}rules-{{machine_name}}.txt
    {% if states is not none -%}
    {% for k,v in states[0].items() -%}
    {% for state in v -%}
    {% for sk,sv in state.items() %}
    python3 ${JOB_PATH}state set {{k}} {{sk}} {{sv}}
    {%- endfor -%}
    {%- endfor -%}
    {%- endfor -%}
    {%- endif %}

    ''')
#'set': [{'BAR': [{'marker:capture1': -1}, {'marker:capture2': 0}]}],

    stop_template = textwrap.dedent('''
    #!/bin/bash
    ### THIS FILE IS AUTOMATICALLY GENERATED BY machine.py ###
    MACHINE_PATH="{{machine_path}}/"
    JOB_PATH="{{job_path}}/"

    {%- for f,job,rpc,args,default_connectivity,location in files -%}
    {% if rpc == True %}
    python3 ${JOB_PATH}jobs.py stop --name {{prefix}}-{{job}}
    {% else %}
    python3 ${JOB_PATH}jobs.py stop --name {{job}}
    {% endif %}
    {%- endfor -%}
    python3 ${JOB_PATH}routes-remove --file ${MACHINE_PATH}routes-{{machine_name}}.txt
    python3 ${JOB_PATH}pipes-remove --file ${MACHINE_PATH}pipes-{{machine_name}}.txt
    python3 ${JOB_PATH}rules-remove --file ${MACHINE_PATH}rules-{{machine_name}}.txt

    ''')

    restart_template = textwrap.dedent('''
    #!/bin/bash
    ### THIS FILE IS AUTOMATICALLY GENERATED BY machine.py ###

    ./stop.sh
    ./start.sh

    ''')
    for script_name,script_template in [('start.sh',start_template),('stop.sh',stop_template),('restart.sh',restart_template)]:
        logger.warn(template_vars)
        print("writing {}".format((os.path.join(path,script_name))))
        logger.info("writing {}".format((os.path.join(path,script_name))))
        with open(os.path.join(path,script_name),'w+') as f:
            f.write(jinja2.Environment().from_string(script_template).render(template_vars))

        make_executable.append(script_name)

    for f,job,_,_,_,_ in named_files:
        make_executable.append(f)

    for file in make_executable:
        file = os.path.join(path,file)
        #logger.debug("chmod 0111 {}".format(file))
        #TODO check for hasbang at start

        try:
            st = os.stat(file)
            os.chmod(file, st.st_mode | 0o111)
        except Exception as ex:
            logger.warn(ex)

        shebang_line = ""
        try:
            with open(file, 'r') as f:
                shebang_line = f.readline()
            if "#!/usr/bin/python3" in shebang_line:
                logger.info("shebang found")
            else:
                logger.warn("no shebang on first line of {}".format(file))
                logger.warn("#!/usr/bin/python3 is not on first line. Nomad will not run file")
        except Exception as ex:
            logger.warn("could not check shebang for {}".format(f))
            logger.warn(ex)
def snapshot_to_machine(name):
    #machine.py snapshot --name new_machine
        #get running jobs from nomad
    #jobs
    #routes
    routes = routeling.get_routes("*")
    #pipes
    pipes = pipeling.get_pipes("*")

    #rules
    #write file....
    print(routes,pipes)

def named(args,required):
    for r in required:
        if r in args:
            return True
    return False
    
def main(argv):
    """
    example:
        python3 machine.py run --name foo --path ../machine_foo/machine.yaml

    """
    parser = argparse.ArgumentParser(description=main.__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("action", help="run|status|snapshot", choices=['run','status','snapshot'])
    parser.add_argument("--name",required=named(argv,['run','stop','help']) , help="machine name")
    parser.add_argument("--path",required=named(argv,['run','stop','help']), help="machine file path",default=None)
    args = parser.parse_args()
    pre_clear = False

    if args.action == 'run':
        start_machine(args.name,pre_clear,args.path)
    elif args.action == 'status':
        status()
    elif args.action == 'snapshot':
        snapshot_to_machine(args.name)

if __name__ == "__main__":
    main(sys.argv)
