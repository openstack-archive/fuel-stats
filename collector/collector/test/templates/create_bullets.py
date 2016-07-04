#    Copyright 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from __future__ import print_function
import getopt
import os
import sys

from requests import ActionLogRequestTemplate
from requests import InstallationRequestTemplate
from requests import OSwLRequestTemplate
from six.moves import xrange


class Settings(object):
    def __init__(self):
        self.config_file = "ammo.txt"
        self.bullets_count = 5
        self.bullets_types = ['installation', 'action-log', 'oswl-stat']
        self.host_address = '127.0.0.1'
        self.max_clusters_count = 10
        self.max_cluster_size = 100
        self.max_logs_count = 30


def parse_args(argv, settings):
    try:
        opts, args = getopt.getopt(argv, "ha:c:t:f:", ["help",
                                                       "host-address=",
                                                       "bullets-count=",
                                                       "bullets-type=",
                                                       "output-file=",
                                                       "max_clusters_count=",
                                                       "max_cluster_size=",
                                                       "max_logs_count="])
    except getopt.GetoptError as err:
        print(str(err))
        return usage()

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
        elif opt in ("-a", "host-address="):
            settings.host_address = arg
        elif opt in ("-c", "--bullets-count"):
            settings.bullets_count = int(arg)
        elif opt in ("-t", "--bullets-type"):
            types = []
            for type in arg.split(','):
                if type in settings.bullets_types:
                    types.append(type)
                else:
                    usage("ERROR! Unsupported bullet type '{0}'".format(type))
            settings.bullets_types = types
        elif opt in ("-f", "--output-file"):
            settings.config_file = arg
        elif opt == "--max_clusters_count":
            settings.max_clusters_count = int(arg)
        elif opt == "--max_cluster_size":
            settings.max_cluster_size = int(arg)
        elif opt == "--max_logs_count":
            settings.max_logs_count = int(arg)

    return settings


def usage(message=None):
    usage_text = """
    Usage: {name} [OPTIONS]
    Example: {name} --bullets-count 10 --bullets-type "installation"

    Options:
        -a, --host-address         set IP address or hostname/domain of
                                   Collector; default - {host}

        -c, --bullets-count        set number of each bullets type to
                                   generate; default value is {count}

        -t, --bullets-type         set bullets types; supported types are:
                                   {types}; by default all types are used

        -f, --output-file          set output file to save bullets;
                                   default file name is "{file}"

        -h, --help                 print this help message

    Additional options:
        --max_clusters_count       set maximum clusters number in each
                                   installation request; default - 10
        --max_cluster_size         set maximum nodes number assigned to each
                                   environment; default - 100
        --max_logs_count           set maximum count of action logs which will
                                   in one request; default - 30
    """.format(name=sys.argv[0],
               host=Settings().host_address,
               count=Settings().bullets_count,
               types=', '.join(Settings().bullets_types),
               file=Settings().config_file)
    if message:
        print('{0}'.format(message))
    print(usage_text)
    sys.exit(2)


def save_bullets(bullets, _file):
    data_to_save = ''

    for bullet in bullets:
        data_to_save += '\r\n'.join(bullet['headers']) + '\r\n'
        data_to_save += '{size} {url}\r\n'.format(size=len(bullet['body']),
                                                  url=bullet['url'])
        data_to_save += '{body}\r\n\n'.format(body=bullet['body'])

    _file.write(data_to_save)


def main(args):
    settings = parse_args(args, Settings())
    req_template = None
    for type in settings.bullets_types:

        if type == "installation":
            req_template = InstallationRequestTemplate(
                max_clusters_count=settings.max_clusters_count,
                max_cluster_size=settings.max_cluster_size)
        elif type == "action-log":
            req_template = ActionLogRequestTemplate(
                max_logs_count=settings.max_logs_count)
        elif type == "oswl-stat":
            req_template = OSwLRequestTemplate()
        #_file = open(settings.config_file, 'a')
        with open(settings.config_file, 'a') as _file:
            for _ in xrange(settings.bullets_count):
                bullets = []
                bullet_url = req_template.url
                bullet_headers = ['[Host: {0}]'.format(settings.host_address)]
                bullet_headers.extend(req_template.headers)
                bullet_body = req_template.get_request_body()
                bullet = {
                    'url': bullet_url,
                    'headers': bullet_headers,
                    'body': bullet_body
                }
                bullets.append(bullet)
                save_bullets(bullets, _file)
        file_size = os.stat(settings.config_file).st_size / 1024
        print("\n\tBullets were saved to '{0}' ({1}K) file\n".format(
            settings.config_file, file_size))


if __name__ == '__main__':
    main(sys.argv[1:])
