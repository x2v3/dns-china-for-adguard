import requests
import zipfile
import os
import logging
import datetime
import re

temp_dir = './temp'
source_zip = 'https://github.com/felixonmars/dnsmasq-china-list/archive/refs/heads/master.zip'
artifacts_dir = '..'


def download_and_unzip(source_zip, temp_dir):
    logging.info('Downloading and unzipping...')
    r = requests.get(source_zip, stream=True)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    with open(f'{temp_dir}/master.zip', 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            f.write(chunk)
    with zipfile.ZipFile(f'{temp_dir}/master.zip', 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    os.remove(f'{temp_dir}/master.zip')
    logging.info(f'Done, files are in {temp_dir}')
    return temp_dir


# the conf file content lines is in the format of : server=/example.com/114.114.114.114
# we need to convert it to : [/example.com/]114.114.114.114
def convert_conf_files(temp_dir: str, artifacts_dir: str, content_handler: callable(str)):
    logging.info('Converting conf files...')
    if not os.path.exists(artifacts_dir):
        logging.info('Creating artifacts directory...')
        os.makedirs(artifacts_dir)
    files = os.listdir(f'{temp_dir}/dnsmasq-china-list-master')
    logging.info(f'Found {len(files)} files to convert.')
    for file in files:
        if file.endswith('.conf'):
            with open(f'{temp_dir}/dnsmasq-china-list-master/{file}', 'r') as f:
                content = f.read()
                content = content_handler(content)
                with open(f'{artifacts_dir}/{file}', 'w') as f:
                    f.write(content)
    logging.info('Done')


def convert_to_aghome_conf(temp_dir, artifacts_dir):
    def ag_content_handler(content: str):
        content = content.replace('/', '/]')
        content = content.replace('server=/]', '[/')
        return content

    return convert_conf_files(temp_dir, artifacts_dir, ag_content_handler)


def convert_to_smartdns_conf(temp_dir, artifacts_dir):
    def smartdns_content_handler(content: str):
        content = content.replace('server=/', '')
        content = re.sub('\/(\d+\.){3}\d+', '', content)
        return content

    return convert_conf_files(temp_dir, artifacts_dir, smartdns_content_handler)


# find the line starting with "Last updated on" and update it
def update_readme():
    file = open('../README.md', 'r')
    lines = file.readlines()
    file.close()
    file = open('../README.md', 'w')
    for line in lines:
        if line.startswith('Last updated on'):
            file.write('Last updated on: ' + str(datetime.datetime.now()) + '\n')
        else:
            file.write(line)


def main():
    download_and_unzip(source_zip, temp_dir)
    convert_to_aghome_conf(temp_dir, '%s/%s' % (artifacts_dir, 'adguard'))
    convert_to_smartdns_conf(temp_dir, '%s/%s' % (artifacts_dir, 'smartdns'))
    update_readme()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
