"""
This script will perform a tree walk through the AWS VGP species directory and
through projects on DNAnexus and compare contents to ensure symlinks are created
for all files.
"""

import boto3
import dxpy
import argparse
import os

VGP_BUCKET = "genomeark"
SHARE_WITH = "org-vgp"

def locate_or_create_dx_drive(drive_name='genomeark'):
    # findDrives is an API method that has not been explicitly added to dxpy yet, so call the API method explicitly.
    drives = dxpy.DXHTTPRequest('/system/findDrives', {'name': drive_name}, always_retry=True)['results']

    # use boto to read the profile info from aws config file
    s3client = boto3.session.Session(profile_name=drive_name)
    profile = s3client.get_credentials()
    
    if len(drives) == 1:
        # Make sure the drive we found is up to date with the latest credentials
        drive_id = drives[0]['id']
        update = {'credentials': {'accessKeyId': profile.access_key,
                                  "secretAccessKey": profile.secret_key}}
        drive_id = dxpy.DXHTTPRequest('/{0}/update'.format(drive_id), update)

        return drive_id
    elif len(drives) == 0:
        # if no drive exists, create it
        print("Creating drive with name: {0}".format(drive_name))

        # create drive using API call
        new_drive_def = {'name': drive_name,
                     'cloud': 'aws',
                     'credentials': {'accessKeyId': profile.access_key,
                                     "secretAccessKey": profile.secret_key}}
        drive_id = dxpy.DXHTTPRequest('/drive/new', new_drive_def)
        print("Created drive with id: {0}".format(drive_id))
        return drive_id
    elif len(drives) > 1:
        print("More than one drives found with name '{0}'".format(drive_name))
        sys.exit(1)

def locate_or_create_dx_project(project_name, billTo=None, skip_share=False):
    '''Try to find the project with the given name.  If one doesn't exist,
    we'll create it.'''
    projects = dxpy.find_projects(name=project_name, name_mode='glob', return_handler=True, level='CONTRIBUTE')

    project = [p for p in projects]
    if len(project) < 1:
        project_params = {'name': project_name, 'summary': 'VGP Data Project'}
        if billTo:
            project_params['billTo'] = billTo
        project = dxpy.DXProject(dxpy.api.project_new(project_params)['id'])
    elif len(project) > 1:
        print 'Found more than 1 project matching ' + project_name + '.'
        print 'Please provide a unique project!'
        sys.exit(1)
    else:
        project = project[0]
    
    if skip_share is False:
        project.invite(SHARE_WITH, "VIEW")

    return project

def parse_args():
    '''Parse the input arguments.'''
    ap = argparse.ArgumentParser(description='Sync VGP AWS Drive to DNAnexus')

    ap.add_argument('-p', '--profile',
                    help='AWS Profile name',
                    required=True)

    ap.add_argument('-d', '--delete-links',
                    help='Delete links in DNAnexus that are not found in AWS',
                    action='store_true',
                    required=False)

    ap.add_argument('-b', '--bill-to',
                    help='Organization to set as \'bill-to\' for newly created DNAnexus projects',
                    required=False)

    ap.add_argument('-s', '--skip-share',
                    help='Newly created projects will be shared with {0} by default. If this option is enabled new projects will not be shared.'.format(SHARE_WITH),
                    required=False,
                    action='store_true')

    ap.add_argument('-i', '--species-id',
                    help='Specify the species-id to sync.',
                    required=True)

    ap.add_argument('-n', '--species-name',
                    help='Specify the species-name to sync.',
                    required=True)

    ap.add_argument('-g', '--prefix',
		    help='Prefix to sync. s3://genomeark/SPECIES_NAME/SPECIES_ID/PREFIX* will be synced. DEFAULT=genomic_data',
		    required=False)

    ap.add_argument('-t', '--target-project',
                    help='Specify the DNAnexus project to sync to. Species ID will be used by default.',
                    required=False)

    return ap.parse_args()

def main(profile, delete_links=False, bill_to =None, skip_share=False, 
         species_id=None, species_name=None, target_project=None, prefix="genomic_data"):
    # connect to S3 using Boto3 client
    s3client = boto3.session.Session(profile_name=profile).resource('s3')
    
    # grab the drive-id on DNAnexus
    dx_drive = locate_or_create_dx_drive(profile)

    # list objects in the bucket under 'species' directory
    all_objects = s3client.Bucket(VGP_BUCKET).objects.filter(Prefix='species/' + species_name + '/' + species_id + '/' + prefix )

    # grab the DNAnexus project
    if target_project:
        project = locate_or_create_dx_project(target_project, bill_to, skip_share)
    else:
        project = locate_or_create_dx_project(species_id, bill_to, skip_share)

    # find all data in the DNAnexus project
    dx_project_files = dxpy.find_data_objects(project=project.id, describe={'defaultFields': True, 'details': True})

    # filter AWS objects to data that should match DNAnexus data
    aws_project_files = [object.key for object in all_objects] #if object.key.split('/')[2] == species_id]
    print "Found {0} matching files.".format(len(aws_project_files))

    # in case project properties doesn't have species_name, update it
    dxpy.api.project_set_properties(project.id, input_params={'properties': {'species_name': species_name}})

    found_links = []
    links_to_delete = []
    # iterate and compare links and objects
    for link in dx_project_files:
        # if this is a real dx file and not a symlink, skip it
        if 'drive' not in link['describe']:
            continue
            
        # now check if this link has object key matching our bucket objects 
        # or if it's a dead link we should delete
        object_key = link['describe']['details'].get('object')
        if object_key in aws_project_files:
            found_links.append(object_key)
        else:
            links_to_delete.append(link['id'])

    # any links that are in AWS but weren't found in DNAnexus should be added
    links_to_add = [object for object in aws_project_files if object not in found_links]

    # delete the bad links
    if delete_links is True:
        project.remove_objects(links_to_delete)
    
    # add the new links
    for object in links_to_add:
	if object.endswith('/'):
	   continue

	print "[DEBUG] :: Adding s3://" + VGP_BUCKET + "/" + object
        folder_path, filename = os.path.split('/' + object)
        folder_path = folder_path.replace('species/{0}/{1}'.format(species_name, species_id), '')
        
        file = dxpy.api.file_new({
                            'project': project.id,
                            'folder': folder_path,
                            'parents': True,
                            'name': filename,
                            'drive': dx_drive["id"],
                            'tags': [species_name, species_id],
                            'symlinkPath': {
                                "container": "{region}:{bucket}".format(region='us-east-1', bucket=VGP_BUCKET),
                                "object": object
                                },
                            'details': {'container': VGP_BUCKET,
                                        'object': object}
                              })

if __name__ == '__main__':
    ap = parse_args()
    main(ap.profile, ap.delete_links, ap.bill_to, ap.skip_share, ap.species_id,
         ap.species_name, ap.target_project, ap.prefix)
