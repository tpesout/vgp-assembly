#!/usr/bin/env python
# dx_to_vgp_s3_file_transfer.py
from __future__ import print_function

import os
import dxpy
import subprocess
import shutil
import time

# This part with break as new Cloud Service Providers are added. In future versions
# Select instance based on requirements
INSTANCES = {
    'NORMAL': 'mem1_ssd1_x2',
    'HIGH': 'mem1_ssd1_x16'
}
TARGET_S3 = 'genomeark'
S3_ROOT_FOLDER = '/species'
DX_DRIVE_NAME = 'genomeark_prod'
AWS_DIR = '/home/dnanexus/.aws'
AWS_ACCESS_KEY_FILENAME = '/home/dnanexus/accessKeys_dnanexus.csv'
CREDENTIALS = '''[default]
aws_access_key_id={aws_access_key}
aws_secret_access_key={aws_secret_access_key}
region=us-east-1'''

def _run_cmd(cmd, returnOutput=False):
    print(cmd)
    if returnOutput:
        output = subprocess.check_output(
            cmd, shell=True, executable='/bin/bash').strip()
        return output
    else:
        subprocess.check_call(cmd, shell=True, executable='/bin/bash')


def _get_aws_key():
    # Read in the credentials from the csv file provided by AWS.
    with open(AWS_ACCESS_KEY_FILENAME) as fh:
        access_key, secret_access_key = fh.read().strip().split('\n')[1].split(',')

    return access_key, secret_access_key


def _write_aws_credential_file():
    access_key, secret_access_key = _get_aws_key()
    # Write the AWS config file into the aws directory
    if not os.path.exists(AWS_DIR):
        os.makedirs(AWS_DIR)
    with open(os.path.join(AWS_DIR, 'config'), 'w') as fh:
        fh.write(CREDENTIALS.format(aws_access_key=access_key, aws_secret_access_key=secret_access_key))


def instance_from_bandwidth(bandwidth):
    return INSTANCES[bandwidth]


def _split_partition(file_links, worker_max):
    """
    More verbose adaptation of Longest processing time algorithm

    Assumes besides bandwidth that size is the limiting factor to S3 cp operations

    Will attempt to create bins of roughly the same size.
    1) Sort items in decreasing size order
    2) Add current largest item first then add smallest item until max bin size is reached.
          Have 2 pointers one going in the forward direction 'i' and the other going in the reverse 'j'.
          When 'i' > 'j' all items have been covered.
    """
    f_files = []
    proj_id = os.environ['DX_PROJECT_CONTEXT_ID']
    for fl in file_links:
        fdx = dxpy.DXFile(fl, project=proj_id)
        f_info = fdx.describe(fields={'size', 'id', 'folder', 'name'})
        print('FileID: {0} Size: {1} Folder: {2}'.format(f_info['id'], f_info['size'], f_info['folder']))
        f_files.append(f_info)
    # sort list by decreaasing file size
    fl_sorted = sorted(f_files, key=lambda pair: pair['size'], reverse=True)

    # Info: sorted elems #
    print('Sorted array:')
    for elem in fl_sorted:
        print(elem)
    # Info #

    # Create partitions
    partition_list = []
    avg_part_size = sum([elem['size'] for elem in fl_sorted]) / worker_max
    temparr = [fl_sorted[0]]
    running_size = fl_sorted[0]['size']
    max_part_size = max(running_size, avg_part_size)
    print('max partition size: {0}'.format(max_part_size))
    i = 1  # largest elem
    j = len(fl_sorted) - 1  # smallest elem
    while i < len(fl_sorted):
        if i > j:
            break
        elif running_size >= max_part_size:
            partition_list.append(temparr)
            temparr = [fl_sorted[i]]
            running_size = fl_sorted[i]['size']
            i += 1
            continue
        temparr.append(fl_sorted[j])
        running_size += fl_sorted[j]['size']
        j -= 1

    partition_list.append(temparr)  # Append last partition
    print('partitions to create: {0}'.format(len(partition_list)))
    return partition_list


def locate_or_create_dx_drive():
    # findDrives is an API method that has not been explicitly added to dxpy yet, so call the API method explicitly.
    drives = dxpy.DXHTTPRequest('/system/findDrives', {'name': DX_DRIVE_NAME}, always_retry=True)['results']

    if len(drives) == 1:
        return drives[0]
    elif len(drives) == 0:
        # if no drive exists, create it
        access_key, secret_access_key = _get_aws_key()
        print('Creating drive with name: {0}'.format(DX_DRIVE_NAME))
        # create drive using API call
        new_drive_def = {'name': DX_DRIVE_NAME,
                         'cloud': 'aws',
                         'credentials': {'accessKeyId': access_key,
                                         'secretAccessKey': secret_access_key}}
        drive_id = dxpy.DXHTTPRequest('/drive/new', new_drive_def)
        print('Created drive with id: {0}'.format(DX_DRIVE_NAME))
        return drive_id
    elif len(drives) > 1:
        msg = 'More than one drives found with name "{0}"'.format(DX_DRIVE_NAME)
        raise dxpy.AppInternalError(msg)


def create_sym_link(f_id, f_name, f_folder, target_s3, upload_dest, md5sum):
    dx_drive = locate_or_create_dx_drive()
    # create new dx file
    sym_link_details = {'project': dxpy.PROJECT_CONTEXT_ID,
                        'folder': '/{0}'.format(f_folder),
                        'parents': True,
                        'name': f_name,
                        'drive': dx_drive['id'],
                        'md5sum': md5sum,
                        'symlinkPath': {
                            'container': '{region}:{bucket}'.format(region='us-east-1', bucket=target_s3),
                            'object': str(upload_dest)
                        },
                        'details': {'container': target_s3,
                                    'object': upload_dest}
                        }
    print(str(sym_link_details))
    file = dxpy.api.file_new(sym_link_details)
    dxf = dxpy.DXFile(f_id, project=dxpy.PROJECT_CONTEXT_ID)
    dxf.remove()


def _get_species_name():
    project_desc = dxpy.describe(dxpy.PROJECT_CONTEXT_ID, input_params={'properties': True})
    if 'species_name' in project_desc['properties']:
        return project_desc['properties']['species_name']
    else:
        raise dxpy.AppInternalError('No species name was provided as input or as a property of this project.')


@dxpy.entry_point('s3_upload')
def s3_upload(target_s3, assigned_files, up_dir):
    # info
    print('Total size: {0}'.format(sum([item['size'] for item in assigned_files])))
    print('Total files: {0}'.format(len(assigned_files)))

    _write_aws_credential_file()

    # Append user added options
    options = ''

    # Upload files via stream
    for i, f_info in enumerate(assigned_files):
        # Set upload dir
        fn = f_info['name']
        f_folder = f_info['folder'].strip('/')
        upload_dest = os.path.join(up_dir, f_folder, fn)
        full_s3_path = 's3://{0}'.format(os.path.join(target_s3, upload_dest))

        # Create cp command
        print('Uploading File name: ' + fn)
        temp_filename = 'temp_file'
        _run_cmd('mkfifo {0}'.format(temp_filename))
        cmd = 'set -o pipefail; dx cat {f_id} | tee {fifo_fn} | aws s3 cp - \'{full_s3_path}\' --expected-size {file_size} {adv_opts}'.format(
            f_id=f_info['id'], fifo_fn = temp_filename, full_s3_path=full_s3_path, file_size=f_info['size'], adv_opts=options)
        print(cmd)
        stream_proc = subprocess.Popen(cmd, shell=True, executable='/bin/bash')
        md5sum = _run_cmd('md5sum {0}'.format(temp_filename), True).split()[0]
        print('{0}'.format(md5sum))
        stream_stdout, stream_stderr = stream_proc.communicate()
        if stream_proc.returncode != 0:
            print(str(fn) + ' failed upload')
            with open('response.txt', 'a') as f:
                f.write('FAILED copy: {0} to {1}'.format(fn, full_s3_path) + '\n')
        else:
            print(str(fn) + ' successful upload')
            create_sym_link(f_info['id'], fn, f_folder, target_s3, upload_dest, md5sum)
            with open('response.txt', 'a') as f:
                f.write('copy: {0} to {1}'.format(fn, full_s3_path) + '\n')
        os.remove(temp_filename)

    rspDXFile = dxpy.upload_local_file('response.txt')
    rspDXLink = dxpy.dxlink(rspDXFile.get_id())
    return {'report_file_link': rspDXLink}


@dxpy.entry_point('create_upload_report')
def create_upload_report(filelinks):
    print('File links: ' + str(filelinks))

    curr_date = time.strftime('%b_%d_%Y')

    for dxlink in filelinks:
        filemerge_cmd = 'dx cat {0} >> upload_report{1}.txt'.format(dxlink['$dnanexus_link'], curr_date)
        _run_cmd(filemerge_cmd)

    reportDXFile = dxpy.upload_local_file('upload_report{0}.txt'.format(curr_date))
    reportDXlink = dxpy.dxlink(reportDXFile.get_id())

    return {'reportDXLink': reportDXlink}


def _is_symlink(f_id):
    dxf = dxpy.DXFile(f_id)
    desc = dxf.describe(fields={'symlinkPath':True})
    return 'symlinkPath' in desc


@dxpy.entry_point('main')
def main(worker_max, f_ids, bandwidth, species_name=None):
    """
    Input variables removed:
    """
    _run_cmd('aws --version', True)
    print('file ids: ' + str(f_ids))

    # Remove any files which are already symlinks
    f_ids = filter(lambda x: not _is_symlink(x), f_ids)

    if species_name is None:
        species_name = _get_species_name()

    # Set upload root to user specified directory or project
    projdx = dxpy.DXProject(os.environ['DX_PROJECT_CONTEXT_ID'])
    dir_file = os.path.join(S3_ROOT_FOLDER, species_name, projdx.name)

    # Trim trailing / in upload dir
    dir_file = dir_file.strip('/')
    print('Upload directory: ' + dir_file)

    # Programatically split files into equal list based on size and max workers
    split_list_dxlinks = _split_partition(f_ids, worker_max)

    # Select instance type based on user input
    trans_worker_inst = instance_from_bandwidth(bandwidth)

    # Run subjobs on list
    uploadjobs = [dxpy.new_dxjob(
                  fn_input={'target_s3': TARGET_S3,
                            'assigned_files': f_group,
                            'up_dir': dir_file},
                  fn_name='s3_upload',
                  instance_type=trans_worker_inst)
                  for f_group in split_list_dxlinks]

    # Merge S3 status upload reports from subjobs
    report_fileDXLinks = [subjob.get_output_ref('report_file_link')
                          for subjob in uploadjobs]

    print('Creating S3 upload report')
    report_job = dxpy.new_dxjob(
        fn_input={'filelinks': report_fileDXLinks}, fn_name='create_upload_report')

    # Output merged report
    print('Output final report')
    finalreportDXLink = report_job.get_output_ref('reportDXLink')
    output = {}
    output['upload_report'] = finalreportDXLink

    return output


dxpy.run()
